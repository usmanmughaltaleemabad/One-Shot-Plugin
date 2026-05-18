#!/usr/bin/env python3
"""
Cross-Agent Consistency Checker — v1.0.0  (Stage 5.7 — closes Risk #1)

Risk: when 10 different AI agents talk to each other, pass specs, and
write code in parallel, subtle drift accumulates. The architect declares
an invariant; the implementer doesn't enforce it; the reviewer doesn't
notice; the doubter passes because the contract LOOKS satisfied; the
critic ships because tests are green. Each agent did its job; the
SYSTEM produced a bug.

This stage runs AFTER doubter (Stage 5.5) and BEFORE wirer (Stage 6).
It checks the artifacts ACROSS agents — not within a single agent's
output. Five concrete checks:

  1. INVARIANT_ENFORCED — every invariant from spec.json appears as a
     guard / raise / check in the matching service file
  2. SPEC_ATTRS_MATCH_MODEL — every attribute in spec.json's entity
     definition has a corresponding Column / Field / @Column in the
     model file
  3. SPEC_RELATIONSHIPS_MATCH_FKS — every relationship in spec.json
     produces an FK column in the child model (or join table)
  4. REVIEWER_FINDINGS_ADDRESSED — if reviewer flagged "missing X" in
     iteration N, file content in iteration N+1 contains X
  5. DOUBTER_FINDINGS_ADDRESSED — same for doubt-driver findings

The first three are intrinsic (spec ↔ code alignment). The last two
are temporal (iteration N+1 actually fixes what iteration N flagged).

Returns a structured report with violations classified by severity. A
single CRITICAL violation is enough to block ship.

CLI:
    cross_agent_consistency.py \\
        --spec /tmp/osp-spec.json \\
        --generated-dir /tmp/osp-out \\
        [--reviewer-verdict /tmp/osp-reviewer.json] \\
        [--doubt-state /tmp/osp-doubt-state.json] \\
        [--json] [--strict]

Exit codes:
    0  no violations OR only WARN findings
    1  bad args / missing inputs
    2  any CRITICAL violation (--strict: also any WARN)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from lib.base_script import bootstrap_runtime, setup_logging
bootstrap_runtime()
logger = setup_logging(__name__)


@dataclass
class Violation:
    rule: str
    severity: str          # CRITICAL | WARN | INFO
    where: str
    what: str
    why_it_matters: str
    fix_hint: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


# ─── Spec ↔ model alignment ────────────────────────────────────────────────

def _find_model_file(snake_name: str, generated_dir: Path) -> Optional[Path]:
    candidates = [
        generated_dir / snake_name / "models.py",
        generated_dir / snake_name / "model.py",
        generated_dir / snake_name / "entity.py",
        generated_dir / snake_name / f"{snake_name}.go",
    ]
    for p in candidates:
        if p.exists():
            return p
    # Java: look for capitalized name
    cap = "".join(p.capitalize() for p in snake_name.split("_"))
    java_candidates = list(generated_dir.rglob(f"{cap}.java"))
    if java_candidates:
        return java_candidates[0]
    # NestJS / TS
    ts = generated_dir / "src" / snake_name.replace("_", "-")
    if ts.exists():
        ent = ts / "entities" / f"{snake_name.replace('_', '-')}.entity.ts"
        if ent.exists():
            return ent
    return None


def _find_service_file(snake_name: str, generated_dir: Path) -> Optional[Path]:
    candidates = [
        generated_dir / snake_name / "service.py",
        generated_dir / snake_name / "services.py",
        generated_dir / snake_name / "service.go",
    ]
    for p in candidates:
        if p.exists():
            return p
    cap = "".join(p.capitalize() for p in snake_name.split("_"))
    java_candidates = list(generated_dir.rglob(f"{cap}Service.java"))
    if java_candidates:
        return java_candidates[0]
    ts = generated_dir / "src" / snake_name.replace("_", "-")
    if ts.exists():
        svc = ts / f"{snake_name.replace('_', '-')}.service.ts"
        if svc.exists():
            return svc
    return None


def _check_attrs_in_model(spec: Dict, generated_dir: Path) -> List[Violation]:
    out: List[Violation] = []
    for entity in spec.get("entities", []):
        if entity.get("action") not in (None, "create"):
            continue
        snake = entity.get("snake_name", entity.get("name", "").lower())
        model_path = _find_model_file(snake, generated_dir)
        if model_path is None:
            out.append(Violation(
                rule="SPEC_ATTRS_MATCH_MODEL", severity="CRITICAL",
                where=f"<missing model for {entity.get('name')}>",
                what=f"No model file found for entity '{entity.get('name')}'",
                why_it_matters="Spec declares entity but no model file emitted "
                                "by implementer — spec ↔ code drift.",
                fix_hint=f"Re-spawn implementer for {snake} model file",
            ))
            continue
        text = model_path.read_text(encoding="utf-8", errors="replace")
        for attr in entity.get("attributes", []):
            attr_name = attr.get("name") if isinstance(attr, dict) else str(attr)
            if not attr_name:
                continue
            if attr_name in ("id", "created_at", "updated_at"):
                continue  # framework-generated
            # Look for the attribute as a Column / Field / @Column / mapped_column
            if attr_name not in text:
                out.append(Violation(
                    rule="SPEC_ATTRS_MATCH_MODEL", severity="CRITICAL",
                    where=str(model_path),
                    what=f"Spec attribute '{attr_name}' missing from {entity.get('name')} model",
                    why_it_matters="Implementer dropped a field declared in the spec — "
                                    "DB will be missing the column.",
                    fix_hint=f"Add '{attr_name}' as a Column / mapped_column / Field",
                ))
    return out


def _check_invariants_in_service(spec: Dict, generated_dir: Path) -> List[Violation]:
    """Every spec.entities[*].invariants entry must produce a guard or
    raise in the entity's service.py."""
    out: List[Violation] = []
    for entity in spec.get("entities", []):
        invariants = entity.get("invariants") or []
        if not invariants:
            continue
        snake = entity.get("snake_name", entity.get("name", "").lower())
        service_path = _find_service_file(snake, generated_dir)
        if service_path is None:
            out.append(Violation(
                rule="INVARIANT_ENFORCED", severity="CRITICAL",
                where=f"<missing service for {entity.get('name')}>",
                what=f"Spec declares {len(invariants)} invariant(s) but "
                     f"no service.py emitted",
                why_it_matters="Invariants in spec.json are contracts the service "
                                "MUST enforce. Without a service file, nothing enforces them.",
                fix_hint=f"Spawn service-author agent for entity {entity.get('name')}",
            ))
            continue
        text = service_path.read_text(encoding="utf-8", errors="replace")
        # Heuristic: each invariant must produce SOME explicit enforcement —
        # we look for `raise`, `if .*:`, `assert`, `validate`, `check_`.
        # If service.py is short (< 20 LOC) it almost certainly doesn't
        # enforce N invariants. If the file is long, we look for raise/if/etc.
        loc = sum(1 for line in text.splitlines() if line.strip())
        raise_count = len(re.findall(r"\braise\s+\w+", text))
        if_count    = len(re.findall(r"\n\s+if\s+", text))
        enforcement_signals = raise_count + (if_count // 2)
        if loc < 30 and len(invariants) > 0:
            out.append(Violation(
                rule="INVARIANT_ENFORCED", severity="CRITICAL",
                where=str(service_path),
                what=f"service.py has only {loc} LOC but spec declares "
                     f"{len(invariants)} invariant(s) — too sparse to enforce them",
                why_it_matters="Invariants are usually 5-20 LOC each (load, check, "
                                "raise). A 30-LOC file can't enforce 2+ invariants honestly.",
                fix_hint="Re-spawn service-author with explicit invariant list",
            ))
        elif enforcement_signals < len(invariants):
            out.append(Violation(
                rule="INVARIANT_ENFORCED", severity="WARN",
                where=str(service_path),
                what=f"service.py has {enforcement_signals} raise/check signal(s) "
                     f"but spec declares {len(invariants)} invariant(s)",
                why_it_matters="Each invariant typically maps to at least one "
                                "raise/check. Lower count suggests under-enforcement.",
                fix_hint="Audit service.py: confirm each invariant has an explicit guard",
            ))
    return out


def _check_fks_for_relationships(spec: Dict, generated_dir: Path) -> List[Violation]:
    out: List[Violation] = []
    for rel in spec.get("relationships") or []:
        kind = rel.get("kind", "has_many")
        from_ent = rel.get("from") or rel.get("from_entity")
        to_ent = rel.get("to") or rel.get("to_entity")
        if not (from_ent and to_ent):
            continue
        # Child carries the FK; FK column name = `{parent}_id`
        if kind == "has_many":
            child, parent = to_ent, from_ent
        elif kind == "belongs_to":
            child, parent = from_ent, to_ent
        else:
            continue
        expected_fk = f"{parent}_id"
        model_path = _find_model_file(child, generated_dir)
        if model_path is None:
            continue  # already flagged by _check_attrs_in_model
        text = model_path.read_text(encoding="utf-8", errors="replace")
        if expected_fk not in text:
            out.append(Violation(
                rule="SPEC_RELATIONSHIPS_MATCH_FKS", severity="CRITICAL",
                where=str(model_path),
                what=f"Relationship '{from_ent} {kind} {to_ent}' declared in "
                     f"spec but FK column '{expected_fk}' missing from {child}/models.py",
                why_it_matters="DB will have no way to link the entities. "
                                "Either the relationship was dropped or the FK "
                                "uses a different name than the implementer expected.",
                fix_hint=f"Add '{expected_fk}' ForeignKey column to {child}/models.py",
            ))
    return out


# ─── Reviewer + doubter follow-through ────────────────────────────────────

def _check_reviewer_follow_through(reviewer_verdict: Optional[Dict],
                                     generated_dir: Path) -> List[Violation]:
    """If the reviewer flagged a finding in iteration N, the file at
    iteration N+1 must contain a fix marker (or simply not contain the
    same flagged pattern any more). We can only check the latter."""
    out: List[Violation] = []
    if not reviewer_verdict:
        return out
    findings = reviewer_verdict.get("findings") or []
    for f in findings:
        # If the reviewer reported a finding and the artifact still
        # matches the flagged 'what' pattern, the implementer didn't fix it.
        severity = f.get("severity", "info").lower()
        if severity not in ("critical", "high", "warning"):
            continue
        where = f.get("where") or f.get("file") or ""
        what = (f.get("what") or "")[:120]
        if not where or not what:
            continue
        # Strip ":42" line suffix
        file_part = where.split(":")[0]
        target = generated_dir / file_part
        if not target.exists():
            continue
        text = target.read_text(encoding="utf-8", errors="replace")
        # Pull a distinctive token from `what` and check still-present
        tokens = re.findall(r"[a-zA-Z_]{4,}", what)[:3]
        if tokens and all(t in text for t in tokens):
            out.append(Violation(
                rule="REVIEWER_FINDINGS_ADDRESSED", severity="WARN",
                where=str(target),
                what=f"Reviewer's flagged tokens ({tokens}) still present after fix",
                why_it_matters="The implementer was re-spawned with this finding but "
                                "the symptom appears unchanged — possible cosmetic-only fix.",
                fix_hint="Re-read the reviewer's finding and the file; confirm the "
                          "fix actually addresses the root cause.",
            ))
    return out


def _check_doubt_follow_through(doubt_state: Optional[Dict]) -> List[Violation]:
    if not doubt_state:
        return []
    out: List[Violation] = []
    artifacts = doubt_state.get("artifacts") or {}
    for path, entry in artifacts.items():
        rounds = entry.get("rounds") or []
        if len(rounds) < 2:
            continue
        final = rounds[-1]
        if final.get("blocking_count", 0) == 0:
            continue
        prior = rounds[-2]
        # If the FINAL round has equal-or-greater blocking count than
        # the prior round, doubter loop hit theater or regression
        if final["blocking_count"] >= prior["blocking_count"]:
            out.append(Violation(
                rule="DOUBTER_FINDINGS_ADDRESSED", severity="WARN",
                where=path,
                what=f"Doubter rounds {len(rounds)-1}->{len(rounds)}: "
                     f"blocking count {prior['blocking_count']} -> "
                     f"{final['blocking_count']} (no reduction)",
                why_it_matters="Doubter raised concerns; implementer's response "
                                "didn't shrink them. Likely doubt-theater or "
                                "regression — shipping is risky.",
                fix_hint="Inspect the artifact + re-spawn implementer with the "
                          "explicit finding list",
            ))
    return out


# ─── Orchestration ─────────────────────────────────────────────────────────

def run(spec: Dict, generated_dir: Path,
        reviewer_verdict: Optional[Dict] = None,
        doubt_state: Optional[Dict] = None) -> Dict:
    violations: List[Violation] = []
    violations += _check_attrs_in_model(spec, generated_dir)
    violations += _check_invariants_in_service(spec, generated_dir)
    violations += _check_fks_for_relationships(spec, generated_dir)
    violations += _check_reviewer_follow_through(reviewer_verdict, generated_dir)
    violations += _check_doubt_follow_through(doubt_state)

    by_severity = {"CRITICAL": 0, "WARN": 0, "INFO": 0}
    for v in violations:
        by_severity[v.severity] = by_severity.get(v.severity, 0) + 1

    if by_severity["CRITICAL"]:
        verdict = "BLOCKED"
    elif by_severity["WARN"]:
        verdict = "READY_WITH_WARN"
    else:
        verdict = "CLEAN"

    return {
        "verdict": verdict,
        "summary": (f"{by_severity['CRITICAL']} CRITICAL, "
                    f"{by_severity['WARN']} WARN, {by_severity['INFO']} INFO"),
        "checks_run": [
            "SPEC_ATTRS_MATCH_MODEL",
            "INVARIANT_ENFORCED",
            "SPEC_RELATIONSHIPS_MATCH_FKS",
            "REVIEWER_FINDINGS_ADDRESSED" if reviewer_verdict else "REVIEWER_FINDINGS_ADDRESSED (skipped — no verdict)",
            "DOUBTER_FINDINGS_ADDRESSED" if doubt_state else "DOUBTER_FINDINGS_ADDRESSED (skipped — no state)",
        ],
        "violations": [v.to_dict() for v in violations],
    }


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        description="Stage 5.7 — cross-agent consistency checker. "
                    "Catches subtle drift between architect / implementer / "
                    "reviewer / doubter that each agent alone can't see."
    )
    p.add_argument("--spec", required=True, type=Path)
    p.add_argument("--generated-dir", required=True, type=Path)
    p.add_argument("--reviewer-verdict", type=Path, default=None,
                   help="Optional: reviewer's JSON verdict for follow-through check")
    p.add_argument("--doubt-state", type=Path, default=None,
                   help="Optional: doubt_driver state file for follow-through check")
    p.add_argument("--json", action="store_true")
    p.add_argument("--strict", action="store_true",
                   help="Exit 2 on WARN as well as CRITICAL")
    args = p.parse_args(argv if argv is not None else sys.argv[1:])

    if not args.spec.exists():
        print(f"spec not found: {args.spec}", file=sys.stderr)
        return 1
    if not args.generated_dir.exists():
        print(f"generated dir not found: {args.generated_dir}", file=sys.stderr)
        return 1
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    reviewer = None
    if args.reviewer_verdict and args.reviewer_verdict.exists():
        reviewer = json.loads(args.reviewer_verdict.read_text(encoding="utf-8"))
    doubt = None
    if args.doubt_state and args.doubt_state.exists():
        doubt = json.loads(args.doubt_state.read_text(encoding="utf-8"))

    result = run(spec, args.generated_dir, reviewer, doubt)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"CROSS-AGENT CONSISTENCY — {result['verdict']}")
        print(f"  {result['summary']}")
        print()
        for v in result["violations"]:
            print(f"  [{v['severity']}] {v['rule']:35} {v['where']}")
            print(f"     {v['what']}")
            print(f"     why: {v['why_it_matters']}")
            if v["fix_hint"]:
                print(f"     fix: {v['fix_hint']}")
            print()

    if result["verdict"] == "BLOCKED":
        return 2
    if args.strict and result["verdict"] == "READY_WITH_WARN":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
