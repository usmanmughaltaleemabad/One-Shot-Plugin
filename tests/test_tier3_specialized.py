"""Tests for v4.5 Tier-3 specialized hints.

6 cross-framework specialized contracts:
  - graphql_resolver: code-first, DataLoader-mandatory
  - grpc_service: proto-first, shared service layer, mTLS in prod
  - saga_orchestrator: forward+compensation, idempotent, crash-safe state
  - dead_letter_queue: distinct from outbox; growth-rate alerts; never auto-requeue
  - gdpr_export_delete: anonymise when legal retention applies; signed URLs
  - i18n: locale catalogues, never concatenate fragments
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
    assert proc.returncode == 0, f"missing ({framework}, {kind}): {proc.stderr}"
    return json.loads(proc.stdout)


TIER3_CONTRACTS = [
    "graphql_resolver",
    "grpc_service",
    "saga_orchestrator",
    "dead_letter_queue",
    "gdpr_export_delete",
    "i18n",
]


def test_all_tier3_contracts_present():
    proc = _run("body_hints.py", "--list", "--json")
    kinds = {h["kind"] for h in json.loads(proc.stdout) if h["framework"] == "common"}
    missing = set(TIER3_CONTRACTS) - kinds
    assert not missing, f"missing tier-3 contracts: {missing}"


# ─── graphql_resolver ───────────────────────────────────────────────────────

def test_graphql_resolver_mandates_dataloader_and_service_delegation():
    data = _hint("common", "graphql_resolver")
    blob = json.dumps(data).lower()
    assert "dataloader" in blob, "must require DataLoader for N+1 prevention"
    anti = " ".join(data["anti_patterns"]).lower()
    assert "business logic" in anti or "service" in anti, \
        "must rule out business logic in resolvers"
    assert "n+1" in anti, "must explicitly warn about N+1"
    # framework map covers real GraphQL libs
    libs = json.dumps(data["file_hint_per_framework"]).lower()
    assert "strawberry" in libs and "graphene" in libs
    assert "dgs" in libs or "graphql-java" in libs


# ─── grpc_service ───────────────────────────────────────────────────────────

def test_grpc_uses_proto_first_and_shared_service_layer():
    data = _hint("common", "grpc_service")
    blob = json.dumps(data).lower()
    assert ".proto" in blob, "must be proto-first"
    must = " ".join(data["must_emit"]).lower()
    assert "delegate" in must or "service" in must, \
        "must delegate to existing service layer"
    anti = " ".join(data["anti_patterns"]).lower()
    assert "duplicate" in anti, "must rule out duplicating logic vs REST"
    assert "plaintext" in anti or "tls" in anti, "must require TLS in prod"
    assert "reserved" in anti or "breaking" in anti or "break" in anti, \
        "must rule out breaking proto changes in place"


# ─── saga_orchestrator ──────────────────────────────────────────────────────

def test_saga_orchestrator_requires_compensation_and_persistence():
    data = _hint("common", "saga_orchestrator")
    blob = json.dumps(data).lower()
    assert "compensation" in blob or "compensating" in blob, \
        "must require compensating actions"
    assert "saga_instances" in blob, "must persist saga state"
    assert "idempotent" in blob, "every step must be idempotent"
    anti = " ".join(data["anti_patterns"]).lower()
    assert "2pc" in anti or "xa" in anti, "must rule out distributed-transaction protocols"
    assert "lifo" in anti or "reverse" in anti, \
        "compensations must run in reverse"


# ─── dead_letter_queue ──────────────────────────────────────────────────────

def test_dlq_distinct_from_outbox_and_no_auto_requeue():
    data = _hint("common", "dead_letter_queue")
    blob = json.dumps(data).lower()
    assert "outbox" in blob, "must distinguish from outbox"
    anti = " ".join(data["anti_patterns"]).lower()
    assert "auto-requeue" in anti or "infinite" in anti, \
        "must rule out auto-requeue (infinite loops)"
    assert "unbounded" in anti or "prune" in anti or "30 days" in anti, \
        "must require bounded growth"
    # admin surface required
    must = " ".join(data["must_emit"]).lower()
    assert "admin" in must, "must expose an admin surface"
    assert "growth" in must or "metric" in must, "must monitor growth rate"


# ─── gdpr_export_delete ─────────────────────────────────────────────────────

def test_gdpr_distinguishes_anonymise_from_hard_delete():
    data = _hint("common", "gdpr_export_delete")
    blob = json.dumps(data).lower()
    assert "anonymise" in blob or "anonymize" in blob, \
        "must offer anonymise as alternative to hard-delete"
    assert "retention" in blob or "legal" in blob, \
        "must reason about legal retention obligations"
    anti = " ".join(data["anti_patterns"]).lower()
    assert "email" in anti and ("url" in anti or "ttl" in anti), \
        "must rule out emailing raw data; require signed URLs"
    assert "audit" in anti, "audit log is special — must be considered"
    assert "third-part" in anti or "other users" in anti, \
        "must consider third-party PII in user's archive"


# ─── i18n ───────────────────────────────────────────────────────────────────

def test_i18n_resolution_order_and_concatenation_warning():
    data = _hint("common", "i18n")
    blob = json.dumps(data).lower()
    assert "accept-language" in blob, "must parse Accept-Language header"
    assert "q-value" in blob or "q value" in blob, \
        "must respect Accept-Language q-values"
    anti = " ".join(data["anti_patterns"]).lower()
    assert "concatenate" in anti, \
        "must rule out concatenating translated fragments"
    assert "rtl" in anti or "right-to-left" in anti, \
        "must mention RTL locale handling"
    libs = json.dumps(data["file_hint_per_framework"]).lower()
    assert "gettext" in libs or "babel" in libs, "Python should reference gettext/Babel"
    assert "messagesource" in libs or "resourcebundle" in libs, \
        "Spring should reference MessageSource / ResourceBundle"


# ─── catalogue size monotone-grows ─────────────────────────────────────────

def test_body_hints_total_count_after_tier3():
    """v4.4 ended at 85 hints. v4.5 adds 6 specialised contracts.
    Expect >= 91 entries."""
    proc = _run("body_hints.py", "--list", "--json")
    data = json.loads(proc.stdout)
    assert len(data) >= 91, f"expected >= 91 hint entries after v4.5 Tier 3, got {len(data)}"
