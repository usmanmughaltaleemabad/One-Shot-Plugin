#!/usr/bin/env python3
"""
Cost Stats — aggregates `.beads/cost_observations.jsonl` into a calibration report.

The plugin already records per-agent token counts to ``.beads/cost_observations.jsonl``
via ``cost_budget.observe_agent_call``. ``cost_calibrator.py`` reads that log to
recalibrate the per-agent hardcoded estimates.

This script is the *user-facing* side: it summarises what the log says today so
the calibration confidence number in the README can be backed by data instead of
asserted by hand.

Output (JSON or human-readable):

    {
      "samples": 6,
      "agents": {
        "architect": {"runs": 6, "tokens_p50": 27200, "tokens_p95": 28700, "cost_usd_p50": 0.0944}
      },
      "confidence": "low",
      "confidence_reason": "fewer than 20 samples; estimates are directional",
      "recommendation": "accumulate observations from real /one-shot runs"
    }

CLI:
    cost_stats.py                # human-readable report
    cost_stats.py --json         # JSON for CI / dashboards
    cost_stats.py --by-agent     # only emit per-agent breakdown

Pricing constants are taken from cost_budget.PRICING_USD; if cost_budget cannot
be imported (running outside the plugin), an inline copy is used.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path
from typing import Any

# Pricing fallback if cost_budget isn't importable. Updated 2026-05-25.
# Numbers are $/1M tokens, separated by tier.
_PRICING_FALLBACK = {
    "haiku":  {"input": 0.80,  "output": 4.00},
    "sonnet": {"input": 3.00,  "output": 15.00},
    "opus":   {"input": 15.00, "output": 75.00},
}

_OBS_LOG = Path(".beads/cost_observations.jsonl")

# Confidence thresholds — how many real samples are required before
# we stop calling the estimates directional.
_CONFIDENCE_LOW   = 20
_CONFIDENCE_MED   = 50
_CONFIDENCE_HIGH  = 100


def _load_pricing() -> dict:
    try:
        sys.path.insert(0, "skills/one-shot-generator/scripts")
        from cost_budget import PRICING_USD  # type: ignore
        return PRICING_USD
    except Exception:
        return _PRICING_FALLBACK


def _load_observations(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out: list[dict] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def _cost_usd(obs: dict, pricing: dict) -> float | None:
    model = (obs.get("model") or "").lower()
    if model not in pricing:
        return None
    inp = obs.get("input") or 0
    out = obs.get("output") or 0
    p = pricing[model]
    return (inp / 1_000_000) * p["input"] + (out / 1_000_000) * p["output"]


def _percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    return float(statistics.quantiles(values + values, n=100)[int(q) - 1]) \
        if len(values) >= 2 else float(values[0])


def _confidence(n_samples: int) -> tuple[str, str]:
    if n_samples >= _CONFIDENCE_HIGH:
        return "high", "100+ real samples; estimates are statistically robust"
    if n_samples >= _CONFIDENCE_MED:
        return "medium", "50+ real samples; estimates are reasonably stable"
    if n_samples >= _CONFIDENCE_LOW:
        return "low-medium", "20+ samples; estimates are directional but improving"
    if n_samples > 0:
        return "low", f"fewer than {_CONFIDENCE_LOW} samples; estimates are directional"
    return "none", "no observations recorded; defaults are hardcoded estimates only"


def build_report(observations: list[dict], pricing: dict) -> dict[str, Any]:
    """Aggregate observations into a calibration report."""
    by_agent: dict[str, list[dict]] = {}
    for obs in observations:
        by_agent.setdefault(obs.get("agent", "unknown"), []).append(obs)

    per_agent: dict[str, dict[str, Any]] = {}
    for agent, runs in by_agent.items():
        tokens = [(r.get("input") or 0) + (r.get("output") or 0) for r in runs]
        costs = [c for c in (_cost_usd(r, pricing) for r in runs) if c is not None]
        per_agent[agent] = {
            "runs": len(runs),
            "tokens_p50": round(statistics.median(tokens), 0) if tokens else 0,
            "tokens_p95": round(_percentile(sorted(tokens), 95), 0) if tokens else 0,
            "cost_usd_p50": round(statistics.median(costs), 4) if costs else None,
            "cost_usd_p95": round(_percentile(sorted(costs), 95), 4) if costs else None,
        }

    confidence, reason = _confidence(len(observations))

    return {
        "samples": len(observations),
        "agents": per_agent,
        "confidence": confidence,
        "confidence_reason": reason,
        "recommendation": (
            "ship as-is"
            if confidence == "high"
            else "accumulate observations from real /one-shot runs"
        ),
        "observations_log": str(_OBS_LOG),
    }


def _print_human(report: dict) -> None:
    print(f"Cost calibration report (samples: {report['samples']})")
    print(f"Confidence: {report['confidence']} — {report['confidence_reason']}")
    print()
    if not report["agents"]:
        print("(no observations recorded yet)")
        print(f"Recommendation: {report['recommendation']}")
        return
    print(f"{'agent':<15} {'runs':>5} {'tokens p50':>12} {'tokens p95':>12} "
          f"{'$ p50':>8} {'$ p95':>8}")
    for agent, stats in sorted(report["agents"].items()):
        cost_p50 = f"${stats['cost_usd_p50']:.4f}" if stats["cost_usd_p50"] is not None else "n/a"
        cost_p95 = f"${stats['cost_usd_p95']:.4f}" if stats["cost_usd_p95"] is not None else "n/a"
        print(f"{agent:<15} {stats['runs']:>5} {stats['tokens_p50']:>12,.0f} "
              f"{stats['tokens_p95']:>12,.0f} {cost_p50:>8} {cost_p95:>8}")
    print()
    print(f"Recommendation: {report['recommendation']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument("--by-agent", action="store_true",
                        help="JSON: only the per-agent map (no confidence wrapper)")
    parser.add_argument("--observations", type=Path, default=_OBS_LOG,
                        help=f"observations log (default: {_OBS_LOG})")
    args = parser.parse_args(argv)

    observations = _load_observations(args.observations)
    pricing = _load_pricing()
    report = build_report(observations, pricing)

    if args.by_agent:
        print(json.dumps(report["agents"], indent=2))
    elif args.json:
        print(json.dumps(report, indent=2))
    else:
        _print_human(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
