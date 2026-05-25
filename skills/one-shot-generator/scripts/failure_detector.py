#!/usr/bin/env python3
"""
Failure Detector — v1.0.0

Tracks consecutive failures and provides rollback trigger for autonomous recovery.
Maintains state in ``.beads/failures_state.jsonl`` with one JSON object per line.

Failure state tracks:
  - consecutive_failures: count of failures in a row
  - last_failing_spec: hash of the spec that failed
  - last_failure_ts: ISO 8601 timestamp of last failure

CLI:
    python failure_detector.py --action record --spec-hash abc123def456
    python failure_detector.py --action reset
    python failure_detector.py --action should-trigger --threshold 3
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Dict, Optional

from lib.base_script import bootstrap_runtime, setup_logging
bootstrap_runtime()

logger = setup_logging(__name__)


def _get_failures_state_path() -> Path:
    """Locate .beads/failures_state.jsonl, walking up from cwd."""
    cur = Path.cwd().resolve()
    while cur != cur.parent:
        beads_dir = cur / ".beads"
        if beads_dir.exists():
            return beads_dir / "failures_state.jsonl"
        cur = cur.parent
    # Fallback: create in current .beads if it exists
    default = Path.cwd().resolve() / ".beads" / "failures_state.jsonl"
    return default


def load_failure_state(repo_root: Optional[Path] = None) -> Dict:
    """Load failure tracking state from .beads/failures_state.jsonl.

    Returns the most recent state record as a dict:
      {
        "consecutive_failures": N (int),
        "last_failing_spec": str or None,
        "last_failure_ts": ISO 8601 str or None
      }

    Default (no file or empty file): consecutive_failures=0, others=None.
    """
    if repo_root:
        state_path = repo_root / ".beads" / "failures_state.jsonl"
    else:
        state_path = _get_failures_state_path()

    if not state_path.exists():
        return {
            "consecutive_failures": 0,
            "last_failing_spec": None,
            "last_failure_ts": None,
        }

    try:
        lines = state_path.read_text(encoding="utf-8").splitlines()
        if not lines:
            return {
                "consecutive_failures": 0,
                "last_failing_spec": None,
                "last_failure_ts": None,
            }
        # Take last line as current state
        last_line = lines[-1].strip()
        if not last_line:
            return {
                "consecutive_failures": 0,
                "last_failing_spec": None,
                "last_failure_ts": None,
            }
        return json.loads(last_line)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Failed to load failure state: %s. Resetting.", e)
        return {
            "consecutive_failures": 0,
            "last_failing_spec": None,
            "last_failure_ts": None,
        }


def record_failure(spec_hash: str, repo_root: Optional[Path] = None) -> int:
    """Record a failure, increment counter.

    Args:
        spec_hash: Hash or ID of the failing spec
        repo_root: Optional repo root (auto-discovered if None)

    Returns:
        New consecutive failure count
    """
    if repo_root:
        state_path = repo_root / ".beads" / "failures_state.jsonl"
    else:
        state_path = _get_failures_state_path()

    # Ensure directory exists
    state_path.parent.mkdir(parents=True, exist_ok=True)

    # Load current state
    state = load_failure_state(repo_root=repo_root)

    # Increment
    state["consecutive_failures"] = state.get("consecutive_failures", 0) + 1
    state["last_failing_spec"] = spec_hash
    state["last_failure_ts"] = dt.datetime.now(dt.timezone.utc).replace(
        microsecond=0
    ).isoformat() + "Z"

    # Append to file
    try:
        with state_path.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(state) + "\n")
        logger.info(
            "recorded failure: spec_hash=%s, consecutive_count=%d",
            spec_hash,
            state["consecutive_failures"],
        )
    except OSError as e:
        logger.error("Failed to record failure: %s", e)
        raise

    return state["consecutive_failures"]


def reset_failure_counter(repo_root: Optional[Path] = None) -> None:
    """Reset failure counter on success.

    Writes a new state record with consecutive_failures=0.
    """
    if repo_root:
        state_path = repo_root / ".beads" / "failures_state.jsonl"
    else:
        state_path = _get_failures_state_path()

    # Ensure directory exists
    state_path.parent.mkdir(parents=True, exist_ok=True)

    state = {
        "consecutive_failures": 0,
        "last_failing_spec": None,
        "last_failure_ts": None,
    }

    try:
        with state_path.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(state) + "\n")
        logger.info("reset failure counter")
    except OSError as e:
        logger.error("Failed to reset failure counter: %s", e)
        raise


def should_trigger_rollback(threshold: int = 3,
                           repo_root: Optional[Path] = None) -> bool:
    """Check if consecutive failures >= threshold.

    Args:
        threshold: Number of consecutive failures to trigger rollback (default: 3)
        repo_root: Optional repo root (auto-discovered if None)

    Returns:
        True if consecutive_failures >= threshold, else False
    """
    state = load_failure_state(repo_root=repo_root)
    result = state.get("consecutive_failures", 0) >= threshold
    logger.info(
        "rollback check: %d >= %d -> %s",
        state.get("consecutive_failures", 0),
        threshold,
        result,
    )
    return result


# ─── CLI ─────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Track consecutive failures and manage rollback trigger"
    )
    parser.add_argument(
        "--action",
        required=True,
        choices=["record", "reset", "should-trigger", "status"],
        help="Action to perform",
    )
    parser.add_argument(
        "--spec-hash",
        default=None,
        help="Spec hash to record (required for 'record' action)",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=3,
        help="Consecutive failure threshold for rollback trigger (default: 3)",
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Plugin repo root (auto-discovered if not provided)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON output",
    )
    args = parser.parse_args()

    repo_root = None
    if args.repo_root:
        repo_root = Path(args.repo_root).resolve()

    try:
        if args.action == "record":
            if not args.spec_hash:
                print("Error: --spec-hash required for 'record' action", file=sys.stderr)
                sys.exit(1)
            count = record_failure(args.spec_hash, repo_root=repo_root)
            if args.json:
                print(json.dumps({"action": "record", "consecutive_failures": count}))
            else:
                print(f"Recorded failure. Consecutive count: {count}")

        elif args.action == "reset":
            reset_failure_counter(repo_root=repo_root)
            if args.json:
                print(json.dumps({"action": "reset", "consecutive_failures": 0}))
            else:
                print("Failure counter reset.")

        elif args.action == "should-trigger":
            trigger = should_trigger_rollback(threshold=args.threshold, repo_root=repo_root)
            if args.json:
                print(
                    json.dumps(
                        {
                            "action": "should-trigger",
                            "threshold": args.threshold,
                            "trigger": trigger,
                        }
                    )
                )
            else:
                state = load_failure_state(repo_root=repo_root)
                print(
                    f"Consecutive failures: {state['consecutive_failures']} / "
                    f"Threshold: {args.threshold}"
                )
                print(f"Trigger rollback: {trigger}")

        elif args.action == "status":
            state = load_failure_state(repo_root=repo_root)
            if args.json:
                print(json.dumps({"action": "status", "state": state}))
            else:
                print(f"Status: {json.dumps(state, indent=2)}")

    except Exception as e:
        logger.error("Action failed: %s", e)
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
