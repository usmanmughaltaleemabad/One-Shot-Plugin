#!/usr/bin/env python3
"""
Spec Compiler — v0.9.0  (Tier 2 bridge)

Takes a finished ``OrchestratorReport`` (the structured JSON the orchestrator
emits) plus the original domain model and produces ``spec.json`` — the
canonical contract the architect / implementer / test-author / reviewer /
wirer / critic agents all consume.

This is the explicit handoff from Tier 1 (deterministic Python pipeline)
to Tier 2 (multi-agent specialist execution). The compiler does:

  * Build a list of every entity needing a new module, with attributes,
    invariants, and required modules.
  * Derive the API surface (CRUD by default; auth flows for ``intent: auth``;
    job-queue endpoints for ``intent: batch``).
  * Pin the test contract from the codebase graph — auth style, pagination
    shape, error envelope, error codes the project already uses.
  * Plan the wiring — which files the wirer should edit, which migrations
    must run.

The spec is the single source of truth. If the architect, implementer, and
test-author disagree, the spec wins. The critic enforces it.

CLI:
    python compile_spec.py --orchestrator-json report.json --out spec.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from lib.base_script import bootstrap_runtime, setup_logging
bootstrap_runtime()

logger = setup_logging(__name__)


# ─── Defaults the architect agent will inherit ───────────────────────────────

_DEFAULT_INVARIANTS = {
    "shopping_cart": [
        "total = sum(line_items.unit_price * quantity) - sum(discounts)",
        "cannot check out while inventory_holds are still active",
    ],
    "line_item": [
        "quantity must be positive integer",
        "unit_price must be non-negative",
    ],
    "discount": [
        "exactly one of percent_off / amount_off must be set",
        "valid_until must be in the future when applied",
    ],
    "inventory_hold": [
        "expires_at must be strictly greater than created_at",
        "quantity is consumed from the product's available stock",
    ],
    "order": [
        "total = sum(line_items) - sum(discounts) + tax",
        "status transitions: pending → paid → fulfilled → closed (no skipping)",
    ],
    "user": [
        "email must be RFC-5322 valid and unique",
        "password_hash must use a current hashing algorithm (bcrypt/argon2/scrypt)",
    ],
    "audit": [
        "every record is append-only; never modified after creation",
        "actor_id is required for any action initiated by an authenticated user",
    ],
}


def _crud_endpoints(entity_plural: str, entity_pascal: str) -> List[Dict]:
    return [
        {"method": "GET",    "path": f"/api/v1/{entity_plural}",
         "handler": f"list_{entity_plural}",
         "response": f"List[{entity_pascal}Schema]"},
        {"method": "POST",   "path": f"/api/v1/{entity_plural}",
         "handler": f"create_{entity_pascal.lower()}",
         "request": f"{entity_pascal}CreateSchema",
         "response": f"{entity_pascal}Schema",
         "status": 201},
        {"method": "GET",    "path": f"/api/v1/{entity_plural}/{{id}}",
         "handler": f"retrieve_{entity_pascal.lower()}",
         "response": f"{entity_pascal}Schema"},
        {"method": "PUT",    "path": f"/api/v1/{entity_plural}/{{id}}",
         "handler": f"update_{entity_pascal.lower()}",
         "request": f"{entity_pascal}UpdateSchema",
         "response": f"{entity_pascal}Schema"},
        {"method": "DELETE", "path": f"/api/v1/{entity_plural}/{{id}}",
         "handler": f"delete_{entity_pascal.lower()}",
         "status": 204},
    ]


def _intent_to_endpoints(intent: str, plural: str, pascal: str) -> List[Dict]:
    if intent == "auth":
        return [
            {"method": "POST", "path": "/api/v1/auth/signup",
             "handler": "signup", "status": 201,
             "request": "SignupSchema", "response": "UserSchema"},
            {"method": "POST", "path": "/api/v1/auth/login",
             "handler": "login",
             "request": "LoginSchema", "response": "TokenSchema"},
            {"method": "POST", "path": "/api/v1/auth/verify",
             "handler": "verify_email",
             "request": "VerifyTokenSchema", "status": 204},
            {"method": "POST", "path": "/api/v1/auth/password-reset",
             "handler": "request_password_reset",
             "request": "PasswordResetRequestSchema", "status": 202},
        ]
    if intent == "batch":
        return [
            {"method": "POST", "path": f"/api/v1/jobs/{pascal.lower()}",
             "handler": f"enqueue_{pascal.lower()}",
             "request": f"{pascal}JobSchema", "response": "JobAckSchema",
             "status": 202},
            {"method": "GET",  "path": f"/api/v1/jobs/{pascal.lower()}/{{job_id}}",
             "handler": f"status_{pascal.lower()}",
             "response": "JobStatusSchema"},
        ]
    return _crud_endpoints(plural, pascal)


# ─── Public entry ────────────────────────────────────────────────────────────

def compile_spec(report: Dict[str, Any]) -> Dict[str, Any]:
    """Turn an OrchestratorReport into a spec.json document."""
    intent = report.get("intent", "feature")
    cs = report.get("codebase_summary", {})
    framework = cs.get("framework", "unknown")
    conventions = cs.get("conventions", {}) or {}
    test_contract = {
        # If the codebase has auth scaffolding we pick it up; otherwise the
        # default is "none" so we don't generate impossible 401 tests.
        "auth": "jwt" if any("auth" in (k or "").lower()
                              for k in (cs.get("imports") or {}))
                       else "none",
        "pagination": "list",
        "error_shape": "fastapi_httpexception" if framework == "fastapi"
                       else "drf_validationerror" if framework == "django"
                       else "rfc7807",
        "naming": conventions.get("naming", "snake_case"),
    }

    entities_spec: List[Dict] = []
    for reconciled in report.get("reconciled_entities", []):
        name = reconciled.get("entity_name")
        pascal = reconciled.get("pascal", name.capitalize() if name else "Entity")
        plural = reconciled.get("plural", f"{name}s")
        action = "reuse" if reconciled.get("status") == "exists" else "create"
        ent = {
            "name": pascal,
            "snake_name": name,
            "plural": plural,
            "action": action,
            "attributes": reconciled.get("attributes", []),
            "invariants": _DEFAULT_INVARIANTS.get(name, []),
        }
        if action == "reuse":
            ent["existing_file"] = reconciled.get("existing_file")
        else:
            ent["module"] = f"{name}/models.py" if framework == "fastapi" else f"{name}/__init__.py"
        entities_spec.append(ent)

    # API surface uses the PRIMARY entity for intent-driven shapes; secondary
    # entities each get CRUD endpoints in addition.
    api_surface: List[Dict] = []
    primary = next((e for e in entities_spec if e["action"] == "create"), None)
    if primary:
        api_surface.extend(_intent_to_endpoints(intent, primary["plural"], primary["name"]))
    for e in entities_spec:
        if e is primary:
            continue
        if e["action"] == "create":
            api_surface.extend(_crud_endpoints(e["plural"], e["name"]))

    # Wiring plan derived from the orchestrator's auto_wirer report
    wire = report.get("wire") or {}
    wiring = {
        "framework": wire.get("framework", framework),
        "edits": [a.get("after", "") for a in wire.get("actions", [])],
    }
    if framework == "fastapi":
        wiring["migrations"] = [
            f"alembic_{e['snake_name']}" for e in entities_spec if e["action"] == "create"
        ]
    elif framework == "django":
        wiring["migrations"] = ["python manage.py makemigrations && python manage.py migrate"]

    return {
        "feature": report.get("task", ""),
        "intent": intent,
        "framework": framework,
        "language": cs.get("language"),
        "test_contract": test_contract,
        "entities": entities_spec,
        "api_surface": api_surface,
        "wiring": wiring,
        "open_questions": _derive_open_questions(report, entities_spec),
        "source_report": {
            "confidence": report.get("confidence"),
            "bead_id": report.get("bead_id"),
        },
    }


def _derive_open_questions(report: Dict, entities: List[Dict]) -> List[str]:
    questions: List[str] = []
    conf = report.get("confidence", 0.0) or 0.0
    if conf < 0.7:
        questions.append(
            f"Low confidence ({conf:.2f}) — please confirm the primary entity is "
            f"'{entities[0]['name']}' if any were extracted."
        )
    for ent in entities:
        if ent["action"] == "create" and not ent.get("invariants"):
            questions.append(
                f"No default invariants for '{ent['name']}' — should this entity "
                "have any business rules beyond CRUD?"
            )
    return questions


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Compile an OrchestratorReport into a spec.json the agents consume"
    )
    parser.add_argument("--orchestrator-json", required=True,
                        help="Path to JSON from one_shot_orchestrator --json")
    parser.add_argument("--out", default=None,
                        help="Where to write spec.json (default: stdout)")
    args = parser.parse_args()

    report = json.loads(Path(args.orchestrator_json).read_text(encoding="utf-8"))
    spec = compile_spec(report)
    payload = json.dumps(spec, indent=2)
    if args.out:
        Path(args.out).write_text(payload, encoding="utf-8")
        print(f"wrote {args.out}", file=sys.stderr)
    else:
        print(payload)


if __name__ == "__main__":
    main()
