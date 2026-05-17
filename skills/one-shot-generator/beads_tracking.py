#!/usr/bin/env python3
"""Beads tracking system for generation decisions (Phase 2 enhancement)"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


def track_generation(
    project_path: str,
    request: str,
    generated_code: Dict,
    framework: str,
    agents_feedback: Dict,
    approval_status: str = "pending",
) -> None:
    """
    Track code generation in .claude/beads/status.jsonl

    Args:
        project_path: Project root
        request: User requirement ("add user auth")
        generated_code: Generated code dict
        framework: Detected framework
        agents_feedback: Feedback from validation agents
        approval_status: "approved", "rejected", "pending", "with_changes"
    """

    beads_file = Path(project_path) / ".claude" / "beads" / "status.jsonl"
    beads_file.parent.mkdir(parents=True, exist_ok=True)

    # Create generation record
    record = {
        "id": _generate_id("gen"),
        "type": "generation",
        "request": request,
        "framework": framework,
        "files_generated": len(generated_code.get("code", {})),
        "status": approval_status,
        "agents_feedback": agents_feedback,
        "timestamp": datetime.utcnow().isoformat(),
        "approval_date": None,
    }

    # Append to beads file
    with open(beads_file, "a") as f:
        f.write(json.dumps(record) + "\n")


def track_approval(
    project_path: str,
    generation_id: str,
    approver: str,
    notes: Optional[str] = None,
) -> None:
    """
    Track approval of generated code

    Args:
        project_path: Project root
        generation_id: ID of generation to approve
        approver: Who approved (agent or human)
        notes: Additional notes
    """

    beads_file = Path(project_path) / ".claude" / "beads" / "status.jsonl"

    # Read all beads
    beads = []
    if beads_file.exists():
        for line in beads_file.read_text().strip().split("\n"):
            if line:
                beads.append(json.loads(line))

    # Find and update generation record
    for bead in beads:
        if bead.get("id") == generation_id and bead.get("type") == "generation":
            bead["status"] = "approved"
            bead["approval_date"] = datetime.utcnow().isoformat()
            bead["approver"] = approver
            if notes:
                bead["approval_notes"] = notes
            break

    # Write back
    with open(beads_file, "w") as f:
        for bead in beads:
            f.write(json.dumps(bead) + "\n")


def track_failure(
    project_path: str,
    generation_id: str,
    error: str,
    lesson: Optional[str] = None,
) -> None:
    """
    Track generation failure for learning

    Args:
        project_path: Project root
        generation_id: ID of failed generation
        error: Error message
        lesson: Lesson learned
    """

    failures_file = Path(project_path) / ".claude" / "beads" / "failures.jsonl"
    failures_file.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "id": _generate_id("fail"),
        "generation_id": generation_id,
        "error": error,
        "lesson": lesson,
        "timestamp": datetime.utcnow().isoformat(),
        "fixed": False,
    }

    with open(failures_file, "a") as f:
        f.write(json.dumps(record) + "\n")


def get_generation_stats(project_path: str) -> Dict:
    """
    Get statistics about code generations

    Args:
        project_path: Project root

    Returns:
        Stats dict with generation counts, approval rate, common patterns
    """

    beads_file = Path(project_path) / ".claude" / "beads" / "status.jsonl"

    if not beads_file.exists():
        return {"total": 0, "approved": 0, "pending": 0}

    stats = {
        "total": 0,
        "approved": 0,
        "rejected": 0,
        "pending": 0,
        "frameworks": {},
        "common_requests": [],
    }

    for line in beads_file.read_text().strip().split("\n"):
        if not line:
            continue

        bead = json.loads(line)
        if bead.get("type") != "generation":
            continue

        stats["total"] += 1
        status = bead.get("status", "unknown")
        if status == "approved":
            stats["approved"] += 1
        elif status == "rejected":
            stats["rejected"] += 1
        else:
            stats["pending"] += 1

        # Track frameworks
        framework = bead.get("framework", "unknown")
        stats["frameworks"][framework] = stats["frameworks"].get(framework, 0) + 1

        # Track request patterns
        request = bead.get("request", "")
        if request:
            stats["common_requests"].append(request)

    return stats


def _generate_id(prefix: str) -> str:
    """Generate unique ID with prefix"""
    import random
    import string
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{prefix}-{suffix}"


if __name__ == "__main__":
    import sys

    project_path = sys.argv[1] if len(sys.argv) > 1 else "."

    # Example: Track a generation
    track_generation(
        project_path,
        "Add user authentication with JWT",
        {"code": {"models.py": "...", "views.py": "..."}},
        "django",
        {"code_reviewer": "approved", "security_scanner": "no_issues"},
        "pending",
    )

    # Get stats
    stats = get_generation_stats(project_path)
    print(json.dumps(stats, indent=2))

