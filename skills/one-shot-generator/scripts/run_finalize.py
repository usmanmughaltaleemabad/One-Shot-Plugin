#!/usr/bin/env python3
"""
Run Finalize — v1.0.0  (Tier 9 wiring — closes the loop critic_loop_driver
finishes by writing per-agent learnings to the registry).

When a /one-shot invocation completes (either SHIPPED or ESCALATED), the
orchestrator calls this helper to record one learning per agent that
ran. Those rows feed learnings_hub's `top-agents` and `rate` queries,
which downstream surfaces (the curator, agent_discovery, the new
/learnings slash command) use to detect drift in our local agents'
success rates.

This is the "wiring" piece between three previously-disconnected components:

  critic_loop_driver  ─ SHIPPED/ESCALATE verdict (+ history)
        │
        ▼
   run_finalize       ─ map agents → outcomes → record learnings
        │
        ▼
   learnings_hub      ─ append to .claude/registry/learnings.jsonl

The orchestrator passes:
  - the sandbox (so we can read the loop state)
  - the list of agents that were spawned during this run
  - the task keywords (from the user prompt) so future runs can filter

For SHIPPED runs: every agent records `succeeded`.
For ESCALATED runs: agents whose route_to bucket still has open failures
record `failed`; the rest record `succeeded` (their work didn't break,
the run failed elsewhere).

CLI:
    run_finalize.py \
        --sandbox <dir> \
        --agents architect,implementer,test-author,reviewer,wirer,critic \
        --task-keywords "shopping cart with line items" \
        [--repo-root <plugin-root>]    # default: cwd

Exit codes:
    0   learnings written
    1   bad CLI args
    2   loop state missing (orchestrator forgot init+record)
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Set

from lib.base_script import bootstrap_runtime, setup_logging

bootstrap_runtime()
logger = setup_logging(__name__)


LOOP_STATE_FILE = ".osp-loop-state.json"


def _read_loop_state(sandbox: Path) -> Dict:
    p = sandbox / LOOP_STATE_FILE
    if not p.exists():
        raise FileNotFoundError(
            f"loop state not found at {p}. Did the orchestrator skip "
            f"critic_loop_driver.py?"
        )
    return json.loads(p.read_text(encoding="utf-8"))


def _failing_agents_from_state(state: Dict) -> Set[str]:
    """Agents that still own open failures at the end of the run."""
    history = state.get("history", [])
    if not history:
        return set()
    final = history[-1]
    if final.get("verdict") != "LOOP":
        return set()
    return {r.get("route_to", "implementer") for r in final.get("routes", [])}


def _classify_outcomes(state: Dict, agents: List[str]) -> Dict[str, str]:
    """Map each agent in `agents` to 'succeeded' or 'failed'.

    SHIPPED state → everyone succeeded.
    LOOP state (we were called mid-escalation) → only agents that own
    open failure routes are 'failed'; the rest succeeded.
    """
    history = state.get("history", [])
    if not history:
        # Defensive: no critic record → treat as inconclusive but
        # don't punish; mark everyone 'inconclusive'.
        return {a: "inconclusive" for a in agents}
    final = history[-1]
    if final.get("verdict") == "SHIPPED":
        return {a: "succeeded" for a in agents}
    failing = _failing_agents_from_state(state)
    return {a: ("failed" if a in failing else "succeeded") for a in agents}


# Keyword extraction lifted from learnings_hub spirit — keep simple,
# stop-word filter, lower-case, dedup.
_STOPWORDS = {
    "the", "a", "an", "to", "of", "and", "or", "for", "in", "on", "with",
    "build", "add", "create", "new", "make", "is", "be", "this", "that",
    "by", "as", "at", "from", "into", "but", "if", "not", "no",
}


def _extract_keywords(task: str, *, limit: int = 6) -> List[str]:
    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{2,}", task.lower())
    out: List[str] = []
    seen: Set[str] = set()
    for t in tokens:
        if t in _STOPWORDS or t in seen:
            continue
        seen.add(t)
        out.append(t)
        if len(out) >= limit:
            break
    return out


_HUB_SCRIPT = Path(__file__).resolve().parent / "learnings_hub.py"


def _record_via_learnings_hub(*, repo_root: Path, agent_id: str,
                               outcome: str, keywords: List[str],
                               duration_ms: int = 0,
                               cost_usd: float | None = None,
                               notes: str = "") -> None:
    """Shell out to learnings_hub.py so its append semantics stay the
    single source of truth. The hub script is resolved relative to THIS
    file (it's our sibling); --repo-root tells it where to write."""
    # NOTE: learnings_hub puts --repo-root on the ROOT parser, so it must
    # appear BEFORE the "record" subcommand, not after.
    cmd = [
        sys.executable, str(_HUB_SCRIPT),
        "--repo-root", str(repo_root),
        "record",
        "--agent", agent_id,
        "--outcome", outcome,
        "--task-keywords", *keywords,
        "--duration-ms", str(duration_ms),
    ]
    if cost_usd is not None:
        cmd += ["--cost-usd", f"{cost_usd:.4f}"]
    if notes:
        cmd += ["--notes", notes]
    result = subprocess.run(cmd, capture_output=True, text=True,
                            encoding="utf-8")
    if result.returncode != 0:
        logger.warning("learnings_hub record failed for %s: %s",
                       agent_id, result.stderr.strip())


def finalize(*, sandbox: Path, agents: List[str], task: str,
             repo_root: Path) -> Dict:
    """Read the loop state, classify outcomes, record one learning per
    agent. Returns a summary dict the orchestrator can show to the user."""
    state = _read_loop_state(sandbox)
    keywords = _extract_keywords(task)
    outcomes = _classify_outcomes(state, agents)

    history = state.get("history", [])
    final_verdict = history[-1]["verdict"] if history else "UNKNOWN"
    iterations = state.get("iteration", 0)

    recorded: List[Dict] = []
    for agent_id in agents:
        outcome = outcomes[agent_id]
        # local agents (architect, implementer, etc.) get a 'local/' prefix
        # so they don't collide with external-registry agents.
        normalised = (
            agent_id if "/" in agent_id else f"local/{agent_id}"
        )
        _record_via_learnings_hub(
            repo_root=repo_root,
            agent_id=normalised,
            outcome=outcome,
            keywords=keywords,
            notes=f"verdict={final_verdict};iterations={iterations}",
        )
        recorded.append({"agent_id": normalised, "outcome": outcome})

    summary = {
        "final_verdict": final_verdict,
        "iterations": iterations,
        "task_keywords": keywords,
        "recorded": recorded,
        "sandbox": str(sandbox),
    }

    # Auto-trigger dream consolidation when enough failures have accumulated.
    # Threshold: 5+ failures. Runs quickly (pure stdlib) so it adds <100ms.
    _maybe_dream(repo_root)
    return summary


_DREAM_SCRIPT = Path(__file__).resolve().parent / "dream_consolidator.py"
_DREAM_THRESHOLD = 5  # minimum failure beads before auto-dreaming


def _maybe_dream(repo_root: Path) -> None:
    """Run dream_consolidator if failures.jsonl has ≥ _DREAM_THRESHOLD entries."""
    failures_path = repo_root / ".beads" / "failures.jsonl"
    if not failures_path.exists():
        return
    try:
        count = sum(1 for line in failures_path.read_text(
            encoding="utf-8").splitlines() if line.strip())
    except OSError:
        return
    if count < _DREAM_THRESHOLD:
        return
    try:
        result = subprocess.run(
            [sys.executable, str(_DREAM_SCRIPT),
             "--repo-root", str(repo_root),
             "--min-recurrence", "2"],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            logger.info("dream_consolidator: %s", result.stdout.strip().splitlines()[:3])
        else:
            logger.warning("dream_consolidator failed: %s", result.stderr[:200])
    except (OSError, subprocess.TimeoutExpired) as exc:
        logger.warning("dream_consolidator skipped: %s", exc)


# ─── CLI ────────────────────────────────────────────────────────────────────

def main(argv: List[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Finalise a /one-shot run by recording per-agent "
                    "learnings derived from the critic loop driver's verdict."
    )
    p.add_argument("--sandbox", required=True, type=Path,
                   help="Same path passed to critic_loop_driver.py init")
    p.add_argument("--agents", required=True,
                   help="Comma-separated list of agents that spawned this run.")
    p.add_argument("--task-keywords", default="",
                   help="The user's feature request — used to derive keywords.")
    p.add_argument("--repo-root", type=Path, default=Path.cwd(),
                   help="Plugin repo root (where .claude/registry/ lives).")
    args = p.parse_args(argv if argv is not None else sys.argv[1:])

    agents = [a.strip() for a in args.agents.split(",") if a.strip()]
    if not agents:
        print("--agents must list at least one agent", file=sys.stderr)
        return 1

    try:
        summary = finalize(
            sandbox=args.sandbox,
            agents=agents,
            task=args.task_keywords,
            repo_root=args.repo_root,
        )
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 2

    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
