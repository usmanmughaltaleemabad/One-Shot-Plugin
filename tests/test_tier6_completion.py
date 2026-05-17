"""Tests for the Tier 6 completion work — agentic_evals, body_hints,
promote_rule, sast_runner, route-override wiring, telemetry-on-hot-paths,
and the marketplace + tutorial + CI yaml shipped artefacts.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "skills" / "one-shot-generator" / "scripts"
EVALS = REPO_ROOT / "tests" / "evals"


def _run(script: str, *args: str) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args],
        capture_output=True, text=True, env=env, encoding="utf-8",
        timeout=60,
    )


# ─── agentic_evals ──────────────────────────────────────────────────────────

def test_agentic_evals_replay_mode_runs():
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        [sys.executable, str(EVALS / "agentic_evals.py"), "--json"],
        capture_output=True, text=True, env=env, encoding="utf-8",
        timeout=30,
    )
    data = json.loads(proc.stdout)
    assert isinstance(data, list)
    assert len(data) >= 2, "should have at least 2 seeded replay scenarios"
    for s in data:
        assert s["passed"], f"replay {s['scenario']} failed: {s}"


def test_agentic_evals_plan_mode_runs():
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        [sys.executable, str(EVALS / "agentic_evals.py"), "--mode", "plan", "--json"],
        capture_output=True, text=True, env=env, encoding="utf-8",
        timeout=30,
    )
    data = json.loads(proc.stdout)
    assert isinstance(data, list)
    assert all("scenario" in p for p in data)


# ─── body_hints ─────────────────────────────────────────────────────────────

def test_body_hints_lists_at_least_25_pairs():
    """The hint catalogue should cover all 5 frameworks. Tier 8 added
    5 more hints (service_layer, auth, background, events, exceptions);
    catalogue keeps growing — anything ≥ 25 is healthy."""
    proc = _run("body_hints.py", "--list", "--json")
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert len(data) >= 25, f"expected ≥25 hints, got {len(data)}"
    frameworks_covered = {entry["framework"] for entry in data}
    expected = {"fastapi", "django", "spring", "go", "nestjs"}
    assert expected.issubset(frameworks_covered)


def test_body_hints_returns_structured_hint_for_fastapi_router():
    proc = _run("body_hints.py", "--framework", "fastapi", "--kind", "fastapi_router")
    data = json.loads(proc.stdout)
    assert data["language"] == "python"
    assert "imports_must_include" in data
    assert "must_emit_endpoints" in data
    assert "anti_patterns" in data


def test_body_hints_returns_structured_hint_for_django_viewset():
    proc = _run("body_hints.py", "--framework", "django", "--kind", "drf_viewset")
    data = json.loads(proc.stdout)
    assert data["language"] == "python"
    assert any("ModelViewSet" in s for s in data.get("class_decl", "").split("\n")) \
        or "ModelViewSet" in str(data)


def test_body_hints_unknown_pair_exits_nonzero():
    proc = _run("body_hints.py", "--framework", "fastapi", "--kind", "no_such_kind")
    assert proc.returncode != 0


# ─── promote_rule ───────────────────────────────────────────────────────────

def test_promote_rule_emits_python_stub_from_candidate(tmp_path):
    (tmp_path / ".beads").mkdir()
    failures = tmp_path / ".beads" / "proposed_patch_rules.jsonl"
    candidate = {
        "id": "rule-test-001",
        "ts": "2026-05-18T00:00:00Z",
        "trigger_pattern": r"async\ def\ list_items\(\):",
        "replacement_template": "async def list_items() -> list:",
        "sample_files": ["product/router.py"],
        "diagnostic_signature": "",
        "occurrences": 3,
        "promoted_to_auto_patch": False,
    }
    failures.write_text(json.dumps(candidate) + "\n", encoding="utf-8")
    proc = _run("promote_rule.py",
                "--rule-id", "rule-test-001",
                "--repo-root", str(tmp_path))
    assert proc.returncode == 0, proc.stderr
    out = proc.stdout
    assert "def _patch_rule_test_001" in out
    assert "_RULE_P5_TRIGGER" in out
    assert "PatchAction" in out


def test_promote_rule_errors_on_missing_id(tmp_path):
    proc = _run("promote_rule.py",
                "--rule-id", "rule-does-not-exist",
                "--repo-root", str(tmp_path))
    assert proc.returncode != 0


# ─── sast_runner ────────────────────────────────────────────────────────────

def test_sast_runner_handles_missing_bandit_gracefully(tmp_path):
    """When bandit isn't installed, the runner reports unavailable and
    exits 0 (no-op gate, not a failure)."""
    proc = _run("sast_runner.py", "--dir", str(tmp_path), "--json")
    # If bandit IS installed, returncode 0 (clean) or 2 (findings).
    # If bandit isn't installed, returncode 0 with available=False.
    assert proc.returncode in (0, 2), proc.stderr
    data = json.loads(proc.stdout)
    assert "available" in data


# ─── route-override wiring ──────────────────────────────────────────────────

def test_skill_md_documents_route_override_application():
    skill = REPO_ROOT / "skills" / "one-shot-generate" / "SKILL.md"
    text = skill.read_text(encoding="utf-8")
    assert "Stage 1.7" in text
    assert "route-override" in text
    assert "replaces_local" in text


# ─── Telemetry on hot-paths ─────────────────────────────────────────────────

def test_telemetry_decorator_applied_to_verify_directory():
    text = (SCRIPTS / "generate_and_verify.py").read_text(encoding="utf-8")
    assert "@_traced" in text
    assert "verify_directory" in text


def test_telemetry_decorator_applied_to_auto_patch():
    text = (SCRIPTS / "auto_patch.py").read_text(encoding="utf-8")
    assert "@_traced" in text


def test_telemetry_decorator_applied_to_auto_wirer():
    text = (SCRIPTS / "auto_wirer.py").read_text(encoding="utf-8")
    assert "@_traced" in text


def test_telemetry_decorator_applied_to_critic_runner():
    text = (SCRIPTS / "critic_runner.py").read_text(encoding="utf-8")
    assert "@_traced" in text


def test_telemetry_decorator_applied_to_scaffold_planner():
    text = (SCRIPTS / "scaffold_planner.py").read_text(encoding="utf-8")
    assert "@_traced" in text


# ─── Marketplace + CI + tutorial ────────────────────────────────────────────

def test_marketplace_submission_md_exists():
    path = REPO_ROOT / "MARKETPLACE_SUBMISSION.md"
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "v3.5.0" in text
    assert "submission" in text.lower()


def test_cross_os_ci_yaml_exists_and_has_matrix():
    path = REPO_ROOT / ".github" / "workflows" / "cross-os.yml"
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "ubuntu-latest" in text
    assert "macos-latest" in text
    assert "windows-latest" in text


def test_cookbook_doc_exists_with_three_examples():
    path = REPO_ROOT / "docs" / "cookbook.md"
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "Example 1" in text
    assert "Example 2" in text
    assert "Example 3" in text
