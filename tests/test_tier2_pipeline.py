"""Invocation-based smoke tests for the Tier-2 + Tier-3 modules.

Same protocol as test_tier1_pipeline: every test runs a script via
subprocess and asserts on its structured output, so the suite catches the
class of bug that only manifests when you actually invoke the runner
(imports, Windows encoding, CLI drift).
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
        timeout=120,
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
        "from sqlalchemy.orm import declarative_base\nfrom sqlalchemy import Column, Integer, String\n\n"
        "Base = declarative_base()\n\nclass Product(Base):\n"
        "    __tablename__ = 'products'\n    id = Column(Integer, primary_key=True)\n"
    )
    return project


# ─── critic_runner ───────────────────────────────────────────────────────────

def test_critic_runner_reports_pass_on_passing_tests(tmp_path):
    test_dir = tmp_path / "passing"
    test_dir.mkdir()
    (test_dir / "test_ok.py").write_text(
        "def test_obvious():\n    assert 1 + 1 == 2\n"
    )
    proc = _run("critic_runner.py", "--tests", str(test_dir), "--json")
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data["passed"] == 1
    assert data["failed"] == 0
    assert data["exit_code"] == 0


def test_critic_runner_routes_401_failure_to_test_author(tmp_path):
    test_dir = tmp_path / "failing"
    test_dir.mkdir()
    (test_dir / "test_auth.py").write_text(
        "def test_unauthorized():\n    response_status = 200\n"
        "    assert response_status == 401\n"
    )
    proc = _run("critic_runner.py", "--tests", str(test_dir), "--json", "--route")
    data = json.loads(proc.stdout)
    assert data["failed"] >= 1
    assert data.get("routes")
    # The route should call out test-author since the assertion involves 401
    assert any(r["route_to"] == "test-author" for r in data["routes"])


# ─── auto_patch ──────────────────────────────────────────────────────────────

def test_auto_patch_skips_401_test(tmp_path):
    sandbox = tmp_path / "sb"
    sandbox.mkdir()
    test_file = sandbox / "test_cart_api.py"
    test_file.write_text(
        "def test_unauthorized():\n    response_status = 200\n"
        "    assert response_status == 401\n"
    )
    diag = {"file": "test_cart_api.py", "line": None,
            "severity": "warning", "code": "semantic",
            "message": "test asserts HTTP 401 but matching router has no auth dependency"}
    diag_path = tmp_path / "diag.json"
    diag_path.write_text(json.dumps([diag]))
    proc = _run("auto_patch.py", "--sandbox", str(sandbox),
                "--diagnostics", str(diag_path))
    # Auto-patch exits 0 (no unresolved diagnostics)
    assert proc.returncode == 0, proc.stderr
    patched = test_file.read_text()
    assert "pytest.skip" in patched, patched


def test_auto_patch_rewrites_pagination_assertion(tmp_path):
    sandbox = tmp_path / "sb"
    sandbox.mkdir()
    test_file = sandbox / "test_p.py"
    test_file.write_text(
        'def test_pagination():\n    response = type("R", (), {"json": lambda self: []})()\n'
        '    assert "next" in response.json()\n'
    )
    diag = {"file": "test_p.py", "line": None,
            "severity": "warning", "code": "semantic",
            "message": 'test asserts "next" in response.json() but router returns a plain list'}
    diag_path = tmp_path / "d.json"
    diag_path.write_text(json.dumps([diag]))
    proc = _run("auto_patch.py", "--sandbox", str(sandbox),
                "--diagnostics", str(diag_path))
    patched = test_file.read_text()
    assert '"next"' not in patched
    assert "isinstance(response.json(), list)" in patched


# ─── beads_curriculum ────────────────────────────────────────────────────────

def test_curriculum_returns_no_hits_on_empty_log(tmp_path):
    (tmp_path / ".beads").mkdir()
    (tmp_path / ".beads" / "failures.jsonl").write_text("")
    proc = _run("beads_curriculum.py", "shopping cart",
                "--repo-root", str(tmp_path), "--json")
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data["total_beads"] == 0
    assert data["hits"] == []


def test_curriculum_matches_similar_task(tmp_path):
    (tmp_path / ".beads").mkdir()
    failures = tmp_path / ".beads" / "failures.jsonl"
    bead = {
        "id": "bd-fail-20260518-001",
        "ts": "2026-05-18T00:00:00Z",
        "phase": "phase2",
        "task": "shopping cart with line items",
        "project": None,
        "kind": "verification_warning",
        "diagnostics": [{"file": "test_cart_api.py", "code": "semantic",
                          "severity": "warning",
                          "message": "test asserts HTTP 401 but matching router has no auth dependency"}],
        "resolved": False,
    }
    failures.write_text(json.dumps(bead) + "\n")
    proc = _run("beads_curriculum.py", "shopping cart with discounts",
                "--repo-root", str(tmp_path), "--json")
    data = json.loads(proc.stdout)
    assert data["hits"], data
    # The advice should reference the auth/contract drift class of bug
    assert "auth" in data["hits"][0]["advice"].lower()


# ─── compile_spec ────────────────────────────────────────────────────────────

def test_compile_spec_produces_api_surface(tmp_path):
    orch_report = {
        "task": "add product CRUD",
        "intent": "api",
        "confidence": 0.62,
        "codebase_summary": {
            "language": "python", "framework": "fastapi",
            "imports": {}, "conventions": {"naming": "snake_case"},
        },
        "reconciled_entities": [
            {"entity_name": "product", "pascal": "Product", "plural": "products",
             "status": "new", "attributes": []}
        ],
        "wire": {"actions": [{"after": "app.include_router(product_router)"}],
                  "framework": "fastapi"},
    }
    in_path = tmp_path / "orch.json"
    in_path.write_text(json.dumps(orch_report))
    proc = _run("compile_spec.py", "--orchestrator-json", str(in_path))
    assert proc.returncode == 0, proc.stderr
    spec = json.loads(proc.stdout)
    assert spec["intent"] == "api"
    methods = [e["method"] for e in spec["api_surface"]]
    assert {"GET", "POST", "PUT", "DELETE"} <= set(methods)


# ─── cross_feature_consistency ───────────────────────────────────────────────

def test_consistency_flags_missing_import(tmp_path):
    project = _fastapi_fixture(tmp_path)
    generated = tmp_path / "gen"
    (generated / "cart").mkdir(parents=True)
    (generated / "cart" / "router.py").write_text(
        "from app.deps_nonexistent import session\n"
        "def list_carts():\n    return []\n"
    )
    proc = _run("cross_feature_consistency.py",
                "--project", str(project),
                "--generated-dir", str(generated),
                "--json")
    # exit 2 = drift detected
    assert proc.returncode in (0, 2)
    data = json.loads(proc.stdout)
    assert any(i["rule"] == "C5" for i in data["issues"])


# ─── self_improvement_proposer ───────────────────────────────────────────────

def test_self_improvement_threshold(tmp_path):
    (tmp_path / ".beads").mkdir()
    failures = tmp_path / ".beads" / "failures.jsonl"
    # Three beads with the 401 pattern → should propose
    template = {
        "id": "bd-fail-x", "ts": "2026-05-18T00:00:00Z", "phase": "phase2",
        "task": "x", "project": None, "kind": "verification_warning",
        "diagnostics": [{"file": "t.py", "code": "semantic", "severity": "warning",
                          "message": "test asserts HTTP 401 but matching router has no auth"}],
        "resolved": False,
    }
    failures.write_text("\n".join(json.dumps(template) for _ in range(3)) + "\n")
    proc = _run("self_improvement_proposer.py",
                "--repo-root", str(tmp_path),
                "--threshold", "3", "--json")
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data["entries"], data
    labels = [e["pattern"] for e in data["entries"]]
    assert "test_router_auth_drift" in labels


# ─── orchestrator clarification gate ─────────────────────────────────────────

def test_orchestrator_halts_on_low_confidence(tmp_path):
    project = _fastapi_fixture(tmp_path)
    proc = _run("one_shot_orchestrator.py", "wat",
                "--project", str(project), "--json")
    # exit 2 = report says overall_succeeded=False (halted)
    data = json.loads(proc.stdout)
    assert data["clarifying_question"], data
    assert data["overall_succeeded"] is False


def test_orchestrator_force_bypasses_clarification(tmp_path):
    project = _fastapi_fixture(tmp_path)
    proc = _run("one_shot_orchestrator.py", "wat",
                "--project", str(project), "--force", "--json")
    data = json.loads(proc.stdout)
    assert data["clarifying_question"] is None
    # The generator may still run; we just assert the gate didn't fire.
