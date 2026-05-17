#!/usr/bin/env python3
"""
Beads Auto-Writer — v0.8.0

Whenever a generator or verification step fails, drop a structured record
into ``.beads/failures.jsonl`` so future sessions know what went wrong and
can attempt to avoid the same mistake.

Each bead is a single JSON line with shape::

    {
        "id": "bd-fail-20260517-001",
        "ts": "2026-05-17T20:43:11Z",
        "phase": "phase2",
        "task": "add product CRUD",
        "project": "/path/to/fastapi-shop",
        "kind": "verification_warning",
        "diagnostics": [...],
        "resolved": false
    }

CLI:
    python beads_writer.py --phase phase2 \\
        --task "add product CRUD" \\
        --project /tmp/x \\
        --kind verification_warning \\
        --diagnostics path/to/report.json
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

from lib.base_script import bootstrap_runtime, setup_logging
bootstrap_runtime()

logger = setup_logging(__name__)


def _next_id(failures_path: Path) -> str:
    today = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d")
    count = 0
    if failures_path.exists():
        for line in failures_path.read_text(encoding="utf-8").splitlines():
            try:
                rec = json.loads(line)
                if rec.get("id", "").startswith(f"bd-fail-{today}"):
                    count += 1
            except json.JSONDecodeError:
                continue
    return f"bd-fail-{today}-{count + 1:03d}"


def record_failure(*, repo_root: Path, phase: str, task: str,
                   project: Optional[str], kind: str,
                   diagnostics: List[Dict]) -> Dict:
    failures_path = repo_root / ".beads" / "failures.jsonl"
    failures_path.parent.mkdir(parents=True, exist_ok=True)
    bead = {
        "id": _next_id(failures_path),
        "ts": dt.datetime.now(dt.timezone.utc).replace(microsecond=0, tzinfo=None).isoformat() + "Z",
        "phase": phase,
        "task": task,
        "project": project,
        "kind": kind,
        "diagnostics": diagnostics,
        "resolved": False,
    }
    with failures_path.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(bead) + "\n")
    logger.info("recorded bead %s in %s", bead["id"], failures_path)
    return bead


def main():
    parser = argparse.ArgumentParser(
        description="Record a generator/verification failure as a bead"
    )
    parser.add_argument("--repo-root", default=None,
                        help="Plugin repo root (default: walk up from cwd)")
    parser.add_argument("--phase", required=True)
    parser.add_argument("--task", required=True)
    parser.add_argument("--project", default=None)
    parser.add_argument("--kind", default="verification_warning",
                        help="generator_crash | verification_error | verification_warning")
    parser.add_argument("--diagnostics",
                        help="Path to JSON file with a list of diagnostic dicts")
    args = parser.parse_args()

    if args.repo_root:
        repo_root = Path(args.repo_root).resolve()
    else:
        # Walk up looking for .beads/
        cur = Path.cwd().resolve()
        while cur != cur.parent and not (cur / ".beads").exists():
            cur = cur.parent
        repo_root = cur

    diags: List[Dict] = []
    if args.diagnostics:
        diag_path = Path(args.diagnostics)
        raw = json.loads(diag_path.read_text(encoding="utf-8"))
        diags = raw if isinstance(raw, list) else raw.get("diagnostics", [])

    bead = record_failure(repo_root=repo_root, phase=args.phase, task=args.task,
                          project=args.project, kind=args.kind,
                          diagnostics=diags)
    print(json.dumps(bead, indent=2))


if __name__ == "__main__":
    main()
