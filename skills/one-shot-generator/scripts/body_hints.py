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
