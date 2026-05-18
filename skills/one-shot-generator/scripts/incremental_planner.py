#!/usr/bin/env python3
"""
Incremental Planner — v1.0.0  (--incremental slicing for /one-shot)

The default /one-shot generates every entity in parallel — one big slice.
That's efficient when nothing fails. When something fails, you've burned
~$0.45 with nothing shippable.

`--incremental` mode trades parallelism for shippability. It generates
entities one at a time in FK-dependency order. Each slice is a real
PR-shaped unit: ~5 files, tests must be green BEFORE next slice begins,
git commit between slices. If slice 3 fails, slices 1 + 2 are already
shipped and the user has a working partial feature.

Inspired by Addy Osmani's incremental-implementation skill — thin
vertical slices that keep the system working at every step.

This module is the topological sorter + slice emitter:
  - Read spec.json
  - Topo-sort entities (parents-before-children, per FK relationships)
  - For each entity, emit a sliced spec with ONLY that entity in the
    entities list (relationships preserved so FKs still resolve)
  - Emit a per-slice plan: commit message, expected files, ship-gate scope

The orchestrator (the slash-command Claude session) runs the existing
pipeline (scaffold_planner → implementer → reviewer → doubter → wirer →
critic) on each sliced spec in turn.

CLI:
    incremental_planner.py --spec <path> [--out-dir <dir>]
    incremental_planner.py --spec <path> --validate    # exit 1 if cycle

Outputs (JSON to stdout):
    {
      "feature": "shopping cart with line items and discounts",
      "framework": "fastapi",
      "total_slices": 3,
      "slices": [
        {
          "slice_number": 1,
          "entity": "ShoppingCart",
          "snake_name": "shopping_cart",
          "depends_on": [],
          "commit_subject": "feat(shopping-cart): add ShoppingCart [slice 1/3]",
          "sliced_spec_path": "/tmp/osp-slice-1-shopping_cart.json"
        },
        {
          "slice_number": 2,
          "entity": "LineItem",
          "snake_name": "line_item",
          "depends_on": ["ShoppingCart"],
          "commit_subject": "feat(shopping-cart): add LineItem [slice 2/3]",
          "sliced_spec_path": "/tmp/osp-slice-2-line_item.json"
        },
        ...
      ],
      "cycle_detected": false,
      "cycle_members": []
    }

Exit codes:
    0   plan emitted (no cycle)
    1   bad CLI args
    2   spec has an FK cycle — incremental mode is impossible, abort
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from lib.base_script import bootstrap_runtime, setup_logging
bootstrap_runtime()
logger = setup_logging(__name__)


# ─── Topological sort with cycle detection ─────────────────────────────────

def _build_dep_graph(entities: List[Dict],
                      relationships: List[Dict]) -> Dict[str, Set[str]]:
    """Return {child_pascal: set(parent_pascals_it_depends_on)} — child must
    come AFTER every parent. Self-references are stripped (single entity)."""
    pascal_by_snake: Dict[str, str] = {}
    pascal_set: Set[str] = set()
    for ent in entities:
        snake = ent.get("snake_name") or ent.get("name", "").lower()
        pascal = ent.get("name") or snake.title()
        pascal_by_snake[snake] = pascal
        pascal_set.add(pascal)

    deps: Dict[str, Set[str]] = {p: set() for p in pascal_set}

    for rel in relationships:
        kind = rel.get("kind", "has_many")
        from_ent = rel.get("from") or rel.get("from_entity")
        to_ent = rel.get("to") or rel.get("to_entity")
        if not (from_ent and to_ent):
            continue
        from_pascal = pascal_by_snake.get(from_ent, from_ent.title())
        to_pascal = pascal_by_snake.get(to_ent, to_ent.title())
        if from_pascal not in pascal_set or to_pascal not in pascal_set:
            # FK to an entity we're not creating — ignore for ordering;
            # the existing entity is already there.
            continue
        if from_pascal == to_pascal:
            # self-reference — single entity is its own slice, no extra edge.
            continue
        # has_many: parent (from) → child (to). Child carries the FK column,
        # so child depends on parent.
        # belongs_to: from is the child; to is the parent.
        if kind == "has_many":
            deps[to_pascal].add(from_pascal)
        elif kind == "belongs_to":
            deps[from_pascal].add(to_pascal)
        else:
            # Treat one_to_one and many_to_many heuristically: prefer
            # alphabetical order to avoid arbitrary thrash.
            if from_pascal < to_pascal:
                deps[to_pascal].add(from_pascal)
            else:
                deps[from_pascal].add(to_pascal)

    return deps


def _topo_sort(deps: Dict[str, Set[str]]) -> Tuple[List[str], List[str]]:
    """Kahn's algorithm — return (ordered_list, cycle_members).
    cycle_members is empty when no cycle. ordered_list is the resolved
    portion (may be partial if a cycle exists)."""
    # In-degree count: how many parents each node still has unresolved.
    in_degree: Dict[str, int] = {n: len(parents) for n, parents in deps.items()}
    # Reverse map: which children does each parent unblock?
    children: Dict[str, Set[str]] = defaultdict(set)
    for child, parents in deps.items():
        for p in parents:
            children[p].add(child)

    # Stable tie-break: alphabetical among same-in-degree.
    ready = sorted(n for n, d in in_degree.items() if d == 0)
    order: List[str] = []
    while ready:
        # Pop alphabetically smallest for deterministic ordering.
        ready.sort()
        n = ready.pop(0)
        order.append(n)
        for child in sorted(children[n]):
            in_degree[child] -= 1
            if in_degree[child] == 0:
                ready.append(child)

    # Anything still with in_degree > 0 is in a cycle.
    cycle = sorted(n for n, d in in_degree.items() if d > 0)
    return order, cycle


# ─── Slice emission ────────────────────────────────────────────────────────

def _pascal_to_snake(pascal: str) -> str:
    """PascalCase -> snake_case ('UserProfile' -> 'user_profile')."""
    out: List[str] = []
    for i, ch in enumerate(pascal):
        if i > 0 and ch.isupper():
            out.append("_")
        out.append(ch.lower())
    return "".join(out)


def _slug(s: str) -> str:
    return s.replace("_", "-").lower()


def _sliced_spec(full_spec: Dict, target_pascal: str) -> Dict:
    """Produce a spec that contains ONLY the target entity in entities[],
    but preserves the global relationships + graph_imports + test_contract.
    The relationships list is also pruned to remove edges whose other end
    refers to an entity NOT in this slice — except where the other end
    already exists in the project (FK to pre-existing data)."""
    # Find the entity row
    target_entity = None
    for ent in full_spec.get("entities", []):
        if ent.get("name") == target_pascal:
            target_entity = ent
            break
    if target_entity is None:
        raise ValueError(f"entity '{target_pascal}' not in spec")

    target_snake = target_entity.get("snake_name") or target_pascal.lower()

    # Keep relationships involving the target. Any FK to an entity NOT in
    # this slice resolves against earlier-slice data (already in the DB).
    kept_rels: List[Dict] = []
    for rel in full_spec.get("relationships", []):
        f = rel.get("from") or rel.get("from_entity")
        t = rel.get("to") or rel.get("to_entity")
        if f == target_snake or t == target_snake:
            kept_rels.append(rel)

    sliced = dict(full_spec)
    sliced["entities"] = [target_entity]
    sliced["relationships"] = kept_rels
    # API surface: keep only routes that mention this entity.
    if "api_surface" in sliced:
        api = []
        for route in sliced.get("api_surface", []) or []:
            path = (route.get("path") or "").lower()
            if target_snake in path or _slug(target_snake) in path \
                    or target_pascal.lower() in path:
                api.append(route)
        sliced["api_surface"] = api

    return sliced


def _commit_subject(feature: str, pascal: str, slice_n: int, total: int) -> str:
    """Commit subject ≤ 72 chars, scoped by the FEATURE's first 2-3 words
    (clean kebab; never truncated mid-word) and the entity being added."""
    words = [w for w in feature.replace("_", " ").split() if w][:3]
    scope = _slug("-".join(words)).strip("-") or "feature"
    subject = f"feat({scope}): add {pascal} [slice {slice_n}/{total}]"
    # Hard cap at 72 — if the entity name is huge, fall back to no-scope form
    if len(subject) > 72:
        subject = f"feat: add {pascal} [slice {slice_n}/{total}]"
    return subject


def plan(spec: Dict, *, out_dir: Optional[Path] = None) -> Dict:
    entities = spec.get("entities") or []
    new_entities = [e for e in entities if e.get("action") == "create" or "action" not in e]
    if not new_entities:
        return {
            "feature": spec.get("feature", ""),
            "framework": spec.get("framework", "fastapi"),
            "total_slices": 0,
            "slices": [],
            "cycle_detected": False,
            "cycle_members": [],
            "skip_reason": "no_new_entities",
        }

    deps = _build_dep_graph(new_entities, spec.get("relationships") or [])
    order, cycle = _topo_sort(deps)

    # v4.13: cycle-breaking via deferred FK
    # When entities have circular FKs (User ↔ Profile, common in legacy
    # systems), the original behaviour was hard-fail. New behaviour:
    # automatically downgrade ONE FK to nullable, slice the rest normally,
    # and emit a "deferred_fk" instruction the orchestrator turns into a
    # secondary migration after initial tables exist.
    #
    # Strategy:
    #   1. Identify the "back edge" — the cycle's lexicographically later
    #      entity's FK to the earlier one. That's the FK we defer.
    #   2. Drop the back edge from the dependency graph; rerun topo sort.
    #   3. Emit `deferred_fks` field on the result so the orchestrator
    #      knows which FK to make nullable initially + apply via
    #      secondary migration.
    deferred_fks: List[Dict[str, str]] = []
    cycle_breaking_applied = False

    if cycle:
        # Sort cycle members alphabetically; back edge runs from LAST to FIRST.
        cycle_sorted = sorted(cycle)
        back_from = cycle_sorted[-1]   # later entity (e.g. "Profile")
        back_to   = cycle_sorted[0]    # earlier entity (e.g. "User")
        # Drop the cycle dep (back_from -> back_to)
        if back_to in deps.get(back_from, set()):
            deps[back_from].discard(back_to)
            cycle_breaking_applied = True
            deferred_fks.append({
                "from_entity": _pascal_to_snake(back_from),
                "to_entity": _pascal_to_snake(back_to),
                "rationale": (
                    f"Detected FK cycle between "
                    f"{', '.join(cycle_sorted)}. Made the "
                    f"{back_from}.{_pascal_to_snake(back_to)}_id column "
                    f"nullable initially; apply NOT NULL constraint via "
                    f"a secondary migration after both tables exist."
                ),
                "migration_stage": "6.7-deferred-fk",
            })
            # Re-run topo sort with the cycle broken
            order, cycle = _topo_sort(deps)

    if cycle:
        # Still a cycle (3-way or larger that one edge-drop can't fix) —
        # surface to the user as before.
        return {
            "feature": spec.get("feature", ""),
            "framework": spec.get("framework", "fastapi"),
            "total_slices": 0,
            "slices": [],
            "cycle_detected": True,
            "cycle_members": cycle,
            "skip_reason": "fk_cycle_detected_multi_edge",
            "note": ("Tried to break the cycle by deferring one FK but "
                      "the cycle has 3+ edges. Redesign the relationships."),
        }

    total = len(order)
    slices: List[Dict] = []
    for i, pascal in enumerate(order, start=1):
        ent = next(e for e in new_entities if e.get("name") == pascal)
        snake = ent.get("snake_name") or pascal.lower()
        sliced_spec = _sliced_spec(spec, pascal)
        slice_path = None
        if out_dir is not None:
            out_dir.mkdir(parents=True, exist_ok=True)
            slice_path = out_dir / f"osp-slice-{i}-{snake}.json"
            slice_path.write_text(json.dumps(sliced_spec, indent=2),
                                   encoding="utf-8")
        slices.append({
            "slice_number": i,
            "entity": pascal,
            "snake_name": snake,
            "depends_on": sorted(deps.get(pascal, [])),
            "commit_subject": _commit_subject(
                spec.get("feature", "feature"), pascal, i, total),
            "sliced_spec_path": str(slice_path) if slice_path else None,
        })

    return {
        "feature": spec.get("feature", ""),
        "framework": spec.get("framework", "fastapi"),
        "total_slices": total,
        "slices": slices,
        "cycle_detected": False,
        "cycle_members": [],
        "cycle_breaking_applied": cycle_breaking_applied,
        "deferred_fks": deferred_fks,
    }


# ─── CLI ───────────────────────────────────────────────────────────────────

def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        description="Plan an --incremental /one-shot run by topo-sorting entities."
    )
    p.add_argument("--spec", required=True, type=Path)
    p.add_argument("--out-dir", type=Path, default=None,
                   help="If set, write per-slice spec JSON files into this dir.")
    p.add_argument("--validate", action="store_true",
                   help="Just check for FK cycles; exit 2 if found.")
    args = p.parse_args(argv if argv is not None else sys.argv[1:])

    if not args.spec.exists():
        print(f"spec not found: {args.spec}", file=sys.stderr)
        return 1

    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    result = plan(spec, out_dir=args.out_dir)

    if args.validate:
        if result["cycle_detected"]:
            print(f"FK cycle detected among: {result['cycle_members']}",
                  file=sys.stderr)
            return 2
        return 0

    print(json.dumps(result, indent=2))
    return 2 if result["cycle_detected"] else 0


if __name__ == "__main__":
    sys.exit(main())
