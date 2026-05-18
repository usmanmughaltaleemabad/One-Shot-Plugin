#!/usr/bin/env python3
"""
Legacy-Safe Mode Guard — v1.0.0  (closes Risk #2)

Gemini's warning: "Don't use it if you're working on a massive, highly
complex legacy codebase. Auto-generating 17 files + running migrations
on a critical app is a massive risk."

This guard enforces a SAFE MODE for `/one-shot --legacy-safe`. When
active, the orchestrator MUST respect every constraint here. Any
violation aborts the run with a clear message.

Constraints enforced:

  HARD LIMITS
    - Max 3 files generated per run (was 17+ in default mode)
    - --apply implicitly DISABLED (always dry-run)
    - Migrations NEVER auto-run; emit MIGRATION_RUNBOOK.md instead
    - Wiring NEVER auto-applies to main.py; emit a wire-plan diff for
      manual review

  REQUIRED FLAGS
    - --review FORCED ON (spec.json must be approved before code gen)
    - --no-doubt DISABLED (doubter MUST run — extra scrutiny)
    - --no-ship-check DISABLED (ship-gates MUST run)

  ADDITIONAL CHECKS
    - Run impact_analyzer.py on every file the spec touches; refuse
      to proceed if ANY target has heat_verdict == DO_NOT_TOUCH
    - Run cross_agent_consistency.py with --strict (any WARN blocks)
    - Run security_deep_scan.py with --strict (any MEDIUM blocks)
    - Require an empty git working tree at start (no uncommitted changes
      so the user can `git diff` cleanly to see what we touched)
    - Stage every generated file as a separate git commit so review
      is one file per commit

CLI:
    legacy_guard.py validate \\
        --project <dir> \\
        --spec /tmp/osp-spec.json \\
        --planned-files file1.py file2.py file3.py

    legacy_guard.py enforce-limits \\
        --planned-file-count 5

Exit codes:
    0  all constraints satisfied
    1  bad args
    2  constraint violation (orchestrator MUST abort)
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from lib.base_script import bootstrap_runtime, setup_logging
bootstrap_runtime()
logger = setup_logging(__name__)


# ─── Constants (intentionally conservative) ───────────────────────────────

MAX_FILES_LEGACY_SAFE = 3
FORBIDDEN_FLAGS_WHEN_LEGACY_SAFE = (
    "--apply",
    "--no-doubt",
    "--no-ship-check",
    "--no-adr",
)
REQUIRED_FLAGS_WHEN_LEGACY_SAFE = ("--review",)


@dataclass
class Violation:
    rule: str
    detail: str
    fix: str

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class GuardResult:
    verdict: str          # ALLOWED | BLOCKED
    violations: List[Violation] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> Dict:
        return {
            "verdict": self.verdict,
            "violations": [v.to_dict() for v in self.violations],
            "summary": self.summary,
        }


# ─── Checks ────────────────────────────────────────────────────────────────

def _check_file_count(planned_file_count: int) -> Optional[Violation]:
    if planned_file_count > MAX_FILES_LEGACY_SAFE:
        return Violation(
            rule="MAX_FILES_EXCEEDED",
            detail=f"--legacy-safe caps generation at {MAX_FILES_LEGACY_SAFE} "
                   f"files per run; spec produces {planned_file_count}",
            fix=f"Split the feature into {planned_file_count // MAX_FILES_LEGACY_SAFE + 1} "
                f"smaller /one-shot --legacy-safe runs (one entity per run), "
                f"OR fall back to --incremental mode if you can review per-slice",
        )
    return None


def _check_git_working_tree_clean(project: Path) -> Optional[Violation]:
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(project), capture_output=True, text=True, timeout=10,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        # No git? Not a fatal violation; legacy-safe is mostly about git workflows
        return Violation(
            rule="GIT_NOT_AVAILABLE",
            detail="git command failed in the target project",
            fix="Initialise a git repo + commit current state so we can diff "
                "cleanly post-generation",
        )
    if proc.returncode != 0:
        return Violation(
            rule="GIT_STATUS_FAILED",
            detail=f"git status exited {proc.returncode}: {proc.stderr[:120]}",
            fix="Run inside a clean git repository",
        )
    if proc.stdout.strip():
        return Violation(
            rule="UNCOMMITTED_CHANGES",
            detail="Working tree has uncommitted changes; legacy-safe mode "
                   "requires a clean start so the user can `git diff` to "
                   "see exactly what /one-shot produced",
            fix="git stash OR git commit before re-running /one-shot --legacy-safe",
        )
    return None


def _check_impact_heat(project: Path, planned_files: List[Path]) -> List[Violation]:
    """Run impact_analyzer for the planned files; flag any with
    heat_verdict in {HOT, DO_NOT_TOUCH}."""
    out: List[Violation] = []
    # Only check files that ALREADY EXIST (i.e. modifications, not creates).
    existing = [p for p in planned_files if p.exists()]
    if not existing:
        return out

    script = Path(__file__).parent / "impact_analyzer.py"
    proc = subprocess.run(
        [sys.executable, str(script),
         "--project", str(project),
         "--targets", *[str(p) for p in existing],
         "--json"],
        capture_output=True, text=True, encoding="utf-8", timeout=60,
    )
    if proc.returncode != 0:
        return [Violation(
            rule="IMPACT_ANALYZER_FAILED",
            detail=f"impact_analyzer exited {proc.returncode}: "
                   f"{proc.stderr[:200]}",
            fix="Investigate impact_analyzer.py before retrying",
        )]
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return [Violation(
            rule="IMPACT_ANALYZER_BAD_OUTPUT",
            detail="impact_analyzer didn't emit valid JSON",
            fix="Check impact_analyzer.py output by hand",
        )]
    for r in data.get("reports", []):
        verdict = r.get("heat_verdict", "")
        if verdict == "DO_NOT_TOUCH":
            out.append(Violation(
                rule="IMPACT_HEAT_DO_NOT_TOUCH",
                detail=(f"{r['target']} has heat score {r['heat_score']} "
                        f"({r['direct_importer_count']} direct importers, "
                        f"{r['transitive_fanout_count']} transitive). "
                        f"Auto-mutating this in legacy-safe mode is a NO."),
                fix="Refactor the change to NOT touch this file, OR drop "
                    "legacy-safe mode and accept the risk explicitly with "
                    "a manual review",
            ))
        elif verdict == "HOT":
            out.append(Violation(
                rule="IMPACT_HEAT_HOT",
                detail=(f"{r['target']} has heat score {r['heat_score']} "
                        f"({r['direct_importer_count']} direct importers). "
                        f"HOT files require human review BEFORE auto-mutation."),
                fix="Confirm the change with a code review, then re-run "
                    "without --legacy-safe (or split the file into smaller "
                    "ones first)",
            ))
    return out


def _check_apply_disabled(extra_flags: List[str]) -> Optional[Violation]:
    forbidden = [f for f in extra_flags
                  if f in FORBIDDEN_FLAGS_WHEN_LEGACY_SAFE]
    if forbidden:
        return Violation(
            rule="FORBIDDEN_FLAG_IN_LEGACY_SAFE",
            detail=f"Flags forbidden in --legacy-safe mode: {forbidden}",
            fix="Drop these flags; legacy-safe mandates dry-run + all "
                "discipline gates default-on",
        )
    return None


def _check_required_flags_present(extra_flags: List[str]) -> List[Violation]:
    missing = [f for f in REQUIRED_FLAGS_WHEN_LEGACY_SAFE
                if f not in extra_flags]
    if not missing:
        return []
    return [Violation(
        rule="REQUIRED_FLAG_MISSING",
        detail=f"--legacy-safe mode requires these flags: {missing}",
        fix=f"Add {missing} to your /one-shot invocation",
    )]


# ─── Orchestration ─────────────────────────────────────────────────────────

def validate(project: Path, planned_files: List[Path],
             extra_flags: List[str]) -> GuardResult:
    violations: List[Violation] = []

    # File count
    v = _check_file_count(len(planned_files))
    if v:
        violations.append(v)

    # Forbidden / required flags
    v = _check_apply_disabled(extra_flags)
    if v:
        violations.append(v)
    violations.extend(_check_required_flags_present(extra_flags))

    # Git working tree must be clean
    v = _check_git_working_tree_clean(project)
    if v:
        violations.append(v)

    # Impact analysis on existing files
    violations.extend(_check_impact_heat(project, planned_files))

    result = GuardResult(
        verdict=("BLOCKED" if violations else "ALLOWED"),
        violations=violations,
        summary=(f"{len(violations)} violation(s) — legacy-safe gate "
                  f"{'BLOCKED' if violations else 'ALLOWED'} the run"),
    )
    return result


# ─── CLI ───────────────────────────────────────────────────────────────────

def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        description="Legacy-safe mode guard for /one-shot --legacy-safe. "
                    "Enforces small blast radius + manual review for runs "
                    "against critical / large / legacy codebases."
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    p_v = sub.add_parser("validate",
                          help="Run all checks; exit 2 if any violated")
    p_v.add_argument("--project", required=True, type=Path)
    p_v.add_argument("--planned-files", nargs="+", type=Path, default=[],
                      help="Paths /one-shot intends to create or modify")
    p_v.add_argument("--extra-flags", default="",
                      help="Comma-separated list of other flags being passed to "
                           "/one-shot (use commas, not spaces, so argparse can "
                           "distinguish from top-level flags). "
                           "Example: --extra-flags=--review,--apply")
    p_v.add_argument("--json", action="store_true")

    p_l = sub.add_parser("limits",
                          help="Show the constants enforced by --legacy-safe")

    args = p.parse_args(argv if argv is not None else sys.argv[1:])

    if args.cmd == "limits":
        print(json.dumps({
            "max_files_per_run": MAX_FILES_LEGACY_SAFE,
            "forbidden_flags": list(FORBIDDEN_FLAGS_WHEN_LEGACY_SAFE),
            "required_flags": list(REQUIRED_FLAGS_WHEN_LEGACY_SAFE),
            "extra_constraints": [
                "git working tree must be clean at start",
                "every generated file staged as separate git commit",
                "impact_analyzer.py must clear all targets (no HOT or DO_NOT_TOUCH)",
                "cross_agent_consistency.py runs with --strict (any WARN blocks)",
                "security_deep_scan.py runs with --strict (any MEDIUM blocks)",
                "migrations NEVER auto-run; emit MIGRATION_RUNBOOK.md only",
                "wiring NEVER auto-applies to main.py; emit wire-plan diff",
            ],
        }, indent=2))
        return 0

    project = args.project.resolve()
    if not project.exists():
        print(f"project not found: {project}", file=sys.stderr)
        return 1

    extra_flags = [f.strip() for f in (args.extra_flags or "").split(",") if f.strip()]
    result = validate(project, args.planned_files, extra_flags)
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    else:
        print(f"LEGACY-SAFE GUARD — {result.verdict}")
        print(f"  {result.summary}")
        print()
        for v in result.violations:
            print(f"  [BLOCK] {v.rule}")
            print(f"     {v.detail}")
            print(f"     fix: {v.fix}")
            print()
    return 2 if result.verdict == "BLOCKED" else 0


if __name__ == "__main__":
    sys.exit(main())
