#!/usr/bin/env python3
"""
Curriculum Status — reports the state of the self-learning loop.

The plugin has two curriculum files:

  .claude/registry/curriculum_seed.jsonl   — hand-curated, ships with the plugin
  .beads/curriculum.jsonl                  — runtime-accumulated from /one-shot runs
                                             (written by /dream, stage 8.5)

This script answers the question: "is the learning loop alive?"

Output:
    {
      "seed_entries": 10,
      "runtime_entries": 4,
      "total": 14,
      "runtime_share": 0.286,
      "loop_status": "warming",
      "newest_runtime": "2026-05-18T...",
      "topics_covered": ["FK type mismatch", "pagination envelope", ...]
    }

Loop status semantics:
  - "cold":    runtime_entries == 0; only seeds are in play
  - "warming": 1-19 runtime entries; loop is alive but underfit
  - "active":  20-99 runtime entries; advice meaningfully data-driven
  - "mature":  100+ runtime entries

CLI:
    curriculum_status.py            # human-readable
    curriculum_status.py --json     # machine-readable
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SEED_PATH    = Path(".claude/registry/curriculum_seed.jsonl")
RUNTIME_PATH = Path(".beads/curriculum.jsonl")


def _load(path: Path) -> list[dict]:
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


def _status(runtime_count: int) -> str:
    if runtime_count == 0:
        return "cold"
    if runtime_count < 20:
        return "warming"
    if runtime_count < 100:
        return "active"
    return "mature"


def build_status(seed_path: Path = SEED_PATH, runtime_path: Path = RUNTIME_PATH) -> dict:
    seeds = _load(seed_path)
    runtime = _load(runtime_path)

    total = len(seeds) + len(runtime)
    share = round(len(runtime) / total, 3) if total else 0.0

    newest = ""
    for r in runtime:
        ts = r.get("timestamp") or r.get("ts") or r.get("created_at") or ""
        if ts and ts > newest:
            newest = ts

    # Lightweight "topic" extraction — first 50 chars of the reason field
    topics = []
    seen: set[str] = set()
    for entry in seeds + runtime:
        topic = (entry.get("reason") or entry.get("task_text") or "")[:60]
        if topic and topic not in seen:
            seen.add(topic)
            topics.append(topic)
    topics = topics[:10]

    return {
        "seed_entries": len(seeds),
        "runtime_entries": len(runtime),
        "total": total,
        "runtime_share": share,
        "loop_status": _status(len(runtime)),
        "newest_runtime": newest or None,
        "topics_covered": topics,
        "seed_path": str(seed_path),
        "runtime_path": str(runtime_path),
    }


def _print_human(s: dict) -> None:
    print(f"Curriculum status: {s['loop_status'].upper()}")
    print(f"  Seed entries:    {s['seed_entries']}  ({s['seed_path']})")
    print(f"  Runtime entries: {s['runtime_entries']}  ({s['runtime_path']})")
    print(f"  Runtime share:   {s['runtime_share']:.1%}")
    if s["newest_runtime"]:
        print(f"  Newest runtime:  {s['newest_runtime']}")
    print()
    if s["topics_covered"]:
        print("Topics covered (top 10):")
        for t in s["topics_covered"]:
            print(f"  - {t}")
    print()
    next_step = {
        "cold":    "Run /one-shot a few times and let /dream populate .beads/curriculum.jsonl.",
        "warming": "Continue real /one-shot usage; loop is alive but underfit.",
        "active":  "Curriculum is data-driven; advice should be meaningful.",
        "mature":  "Curriculum is mature; periodic re-distillation recommended.",
    }[s["loop_status"]]
    print(f"Next step: {next_step}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--seed", type=Path, default=SEED_PATH)
    parser.add_argument("--runtime", type=Path, default=RUNTIME_PATH)
    args = parser.parse_args(argv)

    status = build_status(args.seed, args.runtime)
    if args.json:
        print(json.dumps(status, indent=2))
    else:
        _print_human(status)
    return 0


if __name__ == "__main__":
    sys.exit(main())
