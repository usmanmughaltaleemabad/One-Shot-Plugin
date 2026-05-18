#!/usr/bin/env python3
"""
Scaffold Planner — v1.0.0  (Tier 3.5 — replaces spec_driven_generator's
template-body emission)

Pure structural plumbing: given a ``spec.json``, decide WHICH files need
to exist, WHAT path each one lives at, and WHAT skeleton context the
implementer agents need to fill in the body. **No code-content
generation here.** Claude (the implementer agents) fills in the bodies.

Outputs a plan document the SKILL.md (and ``one_shot_orchestrator.py``
in headless mode) hands to the implementer agents:

    {
        "feature": "shopping cart with line items",
        "files_to_create": [
            {
                "path": "cart/models.py",
                "kind": "sqlalchemy_model",
                "entity": "ShoppingCart",
                "fk_columns": [],
                "base_module": "models",
                "base_name": "Base",
                "attribute_names": ["status", "total", ...]
            },
            {
                "path": "line_item/models.py",
                "kind": "sqlalchemy_model",
                "entity": "LineItem",
                "fk_columns": [{"col": "shopping_cart_id",
                                  "references": "shopping_carts.id"}],
                ...
            },
            ...
        ],
        "stubs_needed": [],   # e.g. ["database.py"] if project has no get_db
        "wiring_targets": ["main.py"],
        "migrations": ["alembic_revision"]
    }

This module is the structural skeleton planner. The Tier-2.5
``spec_driven_generator.py`` is kept as the headless/templated fallback
(it still has the f-string bodies); ``scaffold_planner.py`` is what the
agentic pipeline uses.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from lib.base_script import bootstrap_runtime, setup_logging
bootstrap_runtime()

logger = setup_logging(__name__)


# ─── Data shapes ─────────────────────────────────────────────────────────────

@dataclass
class FileSpec:
    path: str
    kind: str               # sqlalchemy_model | pydantic_schema | fastapi_router | pytest_module | python_init
    entity: Optional[str] = None
    fk_columns: List[Dict[str, str]] = field(default_factory=list)
    base_module: Optional[str] = None
    base_name: Optional[str] = None
    db_module: Optional[str] = None
    db_func: Optional[str] = None
    attribute_names: List[str] = field(default_factory=list)
    test_contract: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ScaffoldPlan:
    feature: str
    framework: str
    files_to_create: List[FileSpec] = field(default_factory=list)
    stubs_needed: List[str] = field(default_factory=list)
    wiring_targets: List[str] = field(default_factory=list)
    migrations: List[str] = field(default_factory=list)
    relationships: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "feature": self.feature,
            "framework": self.framework,
            "files_to_create": [f.to_dict() for f in self.files_to_create],
            "stubs_needed": self.stubs_needed,
            "wiring_targets": self.wiring_targets,
            "migrations": self.migrations,
            "relationships": self.relationships,
        }


# ─── FK derivation ───────────────────────────────────────────────────────────

def _fks_for_entity(snake_name: str,
                    relationships: List[Dict]) -> List[Dict[str, str]]:
    """Return list of {col, references} dicts for FKs into this entity."""
    out: List[Dict[str, str]] = []
    for rel in relationships:
        kind = rel.get("kind", "has_many")
        from_ent = rel.get("from") or rel.get("from_entity")
        to_ent = rel.get("to") or rel.get("to_entity")
        if not (from_ent and to_ent):
            continue
        # has_many on parent → child carries the FK
        if kind == "has_many" and to_ent == snake_name:
            out.append({"col": f"{from_ent}_id",
                        "references": f"{from_ent}s.id"})
        elif kind == "belongs_to" and from_ent == snake_name:
            out.append({"col": f"{to_ent}_id",
                        "references": f"{to_ent}s.id"})
    return out


def _attribute_names_for(spec: Dict, snake_name: str,
                          fk_cols: List[Dict[str, str]]) -> List[str]:
    """Names to expose as schema fields (FKs first, then declared attrs).

    Filters out attributes that duplicate FK columns AND the always-present
    `id`/`created_at`/`updated_at` (those are emitted by the implementer
    template knowledge, not the spec).
    """
    fk_col_names = {fk["col"] for fk in fk_cols}
    fk_roots = set()
    for fk in fk_cols:
        ref_root = fk["references"].split(".")[0].rstrip("s")
        fk_roots.add(ref_root)
        for tail in ref_root.split("_"):
            fk_roots.add(tail)
    names = [fk["col"] for fk in fk_cols]
    for ent in spec.get("entities", []):
        if ent.get("snake_name") != snake_name and ent.get("name").lower() != snake_name:
            continue
        for attr in ent.get("attributes", []):
            n = attr.get("name")
            if not n or n in ("id", "created_at", "updated_at"):
                continue
            if n in fk_col_names:
                continue
            if n.endswith("_id") and n[:-3] in fk_roots:
                continue
            names.append(n)
        break
    return names


# ─── Per-framework file-layout dispatchers ──────────────────────────────────

# Each dispatcher returns the list of (relative_path, file_kind) tuples a
# new entity needs in that framework. The implementer agent reads the
# `kind` to know which body template / pattern to apply.

def _files_fastapi(snake: str) -> List[Tuple[str, str]]:
    return [
        (f"{snake}/__init__.py",  "python_init"),
        (f"{snake}/models.py",    "sqlalchemy_model"),
        (f"{snake}/schemas.py",   "pydantic_schema"),
        (f"{snake}/service.py",   "service_layer"),       # Tier 8
        (f"{snake}/router.py",    "fastapi_router"),
        (f"tests/test_{snake}_api.py",     "pytest_module"),
        (f"tests/test_{snake}_service.py", "pytest_module"),  # Tier 8
    ]


def _files_django(snake: str) -> List[Tuple[str, str]]:
    # Django convention: each entity is its own app. Service / auth / tasks
    # added at v4.2 to match FastAPI's parity (business logic + auth + Celery).
    return [
        (f"{snake}/__init__.py",        "python_init"),
        (f"{snake}/apps.py",            "django_appconfig"),
        (f"{snake}/models.py",          "django_model"),
        (f"{snake}/serializers.py",     "drf_serializer"),
        (f"{snake}/services.py",        "django_service"),
        (f"{snake}/views.py",           "drf_viewset"),
        (f"{snake}/urls.py",            "django_urls"),
        (f"{snake}/auth.py",            "django_auth"),
        (f"{snake}/tasks.py",           "django_background_task"),
        (f"{snake}/admin.py",           "django_admin"),
        (f"{snake}/tests.py",           "django_tests"),
        (f"{snake}/migrations/__init__.py", "python_init"),
    ]


def _files_spring(snake: str) -> List[Tuple[str, str]]:
    # Spring Boot Java layout: domain / repository / service / controller / dto.
    # Auth + background added at v4.2 to match FastAPI's parity.
    pkg = snake.replace("_", "")
    cap = "".join(p.capitalize() for p in snake.split("_"))
    base = f"src/main/java/com/example/{pkg}"
    test_base = f"src/test/java/com/example/{pkg}"
    return [
        (f"{base}/{cap}.java",             "spring_entity"),
        (f"{base}/{cap}Repository.java",   "spring_repository"),
        (f"{base}/{cap}Service.java",      "spring_service"),
        (f"{base}/{cap}Controller.java",   "spring_controller"),
        (f"{base}/{cap}Dto.java",          "spring_dto"),
        (f"{base}/{cap}AuthService.java",  "spring_auth"),
        (f"{base}/{cap}BackgroundJob.java", "spring_background"),
        (f"{test_base}/{cap}ControllerTest.java", "spring_test"),
    ]


def _files_go(snake: str) -> List[Tuple[str, str]]:
    # Go layout: each entity is a package directory. Service / dto / auth /
    # background added at v4.2 to match FastAPI's parity.
    return [
        (f"internal/{snake}/{snake}.go",         "go_model"),
        (f"internal/{snake}/dto.go",             "go_dto"),
        (f"internal/{snake}/repository.go",      "go_repository"),
        (f"internal/{snake}/service.go",         "go_service"),
        (f"internal/{snake}/handler.go",         "go_handler"),
        (f"internal/{snake}/auth.go",            "go_auth"),
        (f"internal/{snake}/background.go",      "go_background"),
        (f"internal/{snake}/{snake}_test.go",    "go_test"),
    ]


def _files_nestjs(snake: str) -> List[Tuple[str, str]]:
    # NestJS layout. Auth + background processor added at v4.2 for parity.
    kebab = snake.replace("_", "-")
    return [
        (f"src/{kebab}/{kebab}.module.ts",          "nestjs_module"),
        (f"src/{kebab}/{kebab}.controller.ts",      "nestjs_controller"),
        (f"src/{kebab}/{kebab}.service.ts",         "nestjs_service"),
        (f"src/{kebab}/{kebab}.auth.service.ts",    "nestjs_auth"),
        (f"src/{kebab}/{kebab}.processor.ts",       "nestjs_background"),
        (f"src/{kebab}/dto/create-{kebab}.dto.ts",  "nestjs_dto"),
        (f"src/{kebab}/dto/update-{kebab}.dto.ts",  "nestjs_dto"),
        (f"src/{kebab}/entities/{kebab}.entity.ts", "nestjs_entity"),
        (f"src/{kebab}/{kebab}.controller.spec.ts", "nestjs_spec"),
    ]


def _files_nodejs(snake: str) -> List[Tuple[str, str]]:
    # Node.js (Express + Sequelize) layout — added at v4.2. Mirrors FastAPI's
    # 8-hint shape: init / model / schema / service / router / auth / background / test.
    return [
        (f"src/{snake}/index.js",        "nodejs_init"),
        (f"src/{snake}/model.js",        "nodejs_model"),
        (f"src/{snake}/schema.js",       "nodejs_schema"),
        (f"src/{snake}/service.js",      "nodejs_service"),
        (f"src/{snake}/router.js",       "nodejs_router"),
        (f"src/{snake}/auth.js",         "nodejs_auth"),
        (f"src/{snake}/background.js",   "nodejs_background"),
        (f"tests/{snake}.test.js",       "nodejs_test"),
    ]


_FILE_DISPATCHERS = {
    "fastapi": _files_fastapi,
    "django":  _files_django,
    "spring":  _files_spring,
    "go":      _files_go,
    "nestjs":  _files_nestjs,
    "nodejs":  _files_nodejs,
}


def _stubs_for_framework(framework: str, graph_imports: Dict,
                         has_new_entities: bool) -> List[str]:
    """Project-level stubs the implementer should also write when the host
    project lacks them.
    """
    if not has_new_entities:
        return []
    out: List[str] = []
    if framework == "fastapi":
        if "db_session_getter" not in graph_imports:
            out.append("database.py")
        if "model_base" not in graph_imports:
            out.append("models.py")
    elif framework == "django":
        # Django's settings.py needs new apps registered, but that's a
        # wiring action (handled by auto_wirer), not a stub file.
        pass
    elif framework == "spring":
        # Application class is typically already present; nothing to stub.
        pass
    elif framework == "go":
        if "db_session_getter" not in graph_imports:
            out.append("internal/db/db.go")
    elif framework == "nestjs":
        # AppModule already exists; nothing to stub.
        pass
    elif framework == "nodejs":
        if "db_session_getter" not in graph_imports:
            out.append("src/db.js")
        if "model_base" not in graph_imports:
            out.append("src/common/errors.js")
    return out


def _wiring_targets_for(framework: str) -> List[str]:
    return {
        "fastapi": ["main.py"],
        "django":  ["urls.py", "settings.py"],
        "spring":  [],   # autowiring via @SpringBootApplication scanning
        "go":      ["cmd/server/main.go"],
        "nestjs":  ["src/app.module.ts"],
        "nodejs":  ["src/app.js"],
    }.get(framework, ["main"])


def _migrations_for(framework: str) -> List[str]:
    return {
        "fastapi": ["alembic_revision"],
        "django":  ["python manage.py makemigrations && python manage.py migrate"],
        "spring":  ["flyway_or_liquibase"],
        "go":      ["golang-migrate_revision"],
        "nestjs":  ["typeorm_migration_generate"],
        "nodejs":  ["sequelize-cli_migration_generate"],
    }.get(framework, [])


# ─── Public entry ────────────────────────────────────────────────────────────

from lib.telemetry import traced as _traced


@_traced("scaffold_plan")
def plan(spec: Dict[str, Any]) -> ScaffoldPlan:
    framework = spec.get("framework", "fastapi")
    if framework not in _FILE_DISPATCHERS:
        raise ValueError(
            f"scaffold_planner does not yet support framework '{framework}'. "
            f"Supported: {sorted(_FILE_DISPATCHERS)}"
        )
    relationships = spec.get("relationships", [])
    graph_imports = spec.get("graph_imports", {}) or {}
    db = graph_imports.get("db_session_getter") or {}
    base = graph_imports.get("model_base") or {}
    db_module = db.get("module") or "database"
    db_func = db.get("name") or "get_db"
    base_module = base.get("module") or "models"
    base_name = base.get("name") or "Base"
    test_contract = spec.get("test_contract") or {}

    files: List[FileSpec] = []
    new_entities = [e for e in spec.get("entities", [])
                    if e.get("action") == "create"]
    dispatcher = _FILE_DISPATCHERS[framework]

    for ent in new_entities:
        pascal = ent["name"]
        snake = ent.get("snake_name") or pascal.lower()
        plural = ent.get("plural") or f"{snake}s"
        fk_cols = _fks_for_entity(snake, relationships)
        attr_names = _attribute_names_for(spec, snake, fk_cols)

        common = {
            "entity": pascal,
            "fk_columns": fk_cols,
            "base_module": base_module,
            "base_name": base_name,
            "db_module": db_module,
            "db_func": db_func,
            "attribute_names": attr_names,
            "test_contract": test_contract,
        }
        for path, kind in dispatcher(snake):
            files.append(FileSpec(path=path, kind=kind, **common))

    stubs: List[str] = _stubs_for_framework(framework, graph_imports,
                                             has_new_entities=bool(new_entities))

    return ScaffoldPlan(
        feature=spec.get("feature", ""),
        framework=framework,
        files_to_create=files,
        stubs_needed=stubs,
        wiring_targets=_wiring_targets_for(framework),
        migrations=_migrations_for(framework),
        relationships=relationships,
    )


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Plan the structural skeleton for an agentic generation. "
                    "Implementer agents fill in the bodies."
    )
    parser.add_argument("--spec", required=True, help="Path to spec.json")
    parser.add_argument("--out", default=None,
                        help="Write plan.json to this path (default: stdout)")
    args = parser.parse_args()

    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    p = plan(spec)
    payload = json.dumps(p.to_dict(), indent=2)
    if args.out:
        Path(args.out).write_text(payload, encoding="utf-8")
        print(f"wrote {args.out}", file=sys.stderr)
    else:
        print(payload)


if __name__ == "__main__":
    main()
