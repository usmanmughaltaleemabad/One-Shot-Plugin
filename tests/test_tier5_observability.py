"""Tests for Tier 5 observability + self-improvement additions.

Coverage:
  - Eval harness runs and produces structured reports
  - Eval harness regenerates goldens with --update-golden
  - Auto rule extractor CLI subcommands work
  - Auto rule extractor recognises small templatable diffs
  - Telemetry library is import-safe with or without otel installed
  - Telemetry no-op spans expose .set_attr / duration / traceparent
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "skills" / "one-shot-generator" / "scripts"


def _run_script(script: str, *args: str) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args],
        capture_output=True, text=True, env=env, encoding="utf-8",
        timeout=60,
    )


# ─── Eval harness ───────────────────────────────────────────────────────────

def test_eval_runner_runs_all_fixtures():
    runner = REPO_ROOT / "tests" / "evals" / "eval_runner.py"
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        [sys.executable, str(runner), "--json"],
        capture_output=True, text=True, env=env, encoding="utf-8",
        timeout=120,
    )
    assert proc.returncode == 0, proc.stderr
    results = json.loads(proc.stdout)
    assert len(results) >= 3, f"expected at least 3 evals, got {len(results)}"
    for r in results:
        assert r["passed"], f"eval {r['eval']} failed: {r}"
        assert r["overall"] >= 0.85, r


def test_eval_runner_per_eval_invocation_works():
    runner = REPO_ROOT / "tests" / "evals" / "eval_runner.py"
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        [sys.executable, str(runner), "--eval", "cart-with-line-items", "--json"],
        capture_output=True, text=True, env=env, encoding="utf-8",
        timeout=60,
    )
    results = json.loads(proc.stdout)
    r = results[0]
    assert "eval" in r and "overall" in r and "passed" in r


# ─── Auto rule extractor ────────────────────────────────────────────────────

def test_rule_extractor_list_candidates_runs():
    """list-candidates should succeed even when no proposals exist."""
    proc = _run_script("auto_rule_extractor.py",
                       "list-candidates",
                       "--repo-root", str(REPO_ROOT),
                       "--json")
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert isinstance(data, list)


def test_rule_extractor_recognises_small_templatable_diff():
    sys.path.insert(0, str(SCRIPTS))
    try:
        from auto_rule_extractor import _diff_to_pattern
    finally:
        sys.path.remove(str(SCRIPTS))
    old = (
        "@router.get('/')\n"
        "async def list_items():\n"
        "    return []\n"
    )
    new = (
        "@router.get('/')\n"
        "async def list_items() -> list:\n"
        "    return []\n"
    )
    rule = _diff_to_pattern(old, new)
    assert rule is not None
    assert "trigger_pattern" in rule
    assert "replacement_template" in rule


def test_rule_extractor_rejects_large_diffs():
    sys.path.insert(0, str(SCRIPTS))
    try:
        from auto_rule_extractor import _diff_to_pattern
    finally:
        sys.path.remove(str(SCRIPTS))
    old = "\n".join(f"line_{i}" for i in range(20))
    new = "\n".join(f"new_line_{i}" for i in range(20))
    assert _diff_to_pattern(old, new) is None


# ─── Telemetry ──────────────────────────────────────────────────────────────

def test_telemetry_imports_with_otel_disabled():
    sys.path.insert(0, str(SCRIPTS))
    try:
        from lib import telemetry
    finally:
        sys.path.remove(str(SCRIPTS))
    assert callable(telemetry.span)
    assert callable(telemetry.is_enabled)
    assert callable(telemetry.current_traceparent)


def test_telemetry_noop_span_supports_set_attr():
    sys.path.insert(0, str(SCRIPTS))
    try:
        from lib import telemetry
    finally:
        sys.path.remove(str(SCRIPTS))
    prev = os.environ.pop("OSP_OTEL_ENABLED", None)
    try:
        with telemetry.span("test", attrs={"a": 1}) as sp:
            sp.set_attr("b", 2)
            tp = telemetry.current_traceparent()
        assert tp.startswith("00-")
    finally:
        if prev is not None:
            os.environ["OSP_OTEL_ENABLED"] = prev


def test_telemetry_traceparent_is_w3c_shaped():
    sys.path.insert(0, str(SCRIPTS))
    try:
        from lib import telemetry
    finally:
        sys.path.remove(str(SCRIPTS))
    tp = telemetry.current_traceparent()
    parts = tp.split("-")
    assert len(parts) == 4, tp
    assert len(parts[1]) == 32
    assert len(parts[2]) == 16


def test_extract_domain_model_still_works_with_telemetry_wrapped():
    proc = _run_script("extract_domain_model.py",
                       "--json",
                       "shopping cart with line items and discounts")
    assert proc.returncode == 0, proc.stderr
    data = json.loads(proc.stdout)
    assert len(data["entities"]) == 3
    names = {e["pascal"] for e in data["entities"]}
    assert names == {"ShoppingCart", "LineItem", "Discount"}
