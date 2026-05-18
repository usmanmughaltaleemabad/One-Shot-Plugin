#!/usr/bin/env python3
"""
Body Hints — v1.0.0  (cross-language implementer guidance)

The scaffold_planner emits *what files to create* across 5 frameworks
(FastAPI, Django, Spring, Go, NestJS). Each implementer agent then
needs to know *what idiomatic code goes inside* each file kind.

This module is the bridge: given a (framework, file_kind) pair, return
a structured hint document the implementer agent uses as a contract.

Hints are NOT templates with substitutions — they describe the shape,
imports, methods, and contract the agent must satisfy. The agent
fills in the actual code by reasoning about the spec.json's entity
attributes + the codebase's conventions.

CLI:
    python body_hints.py --framework django --kind drf_viewset
    python body_hints.py --framework spring --kind spring_controller
    python body_hints.py --list   # show all available hints
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Dict, List, Optional

from lib.base_script import bootstrap_runtime, setup_logging
bootstrap_runtime()

logger = setup_logging(__name__)


# ─── Hint catalogue ──────────────────────────────────────────────────────────

HINTS: Dict[tuple, Dict] = {

    # ─── FastAPI ─────────────────────────────────────────────────────────
    ("fastapi", "sqlalchemy_model"): {
        "language": "python",
        "imports_must_include": [
            "from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, Float, ForeignKey",
            "from sqlalchemy.orm import relationship",
            "from {base_module} import {base_name}",
        ],
        "class_decl": "class {Pascal}({base_name}):",
        "tablename": "__tablename__ = '{plural}'",
        "must_have_columns": ["id (primary key)", "created_at", "updated_at"],
        "must_include_fks_from_relationships": True,
        "must_include_repr": True,
        "anti_patterns": [
            "Don't redeclare Base if it already exists in {base_module}",
            "Don't import datetime.utcnow without scheduling deprecation note",
        ],
    },
    ("fastapi", "pydantic_schema"): {
        "language": "python",
        "imports_must_include": [
            "from pydantic import BaseModel, Field",
            "from datetime import datetime",
        ],
        "must_emit_classes": ["{Pascal}Base", "{Pascal}Create", "{Pascal}Read", "{Pascal}Update"],
        "read_must_have": ["id: int", "created_at: datetime", "updated_at: datetime",
                            "model_config = {'from_attributes': True}"],
        "update_must": "Use Optional[...] = None for every field (PATCH semantics)",
        "anti_patterns": [
            "Don't add `class Config: orm_mode = True` — use model_config instead (Pydantic v2)",
        ],
    },
    ("fastapi", "fastapi_router"): {
        "language": "python",
        "imports_must_include": [
            "from fastapi import APIRouter, Depends, HTTPException, status",
            "from sqlalchemy.orm import Session",
            "from {db_module} import {db_func}",
        ],
        "router_decl": "router = APIRouter(prefix='/api/v1/{plural}', tags=['{snake}'])",
        "must_emit_endpoints": [
            "GET /  (list, response_model=List[{Pascal}Read])",
            "POST / (create, status=201, response_model={Pascal}Read)",
            "GET /{{item_id}}  (retrieve, 404 if missing)",
            "PUT /{{item_id}}  (update, 404 if missing)",
            "DELETE /{{item_id}}  (status=204, 404 if missing)",
        ],
        "auth_pattern": "Apply Depends() per spec.test_contract.auth ('none' → no auth)",
        "anti_patterns": [
            "Don't generate 401 logic if test_contract.auth == 'none'",
            "Don't return raw SQLAlchemy objects — use response_model on every route",
        ],
    },
    ("fastapi", "pytest_module"): {
        "language": "python",
        "imports_must_include": ["from fastapi.testclient import TestClient"],
        "fixture_assumed": "client: TestClient (project's conftest)",
        "must_test": [
            "list returns 200 + list shape",
            "create round-trip (POST → 201, retrieve confirms)",
            "retrieve missing returns 404",
        ],
        "test_contract_alignment": "Read spec.test_contract — DO NOT assert 401 if auth='none'",
        "anti_patterns": [
            "Don't assert pagination envelope keys if test_contract.pagination='list'",
            "Don't assume auth dependency unless test_contract.auth != 'none'",
        ],
    },
    ("fastapi", "python_init"): {
        "language": "python",
        "guidance": "Empty file (Python package marker)",
    },
    ("fastapi", "service_layer"): {
        "language": "python",
        "imports_must_include": [
            "from sqlalchemy.orm import Session",
            "from fastapi import HTTPException, status",
            "from .models import {Pascal}",
            "from common.events import emit",
            "from common.exceptions import DomainError",
        ],
        "class_decl": "class {Pascal}Service:",
        "must_emit_methods": [
            "__init__(self, db: Session)",
            "list(self, *, skip=0, limit=100)",
            "get_or_404(self, item_id)",
            "create(self, payload, *, actor_id)",
            "update(self, item_id, payload, *, actor_id)",
            "delete(self, item_id, *, actor_id)",
        ],
        "must_enforce_invariants_from_spec": True,
        "must_use_transactions": True,
        "must_emit_events_on_state_transitions": True,
        "anti_patterns": [
            "Don't put HTTPException(401/403) — that's router-level",
            "Don't import from router.py — service is the lower layer",
            "Don't write raw SQL — use SQLAlchemy session",
        ],
    },
    ("fastapi", "auth_endpoints"): {
        "language": "python",
        "imports_must_include": [
            "from passlib.context import CryptContext",
            "from jose import JWTError, jwt",
        ],
        "must_emit_helpers": [
            "pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')",
            "hash_password(plain) -> str",
            "verify_password(plain, hashed) -> bool",
            "create_access_token(subject, expires_in_minutes=60) -> str",
            "decode_access_token(token) -> dict",
        ],
        "must_use_bcrypt_not_plain_hash": True,
        "must_schedule_email_via_background_task": True,
        "anti_patterns": [
            "Never store plain passwords",
            "Never put JWT secret in source — read from env",
            "Never accept verification tokens older than 24h",
        ],
    },
    ("fastapi", "soft_delete"): {
        "language": "python",
        "guidance": (
            "SQLAlchemy mixin pattern. Add deleted_at DateTime column (nullable). "
            "Default query helpers filter where deleted_at IS NULL. .delete() sets "
            "deleted_at = utcnow() instead of issuing DELETE. .hard_delete() still "
            "available for GDPR / admin operations."
        ),
        "must_emit": [
            "class SoftDeleteMixin: deleted_at = Column(DateTime, nullable=True, index=True)",
            "Service.list() — filter .where({Pascal}.deleted_at.is_(None)) by default",
            "Service.delete() — sets deleted_at = datetime.now(timezone.utc); commits",
            "Service.hard_delete() — issues real DELETE (admin only)",
        ],
        "anti_patterns": [
            "Don't forget the partial index on deleted_at — full-table scans otherwise",
            "Don't allow soft-deleted rows in UNIQUE constraints — use partial unique index WHERE deleted_at IS NULL",
            "Don't soft-delete audit_log rows — audit must be append-only",
        ],
    },
    ("fastapi", "file_upload"): {
        "language": "python",
        "imports_must_include": [
            "from fastapi import UploadFile, File, HTTPException, status",
            "import hashlib, os",
        ],
        "must_emit_endpoints": [
            "POST /{{plural}}/{{id}}/upload  body=multipart/form-data  field='file: UploadFile'",
        ],
        "guidance": (
            "Validate: content_type allowlist, max size (read in chunks; never load "
            "entire body into memory), virus scan stub. Storage: S3 presigned PUT "
            "preferred (client uploads direct to S3, server only signs); local disk "
            "only for dev. Store the storage_key + content_type + size + sha256 in "
            "DB; never store the bytes in the DB row."
        ),
        "must_emit": [
            "MAX_FILE_BYTES constant from env (default 10 MB)",
            "ALLOWED_CONTENT_TYPES set",
            "Chunked read loop: while chunk := await file.read(64*1024): hasher.update(chunk); size += len(chunk); abort if size > MAX",
            "Helper: presign_s3_put(key, content_type, expires_in=900) -> {url, fields}",
        ],
        "anti_patterns": [
            "Never trust client-supplied content_type — sniff first bytes",
            "Never await file.read() without a size cap — denial-of-service via huge upload",
            "Never store bytes in the DB row (BLOB) — separate object storage",
            "Never use the original filename as the storage key — generate UUID-based keys",
        ],
    },
    ("fastapi", "background_task"): {
        "language": "python",
        "imports_must_include": ["from fastapi import BackgroundTasks"],
        "guidance": (
            "FastAPI BackgroundTasks for fire-and-forget. Celery (detected "
            "via codebase_graph) for retryable / scheduled work. Pass IDs, "
            "not models."
        ),
        "anti_patterns": [
            "Don't block the request handler on external IO",
            "Don't store sensitive data in BackgroundTasks payload",
        ],
    },
    ("common", "events_emitter"): {
        "language": "python",
        "file": "common/events.py",
        "must_emit": [
            "_subscribers: dict[str, list] = {}",
            "def emit(event_name: str, **payload) -> None",
            "def subscribe(event_name: str, handler) -> None",
        ],
        "guidance": (
            "Stub pub/sub. Default logs to stderr; production swaps for "
            "Kafka / SNS / Redis Streams. Serialise payload to JSON-compatible "
            "before emit."
        ),
    },
    ("common", "domain_exceptions"): {
        "language": "python",
        "file": "common/exceptions.py",
        "must_emit_classes": [
            "class DomainError(Exception)",
            "class NotFoundError(DomainError)",
            "class ConflictError(DomainError)",
            "class ForbiddenError(DomainError)",
            "class ValidationError(DomainError)",
        ],
        "guidance": "Each carries a `code: str` field for machine handling",
    },
    ("common", "rate_limiter"): {
        "language": "python",
        "file": "common/rate_limit.py",
        "imports_must_include": [
            "from fastapi import Request, HTTPException, status",
            "from collections import defaultdict, deque",
            "import time",
        ],
        "guidance": (
            "In-memory token bucket per (route, client_ip). For real "
            "production, swap for Redis-backed via slowapi or fastapi-limiter. "
            "Apply as a dependency: Depends(rate_limit('/auth/login', limit=5, window=60))"
        ),
        "must_emit": [
            "def rate_limit(route_key: str, limit: int, window: int) -> Callable",
            "_buckets: dict[tuple[str, str], deque] = defaultdict(deque)",
        ],
        "anti_patterns": [
            "Don't use in-memory state in multi-worker deployments — use Redis",
            "Don't rate-limit by user_id alone — combine with IP for unauthenticated routes",
        ],
    },
    ("common", "cache_layer"): {
        "language": "python",
        "file": "common/cache.py",
        "imports_must_include": [
            "from functools import wraps",
            "import hashlib, json, time",
        ],
        "guidance": (
            "TTL-based in-memory cache with optional Redis backend. "
            "Decorator API: @cached(ttl=60, key_prefix='cart.list'). "
            "Cache key = SHA-256 of (function_name, args, kwargs)."
        ),
        "must_emit": [
            "def cached(ttl: int = 60, key_prefix: str = '') -> Callable",
            "def invalidate(prefix: str) -> int",
        ],
        "anti_patterns": [
            "Don't cache write endpoints",
            "Don't cache per-user data with a global key — include user_id in the key",
            "Don't set TTL >5 minutes without an invalidation strategy",
        ],
    },
    ("common", "logging_setup"): {
        "language": "python",
        "file": "common/logging_setup.py",
        "imports_must_include": [
            "import logging, sys, json",
        ],
        "guidance": (
            "Structured JSON logging to stdout (12-factor). Each log "
            "entry: {ts, level, logger, message, trace_id, request_id, ...}. "
            "Routers inject request_id from X-Request-ID header (or generate)."
        ),
        "must_emit": [
            "def configure_logging(level: str = 'INFO') -> None",
            "class JsonFormatter(logging.Formatter)",
        ],
    },

    # ─── Tier-1 production concerns (v4.3) ──────────────────────────────────
    # Cross-framework contracts. Each implementer agent reads the contract
    # and translates to the host framework's idiomatic patterns.

    ("common", "pagination_contract"): {
        "scope": "cross-framework",
        "guidance": (
            "Two pagination strategies; pick per route based on spec.test_contract.pagination. "
            "OFFSET: query params skip + limit (max 100). Response: {items: [...], total: int, "
            "skip: int, limit: int}. KEYSET (cursor): query param cursor (opaque base64 of "
            "{last_id, last_ts}). Response: {items, next_cursor: str|null}. Keyset is required "
            "for any list that may exceed 10k rows or is sorted by created_at desc."
        ),
        "must_emit": [
            "encode_cursor(last_id, last_ts) -> str  (base64 of JSON)",
            "decode_cursor(cursor) -> dict | None",
            "paginate_offset(query, skip, limit, *, max_limit=100) -> dict",
            "paginate_keyset(query, cursor, limit, *, max_limit=100, key='created_at') -> dict",
        ],
        "anti_patterns": [
            "Never accept unbounded limit — clamp to max_limit",
            "Never expose raw DB cursors — encode opaque so we can change them later",
            "Never use OFFSET on tables that grow without bound — pagination cost grows O(skip)",
        ],
        "file_hint_per_framework": {
            "fastapi": "common/pagination.py",
            "django":  "common/pagination.py (or use rest_framework.pagination.CursorPagination)",
            "spring":  "src/main/java/com/example/common/Pagination.java + Pageable (Spring Data)",
            "nestjs":  "src/common/pagination/  (or nestjs-paginate package)",
            "go":      "internal/common/pagination.go",
            "nodejs":  "src/common/pagination.js",
        },
    },

    ("common", "idempotency_keys"): {
        "scope": "cross-framework",
        "guidance": (
            "Stripe-style idempotency for POST/PUT mutations. Client sends "
            "Idempotency-Key header (UUID); server stores {key, request_hash, "
            "response_status, response_body, created_at} in idempotency_keys "
            "table (24h TTL). On replay with same key + same hash: return cached "
            "response. Same key + different hash: 422 (conflict)."
        ),
        "must_emit": [
            "idempotency_keys table: key VARCHAR PK, request_hash VARCHAR, "
            "response_status INT, response_body TEXT, created_at TIMESTAMP, expires_at TIMESTAMP",
            "Middleware/decorator: idempotent(ttl_hours=24)",
            "Hash function: SHA-256 of (method, path, sorted_body_json)",
            "Background cleanup job: delete WHERE expires_at < now()",
        ],
        "anti_patterns": [
            "Never trust client-supplied keys without scope (combine with user_id)",
            "Never apply to GET — GETs are already idempotent",
            "Never cache 5xx — only 2xx/4xx (5xx may be transient)",
            "Never store the full request body in plain text if it contains secrets",
        ],
    },

    ("common", "audit_log"): {
        "scope": "cross-framework",
        "guidance": (
            "Append-only audit trail for every mutation. Captured: who (actor_id, actor_role), "
            "what (entity_type, entity_id, action: create/update/delete), when (timestamp), "
            "old_value (JSON snapshot before), new_value (JSON snapshot after), source (api/admin/job), "
            "request_id (correlates with logs). Emitted by service layer (NOT router) so background "
            "jobs and admin actions also audit. Storage: separate audit_log table, never DELETE rows."
        ),
        "must_emit": [
            "audit_log table: id, actor_id, actor_role, entity_type, entity_id, action, "
            "old_value JSON, new_value JSON, source, request_id, created_at",
            "audit(actor, entity, action, *, old=None, new=None, source='api') -> None",
            "Hook: emit from service.create/update/delete via the events module",
        ],
        "anti_patterns": [
            "Never DELETE from audit_log — partition / archive old rows instead",
            "Never log full payloads if they contain secrets (passwords, tokens, PII) — redact",
            "Never let an audit failure abort the business write — log and continue",
            "Never write the audit row in a separate transaction from the business write — use outbox",
        ],
    },

    ("common", "email_template"): {
        "scope": "cross-framework",
        "guidance": (
            "Templated email with HTML + plain-text fallback. Templates live in "
            "templates/email/{{template_name}}.{{html,txt}}.j2. Subject is the "
            "first line; body follows. Variables passed as a dict. Always send "
            "BOTH HTML and plain text (Multipart/Alternative). Subject/body are "
            "rendered server-side; never accept raw HTML from users."
        ),
        "must_emit": [
            "render_email(template_name, ctx) -> {subject: str, html: str, text: str}",
            "send_email(to, template_name, ctx, *, from_addr=None) -> None  "
            "(delegates to provider: SES/SendGrid/Mailgun — detected via codebase_graph)",
            "Background-task wrapper so request handler doesn't block on SMTP",
        ],
        "must_have_templates": [
            "verification_email.{html,txt}.j2",
            "password_reset.{html,txt}.j2",
        ],
        "anti_patterns": [
            "Never call SMTP from a request handler — always enqueue via background task",
            "Never interpolate user-supplied HTML into templates — escape always",
            "Never put the verification token in the email subject (subjects are often logged)",
            "Never put the SMTP password in source — env var or secret manager",
        ],
        "file_hint_per_framework": {
            "fastapi": "common/email.py + templates/email/",
            "django":  "use django.core.mail with templated body via render_to_string",
            "spring":  "JavaMailSender + Thymeleaf templates under resources/templates/email/",
            "nestjs":  "@nestjs-modules/mailer + Handlebars/Pug under templates/",
            "go":      "internal/common/email.go + text/template + html/template",
            "nodejs":  "src/common/email.js + nodemailer + Handlebars templates",
        },
    },

    ("common", "outbox_pattern"): {
        "scope": "cross-framework",
        "guidance": (
            "Transactional outbox for reliable event publishing. Business write + "
            "outbox row written in SAME DB transaction. A poller process reads "
            "unprocessed outbox rows and publishes to the real broker (Kafka/SNS/"
            "RabbitMQ/Redis Streams). Marks processed_at on success; retries with "
            "exponential backoff on failure. Guarantees at-least-once delivery "
            "without 2PC. The events.emit() function writes to outbox, not directly to broker."
        ),
        "must_emit": [
            "outbox table: id BIGINT PK, event_name VARCHAR, payload JSON, "
            "aggregate_type VARCHAR, aggregate_id VARCHAR, created_at, "
            "processed_at NULL, attempt_count INT DEFAULT 0, last_error TEXT NULL",
            "write_outbox(session, event_name, payload, aggregate_type, aggregate_id) — runs inside the business tx",
            "Worker process: poll WHERE processed_at IS NULL ORDER BY id LIMIT N; "
            "publish; UPDATE processed_at OR increment attempt_count + last_error",
            "Index: (processed_at, id) for poller; (aggregate_type, aggregate_id) for replay",
        ],
        "anti_patterns": [
            "Never publish to the broker inside the business request — that's what the outbox prevents",
            "Never DELETE processed outbox rows immediately — keep for N days for replay",
            "Never lose ordering for the same aggregate_id — single-threaded per aggregate or use partitioned queue",
            "Never poll without LIMIT — full-table scans kill performance",
        ],
    },

    ("common", "health_check_contract"): {
        "scope": "cross-framework",
        "guidance": (
            "Three endpoints, distinct semantics: "
            "/livez — process alive (200 if app is responding; no dependency checks). "
            "/readyz — ready to serve traffic (200 only if DB + broker + cache are reachable). "
            "/healthz — alias for /readyz (legacy / k8s convention). "
            "Kubernetes liveness probe hits /livez; readiness probe hits /readyz. "
            "Failing /readyz removes the pod from service; failing /livez restarts it."
        ),
        "must_emit_endpoints": [
            "GET /livez -> 200 {'status': 'ok'}  (NO dependency checks)",
            "GET /readyz -> 200 {'status': 'ok', 'checks': {db: true, broker: true, cache: true}} OR 503 with failing checks",
            "GET /healthz -> alias for /readyz",
        ],
        "anti_patterns": [
            "Never check external APIs (third parties) in /readyz — they'll flap and remove your pod from rotation",
            "Never put auth on these endpoints — load balancers + k8s probes are unauthenticated",
            "Never make /livez do anything slow or fallible — it must respond < 100ms",
            "Never return 200 from /readyz when DB is down — the orchestrator can't shed load if you lie",
        ],
        "file_hint_per_framework": {
            "fastapi": "common/health.py (router @ /  )",
            "django":  "common/health.py (urls.py route) — or use django-health-check",
            "spring":  "Spring Boot Actuator: management.endpoints.web.exposure.include=health,info; add custom HealthIndicator beans",
            "nestjs":  "@nestjs/terminus — HealthController with TypeOrmHealthIndicator, MemoryHealthIndicator",
            "go":      "internal/common/health.go (http handlers)",
            "nodejs":  "src/common/health.js (Express handlers)",
        },
    },

    ("common", "rbac_contract"): {
        "scope": "cross-framework",
        "guidance": (
            "Role-based access control above plain authentication. Users carry "
            "one OR more roles (Role enum or role table). Routes declare required "
            "role/permission; framework guard enforces. Common roles: admin, "
            "owner, member, viewer. Permission strings: '{resource}:{action}' "
            "e.g. 'cart:write', 'invoice:read'. Service layer can re-check via "
            "actor.has_permission('cart:write')."
        ),
        "must_emit": [
            "Role enum / table with admin/owner/member/viewer (configurable)",
            "Permission table: role_name VARCHAR, permission VARCHAR (e.g. 'cart:write')",
            "Decorator/guard: @requires_permission('cart:write') for routes",
            "actor.has_permission(perm) -> bool — used by service for in-band checks",
        ],
        "anti_patterns": [
            "Never check roles by string comparison scattered across handlers — centralise in a guard/decorator",
            "Never let admin bypass audit logging — admins must audit MORE not less",
            "Never grant permissions by negation ('NOT admin') — explicit allow-lists only",
            "Never check authorization in the model layer — service or router only",
        ],
        "file_hint_per_framework": {
            "fastapi": "common/permissions.py (Depends-based guards + Role enum)",
            "django":  "DRF permission_classes — IsAuthenticated + custom HasRole permission",
            "spring":  "Spring Security @PreAuthorize(\"hasRole('ADMIN')\") on controller methods",
            "nestjs":  "RolesGuard + @Roles('admin') decorator (@nestjs/passport + custom)",
            "go":      "internal/common/permissions.go (middleware that reads claims)",
            "nodejs":  "src/common/permissions.js (Express middleware factory)",
        },
    },

    ("common", "api_versioning_contract"): {
        "scope": "cross-framework",
        "guidance": (
            "URL-path versioning (/api/v1, /api/v2). New version is a separate "
            "router/module that COEXISTS with the old; never break v1 once shipped. "
            "Deprecation: add Deprecation + Sunset headers to v1 responses 6 months "
            "before removal. Versioning applies at the routing layer, not the "
            "model/service layer — services are version-agnostic; routers translate. "
            "When introducing v2: copy v1's router file to v2/, change the import + "
            "schema imports, mount under /api/v2."
        ),
        "must_emit": [
            "Router prefix: /api/v{N}/{plural}",
            "Schema layout: {entity}/v1/schemas.py vs {entity}/v2/schemas.py (one per version)",
            "Service layer SHARED across versions — never duplicate business logic",
            "Deprecation response header on v1 once v2 ships: Deprecation: true; Sunset: <RFC1123 date>",
        ],
        "anti_patterns": [
            "Never use a single shared schema across versions — schema breaks are why you versioned",
            "Never put version logic inside the service — the service speaks the current canonical model only",
            "Never use query-param versioning (?version=2) — breaks caches and middlewares",
            "Never remove v1 routes without 6+ months of Sunset header + customer comms",
        ],
        "file_hint_per_framework": {
            "fastapi": "Mount routers: app.include_router(v1.router, prefix='/api/v1'); app.include_router(v2.router, prefix='/api/v2')",
            "django":  "urls.py: path('api/v1/', include('myapp.urls_v1')) and path('api/v2/', include('myapp.urls_v2'))",
            "spring":  "@RestController @RequestMapping(\"/api/v1/...\") + separate controller class per version",
            "nestjs":  "@Controller({ path: 'carts', version: '1' }) — use built-in URI versioning, enable in main.ts",
            "go":      "Separate sub-routers: v1 := router.PathPrefix(\"/api/v1\").Subrouter()",
            "nodejs":  "app.use('/api/v1', require('./v1/router')); app.use('/api/v2', require('./v2/router'))",
        },
    },

    ("common", "data_migration"): {
        "scope": "cross-framework",
        "guidance": (
            "Data migrations are DISTINCT from schema migrations. Schema migrations "
            "change DDL; data migrations rewrite rows under a new schema. Rules: "
            "(1) always reversible (provide downgrade), (2) batched (LIMIT N per "
            "iteration, never one big UPDATE on a hot table), (3) idempotent "
            "(safe to re-run if partially completed), (4) separate revision from "
            "the schema migration that adds the column being backfilled — deploy "
            "schema first, then data, so partial deploys don't break."
        ),
        "must_emit": [
            "Empty-then-fill pattern: (1) add column nullable in revision N, "
            "(2) backfill in revision N+1 (data migration), "
            "(3) add NOT NULL constraint in revision N+2",
            "Batch loop: WHILE rows_remaining: UPDATE ... LIMIT 1000; COMMIT; SLEEP 100ms",
            "Progress logging: every batch, log {processed, remaining, eta}",
        ],
        "anti_patterns": [
            "Never UPDATE without LIMIT on tables > 1M rows — locks + replication lag",
            "Never combine schema + data in one revision — partial deploy will leave you stranded",
            "Never write data migrations as raw SQL — use the ORM so testing + rollback work",
            "Never mark a data migration complete without a verification query (COUNT WHERE new_col IS NULL)",
        ],
        "file_hint_per_framework": {
            "fastapi": "Alembic data migration: op.execute() + Session via op.get_bind(); use chunked update",
            "django":  "RunPython operation: python manage.py makemigrations --empty appname",
            "spring":  "Flyway: V{N}__backfill_{description}.sql with batched DML; or Java migrations for ORM access",
            "nestjs":  "TypeORM: queryRunner-based migration with manual chunked update + commit per batch",
            "go":      "golang-migrate: separate .up.sql / .down.sql file; or programmatic via goose for ORM access",
            "nodejs":  "sequelize-cli: queryInterface.bulkUpdate in batches OR raw queryInterface.sequelize.query with LIMIT",
        },
    },

    # ─── Django ──────────────────────────────────────────────────────────
    ("django", "django_appconfig"): {
        "language": "python",
        "imports_must_include": ["from django.apps import AppConfig"],
        "class_decl": "class {Pascal}Config(AppConfig):",
        "must_emit": [
            "default_auto_field = 'django.db.models.BigAutoField'",
            "name = '{snake}'",
        ],
    },
    ("django", "django_model"): {
        "language": "python",
        "imports_must_include": ["from django.db import models"],
        "class_decl": "class {Pascal}(models.Model):",
        "must_have_fields": ["created_at = models.DateTimeField(auto_now_add=True)",
                              "updated_at = models.DateTimeField(auto_now=True)"],
        "must_include_fks_from_relationships": True,
        "must_have_meta": "Meta with verbose_name and verbose_name_plural",
        "must_have_str": "Use Django's __str__",
    },
    ("django", "drf_serializer"): {
        "language": "python",
        "imports_must_include": [
            "from rest_framework import serializers",
            "from .models import {Pascal}",
        ],
        "class_decl": "class {Pascal}Serializer(serializers.ModelSerializer):",
        "meta_must": ["model = {Pascal}", "fields = '__all__' or explicit list"],
    },
    ("django", "drf_viewset"): {
        "language": "python",
        "imports_must_include": [
            "from rest_framework import viewsets",
            "from .models import {Pascal}",
            "from .serializers import {Pascal}Serializer",
        ],
        "class_decl": "class {Pascal}ViewSet(viewsets.ModelViewSet):",
        "must_emit": ["queryset = {Pascal}.objects.all()", "serializer_class = {Pascal}Serializer"],
        "permission_classes_per_test_contract": True,
    },
    ("django", "django_urls"): {
        "language": "python",
        "imports_must_include": [
            "from rest_framework.routers import DefaultRouter",
            "from .views import {Pascal}ViewSet",
        ],
        "must_emit": [
            "router = DefaultRouter()",
            "router.register(r'', {Pascal}ViewSet)",
            "urlpatterns = router.urls",
        ],
    },
    ("django", "django_admin"): {
        "language": "python",
        "imports_must_include": ["from django.contrib import admin", "from .models import {Pascal}"],
        "must_emit": "admin.site.register({Pascal})",
    },
    ("django", "django_tests"): {
        "language": "python",
        "imports_must_include": [
            "from django.test import TestCase",
            "from rest_framework.test import APIClient",
            "from rest_framework import status",
            "from .models import {Pascal}",
        ],
        "must_test": ["list", "create", "retrieve", "update", "delete"],
        "test_contract_alignment": "Read spec.test_contract.auth",
    },
    ("django", "python_init"): {
        "language": "python",
        "guidance": "Empty file (Python package marker). For migrations/__init__.py, also leave empty.",
    },
    ("django", "django_service"): {
        "language": "python",
        "imports_must_include": [
            "from django.db import transaction",
            "from django.core.exceptions import ObjectDoesNotExist, PermissionDenied",
            "from .models import {Pascal}",
        ],
        "class_decl": "class {Pascal}Service:",
        "must_emit_methods": [
            "list(*, skip=0, limit=100) -> QuerySet",
            "get_or_404(item_id) -> {Pascal}",
            "create(payload, *, actor) -> {Pascal}  (wrap in transaction.atomic)",
            "update(item_id, payload, *, actor) -> {Pascal}",
            "delete(item_id, *, actor) -> None",
        ],
        "must_enforce_invariants_from_spec": True,
        "must_use_transactions": True,
        "must_emit_events_on_state_transitions": True,
        "anti_patterns": [
            "Don't put 401/403 HTTP exceptions here — that's the viewset/permission layer",
            "Don't import from views.py — service is the lower layer",
            "Don't call .save() without transaction.atomic() when multiple writes happen",
        ],
    },
    ("django", "django_auth"): {
        "language": "python",
        "imports_must_include": [
            "from django.contrib.auth.hashers import make_password, check_password",
            "from rest_framework_simplejwt.tokens import RefreshToken",
            "from django.utils import timezone",
            "from datetime import timedelta",
        ],
        "must_emit_helpers": [
            "hash_password(plain) -> str  (delegates to make_password — uses Django's PBKDF2 by default; configure bcrypt in settings.PASSWORD_HASHERS)",
            "verify_password(plain, hashed) -> bool  (delegates to check_password)",
            "issue_tokens_for(user) -> dict  (RefreshToken.for_user(user), returns {access, refresh})",
            "decode_access_token(token) -> dict",
            "verification_token_valid(token, *, max_age_hours=24) -> bool",
        ],
        "must_use_bcrypt_not_plain_hash": True,
        "must_schedule_email_via_background_task": True,
        "anti_patterns": [
            "Never store plain passwords — always go through make_password",
            "Never put SECRET_KEY or JWT signing keys in source — read from env / settings",
            "Never trust verification tokens older than 24h (1h for password reset)",
        ],
    },
    ("django", "soft_delete"): {
        "language": "python",
        "guidance": (
            "Custom Manager pattern. Add deleted_at DateTimeField(null=True, "
            "db_index=True). Override default Manager to filter deleted_at__isnull=True; "
            "expose .all_with_deleted() for admin. Override .delete() on QuerySet "
            "to UPDATE deleted_at instead of DELETE. Keep .hard_delete() for GDPR."
        ),
        "must_emit": [
            "deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)",
            "class {Pascal}Manager(models.Manager): get_queryset(self) returns super().get_queryset().filter(deleted_at__isnull=True)",
            "objects = {Pascal}Manager(); all_objects = models.Manager()",
            "soft_delete(self): self.deleted_at = timezone.now(); self.save(update_fields=['deleted_at'])",
        ],
        "anti_patterns": [
            "Don't forget UniqueConstraint(condition=Q(deleted_at__isnull=True))",
            "Don't let ON_DELETE=CASCADE cascade through soft-deleted rows — write a signal",
            "Don't soft-delete LogEntry / audit rows",
        ],
    },
    ("django", "file_upload"): {
        "language": "python",
        "imports_must_include": [
            "from rest_framework import status",
            "from rest_framework.decorators import action",
            "from rest_framework.parsers import MultiPartParser",
        ],
        "must_emit_endpoints": [
            "@action(detail=True, methods=['post'], parser_classes=[MultiPartParser]) def upload(...)",
        ],
        "guidance": (
            "FileField with upload_to= a path resolver that namespaces by entity "
            "type + UUID. Configure DEFAULT_FILE_STORAGE = "
            "'storages.backends.s3boto3.S3Boto3Storage' for S3. Validate "
            "content_type + size in serializer.validate_file(). Use "
            "django-storages package for cloud storage."
        ),
        "must_emit": [
            "file = models.FileField(upload_to=_upload_path)",
            "_upload_path(instance, filename) -> f'{type(instance).__name__.lower()}/{instance.id}/{uuid4()}'",
            "FILE_UPLOAD_MAX_MEMORY_SIZE in settings (forces streaming above this)",
            "Allowlist of content_types validated in serializer",
        ],
        "anti_patterns": [
            "Never use MEDIA_ROOT on disk in production — use S3/GCS via django-storages",
            "Never trust request.FILES['x'].content_type — sniff via python-magic",
            "Never accept files without a size cap (DATA_UPLOAD_MAX_MEMORY_SIZE)",
        ],
    },
    ("django", "django_background_task"): {
        "language": "python",
        "imports_must_include": [
            "from celery import shared_task",
        ],
        "guidance": (
            "Celery for retryable / scheduled work (detected via codebase_graph). "
            "Fall back to django-q or django-rq if those are present. Pass primary "
            "keys, not model instances, to avoid stale-state issues."
        ),
        "must_emit": [
            "@shared_task(bind=True, max_retries=3) on every task fn",
            "Task body looks up the row by id and re-checks invariants",
        ],
        "anti_patterns": [
            "Don't pass ORM model instances as task args — pass IDs",
            "Don't block on external IO in the request/response cycle — enqueue instead",
            "Don't forget idempotency — retried tasks must be safe",
        ],
    },

    # ─── Spring Boot ─────────────────────────────────────────────────────
    ("spring", "spring_entity"): {
        "language": "java",
        "imports_must_include": [
            "import jakarta.persistence.*;",
            "import java.time.Instant;",
        ],
        "annotations": ["@Entity", "@Table(name = \"{plural}\")"],
        "class_decl": "public class {Pascal} {",
        "must_have_fields": [
            "@Id @GeneratedValue private Long id;",
            "@Column(nullable = false) private Instant createdAt;",
            "@Column(nullable = false) private Instant updatedAt;",
        ],
        "must_include_fks_from_relationships": True,
        "use_jpa_annotations": True,
        "must_emit": "@PrePersist + @PreUpdate for timestamps; equals/hashCode by id",
    },
    ("spring", "spring_repository"): {
        "language": "java",
        "imports_must_include": [
            "import org.springframework.data.jpa.repository.JpaRepository;",
            "import org.springframework.stereotype.Repository;",
        ],
        "class_decl": "public interface {Pascal}Repository extends JpaRepository<{Pascal}, Long> {",
        "guidance": "Add custom finder methods derived from FK columns",
    },
    ("spring", "spring_service"): {
        "language": "java",
        "imports_must_include": [
            "import org.springframework.stereotype.Service;",
            "import org.springframework.transaction.annotation.Transactional;",
        ],
        "annotations": ["@Service", "@Transactional"],
        "must_emit_methods": ["list()", "findById(Long id)", "create({Pascal}Dto)", "update(Long id, {Pascal}Dto)", "delete(Long id)"],
        "guidance": "Throws ResponseStatusException(NOT_FOUND) on missing entities",
    },
    ("spring", "spring_controller"): {
        "language": "java",
        "imports_must_include": [
            "import org.springframework.web.bind.annotation.*;",
            "import org.springframework.http.ResponseEntity;",
        ],
        "annotations": ["@RestController", "@RequestMapping(\"/api/v1/{plural}\")"],
        "must_emit_endpoints": [
            "@GetMapping  list()",
            "@PostMapping  create(@RequestBody @Valid {Pascal}Dto)",
            "@GetMapping(\"/{{id}}\")  retrieve",
            "@PutMapping(\"/{{id}}\")  update",
            "@DeleteMapping(\"/{{id}}\")  delete (returns 204)",
        ],
        "auth_pattern": "@PreAuthorize per spec.test_contract.auth",
    },
    ("spring", "spring_dto"): {
        "language": "java",
        "imports_must_include": ["import jakarta.validation.constraints.*;", "import lombok.Data;"],
        "annotations": ["@Data"],
        "guidance": "Validation annotations (@NotNull, @Size) per attribute requirements",
    },
    ("spring", "spring_auth"): {
        "language": "java",
        "imports_must_include": [
            "import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;",
            "import org.springframework.stereotype.Service;",
            "import io.jsonwebtoken.Jwts;",
            "import io.jsonwebtoken.SignatureAlgorithm;",
            "import java.util.Date;",
        ],
        "annotations": ["@Service"],
        "class_decl": "public class AuthService {",
        "must_emit_methods": [
            "String hashPassword(String plain)  (delegates to BCryptPasswordEncoder.encode)",
            "boolean verifyPassword(String plain, String hashed)",
            "String issueAccessToken(Long subjectId, long expiresInMinutes)",
            "Claims decodeAccessToken(String token)",
            "boolean verificationTokenValid(String token, int maxAgeHours)",
        ],
        "must_use_bcrypt_not_plain_hash": True,
        "must_schedule_email_via_background_task": True,
        "must_read_secret_from_env": True,
        "anti_patterns": [
            "Never store plain passwords — always BCryptPasswordEncoder",
            "Never put JWT secret in source — read from @Value(\"${jwt.secret}\") / env",
            "Never accept verification tokens older than 24h",
        ],
    },
    ("spring", "soft_delete"): {
        "language": "java",
        "guidance": (
            "Hibernate @SQLDelete + @Where annotations. @SQLDelete rewrites "
            "DELETE statements to UPDATE deletedAt = now(). @Where("
            "clause = \"deleted_at IS NULL\") filters every read. Keep a "
            "@Repository method named hardDelete(id) that uses native query "
            "for GDPR / admin cleanup."
        ),
        "imports_must_include": [
            "import org.hibernate.annotations.SQLDelete;",
            "import org.hibernate.annotations.Where;",
            "import java.time.Instant;",
        ],
        "must_emit": [
            "@SQLDelete(sql = \"UPDATE {plural} SET deleted_at = NOW() WHERE id = ?\")",
            "@Where(clause = \"deleted_at IS NULL\")",
            "@Column(name = \"deleted_at\") private Instant deletedAt;  // nullable",
            "Repository: @Modifying @Query(value = \"DELETE FROM {plural} WHERE id = :id\", nativeQuery = true) void hardDelete(@Param(\"id\") Long id);",
        ],
        "anti_patterns": [
            "Don't index deleted_at without a partial index — many rows will be NULL",
            "Don't @Where on JpaRepository.findAll() — you may want all rows for admin; expose a separate method",
            "Don't soft-delete entities referenced by hard FKs without ON DELETE handling",
            "Don't expect unique constraints to ignore soft-deleted rows — they still occupy the value; use a partial unique index (Postgres) or composite (deleted_at, value)",
            "Don't soft-delete audit_log entries — audit must remain append-only",
        ],
    },
    ("spring", "file_upload"): {
        "language": "java",
        "imports_must_include": [
            "import org.springframework.web.multipart.MultipartFile;",
            "import org.springframework.web.bind.annotation.PostMapping;",
            "import org.springframework.web.bind.annotation.RequestParam;",
        ],
        "must_emit_endpoints": [
            "@PostMapping(value = \"/{{id}}/upload\", consumes = \"multipart/form-data\") public ResponseEntity<?> upload(@PathVariable Long id, @RequestParam(\"file\") MultipartFile file)",
        ],
        "guidance": (
            "Validate file.getSize() against spring.servlet.multipart.max-file-size. "
            "Validate file.getContentType() against allowlist. Stream to S3 via "
            "AWS SDK v2 TransferManager or to local disk via Files.copy(); never "
            "load full byte[] into memory for files > 10 MB. Store metadata (key, "
            "size, sha256, content_type) in DB; bytes in object storage."
        ),
        "must_emit": [
            "spring.servlet.multipart.max-file-size in application.properties",
            "ALLOWED_CONTENT_TYPES Set<String> constant",
            "Chunked SHA-256 of input stream during streaming",
            "S3 presigned URL helper for direct client upload (preferred over proxying)",
        ],
        "anti_patterns": [
            "Don't call file.getBytes() — loads entire file into memory",
            "Don't trust file.getContentType() — clients lie; sniff first bytes",
            "Don't save with original filename as key — generate UUID",
        ],
    },
    ("spring", "spring_background"): {
        "language": "java",
        "imports_must_include": [
            "import org.springframework.scheduling.annotation.Async;",
            "import org.springframework.scheduling.annotation.Scheduled;",
            "import org.springframework.stereotype.Component;",
        ],
        "annotations": ["@Component"],
        "guidance": (
            "Use @Async for fire-and-forget work (requires @EnableAsync on a "
            "@Configuration class). Use @Scheduled(cron=...) or fixedDelay for "
            "recurring tasks. For retryable work with persistence, prefer Spring "
            "Batch or an external broker (RabbitMQ / Kafka). Pass IDs, not entities."
        ),
        "must_emit": [
            "@Async-annotated method returning CompletableFuture<Void> or void",
            "@Scheduled(cron = \"0 0 * * * ?\") on scheduled methods",
        ],
        "anti_patterns": [
            "Don't @Async a method that returns Future<T> and never get() it — exceptions are swallowed",
            "Don't block on external IO inside the controller — delegate to @Async",
            "Don't pass JPA entities to @Async — they may be detached; pass IDs",
        ],
    },
    ("spring", "spring_test"): {
        "language": "java",
        "imports_must_include": [
            "import org.springframework.boot.test.context.SpringBootTest;",
            "import org.springframework.test.web.servlet.MockMvc;",
            "import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;",
            "import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;",
        ],
        "annotations": ["@SpringBootTest", "@AutoConfigureMockMvc"],
        "must_test": ["list", "create", "retrieve", "update", "delete"],
    },

    # ─── Go ──────────────────────────────────────────────────────────────
    ("go", "go_model"): {
        "language": "go",
        "package_decl": "package {snake}",
        "must_emit_struct": "type {Pascal} struct with fields including ID, CreatedAt, UpdatedAt",
        "must_use_gorm_tags": "`gorm:\"primaryKey\"` etc. when project uses GORM",
        "fks_as_struct_fields": "Add `{Pascal}ID uint` AND `{Pascal} {Pascal}` (struct reference)",
    },
    ("go", "go_repository"): {
        "language": "go",
        "package_decl": "package {snake}",
        "must_emit": "type Repository interface { List, Get, Create, Update, Delete }",
        "guidance": "Return (entity, error) pairs idiomatically; use context.Context",
    },
    ("go", "go_handler"): {
        "language": "go",
        "package_decl": "package {snake}",
        "must_emit_handlers": ["List", "Get", "Create", "Update", "Delete"],
        "framework_check": "Detect Gin / Echo / chi from codebase_graph; match the project's choice",
        "must_return_json": "Use c.JSON(http.StatusOK, ...) or equivalent",
    },
    ("go", "go_service"): {
        "language": "go",
        "package_decl": "package {snake}",
        "imports_must_include": ["context", "errors"],
        "must_emit": (
            "type Service struct { repo Repository } with NewService(repo Repository) *Service. "
            "Methods: List(ctx context.Context, skip, limit int) ([]{Pascal}, error); "
            "GetOrNotFound(ctx, id) ({Pascal}, error); Create(ctx, payload, actorID) ({Pascal}, error); "
            "Update(ctx, id, payload, actorID) ({Pascal}, error); Delete(ctx, id, actorID) error"
        ),
        "must_enforce_invariants_from_spec": True,
        "must_use_transactions": True,
        "must_emit_events_on_state_transitions": True,
        "anti_patterns": [
            "Don't return *gorm.DB or *sql.Rows from a service method — wrap in domain types",
            "Don't return HTTP error codes from service — return sentinel errors (ErrNotFound) and let the handler translate",
            "Don't ignore context cancellation — always pass ctx through to repo calls",
        ],
    },
    ("go", "go_dto"): {
        "language": "go",
        "package_decl": "package {snake}",
        "must_emit_struct": (
            "type Create{Pascal}Request struct with json tags + validate tags "
            "(go-playground/validator). type Update{Pascal}Request with optional fields "
            "(use pointers for nullable). type {Pascal}Response with id + created_at + updated_at."
        ),
        "guidance": (
            "Keep DTOs in their own file (dto.go). Validate input with "
            "github.com/go-playground/validator/v10 on the request side; never trust "
            "raw JSON bodies. Response structs decouple wire-format from internal model."
        ),
        "anti_patterns": [
            "Don't expose internal model fields as JSON (e.g. internal flags, soft-delete cols)",
            "Don't reuse one struct for create + update + response — semantics differ (required vs optional)",
        ],
    },
    ("go", "go_auth"): {
        "language": "go",
        "package_decl": "package auth",
        "imports_must_include": [
            "golang.org/x/crypto/bcrypt",
            "github.com/golang-jwt/jwt/v5",
            "time",
            "os",
        ],
        "must_emit": (
            "HashPassword(plain string) (string, error)  (bcrypt.GenerateFromPassword, cost ≥ 12); "
            "VerifyPassword(plain, hashed string) bool  (bcrypt.CompareHashAndPassword); "
            "IssueAccessToken(subjectID uint, expiresIn time.Duration) (string, error); "
            "DecodeAccessToken(token string) (jwt.MapClaims, error); "
            "VerificationTokenValid(token string, maxAge time.Duration) bool"
        ),
        "must_use_bcrypt_not_plain_hash": True,
        "must_schedule_email_via_background_task": True,
        "anti_patterns": [
            "Never store plain passwords",
            "Never hard-code the JWT secret — os.Getenv(\"JWT_SECRET\")",
            "Never accept verification tokens older than 24h (1h for password reset)",
        ],
    },
    ("go", "soft_delete"): {
        "language": "go",
        "guidance": (
            "GORM ships gorm.DeletedAt support out of the box. Embed gorm.Model "
            "OR add `DeletedAt gorm.DeletedAt `gorm:\"index\"``. db.Delete(&row) "
            "becomes an UPDATE deletedAt = now(). db.Unscoped().Delete() does a "
            "real DELETE. For non-GORM projects: write a deletedAt *time.Time "
            "column + custom repository methods that add WHERE deleted_at IS NULL."
        ),
        "imports_must_include": [
            "gorm.io/gorm",
        ],
        "must_emit": [
            "DeletedAt gorm.DeletedAt `gorm:\"index\"`  (or embed gorm.Model)",
            "Repository.SoftDelete(ctx, id) — db.WithContext(ctx).Delete(&{Pascal}{ID: id})",
            "Repository.HardDelete(ctx, id) — db.WithContext(ctx).Unscoped().Delete(...)",
            "Repository.Restore(ctx, id) — db.Unscoped().Model(...).Update(\"deleted_at\", nil)",
        ],
        "anti_patterns": [
            "Don't forget the `gorm:\"index\"` tag — soft-delete filters scan otherwise",
            "Don't use UNIQUE without partial index — soft-deleted rows still hold the value",
            "Don't expose Unscoped operations to non-admin handlers",
        ],
    },
    ("go", "file_upload"): {
        "language": "go",
        "imports_must_include": [
            "net/http",
            "io",
            "crypto/sha256",
            "github.com/google/uuid",
        ],
        "must_emit": (
            "POST /{plural}/{id}/upload handler: r.ParseMultipartForm(maxMemory); "
            "file, header, err := r.FormFile(\"file\"); defer file.Close(); validate "
            "header.Size <= MAX_FILE_BYTES; validate header.Header.Get(\"Content-Type\") "
            "in allowlist; stream to S3 via aws-sdk-go-v2 manager.NewUploader; store "
            "metadata (key, size, sha256, content_type) in DB."
        ),
        "guidance": (
            "Use io.LimitReader to enforce size cap mid-stream. Use multipart.Reader "
            "(not ParseMultipartForm) for very large files to avoid memory pressure. "
            "Prefer direct-to-S3 via presigned PUT URLs over proxying."
        ),
        "anti_patterns": [
            "Don't use ParseMultipartForm without a maxMemory arg — defaults to 32 MB in RAM",
            "Don't trust header.Header.Get(\"Content-Type\") — sniff first 512 bytes via http.DetectContentType",
            "Don't use header.Filename as the storage key — generate uuid.New().String()",
        ],
    },
    ("go", "go_background"): {
        "language": "go",
        "package_decl": "package {snake}",
        "imports_must_include": ["context", "sync", "log"],
        "guidance": (
            "For fire-and-forget: spawn a goroutine with a derived ctx + recover(). "
            "For retryable/scheduled: detect github.com/hibiken/asynq or "
            "github.com/robfig/cron in go.mod and use that. Otherwise emit a simple "
            "worker-pool pattern with a buffered chan. Always pass IDs, not pointers to mutable state."
        ),
        "must_emit": [
            "Worker function signature: func(ctx context.Context, jobID uint) error",
            "defer recover() in every goroutine spawned from a request handler",
        ],
        "anti_patterns": [
            "Don't go func() { ... }() without recover() — a panic crashes the whole process",
            "Don't share request ctx with a long-running goroutine — derive a new one with context.WithoutCancel or context.Background",
            "Don't pass model pointers to a worker — they may be mutated; pass IDs",
        ],
    },
    ("go", "go_test"): {
        "language": "go",
        "package_decl": "package {snake}_test",
        "imports_must_include": ["testing", "net/http/httptest"],
        "must_use_table_driven_tests": True,
        "must_test": ["list", "create", "retrieve", "update", "delete"],
    },

    # ─── NestJS ──────────────────────────────────────────────────────────
    ("nestjs", "nestjs_module"): {
        "language": "typescript",
        "imports_must_include": [
            "import { Module } from '@nestjs/common';",
            "import { TypeOrmModule } from '@nestjs/typeorm';",
        ],
        "class_decl": "export class {Pascal}Module {",
        "decorator": "@Module({{ imports: [TypeOrmModule.forFeature([{Pascal}])], controllers: [{Pascal}Controller], providers: [{Pascal}Service] }})",
    },
    ("nestjs", "nestjs_controller"): {
        "language": "typescript",
        "imports_must_include": [
            "import { Controller, Get, Post, Put, Delete, Param, Body, HttpCode } from '@nestjs/common';",
        ],
        "decorators": ["@Controller('{kebab}')"],
        "must_emit_endpoints": ["@Get()", "@Post()", "@Get(':id')", "@Put(':id')", "@Delete(':id') @HttpCode(204)"],
    },
    ("nestjs", "nestjs_service"): {
        "language": "typescript",
        "imports_must_include": [
            "import { Injectable, NotFoundException } from '@nestjs/common';",
            "import { InjectRepository } from '@nestjs/typeorm';",
            "import { Repository } from 'typeorm';",
        ],
        "decorators": ["@Injectable()"],
        "must_emit_methods": ["findAll", "findOne", "create", "update", "remove"],
    },
    ("nestjs", "nestjs_dto"): {
        "language": "typescript",
        "imports_must_include": ["import { IsNotEmpty, IsString, IsNumber, IsOptional } from 'class-validator';"],
        "guidance": "Use class-validator decorators per attribute. Create DTO = all required; Update DTO = all optional (PartialType).",
    },
    ("nestjs", "nestjs_entity"): {
        "language": "typescript",
        "imports_must_include": [
            "import { Entity, Column, PrimaryGeneratedColumn, CreateDateColumn, UpdateDateColumn } from 'typeorm';",
        ],
        "decorators": ["@Entity('{plural}')"],
        "must_have_columns": ["@PrimaryGeneratedColumn() id: number;",
                              "@CreateDateColumn() createdAt: Date;",
                              "@UpdateDateColumn() updatedAt: Date;"],
        "must_include_fks_from_relationships": True,
    },
    ("nestjs", "nestjs_auth"): {
        "language": "typescript",
        "imports_must_include": [
            "import { Injectable, UnauthorizedException } from '@nestjs/common';",
            "import { JwtService } from '@nestjs/jwt';",
            "import * as bcrypt from 'bcrypt';",
        ],
        "decorators": ["@Injectable()"],
        "class_decl": "export class AuthService {",
        "must_emit_methods": [
            "hashPassword(plain: string): Promise<string>  (bcrypt.hash, cost ≥ 12)",
            "verifyPassword(plain: string, hashed: string): Promise<boolean>  (bcrypt.compare)",
            "issueAccessToken(subjectId: number, expiresIn: string = '60m'): string",
            "decodeAccessToken(token: string): any",
            "verificationTokenValid(token: string, maxAgeHours: number = 24): boolean",
        ],
        "must_use_bcrypt_not_plain_hash": True,
        "must_schedule_email_via_background_task": True,
        "anti_patterns": [
            "Never store plain passwords",
            "Never put JWT secret in source — read from ConfigService / process.env",
            "Never accept verification tokens older than 24h (1h for password reset)",
            "Don't use synchronous bcrypt.hashSync in a request handler — blocks event loop",
        ],
    },
    ("nestjs", "soft_delete"): {
        "language": "typescript",
        "guidance": (
            "TypeORM built-in @DeleteDateColumn. Repository.softDelete(id) issues "
            "UPDATE deletedAt = NOW(). Repository.restore(id) clears it. Default "
            "find() excludes soft-deleted; pass { withDeleted: true } to include. "
            "Service exposes both softDelete() and a separate hardDelete() for "
            "GDPR / admin paths."
        ),
        "imports_must_include": [
            "import { DeleteDateColumn, Repository } from 'typeorm';",
        ],
        "must_emit": [
            "@DeleteDateColumn() deletedAt?: Date;",
            "service.softDelete(id): await repo.softDelete(id)",
            "service.restore(id): await repo.restore(id)",
            "service.hardDelete(id, *, actor): admin-only; await repo.delete(id)",
        ],
        "anti_patterns": [
            "Don't forget unique constraints with @Index({ unique: true, where: 'deletedAt IS NULL' })",
            "Don't return restore() / hardDelete() to non-admin actors",
            "Don't soft-delete audit_log entries — audit must be append-only",
        ],
    },
    ("nestjs", "file_upload"): {
        "language": "typescript",
        "imports_must_include": [
            "import { Post, Param, UploadedFile, UseInterceptors, BadRequestException } from '@nestjs/common';",
            "import { FileInterceptor } from '@nestjs/platform-express';",
        ],
        "decorators": [
            "@Post(':id/upload')",
            "@UseInterceptors(FileInterceptor('file', { limits: { fileSize: MAX_FILE_BYTES }, fileFilter: contentTypeFilter }))",
        ],
        "guidance": (
            "Multer via @nestjs/platform-express. Configure { limits, fileFilter, "
            "storage } at the interceptor level. For S3: use multer-s3 OR upload "
            "the buffer via aws-sdk v3 PutObjectCommand. For direct-to-S3: return "
            "a presigned PUT URL from a separate endpoint."
        ),
        "must_emit": [
            "MAX_FILE_BYTES constant (from ConfigService)",
            "ALLOWED_CONTENT_TYPES Set<string> + contentTypeFilter function",
            "Helper: getPresignedPutUrl(key, contentType, expiresIn = 900): Promise<string>",
        ],
        "anti_patterns": [
            "Don't use multer's default disk storage in production — use multer-s3 or stream",
            "Don't trust file.mimetype — clients can lie; sniff via file-type package",
            "Don't await an unbounded buffer — enforce limits at the interceptor",
        ],
    },
    ("nestjs", "nestjs_background"): {
        "language": "typescript",
        "imports_must_include": [
            "import { Processor, Process, InjectQueue } from '@nestjs/bull';",
            "import { Queue, Job } from 'bull';",
        ],
        "decorators": ["@Processor('{snake}')"],
        "guidance": (
            "BullMQ for retryable / scheduled work (detected via codebase_graph / "
            "package.json — checks @nestjs/bull or bullmq). If not present, fall "
            "back to @nestjs/schedule (@Cron). Pass IDs, not entities."
        ),
        "must_emit": [
            "@Processor('queue-name') class with @Process('job-type') handlers",
            "Job retry policy: { attempts: 3, backoff: { type: 'exponential', delay: 1000 } }",
        ],
        "anti_patterns": [
            "Don't block the request handler on external IO — enqueue a job",
            "Don't store sensitive data in job payload — store IDs and look up",
            "Don't forget idempotency — retried jobs must be safe",
        ],
    },
    ("nestjs", "nestjs_spec"): {
        "language": "typescript",
        "imports_must_include": [
            "import { Test, TestingModule } from '@nestjs/testing';",
        ],
        "must_test": ["controller defined", "all 5 endpoints exist", "service is injected"],
    },

    # ─── Node.js (Express + Sequelize) ────────────────────────────────────
    ("nodejs", "nodejs_init"): {
        "language": "javascript",
        "guidance": (
            "Module entrypoint that re-exports the router. Convention: "
            "`module.exports = require('./router');` so app.js can do "
            "`app.use('/api/v1/{plural}', require('./{snake}'))`."
        ),
    },
    ("nodejs", "nodejs_model"): {
        "language": "javascript",
        "imports_must_include": [
            "const { DataTypes, Model } = require('sequelize');",
            "const sequelize = require('../db');",
        ],
        "must_emit": (
            "class {Pascal} extends Model {} with {Pascal}.init({...}, {{ sequelize, modelName: '{Pascal}', tableName: '{plural}', timestamps: true }})"
        ),
        "must_have_columns": [
            "id: { type: DataTypes.INTEGER, primaryKey: true, autoIncrement: true }",
            "createdAt / updatedAt (timestamps: true)",
        ],
        "must_include_fks_from_relationships": True,
        "guidance": (
            "Sequelize for SQL-backed projects. Detect Mongoose via codebase_graph "
            "and switch the imports + schema syntax accordingly. Use class-based "
            "models so business helpers (instance methods) live with the model."
        ),
        "anti_patterns": [
            "Don't define associations inside the model file — do it in models/index.js after all models load",
            "Don't store secrets in model defaults",
        ],
    },
    ("nodejs", "nodejs_schema"): {
        "language": "javascript",
        "imports_must_include": [
            "const Joi = require('joi');",
        ],
        "must_emit": (
            "create{Pascal}Schema (all required attrs); update{Pascal}Schema "
            "(all optional, PATCH semantics); {snake}IdParamSchema (id: number positive). "
            "Each schema exported individually for router middleware use."
        ),
        "guidance": (
            "Joi for runtime validation. Switch to Zod or class-validator if "
            "detected in package.json. Validate BEFORE the request hits the service "
            "layer — fail fast at the boundary."
        ),
        "anti_patterns": [
            "Don't reuse one schema for create + update — semantics differ",
            "Don't validate inside the service — service should trust validated input",
        ],
    },
    ("nodejs", "nodejs_service"): {
        "language": "javascript",
        "imports_must_include": [
            "const { {Pascal} } = require('./model');",
            "const { NotFoundError, ValidationError } = require('../common/errors');",
            "const { emit } = require('../common/events');",
        ],
        "class_decl": "class {Pascal}Service {",
        "must_emit_methods": [
            "constructor({ db })  (dependency injection)",
            "async list({ skip = 0, limit = 100 })",
            "async getOrNotFound(id)",
            "async create(payload, { actorId })",
            "async update(id, payload, { actorId })",
            "async delete(id, { actorId })",
        ],
        "must_enforce_invariants_from_spec": True,
        "must_use_transactions": True,
        "must_emit_events_on_state_transitions": True,
        "anti_patterns": [
            "Don't throw HTTP-aware errors here (res.status(404)) — throw domain errors; the router translates",
            "Don't import from router.js — service is the lower layer",
            "Don't write raw SQL — use the ORM session (sequelize.transaction)",
        ],
    },
    ("nodejs", "nodejs_router"): {
        "language": "javascript",
        "imports_must_include": [
            "const express = require('express');",
            "const router = express.Router();",
            "const service = require('./service');",
            "const { validate } = require('../common/validate');",
            "const { create{Pascal}Schema, update{Pascal}Schema } = require('./schema');",
        ],
        "must_emit_endpoints": [
            "GET '/'  (list, 200)",
            "POST '/' validate(create{Pascal}Schema)  (create, 201)",
            "GET '/:id'  (retrieve, 404 if missing)",
            "PUT '/:id' validate(update{Pascal}Schema)  (update, 404 if missing)",
            "DELETE '/:id'  (delete, 204, 404 if missing)",
        ],
        "auth_pattern": (
            "Apply `requireAuth` middleware per spec.test_contract.auth ('none' → no middleware)"
        ),
        "must_use_async_error_wrapper": True,
        "anti_patterns": [
            "Don't write `try/catch` in every handler — wrap with asyncHandler / express-async-errors",
            "Don't return raw ORM instances — call .toJSON() or use a response mapper",
            "Don't generate 401 logic if test_contract.auth === 'none'",
        ],
    },
    ("nodejs", "nodejs_auth"): {
        "language": "javascript",
        "imports_must_include": [
            "const bcrypt = require('bcrypt');",
            "const jwt = require('jsonwebtoken');",
        ],
        "must_emit_helpers": [
            "hashPassword(plain) -> Promise<string>  (bcrypt.hash, cost ≥ 12)",
            "verifyPassword(plain, hashed) -> Promise<boolean>  (bcrypt.compare)",
            "issueAccessToken(subjectId, expiresIn = '60m') -> string  (jwt.sign with process.env.JWT_SECRET)",
            "decodeAccessToken(token) -> object  (jwt.verify)",
            "verificationTokenValid(token, maxAgeHours = 24) -> boolean",
            "requireAuth(req, res, next) — Express middleware that reads Authorization header",
        ],
        "must_use_bcrypt_not_plain_hash": True,
        "must_schedule_email_via_background_task": True,
        "anti_patterns": [
            "Never store plain passwords",
            "Never hard-code the JWT secret — process.env.JWT_SECRET",
            "Never use bcrypt.hashSync in a request handler — blocks the event loop",
            "Never accept verification tokens older than 24h (1h for password reset)",
        ],
    },
    ("nodejs", "nodejs_background"): {
        "language": "javascript",
        "imports_must_include": [
            "const { Queue, Worker } = require('bullmq');",
        ],
        "guidance": (
            "BullMQ for retryable / scheduled work (detected via package.json: "
            "bullmq, bull, agenda, or node-cron). Fall back to setImmediate / "
            "process.nextTick only for trivial fire-and-forget. Pass IDs, not "
            "model instances. Always set { attempts, backoff } on retryable jobs."
        ),
        "must_emit": [
            "Queue declaration: const queue = new Queue('{snake}', { connection: { ... } })",
            "Worker with retry policy: { attempts: 3, backoff: { type: 'exponential', delay: 1000 } }",
            "Worker handler signature: async (job) => { const { id } = job.data; ... }",
        ],
        "anti_patterns": [
            "Don't block the request handler on external IO — enqueue a job",
            "Don't pass model instances as job data — pass IDs",
            "Don't forget idempotency — retried jobs must be safe",
            "Don't share a Redis connection across Queue and Worker without { connection } config — leads to leaks",
        ],
    },
    ("nodejs", "soft_delete"): {
        "language": "javascript",
        "guidance": (
            "Sequelize supports `paranoid: true` on the model definition. This adds "
            "a deletedAt timestamp column and changes destroy() to set the column "
            "instead of DELETEing. force: true restores normal DELETE. include "
            "`paranoid: false` in find options to include soft-deleted rows. For "
            "Mongoose: use mongoose-delete plugin or implement deletedAt + a query "
            "middleware."
        ),
        "must_emit": [
            "Model.init({...}, { sequelize, paranoid: true, timestamps: true })",
            "service.softDelete(id): await {Pascal}.destroy({ where: { id } })",
            "service.hardDelete(id, { actor }): admin-only; await {Pascal}.destroy({ where: { id }, force: true })",
            "service.restore(id): await {Pascal}.restore({ where: { id } })",
        ],
        "anti_patterns": [
            "Don't forget partial UNIQUE constraints — Sequelize 'unique' indexes still trip on soft-deleted rows on most engines",
            "Don't expose .restore / hardDelete via the public API",
            "Don't soft-delete audit rows",
        ],
    },
    ("nodejs", "file_upload"): {
        "language": "javascript",
        "imports_must_include": [
            "const multer = require('multer');",
            "const crypto = require('crypto');",
        ],
        "must_emit_endpoints": [
            "POST /{plural}/:id/upload  (multer.single('file') middleware)",
        ],
        "guidance": (
            "Multer for multipart parsing. For S3: multer-s3 OR aws-sdk v3 "
            "PutObjectCommand on the buffer. Configure { limits: { fileSize }, "
            "fileFilter } per route. Compute SHA-256 of the buffer / stream during "
            "upload. Prefer presigned PUT URLs for files > 5 MB so the API server "
            "doesn't proxy bytes."
        ),
        "must_emit": [
            "MAX_FILE_BYTES from process.env.MAX_FILE_BYTES",
            "ALLOWED_CONTENT_TYPES Set + fileFilter(req, file, cb) function",
            "Helper: getPresignedPutUrl(key, contentType, expiresIn = 900) -> string",
            "Storage key generator: `${entityType}/${entityId}/${crypto.randomUUID()}`",
        ],
        "anti_patterns": [
            "Never use multer.diskStorage in production — files vanish on container restart",
            "Never trust file.mimetype — clients lie; sniff via file-type npm package",
            "Never await large upload buffers without limits.fileSize — DoS",
            "Never use file.originalname as the storage key — generate UUID",
        ],
    },
    ("nodejs", "nodejs_test"): {
        "language": "javascript",
        "imports_must_include": [
            "const request = require('supertest');",
            "const app = require('../../app');",
        ],
        "test_framework": "jest (or mocha+chai if detected in package.json)",
        "must_test": [
            "list returns 200 + array shape",
            "create round-trip (POST → 201, retrieve confirms)",
            "retrieve missing returns 404",
            "update applies partial fields",
            "delete returns 204 then retrieve returns 404",
        ],
        "test_contract_alignment": "Read spec.test_contract — DO NOT assert 401 if auth === 'none'",
        "anti_patterns": [
            "Don't hit a real database — use an in-memory SQLite or a per-test transaction rollback",
            "Don't assume auth middleware unless test_contract.auth !== 'none'",
        ],
    },
}


def get(framework: str, kind: str) -> Optional[Dict]:
    return HINTS.get((framework, kind))


def list_all() -> List[Dict[str, str]]:
    return [{"framework": fw, "kind": k} for (fw, k) in sorted(HINTS.keys())]


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Return idiomatic-code hints for a (framework, file_kind) pair"
    )
    parser.add_argument("--framework", choices=["fastapi", "django", "spring", "go", "nestjs", "nodejs", "common"],
                        help="'common' for cross-cutting hints (events_emitter, domain_exceptions)")
    parser.add_argument("--kind", help="File kind from scaffold_planner")
    parser.add_argument("--list", action="store_true", help="List all available (framework, kind) pairs")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.list:
        data = list_all()
        if args.json:
            print(json.dumps(data, indent=2))
        else:
            for entry in data:
                print(f"  {entry['framework']:<10} {entry['kind']}")
        return

    if not (args.framework and args.kind):
        parser.error("--framework and --kind are required (or use --list)")
    hint = get(args.framework, args.kind)
    if hint is None:
        print(f"No hint for ({args.framework}, {args.kind})", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(hint, indent=2))


if __name__ == "__main__":
    main()
