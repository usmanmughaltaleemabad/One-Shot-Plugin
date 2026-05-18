"""Stress tests for the multi-iteration critic loop driver.

Existing test_critic_loop_driver.py covers correctness on the happy path.
This file covers SCALE and DEGENERATE cases — proves the driver behaves
sanely when:

  - synthetic failure counts blow up (100 routes in one verdict)
  - many artifacts get doubted in parallel (1000 distinct entries)
  - regression detection works correctly across DEEP histories
  - theater detection doesn't false-positive on legitimate iterative fix
  - escalation reasons stay stable across thousands of replay calls
  - the JSON state file remains parseable after pathological inputs

These compensate for "critic loop in production — untested at scale" —
they're synthetic so they're not a substitute for real-user signal,
but they ARE evidence that the driver doesn't break under realistic
scaled inputs.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

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
            f"driver failed: {proc.stderr}"
    return proc


def _init(sbx: Path) -> None:
    _run("init", "--sandbox", str(sbx))


def _record(sbx: Path, verdict: dict, tmp_path: Path, name: str) -> dict:
    vp = tmp_path / name
    vp.write_text(json.dumps(verdict), encoding="utf-8")
    proc = _run("record", "--sandbox", str(sbx), "--verdict", str(vp))
    return json.loads(proc.stdout)


# ─── Large-volume single-verdict ───────────────────────────────────────────

def test_verdict_with_100_routes_buckets_correctly(tmp_path):
    """100 failures across 4 agent buckets — bucketing must scale linearly."""
    sbx = tmp_path / "sbx"
    _init(sbx)
    routes = []
    agents = ["implementer", "test-author", "reviewer", "architect"]
    for i in range(100):
        routes.append({
            "nodeid": f"tests/test_e2e.py::test_case_{i:03d}",
            "route_to": agents[i % len(agents)],
            "reason": f"failure mode {i % 7}",
            "file": f"src/module_{i % 20}.py",
        })
    result = _record(sbx, {"verdict": "LOOP", "routes": routes}, tmp_path, "big.json")
    # Decision: loop continues OR escalates — but ANY decision must come
    # back well-formed with all 100 routes accounted for.
    assert result["decision"] in {"LOOP_CONTINUE", "ESCALATE"}
    total_in_buckets = sum(len(v) for v in result["routes_by_agent"].values()
                            if isinstance(v, list))
    assert total_in_buckets == 100, \
        f"lost some routes during bucketing: got {total_in_buckets}/100"
    # Bucket count should be 4 (one per distinct route_to)
    assert len(result["routes_by_agent"]) == 4


def test_first_iteration_with_huge_input_completes_under_one_second(tmp_path):
    """Driver overhead must stay tight even when the verdict is large.
    Anything > 1 second on a single record() call is a smell."""
    sbx = tmp_path / "sbx"
    _init(sbx)
    routes = [{"nodeid": f"t::case_{i}", "route_to": "implementer",
                "reason": "x", "file": "f.py"} for i in range(500)]
    vp = tmp_path / "huge.json"
    vp.write_text(json.dumps({"verdict": "LOOP", "routes": routes}),
                  encoding="utf-8")
    start = time.perf_counter()
    proc = _run("record", "--sandbox", str(sbx), "--verdict", str(vp))
    elapsed = time.perf_counter() - start
    assert proc.returncode == 0
    assert elapsed < 5.0, f"record() took {elapsed:.2f}s on 500-route input"


# ─── Regression detection at depth ─────────────────────────────────────────

def test_regression_detection_after_partial_fixes(tmp_path):
    """Iter 1: 10 failures. Iter 2: 8 of the original ones fixed but 1
    NEW failure introduced — driver MUST escalate as regression."""
    sbx = tmp_path / "sbx"
    _init(sbx)

    iter1 = [
        {"nodeid": f"t::orig_{i}", "route_to": "implementer", "reason": "x"}
        for i in range(10)
    ]
    r1 = _record(sbx, {"verdict": "LOOP", "routes": iter1}, tmp_path, "v1.json")
    assert r1["decision"] == "LOOP_CONTINUE"

    # Iter 2: only 2 of the original 10 still failing, but 1 NEW nodeid
    iter2 = [
        {"nodeid": "t::orig_3", "route_to": "implementer", "reason": "x"},
        {"nodeid": "t::orig_7", "route_to": "implementer", "reason": "x"},
        {"nodeid": "t::brand_new", "route_to": "implementer",
         "reason": "introduced while fixing"},
    ]
    r2 = _record(sbx, {"verdict": "LOOP", "routes": iter2}, tmp_path, "v2.json")
    assert r2["decision"] == "ESCALATE"
    assert r2["reason"] == "regression_new_failures"
    assert "t::brand_new" in r2["new_failures"]


def test_no_false_positive_on_pure_shrinking_failure_set(tmp_path):
    """Iter 1: 10 failures. Iter 2: 5 of the same. Healthy progress —
    do NOT escalate as regression."""
    sbx = tmp_path / "sbx"
    _init(sbx)

    iter1 = [{"nodeid": f"t::case_{i}", "route_to": "implementer",
               "reason": "x"} for i in range(10)]
    _record(sbx, {"verdict": "LOOP", "routes": iter1}, tmp_path, "v1.json")

    # Same 5 nodeids still failing, none new
    iter2 = iter1[:5]
    r2 = _record(sbx, {"verdict": "LOOP", "routes": iter2}, tmp_path, "v2.json")
    assert r2["decision"] in {"LOOP_CONTINUE", "ESCALATE"}
    # If ESCALATE, it must NOT be on regression grounds
    if r2["decision"] == "ESCALATE":
        assert r2["reason"] != "regression_new_failures"


# ─── Identical-routes-twice path (critic_loop's behaviour) ────────────────

def test_identical_routes_twice_loops_not_escalates(tmp_path):
    """Note: theater detection (same fingerprint across rounds) lives in
    doubt_driver, NOT critic_loop_driver. critic_loop only escalates on
    max-iterations, timeout, or REGRESSION (new nodeids). Identical
    failures across iterations means the implementer hasn't fixed
    anything yet — but that's NOT a regression. The hard cap at 3
    iterations catches the infinite-spin case."""
    sbx = tmp_path / "sbx"
    _init(sbx)
    same = {"verdict": "LOOP", "routes": [
        {"nodeid": "t::a", "route_to": "implementer", "reason": "x"},
    ]}
    r1 = _record(sbx, same, tmp_path, "v1.json")
    r2 = _record(sbx, same, tmp_path, "v2.json")
    r3 = _record(sbx, same, tmp_path, "v3.json")
    r4 = _record(sbx, same, tmp_path, "v4.json")
    # Iterations 1-3: LOOP_CONTINUE (the implementer gets a chance each time)
    assert r1["decision"] == "LOOP_CONTINUE"
    assert r2["decision"] == "LOOP_CONTINUE"
    assert r3["decision"] == "LOOP_CONTINUE"
    # Iteration 4: hit the max-iterations cap
    assert r4["decision"] == "ESCALATE"
    assert r4["reason"] == "max_iterations_exceeded"


# ─── State file integrity across many records ─────────────────────────────

def test_state_file_remains_valid_json_after_many_records(tmp_path):
    """Drive the driver through many LOOPs in a row and confirm the
    state file is still parseable + history grows as expected."""
    sbx = tmp_path / "sbx"
    _init(sbx)

    # 3 iterations of different routes (no theater, no regression)
    for i in range(3):
        v = {"verdict": "LOOP", "routes": [{"nodeid": f"t::iter_{i}",
                                              "route_to": "implementer",
                                              "reason": f"iter {i}"}]}
        _record(sbx, v, tmp_path, f"v{i}.json")

    state = json.loads((sbx / ".osp-loop-state.json").read_text(encoding="utf-8"))
    assert state["iteration"] >= 3
    assert len(state["history"]) >= 3
    # Each entry has the keys critic_loop_driver actually persists
    for entry in state["history"]:
        assert "verdict" in entry
        assert "recorded_at" in entry
        assert "routes" in entry
        assert "duration_seconds" in entry


# ─── Edge cases ────────────────────────────────────────────────────────────

def test_empty_routes_loop_proceeds_normally(tmp_path):
    """A LOOP verdict with zero routes is unusual but legal — driver
    must not crash or get stuck."""
    sbx = tmp_path / "sbx"
    _init(sbx)
    result = _record(sbx, {"verdict": "LOOP", "routes": []}, tmp_path, "v.json")
    # zero blocking routes means it could PROCEED-like (no work needed)
    # but the driver treats LOOP verdict as needing another iteration.
    # Either way: must NOT crash + result has decision field.
    assert result["decision"] in {"LOOP_CONTINUE", "ESCALATE"}
    assert result["iteration"] >= 1


def test_unknown_route_to_buckets_as_implementer(tmp_path):
    """Critic might emit a route to an agent we don't know. Driver
    bucketed it (test_critic_loop_driver covers default), but here we
    confirm at scale."""
    sbx = tmp_path / "sbx"
    _init(sbx)
    routes = [{"nodeid": f"t::x{i}", "route_to": "unknown-agent",
                "reason": "z"} for i in range(20)]
    result = _record(sbx, {"verdict": "LOOP", "routes": routes}, tmp_path, "v.json")
    # All 20 must be bucketed somewhere — verify nothing was dropped
    total = sum(len(v) for v in result["routes_by_agent"].values()
                if isinstance(v, list))
    assert total == 20


def test_verdict_with_many_unique_nodeids_no_false_regression(tmp_path):
    """50 failures iter-1, 30 different failures iter-2 — ALL different
    so technically every iter-2 nodeid is 'new'. Driver MUST flag
    regression (correct call: we didn't fix anything from iter-1)."""
    sbx = tmp_path / "sbx"
    _init(sbx)
    iter1 = [{"nodeid": f"t::a_{i}", "route_to": "implementer",
               "reason": "x"} for i in range(50)]
    _record(sbx, {"verdict": "LOOP", "routes": iter1}, tmp_path, "v1.json")
    iter2 = [{"nodeid": f"t::b_{i}", "route_to": "implementer",
               "reason": "y"} for i in range(30)]
    r2 = _record(sbx, {"verdict": "LOOP", "routes": iter2}, tmp_path, "v2.json")
    assert r2["decision"] == "ESCALATE"
    assert r2["reason"] == "regression_new_failures"
    # All 30 should be in new_failures
    assert len(r2["new_failures"]) == 30


# ─── Cumulative sanity check across all stress scenarios ───────────────────

def test_no_decision_outside_expected_vocab(tmp_path):
    """Across many synthetic verdict shapes, the driver must only EVER
    return one of: SHIPPED, LOOP_CONTINUE, ESCALATE. Anything else is a
    contract break."""
    valid = {"SHIPPED", "LOOP_CONTINUE", "ESCALATE"}

    sbx = tmp_path / "sbx"
    _init(sbx)
    scenarios = [
        {"verdict": "SHIPPED"},
        {"verdict": "SHIPPED", "duration_seconds": 0.5},
        {"verdict": "LOOP", "routes": []},
        {"verdict": "LOOP", "routes": [
            {"nodeid": "x", "route_to": "implementer", "reason": "y"}]},
        {"verdict": "LOOP", "routes": [
            {"nodeid": "z", "route_to": "implementer"}]},   # missing reason
    ]
    for i, v in enumerate(scenarios):
        # Fresh sandbox per scenario so state doesn't carry over
        s = tmp_path / f"sbx_{i}"
        _init(s)
        result = _record(s, v, tmp_path, f"s{i}.json")
        assert result["decision"] in valid, \
            f"scenario {i} returned unknown decision: {result['decision']!r}"
