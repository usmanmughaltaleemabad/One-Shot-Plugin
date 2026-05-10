#!/usr/bin/env python3
"""
v1.4.0: Legacy Strangler Pattern Generator

Generates the scaffolding for incrementally replacing a legacy code path
with a new implementation:

  1. New module (your standard generation)
  2. Adapter layer translating legacy <-> new
  3. Feature-flag / routing logic (A/B traffic split)
  4. Dual-run harness (verify old + new produce identical results)
  5. Rollback script (revert to legacy if new path misbehaves)
  6. Cutover plan (5% → 50% → 100% traffic schedule)

Public API:
    strangler = StranglerGenerator(framework='django')
    files = strangler.generate(
        legacy_module='legacy_auth.py',
        new_module='auth_v2.py',
        feature_flag='AUTH_V2',
    )
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class StranglerPlan:
    feature_flag: str
    legacy_module: str
    new_module: str
    framework: str

    def cutover_schedule(self) -> List[Dict]:
        return [
            {'week': 1, 'traffic_pct': 5,  'action': f'Enable {self.feature_flag} for 5% of users in canary cohort.'},
            {'week': 2, 'traffic_pct': 25, 'action': 'Expand to 25% if error rate < legacy baseline.'},
            {'week': 3, 'traffic_pct': 50, 'action': 'Run dual-write for 1 week to verify parity on production data.'},
            {'week': 4, 'traffic_pct': 100,'action': 'Cut all traffic over; keep legacy code on fallback for 2 weeks.'},
            {'week': 6, 'traffic_pct': 100,'action': 'Delete legacy module.'},
        ]


class StranglerGenerator:
    """Emits adapter / routing / dual-run / rollback files for a strangler migration."""

    def __init__(self, framework: str = 'django', language: str = 'python'):
        self.framework = framework.lower()
        self.language = language.lower()

    def generate(self,
                 legacy_module: str,
                 new_module: str,
                 feature_flag: str,
                 entry_function: str = 'handle_request') -> Dict[str, str]:
        plan = StranglerPlan(
            feature_flag=feature_flag,
            legacy_module=legacy_module,
            new_module=new_module,
            framework=self.framework,
        )

        files: Dict[str, str] = {}
        files['strangler/router.py']     = self._router(plan, entry_function)
        files['strangler/adapter.py']    = self._adapter(plan)
        files['strangler/dual_run.py']   = self._dual_run(plan, entry_function)
        files['strangler/rollback.sh']   = self._rollback_script(plan)
        files['strangler/CUTOVER_PLAN.md'] = self._cutover_md(plan)
        files['tests/test_strangler_parity.py'] = self._parity_test(plan, entry_function)
        return files

    # ---- file generators ---------------------------------------------------

    def _router(self, plan: StranglerPlan, entry: str) -> str:
        return f'''"""Routing layer between legacy and new implementation.

The router consults a feature flag (typically wired to LaunchDarkly /
GrowthBook / a database column) and forwards each request to either the
legacy module or its replacement. While both paths are live the router is
the only place that needs to know about the migration.
"""

import os
from {plan.legacy_module.replace(".py", "")} import {entry} as legacy_{entry}
from {plan.new_module.replace(".py", "")} import {entry} as new_{entry}


def is_enabled(user_id: str) -> bool:
    """Return True if the new implementation should serve this request."""
    # Replace with your real feature-flag client.
    pct = int(os.environ.get("{plan.feature_flag}_PCT", "0"))
    return (hash(user_id) % 100) < pct


def {entry}(request, *args, **kwargs):
    if is_enabled(getattr(request, "user_id", "")):
        return new_{entry}(request, *args, **kwargs)
    return legacy_{entry}(request, *args, **kwargs)
'''

    def _adapter(self, plan: StranglerPlan) -> str:
        return f'''"""Adapter — translates between legacy and new data shapes.

Legacy code rarely speaks the same vocabulary as a fresh implementation.
The adapter centralises every translation so callers stay clean.
"""


def legacy_to_new(legacy_obj):
    """Take a legacy DTO and return its equivalent in the new model."""
    if legacy_obj is None:
        return None
    return {{
        # TODO: map fields here, e.g.
        # "user_id": legacy_obj["uid"],
        # "email":   legacy_obj["mail"],
    }}


def new_to_legacy(new_obj):
    """Inverse of legacy_to_new — emit legacy shape from new model."""
    if new_obj is None:
        return None
    return {{
        # TODO: map fields back, e.g.
        # "uid":  new_obj["user_id"],
        # "mail": new_obj["email"],
    }}
'''

    def _dual_run(self, plan: StranglerPlan, entry: str) -> str:
        return f'''"""Dual-run harness — calls both implementations and reports divergences."""

import logging
from {plan.legacy_module.replace(".py", "")} import {entry} as legacy_{entry}
from {plan.new_module.replace(".py", "")} import {entry} as new_{entry}

log = logging.getLogger("strangler.dual_run")


def dual_run(request, *args, **kwargs):
    """Call legacy as the source of truth, then call new and compare."""
    legacy_result = legacy_{entry}(request, *args, **kwargs)
    try:
        new_result = new_{entry}(request, *args, **kwargs)
    except Exception:  # pragma: no cover — surface but never break legacy path
        log.exception("strangler.dual_run new path raised")
        return legacy_result

    if legacy_result != new_result:
        log.warning(
            "strangler.parity_mismatch flag={plan.feature_flag} "
            "legacy=%r new=%r", legacy_result, new_result,
        )
    return legacy_result
'''

    def _rollback_script(self, plan: StranglerPlan) -> str:
        return f'''#!/usr/bin/env bash
# Emergency rollback for the {plan.feature_flag} strangler migration.
set -euo pipefail

echo "[$(date -u +%FT%TZ)] Rolling back {plan.feature_flag} to 0% traffic"
export {plan.feature_flag}_PCT=0
echo "[$(date -u +%FT%TZ)] Verify legacy path is healthy:"
echo "  curl -sSf $LEGACY_HEALTH_URL"
echo "[$(date -u +%FT%TZ)] Done. Investigate before retrying cutover."
'''

    def _cutover_md(self, plan: StranglerPlan) -> str:
        rows = "\n".join(
            f"| Week {step['week']} | {step['traffic_pct']}% | {step['action']} |"
            for step in plan.cutover_schedule()
        )
        return f'''# Cutover Plan — {plan.feature_flag}

| Phase | Traffic | Action |
|-------|---------|--------|
{rows}

## Health checks at each phase
- Error rate ≤ legacy baseline + 10%
- p99 latency ≤ legacy baseline + 20%
- No `strangler.parity_mismatch` warnings in the last hour

## Abort criteria
- Two consecutive phases breach a health check.
- Any data-corruption warning from `dual_run`.
- Customer-reported regression that maps to the new path.

If aborted: run `bash strangler/rollback.sh` immediately.
'''

    def _parity_test(self, plan: StranglerPlan, entry: str) -> str:
        return f'''"""Parity tests — every request must produce identical output on both paths."""

import pytest

from {plan.legacy_module.replace(".py", "")} import {entry} as legacy_{entry}
from {plan.new_module.replace(".py", "")} import {entry} as new_{entry}


@pytest.mark.parametrize("payload", [
    {{"user_id": "alice"}},
    {{"user_id": "bob", "extra": True}},
    # TODO: add real production-shaped payloads here.
])
def test_parity(payload):
    legacy = legacy_{entry}(payload)
    new = new_{entry}(payload)
    assert legacy == new, f"parity mismatch: legacy={{legacy!r}} new={{new!r}}"
'''


def main():
    gen = StranglerGenerator(framework='django')
    files = gen.generate('legacy_auth.py', 'auth_v2.py', 'AUTH_V2')
    for path, body in files.items():
        print(f"--- {path} ---")
        print(body)


if __name__ == '__main__':
    main()
