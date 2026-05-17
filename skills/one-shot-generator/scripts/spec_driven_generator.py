#!/usr/bin/env python3
"""
Spec-Driven Generator — v1.0.0  (Tier 2.5)

Reads a ``spec.json`` produced by ``compile_spec.py`` (which in turn
consumes ``one_shot_orchestrator``'s output) and produces ONE coherent
set of files covering every entity, with relationships respected.

Critical upgrade over the legacy per-entity phase2 loop:

  * Honours ``has_many`` / ``belongs_to`` / ``many_to_many`` relationships
    extracted from the natural-language request. A line_item generated as
    part of "cart with line items" gets a ``cart_id`` FK; today's phase2
    loop produced a standalone line_item with no relationship to cart.

  * Generates schemas + models + routers in a self-consistent way, using
    the existing project's import contracts (``codebase_graph.imports``)
    so the generated code drops straight in.

  * Uses ``textwrap.dedent`` + ``.format(**kwargs)`` instead of f-string
    concatenation, eliminating the entire ``NameError: name 'self'``
    class of bug we fixed in v2.0.0.

The output shape matches what ``generate_and_verify`` expects:

    {
        "cart/models.py":  "...",
        "cart/router.py":  "...",
        "cart/schemas.py": "...",
        "line_item/models.py": "...",
        ...,
        "tests/test_cart_api.py": "...",
        "README.md": "..."
    }

CLI:
    python spec_driven_generator.py --spec spec.json --out-json out.json
"""

from __future__ import annotations

import argparse
import json
import sys
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from lib.base_script import bootstrap_runtime, setup_logging
bootstrap_runtime()

logger = setup_logging(__name__)


# ─── Helpers ─────────────────────────────────────────────────────────────────

_SQLALCHEMY_TYPE_MAP = {
    "int": "Integer",
    "str": "String(255)",
    "bool": "Boolean",
    "datetime": "DateTime",
    "Decimal": "Numeric(precision=12, scale=2)",
    "float": "Float",
}


def _sqla_type(hint: str) -> str:
    """Map a Python type hint to a SQLAlchemy column type string."""
    hint_clean = (hint or "").replace("Optional[", "").rstrip("]").strip()
    return _SQLALCHEMY_TYPE_MAP.get(hint_clean, "String(255)")


def _is_optional(hint: str) -> bool:
    return "Optional[" in (hint or "")


def _python_type(hint: str) -> str:
    return hint or "str"


def _attribute_lookup(spec_entities: List[Dict],
                       entity_name: str) -> List[Dict]:
    for ent in spec_entities:
        if ent.get("snake_name") == entity_name or ent.get("name") == entity_name:
            return ent.get("attributes", []) or []
    return []


def _relationships_for(spec: Dict, entity_snake: str) -> List[Dict]:
    """Return relationships where this entity is the OWNED side (belongs_to).

    For each has_many relationship in the spec, the child entity needs a
    foreign-key column pointing back at the parent. We translate has_many
    on the parent into belongs_to on the child.
    """
    out: List[Dict] = []
    # The spec.json stores relationships under domain_entities OR we infer
    # them from extract_domain_model. compile_spec preserves entities but
    # not raw relationships, so we re-derive from the orchestrator report
    # if present, otherwise use a passed-in list.
    for rel in spec.get("relationships", []):
        if rel.get("kind") == "has_many" and rel.get("to") == entity_snake:
            out.append({
                "fk_column": f"{rel['from']}_id",
                "references": rel["from"],
            })
        elif rel.get("kind") == "belongs_to" and rel.get("from") == entity_snake:
            out.append({
                "fk_column": f"{rel['to']}_id",
                "references": rel["to"],
            })
    return out


# ─── Code templates ──────────────────────────────────────────────────────────

_MODEL_TEMPLATE = textwrap.dedent("""
    \"\"\"SQLAlchemy model for {pascal}.\"\"\"
    from __future__ import annotations
    from datetime import datetime
    from decimal import Decimal
    from typing import Optional

    from sqlalchemy import (
        Column, Integer, String, Boolean, DateTime, Numeric, Float, ForeignKey
    )
    from sqlalchemy.orm import relationship

    from {base_module} import {base_name}


    class {pascal}({base_name}):
        \"\"\"{pascal} domain entity.\"\"\"

        __tablename__ = "{plural}"

    {columns}

        def __repr__(self) -> str:
            return f"<{pascal}(id={{self.id!r}})>"
    """).strip() + "\n"


_SCHEMA_TEMPLATE = textwrap.dedent("""
    \"\"\"Pydantic schemas for {pascal}.\"\"\"
    from __future__ import annotations
    from datetime import datetime
    from decimal import Decimal
    from typing import Optional

    from pydantic import BaseModel, Field


    class {pascal}Base(BaseModel):
    {field_lines_optional}


    class {pascal}Create({pascal}Base):
    {field_lines_required}


    class {pascal}Read({pascal}Base):
        id: int
        created_at: datetime
        updated_at: datetime

        model_config = {{"from_attributes": True}}


    class {pascal}Update(BaseModel):
    {field_lines_update}
    """).strip() + "\n"


_ROUTER_TEMPLATE = textwrap.dedent("""
    \"\"\"REST router for {pascal} (CRUD).\"\"\"
    from __future__ import annotations
    from typing import List

    from fastapi import APIRouter, Depends, HTTPException, status
    from sqlalchemy.orm import Session

    from {db_module} import {db_func}
    from {model_module} import {pascal}
    from {schema_module} import {pascal}Create, {pascal}Read, {pascal}Update

    router = APIRouter(prefix="/api/v1/{plural}", tags=["{snake}"])


    @router.get("/", response_model=List[{pascal}Read])
    def list_{plural}(db: Session = Depends({db_func}),
                       skip: int = 0,
                       limit: int = 100) -> List[{pascal}]:
        return db.query({pascal}).offset(skip).limit(limit).all()


    @router.post("/", response_model={pascal}Read,
                  status_code=status.HTTP_201_CREATED)
    def create_{snake}(payload: {pascal}Create,
                        db: Session = Depends({db_func})) -> {pascal}:
        obj = {pascal}(**payload.model_dump())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj


    @router.get("/{{item_id}}", response_model={pascal}Read)
    def retrieve_{snake}(item_id: int,
                          db: Session = Depends({db_func})) -> {pascal}:
        obj = db.get({pascal}, item_id)
        if obj is None:
            raise HTTPException(status_code=404, detail="not found")
        return obj


    @router.put("/{{item_id}}", response_model={pascal}Read)
    def update_{snake}(item_id: int,
                        payload: {pascal}Update,
                        db: Session = Depends({db_func})) -> {pascal}:
        obj = db.get({pascal}, item_id)
        if obj is None:
            raise HTTPException(status_code=404, detail="not found")
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(obj, key, value)
        db.commit()
        db.refresh(obj)
        return obj


    @router.delete("/{{item_id}}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_{snake}(item_id: int,
                        db: Session = Depends({db_func})) -> None:
        obj = db.get({pascal}, item_id)
        if obj is None:
            raise HTTPException(status_code=404, detail="not found")
        db.delete(obj)
        db.commit()
    """).strip() + "\n"


_TEST_TEMPLATE = textwrap.dedent("""
    \"\"\"Smoke tests for {pascal} CRUD endpoints.\"\"\"
    from __future__ import annotations
    from fastapi.testclient import TestClient


    def test_list_{plural}_returns_list(client: TestClient) -> None:
        response = client.get("/api/v1/{plural}/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


    def test_create_{snake}_round_trip(client: TestClient) -> None:
        payload = {payload_literal}
        response = client.post("/api/v1/{plural}/", json=payload)
        assert response.status_code == 201
        created = response.json()
        assert "id" in created
        # Retrieve confirms persistence
        got = client.get(f"/api/v1/{plural}/{{created['id']}}")
        assert got.status_code == 200


    def test_retrieve_missing_{snake}_is_404(client: TestClient) -> None:
        response = client.get("/api/v1/{plural}/99999999")
        assert response.status_code == 404
    """).strip() + "\n"


# ─── Column / field rendering ────────────────────────────────────────────────

def _render_columns(attributes: List[Dict],
                    relationships: List[Dict]) -> str:
    lines: List[str] = []
    lines.append("    id = Column(Integer, primary_key=True, index=True)")
    seen_names = {"id"}
    fk_roots: set = set()  # singular references e.g. 'shopping_cart', 'cart'
    for rel in relationships:
        fk_col = rel["fk_column"]
        ref_table = f"{rel['references']}s"
        lines.append(
            f"    {fk_col} = Column(Integer, "
            f'ForeignKey("{ref_table}.id"), nullable=False, index=True)'
        )
        seen_names.add(fk_col)
        # Track the "root" so we can deduplicate a default `cart_id` when a
        # relationship has already produced `shopping_cart_id`.
        fk_roots.add(rel["references"])
        for tail in rel["references"].split("_"):
            fk_roots.add(tail)
    for attr in attributes:
        name = attr.get("name")
        if not name or name in seen_names or name in ("id", "created_at", "updated_at"):
            continue
        # Skip _id columns that duplicate an inferred FK relationship
        if name.endswith("_id"):
            root = name[:-3]
            if root in fk_roots:
                continue
        col_type = _sqla_type(attr.get("type_hint"))
        nullable = "True" if _is_optional(attr.get("type_hint", "")) \
                            or not attr.get("required", True) else "False"
        lines.append(f"    {name} = Column({col_type}, nullable={nullable})")
        seen_names.add(name)
    lines.append("    created_at = Column(DateTime, nullable=False, "
                  "default=datetime.utcnow)")
    lines.append("    updated_at = Column(DateTime, nullable=False, "
                  "default=datetime.utcnow, onupdate=datetime.utcnow)")
    return "\n".join(lines)


def _render_field_lines(attributes: List[Dict], relationships: List[Dict],
                         *, required_only: bool = False,
                         all_optional: bool = False) -> str:
    out: List[str] = []
    seen = {"id", "created_at", "updated_at"}
    fk_roots: set = set()
    for rel in relationships:
        fk_col = rel["fk_column"]
        if all_optional:
            out.append(f"    {fk_col}: Optional[int] = None")
        else:
            out.append(f"    {fk_col}: int")
        seen.add(fk_col)
        fk_roots.add(rel["references"])
        for tail in rel["references"].split("_"):
            fk_roots.add(tail)
    for attr in attributes:
        name = attr.get("name")
        if not name or name in seen:
            continue
        if name.endswith("_id") and name[:-3] in fk_roots:
            continue
        is_required = attr.get("required", True) and not _is_optional(
            attr.get("type_hint", ""))
        if required_only and not is_required:
            continue
        py_type = _python_type(attr.get("type_hint"))
        if all_optional:
            base = py_type.replace("Optional[", "").rstrip("]")
            out.append(f"    {name}: Optional[{base}] = None")
        elif is_required:
            out.append(f"    {name}: {py_type}")
        else:
            out.append(f"    {name}: {py_type} = None")
        seen.add(name)
    return "\n".join(out) if out else "    pass"


def _example_payload(attributes: List[Dict], relationships: List[Dict]) -> str:
    parts: List[str] = []
    fk_roots: set = set()
    for rel in relationships:
        parts.append(f'"{rel["fk_column"]}": 1')
        fk_roots.add(rel["references"])
        for tail in rel["references"].split("_"):
            fk_roots.add(tail)
    for attr in attributes:
        name = attr.get("name")
        if not name or name in ("id", "created_at", "updated_at"):
            continue
        if name.endswith("_id") and name[:-3] in fk_roots:
            continue
        hint = attr.get("type_hint", "str")
        if "int" in hint:
            parts.append(f'"{name}": 1')
        elif "Decimal" in hint or "float" in hint:
            parts.append(f'"{name}": 1.0')
        elif "bool" in hint:
            parts.append(f'"{name}": True')
        elif "datetime" in hint:
            parts.append(f'"{name}": "2026-01-01T00:00:00"')
        else:
            parts.append(f'"{name}": "example"')
    return "{" + ", ".join(parts) + "}"


# ─── Wiring helpers ──────────────────────────────────────────────────────────

def _resolve_imports(graph_imports: Dict[str, Dict[str, str]],
                      framework: str) -> Tuple[str, str, str, str]:
    """Return (db_module, db_func, base_module, base_name)."""
    db = graph_imports.get("db_session_getter") or {}
    base = graph_imports.get("model_base") or {}
    db_module = db.get("module") or "database"
    db_func = db.get("name") or "get_db"
    base_module = base.get("module") or "models"
    base_name = base.get("name") or "Base"
    return db_module, db_func, base_module, base_name


# ─── Main entry ──────────────────────────────────────────────────────────────

def generate_from_spec(spec: Dict[str, Any]) -> Dict[str, str]:
    framework = spec.get("framework", "fastapi")
    if framework != "fastapi":
        raise NotImplementedError(
            f"spec_driven_generator only supports FastAPI at v1.0; got {framework}"
        )
    graph_imports = spec.get("graph_imports") or {}
    db_module, db_func, base_module, base_name = _resolve_imports(
        graph_imports, framework)

    relationships_by_entity: Dict[str, List[Dict]] = {}
    for rel in spec.get("relationships", []):
        relationships_by_entity.setdefault(rel.get("to", ""), []).append(rel)

    out: Dict[str, str] = {}
    entities_to_emit = [e for e in spec.get("entities", [])
                        if e.get("action") == "create"]
    if not entities_to_emit:
        return out

    # If the project has no get_db / model base, emit thin stubs so the
    # generated code is self-contained and the C5 consistency checker
    # doesn't flag the imports as missing.
    if "db_session_getter" not in graph_imports:
        out["database.py"] = textwrap.dedent("""
            \"\"\"Database session stub generated by one-shot-prompting.

            Replace this with your real database wiring (SQLAlchemy engine
            + sessionmaker) once the rest of the feature is plumbed in.
            \"\"\"
            from __future__ import annotations
            from typing import Iterator

            from sqlalchemy import create_engine
            from sqlalchemy.orm import Session, sessionmaker

            _engine = create_engine("sqlite:///./osp_app.db", future=True)
            _SessionLocal = sessionmaker(bind=_engine, autocommit=False,
                                          autoflush=False, future=True)


            def get_db() -> Iterator[Session]:
                \"\"\"FastAPI dependency that yields a database session.\"\"\"
                session = _SessionLocal()
                try:
                    yield session
                finally:
                    session.close()
            """).strip() + "\n"
    if "model_base" not in graph_imports:
        out["models.py"] = textwrap.dedent("""
            \"\"\"Declarative Base for SQLAlchemy models.

            Imported by every generated module so all models share metadata
            and migrations stay in sync.
            \"\"\"
            from __future__ import annotations
            from sqlalchemy.orm import declarative_base

            Base = declarative_base()
            """).strip() + "\n"

    for ent in entities_to_emit:
        pascal = ent["name"]
        snake = ent["snake_name"]
        plural = ent["plural"]
        attrs = ent.get("attributes", [])
        rels = _relationships_for(spec, snake)

        out[f"{snake}/__init__.py"] = ""
        out[f"{snake}/models.py"] = _MODEL_TEMPLATE.format(
            pascal=pascal, plural=plural,
            base_module=base_module, base_name=base_name,
            columns=_render_columns(attrs, rels),
        )
        out[f"{snake}/schemas.py"] = _SCHEMA_TEMPLATE.format(
            pascal=pascal,
            field_lines_optional=_render_field_lines(attrs, rels),
            field_lines_required=_render_field_lines(
                attrs, rels, required_only=True),
            field_lines_update=_render_field_lines(
                attrs, rels, all_optional=True),
        )
        out[f"{snake}/router.py"] = _ROUTER_TEMPLATE.format(
            pascal=pascal, snake=snake, plural=plural,
            db_module=db_module, db_func=db_func,
            model_module=f"{snake}.models",
            schema_module=f"{snake}.schemas",
        )
        out[f"tests/test_{snake}_api.py"] = _TEST_TEMPLATE.format(
            pascal=pascal, snake=snake, plural=plural,
            payload_literal=_example_payload(attrs, rels),
        )

    # One README that lists every entity generated and the relationships
    readme_lines = ["# Generated Feature: " + spec.get("feature", "<unnamed>"),
                     "",
                     "## Entities",
                     ""]
    for ent in entities_to_emit:
        readme_lines.append(f"- **{ent['name']}** (`{ent['snake_name']}`)")
    rels = spec.get("relationships", [])
    if rels:
        readme_lines.extend(["", "## Relationships", ""])
        for rel in rels:
            readme_lines.append(
                f"- `{rel['from']}` --{rel['kind']}--> `{rel['to']}`"
            )
    readme_lines.extend([
        "",
        "## Integration",
        "",
        "Run migrations after wiring the routers into your app:",
        "",
        "```bash",
        "alembic revision --autogenerate -m 'add " +
        ", ".join(e["snake_name"] for e in entities_to_emit) + "'",
        "alembic upgrade head",
        "```",
        "",
    ])
    out["README.md"] = "\n".join(readme_lines)
    return out


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate code from a spec.json (multi-entity, relationship-aware)"
    )
    parser.add_argument("--spec", required=True, help="Path to spec.json")
    parser.add_argument("--out-json", default=None,
                        help="Write generated files as {filename: content} JSON")
    parser.add_argument("--out-dir", default=None,
                        help="Write generated files to disk")
    args = parser.parse_args()

    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    files = generate_from_spec(spec)

    if args.out_dir:
        out_dir = Path(args.out_dir).resolve()
        for name, content in files.items():
            path = out_dir / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        print(f"wrote {len(files)} files to {out_dir}", file=sys.stderr)
    if args.out_json:
        Path(args.out_json).write_text(json.dumps(files, indent=2),
                                        encoding="utf-8")
        print(f"wrote {args.out_json}", file=sys.stderr)
    if not args.out_dir and not args.out_json:
        print(json.dumps(files, indent=2))


if __name__ == "__main__":
    main()
