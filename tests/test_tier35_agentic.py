"""Tests for the Tier 3.5 agentic restructure.

We can't directly invoke Claude agents from pytest — those require the
Claude Code runtime. But we CAN assert that:

  1. The /one-shot slash command exists with proper frontmatter.
  2. The one-shot-generate SKILL.md exists and references the right
     scripts/agents.
  3. Every agent definition has both `tools:` and `model:` frontmatter
     so it's invocable via Task.
  4. scaffold_planner.py produces a structurally-correct plan.json from
     a spec.
  5. cost_budget.py emits believable USD figures within a budget gate.
  6. The thin phase 4-5 stubs are gone from the scripts directory.
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
AGENTS = REPO_ROOT / "agents"
COMMANDS = REPO_ROOT / "commands"
SKILLS = REPO_ROOT / "skills"


def _run(script: str, *args: str) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args],
        capture_output=True, text=True, env=env, encoding="utf-8",
        timeout=60,
    )


# ─── Slash command ──────────────────────────────────────────────────────────

def test_one_shot_slash_command_exists_with_frontmatter():
    cmd_path = COMMANDS / "one-shot.md"
    assert cmd_path.exists(), "commands/one-shot.md must exist"
    text = cmd_path.read_text(encoding="utf-8")
    assert text.startswith("---"), "command must have YAML frontmatter"
    # Required keys for a real Claude Code slash command
    assert re.search(r"^description:", text, re.MULTILINE), "missing description"
    assert re.search(r"^argument-hint:", text, re.MULTILINE), "missing argument-hint"
    assert re.search(r"^allowed-tools:", text, re.MULTILINE), "missing allowed-tools"
    # Must reference the new skill
    assert "one-shot-generate" in text, "command must invoke one-shot-generate skill"


# ─── Main skill ─────────────────────────────────────────────────────────────

def test_one_shot_generate_skill_exists():
    skill = SKILLS / "one-shot-generate" / "SKILL.md"
    assert skill.exists(), "skills/one-shot-generate/SKILL.md must exist"


def test_skill_has_valid_frontmatter():
    from conftest import pipeline_text
    text = pipeline_text()
    assert text.startswith("---"), "SKILL.md must have YAML frontmatter"
    for required in ("name:", "description:", "allowed-tools:"):
        assert re.search(rf"^{required}", text, re.MULTILINE), \
            f"SKILL.md missing {required}"


def test_skill_references_the_six_agents():
    """The agentic playbook must mention every specialist agent."""
    from conftest import pipeline_text
    text = pipeline_text().lower()
    for agent in ("architect", "implementer", "test-author",
                   "reviewer", "wirer", "critic"):
        assert agent in text, f"SKILL.md missing reference to {agent}"


def test_skill_references_deterministic_scripts():
    """The skill must call the deterministic services in the right order."""
    from conftest import pipeline_text
    text = pipeline_text()
    for script in ("extract_domain_model", "codebase_graph",
                    "beads_curriculum", "generate_and_verify",
                    "auto_patch", "auto_wirer", "critic_runner",
                    "beads_writer"):
        assert script in text, f"SKILL.md missing call to {script}"


# ─── Agent definitions ─────────────────────────────────────────────────────

def test_every_agent_has_tools_and_model_frontmatter():
    """Each agent .md must declare its tools + model to be Task-spawnable."""
    expected_agents = {"architect", "implementer", "test-author",
                       "reviewer", "wirer", "critic"}
    for name in expected_agents:
        path = AGENTS / f"{name}.md"
        assert path.exists(), f".claude/agents/{name}.md must exist"
        text = path.read_text(encoding="utf-8")
        front_match = re.search(r"^---\n(.+?)\n---", text, re.DOTALL)
        assert front_match, f"{name}.md must have YAML frontmatter"
        front = front_match.group(1)
        assert re.search(r"^tools:", front, re.MULTILINE), \
            f"{name}.md missing tools:"
        assert re.search(r"^model:", front, re.MULTILINE), \
            f"{name}.md missing model:"


def test_implementer_and_wirer_use_haiku():
    """Cost optimisation: file-writers use Haiku not Sonnet."""
    for name in ("implementer", "wirer"):
        text = (AGENTS / f"{name}.md").read_text(encoding="utf-8")
        assert re.search(r"^model:\s*haiku\b", text, re.MULTILINE), \
            f"{name}.md should use haiku for cost savings"


# ─── scaffold_planner ───────────────────────────────────────────────────────

def _build_spec(entities, relationships=None, graph_imports=None):
    return {
        "feature": "test feature",
        "intent": "feature",
        "framework": "fastapi",
        "language": "python",
        "test_contract": {"auth": "none", "pagination": "list"},
        "entities": entities,
        "api_surface": [],
        "wiring": {"framework": "fastapi"},
        "relationships": relationships or [],
        "graph_imports": graph_imports or {},
    }


def test_scaffold_planner_emits_paths_per_entity(tmp_path):
    spec = _build_spec([
        {"name": "Cart", "snake_name": "cart", "plural": "carts",
         "action": "create",
         "attributes": [{"name": "status", "type_hint": "str", "required": True}]},
    ])
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec))
    proc = _run("scaffold_planner.py", "--spec", str(spec_path))
    assert proc.returncode == 0, proc.stderr
    plan = json.loads(proc.stdout)
    paths = [f["path"] for f in plan["files_to_create"]]
    assert "cart/models.py" in paths
    assert "cart/router.py" in paths
    assert "cart/schemas.py" in paths
    assert "tests/test_cart_api.py" in paths


def test_scaffold_planner_derives_fks_from_relationships(tmp_path):
    spec = _build_spec(
        entities=[
            {"name": "Cart", "snake_name": "cart", "plural": "carts",
             "action": "create", "attributes": []},
            {"name": "LineItem", "snake_name": "line_item",
             "plural": "line_items", "action": "create", "attributes": []},
        ],
        relationships=[{"from": "cart", "to": "line_item", "kind": "has_many"}],
    )
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec))
    proc = _run("scaffold_planner.py", "--spec", str(spec_path))
    plan = json.loads(proc.stdout)
    line_item_model = next(f for f in plan["files_to_create"]
                           if f["path"] == "line_item/models.py")
    assert any(fk["col"] == "cart_id" for fk in line_item_model["fk_columns"]), \
        line_item_model


def test_scaffold_planner_flags_stubs_when_get_db_missing(tmp_path):
    spec = _build_spec([
        {"name": "X", "snake_name": "x", "plural": "xs", "action": "create",
         "attributes": []}
    ])
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec))
    proc = _run("scaffold_planner.py", "--spec", str(spec_path))
    plan = json.loads(proc.stdout)
    assert "database.py" in plan["stubs_needed"]


def test_scaffold_planner_skips_stub_when_get_db_present(tmp_path):
    spec = _build_spec(
        entities=[{"name": "X", "snake_name": "x", "plural": "xs",
                   "action": "create", "attributes": []}],
        graph_imports={
            "db_session_getter": {"name": "get_db", "module": "app.deps"},
            "model_base": {"name": "Base", "module": "models"},
        },
    )
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec))
    proc = _run("scaffold_planner.py", "--spec", str(spec_path))
    plan = json.loads(proc.stdout)
    assert plan["stubs_needed"] == []
    # And the file specs should carry the discovered db_func / module
    model_file = next(f for f in plan["files_to_create"]
                      if f["path"] == "x/router.py")
    assert model_file["db_module"] == "app.deps"
    assert model_file["db_func"] == "get_db"


# ─── cost_budget ────────────────────────────────────────────────────────────

def test_cost_budget_emits_reasonable_estimate(tmp_path):
    plan = {
        "feature": "test",
        "framework": "fastapi",
        "files_to_create": [
            {"path": "x/models.py",  "kind": "sqlalchemy_model"},
            {"path": "x/router.py",  "kind": "fastapi_router"},
            {"path": "x/schemas.py", "kind": "pydantic_schema"},
        ],
        "stubs_needed": [], "wiring_targets": ["main.py"],
        "migrations": [], "relationships": [],
    }
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan))
    proc = _run("cost_budget.py", "--plan", str(plan_path), "--json")
    assert proc.returncode == 0, proc.stderr
    est = json.loads(proc.stdout)
    # Total should land in cents-to-dollar range; sanity check bounds
    assert 0.05 < est["total_usd"] < 5.00, est
    agents_in = {line["agent"] for line in est["breakdown"]}
    assert {"architect", "implementer", "reviewer", "critic"} <= agents_in


def test_cost_budget_exits_2_when_over_budget(tmp_path):
    plan = {
        "feature": "test", "framework": "fastapi",
        "files_to_create": [{"path": "x/router.py", "kind": "fastapi_router"}],
        "stubs_needed": [], "wiring_targets": [], "migrations": [],
        "relationships": [],
    }
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan))
    proc = _run("cost_budget.py", "--plan", str(plan_path),
                "--budget", "0.001", "--json")
    assert proc.returncode == 2
    est = json.loads(proc.stdout)
    assert est["within_budget"] is False


# ─── Stub archival ──────────────────────────────────────────────────────────

def test_thin_stubs_were_archived():
    """The 9 thin Phase 5 placeholders must not be in scripts/.
    If .archive/ is present locally, also verify the files landed there."""
    archived_dir = REPO_ROOT / ".archive" / "phase4-5-aspirational"
    expected_archived = [
        "phase5_advanced_caching.py", "phase5_blockchain_consensus.py",
        "phase5_content_delivery.py", "phase5_data_residency.py",
        "phase5_edge_computing.py", "phase5_fraud_detection.py",
        "phase5_graphql_caching.py", "phase5_iot_patterns.py",
        "phase5_request_deduplication.py",
    ]
    for name in expected_archived:
        if archived_dir.exists():
            assert (archived_dir / name).exists(), f"{name} should be archived"
        assert not (SCRIPTS / name).exists(), \
            f"{name} should be REMOVED from scripts/ (it was archived)"


def test_archive_has_readme():
    """If .archive/ is present, it must contain a README. Skipped on CI
    where .archive/ is gitignored and therefore absent."""
    readme = REPO_ROOT / ".archive" / "phase4-5-aspirational" / "README.md"
    if not readme.parent.exists():
        import pytest
        pytest.skip(".archive/ not present (gitignored on CI)")
    assert readme.exists(), "archive must have a README explaining why"
