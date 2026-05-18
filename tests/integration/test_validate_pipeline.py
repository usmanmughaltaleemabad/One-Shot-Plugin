"""Pytest wrapper around the end-to-end validator.

Runs `validate_templated_pipeline.py` against a synthetic FastAPI
project and asserts every stage passes. This is a meta-test — it's
already covered by the validator's own exit code, but wrapping it in
pytest gives:

  - automatic invocation as part of `pytest tests/`
  - a clear failure message in the CI dashboard if a single stage breaks
  - integration with the rest of the suite's reporting

Tests the canary's guard rails too (no flag → exit 1, dry-run with no
key → graceful skip, etc.) without spending any money.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = REPO_ROOT / "tests" / "integration" / "validate_templated_pipeline.py"
CANARY = REPO_ROOT / "tests" / "integration" / "canary_live_api.py"


def _run(script: Path, *args: str, timeout: int = 120,
         env_overrides: dict | None = None) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True, text=True, env=env, encoding="utf-8",
        timeout=timeout,
    )


# ─── validate_templated_pipeline.py ────────────────────────────────────────

def test_full_pipeline_validator_passes_end_to_end():
    """Run all 15 templated-mode stages against a synthetic FastAPI
    project. Asserts the validator exits 0 (all stages PASS)."""
    proc = _run(VALIDATOR, timeout=180)
    assert proc.returncode == 0, (
        f"validator exited {proc.returncode}\n"
        f"stdout tail:\n{proc.stdout[-800:]}\n"
        f"stderr:\n{proc.stderr[-400:]}"
    )
    # Sanity: the output mentions all 15 named stages
    expected_stages = [
        "extract_domain_model", "codebase_graph", "scaffold_planner",
        "incremental_planner", "source_docs_fetcher", "body_hints",
        "critic_loop_driver", "doubt_driver", "adr_writer",
        "ship_gates", "cost_budget", "cost_calibrator",
        "run_finalize", "learnings_hub_dashboard", "live_api_graceful_skip",
    ]
    missing = [s for s in expected_stages if s not in proc.stdout]
    assert not missing, f"validator skipped stages: {missing}"
    # Final summary line must claim 0 failures
    assert "0 fail" in proc.stdout, \
        f"validator reported failures: {proc.stdout[-300:]}"


def test_validator_verbose_flag_emits_artifact_paths():
    """--verbose prints artifact: lines under stages that produce files."""
    proc = _run(VALIDATOR, "--verbose", timeout=180)
    assert proc.returncode == 0
    assert "artifact:" in proc.stdout, \
        "--verbose should surface per-stage artifact paths"


def test_validator_keep_temp_does_not_remove_project(tmp_path):
    """--keep-temp + --temp-dir: validator should NOT delete the project."""
    project_root = tmp_path / "kept"
    proc = _run(VALIDATOR, "--keep-temp", "--temp-dir", str(project_root),
                timeout=180)
    assert proc.returncode == 0
    assert project_root.exists(), "project removed despite --keep-temp"
    assert (project_root / "fake-fastapi").exists(), \
        "synthetic project missing after run"
    # Should also contain the artifacts each stage produces
    fastapi = project_root / "fake-fastapi"
    assert (fastapi / "spec.json").exists()
    assert (fastapi / "domain.json").exists()
    assert (fastapi / "plan.json").exists()
    assert (fastapi / "docs" / "adr").is_dir()


# ─── canary_live_api.py (dry-run + guards only — no money spent) ─────────

def test_canary_dry_run_succeeds_without_api_key(monkeypatch):
    """--dry-run walks the harness without an API key. Validates the
    live-api graceful-skip path executes cleanly."""
    proc = _run(CANARY, "--dry-run",
                env_overrides={"ANTHROPIC_API_KEY": ""}, timeout=30)
    assert proc.returncode == 0, \
        f"dry-run failed: {proc.stderr[:500]}"
    assert "DRY-RUN" in proc.stdout
    assert "missing_anthropic_api_key" in proc.stdout, \
        "expected graceful-skip reason in output"


def test_canary_refuses_without_consent_flag():
    """No --i-know-this-costs-money + no --dry-run → exit 1 + clear abort
    message. This is the safety guard against accidental spends."""
    proc = _run(CANARY, env_overrides={"ANTHROPIC_API_KEY": ""}, timeout=30)
    assert proc.returncode == 1
    assert "cost real money" in proc.stderr
    assert "--i-know-this-costs-money" in proc.stderr


def test_canary_refuses_with_consent_but_no_key():
    """User said yes to spending but has no key → exit 1 + key-missing message."""
    proc = _run(CANARY, "--i-know-this-costs-money",
                env_overrides={"ANTHROPIC_API_KEY": ""}, timeout=30)
    assert proc.returncode == 1
    assert "ANTHROPIC_API_KEY" in proc.stderr
