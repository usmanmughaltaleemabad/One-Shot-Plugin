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
    ("nestjs", "nestjs_spec"): {
        "language": "typescript",
        "imports_must_include": [
            "import { Test, TestingModule } from '@nestjs/testing';",
        ],
        "must_test": ["controller defined", "all 5 endpoints exist", "service is injected"],
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
    parser.add_argument("--framework", choices=["fastapi", "django", "spring", "go", "nestjs", "common"],
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
