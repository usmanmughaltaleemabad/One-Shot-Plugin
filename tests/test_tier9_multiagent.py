"""Tier 9 tests: pass^k, learnings hub, session driver, extractor agent."""

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
        timeout=120,
    )


# ─── pass_k_runner ──────────────────────────────────────────────────────────

def test_pass_k_runner_deterministic_replay_passes():
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        [sys.executable, str(EVALS / "pass_k_runner.py"),
         "--mode", "deterministic-replay", "--k", "3", "--json"],
        capture_output=True, text=True, env=env, encoding="utf-8",
        timeout=120,
    )
    data = json.loads(proc.stdout)
    summary = data["summary"]
    assert summary["k"] == 3
    # Deterministic re-runs should ALL pass^k (variance = 0)
    assert summary["all_pass_at_k"] == summary["total"]
    assert summary["mean_variance"] == 0.0


def test_pass_k_runner_agentic_flake_check_runs():
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        [sys.executable, str(EVALS / "pass_k_runner.py"),
         "--mode", "agentic-flake-check", "--k", "5", "--json"],
        capture_output=True, text=True, env=env, encoding="utf-8",
        timeout=30,
    )
    data = json.loads(proc.stdout)
    assert data["summary"]["k"] == 5
    assert "per_eval" in data


# ─── learnings_hub ──────────────────────────────────────────────────────────

def test_learnings_hub_record_and_rate(tmp_path):
    # Record 5 succeeds + 1 fail for an agent
    for i in range(5):
        _run("learnings_hub.py", "--repo-root", str(tmp_path),
             "record", "--agent", "claude-code/code-reviewer",
             "--outcome", "succeeded", "--task-keywords", "code", "review",
             "--duration-ms", "12000", "--cost-usd", "0.05")
    _run("learnings_hub.py", "--repo-root", str(tmp_path),
         "record", "--agent", "claude-code/code-reviewer",
         "--outcome", "failed", "--task-keywords", "code", "review")

    proc = _run("learnings_hub.py", "--repo-root", str(tmp_path),
                "rate", "--agent", "claude-code/code-reviewer")
    rating = json.loads(proc.stdout)
    assert rating["sample_count"] == 6
    assert rating["success_rate"] == round(5 / 6, 3)
    assert rating["overall_rating"] > 0.5


def test_learnings_hub_top_agents(tmp_path):
    # Two agents, one with better track record
    for _ in range(8):
        _run("learnings_hub.py", "--repo-root", str(tmp_path),
             "record", "--agent", "alpha", "--outcome", "succeeded")
    _run("learnings_hub.py", "--repo-root", str(tmp_path),
         "record", "--agent", "beta", "--outcome", "succeeded")
    _run("learnings_hub.py", "--repo-root", str(tmp_path),
         "record", "--agent", "beta", "--outcome", "failed")

    proc = _run("learnings_hub.py", "--repo-root", str(tmp_path),
                "top-agents")
    ratings = json.loads(proc.stdout)
    assert len(ratings) == 2
    # alpha should rank higher (more samples, 100% success)
    assert ratings[0]["agent_id"] == "alpha"


def test_learnings_hub_export_anonymized_strips_identity(tmp_path):
    _run("learnings_hub.py", "--repo-root", str(tmp_path),
         "record", "--agent", "secret-internal-tool",
         "--outcome", "succeeded", "--notes", "internal prod stuff")
    proc = _run("learnings_hub.py", "--repo-root", str(tmp_path),
                "export-anonymized")
    data = json.loads(proc.stdout)
    assert data["total"] == 1
    entry = data["learnings"][0]
    assert "agent_id" not in entry
    assert "notes" not in entry
    assert "agent_id_hash" in entry
    assert len(entry["agent_id_hash"]) == 12


def test_learnings_hub_rate_unknown_agent_returns_neutral_prior(tmp_path):
    proc = _run("learnings_hub.py", "--repo-root", str(tmp_path),
                "rate", "--agent", "completely-unknown")
    rating = json.loads(proc.stdout)
    assert rating["sample_count"] == 0
    assert rating["success_rate"] == 0.5   # neutral prior


# ─── agentic_session_driver ─────────────────────────────────────────────────

def test_session_driver_dry_run_produces_plan(tmp_path):
    spec = {
        "feature": "test feature",
        "framework": "fastapi",
        "intent": "auth",   # triggers service-author
        "entities": [
            {"name": "User", "snake_name": "user", "plural": "users",
             "action": "create",
             "invariants": ["email must be unique"]},
            {"name": "Session", "snake_name": "session", "plural": "sessions",
             "action": "create"},
        ],
        "relationships": [],
    }
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec))
    proc = _run("agentic_session_driver.py", "--spec", str(spec_path),
                "--mode", "dry-run", "--json")
    plan = json.loads(proc.stdout)
    spawn_names = [s["agent_name"] for s in plan["spawns"]]
    assert "architect" in spawn_names
    assert "service-author" in spawn_names   # because auth intent
    assert "test-author" in spawn_names
    assert any(n.startswith("implementer-") for n in spawn_names)
    assert "reviewer" in spawn_names
    assert "critic" in spawn_names
    assert plan["total_estimated_usd"] > 0


def test_session_driver_record_mode_writes_templates(tmp_path):
    spec = {
        "feature": "test", "framework": "fastapi",
        "entities": [{"name": "Cart", "snake_name": "cart",
                      "plural": "carts", "action": "create"}],
        "relationships": [],
    }
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec))
    out_dir = tmp_path / "session"
    proc = _run("agentic_session_driver.py", "--spec", str(spec_path),
                "--mode", "record", "--out", str(out_dir))
    assert proc.returncode == 0, proc.stderr
    assert (out_dir / "_plan.json").exists()
    template_files = list(out_dir.glob("[0-9]*.json"))
    assert len(template_files) >= 4  # architect + implementer + test-author + reviewer + critic
    template = json.loads(template_files[0].read_text())
    assert template["recorded_output"] is None
    assert "instructions" in template


# ─── extractor agent ────────────────────────────────────────────────────────

def test_extractor_agent_exists_with_proper_frontmatter():
    path = REPO_ROOT / ".claude" / "agents" / "extractor.md"
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    front = re.search(r"^---\n(.+?)\n---", text, re.DOTALL).group(1)
    assert "tools:" in front
    assert "model: sonnet" in front
    assert "name: extractor" in front
    # Body should explain its niche (low-confidence fallback)
    assert "confidence < 0.55" in text or "low-confidence" in text.lower()
    assert "many_to_many" in text  # mentions the relationship class
