#!/usr/bin/env python3
"""
Doubt Driver — v1.0.0  (Stage 5.5 — Doubt-Driven Development)

After the reviewer passes, spawn a FRESH-CONTEXT doubter agent for each
generated artifact. The doubter sees only the artifact + contract — not
the spec's reasoning, the implementer's notes, or the reviewer's verdict.
That information withholding is the point: it prevents agreement bias.

This script is the deterministic enforcement layer:
  - tracks per-artifact doubt iterations (max 2)
  - classifies findings by precedence (contract_violation > actionable_gap > ...)
  - decides PROCEED (PASS or only accepted_tradeoff/noise findings) vs
    LOOP_TO_IMPLEMENTER (any contract_violation OR actionable_gap)
  - prevents doubt theater: same findings across 2 rounds → escalate

Inspired by Addy Osmani's doubt-driven-development skill.

Pattern (same shape as critic_loop_driver):

    doubt_driver.py init    --sandbox <dir>
    doubt_driver.py record  --sandbox <dir> --artifact <path> --verdict <json>
    doubt_driver.py summary --sandbox <dir>

State file: <sandbox>/.osp-doubt-state.json

Decision values returned by `record`:
  PROCEED              — artifact passes doubt; advance to next stage
  LOOP_TO_IMPLEMENTER  — find serious gap; re-spawn implementer with findings
  ESCALATE             — max rounds hit OR same gap re-found OR doubt theater
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from lib.base_script import bootstrap_runtime, setup_logging
bootstrap_runtime()
logger = setup_logging(__name__)


MAX_DOUBT_ROUNDS_PER_ARTIFACT = 2
STATE_FILENAME = ".osp-doubt-state.json"

# Severity precedence — only these two block PROCEED.
BLOCKING = {"contract_violation", "actionable_gap"}


def _state_path(sandbox: Path) -> Path:
    return sandbox / STATE_FILENAME


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read_state(sandbox: Path) -> Dict[str, Any]:
    p = _state_path(sandbox)
    if not p.exists():
        raise FileNotFoundError(
            f"doubt state not found at {p}. Call doubt_driver.py init first."
        )
    return json.loads(p.read_text(encoding="utf-8"))


def _write_state(sandbox: Path, state: Dict[str, Any]) -> None:
    _state_path(sandbox).write_text(json.dumps(state, indent=2), encoding="utf-8")


def init(sandbox: Path) -> Dict[str, Any]:
    sandbox.mkdir(parents=True, exist_ok=True)
    state = {
        "started_at": _now_iso(),
        "max_rounds_per_artifact": MAX_DOUBT_ROUNDS_PER_ARTIFACT,
        "artifacts": {},   # artifact_path -> { rounds: [...] }
    }
    _write_state(sandbox, state)
    return state


def _classify(findings: List[Dict[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = defaultdict(int)
    for f in findings:
        sev = f.get("severity", "noise")
        counts[sev] += 1
    return dict(counts)


def _findings_fingerprint(findings: List[Dict[str, Any]]) -> set:
    """A fingerprint set for cross-round comparison — `where + what` pairs.
    If round N+1 reports the SAME pairs as round N, the implementer didn't
    address anything → doubt theater → escalate."""
    return {
        (f.get("where", ""), f.get("what", "")[:80])
        for f in findings
        if f.get("severity") in BLOCKING
    }


def record(sandbox: Path, artifact: str, verdict: Dict[str, Any]) -> Dict[str, Any]:
    state = _read_state(sandbox)
    raw = (verdict.get("verdict") or "").upper()
    findings = list(verdict.get("findings", []))

    counts = _classify(findings)
    blocking_count = sum(counts.get(s, 0) for s in BLOCKING)

    artifact_entry = state["artifacts"].setdefault(artifact, {"rounds": []})
    round_n = len(artifact_entry["rounds"]) + 1

    entry = {
        "round": round_n,
        "recorded_at": _now_iso(),
        "verdict": raw,
        "counts": counts,
        "blocking_count": blocking_count,
        "fingerprint": sorted(_findings_fingerprint(findings)),
        "findings": findings,
    }
    artifact_entry["rounds"].append(entry)
    _write_state(sandbox, state)

    # PASS verdict with no blocking findings → PROCEED.
    if raw == "PASS" and blocking_count == 0:
        return {
            "decision": "PROCEED",
            "artifact": artifact,
            "round": round_n,
            "reason": "no_blocking_findings",
            "counts": counts,
        }

    # Always PROCEED if no blocking findings — doubter may have flagged
    # only noise / accepted_tradeoffs.
    if blocking_count == 0:
        return {
            "decision": "PROCEED",
            "artifact": artifact,
            "round": round_n,
            "reason": "only_noise_or_tradeoffs",
            "counts": counts,
        }

    # Doubt theater detection runs BEFORE the iteration cap so the
    # reason field is precise: "same findings twice" is more actionable
    # than "you hit the cap".
    if round_n >= 2:
        prior = artifact_entry["rounds"][-2]
        if entry["fingerprint"] and set(map(tuple, prior["fingerprint"])) == set(map(tuple, entry["fingerprint"])):
            return {
                "decision": "ESCALATE",
                "artifact": artifact,
                "round": round_n,
                "reason": "doubt_theater_same_findings",
                "counts": counts,
                "blocking_findings": [f for f in findings
                                      if f.get("severity") in BLOCKING],
            }

    # Hit the cap — escalate.
    if round_n >= MAX_DOUBT_ROUNDS_PER_ARTIFACT:
        return {
            "decision": "ESCALATE",
            "artifact": artifact,
            "round": round_n,
            "reason": "max_doubt_rounds_reached",
            "counts": counts,
            "blocking_findings": [f for f in findings
                                  if f.get("severity") in BLOCKING],
        }

    return {
        "decision": "LOOP_TO_IMPLEMENTER",
        "artifact": artifact,
        "round": round_n,
        "reason": "blocking_findings_present",
        "counts": counts,
        "blocking_findings": [f for f in findings
                              if f.get("severity") in BLOCKING],
    }


def summary(sandbox: Path) -> Dict[str, Any]:
    state = _read_state(sandbox)
    artifacts = state["artifacts"]
    out: List[Dict[str, Any]] = []
    total_rounds = 0
    total_blocking_resolved = 0
    for path, entry in artifacts.items():
        rounds = entry["rounds"]
        if not rounds:
            continue
        total_rounds += len(rounds)
        first_blocking = rounds[0]["blocking_count"]
        final_blocking = rounds[-1]["blocking_count"]
        total_blocking_resolved += max(0, first_blocking - final_blocking)
        out.append({
            "artifact": path,
            "rounds_used": len(rounds),
            "first_round_blocking": first_blocking,
            "final_round_blocking": final_blocking,
            "verdict": rounds[-1]["verdict"],
        })
    return {
        "started_at": state["started_at"],
        "total_artifacts": len(out),
        "total_rounds": total_rounds,
        "total_blocking_resolved": total_blocking_resolved,
        "per_artifact": out,
    }


# ─── CLI ────────────────────────────────────────────────────────────────────

def _parse(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Doubt-driven Stage 5.5 driver.")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init")
    p_init.add_argument("--sandbox", required=True, type=Path)

    p_rec = sub.add_parser("record")
    p_rec.add_argument("--sandbox", required=True, type=Path)
    p_rec.add_argument("--artifact", required=True,
                       help="Path of the artifact being doubted")
    p_rec.add_argument("--verdict", required=True, type=Path,
                       help="Path to JSON file containing the doubter's verdict")

    p_sum = sub.add_parser("summary")
    p_sum.add_argument("--sandbox", required=True, type=Path)

    return p.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = _parse(argv if argv is not None else sys.argv[1:])
    if args.cmd == "init":
        result = init(args.sandbox)
    elif args.cmd == "record":
        if not args.verdict.exists():
            print(f"verdict file not found: {args.verdict}", file=sys.stderr)
            return 2
        verdict = json.loads(args.verdict.read_text(encoding="utf-8"))
        result = record(args.sandbox, args.artifact, verdict)
    elif args.cmd == "summary":
        result = summary(args.sandbox)
    else:
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
