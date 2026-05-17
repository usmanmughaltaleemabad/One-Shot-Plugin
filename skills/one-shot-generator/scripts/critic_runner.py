#!/usr/bin/env python3
"""
Critic Runner — v0.9.0  (Tier 2 closed loop)

Actually executes the generated tests in a subprocess and turns the result
into structured diagnostics the orchestrator + critic agent can route on.

This is the "no more assuming green from looking at the code" step. The
critic.md agent calls this script to make its verdict.

The runner is intentionally Python-only for v0.9.0 (pytest + py_compile).
JS/Go test execution is queued for v0.9.1.

CLI:
    # Run every test under a directory
    python critic_runner.py --tests <dir>

    # Run a single test file, surfacing per-test status
    python critic_runner.py --tests <dir> --pattern test_cart_api.py

Exit code:
    0    all tests passed
    2    one or more tests failed
    3    pytest could not even collect (import error, etc.)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional

from lib.base_script import bootstrap_runtime, setup_logging
bootstrap_runtime()

logger = setup_logging(__name__)


# ─── Data shapes ─────────────────────────────────────────────────────────────

@dataclass
class TestOutcome:
    nodeid: str               # tests/test_cart.py::test_create
    outcome: str              # passed | failed | error | skipped
    duration_ms: float = 0.0
    short_traceback: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class CriticReport:
    tests_dir: str
    runner: str               # pytest
    exit_code: int
    passed: int
    failed: int
    errored: int
    skipped: int
    outcomes: List[TestOutcome] = field(default_factory=list)
    stderr_tail: str = ""

    def to_dict(self) -> Dict:
        return {
            "tests_dir": self.tests_dir,
            "runner": self.runner,
            "exit_code": self.exit_code,
            "passed": self.passed,
            "failed": self.failed,
            "errored": self.errored,
            "skipped": self.skipped,
            "outcomes": [o.to_dict() for o in self.outcomes],
            "stderr_tail": self.stderr_tail,
        }

    @property
    def ok(self) -> bool:
        return self.exit_code == 0


# ─── pytest invocation ───────────────────────────────────────────────────────

# pytest verbose output format:
#   tests/test_cart.py::test_create PASSED                 [ 12%]
_PYTEST_OUTCOME_RE = re.compile(
    r"^(?P<nodeid>.+::\S+)\s+(?P<outcome>PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS)\b"
)


def run_pytest(tests_dir: Path, pattern: Optional[str] = None,
               extra_args: Optional[List[str]] = None,
               python_executable: Optional[str] = None) -> CriticReport:
    py = python_executable or sys.executable
    args = [py, "-m", "pytest", str(tests_dir), "-v", "--tb=line",
            "--no-header"]
    if pattern:
        args.extend(["-k", pattern])
    if extra_args:
        args.extend(extra_args)

    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    proc = subprocess.run(args, capture_output=True, text=True,
                          encoding="utf-8", env=env, timeout=180)
    outcomes: List[TestOutcome] = []
    counts = {"passed": 0, "failed": 0, "errored": 0, "skipped": 0}
    for line in (proc.stdout or "").splitlines():
        m = _PYTEST_OUTCOME_RE.match(line.strip())
        if not m:
            continue
        outcome = m.group("outcome").lower()
        # Normalise pytest's vocabulary to our bucket names
        bucket = {"passed": "passed", "failed": "failed", "error": "errored",
                  "skipped": "skipped", "xfail": "skipped", "xpass": "passed"}.get(outcome, outcome)
        counts[bucket] = counts.get(bucket, 0) + 1
        outcomes.append(TestOutcome(nodeid=m.group("nodeid"), outcome=bucket))

    # Collection errors: pytest exits non-zero with no per-test verbose
    # lines when tests fail to import (ModuleNotFoundError, syntax error
    # in test file, etc.). Synthesize an "errored" outcome so the loop
    # can route these to the implementer.
    if proc.returncode != 0 and not outcomes:
        for line in (proc.stdout or "").splitlines():
            if line.startswith("ERROR "):
                summary = line.split(" - ", 1)
                node_part = summary[0].split(" ", 1)[1].strip()
                tb = summary[1].strip() if len(summary) == 2 else ""
                outcomes.append(TestOutcome(
                    nodeid=f"{node_part}::<collection>",
                    outcome="errored",
                    short_traceback=tb,
                ))
                counts["errored"] += 1
        # Walk for "ModuleNotFoundError: No module named ..." anywhere in
        # output and attach to the first errored outcome
        for line in (proc.stdout or "").splitlines():
            if "ModuleNotFoundError" in line or "ImportError" in line:
                if outcomes and not outcomes[0].short_traceback:
                    outcomes[0].short_traceback = line.strip()
                break

    # Best-effort short tracebacks for failures. pytest produces them in two
    # places depending on --tb=line vs --tb=short; we accept either.
    #
    #   --tb=line summary:   "FAILED tests/test_x.py::test_y - assert 200 == 401"
    #   --tb=line FAILURES:  "E   assert 200 == 401"  on its own line under FAILURES
    #
    # Walk stdout once collecting both forms, then attach to the matching
    # outcome in declaration order.
    failed_outcomes_in_order = [o for o in outcomes
                                if o.outcome in ("failed", "errored")]
    captured_tbs: List[str] = []
    in_failures = False
    for line in (proc.stdout or "").splitlines():
        stripped = line.rstrip()
        if "FAILURES" in stripped and "=" in stripped:
            in_failures = True
            continue
        if "short test summary info" in stripped:
            in_failures = False
        if stripped.startswith(("FAILED ", "ERROR ")):
            parts = stripped.split(" - ", 1)
            if len(parts) == 2:
                captured_tbs.append(parts[1].strip())
        elif in_failures and stripped.lstrip().startswith("E "):
            captured_tbs.append(stripped.lstrip()[2:].strip())
    # Attach in order; cap by length of failed outcomes
    for o, tb in zip(failed_outcomes_in_order, captured_tbs):
        o.short_traceback = tb

    return CriticReport(
        tests_dir=str(tests_dir),
        runner="pytest",
        exit_code=proc.returncode,
        passed=counts.get("passed", 0),
        failed=counts.get("failed", 0),
        errored=counts.get("errored", 0),
        skipped=counts.get("skipped", 0),
        outcomes=outcomes,
        stderr_tail="\n".join((proc.stderr or "").splitlines()[-15:]),
    )


# ─── Routing decisions for the critic agent ──────────────────────────────────

def route_failures(report: CriticReport) -> List[Dict]:
    """Inspect failures and label which agent should fix each one.

    Heuristics, deliberately conservative:

        AssertionError on response.status_code with 401  → test-author
            (test expects auth, router has none — see VALIDATION_REPORT)
        AssertionError on "next" in response.json()      → test-author
        ImportError / ModuleNotFoundError                → implementer
        AttributeError on aggregate / value object        → implementer
        TypeError ... missing N required argument          → architect
            (spec didn't say the field was required)
    """
    routes: List[Dict] = []
    for o in report.outcomes:
        if o.outcome not in ("failed", "errored"):
            continue
        msg = (o.short_traceback or "").lower()
        if "401" in msg:
            agent = "test-author"
            reason = "test asserts HTTP 401 but router has no auth"
        elif '"next"' in msg or "'next'" in msg:
            agent = "test-author"
            reason = "test asserts paginated envelope but router returns list"
        elif "modulenotfounderror" in msg or "importerror" in msg:
            agent = "implementer"
            reason = "generated code references missing module"
        elif "attributeerror" in msg:
            agent = "implementer"
            reason = "missing attribute on generated model"
        elif "missing" in msg and "required" in msg and "argument" in msg:
            agent = "architect"
            reason = "spec did not declare a required field used in code"
        else:
            agent = "implementer"
            reason = "uncategorised failure — defaulting to implementer"
        routes.append({
            "nodeid": o.nodeid,
            "route_to": agent,
            "reason": reason,
            "traceback": o.short_traceback,
        })
    return routes


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Run pytest against a generated tests directory and emit a structured report."
    )
    parser.add_argument("--tests", required=True,
                        help="Directory (or single file) to run pytest against")
    parser.add_argument("--pattern", default=None,
                        help="pytest -k filter")
    parser.add_argument("--python", default=None,
                        help="Python interpreter to use (default: current)")
    parser.add_argument("--json", action="store_true",
                        help="Emit JSON only")
    parser.add_argument("--route", action="store_true",
                        help="Also emit per-failure routing hints")
    args = parser.parse_args()

    tests_dir = Path(args.tests).resolve()
    report = run_pytest(tests_dir, pattern=args.pattern,
                        python_executable=args.python)

    if args.json:
        payload = report.to_dict()
        if args.route:
            payload["routes"] = route_failures(report)
        print(json.dumps(payload, indent=2))
    else:
        verdict = "✅ SHIPPED" if report.ok else "❌ LOOP"
        print(f"CRITIC VERDICT: {verdict}")
        print(f"  runner:   {report.runner}")
        print(f"  passed:   {report.passed}")
        print(f"  failed:   {report.failed}")
        print(f"  errored:  {report.errored}")
        print(f"  skipped:  {report.skipped}")
        if report.failed or report.errored:
            print()
            print("FAILURES")
            for o in report.outcomes:
                if o.outcome in ("failed", "errored"):
                    print(f"  • {o.nodeid}")
                    print(f"      {o.short_traceback}")
            if args.route:
                print()
                print("ROUTING")
                for r in route_failures(report):
                    print(f"  → {r['route_to']}: {r['reason']}  [{r['nodeid']}]")
        print()
        print("---JSON---")
        payload = report.to_dict()
        if args.route:
            payload["routes"] = route_failures(report)
        print(json.dumps(payload, indent=2))

    # Distinguish "all green" / "failed" / "collection error" for shell users.
    if report.exit_code == 0:
        sys.exit(0)
    if report.failed or report.errored:
        sys.exit(2)
    sys.exit(3)


if __name__ == "__main__":
    main()
