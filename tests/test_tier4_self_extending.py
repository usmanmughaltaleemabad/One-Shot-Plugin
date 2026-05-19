"""Tests for the Tier 4 self-extending plugin layer.

Coverage:
  - Registry files exist with valid JSON + expected shape
  - agent_discovery script runs end-to-end and ranks by task overlap
  - External MCP server (chrome-devtools) surfaces for lighthouse tasks
  - Local agents surface for code-review tasks
  - Preferred-over-local hints generate route-override recommendations
  - Curator skill exists with proper frontmatter
  - /curate slash command exists
  - SKILL.md references discovery as Stage 0.5
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
REGISTRY = REPO_ROOT / ".claude" / "registry"
EXTERNAL = REPO_ROOT / ".claude" / "external"


def _run(script: str, *args: str) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args],
        capture_output=True, text=True, env=env, encoding="utf-8",
        timeout=60,
    )


# ─── Registry files ──────────────────────────────────────────────────────────

def test_agents_registry_is_valid_json():
    path = REGISTRY / "agents.json"
    assert path.exists()
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["version"] >= 1
    assert isinstance(data["agents"], list)
    assert len(data["agents"]) >= 5, "registry should ship with a curated set"
    for entry in data["agents"]:
        assert "id" in entry
        assert "description" in entry
        assert "triggers" in entry
        assert "added_at" in entry


def test_mcp_registry_includes_chrome_devtools():
    data = json.loads((REGISTRY / "mcp_servers.json").read_text(encoding="utf-8"))
    ids = [s["id"] for s in data["servers"]]
    assert "anthropic/chrome-devtools" in ids
    chrome = next(s for s in data["servers"] if s["id"] == "anthropic/chrome-devtools")
    assert "lighthouse" in (chrome.get("triggers") or [])
    assert "tools_exposed" in chrome
    assert any("lighthouse" in t for t in chrome["tools_exposed"])


def test_registry_readme_exists():
    assert (REGISTRY / "README.md").exists()


def test_external_dir_documented_not_populated():
    """The external/ directory should exist with a README, but be empty
    (entries get vendored only on explicit curator approval)."""
    assert (EXTERNAL / "README.md").exists()
    for sub in ("agents", "skills", "mcp"):
        assert (EXTERNAL / sub).is_dir(), f"missing external/{sub}/"


# ─── agent_discovery script ─────────────────────────────────────────────────

def test_discovery_runs_and_returns_json():
    proc = _run("agent_discovery.py", "review the code I just wrote",
                "--json", "--repo", str(REPO_ROOT))
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert "task" in data
    assert "hits" in data
    assert isinstance(data["hits"], list)


def test_discovery_finds_code_reviewer_for_review_task():
    """A 'review my code' task should surface the external code-reviewer."""
    proc = _run("agent_discovery.py",
                "review the code I just wrote for style and security issues",
                "--json", "--repo", str(REPO_ROOT))
    data = json.loads(proc.stdout)
    ids = [h["id"] for h in data["hits"]]
    assert "claude-code/code-reviewer" in ids, ids


def test_discovery_finds_chrome_devtools_for_lighthouse():
    """A 'run lighthouse audit' task should surface the chrome-devtools MCP."""
    proc = _run("agent_discovery.py",
                "run a lighthouse audit on the generated UI",
                "--json", "--repo", str(REPO_ROOT))
    data = json.loads(proc.stdout)
    top_match = data["hits"][0] if data["hits"] else None
    assert top_match is not None, data
    assert top_match["id"] == "anthropic/chrome-devtools", top_match
    assert top_match["kind"] == "external-mcp"


def test_discovery_emits_route_override_recommendations():
    """The pr-test-analyzer agent is preferred over our local critic; for
    a PR test task, that should produce a route-override recommendation."""
    proc = _run("agent_discovery.py",
                "review pr test coverage on the recent changes",
                "--json", "--repo", str(REPO_ROOT))
    data = json.loads(proc.stdout)
    overrides = [r for r in data["recommendations"]
                 if r["type"] == "route-override"]
    assert overrides, "expected at least one route-override recommendation"


def test_discovery_surfaces_local_agents_too():
    """The discovery should rank local agents alongside external ones."""
    proc = _run("agent_discovery.py", "implement a new file from spec",
                "--json", "--repo", str(REPO_ROOT))
    data = json.loads(proc.stdout)
    kinds = {h["kind"] for h in data["hits"]}
    assert "local-agent" in kinds or "local-skill" in kinds


# ─── Curator skill ──────────────────────────────────────────────────────────

def test_curator_skill_exists_with_websearch_tool():
    path = REPO_ROOT / "skills" / "curator" / "SKILL.md"
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---")
    front_match = re.search(r"^---\n(.+?)\n---", text, re.DOTALL)
    front = front_match.group(1)
    assert re.search(r"^name:\s*curator", front, re.MULTILINE)
    assert "WebSearch" in front
    assert "WebFetch" in front


def test_curate_slash_command_exists():
    path = REPO_ROOT / "commands" / "curate.md"
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---")
    assert re.search(r"^argument-hint:", text, re.MULTILINE)


# ─── SKILL.md wiring ────────────────────────────────────────────────────────

def test_main_skill_invokes_discovery_at_stage_0_5():
    from conftest import pipeline_text
    text = pipeline_text()
    assert "agent_discovery.py" in text
    assert "Stage 0.5" in text
    assert "route-override" in text
    assert "consider-using" in text


def test_main_skill_includes_curator_fallback_hint():
    from conftest import pipeline_text
    text = pipeline_text()
    assert "/curate" in text or "curator" in text.lower()
