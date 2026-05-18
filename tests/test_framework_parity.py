"""Tests for v4.2 framework parity work — every framework now has the same
8-hint shape (init/model/schema/service/router/auth/background/test) plus
its own scaffold_planner dispatcher.

Covers:
  * body_hints catalogue parity (Django/Spring/NestJS/Go/Node.js gained the
    missing service_layer + auth + background equivalents)
  * scaffold_planner now emits service / auth / background files for every
    supported framework
  * Node.js (Express) is a first-class framework with full hint coverage
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

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


# ─── body_hints — every framework has ≥ 8 hints ─────────────────────────────

def _hints_for(framework: str) -> list[dict]:
    proc = _run("body_hints.py", "--list", "--json")
    assert proc.returncode == 0, proc.stderr
    return [h for h in json.loads(proc.stdout) if h["framework"] == framework]


def test_every_framework_has_at_least_eight_hints():
    """The parity floor — each framework should match FastAPI's 8-hint baseline."""
    for fw in ("fastapi", "django", "spring", "go", "nestjs", "nodejs"):
        hints = _hints_for(fw)
        assert len(hints) >= 8, (
            f"{fw} has only {len(hints)} hints, expected ≥ 8 "
            f"(parity floor matching FastAPI). Hints: {[h['kind'] for h in hints]}"
        )


# ─── Django parity: service, auth, background ──────────────────────────────

def test_django_has_service_hint():
    proc = _run("body_hints.py", "--framework", "django", "--kind", "django_service")
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data["must_enforce_invariants_from_spec"] is True
    assert data["must_use_transactions"] is True
    # service must NOT do HTTP error handling
    anti = " ".join(data.get("anti_patterns", []))
    assert "401" in anti or "permission" in anti.lower()


def test_django_has_auth_hint():
    proc = _run("body_hints.py", "--framework", "django", "--kind", "django_auth")
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data["must_use_bcrypt_not_plain_hash"] is True
    helpers_blob = " ".join(data["must_emit_helpers"])
    assert "hash_password" in helpers_blob
    assert "verify_password" in helpers_blob


def test_django_has_background_hint():
    proc = _run("body_hints.py", "--framework", "django", "--kind", "django_background_task")
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    imports_blob = " ".join(data["imports_must_include"])
    assert "celery" in imports_blob.lower()


# ─── Spring parity: auth, background ────────────────────────────────────────

def test_spring_has_auth_hint():
    proc = _run("body_hints.py", "--framework", "spring", "--kind", "spring_auth")
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data["must_use_bcrypt_not_plain_hash"] is True
    methods_blob = " ".join(data["must_emit_methods"])
    assert "BCrypt" in " ".join(data["imports_must_include"])
    assert "hashPassword" in methods_blob


def test_spring_has_background_hint():
    proc = _run("body_hints.py", "--framework", "spring", "--kind", "spring_background")
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    imports_blob = " ".join(data["imports_must_include"])
    assert "@Async" in imports_blob or "Async" in imports_blob
    assert "@Scheduled" in imports_blob or "Scheduled" in imports_blob


# ─── NestJS parity: auth, background ────────────────────────────────────────

def test_nestjs_has_auth_hint():
    proc = _run("body_hints.py", "--framework", "nestjs", "--kind", "nestjs_auth")
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data["must_use_bcrypt_not_plain_hash"] is True
    imports_blob = " ".join(data["imports_must_include"])
    assert "bcrypt" in imports_blob.lower()
    assert "jwt" in imports_blob.lower()


def test_nestjs_has_background_hint():
    proc = _run("body_hints.py", "--framework", "nestjs", "--kind", "nestjs_background")
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    imports_blob = " ".join(data["imports_must_include"])
    assert "bull" in imports_blob.lower() or "queue" in imports_blob.lower()


# ─── Go parity: service, dto, auth, background ──────────────────────────────

def test_go_has_service_hint():
    proc = _run("body_hints.py", "--framework", "go", "--kind", "go_service")
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data["must_enforce_invariants_from_spec"] is True
    assert "context" in " ".join(data["imports_must_include"])


def test_go_has_dto_hint():
    proc = _run("body_hints.py", "--framework", "go", "--kind", "go_dto")
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    struct_blob = data["must_emit_struct"]
    assert "Create" in struct_blob and "Update" in struct_blob and "Response" in struct_blob


def test_go_has_auth_hint():
    proc = _run("body_hints.py", "--framework", "go", "--kind", "go_auth")
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data["must_use_bcrypt_not_plain_hash"] is True
    imports_blob = " ".join(data["imports_must_include"])
    assert "bcrypt" in imports_blob
    assert "jwt" in imports_blob.lower()


def test_go_has_background_hint():
    proc = _run("body_hints.py", "--framework", "go", "--kind", "go_background")
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    anti = " ".join(data["anti_patterns"]).lower()
    assert "recover" in anti, "Go background hint must warn about missing recover()"


# ─── Node.js: full 8-hint set ───────────────────────────────────────────────

NODEJS_KINDS = [
    "nodejs_init", "nodejs_model", "nodejs_schema", "nodejs_service",
    "nodejs_router", "nodejs_auth", "nodejs_background", "nodejs_test",
]


def test_nodejs_all_eight_hints_present():
    proc = _run("body_hints.py", "--list", "--json")
    assert proc.returncode == 0, proc.stderr
    kinds = {h["kind"] for h in json.loads(proc.stdout) if h["framework"] == "nodejs"}
    missing = set(NODEJS_KINDS) - kinds
    assert not missing, f"Node.js missing hints: {missing}"


def test_nodejs_auth_uses_bcrypt_and_jwt():
    proc = _run("body_hints.py", "--framework", "nodejs", "--kind", "nodejs_auth")
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data["must_use_bcrypt_not_plain_hash"] is True
    imports_blob = " ".join(data["imports_must_include"])
    assert "bcrypt" in imports_blob
    assert "jsonwebtoken" in imports_blob


def test_nodejs_service_must_enforce_invariants():
    proc = _run("body_hints.py", "--framework", "nodejs", "--kind", "nodejs_service")
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert data["must_enforce_invariants_from_spec"] is True
    assert data["must_use_transactions"] is True


# ─── scaffold_planner now emits service / auth / background everywhere ──────

def _scaffold(framework: str, tmp_path: Path) -> dict:
    spec = {
        "feature": "test", "framework": framework, "language": "x",
        "test_contract": {"auth": "none", "pagination": "list"},
        "entities": [{"name": "Cart", "snake_name": "cart", "plural": "carts",
                      "action": "create", "attributes": []}],
        "api_surface": [], "wiring": {}, "relationships": [],
        "graph_imports": {},
    }
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    proc = _run("scaffold_planner.py", "--spec", str(spec_path))
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def test_django_scaffold_emits_service_auth_background(tmp_path):
    plan = _scaffold("django", tmp_path)
    kinds = {f["kind"] for f in plan["files_to_create"]}
    assert "django_service" in kinds
    assert "django_auth" in kinds
    assert "django_background_task" in kinds


def test_spring_scaffold_emits_auth_and_background(tmp_path):
    plan = _scaffold("spring", tmp_path)
    kinds = {f["kind"] for f in plan["files_to_create"]}
    assert "spring_auth" in kinds
    assert "spring_background" in kinds


def test_nestjs_scaffold_emits_auth_and_background(tmp_path):
    plan = _scaffold("nestjs", tmp_path)
    kinds = {f["kind"] for f in plan["files_to_create"]}
    assert "nestjs_auth" in kinds
    assert "nestjs_background" in kinds


def test_go_scaffold_emits_service_dto_auth_background(tmp_path):
    plan = _scaffold("go", tmp_path)
    kinds = {f["kind"] for f in plan["files_to_create"]}
    for expected in ("go_service", "go_dto", "go_auth", "go_background"):
        assert expected in kinds, f"Go scaffold missing {expected}; got {kinds}"


def test_nodejs_scaffold_emits_full_eight_file_layout(tmp_path):
    plan = _scaffold("nodejs", tmp_path)
    kinds = [f["kind"] for f in plan["files_to_create"]]
    for expected in NODEJS_KINDS:
        assert expected in kinds, f"Node.js scaffold missing {expected}; got {kinds}"
    # Wiring + migration metadata also populated
    assert plan["wiring_targets"] == ["src/app.js"]
    assert "sequelize-cli_migration_generate" in plan["migrations"]


def test_nodejs_scaffold_flags_stubs_when_db_missing(tmp_path):
    plan = _scaffold("nodejs", tmp_path)
    assert "src/db.js" in plan["stubs_needed"]
    assert "src/common/errors.js" in plan["stubs_needed"]


# ─── catalogue size monotone-grows ──────────────────────────────────────────

def test_body_hints_total_count_after_parity_work():
    """Before v4.2: 34 hints. After v4.2: +3 Django, +2 Spring, +2 NestJS,
    +4 Go, +8 Node.js = 19 new → catalogue should be ≥ 53."""
    proc = _run("body_hints.py", "--list", "--json")
    data = json.loads(proc.stdout)
    assert len(data) >= 53, f"expected ≥53 hint entries after v4.2 parity, got {len(data)}"
