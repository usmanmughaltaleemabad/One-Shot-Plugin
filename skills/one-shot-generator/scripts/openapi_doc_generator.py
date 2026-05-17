#!/usr/bin/env python3
"""
OpenAPI Doc Generator — Tier 10 (production polish)

Generates an `openapi.json` from spec.json, with proper tags,
descriptions, examples, and security schemes. Drops in next to the
router files so FastAPI's auto-generated docs at /docs become
production-ready.

This is the difference between a generated /docs page that lists
"GET /carts/" with no description vs one that explains the endpoint,
shows a JSON example, lists the error codes, and groups under a tag.

CLI:
    openapi_doc_generator.py --spec spec.json --out openapi.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from lib.base_script import bootstrap_runtime, setup_logging
bootstrap_runtime()

logger = setup_logging(__name__)


# ─── Type mapping ───────────────────────────────────────────────────────────

PY_TO_OPENAPI = {
    "int": {"type": "integer"},
    "str": {"type": "string"},
    "bool": {"type": "boolean"},
    "datetime": {"type": "string", "format": "date-time"},
    "Decimal": {"type": "number", "format": "decimal"},
    "float": {"type": "number"},
}


def _schema_for(attr: Dict) -> Dict:
    hint = (attr.get("type_hint") or "str").replace("Optional[", "").rstrip("]")
    return PY_TO_OPENAPI.get(hint, {"type": "string"}).copy()


def _example_for(attr: Dict) -> Any:
    hint = (attr.get("type_hint") or "str").lower()
    name = attr.get("name", "")
    if "int" in hint:
        return 1
    if "decimal" in hint or "float" in hint:
        return 9.99
    if "bool" in hint:
        return True
    if "datetime" in hint:
        return "2026-05-18T00:00:00Z"
    if "email" in name.lower():
        return "user@example.com"
    return "example"


# ─── Builder ────────────────────────────────────────────────────────────────

def _entity_schemas(entity: Dict, relationships: List[Dict]) -> Dict[str, Dict]:
    """Return OpenAPI component schemas for one entity."""
    pascal = entity["name"]
    snake = entity.get("snake_name", pascal.lower())
    attrs = entity.get("attributes", [])
    fk_cols = []
    for rel in relationships:
        kind = rel.get("kind", "has_many")
        from_ent = rel.get("from") or rel.get("from_entity")
        to_ent = rel.get("to") or rel.get("to_entity")
        if kind == "has_many" and to_ent == snake and from_ent:
            fk_cols.append(f"{from_ent}_id")

    properties: Dict[str, Dict] = {}
    create_properties: Dict[str, Dict] = {}
    create_required: List[str] = []
    create_example: Dict[str, Any] = {}

    for fk in fk_cols:
        properties[fk] = {"type": "integer"}
        create_properties[fk] = {"type": "integer"}
        create_required.append(fk)
        create_example[fk] = 1

    for attr in attrs:
        name = attr.get("name")
        if not name or name in fk_cols:
            continue
        schema = _schema_for(attr)
        properties[name] = schema
        if name in ("id", "created_at", "updated_at"):
            continue
        create_properties[name] = schema
        if attr.get("required") and "Optional" not in (attr.get("type_hint") or ""):
            create_required.append(name)
        create_example[name] = _example_for(attr)

    # Read-only properties on Read schema
    properties.setdefault("id", {"type": "integer", "readOnly": True})
    properties.setdefault("created_at",
                          {"type": "string", "format": "date-time",
                           "readOnly": True})
    properties.setdefault("updated_at",
                          {"type": "string", "format": "date-time",
                           "readOnly": True})

    return {
        f"{pascal}Read": {
            "type": "object",
            "description": f"{pascal} as returned by the API.",
            "properties": properties,
            "required": list(create_required) + ["id", "created_at", "updated_at"],
        },
        f"{pascal}Create": {
            "type": "object",
            "description": f"Payload for creating a new {pascal}.",
            "properties": create_properties,
            "required": create_required,
            "example": create_example,
        },
        f"{pascal}Update": {
            "type": "object",
            "description": (
                f"Payload for partially updating a {pascal}. "
                f"All fields are optional (PATCH semantics)."
            ),
            "properties": {
                k: {**v, "nullable": True} for k, v in create_properties.items()
            },
        },
    }


def _entity_paths(entity: Dict, has_auth: bool) -> Dict[str, Dict]:
    pascal = entity["name"]
    snake = entity.get("snake_name", pascal.lower())
    plural = entity.get("plural", f"{snake}s")
    base = f"/api/v1/{plural}"
    tag = pascal
    security = [{"bearerAuth": []}] if has_auth else []

    return {
        base: {
            "get": {
                "tags": [tag],
                "summary": f"List {plural}",
                "description": (
                    f"List {plural} with pagination support. "
                    f"Returns a JSON array of {pascal}Read objects."
                ),
                "parameters": [
                    {"name": "skip", "in": "query",
                     "schema": {"type": "integer", "default": 0}},
                    {"name": "limit", "in": "query",
                     "schema": {"type": "integer", "default": 100}},
                ],
                "responses": {
                    "200": {
                        "description": "List of " + plural,
                        "content": {"application/json": {
                            "schema": {
                                "type": "array",
                                "items": {"$ref": f"#/components/schemas/{pascal}Read"},
                            }
                        }},
                    },
                },
                "security": security,
            },
            "post": {
                "tags": [tag],
                "summary": f"Create a new {pascal}",
                "description": f"Creates a new {pascal} and returns it.",
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {
                        "schema": {"$ref": f"#/components/schemas/{pascal}Create"},
                    }},
                },
                "responses": {
                    "201": {
                        "description": "Created",
                        "content": {"application/json": {
                            "schema": {"$ref": f"#/components/schemas/{pascal}Read"},
                        }},
                    },
                    "422": {"$ref": "#/components/responses/ValidationError"},
                },
                "security": security,
            },
        },
        f"{base}/{{item_id}}": {
            "get": {
                "tags": [tag],
                "summary": f"Get a single {pascal}",
                "parameters": [{
                    "name": "item_id", "in": "path", "required": True,
                    "schema": {"type": "integer"},
                }],
                "responses": {
                    "200": {
                        "description": pascal,
                        "content": {"application/json": {
                            "schema": {"$ref": f"#/components/schemas/{pascal}Read"},
                        }},
                    },
                    "404": {"$ref": "#/components/responses/NotFound"},
                },
                "security": security,
            },
            "put": {
                "tags": [tag],
                "summary": f"Update an existing {pascal}",
                "parameters": [{
                    "name": "item_id", "in": "path", "required": True,
                    "schema": {"type": "integer"},
                }],
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {
                        "schema": {"$ref": f"#/components/schemas/{pascal}Update"},
                    }},
                },
                "responses": {
                    "200": {
                        "description": "Updated",
                        "content": {"application/json": {
                            "schema": {"$ref": f"#/components/schemas/{pascal}Read"},
                        }},
                    },
                    "404": {"$ref": "#/components/responses/NotFound"},
                },
                "security": security,
            },
            "delete": {
                "tags": [tag],
                "summary": f"Delete a {pascal}",
                "parameters": [{
                    "name": "item_id", "in": "path", "required": True,
                    "schema": {"type": "integer"},
                }],
                "responses": {
                    "204": {"description": "Deleted"},
                    "404": {"$ref": "#/components/responses/NotFound"},
                },
                "security": security,
            },
        },
    }


# ─── Public entry ────────────────────────────────────────────────────────────

def generate(spec: Dict[str, Any]) -> Dict[str, Any]:
    entities_to_create = [
        e for e in spec.get("entities", []) if e.get("action") == "create"
    ]
    relationships = spec.get("relationships", [])
    test_contract = spec.get("test_contract", {})
    has_auth = test_contract.get("auth", "none") != "none"

    schemas: Dict[str, Dict] = {}
    paths: Dict[str, Dict] = {}
    tags: List[Dict] = []

    for ent in entities_to_create:
        schemas.update(_entity_schemas(ent, relationships))
        paths.update(_entity_paths(ent, has_auth))
        tags.append({
            "name": ent["name"],
            "description": f"Operations on {ent['name']} entities",
        })

    openapi: Dict[str, Any] = {
        "openapi": "3.1.0",
        "info": {
            "title": spec.get("feature", "Generated API"),
            "version": "0.1.0",
            "description": (
                f"Auto-generated by one-shot-prompting from spec.json. "
                f"Feature: {spec.get('feature', 'unnamed')}."
            ),
        },
        "tags": tags,
        "paths": paths,
        "components": {
            "schemas": schemas,
            "responses": {
                "NotFound": {
                    "description": "Resource not found",
                    "content": {"application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "detail": {"type": "string"},
                                "code": {"type": "string"},
                            },
                        },
                    }},
                },
                "ValidationError": {
                    "description": "Request validation failed",
                    "content": {"application/json": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "detail": {"type": "array",
                                            "items": {"type": "object"}},
                            },
                        },
                    }},
                },
            },
        },
    }

    if has_auth:
        openapi["components"]["securitySchemes"] = {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
            },
        }

    return openapi


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate production-grade openapi.json from spec.json"
    )
    parser.add_argument("--spec", required=True)
    parser.add_argument("--out", default=None,
                        help="Write to file (default: stdout)")
    args = parser.parse_args()
    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    openapi = generate(spec)
    payload = json.dumps(openapi, indent=2)
    if args.out:
        Path(args.out).write_text(payload, encoding="utf-8")
        print(f"wrote {args.out}", file=sys.stderr)
    else:
        print(payload)


if __name__ == "__main__":
    main()
