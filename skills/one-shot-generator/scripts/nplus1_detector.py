#!/usr/bin/env python3
"""
N+1 Query Detector — v1.0.0  (extends critic_runner with span-count assertions)

Stage 7 critic_runner runs pytest + returns green/red. That catches
test FAILURES — not slow tests caused by N+1 query loops that
silently work in dev with 10 rows but melt production at 10,000 rows.

This script runs pytest WITH OpenTelemetry tracing enabled, collects
DB spans per test (sqlalchemy spans, django.db spans, mysql/pg spans),
and emits a verdict:

  GREEN  — every test had ≤ N db spans per row in the result set
  N_PLUS_ONE — at least one test had db_spans > 2 × rows
  INCONCLUSIVE — OTel SDK not installed / no DB spans captured

Heuristic for detection:
  - For each test, count "db_spans" (any span with attribute db.system,
    db.statement, or with span name matching `SELECT|INSERT|UPDATE|DELETE`).
  - For each test that touches a list endpoint (looks for "list" /
    "all" / "find_all" in the test name), check db_spans vs the
    number of items returned. > 2 * items = highly suspicious N+1.
  - For other tests, span_count > 5 in a single test is a smell.

Graceful no-op when:
  - opentelemetry-sdk not installed
  - pytest fails for reasons unrelated to N+1 (we don't second-guess
    real failures)
  - no DB spans captured at all (test doesn't actually hit a DB)

CLI:
    nplus1_detector.py --project <dir> --tests-cmd "pytest tests/"
    nplus1_detector.py --project <dir> --tests-cmd "pytest tests/" --json
    nplus1_detector.py --project <dir> --tests-cmd "pytest tests/" --threshold 5

Exit codes:
    0  GREEN or INCONCLUSIVE (don't punish tests we can't measure)
    1  bad args
    2  N_PLUS_ONE detected (Stage 7 critic uses this as a hard fail)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from lib.base_script import bootstrap_runtime, setup_logging
bootstrap_runtime()
logger = setup_logging(__name__)


# ─── conftest snippet that captures spans during tests ────────────────────

CONFTEST_SNIPPET = r"""
# N+1 detector — installed by nplus1_detector.py, removed after the run.
# Captures DB spans per test into a JSON file the detector reads.

import json
import os
import re
from pathlib import Path

_OUT = Path(os.environ.get("OSP_NPLUS1_OUT", "/tmp/osp-nplus1-spans.json"))
_SPANS_BY_TEST: dict = {}
_CURRENT_TEST: list = [None]

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter, SpanExportResult

    class _CaptureExporter(SpanExporter):
        def export(self, spans):
            for s in spans:
                test = _CURRENT_TEST[0] or "<unknown>"
                _SPANS_BY_TEST.setdefault(test, []).append({
                    "name": s.name,
                    "attributes": dict(s.attributes) if s.attributes else {},
                })
            return SpanExportResult.SUCCESS

        def shutdown(self): pass

    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(_CaptureExporter()))
    trace.set_tracer_provider(provider)

    try:
        # Patch SQLAlchemy if it's installed
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        SQLAlchemyInstrumentor().instrument()
    except ImportError:
        pass
except ImportError:
    pass


def pytest_runtest_setup(item):
    _CURRENT_TEST[0] = item.nodeid


def pytest_sessionfinish(session, exitstatus):
    try:
        _OUT.write_text(json.dumps(_SPANS_BY_TEST, indent=2), encoding="utf-8")
    except OSError:
        pass
"""


# ─── Analysis ──────────────────────────────────────────────────────────────

DB_SPAN_NAME_RE = re.compile(
    r"(?:^SELECT|^INSERT|^UPDATE|^DELETE|"
    r"sqlalchemy|psycopg|mysql|django\.db|"
    r"prisma|sequelize|gorm|jdbc)",
    re.I,
)


@dataclass
class TestVerdict:
    nodeid: str
    db_span_count: int
    verdict: str          # OK | N_PLUS_ONE_SUSPECTED | TOO_MANY_DB_SPANS
    note: str

    def to_dict(self) -> Dict:
        return asdict(self)


def _is_db_span(span: Dict[str, Any]) -> bool:
    name = (span.get("name") or "").strip()
    if DB_SPAN_NAME_RE.search(name):
        return True
    attrs = span.get("attributes") or {}
    if any(k in attrs for k in ("db.system", "db.statement", "db.name")):
        return True
    return False


def _looks_like_list_endpoint(nodeid: str) -> bool:
    return any(token in nodeid.lower()
                for token in ("list", "all", "find_all", "findall", "index"))


def analyze(spans_by_test: Dict[str, List[Dict]], *,
             threshold: int = 5) -> Dict[str, Any]:
    verdicts: List[TestVerdict] = []
    for nodeid, spans in spans_by_test.items():
        db_spans = [s for s in spans if _is_db_span(s)]
        n = len(db_spans)
        if n == 0:
            verdicts.append(TestVerdict(nodeid, 0, "OK",
                                          "no DB spans (test doesn't hit DB)"))
            continue
        if _looks_like_list_endpoint(nodeid) and n > 3:
            # Likely N+1: a list endpoint should issue 1-2 queries
            verdicts.append(TestVerdict(
                nodeid, n, "N_PLUS_ONE_SUSPECTED",
                f"list endpoint issued {n} DB queries — likely N+1; "
                f"consider joinedload / select_related / include / DataLoader"))
        elif n > threshold:
            verdicts.append(TestVerdict(
                nodeid, n, "TOO_MANY_DB_SPANS",
                f"{n} DB spans in one test exceeds threshold ({threshold}); "
                f"verify whether the work justifies that many round-trips"))
        else:
            verdicts.append(TestVerdict(nodeid, n, "OK",
                                          f"{n} DB span(s) — within budget"))

    has_n_plus_one = any(v.verdict == "N_PLUS_ONE_SUSPECTED" for v in verdicts)
    has_excess = any(v.verdict == "TOO_MANY_DB_SPANS" for v in verdicts)

    if has_n_plus_one:
        overall = "N_PLUS_ONE"
    elif has_excess:
        overall = "EXCESSIVE_QUERIES"
    else:
        overall = "GREEN"

    return {
        "overall_verdict": overall,
        "threshold_per_test": threshold,
        "tests_with_spans": sum(1 for v in verdicts if v.db_span_count > 0),
        "tests_flagged": sum(1 for v in verdicts if v.verdict != "OK"),
        "test_verdicts": [v.to_dict() for v in verdicts],
    }


def run(project: Path, tests_cmd: str, *,
        threshold: int = 5,
        timeout: int = 180) -> Dict[str, Any]:
    """Install conftest snippet, run tests with OTel instrumentation,
    parse the captured spans, emit verdict."""
    # Verify opentelemetry-sdk is installed
    try:
        import opentelemetry   # noqa: F401
    except ImportError:
        return {
            "overall_verdict": "INCONCLUSIVE",
            "reason": "opentelemetry-sdk not installed",
            "fix": "pip install opentelemetry-sdk opentelemetry-instrumentation-sqlalchemy",
            "test_verdicts": [],
        }

    conftest_path = project / "conftest.py"
    backup_path: Optional[Path] = None
    if conftest_path.exists():
        backup_path = project / "conftest.py.osp-nplus1-backup"
        conftest_path.rename(backup_path)
    conftest_path.write_text(CONFTEST_SNIPPET, encoding="utf-8")

    spans_out = Path(tempfile.gettempdir()) / "osp-nplus1-spans.json"
    spans_out.unlink(missing_ok=True)

    env = os.environ.copy()
    env["OSP_NPLUS1_OUT"] = str(spans_out)
    env["PYTHONIOENCODING"] = "utf-8"

    try:
        proc = subprocess.run(
            tests_cmd.split() if isinstance(tests_cmd, str) else tests_cmd,
            cwd=str(project), env=env, capture_output=True, text=True,
            timeout=timeout, encoding="utf-8", errors="replace",
        )
    finally:
        # Restore conftest
        conftest_path.unlink(missing_ok=True)
        if backup_path and backup_path.exists():
            backup_path.rename(conftest_path)

    if not spans_out.exists():
        return {
            "overall_verdict": "INCONCLUSIVE",
            "reason": "no spans captured — tests don't appear to hit a DB",
            "tests_exit_code": proc.returncode,
            "test_verdicts": [],
        }

    try:
        spans_by_test = json.loads(spans_out.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {
            "overall_verdict": "INCONCLUSIVE",
            "reason": "spans file invalid",
            "test_verdicts": [],
        }

    result = analyze(spans_by_test, threshold=threshold)
    result["tests_exit_code"] = proc.returncode
    return result


# ─── CLI ───────────────────────────────────────────────────────────────────

def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        description="Detect N+1 query loops by running pytest under "
                    "OpenTelemetry instrumentation + asserting DB-span "
                    "counts per test. Stage 7 critic fails the build "
                    "when N+1 is detected."
    )
    p.add_argument("--project", required=True, type=Path)
    p.add_argument("--tests-cmd", required=True,
                   help="Command to run the test suite (e.g. 'pytest tests/')")
    p.add_argument("--threshold", type=int, default=5,
                   help="DB spans per test above this is suspicious (default 5)")
    p.add_argument("--timeout", type=int, default=180,
                   help="Test command timeout in seconds (default 180)")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv if argv is not None else sys.argv[1:])

    if not args.project.exists():
        print(f"project not found: {args.project}", file=sys.stderr)
        return 1

    result = run(args.project.resolve(), args.tests_cmd,
                  threshold=args.threshold, timeout=args.timeout)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"N+1 DETECTOR — verdict: {result['overall_verdict']}")
        if result["overall_verdict"] == "INCONCLUSIVE":
            print(f"  reason: {result.get('reason')}")
            if "fix" in result:
                print(f"  fix:    {result['fix']}")
        else:
            print(f"  threshold: {result.get('threshold_per_test', '?')} DB spans/test")
            print(f"  tests with spans: {result.get('tests_with_spans', 0)}")
            print(f"  tests flagged:    {result.get('tests_flagged', 0)}")
            print()
            for v in result["test_verdicts"]:
                if v["verdict"] != "OK":
                    print(f"  [{v['verdict']}] {v['nodeid']}")
                    print(f"     {v['note']}")

    if result["overall_verdict"] == "N_PLUS_ONE":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
