"""Tests for Tier 8: turning scaffolding into production one-shot.

Covers: service-author agent, migration_generator, body_hints
service_layer + auth + events + exceptions entries, SKILL.md Stage 2.7
+ Stage 6.5 wiring.
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


def _run(script: str, *args: str) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args],
        capture_output=True, text=True, env=env, encoding="utf-8",
        timeout=60,
    )


# ─── service-author agent ───────────────────────────────────────────────────

def test_service_author_agent_exists():
    path = REPO_ROOT / ".claude" / "agents" / "service-author.md"
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    front = re.search(r"^---\n(.+?)\n---", text, re.DOTALL).group(1)
    assert "tools:" in front
    assert "model: sonnet" in front
    assert "service" in text.lower()
    assert "invariant" in text.lower()


def test_skill_md_invokes_service_author_at_stage_2_7():
    skill = REPO_ROOT / "skills" / "one-shot-generate" / "SKILL.md"
    text = skill.read_text(encoding="utf-8")
    assert "Stage 2.7" in text
    assert "service-author" in text
    assert "invariants" in text.lower()


# ─── migration_generator ────────────────────────────────────────────────────

def test_migration_generator_emits_alembic_revision(tmp_path):
    spec = {
        "feature": "shopping cart",
        "framework": "fastapi",
        "entities": [
            {"name": "ShoppingCart", "snake_name": "shopping_cart",
             "plural": "shopping_carts", "action": "create",
             "attributes": [
                 {"name": "user_id", "type_hint": "int", "required": True},
                 {"name": "status", "type_hint": "str", "required": True},
             ]},
            {"name": "LineItem", "snake_name": "line_item",
             "plural": "line_items", "action": "create",
             "attributes": [
                 {"name": "quantity", "type_hint": "int", "required": True},
             ]},
        ],
        "relationships": [
            {"from": "shopping_cart", "to": "line_item", "kind": "has_many"},
        ],
    }
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec))
    out_dir = tmp_path / "alembic" / "versions"
    out_dir.mkdir(parents=True)
    proc = _run("migration_generator.py", "--spec", str(spec_path),
                "--out", str(out_dir))
    assert proc.returncode == 0, proc.stderr
    files = list(out_dir.glob("*.py"))
    assert len(files) == 1
    text = files[0].read_text()
    # Both tables present
    assert "shopping_carts" in text
    assert "line_items" in text
    # FK on line_items
    assert "shopping_cart_id" in text
    assert "ForeignKey('shopping_carts.id')" in text
    # Index on FK
    assert "ix_line_items_shopping_cart_id" in text
    # Both upgrade and downgrade
    assert "def upgrade" in text
    assert "def downgrade" in text
    assert "op.drop_table('line_items')" in text


def test_migration_generator_django_emits_runbook(tmp_path):
    spec = {
        "feature": "test",
        "framework": "django",
        "entities": [
            {"name": "Cart", "snake_name": "cart", "plural": "carts",
             "action": "create", "attributes": []},
        ],
        "relationships": [],
    }
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec))
    proc = _run("migration_generator.py", "--spec", str(spec_path),
                "--framework", "django",
                "--out", str(tmp_path))
    assert proc.returncode == 0, proc.stderr
    assert (tmp_path / "MIGRATION_RUNBOOK.md").exists()
    text = (tmp_path / "MIGRATION_RUNBOOK.md").read_text()
    assert "makemigrations" in text
    assert "cart" in text


def test_migration_generator_dedups_default_fk_against_relationship_fk(tmp_path):
    """The line_item entity's hardcoded `cart_id` default attr should be
    dropped in favor of the relationship-derived `shopping_cart_id` FK.
    Same dedup logic as scaffold_planner."""
    spec = {
        "feature": "test",
        "framework": "fastapi",
        "entities": [
            {"name": "ShoppingCart", "snake_name": "shopping_cart",
             "plural": "shopping_carts", "action": "create", "attributes": []},
            {"name": "LineItem", "snake_name": "line_item",
             "plural": "line_items", "action": "create",
             "attributes": [
                 # Default for line_item: has cart_id hardcoded
                 {"name": "cart_id", "type_hint": "int", "required": True},
                 {"name": "quantity", "type_hint": "int", "required": True},
             ]},
        ],
        "relationships": [
            {"from": "shopping_cart", "to": "line_item", "kind": "has_many"},
        ],
    }
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec))
    out_dir = tmp_path / "alembic"
    out_dir.mkdir()
    proc = _run("migration_generator.py", "--spec", str(spec_path),
                "--out", str(out_dir))
    text = list(out_dir.glob("*.py"))[0].read_text()
    # Only ONE shopping_cart_id column; not BOTH cart_id and shopping_cart_id
    assert "shopping_cart_id" in text
    assert text.count("'cart_id'") == 0, \
        "default cart_id should be deduplicated against shopping_cart_id FK"


# ─── body_hints expanded ────────────────────────────────────────────────────

def test_body_hints_has_service_layer():
    proc = _run("body_hints.py", "--framework", "fastapi",
                "--kind", "service_layer")
    data = json.loads(proc.stdout)
    assert data["language"] == "python"
    assert "must_emit_methods" in data
    assert data["must_enforce_invariants_from_spec"] is True
    assert "anti_patterns" in data


def test_body_hints_has_auth_endpoints():
    proc = _run("body_hints.py", "--framework", "fastapi",
                "--kind", "auth_endpoints")
    data = json.loads(proc.stdout)
    assert data["must_use_bcrypt_not_plain_hash"] is True
    # bcrypt mentioned in the helpers (pwd_context uses schemes=['bcrypt'])
    helpers_blob = " ".join(data["must_emit_helpers"])
    assert "bcrypt" in helpers_blob


def test_body_hints_has_events_emitter():
    proc = _run("body_hints.py", "--framework", "common",
                "--kind", "events_emitter")
    data = json.loads(proc.stdout)
    assert data["file"] == "common/events.py"


def test_body_hints_has_domain_exceptions():
    proc = _run("body_hints.py", "--framework", "common",
                "--kind", "domain_exceptions")
    data = json.loads(proc.stdout)
    assert data["file"] == "common/exceptions.py"
    classes = " ".join(data["must_emit_classes"])
    assert "DomainError" in classes
    assert "NotFoundError" in classes
    assert "ConflictError" in classes


def test_body_hints_total_count_at_least_34():
    """Catalogue grows over time. Tier 8 added 5; Tier 10 added 4 more.
    Assert monotone-grow rather than exact count."""
    proc = _run("body_hints.py", "--list", "--json")
    data = json.loads(proc.stdout)
    assert len(data) >= 34, f"expected ≥34 hint entries, got {len(data)}"


# ─── scaffold_planner now produces service.py files ─────────────────────────

def test_scaffold_planner_now_emits_service_file_for_fastapi(tmp_path):
    spec = {
        "feature": "test", "framework": "fastapi", "language": "python",
        "test_contract": {"auth": "none", "pagination": "list"},
        "entities": [{"name": "Cart", "snake_name": "cart", "plural": "carts",
                      "action": "create", "attributes": []}],
        "api_surface": [], "wiring": {}, "relationships": [],
        "graph_imports": {},
    }
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec))
    proc = _run("scaffold_planner.py", "--spec", str(spec_path))
    plan = json.loads(proc.stdout)
    paths = [f["path"] for f in plan["files_to_create"]]
    assert "cart/service.py" in paths
    # Find its kind
    service_file = next(f for f in plan["files_to_create"]
                        if f["path"] == "cart/service.py")
    assert service_file["kind"] == "service_layer"


# ─── new slash commands ─────────────────────────────────────────────────────

def test_rollback_slash_command_exists():
    path = REPO_ROOT / "commands" / "rollback.md"
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "argument-hint:" in text
    assert "rollback" in text.lower()


def test_docs_drift_slash_command_exists():
    path = REPO_ROOT / "commands" / "docs-drift.md"
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "docs-author" in text.lower()


def test_autonomy_slash_command_exists():
    path = REPO_ROOT / "commands" / "autonomy.md"
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "operator" in text.lower()
    assert "observer" in text.lower()


# ─── Stage 6.5 migration wiring ─────────────────────────────────────────────

def test_skill_md_includes_stage_6_5_migration():
    skill = REPO_ROOT / "skills" / "one-shot-generate" / "SKILL.md"
    text = skill.read_text(encoding="utf-8")
    assert "Stage 6.5" in text
    assert "migration_generator.py" in text


# ─── Tier 7A scripts still work ─────────────────────────────────────────────

def test_autonomy_level_get_works(tmp_path):
    proc = _run("autonomy_level.py", "--repo-root", str(tmp_path),
                "get-level")
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data["current_level"] == "operator"  # default for fresh repo


def test_predictive_failure_returns_structure(tmp_path):
    (tmp_path / ".beads").mkdir()
    (tmp_path / ".beads" / "failures.jsonl").write_text("")
    proc = _run("predictive_failure.py",
                "--repo-root", str(tmp_path),
                "shopping cart with line items", "--json")
    data = json.loads(proc.stdout)
    assert "method" in data
    assert "total_beads" in data


def test_perf_profiler_recalibrate_handles_empty_log(tmp_path):
    proc = _run("perf_profiler.py", "--repo-root", str(tmp_path),
                "recalibrate")
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data == {}


def test_prompt_versioner_current_for_existing_skill():
    proc = _run("prompt_versioner.py", "--repo-root", str(REPO_ROOT),
                "current", "--kind", "skill", "--name", "one-shot-generate")
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data["target"] == "skill:one-shot-generate"
    assert data["current_version"] == "1.0.0"
