#!/usr/bin/env python3
"""
Agentic Eval Harness — Tier 6

Runs eval scenarios that REQUIRE Task-tool agent spawns. Unlike the
deterministic eval_runner.py (which exercises pure-Python services),
this harness measures whether the agentic pipeline (architect →
implementer → test-author → reviewer → critic) holds up under
controlled prompts.

Three modes:

  1. ``--mode plan``      Print the eval plan + cost estimate, exit.
                           Useful in CI to verify scenarios parse.

  2. ``--mode replay``    Replay recorded agent outputs from
                           ``tests/evals/agentic_replays/`` and score.
                           No live Task spawns. Idempotent, free, fast.

  3. ``--mode live``      Actually spawn the agents via Task. Costs
                           real tokens (~$0.10–0.50 per scenario).
                           ONLY for human-driven validation; never in CI.

The plan/replay separation lets CI verify the scoring logic + golden
shapes without paying for tokens, while still keeping the "live" mode
available as a manual quality gate before each release.

The recording format mirrors what a real Claude Code session produces:
the agent's returned text + structured outputs (spec.json, files, etc.).
Each scenario lives at ``agentic_replays/<scenario_name>.json`` with
shape::

    {
        "scenario": "cart-with-line-items-architect",
        "agent": "architect",
        "input": {
            "task": "...",
            "domain_model": {...},
            "codebase_graph": {...}
        },
        "expected_output_contract": {
            "must_be_valid_json": true,
            "required_keys": ["entities", "relationships", ...],
            "expected_entities": ["ShoppingCart", "LineItem", ...],
            "must_reuse": [],
            "must_create": ["ShoppingCart", "LineItem"]
        },
        "recorded_output": "<the agent's actual emitted text/JSON>",
        "recorded_at": "...",
        "recorded_model": "sonnet",
        "recorded_tokens": 26119,
        "recorded_duration_ms": 55273
    }

CLI:
    python agentic_evals.py --mode plan
    python agentic_evals.py --mode replay
    python agentic_evals.py --mode live --scenario architect-cart  (manual only)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
REPLAYS = REPO_ROOT / "tests" / "evals" / "agentic_replays"
SCRIPTS = REPO_ROOT / "skills" / "one-shot-generator" / "scripts"


# ─── Data shapes ─────────────────────────────────────────────────────────────

@dataclass
class AgenticScore:
    scenario: str
    agent: str
    json_valid: bool
    required_keys_present: bool
    expected_entities_f1: float
    must_create_satisfied: bool
    must_reuse_satisfied: bool
    overall: float
    passed: bool
    note: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


# ─── Scoring ─────────────────────────────────────────────────────────────────

def _extract_first_json(text: str) -> Optional[Dict]:
    """Find the first balanced JSON object in a string."""
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    in_string = False
    escape = False
    for i, ch in enumerate(text[start:], start=start):
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"' and not escape:
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start:i + 1])
                except json.JSONDecodeError:
                    return None
    return None


def _f1(predicted: set, expected: set) -> float:
    if not predicted and not expected:
        return 1.0
    if not predicted or not expected:
        return 0.0
    tp = len(predicted & expected)
    if tp == 0:
        return 0.0
    p = tp / len(predicted)
    r = tp / len(expected)
    return 2 * p * r / (p + r)


def score_replay(scenario: Dict[str, Any]) -> AgenticScore:
    """Score one recorded agent output against its contract."""
    name = scenario["scenario"]
    agent = scenario.get("agent", "unknown")
    contract = scenario.get("expected_output_contract", {})
    recorded = scenario.get("recorded_output", "")

    parsed: Optional[Dict] = None
    if recorded and contract.get("must_be_valid_json", True):
        parsed = _extract_first_json(recorded)
    json_valid = parsed is not None

    required = set(contract.get("required_keys", []))
    keys_present = json_valid and required.issubset(set((parsed or {}).keys()))

    pred_entities: set = set()
    if parsed and "entities" in parsed:
        for e in parsed["entities"]:
            if isinstance(e, dict):
                pred_entities.add(e.get("name") or e.get("snake_name") or "")
            else:
                pred_entities.add(str(e))
    pred_entities.discard("")
    expected_entities = set(contract.get("expected_entities", []))
    f1 = _f1(pred_entities, expected_entities)

    must_create = set(contract.get("must_create", []))
    must_reuse = set(contract.get("must_reuse", []))
    created: set = set()
    reused: set = set()
    if parsed and "entities" in parsed:
        for e in parsed["entities"]:
            if isinstance(e, dict):
                ent_name = e.get("name") or e.get("snake_name") or ""
                action = e.get("action", "create")
                if action == "create":
                    created.add(ent_name)
                elif action == "reuse":
                    reused.add(ent_name)
    create_ok = must_create.issubset(created) if must_create else True
    reuse_ok = must_reuse.issubset(reused) if must_reuse else True

    overall = (
        (0.20 if json_valid else 0.0)
        + (0.20 if keys_present else 0.0)
        + (0.30 * f1)
        + (0.15 if create_ok else 0.0)
        + (0.15 if reuse_ok else 0.0)
    )

    return AgenticScore(
        scenario=name,
        agent=agent,
        json_valid=json_valid,
        required_keys_present=keys_present,
        expected_entities_f1=round(f1, 3),
        must_create_satisfied=create_ok,
        must_reuse_satisfied=reuse_ok,
        overall=round(overall, 3),
        passed=overall >= 0.85,
        note="" if json_valid else "agent did not emit valid JSON",
    )


# ─── Modes ───────────────────────────────────────────────────────────────────

def run_plan() -> List[Dict]:
    """Print the eval plan with cost estimate per scenario."""
    scenarios = _load_scenarios()
    plan: List[Dict] = []
    for s in scenarios:
        plan.append({
            "scenario": s["scenario"],
            "agent": s.get("agent", "?"),
            "model": s.get("recorded_model") or "sonnet",
            "estimated_tokens": s.get("recorded_tokens") or 25000,
            "has_recording": bool(s.get("recorded_output")),
        })
    return plan


def run_replay() -> List[AgenticScore]:
    return [score_replay(s) for s in _load_scenarios()]


def run_live(scenario_name: str) -> Dict:
    """Live mode is the operator's job — we can't spawn Task from inside
    a non-Claude-Code subprocess. Returns instructions instead."""
    return {
        "scenario": scenario_name,
        "instructions": [
            "Live agentic eval mode requires a Claude Code session to spawn",
            "the Task tool with subagent_type matching the scenario's agent.",
            "1. Open a Claude Code session with this plugin installed.",
            f"2. Run: load `{REPLAYS}/{scenario_name}.json` to get the input.",
            "3. Spawn the matching agent via Task with the recorded `input` payload.",
            "4. Capture the agent's output and overwrite `recorded_output`.",
            "5. Re-run `python agentic_evals.py --mode replay` to score.",
        ],
        "note": "This is by design — the harness records, the operator records.",
    }


def _load_scenarios() -> List[Dict]:
    if not REPLAYS.is_dir():
        return []
    out: List[Dict] = []
    for path in sorted(REPLAYS.glob("*.json")):
        try:
            out.append(json.loads(path.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue
    return out


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Eval harness for the Task-spawn agentic pipeline"
    )
    parser.add_argument("--mode", choices=["plan", "replay", "live"],
                        default="replay")
    parser.add_argument("--scenario", help="Used in --mode live")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.mode == "plan":
        plan = run_plan()
        if args.json:
            print(json.dumps(plan, indent=2))
        else:
            print(f"AGENTIC EVAL PLAN — {len(plan)} scenario(s)")
            for p in plan:
                marker = "[rec]" if p["has_recording"] else "[no rec]"
                print(f"  {marker} {p['scenario']:<40} {p['agent']:<12} "
                      f"~{p['estimated_tokens']:>6} tokens on {p['model']}")
        return

    if args.mode == "live":
        if not args.scenario:
            parser.error("--mode live requires --scenario")
        result = run_live(args.scenario)
        print(json.dumps(result, indent=2))
        return

    scores = run_replay()
    if args.json:
        print(json.dumps([s.to_dict() for s in scores], indent=2))
    else:
        passed = sum(1 for s in scores if s.passed)
        print(f"AGENTIC REPLAY EVAL — {passed}/{len(scores)} passed")
        for s in scores:
            mark = "✓" if s.passed else "✗"
            print(f"  {mark} {s.scenario:<40} {s.agent:<12} "
                  f"overall {s.overall:.2f}")
            if not s.passed and s.note:
                print(f"      note: {s.note}")
    sys.exit(0 if all(s.passed for s in scores) else 1)


if __name__ == "__main__":
    main()
