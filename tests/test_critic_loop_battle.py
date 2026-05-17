"""Battle-test the multi-iteration critic loop.

Constructs synthetic failure scenarios that should trigger specific
routing decisions, and confirms the loop responds correctly. Validates
the protocol documented in `one-shot-generate/SKILL.md` Stage 7:

  A. Parse routes
  B. Group routes by responsible agent
  C. Re-spawn agent with verbatim diagnostic context
  D. Re-verify after re-spawn
  E. Stop conditions (3-iter cap, no new failure classes)
  F. Escalation via bead

These are deterministic checks against critic_runner.route_failures(),
not actual Task spawns. The Task fan-out is documented in SKILL.md and
proven separately by the architect dry-run + real-world run.
"""

from __future__ import annotations

import json
import os
import sys
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "skills" / "one-shot-generator" / "scripts"


def _run(script: str, *args: str) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args],
        capture_output=True, text=True, env=env, encoding="utf-8",
        timeout=60,
    )


def _make_failing_tests(tmp: Path, scenarios: dict) -> Path:
    """Write a tests directory with one test file per scenario."""
    test_dir = tmp / "tests"
    test_dir.mkdir(parents=True)
    for name, body in scenarios.items():
        (test_dir / f"test_{name}.py").write_text(body, encoding="utf-8")
    return test_dir


# ─── Scenario 1: 401 contract drift → test-author ──────────────────────────

def test_critic_routes_401_to_test_author(tmp_path):
    tests_dir = _make_failing_tests(tmp_path, {
        "auth_drift": (
            "def test_unauthorized():\n"
            "    response_status = 200\n"
            "    assert response_status == 401\n"
        ),
    })
    proc = _run("critic_runner.py", "--tests", str(tests_dir),
                "--route", "--json")
    data = json.loads(proc.stdout)
    routes = data.get("routes", [])
    assert routes, "critic should produce routes for failures"
    auth_routes = [r for r in routes if "401" in r.get("reason", "")]
    assert auth_routes, "expected at least one 401-tagged route"
    assert auth_routes[0]["route_to"] == "test-author"


# ─── Scenario 2: pagination envelope drift → test-author ───────────────────

def test_critic_routes_next_to_test_author(tmp_path):
    tests_dir = _make_failing_tests(tmp_path, {
        "pagination_drift": (
            "def test_pagination():\n"
            "    response = type('R', (), {'json': lambda self: []})()\n"
            "    assert \"next\" in response.json()\n"
        ),
    })
    proc = _run("critic_runner.py", "--tests", str(tests_dir),
                "--route", "--json")
    data = json.loads(proc.stdout)
    routes = data.get("routes", [])
    pag_routes = [r for r in routes
                  if "envelope" in r.get("reason", "").lower()
                  or "pagination" in r.get("reason", "").lower()
                  or "paginat" in r.get("reason", "").lower()]
    assert pag_routes, f"expected pagination route, got {routes}"
    assert pag_routes[0]["route_to"] == "test-author"


# ─── Scenario 3: import error → implementer ────────────────────────────────

def test_critic_routes_import_error_to_implementer(tmp_path):
    tests_dir = _make_failing_tests(tmp_path, {
        "missing_module": (
            "from nonexistent_module_xyz import something\n"
            "def test_x():\n    assert True\n"
        ),
    })
    proc = _run("critic_runner.py", "--tests", str(tests_dir),
                "--route", "--json")
    data = json.loads(proc.stdout)
    routes = data.get("routes", [])
    impl_routes = [r for r in routes if r["route_to"] == "implementer"]
    assert impl_routes, f"expected implementer route for missing module, got {routes}"


# ─── Scenario 4: multi-failure → grouped by agent ──────────────────────────

def test_critic_groups_multiple_failures_by_responsible_agent(tmp_path):
    tests_dir = _make_failing_tests(tmp_path, {
        "auth_a": (
            "def test_a():\n    status = 200\n    assert status == 401\n"
        ),
        "auth_b": (
            "def test_b():\n    status = 200\n    assert status == 401\n"
        ),
        "pagination_c": (
            "def test_c():\n"
            "    response = type('R', (), {'json': lambda self: []})()\n"
            "    assert \"next\" in response.json()\n"
        ),
    })
    proc = _run("critic_runner.py", "--tests", str(tests_dir),
                "--route", "--json")
    data = json.loads(proc.stdout)
    routes = data.get("routes", [])
    by_agent = {}
    for r in routes:
        by_agent.setdefault(r["route_to"], []).append(r)
    # All three failures are test-author concerns (401 + pagination drift).
    # The SKILL.md uses this grouping to decide "one re-spawn of
    # test-author per spec-contract drift bucket."
    assert "test-author" in by_agent, by_agent
    assert len(by_agent["test-author"]) >= 2


def test_critic_collection_error_short_circuits_and_routes_to_implementer(tmp_path):
    """Document the real behaviour: a single import-error in a test file
    short-circuits pytest collection. The critic still produces one route
    (to implementer for the missing module) so the loop has a clear next
    step."""
    tests_dir = _make_failing_tests(tmp_path, {
        "good": (
            "def test_a():\n    assert True\n"
        ),
        "missing_import": (
            "from totally_bogus_xyz import nothing\n"
            "def test_b():\n    assert True\n"
        ),
    })
    proc = _run("critic_runner.py", "--tests", str(tests_dir),
                "--route", "--json")
    data = json.loads(proc.stdout)
    # Exactly one route, going to implementer
    assert data["errored"] == 1
    assert len(data["routes"]) == 1
    assert data["routes"][0]["route_to"] == "implementer"


# ─── Scenario 5: clean run → no routes (SHIPPED path) ──────────────────────

def test_critic_passing_tests_emit_no_routes(tmp_path):
    tests_dir = _make_failing_tests(tmp_path, {
        "obvious": (
            "def test_one():\n    assert 1 + 1 == 2\n"
            "def test_two():\n    assert isinstance([], list)\n"
        ),
    })
    proc = _run("critic_runner.py", "--tests", str(tests_dir),
                "--route", "--json")
    data = json.loads(proc.stdout)
    assert data["failed"] == 0
    assert data["passed"] >= 2
    assert data.get("routes", []) == []


# ─── Scenario 6: regen-loop semantics (idempotent route classification) ────

def test_critic_classification_is_deterministic(tmp_path):
    """Re-running the critic on the same failure must yield the same
    route. Without this, the loop could thrash between iterations."""
    tests_dir = _make_failing_tests(tmp_path, {
        "stable": (
            "def test_unauthorized():\n    s = 200\n    assert s == 401\n"
        ),
    })
    proc1 = _run("critic_runner.py", "--tests", str(tests_dir),
                 "--route", "--json")
    proc2 = _run("critic_runner.py", "--tests", str(tests_dir),
                 "--route", "--json")
    routes1 = json.loads(proc1.stdout).get("routes", [])
    routes2 = json.loads(proc2.stdout).get("routes", [])
    # Compare route-target + reason text (ignore traceback formatting deltas)
    sig1 = [(r["route_to"], r["reason"]) for r in routes1]
    sig2 = [(r["route_to"], r["reason"]) for r in routes2]
    assert sig1 == sig2, f"classification flaky: {sig1} vs {sig2}"
