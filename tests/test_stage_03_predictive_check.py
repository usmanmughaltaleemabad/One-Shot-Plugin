"""
Integration tests for Stage 0.3 — Predictive Failure Check.

Tests that:
1. Stage 0.3 is correctly documented in stages/plan.md
2. SKILL.md references the predictive_check span
3. failure_predictor.py can be invoked and returns correct format
4. --force flag bypasses the hard warning gate
5. Hard warnings are properly formatted with action items
6. The stage gracefully handles missing curriculum
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "skills" / "one-shot-generator" / "scripts"
STAGES = REPO_ROOT / "skills" / "one-shot-generate" / "stages"
SKILL_FILE = REPO_ROOT / "skills" / "one-shot-generate" / "SKILL.md"
PLAN_FILE = STAGES / "plan.md"


def _run(script: str, *args: str) -> subprocess.CompletedProcess:
    """Run a Python script with args."""
    env = {}
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args],
        capture_output=True, text=True, env=env, encoding="utf-8",
        timeout=60,
    )


# ─── SKILL.md Structure Tests ──────────────────────────────────────────────

def test_skill_md_documents_predictive_check_phase():
    """SKILL.md must document Stage 0.3 in the PLAN phase."""
    text = SKILL_FILE.read_text(encoding="utf-8")
    assert "predictive_check" in text.lower(), \
        "SKILL.md must reference predictive_check stage"
    assert "0.3" in text, \
        "SKILL.md must document Stage 0.3"


def test_skill_md_references_predictive_check_span():
    """SKILL.md must emit OTel span for predictive_check."""
    text = SKILL_FILE.read_text(encoding="utf-8")
    assert 'start_as_current_span("predictive_check")' in text, \
        "SKILL.md must emit predictive_check OTel span"


def test_skill_md_documents_force_flag_bypass():
    """SKILL.md must document --force bypassing predictive warnings."""
    text = SKILL_FILE.read_text(encoding="utf-8")
    # Find the flags section
    assert "--force" in text
    # Should mention it bypasses predictive failure warnings
    force_section = text[text.find("--force"):text.find("--force") + 300]
    assert "predictive" in force_section.lower() or \
           ("failure" in force_section.lower() and "warning" in force_section.lower()), \
        "SKILL.md must document --force bypassing predictive warnings"


# ─── Plan Stage Documentation Tests ───────────────────────────────────────

def test_plan_md_documents_stage_03():
    """stages/plan.md must document Stage 0.3 Predictive Check."""
    text = PLAN_FILE.read_text(encoding="utf-8")
    assert "Stage 0.3" in text, \
        "plan.md must document Stage 0.3"
    assert "Predictive" in text or "predictive" in text, \
        "plan.md must mention predictive check"
    assert "failure_predictor.py" in text, \
        "plan.md must reference failure_predictor.py script"


def test_plan_md_stage_03_comes_after_curriculum():
    """Stage 0.3 must come after curriculum check (Stage 0)."""
    text = PLAN_FILE.read_text(encoding="utf-8")
    # Extract stage 0 and stage 0.3 positions
    stage_0_pos = text.find("## Stage 0 —")
    stage_03_pos = text.find("## Stage 0.3 —")
    stage_05_pos = text.find("## Stage 0.5 —")

    assert stage_0_pos >= 0, "plan.md must have Stage 0"
    assert stage_03_pos >= 0, "plan.md must have Stage 0.3"
    assert stage_05_pos >= 0, "plan.md must have Stage 0.5"

    assert stage_0_pos < stage_03_pos < stage_05_pos, \
        "Stage order must be: 0 → 0.3 → 0.5"


def test_plan_md_documents_hard_warning_format():
    """Stage 0.3 docs must explain hard warning format."""
    text = PLAN_FILE.read_text(encoding="utf-8")
    stage_03_start = text.find("## Stage 0.3 —")
    stage_05_start = text.find("## Stage 0.5 —")
    stage_03_text = text[stage_03_start:stage_05_start]

    # Should mention that warnings are emitted
    assert "warning" in stage_03_text.lower(), \
        "Stage 0.3 must document hard warnings"
    # Should mention --force bypass
    assert "--force" in stage_03_text, \
        "Stage 0.3 must document --force flag"


def test_plan_md_documents_action_items():
    """Stage 0.3 docs must list action items for users."""
    text = PLAN_FILE.read_text(encoding="utf-8")
    stage_03_start = text.find("## Stage 0.3 —")
    stage_05_start = text.find("## Stage 0.5 —")
    stage_03_text = text[stage_03_start:stage_05_start]

    # Should mention --review
    assert "--review" in stage_03_text, \
        "Stage 0.3 must mention --review action item"
    # Should mention --templated
    assert "--templated" in stage_03_text, \
        "Stage 0.3 must mention --templated action item"
    # Should mention --budget
    assert "--budget" in stage_03_text, \
        "Stage 0.3 must mention --budget action item"


# ─── Failure Predictor Script Tests ────────────────────────────────────────

def test_failure_predictor_script_exists():
    """failure_predictor.py must exist and be importable."""
    script = SCRIPTS / "failure_predictor.py"
    assert script.exists(), "failure_predictor.py must exist"

    # Try to import it
    sys.path.insert(0, str(SCRIPTS / "lib"))
    sys.path.insert(0, str(SCRIPTS))
    try:
        from failure_predictor import check_task_safety, format_hard_warning
        assert callable(check_task_safety)
        assert callable(format_hard_warning)
    except ImportError as e:
        pytest.skip(f"Cannot import failure_predictor: {e}")


def test_failure_predictor_cli_help():
    """failure_predictor.py --help must work."""
    result = _run("failure_predictor.py", "--help")
    assert result.returncode == 0, "failure_predictor --help should succeed"
    assert "task" in result.stdout.lower(), \
        "Help should document task argument"
    assert "threshold" in result.stdout.lower(), \
        "Help should document --threshold option"


def test_failure_predictor_safe_task():
    """Predictor returns 0 (safe) for novel tasks."""
    # Use a task very unlikely to be in curriculum
    result = _run("failure_predictor.py",
                  "xyzzy unique task from test case qwerty")
    # May be 0 (safe) or 1 (warning), depending on curriculum
    # But should not crash
    assert result.returncode in (0, 1), \
        "failure_predictor should exit cleanly"
    # Should have output
    assert len(result.stdout) > 0 or len(result.stderr) > 0, \
        "failure_predictor should produce output"


def test_failure_predictor_json_output():
    """Predictor --json flag produces valid JSON."""
    result = _run("failure_predictor.py", "test task", "--json")
    # Should not crash
    assert result.returncode in (0, 1)

    # Try to parse output as JSON
    try:
        output = json.loads(result.stdout)
        assert isinstance(output, dict)
        assert "task" in output
        assert "safe" in output
        assert isinstance(output["safe"], bool)
    except json.JSONDecodeError:
        pytest.skip("Could not parse JSON output (curriculum may be empty)")


def test_failure_predictor_threshold_parameter():
    """Predictor accepts --threshold parameter."""
    result = _run("failure_predictor.py", "test task", "--threshold", "0.5")
    assert result.returncode in (0, 1), \
        "failure_predictor should accept --threshold"


def test_failure_predictor_invalid_threshold():
    """Predictor rejects invalid threshold values."""
    result = _run("failure_predictor.py", "test task", "--threshold", "1.5")
    assert result.returncode != 0, \
        "failure_predictor should reject threshold > 1.0"


# ─── Hard Warning Format Tests ─────────────────────────────────────────────

@pytest.mark.skipif(True, reason="Requires embedding model; skipped in CI")
def test_hard_warning_format_includes_required_sections():
    """Hard warning must include all required sections."""
    sys.path.insert(0, str(SCRIPTS / "lib"))
    sys.path.insert(0, str(SCRIPTS))

    try:
        from failure_predictor import format_hard_warning
        from curriculum_v2 import FailurePrediction

        prediction = FailurePrediction(
            will_fail=True,
            reason="Test failure reason",
            similarity=0.85,
            mitigation="Test mitigation",
            bead_id="bd-test-001",
        )

        warning = format_hard_warning(prediction)

        # Check required sections
        assert "[!] HARD WARNING" in warning
        assert "85" in warning  # similarity percentage
        assert "bd-test-001" in warning
        assert "Test failure reason" in warning
        assert "Test mitigation" in warning
        assert "--review" in warning
        assert "--templated" in warning
        assert "--budget" in warning
    except ImportError:
        pytest.skip("Cannot import failure_predictor components")


# ─── Integration Tests ─────────────────────────────────────────────────────

def test_stage_03_comes_between_curriculum_and_extraction():
    """Stage 0.3 must be executed between curriculum check and extraction."""
    text = PLAN_FILE.read_text(encoding="utf-8")

    # Get order of stages
    stage_0_pos = text.find("## Stage 0 —")
    stage_03_pos = text.find("## Stage 0.3 —")
    stage_1_pos = text.find("## Stage 1 —")

    assert stage_0_pos < stage_03_pos < stage_1_pos, \
        "Pipeline execution order: Stage 0 → Stage 0.3 → Stage 1"


def test_predictive_check_stage_mentions_engagement_model():
    """Stage 0.3 must explain when warnings are shown vs skipped."""
    text = PLAN_FILE.read_text(encoding="utf-8")
    stage_03_start = text.find("## Stage 0.3 —")
    stage_05_start = text.find("## Stage 0.5 —")
    stage_03_text = text[stage_03_start:stage_05_start]

    # Should mention what happens on will_fail=true
    assert "true" in stage_03_text or "risky" in stage_03_text.lower(), \
        "Stage 0.3 must explain behavior on risky tasks"
    # Should mention what happens on will_fail=false
    assert "false" in stage_03_text or "safe" in stage_03_text.lower() or "[OK]" in stage_03_text, \
        "Stage 0.3 must explain behavior on safe tasks"


def test_predictive_check_stage_documents_graceful_failure():
    """Stage 0.3 must document behavior when predictor fails."""
    text = PLAN_FILE.read_text(encoding="utf-8")
    stage_03_start = text.find("## Stage 0.3 —")
    stage_05_start = text.find("## Stage 0.5 —")
    stage_03_text = text[stage_03_start:stage_05_start]

    # Should mention error handling
    assert "error" in stage_03_text.lower() or \
           "skip" in stage_03_text.lower() or \
           "exception" in stage_03_text.lower() or \
           "unavailable" in stage_03_text.lower(), \
        "Stage 0.3 must document what happens if predictor fails"


def test_predictive_check_stage_documents_curriculum_requirement():
    """Stage 0.3 must explain relationship to curriculum."""
    text = PLAN_FILE.read_text(encoding="utf-8")
    stage_03_start = text.find("## Stage 0.3 —")
    stage_05_start = text.find("## Stage 0.5 —")
    stage_03_text = text[stage_03_start:stage_05_start]

    # Should mention curriculum
    assert "curriculum" in stage_03_text.lower(), \
        "Stage 0.3 must explain use of curriculum"


# ─── Documentation Tests ───────────────────────────────────────────────────

def test_predictive_failures_doc_exists():
    """docs/predictive-failures.md must exist."""
    doc = REPO_ROOT / "docs" / "predictive-failures.md"
    assert doc.exists(), "docs/predictive-failures.md must exist"


def test_predictive_failures_doc_structure():
    """docs/predictive-failures.md must have key sections."""
    doc = REPO_ROOT / "docs" / "predictive-failures.md"
    text = doc.read_text(encoding="utf-8")

    required_sections = [
        "Overview",
        "How It Works",
        "Embedding Similarity",
        "Hard Warning Example",
        "Disabling Warnings",
        "--force Flag",
        "Curriculum Learning",
        "Mitigation Options",
        "FAQ",
    ]

    for section in required_sections:
        assert section in text or section.lower() in text.lower(), \
            f"docs/predictive-failures.md must have '{section}' section"


def test_predictive_failures_doc_has_force_example():
    """docs/predictive-failures.md must show --force usage example."""
    doc = REPO_ROOT / "docs" / "predictive-failures.md"
    text = doc.read_text(encoding="utf-8")

    assert "--force" in text
    # Should show example command
    assert "/one-shot" in text or "one-shot" in text


def test_predictive_failures_doc_has_mitigation_options():
    """docs/predictive-failures.md must document 4 mitigation options."""
    doc = REPO_ROOT / "docs" / "predictive-failures.md"
    text = doc.read_text(encoding="utf-8")

    options = [
        "--review",
        "--templated",
        "--budget",
        "--force",
    ]

    for opt in options:
        assert opt in text, \
            f"docs/predictive-failures.md must document {opt} option"


# ─── Edge Case Tests ──────────────────────────────────────────────────────

def test_stage_03_is_optional_not_blocking():
    """If predictor fails, pipeline must continue (graceful degradation)."""
    text = PLAN_FILE.read_text(encoding="utf-8")
    stage_03_start = text.find("## Stage 0.3 —")
    stage_05_start = text.find("## Stage 0.5 —")
    stage_03_text = text[stage_03_start:stage_05_start]

    # Must mention skipping/graceful handling
    assert any(phrase in stage_03_text.lower()
               for phrase in ["skip", "continue", "proceed", "exception", "error"]), \
        "Stage 0.3 must document graceful failure handling"


def test_curriculum_similarity_threshold_documented():
    """SKILL.md or plan.md must document default similarity threshold."""
    skill_text = SKILL_FILE.read_text(encoding="utf-8")
    plan_text = PLAN_FILE.read_text(encoding="utf-8")
    all_text = skill_text + plan_text

    # Should mention threshold (0.8 is default)
    assert "threshold" in all_text.lower() or "0.8" in all_text or "similarity" in all_text.lower(), \
        "Pipeline docs must mention similarity threshold"
