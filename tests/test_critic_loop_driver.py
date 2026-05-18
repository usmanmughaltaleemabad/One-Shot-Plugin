"""Tests for the multi-iteration critic loop driver (v4.4).

The driver enforces Stage 7's hard caps deterministically:
  - max 3 critic iterations
  - max 5 min per iteration
  - escalate on regression (new failure nodeids in iteration N that
    weren't in iteration N-1)
  - bucket routes by target agent so the orchestrator re-spawns once
    per agent, not once per failure
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
DRIVER = SCRIPTS / "critic_loop_driver.py"


def _run(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        [sys.executable, str(DRIVER), *args],
        capture_output=True, text=True, env=env, encoding="utf-8", timeout=30,
    )
    if check:
        assert proc.returncode == 0, \
            f"driver failed (exit {proc.returncode}): {proc.stderr}"
    return proc


def _init(sandbox: Path) -> dict:
    proc = _run("init", "--sandbox", str(sandbox))
    return json.loads(proc.stdout)


def _record(sandbox: Path, verdict: dict, tmp_path: Path,
            verdict_name: str = "verdict.json") -> dict:
    vp = tmp_path / verdict_name
    vp.write_text(json.dumps(verdict), encoding="utf-8")
    proc = _run("record", "--sandbox", str(sandbox), "--verdict", str(vp))
    return json.loads(proc.stdout)


def _escalate(sandbox: Path) -> dict:
    proc = _run("escalate", "--sandbox", str(sandbox))
    return json.loads(proc.stdout)


# ─── init ──────────────────────────────────────────────────────────────────

def test_init_creates_state_file_with_caps(tmp_path):
    sbx = tmp_path / "sandbox"
    state = _init(sbx)
    assert (sbx / ".osp-loop-state.json").exists()
    assert state["iteration"] == 0
    assert state["history"] == []
    assert state["max_iterations"] == 3
    assert state["max_duration_seconds"] == 300


def test_init_creates_sandbox_dir_if_missing(tmp_path):
    sbx = tmp_path / "deep" / "nested" / "sandbox"
    assert not sbx.exists()
    _init(sbx)
    assert sbx.exists()
    assert (sbx / ".osp-loop-state.json").exists()


# ─── SHIPPED on the first try ──────────────────────────────────────────────

def test_shipped_immediately_ends_loop(tmp_path):
    sbx = tmp_path / "sandbox"
    _init(sbx)
    result = _record(sbx, {"verdict": "SHIPPED"}, tmp_path)
    assert result["decision"] == "SHIPPED"
    assert result["iteration"] == 0
    assert result["reason"] == "all_tests_passed"


# ─── normal LOOP path: routes bucketed by agent ─────────────────────────────

def test_loop_routes_bucketed_by_agent(tmp_path):
    sbx = tmp_path / "sandbox"
    _init(sbx)
    verdict = {
        "verdict": "LOOP",
        "routes": [
            {"nodeid": "t/a::1", "route_to": "implementer", "reason": "x"},
            {"nodeid": "t/a::2", "route_to": "implementer", "reason": "y"},
            {"nodeid": "t/a::3", "route_to": "test-author", "reason": "z"},
        ],
    }
    result = _record(sbx, verdict, tmp_path)
    assert result["decision"] == "LOOP_CONTINUE"
    assert result["iteration"] == 1
    by_agent = result["routes_by_agent"]
    # Three failures, two agent buckets — ONE re-spawn per bucket
    assert set(by_agent.keys()) == {"implementer", "test-author"}
    assert len(by_agent["implementer"]) == 2
    assert len(by_agent["test-author"]) == 1


def test_routes_field_named_failures_is_also_accepted(tmp_path):
    """Defensive: some critic outputs may use 'failures' instead of 'routes'."""
    sbx = tmp_path / "sandbox"
    _init(sbx)
    verdict = {
        "verdict": "LOOP",
        "failures": [
            {"nodeid": "t/a::1", "route_to": "implementer", "reason": "x"},
        ],
    }
    result = _record(sbx, verdict, tmp_path)
    assert result["decision"] == "LOOP_CONTINUE"
    assert "implementer" in result["routes_by_agent"]


def test_missing_route_to_defaults_to_implementer(tmp_path):
    sbx = tmp_path / "sandbox"
    _init(sbx)
    verdict = {"verdict": "LOOP", "routes": [{"nodeid": "t/a::1", "reason": "x"}]}
    result = _record(sbx, verdict, tmp_path)
    assert "implementer" in result["routes_by_agent"]


# ─── max iterations cap ────────────────────────────────────────────────────

def test_escalates_after_three_loop_iterations(tmp_path):
    sbx = tmp_path / "sandbox"
    _init(sbx)
    loop = {
        "verdict": "LOOP",
        "routes": [{"nodeid": "t/a::1", "route_to": "implementer", "reason": "x"}],
    }
    # Same failing nodeid across all iterations — no regression triggered
    r1 = _record(sbx, loop, tmp_path, "v1.json")
    assert r1["decision"] == "LOOP_CONTINUE" and r1["iteration"] == 1
    r2 = _record(sbx, loop, tmp_path, "v2.json")
    assert r2["decision"] == "LOOP_CONTINUE" and r2["iteration"] == 2
    r3 = _record(sbx, loop, tmp_path, "v3.json")
    assert r3["decision"] == "LOOP_CONTINUE" and r3["iteration"] == 3
    r4 = _record(sbx, loop, tmp_path, "v4.json")
    assert r4["decision"] == "ESCALATE"
    assert r4["reason"] == "max_iterations_exceeded"
    assert "Sandbox" in r4["escalation_summary"]


# ─── duration cap ──────────────────────────────────────────────────────────

def test_escalates_when_iteration_exceeds_duration_cap(tmp_path):
    sbx = tmp_path / "sandbox"
    _init(sbx)
    slow = {
        "verdict": "LOOP",
        "duration_seconds": 600,
        "routes": [{"nodeid": "t/a::1", "route_to": "implementer", "reason": "x"}],
    }
    result = _record(sbx, slow, tmp_path)
    assert result["decision"] == "ESCALATE"
    assert result["reason"] == "iteration_timeout"


# ─── regression detection ──────────────────────────────────────────────────

def test_escalates_on_new_failure_nodeids(tmp_path):
    sbx = tmp_path / "sandbox"
    _init(sbx)
    v1 = {
        "verdict": "LOOP",
        "routes": [{"nodeid": "t/a::1", "route_to": "implementer", "reason": "x"}],
    }
    v2 = {
        "verdict": "LOOP",
        "routes": [
            {"nodeid": "t/a::1", "route_to": "implementer", "reason": "x"},
            {"nodeid": "t/a::99_brand_new", "route_to": "implementer",
             "reason": "introduced while fixing 1"},
        ],
    }
    r1 = _record(sbx, v1, tmp_path, "v1.json")
    assert r1["decision"] == "LOOP_CONTINUE"
    r2 = _record(sbx, v2, tmp_path, "v2.json")
    assert r2["decision"] == "ESCALATE"
    assert r2["reason"] == "regression_new_failures"
    assert r2["new_failures"] == ["t/a::99_brand_new"]


def test_no_regression_when_failure_set_shrinks(tmp_path):
    """Iteration that fixes some but not all failures is healthy — don't escalate."""
    sbx = tmp_path / "sandbox"
    _init(sbx)
    v1 = {
        "verdict": "LOOP",
        "routes": [
            {"nodeid": "t/a::1", "route_to": "implementer", "reason": "x"},
            {"nodeid": "t/a::2", "route_to": "implementer", "reason": "y"},
        ],
    }
    v2 = {
        "verdict": "LOOP",
        "routes": [
            {"nodeid": "t/a::1", "route_to": "implementer", "reason": "x"},
        ],
    }
    _record(sbx, v1, tmp_path, "v1.json")
    r2 = _record(sbx, v2, tmp_path, "v2.json")
    assert r2["decision"] == "LOOP_CONTINUE", \
        "shrinking failure set is progress, not regression"


# ─── escalate command ──────────────────────────────────────────────────────

def test_escalate_summary_after_history(tmp_path):
    sbx = tmp_path / "sandbox"
    _init(sbx)
    _record(sbx, {
        "verdict": "LOOP",
        "routes": [
            {"nodeid": "t/a::1", "route_to": "implementer", "reason": "x"},
            {"nodeid": "t/a::2", "route_to": "test-author", "reason": "y"},
        ],
    }, tmp_path)
    summary = _escalate(sbx)
    assert summary["iterations"] == 1
    assert summary["outstanding_by_agent"] == {"implementer": 1, "test-author": 1}
    assert sorted(summary["outstanding_nodeids"]) == ["t/a::1", "t/a::2"]
    assert "iteration" in summary["summary"]


def test_escalate_empty_history(tmp_path):
    sbx = tmp_path / "sandbox"
    _init(sbx)
    summary = _escalate(sbx)
    assert summary["iterations"] == 0


# ─── error paths ───────────────────────────────────────────────────────────

def test_record_fails_clearly_when_no_init(tmp_path):
    """The orchestrator must call init first; record without state is a bug."""
    sbx = tmp_path / "sandbox"
    sbx.mkdir()  # exists but no state file
    vp = tmp_path / "v.json"
    vp.write_text(json.dumps({"verdict": "SHIPPED"}), encoding="utf-8")
    proc = _run("record", "--sandbox", str(sbx), "--verdict", str(vp), check=False)
    assert proc.returncode != 0
    assert "init" in proc.stderr.lower() or "not found" in proc.stderr.lower()


def test_record_rejects_malformed_verdict_file(tmp_path):
    sbx = tmp_path / "sandbox"
    _init(sbx)
    vp = tmp_path / "bad.json"
    vp.write_text("not-json{{{", encoding="utf-8")
    proc = _run("record", "--sandbox", str(sbx), "--verdict", str(vp), check=False)
    assert proc.returncode == 2


def test_record_rejects_missing_verdict_file(tmp_path):
    sbx = tmp_path / "sandbox"
    _init(sbx)
    proc = _run("record", "--sandbox", str(sbx),
                "--verdict", str(tmp_path / "nope.json"), check=False)
    assert proc.returncode == 2


# ─── ship-after-loop happy path ────────────────────────────────────────────

def test_loop_then_ship_terminates_cleanly(tmp_path):
    sbx = tmp_path / "sandbox"
    _init(sbx)
    r1 = _record(sbx, {
        "verdict": "LOOP",
        "routes": [{"nodeid": "t/a::1", "route_to": "implementer", "reason": "x"}],
    }, tmp_path, "v1.json")
    assert r1["decision"] == "LOOP_CONTINUE"
    # Implementer re-spawn fixed it
    r2 = _record(sbx, {"verdict": "SHIPPED"}, tmp_path, "v2.json")
    assert r2["decision"] == "SHIPPED"
    assert r2["iteration"] == 1, "ship after one loop = iteration count stays at 1"
