#!/usr/bin/env python3
"""
Failure Predictor — v1.0.0

Emits hard warnings when a task is likely to fail based on curriculum similarity.
Uses embedding-based prediction to detect risky tasks before execution.

Failure warnings include:
  - Similarity score to past failures
  - Reason the similar task failed
  - Mitigation suggestions from curriculum
  - Action items: --review flag, --templated fallback, --budget=0.50

Usage:
    from failure_predictor import check_task_safety

    safe, msg = check_task_safety("shopping cart with discounts")
    if not safe:
        print(msg)
        sys.exit(1)

CLI:
    python failure_predictor.py "add payment processing to checkout"
    python failure_predictor.py "build user auth" --threshold 0.75 --json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Tuple

from curriculum_v2 import load_curriculum, predict_failure


def format_hard_warning(prediction) -> str:
    """Format a hard warning message with actionable items.

    Args:
        prediction: FailurePrediction object from curriculum_v2

    Returns:
        Formatted warning string with clear action items
    """
    lines = [
        "",
        "=" * 75,
        "[!] HARD WARNING: Task Appears Risky Based on Curriculum Analysis",
        "=" * 75,
        "",
        f"Task Similarity: {prediction.similarity:.1%} match with past failures",
        f"Related Failure: {prediction.bead_id}",
        "",
        f"Why This Failed Before:",
        f"  {prediction.reason}",
        "",
    ]

    if prediction.mitigation:
        lines.extend([
            f"Mitigation from Curriculum:",
            f"  {prediction.mitigation}",
            "",
        ])

    lines.extend([
        "Recommended Action Items:",
        "  1. Use --review flag to inspect generated spec before BUILD zone",
        "  2. Consider --templated fallback for quick iteration",
        "  3. Set --budget=0.50 to limit cost if trying experimental approach",
        "  4. Review curriculum entry: .beads/curriculum.jsonl (search for bead_id)",
        "",
        "=" * 75,
        "",
    ])

    return "\n".join(lines)


def format_safe_message() -> str:
    """Format a safe task message."""
    return "[OK] Task appears safe; proceeding.\n"


def check_task_safety(task_text: str, threshold: float = 0.8) -> Tuple[bool, str]:
    """Check if task is likely to fail; emit hard warning if so.

    Compares task against curriculum using embedding-based similarity.
    If a similar failure is found (similarity >= threshold), returns
    False with a formatted hard warning. Otherwise returns True with OK.

    Args:
        task_text: Description of the task to check
        threshold: Minimum similarity to trigger warning (default 0.8)

    Returns:
        Tuple of (is_safe, message_str):
          - is_safe (bool): True if task appears safe, False if risky
          - message_str (str): Formatted warning or safe message
    """
    if not task_text or not task_text.strip():
        return True, format_safe_message()

    # Load curriculum and predict failure
    curriculum = load_curriculum()
    prediction = predict_failure(task_text, curriculum=curriculum, threshold=threshold)

    # Check if prediction indicates failure risk
    if prediction.will_fail:
        warning_msg = format_hard_warning(prediction)
        return False, warning_msg
    else:
        return True, format_safe_message()


def main():
    """CLI interface for failure_predictor."""
    parser = argparse.ArgumentParser(
        description="Predict task failure risk using curriculum similarity"
    )
    parser.add_argument(
        "task",
        nargs="+",
        help="Task description to predict for",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.8,
        help="Similarity threshold to trigger warning (default 0.8, range 0.0-1.0)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output JSON format instead of human-readable text",
    )
    args = parser.parse_args()

    # Validate threshold
    if not (0.0 <= args.threshold <= 1.0):
        print("Error: --threshold must be between 0.0 and 1.0", file=sys.stderr)
        sys.exit(1)

    task_text = " ".join(args.task)

    # Check safety
    safe, msg = check_task_safety(task_text, threshold=args.threshold)

    if args.json:
        curriculum = load_curriculum()
        prediction = predict_failure(task_text, curriculum=curriculum,
                                     threshold=args.threshold)
        output = {
            "task": task_text,
            "threshold": args.threshold,
            "safe": safe,
            "will_fail": prediction.will_fail,
            "similarity": prediction.similarity,
            "reason": prediction.reason,
            "mitigation": prediction.mitigation,
            "bead_id": prediction.bead_id,
        }
        print(json.dumps(output, indent=2))
    else:
        print(msg, end="")

    # Exit with code 1 if task is risky (not safe)
    sys.exit(0 if safe else 1)


if __name__ == "__main__":
    main()
