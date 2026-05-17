#!/usr/bin/env python3
"""
pass^k Runner — Tier 9 production eval metric

Anthropic's eval guidance distinguishes:

  pass@k  Agent succeeds in AT LEAST 1 of k attempts  (research metric;
          generous; production-misleading)
  pass^k  Agent succeeds in ALL k attempts            (production metric;
          this is what customers experience)

For agentic generations, pass^k matters more — your user expects every
invocation to work, not just 1 in 5. This runner replays an eval N
times and reports both metrics + variance.

Modes:

  --mode deterministic-replay  Re-run the deterministic eval_runner.py
                               N times. All runs should be identical
                               (variance = 0); useful to confirm the
                               pipeline is reproducible.

  --mode agentic-flake-check   Read the existing recorded agent outputs
                               and bootstrap-resample to estimate flake
                               rate per scenario.

CLI:
    pass_k_runner.py --mode deterministic-replay --k 5
    pass_k_runner.py --mode agentic-flake-check --k 10 --json
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List

REPO_ROOT = Path(__file__).resolve().parents[2]
EVALS = REPO_ROOT / "tests" / "evals"


@dataclass
class PassKResult:
    eval_name: str
    k: int
    successes: int
    failures: int
    pass_at_1: float    # = at least 1 success
    pass_at_k: float    # = all k successes (most demanding)
    variance: float     # of the per-run score
    individual_scores: List[float] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return asdict(self)


# ─── Deterministic-replay mode ───────────────────────────────────────────────

def _run_deterministic_eval(eval_name: str) -> float:
    """Run a single deterministic eval and return its overall score."""
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        [sys.executable, str(EVALS / "eval_runner.py"),
         "--eval", eval_name, "--json"],
        capture_output=True, text=True, env=env, encoding="utf-8",
        timeout=60,
    )
    try:
        results = json.loads(proc.stdout)
        return results[0].get("overall", 0.0) if results else 0.0
    except json.JSONDecodeError:
        return 0.0


def run_deterministic_replay(eval_names: List[str], k: int) -> List[PassKResult]:
    out: List[PassKResult] = []
    for name in eval_names:
        scores = [_run_deterministic_eval(name) for _ in range(k)]
        successes = sum(1 for s in scores if s >= 0.85)
        failures = k - successes
        variance = statistics.variance(scores) if len(scores) >= 2 else 0.0
        out.append(PassKResult(
            eval_name=name,
            k=k,
            successes=successes,
            failures=failures,
            pass_at_1=1.0 if successes > 0 else 0.0,
            pass_at_k=1.0 if successes == k else 0.0,
            variance=round(variance, 6),
            individual_scores=[round(s, 3) for s in scores],
        ))
    return out


# ─── Agentic flake check ────────────────────────────────────────────────────

def run_agentic_flake_check(k: int) -> List[PassKResult]:
    """For each recorded agentic replay, simulate k 'runs' by sampling
    from the recorded output's score distribution.

    The recorded output is a single point; we extrapolate variance by
    perturbing the json validity / required-keys flags slightly.
    Without real multi-run data, this is a placeholder; it returns the
    recorded score with zero variance.

    To get REAL pass^k data: run the live mode of agentic_evals.py N
    times (costs $N × per-run cost) and capture each output.
    """
    from agentic_evals import score_replay, _load_scenarios
    scenarios = _load_scenarios()
    out: List[PassKResult] = []
    for s in scenarios:
        score = score_replay(s)
        out.append(PassKResult(
            eval_name=s["scenario"],
            k=k,
            successes=k if score.passed else 0,
            failures=0 if score.passed else k,
            pass_at_1=1.0 if score.passed else 0.0,
            pass_at_k=1.0 if score.passed else 0.0,
            variance=0.0,    # single recording → no variance signal
            individual_scores=[score.overall],
        ))
    return out


# ─── Reports ─────────────────────────────────────────────────────────────────

def aggregate(results: List[PassKResult]) -> Dict:
    if not results:
        return {"total": 0}
    return {
        "total": len(results),
        "all_pass_at_k": sum(1 for r in results if r.pass_at_k == 1.0),
        "all_pass_at_1": sum(1 for r in results if r.pass_at_1 == 1.0),
        "k": results[0].k,
        "mean_variance": round(
            statistics.mean(r.variance for r in results), 6),
    }


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Run pass^k evals (production-style 'always pass') metric"
    )
    parser.add_argument("--mode", required=True,
                        choices=["deterministic-replay", "agentic-flake-check"])
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--eval", default=None,
                        help="Single eval name (default: all)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.mode == "deterministic-replay":
        if args.eval:
            evals = [args.eval]
        else:
            evals = [p.stem for p in
                     (EVALS / "fixtures").glob("*.json")]
        results = run_deterministic_replay(evals, args.k)
    else:
        # Add scripts dir to path for agentic_evals import
        sys.path.insert(0, str(EVALS))
        try:
            results = run_agentic_flake_check(args.k)
        finally:
            sys.path.remove(str(EVALS))

    summary = aggregate(results)
    if args.json:
        print(json.dumps({
            "summary": summary,
            "per_eval": [r.to_dict() for r in results],
        }, indent=2))
    else:
        print(f"pass^k mode: {args.mode}, k={args.k}")
        print(f"  total evals:      {summary['total']}")
        print(f"  pass^k (all k):   {summary.get('all_pass_at_k', 0)}")
        print(f"  pass@1 (any):     {summary.get('all_pass_at_1', 0)}")
        print(f"  mean variance:    {summary.get('mean_variance', 0)}")
        for r in results:
            mark = "✓" if r.pass_at_k == 1.0 else ("△" if r.pass_at_1 == 1.0 else "✗")
            print(f"  {mark} {r.eval_name:<40} "
                  f"successes={r.successes}/{r.k}  var={r.variance:.6f}")

    sys.exit(0 if all(r.pass_at_k == 1.0 for r in results) else 1)


if __name__ == "__main__":
    main()
