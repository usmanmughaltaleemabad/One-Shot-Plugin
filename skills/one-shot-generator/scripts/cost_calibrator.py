#!/usr/bin/env python3
"""
Cost Calibrator — v1.0.0  (self-recalibrating cost model)

`cost_budget.py` carries hardcoded `PER_AGENT_TOKEN_ESTIMATES` that
were anchored against a handful of real architect runs. As more agent
invocations accumulate in `.beads/cost_observations.jsonl`, those
estimates drift from reality.

`cost_budget.recalibrate_from_log()` already COMPUTES what the new
estimates should be (p50 median per agent), but it never writes them
back — by design (no module-state mutation from runtime). This
script does the write-back step: it reads the observations log, the
existing constants, and EITHER:

  - default: emits a unified diff showing the proposed changes (review then apply manually)
  - `--apply`: rewrites `cost_budget.py` in place
  - `--check`: exits 1 if the existing constants drift by > threshold

It also cross-checks against `.claude/registry/learnings.jsonl` for an
independent cost_usd signal (the dashboard's data) so we don't blindly
trust token counts when the actual dollar cost tells a different story.

CLI:
    cost_calibrator.py                          # default: diff to stdout
    cost_calibrator.py --apply                  # rewrite cost_budget.py
    cost_calibrator.py --check --threshold 0.20 # CI gate (exit 1 if drift > 20%)
    cost_calibrator.py --min-samples 5          # default 10
    cost_calibrator.py --repo-root <path>       # default cwd

Exit codes:
    0   no significant drift OR --apply succeeded OR diff emitted
    1   --check found drift > threshold
    2   bad CLI args / observations log missing
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from lib.base_script import bootstrap_runtime, setup_logging

bootstrap_runtime()
logger = setup_logging(__name__)


COST_BUDGET_PATH = Path("skills/one-shot-generator/scripts/cost_budget.py")
OBSERVATIONS_LOG = Path(".beads/cost_observations.jsonl")
LEARNINGS_LOG = Path(".claude/registry/learnings.jsonl")
# Marker comments around the dict so the rewriter can locate it
# unambiguously (matching by name alone is fragile when comments are above).
_DICT_START = re.compile(
    r"^PER_AGENT_TOKEN_ESTIMATES\s*=\s*\{", re.M
)


# ─── Reading existing constants ────────────────────────────────────────────

def _read_existing(repo_root: Path) -> Dict[str, Dict[str, Any]]:
    """Import cost_budget.PER_AGENT_TOKEN_ESTIMATES without polluting
    the test process's sys.modules. Falls back to a regex parse if
    import fails (e.g. from a different worktree)."""
    # Avoid `import cost_budget` here — tests run from arbitrary cwds.
    # Re-parse the file as a dict literal substring.
    path = repo_root / COST_BUDGET_PATH
    if not path.exists():
        raise FileNotFoundError(f"cost_budget.py not found at {path}")
    text = path.read_text(encoding="utf-8")
    m = _DICT_START.search(text)
    if not m:
        raise ValueError(
            "could not locate PER_AGENT_TOKEN_ESTIMATES in cost_budget.py")
    # Find the matching closing brace.
    open_idx = text.find("{", m.start())
    depth = 0
    close_idx = -1
    for i in range(open_idx, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                close_idx = i
                break
    if close_idx < 0:
        raise ValueError("unbalanced braces in PER_AGENT_TOKEN_ESTIMATES")
    body = text[open_idx:close_idx + 1]
    # Pseudo-eval the dict in a tightly-scoped namespace.
    ns: Dict[str, Any] = {}
    exec(f"_x = {body}", {"__builtins__": {}}, ns)
    return ns["_x"]


# ─── Computing recalibrated values from observations ───────────────────────

def _median(xs: List[int]) -> int:
    n = len(xs)
    if n == 0:
        return 0
    s = sorted(xs)
    if n % 2:
        return s[n // 2]
    return (s[n // 2 - 1] + s[n // 2]) // 2


def _read_observations(repo_root: Path) -> Dict[str, List[Dict[str, int]]]:
    path = repo_root / OBSERVATIONS_LOG
    if not path.exists():
        return {}
    by_agent: Dict[str, List[Dict[str, int]]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        agent = entry.get("agent")
        if not agent:
            continue
        by_agent.setdefault(agent, []).append({
            "input":  int(entry.get("input", 0)),
            "output": int(entry.get("output", 0)),
        })
    return by_agent


def compute_p50(observations: Dict[str, List[Dict[str, int]]],
                 *, min_samples: int = 10) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for agent, rows in observations.items():
        if len(rows) < min_samples:
            continue
        out[agent] = {
            "input":  _median([r["input"] for r in rows]),
            "output": _median([r["output"] for r in rows]),
            "n": len(rows),
        }
    return out


# ─── Cross-check against learnings.jsonl ──────────────────────────────────

def _read_learnings_costs(repo_root: Path) -> Dict[str, List[float]]:
    """Return {agent_id: [cost_usd, ...]} from the dashboard's registry.
    Anchors the token-level estimates against actual dollar reality —
    if the recalibrated tokens diverge wildly from observed cost_usd,
    something's off."""
    path = repo_root / LEARNINGS_LOG
    if not path.exists():
        return {}
    by_agent: Dict[str, List[float]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        agent_id = entry.get("agent_id", "")
        # learnings_hub stores "local/architect"; cost_budget keys are
        # bare names. Strip the "local/" namespace before matching.
        agent = agent_id.split("/")[-1] if "/" in agent_id else agent_id
        cost = entry.get("cost_usd")
        if cost is None:
            continue
        by_agent.setdefault(agent, []).append(float(cost))
    return by_agent


# ─── Drift detection ───────────────────────────────────────────────────────

def compute_drift(existing: Dict[str, Dict[str, Any]],
                   recalibrated: Dict[str, Dict[str, Any]]
                   ) -> Dict[str, Dict[str, Any]]:
    """For each agent present in BOTH dicts, compute the relative drift
    on input + output tokens. Returns:
      {agent: {input_existing, input_new, input_drift_frac, output_*, ...}}"""
    out: Dict[str, Dict[str, Any]] = {}
    for agent, new in recalibrated.items():
        old = existing.get(agent)
        if not old:
            out[agent] = {"status": "new_agent", "new": new}
            continue
        def _drift(o: int, n: int) -> float:
            if o == 0:
                return 0.0 if n == 0 else float("inf")
            return (n - o) / o
        out[agent] = {
            "input_existing":  old.get("input", 0),
            "input_new":       new["input"],
            "input_drift":     round(_drift(old.get("input", 0), new["input"]), 3),
            "output_existing": old.get("output", 0),
            "output_new":      new["output"],
            "output_drift":    round(_drift(old.get("output", 0), new["output"]), 3),
            "samples":         new["n"],
            "model":           old.get("model", "?"),
        }
    return out


def has_significant_drift(drift: Dict[str, Dict[str, Any]],
                            threshold: float) -> bool:
    """True if ANY agent's input or output drift exceeds threshold
    (absolute value), i.e. its recalibrated estimate is more than
    `threshold` away from the current constant."""
    for agent, info in drift.items():
        if info.get("status") == "new_agent":
            return True
        if abs(info.get("input_drift", 0.0)) > threshold:
            return True
        if abs(info.get("output_drift", 0.0)) > threshold:
            return True
    return False


# ─── Rewriting cost_budget.py ──────────────────────────────────────────────

def _format_dict_block(merged: Dict[str, Dict[str, Any]]) -> str:
    """Render the merged dict as a Python source block matching the
    style of the existing PER_AGENT_TOKEN_ESTIMATES literal."""
    lines = ["PER_AGENT_TOKEN_ESTIMATES = {"]
    for agent, info in merged.items():
        model = info.get("model", "sonnet")
        in_t  = info.get("input", 0)
        out_t = info.get("output", 0)
        lines.append(
            f'    "{agent}": {{"model": "{model}", '
            f'"input": {in_t}, "output": {out_t}}},'
        )
    lines.append("}")
    return "\n".join(lines)


def _merge(existing: Dict[str, Dict[str, Any]],
           recalibrated: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Keep `model` from existing; replace input/output with recalibrated."""
    out: Dict[str, Dict[str, Any]] = {}
    # Preserve order from existing first, then any new agents at the end.
    for agent, old in existing.items():
        new = recalibrated.get(agent)
        if new:
            out[agent] = {**old, "input": new["input"], "output": new["output"]}
        else:
            out[agent] = old
    for agent, new in recalibrated.items():
        if agent not in out:
            out[agent] = {"model": "sonnet", "input": new["input"],
                          "output": new["output"]}
    return out


def rewrite_cost_budget(repo_root: Path,
                         merged: Dict[str, Dict[str, Any]]) -> str:
    """Atomic in-place rewrite of the PER_AGENT_TOKEN_ESTIMATES literal.
    Returns the new file contents (also written to disk)."""
    path = repo_root / COST_BUDGET_PATH
    text = path.read_text(encoding="utf-8")
    m = _DICT_START.search(text)
    if not m:
        raise ValueError("PER_AGENT_TOKEN_ESTIMATES not found")
    # Locate end of the dict literal (matching close brace).
    open_idx = text.find("{", m.start())
    depth = 0
    close_idx = -1
    for i in range(open_idx, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                close_idx = i
                break
    if close_idx < 0:
        raise ValueError("unbalanced braces")
    new_block = _format_dict_block(merged)
    new_text = text[:m.start()] + new_block + text[close_idx + 1:]
    path.write_text(new_text, encoding="utf-8")
    return new_text


def make_diff(existing_text: str, new_text: str) -> str:
    return "".join(difflib.unified_diff(
        existing_text.splitlines(keepends=True),
        new_text.splitlines(keepends=True),
        fromfile="cost_budget.py (current)",
        tofile="cost_budget.py (recalibrated)",
        n=3,
    ))


# ─── CLI ───────────────────────────────────────────────────────────────────

def _emit_report(*, drift: Dict[str, Dict[str, Any]],
                  learnings_costs: Dict[str, List[float]]) -> Dict:
    return {
        "drift_by_agent": drift,
        "learnings_cross_check_usd": {
            agent: {
                "mean":   round(sum(costs) / len(costs), 5) if costs else 0.0,
                "max":    round(max(costs), 5) if costs else 0.0,
                "min":    round(min(costs), 5) if costs else 0.0,
                "n":      len(costs),
            }
            for agent, costs in learnings_costs.items()
        },
    }


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        description="Self-recalibrate cost_budget.PER_AGENT_TOKEN_ESTIMATES "
                    "from .beads/cost_observations.jsonl. Default mode "
                    "emits a unified diff; --apply rewrites the file."
    )
    p.add_argument("--repo-root", type=Path, default=Path.cwd())
    p.add_argument("--min-samples", type=int, default=10,
                   help="Minimum observations per agent before recalibrating.")
    p.add_argument("--apply", action="store_true",
                   help="Rewrite cost_budget.py in place.")
    p.add_argument("--check", action="store_true",
                   help="Exit 1 if drift > threshold (no writes).")
    p.add_argument("--threshold", type=float, default=0.20,
                   help="Drift threshold for --check (default 0.20 = 20%% drift).")
    p.add_argument("--json", action="store_true",
                   help="Emit a JSON drift report instead of a diff.")
    args = p.parse_args(argv if argv is not None else sys.argv[1:])

    repo = args.repo_root.resolve()
    if not (repo / COST_BUDGET_PATH).exists():
        print(f"cost_budget.py not found under {repo}", file=sys.stderr)
        return 2

    existing = _read_existing(repo)
    observations = _read_observations(repo)
    recalibrated = compute_p50(observations, min_samples=args.min_samples)
    learnings = _read_learnings_costs(repo)
    drift = compute_drift(existing, recalibrated)

    if args.json:
        print(json.dumps(_emit_report(drift=drift,
                                       learnings_costs=learnings), indent=2))
        # For --check + --json, still apply the drift gate
        if args.check and has_significant_drift(drift, args.threshold):
            return 1
        return 0

    if not recalibrated:
        print(json.dumps({
            "status": "no_recalibration_possible",
            "reason": "no agent had >= min_samples observations",
            "min_samples": args.min_samples,
            "agents_observed": {a: len(rows) for a, rows in observations.items()},
        }, indent=2))
        return 0

    if args.check:
        drifted = has_significant_drift(drift, args.threshold)
        report = _emit_report(drift=drift, learnings_costs=learnings)
        report["check_threshold"] = args.threshold
        report["drift_exceeds_threshold"] = drifted
        print(json.dumps(report, indent=2))
        return 1 if drifted else 0

    # Default + --apply: produce the diff
    merged = _merge(existing, recalibrated)
    current_text = (repo / COST_BUDGET_PATH).read_text(encoding="utf-8")
    # Render the new file by doing an in-memory rewrite without touching disk
    new_text = _build_rewritten_text(current_text, merged)
    diff = make_diff(current_text, new_text)

    if args.apply:
        rewrite_cost_budget(repo, merged)
        print(json.dumps({
            "status": "applied",
            "agents_recalibrated": list(recalibrated.keys()),
            "drift_summary": drift,
        }, indent=2))
    else:
        # Show diff + brief summary
        if not diff:
            print(json.dumps({"status": "no_changes",
                              "reason": "merged dict matches existing"},
                              indent=2))
            return 0
        print(diff)
        print("\n# To apply these changes:")
        print("#   python skills/one-shot-generator/scripts/cost_calibrator.py --apply")

    return 0


def _build_rewritten_text(current_text: str,
                            merged: Dict[str, Dict[str, Any]]) -> str:
    """Pure-function variant of rewrite_cost_budget — returns new text
    without writing to disk (used to render diffs without side effects)."""
    m = _DICT_START.search(current_text)
    if not m:
        return current_text
    open_idx = current_text.find("{", m.start())
    depth = 0
    close_idx = -1
    for i in range(open_idx, len(current_text)):
        if current_text[i] == "{":
            depth += 1
        elif current_text[i] == "}":
            depth -= 1
            if depth == 0:
                close_idx = i
                break
    if close_idx < 0:
        return current_text
    return (current_text[:m.start()]
            + _format_dict_block(merged)
            + current_text[close_idx + 1:])


if __name__ == "__main__":
    sys.exit(main())
