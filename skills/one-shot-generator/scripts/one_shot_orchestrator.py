#!/usr/bin/env python3
"""
One-Shot Orchestrator — v0.8.0  (Tier 1 unified pipeline)

This is the new public entry point that ties together every Tier-1 upgrade:

    1.  understand  →  extract_domain_model       (entities, relationships, intent)
    2.  scan        →  codebase_graph             (existing models, conventions)
    3.  plan        →  reconciled spec            (avoid duplicating existing entities,
                                                  reuse import paths, match style)
    4.  generate    →  phase2/phase3 runners      (per-entity scaffolding)
    5.  verify      →  generate_and_verify        (syntax + template + contract checks)
    6.  wire        →  auto_wirer (dry-run)       (show what would integrate)
    7.  record      →  beads_writer (on failure)  (auto-bead diagnostics)

The orchestrator returns ONE structured report so callers (Claude, CI,
humans) can read a single artefact to understand what happened end to end.

CLI:

    python one_shot_orchestrator.py "Build a shopping cart with line items, \\
        discounts, and inventory holds" --project /path/to/fastapi-shop

    python one_shot_orchestrator.py "add user CRUD" --project ./my-project \\
        --apply       # actually mutate main.py/urls.py
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from lib.base_script import bootstrap_runtime, setup_logging
bootstrap_runtime()

from extract_domain_model import extract as extract_domain_model, DomainModel
from codebase_graph import load_or_build as load_codebase_graph
from existing_codebase_scanner import CodebaseGraph
from generate_and_verify import (
    run_loop as run_verify_loop,
    VerificationReport,
)
from auto_wirer import wire as run_wire, WireReport
from beads_writer import record_failure

logger = setup_logging(__name__)


# ─── Output shape ────────────────────────────────────────────────────────────

@dataclass
class ReconciledEntity:
    entity_name: str
    pascal: str
    plural: str
    status: str               # "new" | "exists"
    existing_file: Optional[str] = None
    attributes: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class OrchestratorReport:
    task: str
    project: Optional[str]
    intent: str
    confidence: float
    domain_entities: List[Dict]
    reconciled_entities: List[ReconciledEntity]
    codebase_summary: Dict[str, Any]
    generation: List[Dict]
    wire: Optional[Dict]
    overall_succeeded: bool
    notes: List[str]
    bead_id: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "task": self.task,
            "project": self.project,
            "intent": self.intent,
            "confidence": round(self.confidence, 3),
            "domain_entities": self.domain_entities,
            "reconciled_entities": [e.to_dict() for e in self.reconciled_entities],
            "codebase_summary": self.codebase_summary,
            "generation": self.generation,
            "wire": self.wire,
            "overall_succeeded": self.overall_succeeded,
            "notes": self.notes,
            "bead_id": self.bead_id,
        }


# ─── Reconciliation ──────────────────────────────────────────────────────────

def reconcile_entities(model: DomainModel,
                       graph: CodebaseGraph) -> List[ReconciledEntity]:
    """Match each requested entity against entities already in the codebase."""
    out: List[ReconciledEntity] = []
    for ent in model.entities:
        existing = graph.find_entity(ent.pascal) or graph.find_entity(ent.name)
        if existing:
            out.append(ReconciledEntity(
                entity_name=ent.name,
                pascal=ent.pascal,
                plural=ent.plural,
                status="exists",
                existing_file=existing.file,
                attributes=[f.to_dict() for f in existing.fields],
            ))
        else:
            out.append(ReconciledEntity(
                entity_name=ent.name,
                pascal=ent.pascal,
                plural=ent.plural,
                status="new",
                attributes=[a.to_dict() for a in ent.attributes],
            ))
    return out


# ─── Phase routing ───────────────────────────────────────────────────────────

def choose_phase(intent: str) -> str:
    """Map an extracted intent onto a generator phase."""
    mapping = {
        "api": "phase2",
        "auth": "phase2",
        "batch": "phase3",
        "realtime": "phase2",     # phase 5 streams not wired yet; fall back
        "feature": "phase2",
        "refactor": "phase2",
    }
    return mapping.get(intent, "phase2")


# ─── Orchestrator ────────────────────────────────────────────────────────────

def orchestrate(*, task: str, project: Optional[str], apply: bool = False,
                max_iterations: int = 2,
                repo_root: Optional[Path] = None) -> OrchestratorReport:
    notes: List[str] = []

    # 1. Understand
    model = extract_domain_model(task)
    notes.append(f"extracted {len(model.entities)} entities "
                 f"(confidence {model.confidence:.2f})")

    # 2. Scan
    if project:
        graph = load_codebase_graph(project)
        notes.append(f"scanned project: {graph.framework}, "
                     f"{len(graph.entities)} existing entities")
    else:
        graph = CodebaseGraph(project_path="", language="unknown",
                              framework="unknown")
        notes.append("no project path provided — generating greenfield")

    # 3. Reconcile
    reconciled = reconcile_entities(model, graph)
    new_count = sum(1 for r in reconciled if r.status == "new")
    exist_count = sum(1 for r in reconciled if r.status == "exists")
    notes.append(f"reconciled: {new_count} new, {exist_count} already present")

    # 4–5. Generate + verify, ONE entity at a time. The phase2 generator
    # is single-resource; the orchestrator loops over every NEW reconciled
    # entity so a request like "shopping cart with line items + discounts"
    # produces routers/tests/docs for every child entity, not just the head.
    phase = choose_phase(model.intent)
    generation_reports: List[Dict] = []
    overall_succeeded = True
    new_entities = [r for r in reconciled if r.status == "new"]
    for ent in new_entities:
        entity_task = f"add {ent.entity_name} CRUD API"
        reports = run_verify_loop(
            task=entity_task,
            project=project or "",
            phase=phase,
            max_iterations=max_iterations,
        )
        for r in reports:
            payload = r.to_dict()
            payload["entity"] = ent.entity_name
            generation_reports.append(payload)
        if reports and not reports[-1].succeeded:
            overall_succeeded = False
    if not new_entities:
        notes.append("no new entities to generate (all already exist)")

    # 6. Wire (dry-run unless apply). Aggregate files across ALL generated
    # entities so the auto-wirer sees every router it should hook up.
    wire_report: Optional[Dict] = None
    if project and generation_reports:
        files_payload: Dict[str, str] = {}
        for gen in generation_reports:
            sandbox_path = Path(gen["sandbox"])
            for path in sandbox_path.rglob("*"):
                if path.is_file():
                    rel = str(path.relative_to(sandbox_path)).replace("\\", "/")
                    try:
                        files_payload[rel] = path.read_text(encoding="utf-8")
                    except Exception:
                        continue
        report = run_wire(project, files_payload,
                          framework=graph.framework if graph.framework != "unknown" else None,
                          dry_run=not apply)
        wire_report = report.to_dict()
        notes.append(f"wire plan: {len(report.actions)} action(s)"
                     + ("" if apply else " (dry-run)"))

    # 7. Record failure as bead (if we have any errors)
    bead_id: Optional[str] = None
    if not overall_succeeded and repo_root is not None:
        last = generation_reports[-1] if generation_reports else {}
        bead = record_failure(
            repo_root=repo_root,
            phase=phase,
            task=task,
            project=project,
            kind="verification_error",
            diagnostics=last.get("diagnostics", []),
        )
        bead_id = bead["id"]
        notes.append(f"recorded bead {bead_id}")

    return OrchestratorReport(
        task=task,
        project=project,
        intent=model.intent,
        confidence=model.confidence,
        domain_entities=[e.to_dict() for e in model.entities],
        reconciled_entities=reconciled,
        codebase_summary={
            "language": graph.language,
            "framework": graph.framework,
            "router_style": graph.router_style,
            "existing_entities": len(graph.entities),
            "imports": {k: v.to_dict() for k, v in graph.imports.items()},
        },
        generation=generation_reports,
        wire=wire_report,
        overall_succeeded=overall_succeeded,
        notes=notes,
        bead_id=bead_id,
    )


# ─── CLI ─────────────────────────────────────────────────────────────────────

def _print_human(report: OrchestratorReport) -> None:
    print("ONE-SHOT ORCHESTRATOR")
    print("═" * 60)
    print(f"  Task:       {report.task}")
    print(f"  Project:    {report.project or '—'}")
    print(f"  Intent:     {report.intent}  (confidence {report.confidence:.2f})")
    print()
    print("UNDERSTOOD ENTITIES")
    for ent in report.domain_entities:
        print(f"  • {ent['pascal']:<22} ({ent['name']})")
    print()
    print("RECONCILED")
    for ent in report.reconciled_entities:
        marker = "🆕 NEW" if ent.status == "new" else f"♻️  EXISTS in {ent.existing_file}"
        print(f"  • {ent.pascal:<22} {marker}")
    print()
    print("CODEBASE SUMMARY")
    cs = report.codebase_summary
    print(f"  {cs['language']}/{cs['framework']}  router: {cs.get('router_style') or '—'}  "
          f"existing entities: {cs['existing_entities']}")
    print()
    if report.generation:
        last = report.generation[-1]
        print(f"GENERATION ({len(report.generation)} iteration(s))")
        print(f"  Sandbox:  {last['sandbox']}")
        print(f"  Files:    {len(last['files_written'])}")
        print(f"  Result:   {'✅ PASS' if last['succeeded'] else '❌ FAIL'}")
        for d in last.get("diagnostics", []):
            line = f"L{d['line']}" if d.get('line') else "—"
            print(f"    [{d['severity']}] {d['file']}:{line}  {d['code']}: {d['message']}")
        print()
    if report.wire:
        print(f"WIRE PLAN ({'APPLIED' if not report.wire['dry_run'] else 'DRY RUN'})")
        for action in report.wire["actions"]:
            print(f"  + {action['file']}: {action['description']}")
        for skip in report.wire["skipped"]:
            print(f"  - {skip}")
        print()
    if report.notes:
        print("NOTES")
        for note in report.notes:
            print(f"  - {note}")
    if report.bead_id:
        print()
        print(f"BEAD: {report.bead_id} recorded for future replay")


def main():
    parser = argparse.ArgumentParser(
        description="One-shot orchestrator: understand → scan → generate → verify → wire"
    )
    parser.add_argument("task", nargs="+", help="Feature description in plain English")
    parser.add_argument("--project", help="Target project path")
    parser.add_argument("--apply", action="store_true",
                        help="Actually mutate the project (default: dry-run wire only)")
    parser.add_argument("--max-iterations", type=int, default=2)
    parser.add_argument("--json", action="store_true",
                        help="Emit machine-readable JSON only")
    parser.add_argument("--repo-root", default=None,
                        help="Plugin repo root (for bead recording)")
    args = parser.parse_args()

    task = " ".join(args.task)
    # Allow @/project shorthand in the task itself, for SKILL.md compatibility
    project = args.project
    if not project:
        m = re.search(r"@(\S+)", task)
        if m:
            project = m.group(1)
            task = (task[:m.start()] + task[m.end():]).strip()

    repo_root = Path(args.repo_root).resolve() if args.repo_root else None
    report = orchestrate(task=task, project=project, apply=args.apply,
                         max_iterations=args.max_iterations,
                         repo_root=repo_root)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, default=str))
    else:
        _print_human(report)
        print()
        print("---JSON---")
        print(json.dumps(report.to_dict(), indent=2, default=str))
    sys.exit(0 if report.overall_succeeded else 2)


if __name__ == "__main__":
    main()
