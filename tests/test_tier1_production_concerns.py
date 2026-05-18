"""Tests for v4.3 Tier-1 production-concern hints.

Adds 9 cross-framework contract hints (under 'common' namespace) + 12
per-framework hints (soft_delete + file_upload, where ORM/HTTP syntax
diverges enough to warrant per-framework guidance).

Covers concerns most production APIs hit within the first 3 months:
pagination, idempotency, audit log, email templates, outbox pattern,
health checks, RBAC, API versioning, data migrations, soft delete,
file upload.
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


def _hint(framework: str, kind: str) -> dict:
    proc = _run("body_hints.py", "--framework", framework, "--kind", kind)
    assert proc.returncode == 0, f"missing hint ({framework}, {kind}): {proc.stderr}"
    return json.loads(proc.stdout)


# ─── 9 cross-framework contract hints ───────────────────────────────────────

CROSS_FRAMEWORK_CONTRACTS = [
    "pagination_contract",
    "idempotency_keys",
    "audit_log",
    "email_template",
    "outbox_pattern",
    "health_check_contract",
    "rbac_contract",
    "api_versioning_contract",
    "data_migration",
]


def test_all_cross_framework_contracts_present():
    proc = _run("body_hints.py", "--list", "--json")
    kinds = {h["kind"] for h in json.loads(proc.stdout) if h["framework"] == "common"}
    missing = set(CROSS_FRAMEWORK_CONTRACTS) - kinds
    assert not missing, f"missing common contracts: {missing}"


def test_pagination_contract_covers_offset_and_keyset():
    data = _hint("common", "pagination_contract")
    blob = json.dumps(data).lower()
    assert "offset" in blob, "pagination must document offset strategy"
    assert "keyset" in blob or "cursor" in blob, "pagination must document keyset/cursor"
    # safety floor: warns against unbounded limits
    assert any("max_limit" in p or "unbounded" in p.lower()
               for p in data.get("anti_patterns", []))


def test_idempotency_keys_have_ttl_and_replay_protection():
    data = _hint("common", "idempotency_keys")
    must_emit = " ".join(data["must_emit"])
    assert "ttl" in must_emit.lower() or "expires_at" in must_emit.lower()
    assert "hash" in must_emit.lower(), "must hash the request to detect different bodies"
    # never apply to GETs
    anti = " ".join(data["anti_patterns"]).lower()
    assert "get" in anti


def test_audit_log_is_append_only_and_redacts():
    data = _hint("common", "audit_log")
    anti = " ".join(data["anti_patterns"]).lower()
    assert "delete" in anti and "append-only" in anti or "never delete" in anti
    # secrets / PII concern
    assert "secret" in anti or "pii" in anti or "redact" in anti


def test_email_template_blocks_smtp_in_request_handler():
    data = _hint("common", "email_template")
    anti = " ".join(data["anti_patterns"]).lower()
    assert "smtp" in anti or "background" in anti
    # verification + reset templates required
    templates = " ".join(data["must_have_templates"])
    assert "verification" in templates.lower()
    assert "password_reset" in templates.lower() or "reset" in templates.lower()


def test_outbox_pattern_atomic_with_business_write():
    data = _hint("common", "outbox_pattern")
    guidance = data["guidance"].lower()
    assert "same db transaction" in guidance or "same transaction" in guidance \
        or "same tx" in guidance
    anti = " ".join(data["anti_patterns"]).lower()
    assert "broker" in anti and "request" in anti


def test_health_check_distinguishes_live_vs_ready():
    data = _hint("common", "health_check_contract")
    endpoints = " ".join(data["must_emit_endpoints"])
    assert "/livez" in endpoints
    assert "/readyz" in endpoints
    # framework-specific guidance map
    assert "fastapi" in data["file_hint_per_framework"]
    assert "spring" in data["file_hint_per_framework"]


def test_rbac_contract_centralises_authorization():
    data = _hint("common", "rbac_contract")
    anti = " ".join(data["anti_patterns"]).lower()
    assert "model layer" in anti or "model" in anti
    # role enum + permission strings
    blob = json.dumps(data).lower()
    assert "permission" in blob and "role" in blob


def test_api_versioning_uses_url_path_strategy():
    data = _hint("common", "api_versioning_contract")
    blob = json.dumps(data).lower()
    assert "/api/v" in blob
    anti = " ".join(data["anti_patterns"]).lower()
    assert "query" in anti and "param" in anti, "must rule out ?version="
    # Sunset / Deprecation headers must be documented
    assert "sunset" in blob or "deprecation" in blob


def test_data_migration_requires_batching_and_reversibility():
    data = _hint("common", "data_migration")
    anti = " ".join(data["anti_patterns"]).lower()
    assert "limit" in anti, "must warn against unbounded UPDATE"
    blob = json.dumps(data).lower()
    assert "reversible" in blob or "downgrade" in blob
    assert "batched" in blob or "batch" in blob


# ─── 6 per-framework soft_delete hints ──────────────────────────────────────

FRAMEWORKS_WITH_SOFT_DELETE = ["fastapi", "django", "spring", "nestjs", "go", "nodejs"]


def test_every_framework_has_soft_delete_hint():
    for fw in FRAMEWORKS_WITH_SOFT_DELETE:
        data = _hint(fw, "soft_delete")
        blob = json.dumps(data).lower()
        assert "deleted_at" in blob or "deletedat" in blob, \
            f"{fw} soft_delete must mention deleted_at column"
        anti = " ".join(data["anti_patterns"]).lower()
        assert "audit" in anti or "unique" in anti, \
            f"{fw} soft_delete must warn about audit-log or unique-constraint pitfalls"


def test_fastapi_soft_delete_uses_sqlalchemy_mixin():
    data = _hint("fastapi", "soft_delete")
    blob = json.dumps(data)
    assert "SoftDeleteMixin" in blob or "deleted_at" in blob
    assert "hard_delete" in blob.lower(), "must keep an escape hatch"


def test_django_soft_delete_uses_custom_manager():
    data = _hint("django", "soft_delete")
    blob = json.dumps(data)
    assert "Manager" in blob
    assert "all_objects" in blob or "all_with_deleted" in blob


def test_spring_soft_delete_uses_sqldelete_annotation():
    data = _hint("spring", "soft_delete")
    blob = json.dumps(data)
    assert "@SQLDelete" in blob
    assert "@Where" in blob


def test_nestjs_soft_delete_uses_typeorm_decorator():
    data = _hint("nestjs", "soft_delete")
    blob = json.dumps(data)
    assert "@DeleteDateColumn" in blob
    assert "softDelete" in blob


def test_go_soft_delete_uses_gorm_deletedat():
    data = _hint("go", "soft_delete")
    blob = json.dumps(data)
    assert "gorm.DeletedAt" in blob or "DeletedAt" in blob
    assert "Unscoped" in blob, "Go soft delete must document Unscoped() for hard delete"


def test_nodejs_soft_delete_uses_sequelize_paranoid():
    data = _hint("nodejs", "soft_delete")
    blob = json.dumps(data).lower()
    assert "paranoid" in blob


# ─── 6 per-framework file_upload hints ──────────────────────────────────────

def test_every_framework_has_file_upload_hint():
    for fw in FRAMEWORKS_WITH_SOFT_DELETE:
        data = _hint(fw, "file_upload")
        anti = " ".join(data["anti_patterns"]).lower()
        # Universal pitfalls — every framework hint must warn about these
        assert "content" in anti or "sniff" in anti or "mimetype" in anti, \
            f"{fw} file_upload must warn against trusting client-supplied content-type"
        blob = json.dumps(data).lower()
        assert "max" in blob and ("size" in blob or "byte" in blob), \
            f"{fw} file_upload must enforce a max size"


def test_fastapi_file_upload_streams_chunks():
    data = _hint("fastapi", "file_upload")
    blob = json.dumps(data)
    assert "UploadFile" in blob
    assert "chunk" in blob.lower(), "must read in chunks (DoS protection)"


def test_django_file_upload_uses_multipartparser():
    data = _hint("django", "file_upload")
    blob = json.dumps(data)
    assert "MultiPartParser" in blob


def test_spring_file_upload_uses_multipartfile():
    data = _hint("spring", "file_upload")
    blob = json.dumps(data)
    assert "MultipartFile" in blob


def test_nestjs_file_upload_uses_fileinterceptor():
    data = _hint("nestjs", "file_upload")
    blob = json.dumps(data)
    assert "FileInterceptor" in blob


def test_go_file_upload_uses_form_file():
    data = _hint("go", "file_upload")
    blob = json.dumps(data)
    assert "FormFile" in blob or "multipart" in blob.lower()


def test_nodejs_file_upload_uses_multer():
    data = _hint("nodejs", "file_upload")
    blob = json.dumps(data).lower()
    assert "multer" in blob


# ─── catalogue size monotone-grows ──────────────────────────────────────────

def test_body_hints_total_count_after_tier1_concerns():
    """v4.2 ended at 56 hints. v4.3 adds 9 common + 12 per-framework = 21.
    Expect >= 77 entries after Tier-1 production-concern work."""
    proc = _run("body_hints.py", "--list", "--json")
    data = json.loads(proc.stdout)
    assert len(data) >= 77, f"expected >= 77 hint entries after v4.3 Tier 1, got {len(data)}"
