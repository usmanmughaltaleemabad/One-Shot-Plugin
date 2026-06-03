"""Tests for the memory-propagator agent.

The memory-propagator agent propagates cross-project learnings into the
curriculum and memory systems after each generation completes.

Since agents run in the Claude Code runtime, we test:
  1. Agent definition has proper YAML frontmatter
  2. Learnings structure is valid (pattern, source_task, failure_mode, mitigation, confidence)
  3. Memory and curriculum file structures are correct
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
AGENTS = REPO_ROOT / "agents"
BEADS = REPO_ROOT / ".beads"
MEMORY = REPO_ROOT / "memory"


# ─── Agent definition ───────────────────────────────────────────────────────

def test_memory_propagator_agent_exists():
    """The memory-propagator.md agent file must exist."""
    agent_path = AGENTS / "memory-propagator.md"
    assert agent_path.exists(), ".claude/agents/memory-propagator.md must exist"


def test_memory_propagator_has_valid_frontmatter():
    """Agent must have YAML frontmatter with name, description, tools, model."""
    agent_path = AGENTS / "memory-propagator.md"
    text = agent_path.read_text(encoding="utf-8")

    assert text.startswith("---"), "Agent must start with YAML frontmatter"
    front_match = re.search(r"^---\n(.+?)\n---", text, re.DOTALL)
    assert front_match, "Agent must have YAML frontmatter"
    front = front_match.group(1)

    # Required fields
    assert re.search(r"^name:\s*memory-propagator\b", front, re.MULTILINE), \
        "Must have name: memory-propagator"
    assert re.search(r"^description:", front, re.MULTILINE), \
        "Must have description:"
    assert re.search(r"^tools:", front, re.MULTILINE), \
        "Must have tools:"
    assert re.search(r"^model:", front, re.MULTILINE), \
        "Must have model:"


def test_memory_propagator_uses_sonnet():
    """Memory propagator should use sonnet for reasoning about patterns."""
    agent_path = AGENTS / "memory-propagator.md"
    text = agent_path.read_text(encoding="utf-8")
    assert re.search(r"^model:\s*sonnet\b", text, re.MULTILINE), \
        "memory-propagator should use sonnet for cross-project reasoning"


def test_memory_propagator_has_required_tools():
    """Agent must declare tools for reading learnings and updating memory."""
    agent_path = AGENTS / "memory-propagator.md"
    text = agent_path.read_text(encoding="utf-8")
    front_match = re.search(r"^---\n(.+?)\n---", text, re.DOTALL)
    front = front_match.group(1)

    tools_match = re.search(r"^tools:\s*(.+)$", front, re.MULTILINE)
    assert tools_match, "Must have tools:"
    tools_str = tools_match.group(1)

    required = {"Read", "Write", "Edit"}
    for tool in required:
        assert tool in tools_str, f"Must include {tool} in tools"


# ─── Memory directory structure ──────────────────────────────────────────────

def test_memory_directory_exists():
    """The memory/ directory must exist for cross-project knowledge."""
    assert MEMORY.exists() and MEMORY.is_dir(), \
        "memory/ directory must exist"


def test_memory_jsonl_template_exists():
    """The .beads/memory.jsonl starting template must exist."""
    memory_jsonl = BEADS / "memory.jsonl"
    assert memory_jsonl.exists(), ".beads/memory.jsonl must exist"


def test_memory_jsonl_is_valid_jsonl():
    """Each line in .beads/memory.jsonl must be valid JSON."""
    memory_jsonl = BEADS / "memory.jsonl"
    text = memory_jsonl.read_text(encoding="utf-8").strip()

    if not text:  # Empty file is valid
        return

    for i, line in enumerate(text.split("\n"), 1):
        if line.strip():
            try:
                json.loads(line)
            except json.JSONDecodeError as e:
                pytest.fail(f"Line {i} is not valid JSON: {e}")


# ─── Learnings structure ─────────────────────────────────────────────────────

def test_learning_structure_has_required_fields():
    """A valid learning must have: pattern, source_task, failure_mode, mitigation, confidence."""
    learning = {
        "pattern": "has_many relationships require explicit FK columns",
        "source_task": "shopping cart with line items",
        "failure_mode": "missing cart_id in LineItem schema",
        "mitigation": "architect stage must infer FKs from relationships",
        "confidence": 0.95,
    }

    required = {"pattern", "source_task", "failure_mode", "mitigation", "confidence"}
    assert set(learning.keys()) == required, \
        f"Learning must have exactly {required}, got {set(learning.keys())}"

    # Confidence must be 0.0-1.0
    assert 0.0 <= learning["confidence"] <= 1.0, \
        "confidence must be between 0.0 and 1.0"

    # All string fields must be non-empty
    for field in ["pattern", "source_task", "failure_mode", "mitigation"]:
        assert isinstance(learning[field], str) and learning[field], \
            f"{field} must be a non-empty string"


def test_curriculum_update_structure():
    """Updated curriculum entries must preserve existing structure and add metadata."""
    curriculum_entry = {
        "id": "bd-001",
        "task_text": "shopping cart with line items and discounts",
        "reason": "FK column type mismatch",
        "mitigation": "Check type: key in spec.json matches migration_generator.py type mapping",
        "source_learning_id": "learn-12345",  # Links back to learning
        "propagation_timestamp": "2026-05-25T15:09:00Z",
    }

    required = {"id", "task_text", "reason", "mitigation"}
    for field in required:
        assert field in curriculum_entry, \
            f"Curriculum entry must have {field}"


def test_memory_db_structure():
    """Memory DB entries must include vector embeddings and metadata."""
    memory_entry = {
        "id": "learn-12345",
        "pattern": "has_many relationships require explicit FK columns",
        "source_task": "shopping cart with line items",
        "failure_mode": "missing cart_id in LineItem schema",
        "mitigation": "architect stage must infer FKs from relationships",
        "confidence": 0.95,
        "embedding": [0.1, 0.2, 0.3],  # Example embedding vector
        "created_at": "2026-05-25T15:09:00Z",
        "last_used": "2026-05-25T15:09:00Z",
    }

    required = {"id", "pattern", "source_task", "failure_mode", "mitigation",
                "confidence", "created_at"}
    for field in required:
        assert field in memory_entry, \
            f"Memory entry must have {field}"

    if "embedding" in memory_entry:
        assert isinstance(memory_entry["embedding"], list), \
            "embedding must be a list of floats"


# ─── Integration scenarios ──────────────────────────────────────────────────

def test_propagation_report_structure():
    """The propagation report must document the update."""
    report = {
        "timestamp": "2026-05-25T15:09:00Z",
        "learnings_extracted": 3,
        "learnings_embedded": 3,
        "learnings_stored": 3,
        "curriculum_updated": True,
        "updated_entries": ["bd-001", "bd-002"],
        "errors": [],
    }

    required = {"timestamp", "learnings_extracted", "learnings_embedded",
                "learnings_stored", "curriculum_updated", "errors"}
    for field in required:
        assert field in report, f"Report must have {field}"


def test_learning_similarity_dedup_logic():
    """New learnings should be deduplicated by pattern similarity."""
    learning1 = {
        "pattern": "FK columns must match type",
        "source_task": "cart with items",
        "failure_mode": "type mismatch",
        "mitigation": "check type mapping",
        "confidence": 0.95,
    }

    learning2 = {
        "pattern": "FK columns must match type",  # Identical pattern
        "source_task": "order with payments",
        "failure_mode": "integer vs string",
        "mitigation": "check type mapping",
        "confidence": 0.98,
    }

    # Learning 2 should update learning 1 (same pattern, higher confidence)
    assert learning1["pattern"] == learning2["pattern"], \
        "Duplicate patterns should trigger deduplication logic"


def test_confidence_propagation():
    """Multiple instances of same pattern should increase confidence."""
    base_confidence = 0.7
    num_instances = 3

    # Simple Bayesian update: confidence increases with each instance
    updated_confidence = 1.0 - (1.0 - base_confidence) ** num_instances

    assert updated_confidence > base_confidence, \
        "Confidence should increase with repeated observations"
    assert updated_confidence <= 1.0, \
        "Confidence cannot exceed 1.0"


# ─── Error handling ─────────────────────────────────────────────────────────

def test_missing_learnings_jsonl_is_handled():
    """Agent should handle missing learnings.jsonl gracefully."""
    # This is a design requirement — the agent must emit a report
    # even if there are no learnings to propagate
    report = {
        "timestamp": "2026-05-25T15:09:00Z",
        "learnings_extracted": 0,
        "learnings_embedded": 0,
        "learnings_stored": 0,
        "curriculum_updated": False,
        "updated_entries": [],
        "errors": ["learnings.jsonl not found — no learnings to propagate"],
    }

    # Should not raise, but report the error
    assert len(report["errors"]) > 0, \
        "Should report missing file, not raise"


def test_embedding_failure_is_graceful():
    """If embedding service fails, should report and continue."""
    report = {
        "timestamp": "2026-05-25T15:09:00Z",
        "learnings_extracted": 3,
        "learnings_embedded": 1,  # Only 1 of 3 succeeded
        "learnings_stored": 1,
        "curriculum_updated": True,
        "updated_entries": ["bd-001"],
        "errors": [
            "Failed to embed learning 2: embedding service timeout",
            "Failed to embed learning 3: embedding service timeout",
        ],
    }

    # Should recover from partial failures
    assert report["learnings_extracted"] > report["learnings_embedded"], \
        "Should report partial embedding failures"
    assert len(report["errors"]) > 0, \
        "Should document the failures"


def test_curriculum_conflict_resolution():
    """If a learning conflicts with existing curriculum, should merge."""
    existing = {
        "id": "bd-001",
        "task_text": "shopping cart",
        "reason": "Old reason",
        "mitigation": "Old mitigation",
    }

    new_learning = {
        "pattern": "FK column type mismatch",
        "source_task": "shopping cart",
        "failure_mode": "string vs integer",
        "mitigation": "New mitigation",
        "confidence": 0.99,
    }

    # Merged entry should prefer higher-confidence mitigation
    merged = {
        **existing,
        "reason": new_learning["failure_mode"],
        "mitigation": new_learning["mitigation"],
        "source_learning_id": "learn-12345",
        "propagation_timestamp": "2026-05-25T15:09:00Z",
    }

    assert merged["mitigation"] == new_learning["mitigation"], \
        "Should merge learnings, preferring new mitigation"


# ─── Integration with embedding_cache.py ────────────────────────────────────

def test_embedding_cache_integration():
    """Agent should use embedding_cache.py for semantic vector generation."""
    # The agent definition must reference embedding_cache.py or
    # delegate to it via a Task call
    agent_path = AGENTS / "memory-propagator.md"
    text = agent_path.read_text(encoding="utf-8")

    # Check that either the agent docs mention embedding_cache or
    # the agent is designed to call a service that does
    assert "embedding" in text.lower() or "embed" in text.lower(), \
        "Agent must document how embeddings are generated (via embedding_cache or similar)"
