#!/usr/bin/env python3
"""
Performance Profiler — Tier 7A (Autonomous Performance Tuning)

Wraps any deterministic script in cProfile and records per-function
p50/p95 latencies to ``.beads/perf_observations.jsonl``. After enough
observations accumulate, ``perf_tuner.py`` reads the log and proposes
optimisations (parallelism levels, cache splits, batch sizes).

Two modes:

  profile-once   Single profiling run; useful for ad-hoc inspection.
                 ``python perf_profiler.py profile-once \\
                     --script extract_domain_model.py \\
                     -- "shopping cart with line items"``

  recalibrate    Recompute p50/p95 from the observation log; emit a
                 summary table.

CLI:
    perf_profiler.py profile-once --script <name> -- <script-args>
    perf_profiler.py recalibrate
    perf_profiler.py top-funcs --limit 20
"""

from __future__ import annotations

import argparse
import cProfile
import datetime as dt
import io
import json
import pstats
import statistics
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from lib.base_script import bootstrap_runtime, setup_logging
bootstrap_runtime()

logger = setup_logging(__name__)


OBS_PATH = Path(".beads/perf_observations.jsonl")


@dataclass
class PerfObservation:
    ts: str
    script: str
    duration_ms: float
    top_functions: List[Dict]    # [{func: str, cumtime_ms: float, calls: int}]
    args_summary: str

    def to_dict(self) -> Dict:
        return asdict(self)


# ─── Profiling ──────────────────────────────────────────────────────────────

def profile_once(script_path: Path, script_args: List[str],
                 top_n: int = 10) -> PerfObservation:
    """Run a script under cProfile and return structured perf data."""
    import time
    profiler = cProfile.Profile()
    start = time.perf_counter()

    # We can't import + exec arbitrary scripts safely. Use subprocess
    # with cProfile invocation via -m.
    try:
        cmd = [sys.executable, "-m", "cProfile", "-o", "/dev/stdout",
               str(script_path), *script_args]
        if sys.platform == "win32":
            # /dev/stdout doesn't work; use a tempfile
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".prof", delete=False) as tmpf:
                tmp_path = tmpf.name
            cmd = [sys.executable, "-m", "cProfile", "-o", tmp_path,
                   str(script_path), *script_args]
            subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            stats = pstats.Stats(tmp_path)
            Path(tmp_path).unlink(missing_ok=True)
        else:
            proc = subprocess.run(cmd, capture_output=True, timeout=120)
            stats = pstats.Stats(io.BytesIO(proc.stdout))
    except subprocess.TimeoutExpired:
        return PerfObservation(
            ts=dt.datetime.now(dt.timezone.utc).replace(
                microsecond=0, tzinfo=None).isoformat() + "Z",
            script=str(script_path),
            duration_ms=120000,
            top_functions=[{"func": "<timeout>", "cumtime_ms": 120000, "calls": 0}],
            args_summary=" ".join(script_args)[:100],
        )

    duration_ms = (time.perf_counter() - start) * 1000

    # Extract top functions by cumtime
    stats.sort_stats("cumulative")
    top_funcs: List[Dict] = []
    for (file_str, line, fname), (cc, nc, tt, ct, callers) in list(
            stats.stats.items())[:top_n]:
        if "<frozen" in str(file_str) or "__init__" in fname:
            continue
        top_funcs.append({
            "func": f"{Path(file_str).name}:{fname}",
            "cumtime_ms": round(ct * 1000, 2),
            "calls": nc,
        })

    return PerfObservation(
        ts=dt.datetime.now(dt.timezone.utc).replace(
            microsecond=0, tzinfo=None).isoformat() + "Z",
        script=str(script_path),
        duration_ms=round(duration_ms, 2),
        top_functions=top_funcs[:top_n],
        args_summary=" ".join(script_args)[:100],
    )


def _record(repo_root: Path, observation: PerfObservation) -> None:
    path = repo_root / OBS_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(observation.to_dict()) + "\n")


def _load_obs(repo_root: Path) -> List[PerfObservation]:
    path = repo_root / OBS_PATH
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            data = json.loads(line)
            out.append(PerfObservation(**data))
        except (json.JSONDecodeError, TypeError):
            continue
    return out


def recalibrate(repo_root: Path) -> Dict[str, Dict[str, float]]:
    """Compute p50/p95 per script from observation log."""
    obs = _load_obs(repo_root)
    by_script: Dict[str, List[float]] = {}
    for o in obs:
        by_script.setdefault(o.script, []).append(o.duration_ms)

    out: Dict[str, Dict[str, float]] = {}
    for script, durations in by_script.items():
        if not durations:
            continue
        durations_sorted = sorted(durations)
        p50 = statistics.median(durations_sorted)
        p95 = durations_sorted[int(len(durations_sorted) * 0.95)] \
            if len(durations_sorted) >= 2 else durations_sorted[-1]
        out[script] = {
            "samples": len(durations_sorted),
            "p50_ms": round(p50, 2),
            "p95_ms": round(p95, 2),
            "max_ms": round(max(durations_sorted), 2),
            "min_ms": round(min(durations_sorted), 2),
        }
    return out


def top_functions_across_runs(repo_root: Path, limit: int = 20) -> List[Dict]:
    obs = _load_obs(repo_root)
    aggregate: Dict[str, Dict[str, float]] = {}
    for o in obs:
        for fn in o.top_functions:
            key = fn["func"]
            agg = aggregate.setdefault(key, {"cumtime_ms": 0.0, "calls": 0})
            agg["cumtime_ms"] += fn.get("cumtime_ms", 0)
            agg["calls"] += fn.get("calls", 0)
    items = sorted(aggregate.items(),
                   key=lambda kv: kv[1]["cumtime_ms"], reverse=True)
    return [{"func": k, **v} for k, v in items[:limit]]


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Profile + tune plugin scripts")
    parser.add_argument("--repo-root", default=".")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sp_p = sub.add_parser("profile-once")
    sp_p.add_argument("--script", required=True, help="Path under skills/...")
    sp_p.add_argument("--no-record", action="store_true",
                      help="Don't append to perf_observations.jsonl")
    sp_p.add_argument("--top", type=int, default=10)
    sp_p.add_argument("script_args", nargs=argparse.REMAINDER)

    sub.add_parser("recalibrate")
    sp_t = sub.add_parser("top-funcs")
    sp_t.add_argument("--limit", type=int, default=20)

    args = parser.parse_args()
    repo = Path(args.repo_root).resolve()

    if args.cmd == "profile-once":
        script_path = Path(args.script)
        if not script_path.is_absolute():
            script_path = repo / args.script
        script_args = list(args.script_args)
        if script_args and script_args[0] == "--":
            script_args = script_args[1:]
        obs = profile_once(script_path, script_args, top_n=args.top)
        if not args.no_record:
            _record(repo, obs)
        print(json.dumps(obs.to_dict(), indent=2))
        return

    if args.cmd == "recalibrate":
        stats = recalibrate(repo)
        print(json.dumps(stats, indent=2))
        return

    if args.cmd == "top-funcs":
        top = top_functions_across_runs(repo, limit=args.limit)
        print(json.dumps(top, indent=2))
        return


if __name__ == "__main__":
    main()
