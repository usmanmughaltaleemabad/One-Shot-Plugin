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


# ─── Conservative per-agent estimates ────────────────────────────────────────

# Tokens are educated guesses for a "typical" one-shot of 3–5 entities. The
# input column includes the spec.json + scanner output (cached across all
# agents in the same session via prompt caching, so input cost is mostly
# paid once).
PER_AGENT_TOKEN_ESTIMATES = {
    "architect":   {"model": "sonnet", "input": 8000,  "output": 6000},
    "implementer": {"model": "haiku",  "input": 5000,  "output": 4000},  # per file
    "test-author": {"model": "sonnet", "input": 6000,  "output": 5000},
    "reviewer":    {"model": "sonnet", "input": 8000,  "output": 2500},
    "wirer":       {"model": "haiku",  "input": 2000,  "output": 1500},
    "critic":      {"model": "sonnet", "input": 3000,  "output": 1500},
}


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


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Estimate Claude token cost for an agentic generation"
    )
    parser.add_argument("--plan", required=True, help="Path to plan.json")
    parser.add_argument("--budget", type=float, default=None,
                        help="USD ceiling. Exit 2 if estimated > budget.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

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
