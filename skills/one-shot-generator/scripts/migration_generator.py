#!/usr/bin/env python3
"""
Migration Generator — Tier 8 (real one-shot, not scaffolding)

Emits an Alembic revision file from spec.json. Turns this:

  spec.json: ShoppingCart, LineItem, Discount with has_many

into:

  alembic/versions/2026_05_18_0314-add_cart_features.py
    op.create_table('shopping_carts', ...)
    op.create_table('line_items', ...) with shopping_cart_id FK
    op.create_table('discounts', ...) with shopping_cart_id FK
    op.create_index('ix_line_items_shopping_cart_id', ...)
    + downgrade in reverse order

Now the user's `--apply` path doesn't stop at "generated files in folder";
it produces an actual database migration ready to `alembic upgrade head`.

Framework support:
  fastapi → alembic revision (SQLAlchemy)
  django  → django migration via `python manage.py makemigrations`
            (since Django generates these via introspection, the script
             outputs a runbook instead of a python file)
  others  → not supported yet

CLI:
    migration_generator.py --spec spec.json --out alembic/versions/
    migration_generator.py --spec spec.json --framework django --out .
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import textwrap
from pathlib import Path
from typing import Any, Dict, List

from lib.base_script import bootstrap_runtime, setup_logging
bootstrap_runtime()

logger = setup_logging(__name__)


# ─── Type mapping ───────────────────────────────────────────────────────────

PYTYPE_TO_SQLA = {
    "int": "sa.Integer()",
    "str": "sa.String(length=255)",
    "bool": "sa.Boolean()",
    "datetime": "sa.DateTime()",
    "Decimal": "sa.Numeric(precision=12, scale=2)",
    "float": "sa.Float()",
}


def _sqla_col(attr: Dict[str, Any]) -> str:
    name = attr["name"]
    # Accept both "type_hint" (Python annotation style) and "type" (plain spec style)
    raw = attr.get("type_hint") or attr.get("type") or "str"
    hint = raw.replace("Optional[", "").rstrip("]")
    sqla_type = PYTYPE_TO_SQLA.get(hint, "sa.String(length=255)")
    nullable = "True" if (
        "Optional" in raw or not attr.get("required", True)
    ) else "False"
    return f"sa.Column('{name}', {sqla_type}, nullable={nullable})"


def _revision_id() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d%H%M%S")


def _slug(text: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "_", text.lower()).strip("_")
    return s[:48] or "auto_migration"


# ─── FastAPI / SQLAlchemy / Alembic ────────────────────────────────────────

def generate_alembic_revision(spec: Dict[str, Any]) -> str:
    """Emit a complete Alembic revision file body."""
    entities_to_create = [
        e for e in spec.get("entities", []) if e.get("action") == "create"
    ]
    relationships = spec.get("relationships", [])

    rev_id = _revision_id()
    slug = _slug(spec.get("feature", "feature_migration"))
    feature = spec.get("feature", "")

    # ───── upgrade body ─────────────────────────────────────────────────
    upgrade_blocks: List[str] = []
    for ent in entities_to_create:
        snake = ent.get("snake_name") or ent["name"].lower()
        plural = ent.get("plural") or f"{snake}s"
        pascal = ent["name"]

        # Collect FK roots so we deduplicate against default attrs like
        # `cart_id` when the relationship already produced
        # `shopping_cart_id`. Mirror the dedup logic from scaffold_planner.
        cols_pairs: List[str] = [
            "sa.Column('id', sa.Integer(), nullable=False, autoincrement=True)",
        ]
        fk_col_names: set = set()
        fk_roots: set = set()

        for rel in relationships:
            kind = rel.get("kind", "has_many")
            from_ent = rel.get("from") or rel.get("from_entity")
            to_ent = rel.get("to") or rel.get("to_entity")
            if not (from_ent and to_ent):
                continue
            if kind == "has_many" and to_ent == snake:
                fk_col = f"{from_ent}_id"
                ref_table = f"{from_ent}s"
                cols_pairs.append(
                    f"sa.Column('{fk_col}', sa.Integer(), "
                    f"sa.ForeignKey('{ref_table}.id'), nullable=False)"
                )
                fk_col_names.add(fk_col)
                fk_roots.add(from_ent)
                for tail in from_ent.split("_"):
                    fk_roots.add(tail)

        # Domain attribute columns (with FK dedup)
        for attr in ent.get("attributes", []):
            name = attr.get("name")
            if not name or name in ("id", "created_at", "updated_at"):
                continue
            if name in fk_col_names:
                continue
            if name.endswith("_id") and name[:-3] in fk_roots:
                continue
            cols_pairs.append(_sqla_col(attr))

        # Always-present timestamps
        cols_pairs.append(
            "sa.Column('created_at', sa.DateTime(), nullable=False)")
        cols_pairs.append(
            "sa.Column('updated_at', sa.DateTime(), nullable=False)")
        cols_pairs.append("sa.PrimaryKeyConstraint('id')")

        # Build a properly-indented create_table block manually
        indented_cols = ",\n        ".join(cols_pairs)
        upgrade_blocks.append(
            f"    op.create_table(\n"
            f"        '{plural}',\n"
            f"        {indented_cols},\n"
            f"    )"
        )

        # Indexes on FKs
        for rel in relationships:
            kind = rel.get("kind", "has_many")
            from_ent = rel.get("from") or rel.get("from_entity")
            to_ent = rel.get("to") or rel.get("to_entity")
            if kind == "has_many" and to_ent == snake and from_ent:
                fk_col = f"{from_ent}_id"
                upgrade_blocks.append(
                    f"    op.create_index("
                    f"'ix_{plural}_{fk_col}', '{plural}', ['{fk_col}'])"
                )

    upgrade_body = "\n".join(upgrade_blocks) if upgrade_blocks \
        else "    pass  # no new entities to create"

    # ───── downgrade body (reverse order) ──────────────────────────────
    downgrade_blocks: List[str] = []
    for ent in reversed(entities_to_create):
        snake = ent.get("snake_name") or ent["name"].lower()
        plural = ent.get("plural") or f"{snake}s"
        for rel in relationships:
            from_ent = rel.get("from") or rel.get("from_entity")
            to_ent = rel.get("to") or rel.get("to_entity")
            if (rel.get("kind") == "has_many"
                    and to_ent == snake and from_ent):
                fk_col = f"{from_ent}_id"
                downgrade_blocks.append(
                    f"    op.drop_index("
                    f"'ix_{plural}_{fk_col}', table_name='{plural}')"
                )
        downgrade_blocks.append(f"    op.drop_table('{plural}')")

    downgrade_body = "\n".join(downgrade_blocks) if downgrade_blocks \
        else "    pass"

    created = dt.datetime.now(dt.timezone.utc).replace(
        microsecond=0).isoformat()
    return (
        f'"""{feature}\n\n'
        f"Revision ID: {rev_id}_{slug}\n"
        f"Revises:\n"
        f"Create Date: {created}\n"
        f'"""\n'
        f"from alembic import op\n"
        f"import sqlalchemy as sa\n\n\n"
        f"# revision identifiers, used by Alembic.\n"
        f'revision = "{rev_id}_{slug}"\n'
        f"down_revision = None\n"
        f"branch_labels = None\n"
        f"depends_on = None\n\n\n"
        f"def upgrade() -> None:\n"
        f"{upgrade_body}\n\n\n"
        f"def downgrade() -> None:\n"
        f"{downgrade_body}\n"
    )


# ─── Django runbook ─────────────────────────────────────────────────────────

def generate_django_runbook(spec: Dict[str, Any]) -> str:
    """Django generates migrations via introspection, so emit a runbook."""
    entities = [e["snake_name"] for e in spec.get("entities", [])
                if e.get("action") == "create"]
    lines = ["# Django Migration Runbook", "",
             f"# Feature: {spec.get('feature', '<unnamed>')}", ""]
    for ent in entities:
        lines.append(f"# 1. Add '{ent}' to INSTALLED_APPS in settings.py")
    lines.extend([
        "",
        "# 2. Run makemigrations to introspect models:",
        "python manage.py makemigrations " + " ".join(entities),
        "",
        "# 3. Inspect the generated migration files:",
        "ls -la */migrations/0001_initial.py",
        "",
        "# 4. Apply migrations:",
        "python manage.py migrate",
        "",
        "# 5. Verify in DB:",
        "python manage.py dbshell  -- then .tables (sqlite) or \\d (postgres)",
    ])
    return "\n".join(lines) + "\n"


# ─── Public entry ────────────────────────────────────────────────────────────

def generate(spec: Dict[str, Any], framework: str) -> Dict[str, str]:
    """Return {filename: content} for the migration artefact."""
    if framework == "fastapi":
        rev_id = _revision_id()
        slug = _slug(spec.get("feature", "feature_migration"))
        filename = f"{rev_id}_{slug}.py"
        return {filename: generate_alembic_revision(spec)}
    if framework == "django":
        return {"MIGRATION_RUNBOOK.md": generate_django_runbook(spec)}
    raise NotImplementedError(f"migration generator does not support framework '{framework}'")


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate an Alembic revision (or Django runbook) from spec.json"
    )
    parser.add_argument("--spec", required=True)
    parser.add_argument("--framework", choices=["fastapi", "django"], default=None,
                        help="Defaults to spec.framework")
    parser.add_argument("--out", default=None,
                        help="Directory to write the artefact (default: stdout)")
    args = parser.parse_args()

    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    framework = args.framework or spec.get("framework", "fastapi")
    files = generate(spec, framework)

    if args.out:
        out_dir = Path(args.out).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        for name, body in files.items():
            target = out_dir / name
            target.write_text(body, encoding="utf-8")
            print(f"wrote {target}", file=sys.stderr)
    else:
        for name, body in files.items():
            print(f"# === {name} ===")
            print(body)


if __name__ == "__main__":
    main()
