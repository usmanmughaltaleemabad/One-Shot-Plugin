#!/usr/bin/env python3
"""
Live Critic — v1.0.0  (Tier 2.5 production readiness)

Runs pytest **against the user's actual wired project**, not just the
generated sandbox. This is the difference between "the generated code is
syntactically correct" and "the feature actually works end-to-end."

It is intentionally separate from ``critic_runner`` so callers can:

    1. critic_runner   → run tests inside the sandbox before wiring
                          (cheap, no side-effects)
    2. auto_wirer      → mutate main.py / urls.py
    3. live_critic     → run the full project's test suite to confirm
                          the wired code doesn't regress anything

The live critic also captures:

  * which test ids belong to the NEW feature (paths under the generated
    package) versus the existing project (everything else),
  * regression candidates (existing tests that newly fail),
  * import-time errors that only surface once wiring is real.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from lib.base_script import bootstrap_runtime, setup_logging
from critic_runner import run_pytest, CriticReport
bootstrap_runtime()

logger = setup_logging(__name__)


# ─── Data shapes ─────────────────────────────────────────────────────────────

@dataclass
class LiveReport:
    project: str
    feature_paths: List[str]
    runner: CriticReport
    new_feature_outcomes: List[Dict]
    regression_outcomes: List[Dict]

    def to_dict(self) -> Dict:
        return {
            "project": self.project,
            "feature_paths": self.feature_paths,
            "runner": self.runner.to_dict(),
            "new_feature_outcomes": self.new_feature_outcomes,
            "regression_outcomes": self.regression_outcomes,
        }

    @property
    def ok(self) -> bool:
        return self.runner.ok


# ─── Public entry ────────────────────────────────────────────────────────────

def run(project: Path, *, feature_paths: List[str],
        pattern: Optional[str] = None) -> LiveReport:
    """Run pytest at the project root and partition outcomes."""
    if not project.exists():
        raise FileNotFoundError(f"project does not exist: {project}")
    report = run_pytest(project, pattern=pattern)

    feat_lower = [p.lower().replace("\\", "/") for p in feature_paths]
    new_outcomes: List[Dict] = []
    regress_outcomes: List[Dict] = []
    for o in report.outcomes:
        node = o.nodeid.lower().replace("\\", "/")
        if any(fp in node for fp in feat_lower):
            new_outcomes.append(o.to_dict())
        elif o.outcome in ("failed", "errored"):
            regress_outcomes.append(o.to_dict())

    return LiveReport(
        project=str(project),
        feature_paths=feature_paths,
        runner=report,
        new_feature_outcomes=new_outcomes,
        regression_outcomes=regress_outcomes,
    )


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Run the project's test suite and partition outcomes by feature scope"
    )
    parser.add_argument("--project", required=True, help="Project root")
    parser.add_argument("--feature-path", action="append", default=[],
                        help="Path fragment that identifies new-feature tests")
    parser.add_argument("--pattern", default=None, help="pytest -k filter")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = run(Path(args.project).resolve(),
                 feature_paths=args.feature_path,
                 pattern=args.pattern)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(f"LIVE CRITIC: {'✅ GREEN' if report.ok else '❌ RED'}")
        r = report.runner
        print(f"  passed:  {r.passed}")
        print(f"  failed:  {r.failed}")
        print(f"  errored: {r.errored}")
        if report.new_feature_outcomes:
            print()
            print("NEW-FEATURE OUTCOMES")
            for o in report.new_feature_outcomes:
                print(f"  • [{o['outcome']}] {o['nodeid']}")
                if o.get("short_traceback"):
                    print(f"      {o['short_traceback']}")
        if report.regression_outcomes:
            print()
            print("REGRESSIONS")
            for o in report.regression_outcomes:
                print(f"  • [{o['outcome']}] {o['nodeid']}")
    sys.exit(0 if report.ok else 2)


if __name__ == "__main__":
    main()
