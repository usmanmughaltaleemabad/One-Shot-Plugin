"""Tests for v4.4 Tier-2 production-concern hints.

8 cross-framework contracts under 'common' namespace covering the
production patterns most apps hit between months 3-12: webhook
send/receive, multi-tenancy, feature flags, optimistic locking,
retry+circuit breaker, configuration management, websockets.
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


TIER2_CONTRACTS = [
    "webhook_sender",
    "webhook_receiver",
    "multi_tenancy",
    "feature_flags",
    "optimistic_locking",
    "retry_circuit_breaker",
    "configuration_management",
    "websocket_endpoint",
]


def test_all_tier2_contracts_present():
    proc = _run("body_hints.py", "--list", "--json")
    kinds = {h["kind"] for h in json.loads(proc.stdout) if h["framework"] == "common"}
    missing = set(TIER2_CONTRACTS) - kinds
    assert not missing, f"missing tier-2 contracts: {missing}"


# ─── webhook_sender ─────────────────────────────────────────────────────────

def test_webhook_sender_signs_and_retries_async():
    data = _hint("common", "webhook_sender")
    blob = json.dumps(data).lower()
    assert "hmac" in blob, "must HMAC-sign outbound webhooks"
    assert "timestamp" in blob, "must include timestamp for replay protection"
    anti = " ".join(data["anti_patterns"]).lower()
    assert "synchronously" in anti or "enqueue" in anti, \
        "must warn against sending sync from request path"
    assert "per-subscriber" in anti or "reuse" in anti, \
        "must require per-subscription secrets"


# ─── webhook_receiver ───────────────────────────────────────────────────────

def test_webhook_receiver_constant_time_compare_and_replay_window():
    data = _hint("common", "webhook_receiver")
    blob = json.dumps(data).lower()
    assert "timestamp" in blob and ("5 min" in blob or "300" in blob), \
        "must bound timestamp drift (replay protection)"
    anti = " ".join(data["anti_patterns"]).lower()
    assert "compare_digest" in anti or "constant-time" in anti or "timing" in anti, \
        "must warn against == signature comparison (timing attack)"
    assert "raw" in anti, "must sign the RAW body, not parsed JSON"


# ─── multi_tenancy ──────────────────────────────────────────────────────────

def test_multi_tenancy_documents_three_strategies():
    data = _hint("common", "multi_tenancy")
    blob = json.dumps(data).lower()
    assert "shared-schema" in blob or "shared schema" in blob
    assert "schema-per-tenant" in blob or "schema per tenant" in blob
    assert "database-per-tenant" in blob or "database per tenant" in blob


def test_multi_tenancy_blocks_body_supplied_tenant_id():
    data = _hint("common", "multi_tenancy")
    anti = " ".join(data["anti_patterns"]).lower()
    assert "request body" in anti, \
        "must never trust client-supplied tenant_id"
    assert "unique" in anti, "must require unique constraints include tenant_id"


# ─── feature_flags ──────────────────────────────────────────────────────────

def test_feature_flags_abstracts_provider_and_caches():
    data = _hint("common", "feature_flags")
    blob = json.dumps(data).lower()
    assert "launchdarkly" in blob or "unleash" in blob, "must mention real provider"
    anti = " ".join(data["anti_patterns"]).lower()
    assert "cache" in anti or "hot loop" in anti, \
        "must warn about uncached hot-loop flag checks"
    assert "security" in anti, \
        "must rule out using flags for auth decisions"


# ─── optimistic_locking ─────────────────────────────────────────────────────

def test_optimistic_locking_uses_version_column_and_409():
    data = _hint("common", "optimistic_locking")
    blob = json.dumps(data).lower()
    assert "version" in blob
    assert "409" in blob, "must surface 409 Conflict on lost update"
    anti = " ".join(data["anti_patterns"]).lower()
    assert "updated_at" in anti, "must rule out updated_at as a version surrogate"
    # framework-specific guidance map
    assert "fastapi" in data["file_hint_per_framework"]
    assert "spring" in data["file_hint_per_framework"]


# ─── retry_circuit_breaker ──────────────────────────────────────────────────

def test_retry_circuit_breaker_has_jitter_and_idempotency_warning():
    data = _hint("common", "retry_circuit_breaker")
    blob = json.dumps(data).lower()
    assert "jitter" in blob, "must require jitter to avoid synchronised retries"
    assert "exponential" in blob, "must use exponential backoff"
    anti = " ".join(data["anti_patterns"]).lower()
    assert "idempot" in anti or "post" in anti, \
        "must warn against blind retry of non-idempotent POSTs"
    # framework-specific tooling map
    libs = json.dumps(data["file_hint_per_framework"]).lower()
    assert "resilience4j" in libs, "Spring should reference Resilience4j"
    assert "tenacity" in libs or "backoff" in libs, "Python should reference tenacity"


# ─── configuration_management ──────────────────────────────────────────────

def test_configuration_management_validates_at_boot_and_isolates_secrets():
    data = _hint("common", "configuration_management")
    blob = json.dumps(data).lower()
    assert "fail-fast" in blob or "fail fast" in blob, \
        "must validate at boot"
    anti = " ".join(data["anti_patterns"]).lower()
    assert "os.getenv" in anti or "scatter" in anti, \
        "must rule out scattered env reads"
    assert "version control" in anti or "secrets" in anti, \
        "must rule out secrets in source"
    # framework hints reference real libraries
    libs = json.dumps(data["file_hint_per_framework"]).lower()
    assert "pydantic-settings" in libs or "pydantic_settings" in libs
    assert "@configurationproperties" in libs, "Spring should mention @ConfigurationProperties"


# ─── websocket_endpoint ────────────────────────────────────────────────────

def test_websocket_endpoint_auth_at_connect_and_heartbeat():
    data = _hint("common", "websocket_endpoint")
    blob = json.dumps(data).lower()
    assert "heartbeat" in blob or "ping" in blob, "must include keep-alive/ping"
    assert "authenticate" in blob or "auth" in blob, "must auth on connect"
    anti = " ".join(data["anti_patterns"]).lower()
    assert "rate" in anti or "dos" in anti, "must rate-limit pushes"
    # framework-specific routing fully specified
    libs = json.dumps(data["file_hint_per_framework"]).lower()
    assert "django channels" in libs, "Django should reference Channels"
    assert "gorilla" in libs or "websocket" in libs, "Go should reference gorilla/websocket"


# ─── catalogue size monotone-grows ─────────────────────────────────────────

def test_body_hints_total_count_after_tier2_concerns():
    """v4.3 ended at 77 hints. v4.4 adds 8 cross-framework Tier-2 contracts.
    Expect >= 85 entries."""
    proc = _run("body_hints.py", "--list", "--json")
    data = json.loads(proc.stdout)
    assert len(data) >= 85, f"expected >= 85 hint entries after v4.4 Tier 2, got {len(data)}"
