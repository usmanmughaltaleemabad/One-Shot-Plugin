"""Tier 10 tests: OpenAPI generator + production hints + deployment guide."""

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


# ─── openapi_doc_generator ──────────────────────────────────────────────────

def test_openapi_generator_emits_valid_openapi_31(tmp_path):
    spec = {
        "feature": "shopping cart",
        "framework": "fastapi",
        "test_contract": {"auth": "none", "pagination": "list"},
        "entities": [
            {"name": "Cart", "snake_name": "cart", "plural": "carts",
             "action": "create",
             "attributes": [
                 {"name": "user_id", "type_hint": "int", "required": True},
                 {"name": "status", "type_hint": "str", "required": True},
                 {"name": "total", "type_hint": "Decimal", "required": True},
             ]},
        ],
        "relationships": [],
    }
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec))
    proc = _run("openapi_doc_generator.py", "--spec", str(spec_path))
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data["openapi"] == "3.1.0"
    assert "Cart" in [t["name"] for t in data["tags"]]
    # CRUD paths present
    assert "/api/v1/carts" in data["paths"]
    assert "/api/v1/carts/{item_id}" in data["paths"]
    # Schemas
    assert "CartRead" in data["components"]["schemas"]
    assert "CartCreate" in data["components"]["schemas"]
    assert "CartUpdate" in data["components"]["schemas"]
    # Create schema has an example
    assert "example" in data["components"]["schemas"]["CartCreate"]


def test_openapi_generator_emits_security_when_auth_required(tmp_path):
    spec = {
        "feature": "auth", "framework": "fastapi",
        "test_contract": {"auth": "jwt"},
        "entities": [{"name": "User", "snake_name": "user", "plural": "users",
                      "action": "create", "attributes": []}],
        "relationships": [],
    }
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec))
    proc = _run("openapi_doc_generator.py", "--spec", str(spec_path))
    data = json.loads(proc.stdout)
    assert "securitySchemes" in data["components"]
    assert "bearerAuth" in data["components"]["securitySchemes"]
    # Every endpoint has security
    for path, ops in data["paths"].items():
        for method in ops:
            if method.lower() in ("get", "post", "put", "delete"):
                assert "security" in ops[method]


def test_openapi_generator_includes_fk_columns_from_relationships(tmp_path):
    spec = {
        "feature": "test", "framework": "fastapi",
        "test_contract": {},
        "entities": [
            {"name": "Cart", "snake_name": "cart", "plural": "carts",
             "action": "create", "attributes": []},
            {"name": "LineItem", "snake_name": "line_item",
             "plural": "line_items", "action": "create", "attributes": []},
        ],
        "relationships": [
            {"from": "cart", "to": "line_item", "kind": "has_many"},
        ],
    }
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec))
    proc = _run("openapi_doc_generator.py", "--spec", str(spec_path))
    data = json.loads(proc.stdout)
    line_item_create = data["components"]["schemas"]["LineItemCreate"]
    assert "cart_id" in line_item_create["properties"]
    assert "cart_id" in line_item_create["required"]


# ─── New body hints (Tier 10) ───────────────────────────────────────────────

def test_body_hints_has_rate_limiter():
    proc = _run("body_hints.py", "--framework", "common",
                "--kind", "rate_limiter")
    data = json.loads(proc.stdout)
    assert data["file"] == "common/rate_limit.py"
    assert "anti_patterns" in data


def test_body_hints_has_cache_layer():
    proc = _run("body_hints.py", "--framework", "common",
                "--kind", "cache_layer")
    data = json.loads(proc.stdout)
    assert data["file"] == "common/cache.py"
    assert any("ttl" in s.lower() for s in data["must_emit"])


def test_body_hints_has_logging_setup():
    proc = _run("body_hints.py", "--framework", "common",
                "--kind", "logging_setup")
    data = json.loads(proc.stdout)
    assert data["file"] == "common/logging_setup.py"
    assert "JsonFormatter" in " ".join(data["must_emit"])


# ─── Production deployment doc ──────────────────────────────────────────────

def test_production_deployment_doc_exists():
    path = REPO_ROOT / "docs" / "production-deployment.md"
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    # Five stages
    for stage in ("Stage 1", "Stage 2", "Stage 3", "Stage 4", "Stage 5"):
        assert stage in text
    # Critical pieces
    assert "alembic" in text.lower()
    assert "secrets" in text.lower()
    assert "rollback" in text.lower()
    assert "checklist" in text.lower()


# ─── plugin.json v4.0.0 ─────────────────────────────────────────────────────

def test_plugin_json_at_v4():
    path = REPO_ROOT / ".claude-plugin" / "plugin.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["version"] == "4.0.0"
    # Description mentions the new capabilities
    desc = data["description"].lower()
    assert "agentic" in desc
    assert "9-stage" in desc or "service-author" in desc
    # New keywords
    kws = data["keywords"]
    assert "service-author-agent" in kws
    assert "migration-generator" in kws
    assert "learnings-hub" in kws
    assert "autonomy-levels" in kws


# ─── Scorecard v4 doc ───────────────────────────────────────────────────────

def test_scorecard_v4_doc_exists():
    path = REPO_ROOT / "docs" / "scorecard-v4.md"
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "8.2" in text   # weighted overall after Tier 10
    assert "v4.0.0" in text or "v4.0" in text
