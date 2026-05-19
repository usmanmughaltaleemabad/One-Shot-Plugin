"""
Tests for the shipped curriculum seed at .claude/registry/curriculum_seed.jsonl.

The seed is the plugin's baseline distilled wisdom — patterns we know cause
generation failures, with their fixes. Ships with the plugin so cold-start
users benefit. Augmented by runtime advice from this user's own /dream runs.
"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SEED = REPO_ROOT / ".claude" / "registry" / "curriculum_seed.jsonl"


def test_seed_file_exists():
    assert SEED.exists(), \
        ".claude/registry/curriculum_seed.jsonl must ship with the plugin"


def test_seed_entries_are_valid_json():
    """Every line must be a valid JSON object."""
    for i, line in enumerate(SEED.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError as e:
            raise AssertionError(f"line {i}: invalid JSON — {e}")
        assert isinstance(entry, dict)


def test_seed_entries_have_required_fields():
    """Every advice entry needs at least pattern + advice."""
    for i, line in enumerate(SEED.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        entry = json.loads(line)
        for field in ("pattern", "advice", "source"):
            assert field in entry, f"line {i} missing {field}"
        assert len(entry["advice"]) >= 50, \
            f"line {i} advice too short to be useful (got {len(entry['advice'])} chars)"


def test_seed_loads_via_beads_curriculum():
    """The dynamic advice loader must pick up the seed file."""
    sys.path.insert(0, str(REPO_ROOT / "skills" / "one-shot-generator" / "scripts"))
    sys.path.insert(0, str(REPO_ROOT / "skills" / "one-shot-generator" / "scripts" / "lib"))
    from beads_curriculum import _load_dynamic_advice
    advice = _load_dynamic_advice(REPO_ROOT)
    assert len(advice) >= 5, \
        "seed should ship with at least 5 baseline advice entries"


def test_seed_has_at_least_8_real_session_lessons():
    """The seed was hand-curated from real fixes in v1.0.0 development.
    If this drops below 8, someone deleted historical wisdom."""
    lines = [l for l in SEED.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(lines) >= 8, \
        f"seed has {len(lines)} entries, expected ≥ 8 real-session lessons"


def test_seed_patterns_are_unique():
    """No duplicate pattern keys — runtime overrides seed by pattern key."""
    patterns = []
    for line in SEED.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        patterns.append(json.loads(line)["pattern"])
    assert len(patterns) == len(set(patterns)), \
        f"duplicate patterns in seed: {[p for p in patterns if patterns.count(p) > 1]}"
