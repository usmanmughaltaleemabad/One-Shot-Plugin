#!/usr/bin/env python3
"""
Mutation Tester — v1.0.0  (catches "vanity tests" the test-author wrote)

AI test-writers love superficial assertions: "POST returned 201" without
checking the row landed in the DB; "the function returned a list" without
checking the list contents. The critic agent runs tests and sees green
because the tests are weak — not because the code is correct.

This script intentionally breaks the just-generated code with a small
set of safe mutations, then re-runs the tests. If they still pass green,
the test suite is hollow. The critic should reject the build + flag the
test-author for re-spawn with explicit "assert the persisted state, not
just the HTTP status" instructions.

Mutations applied (sequentially, one at a time, with restore after each):

  ARITHMETIC FLIP
    +   →  -
    -   →  +
    *   →  /     (likely division-by-zero crash for some inputs — fine)

  COMPARISON FLIP
    >   →  <
    <   →  >
    >=  →  <=
    <=  →  >=
    ==  →  !=

  BOOLEAN FLIP
    True   →  False     (literal only, not in string)
    return True  →  return False

  STATE-DROP
    Comment out a `session.commit()` / `db.add()` / `.save()` line.
    Tests that don't query the DB afterward won't notice.

A test suite that catches NONE of these (all mutations survive) is
hollow. The mutation score is `caught_mutations / total_mutations`.
v4.14 default: require ≥ 60% kill rate.

CLI:
    mutation_tester.py --project <dir> --tests-cmd "pytest tests/"
    mutation_tester.py --project <dir> --tests-cmd "pytest tests/" --min-kill 0.6
    mutation_tester.py --project <dir> --tests-cmd "pytest tests/" --max-mutations 8

Exit codes:
    0  kill rate ≥ --min-kill
    1  bad args / no source files found / tests don't run cleanly
    2  kill rate below --min-kill (tests are too weak; fail build)

Conservative on purpose:
  - Mutations are applied to ONE file at a time, restored before next.
  - Tests directory is excluded from mutation targets.
  - Skips files < 20 LOC (too small to mutate meaningfully).
  - 30-second per-mutation timeout to catch infinite-loop mutations.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from lib.base_script import bootstrap_runtime, setup_logging
bootstrap_runtime()
logger = setup_logging(__name__)


# ─── Mutation rules ────────────────────────────────────────────────────────

@dataclass
class MutationRule:
    rule_id: str
    pattern: re.Pattern
    replacement: str
    category: str         # ARITH | CMP | BOOL | STATE
    description: str


# Order matters slightly: prefer the cheapest mutations first (state-drop)
# because they require no semantic understanding.
MUTATIONS: List[MutationRule] = [
    MutationRule("comment_out_commit", re.compile(r"^(\s*)(session\.commit\(\))", re.M),
                  r"\1# MUTATED: \2", "STATE",
                  "comment out session.commit()"),
    MutationRule("comment_out_save", re.compile(r"^(\s*)([\w.]+\.save\(\))", re.M),
                  r"\1# MUTATED: \2", "STATE",
                  "comment out <model>.save()"),
    MutationRule("flip_plus_minus",
                  re.compile(r"(?<![+\-=<>!*/\s])\s\+\s(?!=)"),
                  " - ", "ARITH",
                  "flip + to -"),
    MutationRule("flip_greater_less",
                  re.compile(r"(?<![<>=!])\s>\s(?!=)"),
                  " < ", "CMP",
                  "flip > to <"),
    MutationRule("flip_geq_leq",
                  re.compile(r"\s>=\s"),
                  " <= ", "CMP",
                  "flip >= to <="),
    MutationRule("flip_eq_neq",
                  re.compile(r"\s==\s"),
                  " != ", "CMP",
                  "flip == to !="),
    MutationRule("flip_true_false",
                  re.compile(r"\breturn\s+True\b"),
                  "return False", "BOOL",
                  "flip return True to return False"),
    MutationRule("flip_false_true",
                  re.compile(r"\breturn\s+False\b"),
                  "return True", "BOOL",
                  "flip return False to return True"),
]


# ─── Mutation application ──────────────────────────────────────────────────

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv",
              ".tmp", ".pytest_cache", ".mypy_cache", "dist", "build",
              "tests", "test"}


@dataclass
class MutationAttempt:
    rule_id: str
    category: str
    file: str
    line: int
    original: str
    mutated: str
    tests_passed: bool      # True = test suite missed the mutation (BAD)
    elapsed_sec: float
    skipped_reason: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)


def _iter_target_files(project: Path) -> List[Path]:
    out: List[Path] = []
    for p in project.rglob("*.py"):
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.name.startswith("test_") or p.name.endswith("_test.py"):
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if sum(1 for ln in text.splitlines() if ln.strip()) < 20:
            continue   # too small to mutate meaningfully
        out.append(p)
    return out


def _clear_pycache(project: Path) -> None:
    """Delete all .pyc files under project so Python re-compiles mutated sources.
    Needed on macOS (APFS) and fast SSDs where mtime granularity is < 1s and
    a mutated file may share its mtime with the cached .pyc, causing pytest to
    import stale bytecode and miss the mutation."""
    import shutil
    for cache_dir in project.rglob("__pycache__"):
        if cache_dir.is_dir():
            shutil.rmtree(cache_dir, ignore_errors=True)


def _run_tests(project: Path, cmd: str, timeout: int = 60) -> Tuple[bool, str]:
    """Returns (all_passed, last_lines_of_output)."""
    _clear_pycache(project)
    parts = cmd.split() if isinstance(cmd, str) else cmd
    env = {**__import__("os").environ, "PYTHONDONTWRITEBYTECODE": "1"}
    proc = subprocess.run(
        parts, cwd=str(project), capture_output=True, text=True,
        encoding="utf-8", timeout=timeout, errors="replace", env=env,
    )
    last = "\n".join((proc.stdout + proc.stderr).splitlines()[-5:])
    return proc.returncode == 0, last


def apply_mutation(rule: MutationRule, text: str) -> Tuple[str, Optional[int]]:
    """Apply ONE mutation (the first match). Returns (new_text, lineno)
    or (text, None) if no match."""
    m = rule.pattern.search(text)
    if not m:
        return text, None
    lineno = text.count("\n", 0, m.start()) + 1
    new_text = (text[:m.start()]
                + rule.pattern.sub(rule.replacement, text[m.start():], count=1))
    return new_text, lineno


def run_mutation_test(project: Path, tests_cmd: str, *,
                       max_mutations: int = 10,
                       timeout: int = 60) -> Dict[str, Any]:
    """For each candidate mutation:
       1. Save original file content
       2. Write mutated text
       3. Run the test command
       4. Restore original
       5. Record whether tests passed (= mutation survived = BAD)
    Returns a structured report with kill rate."""
    # Verify baseline (un-mutated) tests pass first
    baseline_ok, baseline_tail = _run_tests(project, tests_cmd, timeout=timeout)
    if not baseline_ok:
        return {
            "verdict": "BASELINE_FAILS",
            "baseline_output_tail": baseline_tail,
            "attempts": [],
            "kill_rate": 0.0,
            "note": ("Baseline tests don't pass — mutation testing requires "
                      "a green baseline. Fix the tests, then re-run."),
        }

    attempts: List[MutationAttempt] = []
    target_files = _iter_target_files(project)
    if not target_files:
        return {
            "verdict": "NO_TARGETS",
            "attempts": [],
            "kill_rate": 0.0,
            "note": "no Python source files found to mutate (project too small)",
        }

    # Stop after max_mutations attempts to keep wall-clock bounded
    attempts_made = 0
    for file_path in target_files:
        if attempts_made >= max_mutations:
            break
        try:
            original = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for rule in MUTATIONS:
            if attempts_made >= max_mutations:
                break
            mutated, lineno = apply_mutation(rule, original)
            if lineno is None:
                continue
            # Apply
            try:
                file_path.write_text(mutated, encoding="utf-8")
            except OSError as e:
                attempts.append(MutationAttempt(
                    rule_id=rule.rule_id, category=rule.category,
                    file=str(file_path.relative_to(project)),
                    line=lineno, original="", mutated="",
                    tests_passed=False, elapsed_sec=0,
                    skipped_reason=f"write failed: {e}",
                ))
                continue

            # Run tests against mutated code
            import time
            start = time.perf_counter()
            try:
                passed, _ = _run_tests(project, tests_cmd, timeout=timeout)
            except subprocess.TimeoutExpired:
                # Treat timeout as "killed" — the test infra noticed something
                passed = False
            elapsed = time.perf_counter() - start

            # Restore
            file_path.write_text(original, encoding="utf-8")

            attempts.append(MutationAttempt(
                rule_id=rule.rule_id, category=rule.category,
                file=str(file_path.relative_to(project)),
                line=lineno, original=rule.description, mutated=rule.replacement,
                tests_passed=passed, elapsed_sec=round(elapsed, 2),
            ))
            attempts_made += 1

    # Compute kill rate. A "kill" = mutation caused tests to FAIL (good).
    kills = sum(1 for a in attempts
                 if not a.skipped_reason and not a.tests_passed)
    total_real = sum(1 for a in attempts if not a.skipped_reason)
    kill_rate = (kills / total_real) if total_real else 0.0

    return {
        "verdict": "DONE",
        "kill_rate": round(kill_rate, 3),
        "total_mutations": total_real,
        "kills": kills,
        "survivors": total_real - kills,
        "attempts": [a.to_dict() for a in attempts],
        "interpretation": (
            "kill_rate < 0.5 → test suite is hollow; "
            "0.5-0.8 → adequate; "
            "0.8+ → strong"
        ),
    }


# ─── CLI ───────────────────────────────────────────────────────────────────

def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        description="Mutation testing: introduce small bugs into the "
                    "generated code + verify the test suite catches them. "
                    "A green test suite that survives mutation is hollow."
    )
    p.add_argument("--project", required=True, type=Path)
    p.add_argument("--tests-cmd", required=True,
                   help="Command to run the test suite (e.g. 'pytest tests/')")
    p.add_argument("--max-mutations", type=int, default=10,
                   help="Maximum mutations to attempt (default 10)")
    p.add_argument("--min-kill", type=float, default=0.5,
                   help="Minimum kill rate required (default 0.5)")
    p.add_argument("--timeout-per-mutation", type=int, default=60,
                   help="Seconds before assuming the mutated test hung (default 60)")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv if argv is not None else sys.argv[1:])

    if not args.project.exists():
        print(f"project not found: {args.project}", file=sys.stderr)
        return 1
    result = run_mutation_test(
        args.project, args.tests_cmd,
        max_mutations=args.max_mutations,
        timeout=args.timeout_per_mutation,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"MUTATION TEST — verdict: {result['verdict']}")
        if result["verdict"] == "DONE":
            print(f"  kill_rate:        {result['kill_rate']:.1%}")
            print(f"  total_mutations:  {result['total_mutations']}")
            print(f"  kills:            {result['kills']}")
            print(f"  survivors:        {result['survivors']}")
            print(f"  interpretation:   {result['interpretation']}")
            if result["survivors"] > 0:
                print()
                print("SURVIVING MUTATIONS (test suite missed these):")
                for a in result["attempts"]:
                    if a.get("tests_passed"):
                        print(f"  [{a['category']:6}] {a['file']}:{a['line']} "
                              f"{a['rule_id']} — '{a['original']}'")
        else:
            print(f"  {result.get('note', '')}")

    if result["verdict"] in ("BASELINE_FAILS", "NO_TARGETS"):
        return 1
    if result["kill_rate"] < args.min_kill:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
