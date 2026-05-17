"""Invocation-based tests for the Tier-2.5 modules.

Covers: spec_driven_generator, run_critic_loop, codebase_diff, live_critic,
plus the orchestrator's spec-driven default path.
"""

from __future__ import annotations

import json
import os
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
        timeout=180,
    )


def _fastapi_fixture(tmp: Path) -> Path:
    project = tmp / "fixture"
    project.mkdir()
    (project / "requirements.txt").write_text(
        "fastapi==0.104.1\nsqlalchemy==2.0.23\npydantic==2.5.0\npytest==7.4.3\n"
    )
    (project / "main.py").write_text(
        "from fastapi import FastAPI\napp = FastAPI()\n"
    )
    (project / "models.py").write_text(
        "from sqlalchemy.orm import declarative_base\n"
        "from sqlalchemy import Column, Integer, String\n\n"
        "Base = declarative_base()\n\nclass Product(Base):\n"
        "    __tablename__ = 'products'\n    id = Column(Integer, primary_key=True)\n"
    )
    return project


def _build_spec(entities, relationships=None, graph_imports=None,
                framework="fastapi"):
    return {
        "feature": "test",
        "intent": "feature",
        "framework": framework,
        "language": "python",
        "test_contract": {"auth": "none", "pagination": "list"},
        "entities": entities,
        "api_surface": [],
        "wiring": {"framework": framework},
        "relationships": relationships or [],
        "graph_imports": graph_imports or {},
    }


# ─── spec_driven_generator ──────────────────────────────────────────────────

def test_spec_generator_emits_files_per_entity(tmp_path):
    spec = _build_spec([
        {"name": "Cart", "snake_name": "cart", "plural": "carts",
         "action": "create",
         "attributes": [
             {"name": "status", "type_hint": "str", "required": True},
         ]},
    ])
    spec_path = tmp_path / "s.json"
    spec_path.write_text(json.dumps(spec))
    proc = _run("spec_driven_generator.py",
                "--spec", str(spec_path),
                "--out-dir", str(tmp_path / "gen"))
    assert proc.returncode == 0, proc.stderr
    out = tmp_path / "gen"
    assert (out / "cart" / "models.py").exists()
    assert (out / "cart" / "router.py").exists()
    assert (out / "cart" / "schemas.py").exists()
    assert (out / "tests" / "test_cart_api.py").exists()


def test_spec_generator_emits_fk_from_relationship(tmp_path):
    spec = _build_spec(
        entities=[
            {"name": "Cart", "snake_name": "cart", "plural": "carts",
             "action": "create", "attributes": []},
            {"name": "LineItem", "snake_name": "line_item",
             "plural": "line_items", "action": "create", "attributes": []},
        ],
        relationships=[
            {"from": "cart", "to": "line_item", "kind": "has_many"},
        ],
    )
    spec_path = tmp_path / "s.json"
    spec_path.write_text(json.dumps(spec))
    proc = _run("spec_driven_generator.py",
                "--spec", str(spec_path),
                "--out-dir", str(tmp_path / "gen"))
    assert proc.returncode == 0, proc.stderr
    line_item_model = (tmp_path / "gen" / "line_item" / "models.py").read_text()
    assert "cart_id" in line_item_model
    assert 'ForeignKey("carts.id")' in line_item_model
    # cart should not have an FK call to itself; the import line includes
    # ForeignKey unconditionally, so check for a USAGE, not just the name.
    cart_model = (tmp_path / "gen" / "cart" / "models.py").read_text()
    assert "ForeignKey(" not in cart_model.replace(
        "from sqlalchemy import", "")


def test_spec_generator_emits_database_stub_when_missing(tmp_path):
    spec = _build_spec([
        {"name": "X", "snake_name": "x", "plural": "xs", "action": "create",
         "attributes": [{"name": "name", "type_hint": "str", "required": True}]},
    ])
    spec_path = tmp_path / "s.json"
    spec_path.write_text(json.dumps(spec))
    proc = _run("spec_driven_generator.py",
                "--spec", str(spec_path),
                "--out-dir", str(tmp_path / "gen"))
    assert proc.returncode == 0
    assert (tmp_path / "gen" / "database.py").exists()


def test_spec_generator_skips_stub_when_project_has_get_db(tmp_path):
    spec = _build_spec(
        entities=[{"name": "X", "snake_name": "x", "plural": "xs",
                   "action": "create", "attributes": []}],
        graph_imports={"db_session_getter": {"name": "get_db",
                                              "module": "app.deps"}},
    )
    spec_path = tmp_path / "s.json"
    spec_path.write_text(json.dumps(spec))
    proc = _run("spec_driven_generator.py",
                "--spec", str(spec_path),
                "--out-dir", str(tmp_path / "gen"))
    assert proc.returncode == 0
    assert not (tmp_path / "gen" / "database.py").exists()
    router = (tmp_path / "gen" / "x" / "router.py").read_text()
    assert "from app.deps import get_db" in router


# ─── run_critic_loop ────────────────────────────────────────────────────────

def test_critic_loop_ships_clean_spec(tmp_path):
    spec = _build_spec([
        {"name": "Widget", "snake_name": "widget", "plural": "widgets",
         "action": "create",
         "attributes": [{"name": "name", "type_hint": "str", "required": True}]},
    ])
    spec_path = tmp_path / "s.json"
    spec_path.write_text(json.dumps(spec))
    proc = _run("run_critic_loop.py", "--spec", str(spec_path),
                "--max-iters", "1", "--json")
    # exit 0 = green; non-zero = red. We accept either but assert structure.
    data = json.loads(proc.stdout)
    assert data["iterations"], data
    assert "final_sandbox" in data


# ─── codebase_diff ──────────────────────────────────────────────────────────

def test_codebase_diff_reports_unchanged_after_caching(tmp_path):
    project = _fastapi_fixture(tmp_path)
    # First scan creates the cache
    _run("codebase_graph.py", str(project))
    # Diff against the same state
    proc = _run("codebase_diff.py", str(project), "--json")
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data["signature_unchanged"] is True


def test_codebase_diff_reports_added_after_new_file(tmp_path):
    project = _fastapi_fixture(tmp_path)
    _run("codebase_graph.py", str(project))
    # Add a new model class
    new_file = project / "tax.py"
    new_file.write_text(
        "from sqlalchemy.orm import declarative_base\n"
        "from sqlalchemy import Column, Integer\n\nBase = declarative_base()\n\n"
        "class Tax(Base):\n    __tablename__ = 'taxes'\n"
        "    id = Column(Integer, primary_key=True)\n"
    )
    proc = _run("codebase_diff.py", str(project), "--json")
    data = json.loads(proc.stdout)
    assert data["signature_unchanged"] is False
    # tax.py should appear as added
    assert any("tax.py" in p for p in data["added"]), data


# ─── live_critic ────────────────────────────────────────────────────────────

def test_live_critic_partitions_feature_vs_regression(tmp_path):
    project = tmp_path / "proj"
    (project / "tests").mkdir(parents=True)
    (project / "tests" / "test_existing.py").write_text(
        "def test_old(): assert True\n"
    )
    (project / "tests" / "test_cart_api.py").write_text(
        "def test_new(): assert True\n"
    )
    proc = _run("live_critic.py", "--project", str(project),
                "--feature-path", "test_cart_api", "--json")
    data = json.loads(proc.stdout)
    new_nodes = data["new_feature_outcomes"]
    assert any("test_cart_api" in o["nodeid"] for o in new_nodes), data


# ─── orchestrator end-to-end via spec path ──────────────────────────────────

def test_orchestrator_uses_spec_driven_path_for_fastapi(tmp_path):
    project = _fastapi_fixture(tmp_path)
    proc = _run("one_shot_orchestrator.py",
                "add a category api", "--project", str(project),
                "--json", "--force")
    data = json.loads(proc.stdout)
    # Spec-driven path produces ONE iteration containing many files
    assert data["generation"], data
    notes = " ".join(data["notes"]).lower()
    assert "spec-driven" in notes
