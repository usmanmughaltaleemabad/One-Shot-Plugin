"""Invocation-based smoke tests for the Tier-1 pipeline.

Every test in this module actually RUNS a script via subprocess and asserts
on the structured output. This is intentionally heavier than a pure unit
test — the value is in catching the kind of bug the previous validation
pass found (import failures, encoding crashes, runner-CLI drift) that
only manifest when you actually invoke the script.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "skills" / "one-shot-generator" / "scripts"


def _run(script: str, *args: str) -> subprocess.CompletedProcess:
    """Invoke a plugin script via subprocess and return the process."""
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args],
        capture_output=True, text=True, env=env, encoding="utf-8",
        timeout=60,
    )


# ─── extract_domain_model ────────────────────────────────────────────────────

def test_extract_domain_model_multi_entity():
    proc = _run("extract_domain_model.py", "--json",
                "Build a shopping cart with line items, discounts, and inventory holds")
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    names = [e["name"] for e in data["entities"]]
    assert "shopping_cart" in names
    assert "line_item" in names
    assert "discount" in names
    assert "inventory_hold" in names
    assert data["confidence"] >= 0.6


def test_extract_domain_model_intent_routing():
    proc = _run("extract_domain_model.py", "--json", "add user CRUD API")
    data = json.loads(proc.stdout)
    assert data["intent"] == "api"
    assert data["primary_entity"] == "user"


def test_extract_domain_model_batch_intent():
    proc = _run("extract_domain_model.py", "--json",
                "process pending invoices in a nightly batch job")
    data = json.loads(proc.stdout)
    assert data["intent"] == "batch"


# ─── existing_codebase_scanner ───────────────────────────────────────────────

def _fastapi_fixture(tmp: Path) -> Path:
    project = tmp / "fixture-fastapi"
    project.mkdir()
    (project / "requirements.txt").write_text("fastapi==0.104.1\nsqlalchemy==2.0.23\npydantic==2.5.0\n")
    (project / "main.py").write_text(
        "from fastapi import FastAPI\nfrom pydantic import BaseModel\n"
        "app = FastAPI()\n\nclass HealthResponse(BaseModel):\n    status: str\n"
    )
    (project / "models.py").write_text(
        "from sqlalchemy import Column, Integer, String\n"
        "from sqlalchemy.orm import declarative_base\n\n"
        "Base = declarative_base()\n\n"
        "class Product(Base):\n    __tablename__ = 'products'\n"
        "    id = Column(Integer, primary_key=True)\n"
        "    name = Column(String(100))\n"
    )
    return project


def test_codebase_scanner_finds_existing_models(tmp_path):
    project = _fastapi_fixture(tmp_path)
    proc = _run("existing_codebase_scanner.py", str(project))
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data["language"] == "python"
    assert data["framework"] == "fastapi"
    names = [e["name"] for e in data["entities"]]
    assert "Product" in names
    assert "HealthResponse" in names


# ─── codebase_graph (caching) ────────────────────────────────────────────────

def test_codebase_graph_caches_on_disk(tmp_path):
    project = _fastapi_fixture(tmp_path)
    # First run: should create the .osp_codebase_graph.json
    proc1 = _run("codebase_graph.py", str(project))
    assert proc1.returncode == 0, proc1.stderr
    cache_file = project / ".osp_codebase_graph.json"
    assert cache_file.exists()
    payload = json.loads(cache_file.read_text(encoding="utf-8"))
    assert "_signature" in payload
    # Second run: should hit the cache (same signature)
    proc2 = _run("codebase_graph.py", str(project))
    data = json.loads(proc2.stdout)
    assert data["framework"] == "fastapi"


# ─── auto_wirer (dry-run) ────────────────────────────────────────────────────

def test_auto_wirer_dry_run_for_fastapi(tmp_path):
    project = _fastapi_fixture(tmp_path)
    generated = tmp_path / "generated"
    (generated / "cart").mkdir(parents=True)
    (generated / "cart" / "router.py").write_text(
        "from fastapi import APIRouter\nrouter = APIRouter()\n"
    )
    proc = _run("auto_wirer.py", "--project", str(project),
                "--generated-dir", str(generated),
                "--framework", "fastapi", "--dry-run")
    assert proc.returncode == 0, proc.stderr
    # The script appends a JSON block after --- separator
    json_start = proc.stdout.find("{")
    data = json.loads(proc.stdout[json_start:])
    assert data["dry_run"] is True
    assert any("cart_router" in a["after"] for a in data["actions"])
    # main.py untouched in dry-run
    assert "include_router" not in (project / "main.py").read_text()


# ─── generate_and_verify (catches the test/router contract bug) ──────────────

def test_verify_flags_contract_mismatch(tmp_path):
    sandbox = tmp_path / "bad-output"
    (sandbox / "product").mkdir(parents=True)
    (sandbox / "product" / "router.py").write_text(
        "from fastapi import APIRouter\n"
        "router = APIRouter(prefix='/products')\n\n"
        "@router.get('/')\n"
        "async def list_products():\n    return []\n"
    )
    (sandbox / "test_product_api.py").write_text(
        "def test_unauthorized(client):\n"
        "    response = client.post('/products/')\n"
        "    assert response.status_code == 401\n"
    )
    proc = _run("generate_and_verify.py", "--verify-dir", str(sandbox))
    marker = proc.stdout.find("---JSON---")
    assert marker != -1, proc.stdout
    json_start = proc.stdout.find("[", marker)
    reports = json.loads(proc.stdout[json_start:])
    diags = reports[0]["diagnostics"]
    messages = [d["message"] for d in diags]
    assert any("HTTP 401" in m for m in messages), \
        f"expected 401 alignment warning, got: {messages}"


# ─── orchestrator end-to-end ─────────────────────────────────────────────────

def test_orchestrator_runs_end_to_end(tmp_path):
    project = _fastapi_fixture(tmp_path)
    proc = _run("one_shot_orchestrator.py",
                "Add a category API",
                "--project", str(project),
                "--json")
    # Allow non-zero exit because warnings count as failures only via --strict
    assert proc.stdout, proc.stderr
    json_start = proc.stdout.find("{")
    report = json.loads(proc.stdout[json_start:])
    assert report["task"]
    entities = [e["entity_name"] for e in report["reconciled_entities"]]
    assert "category" in entities
    # The fixture has Product so Category should be the only NEW entity
    new = [r for r in report["reconciled_entities"] if r["status"] == "new"]
    assert any(r["entity_name"] == "category" for r in new)


def test_orchestrator_reuses_existing_product(tmp_path):
    project = _fastapi_fixture(tmp_path)
    proc = _run("one_shot_orchestrator.py",
                "Add a product API with categories",
                "--project", str(project),
                "--json")
    json_start = proc.stdout.find("{")
    report = json.loads(proc.stdout[json_start:])
    statuses = {r["entity_name"]: r["status"] for r in report["reconciled_entities"]}
    assert statuses.get("product") == "exists", \
        f"Product should be reconciled as 'exists', got {statuses}"
    assert statuses.get("category") == "new"
