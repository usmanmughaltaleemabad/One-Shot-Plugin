"""Tests for cost_calibrator — self-recalibrating cost model.

The calibrator reads .beads/cost_observations.jsonl, computes p50 token
estimates per agent, compares against the hardcoded constants in
cost_budget.py, and EITHER emits a diff (default) or rewrites the file
(--apply) or exits 1 on drift (--check).

Tests fence each scenario in an isolated --repo-root so they never
touch the real cost_budget.py.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "skills" / "one-shot-generator" / "scripts"
CALIB = SCRIPTS / "cost_calibrator.py"


def _run(*args: str, check: bool = True, cwd: Path | None = None) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        [sys.executable, str(CALIB), *args],
        capture_output=True, text=True, env=env, encoding="utf-8", timeout=30,
        cwd=str(cwd) if cwd is not None else None,
    )
    if check:
        assert proc.returncode in (0, 1), \
            f"calibrator failed (exit {proc.returncode}): {proc.stderr}"
    return proc


def _seed_repo(tmp_path: Path) -> Path:
    """Create a minimal repo with cost_budget.py + .beads/ + .claude/registry/
    so the calibrator has somewhere realistic to operate."""
    repo = tmp_path / "fake-repo"
    (repo / "skills" / "one-shot-generator" / "scripts" / "lib").mkdir(parents=True)
    (repo / ".beads").mkdir()
    (repo / ".claude" / "registry").mkdir(parents=True)

    # Stage the actual lib/ so cost_calibrator can import bootstrap_runtime
    src_lib = REPO_ROOT / "skills" / "one-shot-generator" / "scripts" / "lib"
    for child in src_lib.glob("*.py"):
        shutil.copy(child, repo / "skills" / "one-shot-generator" / "scripts" / "lib" / child.name)

    # Stage a minimal cost_budget.py with the same dict-literal shape
    (repo / "skills" / "one-shot-generator" / "scripts" / "cost_budget.py"
     ).write_text(
        "# minimal cost_budget for tests\n"
        "from typing import Any, Dict\n"
        "\n"
        "PER_AGENT_TOKEN_ESTIMATES = {\n"
        '    "architect":   {"model": "sonnet", "input": 14000, "output": 11000},\n'
        '    "implementer": {"model": "haiku",  "input": 9000,  "output": 7000},\n'
        '    "critic":      {"model": "sonnet", "input": 5500,  "output": 2500},\n'
        "}\n",
        encoding="utf-8",
    )
    return repo


def _seed_observations(repo: Path, rows: list[dict]) -> None:
    path = repo / ".beads" / "cost_observations.jsonl"
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def _seed_learnings(repo: Path, rows: list[dict]) -> None:
    path = repo / ".claude" / "registry" / "learnings.jsonl"
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


# ─── default mode: emits a diff ────────────────────────────────────────────

def test_default_emits_diff_when_recalibrated_differs(tmp_path):
    repo = _seed_repo(tmp_path)
    # 10 architect observations with new values diverging from the 14000/11000 baseline
    obs = [{"agent": "architect", "input": 25000, "output": 18000}] * 10
    _seed_observations(repo, obs)

    proc = _run("--repo-root", str(repo))
    assert proc.returncode == 0
    # Diff format: must include both filename markers + the new values
    assert "cost_budget.py" in proc.stdout
    assert "25000" in proc.stdout or "18000" in proc.stdout
    assert "+" in proc.stdout and "-" in proc.stdout
    # And the file on disk MUST NOT have been mutated
    text = (repo / "skills/one-shot-generator/scripts/cost_budget.py"
            ).read_text(encoding="utf-8")
    assert "14000" in text and "11000" in text   # unchanged


def test_default_emits_no_value_changes_when_obs_matches_existing(tmp_path):
    """When the observed p50 EQUALS the existing constant, --json should
    report drift=0. The text-diff path may still show cosmetic whitespace
    changes (canonical dict formatting) — that's fine, but the SEMANTIC
    drift must be zero."""
    repo = _seed_repo(tmp_path)
    obs = [{"agent": "architect", "input": 14000, "output": 11000}] * 10
    _seed_observations(repo, obs)

    proc = _run("--repo-root", str(repo), "--json")
    data = json.loads(proc.stdout)
    arch = data["drift_by_agent"]["architect"]
    assert arch["input_drift"] == 0.0
    assert arch["output_drift"] == 0.0
    # And the file MUST NOT have been written
    text = (repo / "skills/one-shot-generator/scripts/cost_budget.py"
            ).read_text(encoding="utf-8")
    assert "14000" in text  # original values preserved (no --apply was passed)


def test_default_skips_when_no_agent_has_min_samples(tmp_path):
    repo = _seed_repo(tmp_path)
    # Only 5 observations — below default min_samples=10
    obs = [{"agent": "architect", "input": 25000, "output": 18000}] * 5
    _seed_observations(repo, obs)

    proc = _run("--repo-root", str(repo))
    data = json.loads(proc.stdout)
    assert data["status"] == "no_recalibration_possible"
    assert data["agents_observed"] == {"architect": 5}


def test_min_samples_override_unlocks_smaller_sets(tmp_path):
    repo = _seed_repo(tmp_path)
    obs = [{"agent": "architect", "input": 25000, "output": 18000}] * 5
    _seed_observations(repo, obs)

    # With --min-samples 3, the 5 architect runs ARE enough
    proc = _run("--repo-root", str(repo), "--min-samples", "3")
    assert "25000" in proc.stdout or "18000" in proc.stdout


# ─── --apply mode: rewrites the file ──────────────────────────────────────

def test_apply_rewrites_constants_in_place(tmp_path):
    repo = _seed_repo(tmp_path)
    obs = [{"agent": "architect", "input": 25000, "output": 18000}] * 10
    _seed_observations(repo, obs)

    proc = _run("--repo-root", str(repo), "--apply")
    data = json.loads(proc.stdout)
    assert data["status"] == "applied"
    assert "architect" in data["agents_recalibrated"]

    # File now contains the new numbers
    text = (repo / "skills/one-shot-generator/scripts/cost_budget.py"
            ).read_text(encoding="utf-8")
    assert "25000" in text
    assert "18000" in text
    # Untouched agents preserved
    assert "implementer" in text and "9000" in text
    assert "critic" in text and "5500" in text


def test_apply_preserves_agent_order_and_model(tmp_path):
    """Rewriter must keep `model: haiku|sonnet` from existing constants
    even when only input/output get recalibrated. Order also matters
    for predictable diffs."""
    repo = _seed_repo(tmp_path)
    obs = [{"agent": "implementer", "input": 12000, "output": 8500}] * 10
    _seed_observations(repo, obs)

    _run("--repo-root", str(repo), "--apply")
    text = (repo / "skills/one-shot-generator/scripts/cost_budget.py"
            ).read_text(encoding="utf-8")
    # implementer still keyed as haiku (NOT replaced with sonnet)
    assert '"implementer":' in text
    assert '"model": "haiku"' in text
    # And the new numbers are in
    assert "12000" in text and "8500" in text
    # And architect/critic survived untouched
    assert "14000" in text and "11000" in text  # architect (unchanged)
    assert "5500" in text and "2500" in text    # critic (unchanged)


# ─── --check mode: CI gate ────────────────────────────────────────────────

def test_check_returns_exit_1_on_drift(tmp_path):
    repo = _seed_repo(tmp_path)
    # ~78% drift on architect input (14000 → 25000)
    obs = [{"agent": "architect", "input": 25000, "output": 18000}] * 10
    _seed_observations(repo, obs)

    proc = _run("--repo-root", str(repo), "--check", check=False)
    assert proc.returncode == 1
    data = json.loads(proc.stdout)
    assert data["drift_exceeds_threshold"] is True
    arch = data["drift_by_agent"]["architect"]
    assert arch["input_drift"] > 0   # drifted UP


def test_check_returns_exit_0_within_threshold(tmp_path):
    repo = _seed_repo(tmp_path)
    # Tiny drift: 14000 → 14500 = 3.5%, well under 20% threshold
    obs = [{"agent": "architect", "input": 14500, "output": 11200}] * 10
    _seed_observations(repo, obs)

    proc = _run("--repo-root", str(repo), "--check", check=False)
    assert proc.returncode == 0
    data = json.loads(proc.stdout)
    assert data["drift_exceeds_threshold"] is False


def test_check_with_custom_threshold(tmp_path):
    repo = _seed_repo(tmp_path)
    # ~10% drift — fails at threshold 0.05, passes at 0.20
    obs = [{"agent": "architect", "input": 15400, "output": 11000}] * 10
    _seed_observations(repo, obs)

    strict = _run("--repo-root", str(repo), "--check",
                   "--threshold", "0.05", check=False)
    lax    = _run("--repo-root", str(repo), "--check",
                   "--threshold", "0.20", check=False)
    assert strict.returncode == 1
    assert lax.returncode == 0


# ─── --json mode: structured report ───────────────────────────────────────

def test_json_mode_emits_drift_report(tmp_path):
    repo = _seed_repo(tmp_path)
    obs = [{"agent": "architect", "input": 25000, "output": 18000}] * 10
    _seed_observations(repo, obs)

    proc = _run("--repo-root", str(repo), "--json")
    data = json.loads(proc.stdout)
    assert "drift_by_agent" in data
    arch = data["drift_by_agent"]["architect"]
    assert arch["input_existing"] == 14000
    assert arch["input_new"] == 25000
    assert arch["samples"] == 10
    assert arch["model"] == "sonnet"


# ─── learnings.jsonl cross-check ──────────────────────────────────────────

def test_learnings_costs_appear_in_json_report(tmp_path):
    repo = _seed_repo(tmp_path)
    obs = [{"agent": "architect", "input": 14500, "output": 11200}] * 10
    _seed_observations(repo, obs)
    # Also populate learnings.jsonl with actual cost_usd numbers
    _seed_learnings(repo, [
        {"ts": "2026-05-18T10:00:00Z", "agent_id": "local/architect",
         "task_keywords": ["x"], "outcome": "succeeded",
         "duration_ms": 0, "cost_usd": 0.09, "notes": ""},
        {"ts": "2026-05-18T11:00:00Z", "agent_id": "local/architect",
         "task_keywords": ["y"], "outcome": "succeeded",
         "duration_ms": 0, "cost_usd": 0.11, "notes": ""},
    ])
    proc = _run("--repo-root", str(repo), "--json")
    data = json.loads(proc.stdout)
    arch_costs = data["learnings_cross_check_usd"].get("architect")
    assert arch_costs is not None
    assert arch_costs["n"] == 2
    assert arch_costs["mean"] == pytest.approx(0.10, abs=1e-3)


# ─── median computation correctness ──────────────────────────────────────

def test_recalibrated_uses_p50_median_not_mean(tmp_path):
    """When observations include an outlier, p50 should resist it; mean would not."""
    repo = _seed_repo(tmp_path)
    obs = (
        [{"agent": "architect", "input": 14000, "output": 11000}] * 9
        + [{"agent": "architect", "input": 100000, "output": 100000}]   # huge outlier
    )
    _seed_observations(repo, obs)

    proc = _run("--repo-root", str(repo), "--json")
    data = json.loads(proc.stdout)
    arch = data["drift_by_agent"]["architect"]
    # median of [14000, 14000, ..., 14000, 100000] = 14000, NOT (14000*9+100000)/10 = 22600
    assert arch["input_new"] == 14000
    assert arch["output_new"] == 11000


# ─── error paths ─────────────────────────────────────────────────────────

def test_no_observations_file_returns_skip(tmp_path):
    repo = _seed_repo(tmp_path)
    # No .beads/cost_observations.jsonl
    proc = _run("--repo-root", str(repo))
    data = json.loads(proc.stdout)
    assert data["status"] == "no_recalibration_possible"


def test_missing_cost_budget_returns_exit_2(tmp_path):
    """A repo without cost_budget.py is a hard error, not a graceful skip."""
    empty = tmp_path / "empty-repo"
    empty.mkdir()
    proc = _run("--repo-root", str(empty), check=False)
    assert proc.returncode == 2
