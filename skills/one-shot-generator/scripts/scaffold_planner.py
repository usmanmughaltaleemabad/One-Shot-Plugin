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
from typing import Any, Dict, List, Optional

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


# ─── Public entry ────────────────────────────────────────────────────────────

def plan(spec: Dict[str, Any]) -> ScaffoldPlan:
    framework = spec.get("framework", "fastapi")
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
        files.append(FileSpec(path=f"{snake}/__init__.py", kind="python_init", **common))
        files.append(FileSpec(path=f"{snake}/models.py", kind="sqlalchemy_model", **common))
        files.append(FileSpec(path=f"{snake}/schemas.py", kind="pydantic_schema", **common))
        files.append(FileSpec(path=f"{snake}/router.py", kind="fastapi_router", **common))
        files.append(FileSpec(path=f"tests/test_{snake}_api.py", kind="pytest_module", **common))

    stubs: List[str] = []
    if "db_session_getter" not in graph_imports and new_entities:
        stubs.append("database.py")
    if "model_base" not in graph_imports and new_entities:
        stubs.append("models.py")

    return ScaffoldPlan(
        feature=spec.get("feature", ""),
        framework=framework,
        files_to_create=files,
        stubs_needed=stubs,
        wiring_targets=["main.py"] if framework == "fastapi" else ["urls.py"],
        migrations=["alembic_revision"] if framework == "fastapi" else ["django_makemigrations"],
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
