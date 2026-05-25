#!/usr/bin/env python3
"""
Curriculum V2 — Embedding-based failure prediction (v1.0.0)

Uses cosine similarity via embeddings to predict failures based on past
curriculum data in .beads/curriculum.jsonl. Provides semantic similarity
matching (vs. token-based matching in beads_curriculum.py).

Unlike beads_curriculum.py (Jaccard token overlap):
- curriculum_v2.py uses embedding vectors for semantic understanding
- Detects similar failures even when task_text uses different wording
- Enables confidence scoring via similarity threshold
- Suitable when curriculum grows beyond ~1000 entries (token matching O(n))

Usage:
    from curriculum_v2 import load_curriculum, find_similar_failures, predict_failure

    curriculum = load_curriculum()
    similar = find_similar_failures("shopping cart with discounts", threshold=0.8)

    result = predict_failure("add payment processing to checkout flow")
    if result["will_fail"]:
        print(f"Warning: {result['reason']}")
        print(f"Similarity: {result['similarity']:.3f}")
        print(f"Mitigation: {result['mitigation']}")

CLI:
    python curriculum_v2.py "shopping cart with line items" --threshold 0.8
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import embedding utilities
try:
    from embedding_cache import cosine_similarity, get_embedding, init_cache
except ImportError:
    # Graceful fallback if embedding_cache not available
    def get_embedding(_: str) -> Optional[List[float]]:
        return None

    def cosine_similarity(a: List[float], b: List[float]) -> float:
        return 0.0

    def init_cache() -> None:
        pass


@dataclass
class FailurePrediction:
    """Result of failure prediction based on curriculum similarity."""
    will_fail: bool
    reason: str
    similarity: float
    mitigation: Optional[str] = None
    bead_id: Optional[str] = None
    task_text: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def load_curriculum(
    curriculum_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """Load failure curriculum from .beads/curriculum.jsonl.

    Reads one JSON object per line and returns list of curriculum entries.
    Each entry should have:
      - task_text: str (description of the failed task)
      - reason: str (why it failed)
      - mitigation: str (how to fix/avoid it)
      - id: str (optional, bead ID)

    Args:
        curriculum_path: Path to curriculum.jsonl. If None, searches for
                        .beads/curriculum.jsonl starting from cwd.

    Returns:
        List of curriculum dictionaries, or [] if file not found.
    """
    if curriculum_path is None:
        # Search up the tree for .beads/curriculum.jsonl
        cur = Path.cwd().resolve()
        found = False
        while cur != cur.parent:
            candidate = cur / ".beads" / "curriculum.jsonl"
            if candidate.exists():
                curriculum_path = candidate
                found = True
                break
            cur = cur.parent

        if not found:
            # Fallback: create empty curriculum path (will return [])
            curriculum_path = Path.cwd() / ".beads" / "curriculum.jsonl"

    if not curriculum_path.exists():
        return []

    curriculum: List[Dict[str, Any]] = []
    try:
        for line in curriculum_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                curriculum.append(entry)
            except json.JSONDecodeError:
                # Skip malformed lines
                continue
    except Exception:
        # If reading fails, return empty list
        pass

    return curriculum


def find_similar_failures(
    task_text: str,
    curriculum: Optional[List[Dict[str, Any]]] = None,
    threshold: float = 0.8,
) -> List[Dict[str, Any]]:
    """Find similar failures in curriculum using cosine similarity.

    Computes embedding for task_text and compares against all curriculum
    entries. Returns those with similarity >= threshold, sorted by similarity.

    Args:
        task_text: Description of the task to check.
        curriculum: List of curriculum entries. If None, loads from disk.
        threshold: Minimum similarity score (0.0 to 1.0). Default 0.8.

    Returns:
        List of curriculum entries with similarity >= threshold, sorted
        by similarity descending. Each entry includes a 'similarity' key.
    """
    if not task_text or not task_text.strip():
        return []

    # Load curriculum if not provided
    if curriculum is None:
        curriculum = load_curriculum()

    if not curriculum:
        return []

    # Initialize embedding cache
    init_cache()

    # Get embedding for task_text
    task_embedding = get_embedding(task_text.strip())
    if task_embedding is None:
        # Embeddings not available (sentence-transformers not installed)
        return []

    # Compute similarities
    similar_failures: List[Dict[str, Any]] = []
    for entry in curriculum:
        curriculum_task = entry.get("task_text") or entry.get("task", "")
        if not curriculum_task:
            continue

        curriculum_embedding = get_embedding(curriculum_task.strip())
        if curriculum_embedding is None:
            continue

        sim = cosine_similarity(task_embedding, curriculum_embedding)
        if sim >= threshold:
            # Add similarity to entry for sorting
            entry_with_sim = {**entry, "similarity": round(sim, 4)}
            similar_failures.append(entry_with_sim)

    # Sort by similarity descending
    similar_failures.sort(key=lambda x: x["similarity"], reverse=True)
    return similar_failures


def predict_failure(
    task_text: str,
    curriculum: Optional[List[Dict[str, Any]]] = None,
    threshold: float = 0.8,
) -> FailurePrediction:
    """Predict if a task will fail based on curriculum similarity.

    Finds similar failures in curriculum. If any found with similarity >= threshold,
    returns a warning with the most similar failure's details.

    Args:
        task_text: Description of the task to predict for.
        curriculum: List of curriculum entries. If None, loads from disk.
        threshold: Minimum similarity to consider a failure relevant. Default 0.8.

    Returns:
        FailurePrediction with will_fail=True/False and relevant details.
    """
    if not task_text or not task_text.strip():
        return FailurePrediction(
            will_fail=False,
            reason="Empty task text",
            similarity=0.0,
        )

    # Load curriculum if not provided
    if curriculum is None:
        curriculum = load_curriculum()

    # Find similar failures
    similar = find_similar_failures(task_text, curriculum=curriculum,
                                     threshold=threshold)

    if not similar:
        return FailurePrediction(
            will_fail=False,
            reason="No similar failures found in curriculum",
            similarity=0.0,
        )

    # Use most similar failure (first in sorted list)
    most_similar = similar[0]
    sim_score = most_similar.get("similarity", 0.0)
    bead_id = most_similar.get("id", "<unknown>")
    reason = most_similar.get("reason", "Similar failure detected")
    mitigation = most_similar.get("mitigation")
    curriculum_task = most_similar.get("task_text") or most_similar.get("task")

    return FailurePrediction(
        will_fail=True,
        reason=f"Similar failure detected (similarity: {sim_score:.3f}): {reason}",
        similarity=sim_score,
        mitigation=mitigation,
        bead_id=bead_id,
        task_text=curriculum_task,
    )


def main():
    """CLI interface for curriculum_v2."""
    parser = argparse.ArgumentParser(
        description="Predict failures using embedding-based curriculum similarity"
    )
    parser.add_argument("task", nargs="+",
                        help="Task description to predict for")
    parser.add_argument("--threshold", type=float, default=0.8,
                        help="Similarity threshold (0.0 to 1.0, default 0.8)")
    parser.add_argument("--curriculum", type=str, default=None,
                        help="Path to curriculum.jsonl (optional)")
    parser.add_argument("--json", action="store_true",
                        help="Output JSON instead of human-readable text")
    parser.add_argument("--show-all", action="store_true",
                        help="Show all similar failures, not just most similar")
    args = parser.parse_args()

    task_text = " ".join(args.task)

    # Load curriculum
    if args.curriculum:
        curriculum_path = Path(args.curriculum)
    else:
        curriculum_path = None

    curriculum = load_curriculum(curriculum_path)

    if args.show_all:
        # Show all similar failures
        similar = find_similar_failures(task_text, curriculum=curriculum,
                                         threshold=args.threshold)
        if args.json:
            output = {
                "task": task_text,
                "threshold": args.threshold,
                "similar_count": len(similar),
                "results": [
                    {
                        "bead_id": s.get("id"),
                        "similarity": s.get("similarity"),
                        "reason": s.get("reason"),
                        "mitigation": s.get("mitigation"),
                    }
                    for s in similar
                ],
            }
            print(json.dumps(output, indent=2))
        else:
            print(f"Similar failures for: {task_text}")
            print(f"Threshold: {args.threshold}, Found: {len(similar)}\n")
            for s in similar:
                sim = s.get("similarity", 0.0)
                bead = s.get("id", "<unknown>")
                reason = s.get("reason", "?")
                print(f"  [{sim:.3f}] {bead}: {reason}")
    else:
        # Show prediction (single most similar)
        prediction = predict_failure(task_text, curriculum=curriculum,
                                      threshold=args.threshold)
        if args.json:
            print(json.dumps(prediction.to_dict(), indent=2))
        else:
            print(f"Task: {task_text}")
            print(f"Threshold: {args.threshold}\n")
            if prediction.will_fail:
                print(f"[!] WILL LIKELY FAIL")
                print(f"  Reason: {prediction.reason}")
                if prediction.mitigation:
                    print(f"  Mitigation: {prediction.mitigation}")
                if prediction.bead_id:
                    print(f"  Related bead: {prediction.bead_id}")
            else:
                print(f"[OK] No similar failures found")
                print(f"  Reason: {prediction.reason}")


if __name__ == "__main__":
    main()
