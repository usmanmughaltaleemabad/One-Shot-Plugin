#!/usr/bin/env python3
"""
Anti-Rationalization Check — v1.0.0  (closes the "compliance blindness"
gap in multi-agent reviewers)

Even with the doubter and the cross-agent consistency check, multi-agent
pipelines stay vulnerable to mutual confirmation bias. The reviewer
glances at the code, infers a "vibe of correctness", and signs off on
style nitpicks. The doubter sees structurally-clean code that satisfies
the contract on the surface and approves it. The critic runs the tests
the implementer wrote — they pass, because the implementer wrote them.

This script makes the bias explicit. The reviewer + critic agents MUST
fill out a "common shortcuts taken" matrix before their PASS verdict
is accepted. We then inspect their answers:

  - If the agent answered every question with "no" or one-line non-
    answers (rubber-stamp pattern), we ESCALATE (verdict = SUSPICIOUS).
  - If the agent flagged at least one shortcut but the implementer's
    final artifact STILL contains the smell, we ESCALATE (verdict =
    NOT_ADDRESSED).
  - Otherwise PROCEED.

The reviewer / critic agents receive an extended prompt that explicitly
asks them to fill the matrix; this script verifies the matrix in their
output. Each question has 1-3 deterministic signals (regex / structure
checks) that catch the shortcut when it's actually present, so the
agent can't fool the check with a generic "no" answer.

CLI:
    anti_rationalization_check.py \\
        --reviewer-output /tmp/osp-reviewer-output.txt \\
        --generated-dir /tmp/osp-out \\
        --json

Exit codes:
    0  reviewer's matrix is honest + actionable (PROCEED)
    1  bad args
    2  matrix incomplete / rubber-stamped / not addressed in code (ESCALATE)

The 8 shortcut questions are inspired by Addy Osmani's
agent-skills/doubt-driven-development "anti-rationalization patterns".
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from lib.base_script import bootstrap_runtime, setup_logging
bootstrap_runtime()
logger = setup_logging(__name__)


# ─── The 8 shortcut questions + deterministic signal patterns ─────────────

@dataclass
class ShortcutCheck:
    question: str
    answer_token: str        # The matrix key the agent must answer
    signal_patterns: List[Tuple[re.Pattern, str]]   # (pattern, where_to_search: "any" | "py" | "test")
    why_it_matters: str
    fix_hint: str


SHORTCUT_CHECKS: List[ShortcutCheck] = [
    ShortcutCheck(
        question="Did the implementer MOCK an integration instead of wiring it?",
        answer_token="mocked_integration",
        signal_patterns=[
            (re.compile(r"\bMock\(|MagicMock\(|@patch\(", re.M), "py"),
            (re.compile(r"\bjest\.mock\(", re.M), "any"),
        ],
        why_it_matters=(
            "Mocking the DB / HTTP client in PRODUCTION code (not just "
            "tests) means the integration was never actually wired up. "
            "Tests will pass; production will crash."
        ),
        fix_hint=(
            "Identify the mock + replace with the real client. If you "
            "genuinely need a mock for env reasons, put it BEHIND a "
            "feature flag and document the constraint."
        ),
    ),
    ShortcutCheck(
        question="Did the implementer bypass error boundaries with a generic `except Exception:`?",
        answer_token="generic_except",
        signal_patterns=[
            (re.compile(r"^\s*except\s+Exception\s*(?::|$)", re.M), "py"),
            (re.compile(r"^\s*except\s*:\s*$", re.M), "py"),
            (re.compile(r"catch\s*\(\s*\w*\s*\)\s*{", re.M), "any"),
        ],
        why_it_matters=(
            "Catching Exception (or bare except) hides bugs. The next "
            "developer can't tell which errors are expected vs which are "
            "real failures swallowed."
        ),
        fix_hint=(
            "Catch the specific exception you expect (e.g. ConnectionError, "
            "ValueError). If you really want to log + re-raise everything, "
            "use `except Exception: logger.exception(...); raise`."
        ),
    ),
    ShortcutCheck(
        question="Did the implementer skip boundary-value tests (empty, 0, None, max-int, unicode)?",
        answer_token="missing_boundary_tests",
        signal_patterns=[
            # Heuristic: test files contain only the happy path —
            # look for None/empty/zero/maxint test cases
            (re.compile(r"def test_.*_(?:empty|null|none|zero|negative|max|unicode|boundary)",
                         re.M), "test"),
        ],
        why_it_matters=(
            "AI test-writers love asserting 'create returns 201' without "
            "checking what happens when the input is empty / None / "
            "negative / Unicode. Production users hit these every day."
        ),
        fix_hint=(
            "Add at least one test per: empty string, None, 0, negative "
            "number, very-long-input. Should fail loudly with a clear "
            "error, never silently 'succeed' with garbage state."
        ),
    ),
    ShortcutCheck(
        question="Did the implementer write tests that only check HTTP status, not the persisted state?",
        answer_token="status_only_tests",
        signal_patterns=[
            # status-only tests don't query the DB after the operation
            (re.compile(
                r"def test_\w+_create.*?\n(?:.*\n){0,15}.*assert.*status_code\s*==\s*201"
                r"(?!.*?(?:db\.|query\(|.objects\.|select\())",
                re.S), "test"),
        ],
        why_it_matters=(
            "Asserting POST → 201 without then GETing the resource (or "
            "querying the DB) means the test would pass even if the "
            "endpoint accepted-but-ignored the payload."
        ),
        fix_hint=(
            "Every create-path test must also: re-fetch the row + assert "
            "the persisted values match the input. 'Returned 201' is half "
            "the contract; 'and the data is in the DB' is the other half."
        ),
    ),
    ShortcutCheck(
        question="Did the implementer store secrets / tokens / keys in source instead of env?",
        answer_token="hardcoded_secret",
        signal_patterns=[
            (re.compile(r"""(?:API_KEY|SECRET|TOKEN|PASSWORD)\s*=\s*['"][^'"]{6,}['"]""",
                         re.M), "py"),
        ],
        why_it_matters="Hardcoded credentials are a classified incident in any audit.",
        fix_hint=(
            "Move to os.environ['NAME'] (or .env.example). If you genuinely "
            "needed a placeholder, prefix with 'CHANGEME-' so audits catch "
            "it."
        ),
    ),
    ShortcutCheck(
        question="Did the implementer commit `print()` debug statements?",
        answer_token="left_print_statements",
        signal_patterns=[
            # print() in non-test code (test files often use print)
            (re.compile(r"^\s*print\s*\(", re.M), "py"),
        ],
        why_it_matters=(
            "print() in prod code clutters logs + leaks data + bypasses "
            "the project's logger config (log levels, structured output)."
        ),
        fix_hint=(
            "Replace with `logger.debug(...)` (matching the project's "
            "logging convention). Remove entirely if the original purpose "
            "was 'just to check this fires'."
        ),
    ),
    ShortcutCheck(
        question="Did the implementer leave a TODO / FIXME / XXX in the generated code?",
        answer_token="todo_left_behind",
        signal_patterns=[
            (re.compile(r"\b(?:TODO|FIXME|XXX|HACK)\b", re.M), "any"),
        ],
        why_it_matters=(
            "TODOs in fresh-generated code mean the agent recognised "
            "incompleteness but signed off anyway. They become permanent "
            "debt the moment the PR merges."
        ),
        fix_hint=(
            "Either fix the TODO before shipping, or convert it to a "
            "tracked GitHub issue + delete the comment. Don't ship "
            "TODOs from your own generation pass."
        ),
    ),
    ShortcutCheck(
        question="Did the implementer ignore the `test_contract.auth` value (skipping auth checks)?",
        answer_token="ignored_test_contract_auth",
        signal_patterns=[
            # If test_contract.auth is "jwt" but no Depends(auth_…) or
            # @requires_auth in routes
            (re.compile(r"Depends\(auth", re.M), "py"),
            (re.compile(r"@requires_auth|@auth_required|@login_required", re.M), "py"),
        ],
        why_it_matters=(
            "test_contract.auth='jwt' but routes don't wire auth → "
            "production auth gap. Tests pass because they don't simulate "
            "the auth header either."
        ),
        fix_hint=(
            "Wire the auth dependency on every protected route + add a "
            "test that asserts 401 without the header."
        ),
    ),
]


# ─── Matrix extraction ─────────────────────────────────────────────────────

_MATRIX_HEADER = re.compile(
    r"(?:ANTI[-_ ]?RATIONALIZATION|SHORTCUT[-_ ]?CHECK|COMMON SHORTCUTS).*?(?=\n)",
    re.I,
)
# Question line format expected:
#   - mocked_integration: no
#   - generic_except: yes / fixed in <file>:<line>
_ANSWER_LINE = re.compile(
    r"(?:^|\n)\s*[-*]?\s*(\w+):\s*(yes|no|n/a)\b(.*?)(?=\n\s*[-*]|\Z)",
    re.I | re.S,
)


def parse_matrix(reviewer_text: str) -> Dict[str, Dict[str, str]]:
    """Extract the agent's answers. Returns {token: {answer: 'yes'|'no'|'n/a',
    note: text after the answer}}. If the matrix is absent, returns {}."""
    if not _MATRIX_HEADER.search(reviewer_text):
        # Lenient: maybe the agent put the answers without the header
        if not _ANSWER_LINE.search(reviewer_text):
            return {}
    out: Dict[str, Dict[str, str]] = {}
    for m in _ANSWER_LINE.finditer(reviewer_text):
        token = m.group(1).strip().lower()
        ans = m.group(2).strip().lower()
        note = m.group(3).strip()
        out[token] = {"answer": ans, "note": note[:200]}
    return out


# ─── Signal detection in the actual generated code ────────────────────────

def _iter_files(generated_dir: Path, kind: str) -> List[Path]:
    """kind = 'py' | 'test' | 'any'. Skips __pycache__."""
    out: List[Path] = []
    for p in generated_dir.rglob("*"):
        if not p.is_file():
            continue
        if any(part in {"__pycache__", ".git"} for part in p.parts):
            continue
        suffix = p.suffix.lower()
        if kind == "py" and suffix != ".py":
            continue
        if kind == "any" and suffix not in (".py", ".js", ".ts", ".go", ".java"):
            continue
        is_test = (p.name.startswith("test_") or p.name.endswith("_test.py")
                    or "tests" in p.parts or p.name.endswith(".test.ts")
                    or p.name.endswith(".spec.ts"))
        if kind == "test" and not is_test:
            continue
        if kind == "py" and is_test:
            continue   # py kind = production only
        out.append(p)
    return out


def detect_in_code(check: ShortcutCheck, generated_dir: Path) -> List[str]:
    """Return list of 'file:line' matches in the generated code that
    indicate the shortcut WAS taken (regardless of what the agent claimed)."""
    hits: List[str] = []
    for pattern, where in check.signal_patterns:
        for path in _iter_files(generated_dir, where):
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            for m in pattern.finditer(text):
                lineno = text.count("\n", 0, m.start()) + 1
                hits.append(f"{path.relative_to(generated_dir)}:{lineno}")
    return hits


def detect_boundary_tests(check: ShortcutCheck, generated_dir: Path) -> List[str]:
    """Special case for the boundary-tests check: signal is POSITIVE
    (presence = good); we want to flag if MISSING.

    BUT: if the generated dir has NO test files at all, we can't tell
    if boundary tests are missing because the agent skipped them OR
    because tests aren't this stage's concern (e.g. only models.py
    was generated). Return [] (no evidence) in that case — the
    test-author agent's separate output handles test coverage."""
    test_files = list(_iter_files(generated_dir, "test"))
    if not test_files:
        return []   # no test files at all → can't infer skip vs not-this-stage

    found = False
    for pattern, _ in check.signal_patterns:
        for path in test_files:
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if pattern.search(text):
                found = True
                break
        if found:
            break
    if found:
        return []   # boundary tests EXIST → no shortcut
    return ["<test files exist but no boundary-value test names>"]


# ─── Audit logic ──────────────────────────────────────────────────────────

@dataclass
class CheckResult:
    token: str
    question: str
    agent_answer: Optional[str]
    code_evidence: List[str]
    verdict: str          # OK | RUBBER_STAMP | LIED | UNDISCLOSED | MISSING_TESTS
    fix_hint: str

    def to_dict(self) -> Dict:
        return asdict(self)


def audit(reviewer_text: str, generated_dir: Path) -> Dict[str, Any]:
    matrix = parse_matrix(reviewer_text)
    results: List[CheckResult] = []
    for check in SHORTCUT_CHECKS:
        # Detect in code (positive = bad except for boundary-tests check)
        if check.answer_token == "missing_boundary_tests":
            evidence = detect_boundary_tests(check, generated_dir)
        else:
            evidence = detect_in_code(check, generated_dir)

        ans = matrix.get(check.answer_token, {}).get("answer")

        # Verdict per row
        if ans is None:
            verdict = "RUBBER_STAMP" if evidence else "UNDISCLOSED"
        elif evidence:
            # Code shows the shortcut WAS taken
            if ans == "no":
                verdict = "LIED"     # Agent denied but evidence says otherwise
            elif ans == "yes":
                # Did they note WHERE / fix? — sanity check for substance
                note = matrix.get(check.answer_token, {}).get("note", "")
                if len(note.strip()) < 5:
                    verdict = "UNDISCLOSED"
                else:
                    verdict = "OK"
            else:   # n/a
                verdict = "LIED" if evidence else "OK"
        else:
            verdict = "OK"

        results.append(CheckResult(
            token=check.answer_token,
            question=check.question,
            agent_answer=ans,
            code_evidence=evidence[:5],   # cap for output size
            verdict=verdict,
            fix_hint=check.fix_hint if verdict != "OK" else "",
        ))

    # Overall: if the matrix is completely missing, escalate to RUBBER_STAMP
    if not matrix:
        overall = "RUBBER_STAMP"
        summary = ("reviewer/critic output contains no anti-rationalization "
                    "matrix at all — likely passive rubber-stamping")
    else:
        bad = [r for r in results if r.verdict != "OK"]
        if not bad:
            overall = "CLEAN"
            summary = "all 8 anti-rationalization checks pass"
        elif any(r.verdict == "LIED" for r in results):
            overall = "ESCALATE"
            summary = (f"reviewer answered 'no' to {sum(1 for r in results if r.verdict == 'LIED')} "
                        f"question(s) but code shows the shortcut WAS taken")
        else:
            overall = "FLAGGED"
            summary = (f"{len(bad)} of 8 shortcut categories have issues")

    return {
        "overall_verdict": overall,
        "summary": summary,
        "matrix_present": bool(matrix),
        "checks": [r.to_dict() for r in results],
    }


# ─── CLI ───────────────────────────────────────────────────────────────────

def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        description="Verify reviewer/critic anti-rationalization matrix "
                    "against deterministic evidence in the generated code."
    )
    p.add_argument("--reviewer-output", required=True, type=Path,
                   help="Path to the reviewer/critic agent's raw output (text)")
    p.add_argument("--generated-dir", required=True, type=Path,
                   help="Directory containing the generated artifacts")
    p.add_argument("--json", action="store_true")
    p.add_argument("--strict", action="store_true",
                   help="Exit 2 on FLAGGED as well as ESCALATE/RUBBER_STAMP")
    args = p.parse_args(argv if argv is not None else sys.argv[1:])

    if not args.reviewer_output.exists():
        print(f"reviewer output not found: {args.reviewer_output}", file=sys.stderr)
        return 1
    if not args.generated_dir.exists():
        print(f"generated dir not found: {args.generated_dir}", file=sys.stderr)
        return 1

    reviewer_text = args.reviewer_output.read_text(encoding="utf-8", errors="replace")
    result = audit(reviewer_text, args.generated_dir)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"ANTI-RATIONALIZATION — {result['overall_verdict']}")
        print(f"  {result['summary']}")
        print()
        for c in result["checks"]:
            marker = {"OK": "[OK]", "RUBBER_STAMP": "[STAMP]", "LIED": "[LIED]",
                       "UNDISCLOSED": "[hide]", "MISSING_TESTS": "[gap]"}.get(
                c["verdict"], "[?]")
            print(f"  {marker:9} {c['token']:30}  answer={c['agent_answer']}")
            if c["code_evidence"]:
                for e in c["code_evidence"][:3]:
                    print(f"           evidence: {e}")
            if c["fix_hint"]:
                print(f"           fix: {c['fix_hint']}")

    if result["overall_verdict"] in ("RUBBER_STAMP", "ESCALATE"):
        return 2
    if args.strict and result["overall_verdict"] == "FLAGGED":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
