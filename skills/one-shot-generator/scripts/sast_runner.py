#!/usr/bin/env python3
"""
SAST Runner — Tier 6 code-safety gate

Optional Bandit integration that runs static security analysis on
generated Python code before the wirer attaches it to the user's
project. Pure no-op when ``bandit`` isn't installed — the plugin's
core invariant of "stdlib-only" is preserved.

This is a soft gate by default: critical findings (B-101, B-602, B-608)
abort the pipeline; medium/low surfaces as warnings.

CLI:
    python sast_runner.py --dir /tmp/osp-verify-xxx/iter_1
    python sast_runner.py --dir <dir> --strict   # fail on any finding
    python sast_runner.py --dir <dir> --json
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional

from lib.base_script import bootstrap_runtime, setup_logging
bootstrap_runtime()

logger = setup_logging(__name__)


# Tests whose findings ALWAYS abort the pipeline
CRITICAL_TEST_IDS = {
    "B102",  # exec used
    "B602",  # shell=True
    "B608",  # SQL injection
    "B105",  # hardcoded password string
    "B106",  # hardcoded password as kwarg
    "B107",  # hardcoded password default
}


@dataclass
class Finding:
    test_id: str
    severity: str
    confidence: str
    file: str
    line: int
    message: str

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class SastReport:
    available: bool
    findings: List[Finding] = field(default_factory=list)
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    note: str = ""

    def to_dict(self) -> Dict:
        return {
            "available": self.available,
            "findings": [f.to_dict() for f in self.findings],
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "medium_count": self.medium_count,
            "low_count": self.low_count,
            "note": self.note,
        }


def _bandit_available() -> bool:
    try:
        proc = subprocess.run(["bandit", "--version"],
                              capture_output=True, text=True, timeout=5)
        return proc.returncode == 0
    except FileNotFoundError:
        return False


def run_sast(directory: Path) -> SastReport:
    if not _bandit_available():
        return SastReport(
            available=False,
            note="bandit not installed — install with `pip install bandit` to enable SAST",
        )
    try:
        proc = subprocess.run(
            ["bandit", "-r", str(directory), "-f", "json", "--quiet"],
            capture_output=True, text=True, timeout=60,
        )
    except subprocess.TimeoutExpired:
        return SastReport(available=True, note="bandit timed out after 60s")

    try:
        data = json.loads(proc.stdout) if proc.stdout else {"results": []}
    except json.JSONDecodeError:
        return SastReport(available=True, note="bandit emitted invalid JSON")

    findings: List[Finding] = []
    for result in data.get("results", []):
        findings.append(Finding(
            test_id=result.get("test_id", ""),
            severity=result.get("issue_severity", ""),
            confidence=result.get("issue_confidence", ""),
            file=result.get("filename", ""),
            line=result.get("line_number", 0),
            message=result.get("issue_text", ""),
        ))

    crit = sum(1 for f in findings if f.test_id in CRITICAL_TEST_IDS)
    high = sum(1 for f in findings if f.severity == "HIGH")
    med = sum(1 for f in findings if f.severity == "MEDIUM")
    low = sum(1 for f in findings if f.severity == "LOW")
    return SastReport(
        available=True,
        findings=findings,
        critical_count=crit,
        high_count=high,
        medium_count=med,
        low_count=low,
        note=f"{len(findings)} bandit finding(s) total",
    )


def main():
    parser = argparse.ArgumentParser(
        description="Run optional Bandit SAST on a directory of generated code"
    )
    parser.add_argument("--dir", required=True)
    parser.add_argument("--strict", action="store_true",
                        help="Exit non-zero on ANY finding (not just critical)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = run_sast(Path(args.dir).resolve())
    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        if not report.available:
            print(f"SAST: SKIPPED ({report.note})")
            sys.exit(0)
        marker = "✓" if not report.findings else ("✗" if report.critical_count else "⚠")
        print(f"SAST: {marker}  {report.note}")
        print(f"  critical:  {report.critical_count}")
        print(f"  high:      {report.high_count}")
        print(f"  medium:    {report.medium_count}")
        print(f"  low:       {report.low_count}")
        for f in report.findings:
            print(f"    [{f.severity}/{f.confidence}] {f.test_id}  "
                  f"{f.file}:{f.line}  {f.message[:80]}")
    if not report.available:
        sys.exit(0)
    if report.critical_count > 0:
        sys.exit(2)
    if args.strict and report.findings:
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
