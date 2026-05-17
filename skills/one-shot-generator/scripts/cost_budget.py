#!/usr/bin/env python3
"""
Cost Budget Estimator — v1.0.0  (Tier 3.5 token-cost gate)

Before the agentic pipeline spawns agents, estimate the expected token
spend and decide whether to proceed, ask the user, or fall back to the
free templated path. Estimates are deliberately conservative; the gate
is meant to protect users from sticker shock, not micro-bill.

Pricing snapshot (Anthropic API list prices as of mid-2026; update when
Anthropic changes them):

  Haiku 4.5      $0.80 / Mtok input   $4.00 / Mtok output
  Sonnet 4.6     $3.00 / Mtok input  $15.00 / Mtok output
  Opus 4.7      $15.00 / Mtok input  $75.00 / Mtok output

The estimator returns a USD figure and an explanation the SKILL.md
can quote back to the user.

CLI:
    python cost_budget.py --plan plan.json
    python cost_budget.py --plan plan.json --budget=0.50
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from lib.base_script import bootstrap_runtime, setup_logging
bootstrap_runtime()

logger = setup_logging(__name__)


# ─── Pricing snapshot (mid-2026) ─────────────────────────────────────────────

PRICING_USD_PER_MTOK = {
    "haiku":  {"input": 0.80,  "output": 4.00},
    "sonnet": {"input": 3.00,  "output": 15.00},
    "opus":   {"input": 15.00, "output": 75.00},
}


# ─── Per-agent token estimates (calibrated against measured runs) ───────────

# Calibration anchor (2026-05-18): architect dry-run via Task tool
# consumed 26,119 tokens total at ~$0.10 cost. My pre-run estimate of
# 8K in + 6K out = 14K total understated by ~85%. The estimates below
# bump every agent line upward by ~85% from the original guess so they
# track empirical usage. Replace these with measured p50 / p95 as more
# real-run data accumulates (see `cost_budget.log_actual()` and
# `.beads/cost_observations.jsonl`).
PER_AGENT_TOKEN_ESTIMATES = {
    # Architect needs to read scanner + domain model + curriculum + emit
    # full spec.json — measured at 26K total on a 2-entity feature.
    "architect":   {"model": "sonnet", "input": 14000, "output": 11000},
    # Implementer writes one file from spec; conservative across small
    # FastAPI routers (~200 LOC) and longer Spring controllers (~500 LOC).
    "implementer": {"model": "haiku",  "input": 9000,  "output": 7000},
    # Test-author reads spec + test_contract; output is the test module.
    "test-author": {"model": "sonnet", "input": 11000, "output": 9000},
    # Reviewer reads ALL implementer outputs + spec; output is a PASS or
    # REVISE memo, so input dominates.
    "reviewer":    {"model": "sonnet", "input": 15000, "output": 4500},
    # Wirer is cheap: reads main.py + generated routers, edits one file.
    "wirer":       {"model": "haiku",  "input": 4000,  "output": 2500},
    # Critic invokes pytest via Bash; output is the verdict + routes.
    "critic":      {"model": "sonnet", "input": 5500,  "output": 2500},
}

# Calibration source-of-truth: each entry's `(input, output)` should be
# updated when `.beads/cost_observations.jsonl` accumulates >=10 entries
# for that agent. `recalibrate_from_log()` below does this automatically.


@dataclass
class CostLine:
    agent: str
    model: str
    invocations: int
    input_tokens: int
    output_tokens: int
    usd: float

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class CostEstimate:
    feature: str
    total_usd: float
    breakdown: List[CostLine]
    within_budget: Optional[bool] = None
    budget_usd: Optional[float] = None
    explanation: str = ""

    def to_dict(self) -> Dict:
        return {
            "feature": self.feature,
            "total_usd": round(self.total_usd, 4),
            "breakdown": [c.to_dict() for c in self.breakdown],
            "within_budget": self.within_budget,
            "budget_usd": self.budget_usd,
            "explanation": self.explanation,
        }


def _line_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    p = PRICING_USD_PER_MTOK[model]
    return (input_tokens / 1_000_000) * p["input"] + \
           (output_tokens / 1_000_000) * p["output"]


def estimate(plan_doc: Dict[str, Any], *,
             budget_usd: Optional[float] = None) -> CostEstimate:
    n_new_files = sum(
        1 for f in plan_doc.get("files_to_create", [])
        if f.get("kind") in ("sqlalchemy_model", "pydantic_schema",
                              "fastapi_router")
    )
    if n_new_files == 0:
        n_new_files = 1  # at least one implementer pass

    lines: List[CostLine] = []
    for agent, est in PER_AGENT_TOKEN_ESTIMATES.items():
        invocations = n_new_files if agent == "implementer" else 1
        line_input = est["input"] * invocations
        line_output = est["output"] * invocations
        usd = _line_cost(est["model"], line_input, line_output)
        lines.append(CostLine(
            agent=agent, model=est["model"], invocations=invocations,
            input_tokens=line_input, output_tokens=line_output,
            usd=round(usd, 4),
        ))

    total = round(sum(l.usd for l in lines), 4)
    within = None if budget_usd is None else (total <= budget_usd)
    if budget_usd is None:
        explanation = (f"Estimated agentic cost: ${total:.2f}. Pass "
                       f"--budget=<usd> to gate on a ceiling.")
    elif within:
        explanation = (f"${total:.2f} ≤ budget ${budget_usd:.2f}. Proceed.")
    else:
        explanation = (f"${total:.2f} > budget ${budget_usd:.2f}. "
                       "Halt and ask user, or fall back to --templated.")

    return CostEstimate(
        feature=plan_doc.get("feature", ""),
        total_usd=total,
        breakdown=lines,
        within_budget=within,
        budget_usd=budget_usd,
        explanation=explanation,
    )


# ─── Empirical calibration ──────────────────────────────────────────────────

import datetime as _dt
import statistics as _statistics

OBSERVATIONS_LOG = Path(".beads/cost_observations.jsonl")


def log_actual(*, agent: str, model: str, input_tokens: int,
               output_tokens: int, duration_ms: Optional[int] = None,
               repo_root: Optional[Path] = None) -> None:
    """Record one observed agent invocation cost.

    Call from the SKILL.md after any Task() spawn: the model returns
    token counts in its <usage> block; pipe them here so the next run
    estimates against measured reality instead of educated guesses.
    """
    root = Path(repo_root or Path.cwd()).resolve()
    log_path = root / OBSERVATIONS_LOG
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0, tzinfo=None).isoformat() + "Z",
        "agent": agent,
        "model": model,
        "input": int(input_tokens),
        "output": int(output_tokens),
        "duration_ms": duration_ms,
    }
    with log_path.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(entry) + "\n")


def recalibrate_from_log(repo_root: Optional[Path] = None,
                         min_samples: int = 10) -> Dict[str, Dict[str, Any]]:
    """Read observations and return what the new per-agent estimates
    SHOULD be (p50). Caller decides whether to merge them back into
    PER_AGENT_TOKEN_ESTIMATES; this function never mutates module state.

    Returns ``{agent: {"input": p50, "output": p50, "n": sample_count}}``.
    """
    root = Path(repo_root or Path.cwd()).resolve()
    log_path = root / OBSERVATIONS_LOG
    if not log_path.exists():
        return {}
    by_agent: Dict[str, Dict[str, List[int]]] = {}
    for line in log_path.read_text(encoding="utf-8").splitlines():
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        agent = entry.get("agent")
        if not agent:
            continue
        bucket = by_agent.setdefault(agent, {"input": [], "output": []})
        bucket["input"].append(int(entry.get("input", 0)))
        bucket["output"].append(int(entry.get("output", 0)))
    out: Dict[str, Dict[str, Any]] = {}
    for agent, tokens in by_agent.items():
        n = len(tokens["input"])
        if n < min_samples:
            continue
        out[agent] = {
            "input":  int(_statistics.median(tokens["input"])),
            "output": int(_statistics.median(tokens["output"])),
            "n": n,
        }
    return out


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Estimate Claude token cost for an agentic generation"
    )
    parser.add_argument("--plan", help="Path to plan.json")
    parser.add_argument("--budget", type=float, default=None,
                        help="USD ceiling. Exit 2 if estimated > budget.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--log-actual", action="store_true",
                        help="Subcommand: log one observed agent invocation. "
                             "Requires --agent --model --input --output.")
    parser.add_argument("--recalibrate", action="store_true",
                        help="Subcommand: emit recalibrated per-agent estimates "
                             "from .beads/cost_observations.jsonl (p50).")
    parser.add_argument("--agent")
    parser.add_argument("--model", choices=list(PRICING_USD_PER_MTOK))
    parser.add_argument("--input", type=int, dest="in_tokens")
    parser.add_argument("--output", type=int, dest="out_tokens")
    parser.add_argument("--duration-ms", type=int, default=None)
    parser.add_argument("--repo-root", default=None)
    args = parser.parse_args()

    if args.log_actual:
        if not (args.agent and args.model and args.in_tokens and args.out_tokens):
            parser.error("--log-actual requires --agent --model --input --output")
        log_actual(agent=args.agent, model=args.model,
                   input_tokens=args.in_tokens, output_tokens=args.out_tokens,
                   duration_ms=args.duration_ms,
                   repo_root=Path(args.repo_root) if args.repo_root else None)
        print(f"logged {args.agent} observation", file=sys.stderr)
        return

    if args.recalibrate:
        recalibrated = recalibrate_from_log(
            repo_root=Path(args.repo_root) if args.repo_root else None)
        print(json.dumps(recalibrated, indent=2))
        return

    if not args.plan:
        parser.error("--plan is required for the default (estimate) mode")
    plan_doc = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    est = estimate(plan_doc, budget_usd=args.budget)
    if args.json:
        print(json.dumps(est.to_dict(), indent=2))
    else:
        print(f"COST ESTIMATE — {est.feature}")
        for line in est.breakdown:
            print(f"  {line.agent:<13} {line.model:<7} ×{line.invocations:<2}  "
                  f"in={line.input_tokens:>5}  out={line.output_tokens:>5}  "
                  f"${line.usd:.4f}")
        print(f"  {'TOTAL':<13} {'':<7} {' ':<3}  "
              f"{' ':>5}  {' ':>5}        ${est.total_usd:.4f}")
        print(f"\n  {est.explanation}")
    if est.within_budget is False:
        sys.exit(2)


if __name__ == "__main__":
    main()
