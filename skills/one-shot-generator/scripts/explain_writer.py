#!/usr/bin/env python3
"""
Explain Writer — v1.0.0  (--explain flag for /one-shot)

Before --apply mutates files, users want to see what's about to happen
in a human-friendly format. A raw diff of 17 files is overwhelming.
This script turns spec.json + scaffold plan + ship-gates verdict into
a markdown executive summary the user can read in 30 seconds.

The summary covers:
  - Feature restatement (what was asked for)
  - Stack detected (so user can spot wrong framework)
  - Files to be created (count + grouped by entity)
  - Files to be modified (main.py wiring, etc.)
  - Migrations to be emitted (alembic / django / flyway)
  - Cost estimate (from cost_budget)
  - Risk flags (HOT files in impact_analyzer, ship-gates failures)
  - Why-it-was-designed-this-way notes (from architect's reasoning)

Inspired by Gemini's review of v4.12: "before developers run --apply,
they want to know exactly what changes are about to hit their hard drive."

CLI:
    explain_writer.py emit \\
        --spec /tmp/osp-spec.json \\
        --plan /tmp/osp-plan.json \\
        [--ship-gates /tmp/osp-ship.json] \\
        [--impact /tmp/osp-impact.json] \\
        [--cost-estimate-usd 0.42] \\
        [--out /tmp/osp-explain.md]

If --out is omitted, prints to stdout.

Exit codes:
    0  summary emitted
    1  bad args / spec missing
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from lib.base_script import bootstrap_runtime, setup_logging
bootstrap_runtime()
logger = setup_logging(__name__)


def _group_files_by_entity(plan: Dict) -> Dict[str, List[Dict]]:
    groups: Dict[str, List[Dict]] = defaultdict(list)
    for f in plan.get("files_to_create", []):
        entity = f.get("entity") or "common"
        groups[entity].append(f)
    return dict(groups)


def render(spec: Dict, plan: Dict, *,
           ship_gates: Optional[Dict] = None,
           impact: Optional[Dict] = None,
           cost_usd: Optional[float] = None) -> str:
    feature = spec.get("feature", "(no feature description)")
    framework = spec.get("framework", "(unknown)")
    entities = spec.get("entities", []) or []
    relationships = spec.get("relationships", []) or []
    test_contract = spec.get("test_contract", {}) or {}

    new_entities = [e for e in entities if e.get("action") in (None, "create")]
    reuse_entities = [e for e in entities if e.get("action") == "reuse"]

    files = plan.get("files_to_create", []) or []
    grouped = _group_files_by_entity(plan)
    wiring = plan.get("wiring_targets", []) or []
    migrations = plan.get("migrations", []) or []

    lines: List[str] = [
        "# 💡 What `/one-shot` is about to do",
        "",
        f"**Feature:** {feature}",
        f"**Framework:** {framework}",
        f"**Cost estimate:** ${cost_usd:.4f}" if cost_usd is not None
            else "**Cost estimate:** (not run)",
        "",
        "---",
        "",
        "## What will be created",
        "",
        f"**{len(files)} file(s)** across **{len(new_entities)} new entit(ies)**"
        + (f", reusing {len(reuse_entities)} existing entit(ies)"
            if reuse_entities else "")
        + ".",
        "",
    ]

    for entity_name, entity_files in grouped.items():
        lines.append(f"### `{entity_name}` ({len(entity_files)} files)")
        lines.append("")
        for f in entity_files:
            lines.append(f"  - `{f.get('path', '?')}`  *({f.get('kind', '?')})*")
        lines.append("")

    if relationships:
        lines += [
            "## Relationships",
            "",
        ]
        for r in relationships:
            kind = r.get("kind", "?")
            from_e = r.get("from") or r.get("from_entity", "?")
            to_e = r.get("to") or r.get("to_entity", "?")
            lines.append(f"  - `{from_e}` `{kind}` `{to_e}` "
                         f"(FK column on `{to_e if kind == 'has_many' else from_e}`)")
        lines.append("")

    if wiring:
        lines += [
            "## Wiring (will mutate ONLY if `--apply`)",
            "",
        ]
        for w in wiring:
            lines.append(f"  - `{w}` will receive `app.include_router(...)` "
                         f"× {len(new_entities)} line(s)")
        lines.append("")

    if migrations:
        lines += [
            "## Migrations",
            "",
        ]
        for m in migrations:
            lines.append(f"  - {m}")
        lines.append("")

    lines += [
        "## Test contract",
        "",
        f"  - **auth:** `{test_contract.get('auth', 'none')}`",
        f"  - **pagination:** `{test_contract.get('pagination', 'list')}`",
        f"  - **errors:** `{test_contract.get('errors', 'domain_envelope')}`",
        "",
    ]

    invariants_total = 0
    for e in new_entities:
        invariants_total += len(e.get("invariants") or [])
    if invariants_total:
        lines += [
            "## Business invariants to enforce",
            "",
            f"**{invariants_total} invariant(s)** declared by the architect;",
            "Stage 2.7 service-author + Stage 5.7 consistency check will",
            "verify these are honestly enforced in `service.py`:",
            "",
        ]
        for e in new_entities:
            for inv in (e.get("invariants") or []):
                lines.append(f"  - **{e.get('name')}**: {inv}")
        lines.append("")

    # Risk flags from ship-gates + impact analyzer
    risk_lines: List[str] = []

    if ship_gates:
        verdict = ship_gates.get("verdict", "?")
        if verdict == "BLOCKED":
            risk_lines.append(
                f"  - 🚨 **ship-gates verdict: BLOCKED** — "
                f"{ship_gates.get('summary', '?')}")
        elif verdict == "READY_WITH_WARN":
            risk_lines.append(
                f"  - ⚠️  ship-gates: WARN — {ship_gates.get('summary', '?')}")

    if impact:
        for r in impact.get("reports", []):
            hv = r.get("heat_verdict", "")
            if hv in ("HOT", "DO_NOT_TOUCH"):
                emoji = "🛑" if hv == "DO_NOT_TOUCH" else "⚠️"
                risk_lines.append(
                    f"  - {emoji}  **{r['target']}**: heat verdict `{hv}` "
                    f"({r.get('direct_importer_count', '?')} direct importers, "
                    f"score {r.get('heat_score', '?')})")

    if risk_lines:
        lines += [
            "## ⚠️  Risk flags",
            "",
            *risk_lines,
            "",
        ]

    lines += [
        "---",
        "",
        "## Next step",
        "",
        "**Review the above. Then choose:**",
        "",
        "  - **Apply** — `git status` will show every change as a separate commit",
        "    ```bash",
        "    /one-shot \"...\" @./project --apply",
        "    ```",
        "  - **Iterate** — modify the spec via `--review` gate, or pass a `--hint`:",
        "    ```bash",
        "    /one-shot \"...\" @./project --review",
        "    ```",
        "  - **Abort** — the dry-run is harmless; close the session and nothing changed.",
        "",
        "  - **Resume later** — the session state is checkpointed; you can",
        "    `--resume` from the last successful stage if you re-run.",
        "",
    ]

    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        description="Render a human-friendly executive summary of what "
                    "/one-shot is about to do, so users can review before --apply."
    )
    sub = p.add_subparsers(dest="cmd", required=True)
    p_e = sub.add_parser("emit", help="Render the summary")
    p_e.add_argument("--spec", required=True, type=Path)
    p_e.add_argument("--plan", required=True, type=Path)
    p_e.add_argument("--ship-gates", type=Path, default=None)
    p_e.add_argument("--impact", type=Path, default=None)
    p_e.add_argument("--cost-estimate-usd", type=float, default=None)
    p_e.add_argument("--out", type=Path, default=None,
                     help="Output path (default: stdout)")
    args = p.parse_args(argv if argv is not None else sys.argv[1:])

    if not args.spec.exists():
        print(f"spec not found: {args.spec}", file=sys.stderr)
        return 1
    if not args.plan.exists():
        print(f"plan not found: {args.plan}", file=sys.stderr)
        return 1
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    ship = (json.loads(args.ship_gates.read_text(encoding="utf-8"))
             if args.ship_gates and args.ship_gates.exists() else None)
    impact = (json.loads(args.impact.read_text(encoding="utf-8"))
               if args.impact and args.impact.exists() else None)
    md = render(spec, plan, ship_gates=ship, impact=impact,
                  cost_usd=args.cost_estimate_usd)
    if args.out:
        args.out.write_text(md, encoding="utf-8")
        print(json.dumps({"status": "written", "out": str(args.out),
                          "chars": len(md)}, indent=2))
    else:
        print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
