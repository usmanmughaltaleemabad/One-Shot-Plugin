#!/usr/bin/env python3
"""
Critic Loop Driver — v1.0.0  (Tier 8 — multi-iteration critic loop)

The orchestrating Claude (the slash-command session running /one-shot)
calls this helper after each Stage 7 critic spawn to decide whether to
loop, escalate, or ship.

The protocol itself lives in skills/one-shot-generate/SKILL.md § Stage 7.
This driver is the deterministic enforcement layer: it tracks iteration
count, compares route sets across iterations to detect regression, owns
the hard caps, and groups routes by target agent so the orchestrator can
re-spawn the right specialists in parallel.

State is kept in a single JSON file inside the sandbox so the driver is
stateless across CLI invocations:

    <sandbox>/.osp-loop-state.json
    {
      "iteration": 1,
      "started_at": "2026-05-18T12:34:56Z",
      "history": [
        {
          "recorded_at": "...",
          "verdict": "LOOP",
          "routes": [{"nodeid": "...", "route_to": "implementer", "reason": "..."}],
          "duration_seconds": 47.2
        }
      ]
    }

CLI:
    # 1. After Stage 6 (wire) — initialise the loop state
    python critic_loop_driver.py init --sandbox <dir>

    # 2. After each critic spawn — record the verdict, get a decision
    python critic_loop_driver.py record \
        --sandbox <dir> --verdict <path-to-critic-output.json>

    Returns JSON to stdout:
      { "decision": "SHIPPED" | "LOOP_CONTINUE" | "ESCALATE",
        "iteration": int,
        "reason": "<short tag>",
        "routes_by_agent": {"implementer": [...], "test-author": [...]},
        "escalation_summary": "<user-facing message, when ESCALATE>" }

    # 3. On ESCALATE — write a structured bead with the full history
    python critic_loop_driver.py escalate --sandbox <dir>

Exit codes:
    0   normal (decision in JSON output)
    1   invalid CLI args or unreadable state file
    2   critic verdict file missing or malformed
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from lib.base_script import bootstrap_runtime, setup_logging

bootstrap_runtime()
logger = setup_logging(__name__)


# ─── Hard caps (also documented in SKILL.md Stage 7) ────────────────────────

MAX_ITERATIONS = 3                  # 3 loop cycles, then escalate
MAX_DURATION_SECONDS = 300          # 5 min per iteration
STATE_FILENAME = ".osp-loop-state.json"


# ─── State I/O ──────────────────────────────────────────────────────────────

def _state_path(sandbox: Path) -> Path:
    return sandbox / STATE_FILENAME


def _read_state(sandbox: Path) -> Dict[str, Any]:
    p = _state_path(sandbox)
    if not p.exists():
        raise FileNotFoundError(
            f"loop state not found at {p}. Run `critic_loop_driver.py init` "
            f"before recording verdicts."
        )
    return json.loads(p.read_text(encoding="utf-8"))


def _write_state(sandbox: Path, state: Dict[str, Any]) -> None:
    _state_path(sandbox).write_text(json.dumps(state, indent=2), encoding="utf-8")


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ─── Operations ─────────────────────────────────────────────────────────────

def init(sandbox: Path) -> Dict[str, Any]:
    sandbox.mkdir(parents=True, exist_ok=True)
    state = {
        "iteration": 0,
        "started_at": _now_iso(),
        "history": [],
        "max_iterations": MAX_ITERATIONS,
        "max_duration_seconds": MAX_DURATION_SECONDS,
    }
    _write_state(sandbox, state)
    return state


def _normalise_routes(verdict: Dict[str, Any]) -> List[Dict[str, str]]:
    """Critic output may use 'routes' (preferred) or 'failures'. Coerce."""
    routes = verdict.get("routes") or verdict.get("failures") or []
    out: List[Dict[str, str]] = []
    for r in routes:
        if not isinstance(r, dict):
            continue
        out.append({
            "nodeid": r.get("nodeid", ""),
            "route_to": r.get("route_to", "implementer"),
            "reason": r.get("reason", ""),
            "file": r.get("file", ""),
            "traceback": r.get("traceback", ""),
        })
    return out


def _group_routes_by_agent(routes: List[Dict[str, str]]) -> Dict[str, List[Dict[str, str]]]:
    """Bucket failures by route_to. Each bucket → ONE re-spawn (not one per failure)."""
    buckets: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    for r in routes:
        buckets[r["route_to"]].append(r)
    return dict(buckets)


def _detect_regression(history: List[Dict[str, Any]],
                       current_routes: List[Dict[str, str]]) -> List[str]:
    """A new nodeid appearing in iteration N+1 that wasn't failing in N is a
    regression — we broke something new while trying to fix old failures.
    Returns the list of regressed nodeids (empty if none)."""
    if len(history) < 2:
        return []
    prior = history[-2]  # the LOOP that triggered this iteration
    if prior.get("verdict") != "LOOP":
        return []
    prior_nodeids = {r["nodeid"] for r in prior.get("routes", [])}
    current_nodeids = {r["nodeid"] for r in current_routes if r["nodeid"]}
    return sorted(current_nodeids - prior_nodeids)


def record(sandbox: Path, verdict: Dict[str, Any]) -> Dict[str, Any]:
    """Record one critic verdict, decide whether to loop, escalate, or ship."""
    state = _read_state(sandbox)

    raw_verdict = (verdict.get("verdict") or "").upper()
    routes = _normalise_routes(verdict)
    duration = float(verdict.get("duration_seconds", 0.0))

    state["history"].append({
        "recorded_at": _now_iso(),
        "verdict": raw_verdict,
        "routes": routes,
        "duration_seconds": duration,
    })

    # SHIPPED — game over, success
    if raw_verdict == "SHIPPED":
        _write_state(sandbox, state)
        return {
            "decision": "SHIPPED",
            "iteration": state["iteration"],
            "reason": "all_tests_passed",
            "routes_by_agent": {},
        }

    # LOOP path
    state["iteration"] += 1
    _write_state(sandbox, state)

    # Hard cap on iterations
    if state["iteration"] > MAX_ITERATIONS:
        return {
            "decision": "ESCALATE",
            "iteration": state["iteration"],
            "reason": "max_iterations_exceeded",
            "routes_by_agent": _group_routes_by_agent(routes),
            "escalation_summary": (
                f"Critic returned LOOP on iteration {state['iteration']}. "
                f"Hard cap is {MAX_ITERATIONS}. Escalating to user. "
                f"Sandbox: {sandbox}"
            ),
        }

    # Hard cap on iteration duration (caller should pass duration_seconds in verdict)
    if duration > MAX_DURATION_SECONDS:
        return {
            "decision": "ESCALATE",
            "iteration": state["iteration"],
            "reason": "iteration_timeout",
            "routes_by_agent": _group_routes_by_agent(routes),
            "escalation_summary": (
                f"Iteration {state['iteration']} took {duration:.1f}s "
                f"(cap: {MAX_DURATION_SECONDS}s). Escalating. Sandbox: {sandbox}"
            ),
        }

    # Regression detection: did this iteration introduce nodeids that
    # the previous iteration didn't have? Looping further would risk
    # an infinite chase.
    regressed = _detect_regression(state["history"], routes)
    if regressed:
        return {
            "decision": "ESCALATE",
            "iteration": state["iteration"],
            "reason": "regression_new_failures",
            "routes_by_agent": _group_routes_by_agent(routes),
            "new_failures": regressed,
            "escalation_summary": (
                f"Iteration {state['iteration']} introduced failures that "
                f"iteration {state['iteration'] - 1} did not have: "
                f"{regressed[:3]}{'...' if len(regressed) > 3 else ''}. "
                f"Stopping rather than chasing regressions. Sandbox: {sandbox}"
            ),
        }

    # Normal loop — re-spawn the agents listed under each bucket
    return {
        "decision": "LOOP_CONTINUE",
        "iteration": state["iteration"],
        "reason": "respawn_agents",
        "routes_by_agent": _group_routes_by_agent(routes),
    }


def escalate(sandbox: Path) -> Dict[str, Any]:
    """Emit a user-facing summary that the orchestrator presents verbatim.
    The orchestrator separately writes a bead via beads_writer.py — this
    helper just summarises state."""
    state = _read_state(sandbox)
    history = state["history"]
    final = history[-1] if history else None
    if final is None:
        return {"summary": "No critic verdicts recorded.", "iterations": 0}

    routes = final.get("routes", [])
    by_agent = _group_routes_by_agent(routes)
    counts = {agent: len(rs) for agent, rs in by_agent.items()}

    lines = [
        f"Critic loop escalated after {state['iteration']} iteration(s).",
        f"Started at {state['started_at']}.",
        f"Final verdict: {final.get('verdict')}",
        f"Outstanding failures by agent: {counts}",
        f"Sandbox: {sandbox}",
    ]
    return {
        "summary": "\n".join(lines),
        "iterations": state["iteration"],
        "final_verdict": final.get("verdict"),
        "outstanding_by_agent": counts,
        "outstanding_nodeids": [r["nodeid"] for r in routes if r["nodeid"]],
        "sandbox": str(sandbox),
    }


# ─── CLI ────────────────────────────────────────────────────────────────────

def _parse_args(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Drive the multi-iteration critic loop. Stateful; "
                    "called once per critic spawn."
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="Create loop state in the sandbox.")
    p_init.add_argument("--sandbox", required=True, type=Path)

    p_rec = sub.add_parser("record", help="Record a critic verdict and decide next step.")
    p_rec.add_argument("--sandbox", required=True, type=Path)
    p_rec.add_argument("--verdict", required=True, type=Path,
                       help="Path to JSON file containing the critic's output.")

    p_esc = sub.add_parser("escalate", help="Summarise state for user-facing message.")
    p_esc.add_argument("--sandbox", required=True, type=Path)

    return p.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])

    if args.cmd == "init":
        result = init(args.sandbox)
    elif args.cmd == "record":
        if not args.verdict.exists():
            print(f"verdict file not found: {args.verdict}", file=sys.stderr)
            return 2
        try:
            verdict = json.loads(args.verdict.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"verdict file is not valid JSON: {e}", file=sys.stderr)
            return 2
        result = record(args.sandbox, verdict)
    elif args.cmd == "escalate":
        result = escalate(args.sandbox)
    else:
        return 1

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
