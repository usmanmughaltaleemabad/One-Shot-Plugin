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


def _score_architect(recorded: str, contract: Dict) -> Dict:
    """Architect: must emit spec.json with entities + relationships."""
    parsed = _extract_first_json(recorded) if recorded else None
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
    f1 = _f1(pred_entities, set(contract.get("expected_entities", [])))

    must_create = set(contract.get("must_create", []))
    must_reuse = set(contract.get("must_reuse", []))
    created, reused = set(), set()
    if parsed and "entities" in parsed:
        for e in parsed["entities"]:
            if isinstance(e, dict):
                ent_name = e.get("name") or e.get("snake_name") or ""
                action = e.get("action", "create")
                (created if action == "create" else reused if action == "reuse" else set()).add(ent_name)
    create_ok = must_create.issubset(created) if must_create else True
    reuse_ok = must_reuse.issubset(reused) if must_reuse else True

    overall = (0.20 * json_valid + 0.20 * keys_present + 0.30 * f1
               + 0.15 * create_ok + 0.15 * reuse_ok)
    return dict(json_valid=json_valid, required_keys_present=keys_present,
                expected_entities_f1=round(f1, 3),
                must_create_satisfied=create_ok,
                must_reuse_satisfied=reuse_ok,
                overall=round(overall, 3),
                note="" if json_valid else "agent did not emit valid JSON")


def _score_implementer(recorded: str, contract: Dict) -> Dict:
    """Implementer: writes ONE python file. Must parse + contain required tokens."""
    import ast
    code_valid = False
    try:
        ast.parse(recorded)
        code_valid = True
    except SyntaxError:
        pass
    must_contain = contract.get("must_contain", [])
    must_not_contain = contract.get("must_not_contain", [])
    contains_ok = all(token in recorded for token in must_contain)
    avoids_ok = not any(token in recorded for token in must_not_contain)
    overall = 0.40 * code_valid + 0.40 * contains_ok + 0.20 * avoids_ok
    return dict(json_valid=code_valid, required_keys_present=contains_ok,
                expected_entities_f1=1.0 if avoids_ok else 0.0,
                must_create_satisfied=contains_ok, must_reuse_satisfied=avoids_ok,
                overall=round(overall, 3),
                note="" if code_valid else "implementer output not valid Python")


def _score_test_author(recorded: str, contract: Dict) -> Dict:
    """Test-author: valid Python with pytest-discoverable tests + real assertions."""
    import ast, re
    code_valid = False
    test_count = 0
    assert_count = 0
    try:
        tree = ast.parse(recorded)
        code_valid = True
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                    and node.name.startswith("test_"):
                test_count += 1
            if isinstance(node, ast.Assert):
                assert_count += 1
    except SyntaxError:
        pass
    min_tests = contract.get("min_tests", 1)
    min_asserts = contract.get("min_asserts", 1)
    has_tests = test_count >= min_tests
    has_asserts = assert_count >= min_asserts
    no_mock_anti = "Mock(" not in recorded or contract.get("allow_mocks", False)
    overall = 0.30 * code_valid + 0.25 * has_tests + 0.25 * has_asserts + 0.20 * no_mock_anti
    return dict(json_valid=code_valid, required_keys_present=has_tests,
                expected_entities_f1=round(assert_count / max(min_asserts, 1), 3),
                must_create_satisfied=has_asserts, must_reuse_satisfied=no_mock_anti,
                overall=round(overall, 3),
                note=f"{test_count} tests / {assert_count} asserts")


def _score_reviewer(recorded: str, contract: Dict) -> Dict:
    """Reviewer: emits 'REVIEW: PASS' or 'REVIEW: REVISE' with file:line on revise."""
    import re
    has_verdict = bool(re.search(r"REVIEW:\s*(PASS|REVISE)", recorded))
    is_pass = "REVIEW: PASS" in recorded
    is_revise = "REVIEW: REVISE" in recorded
    expected_verdict = contract.get("expected_verdict")  # "PASS" or "REVISE" or None
    verdict_match = True
    if expected_verdict == "PASS":
        verdict_match = is_pass
    elif expected_verdict == "REVISE":
        verdict_match = is_revise
    # If REVISE, must reference a file:line
    has_file_ref = bool(re.search(r"\w+\.(py|java|go|ts|js):\d+", recorded))
    revise_well_formed = (not is_revise) or has_file_ref
    overall = 0.40 * has_verdict + 0.40 * verdict_match + 0.20 * revise_well_formed
    return dict(json_valid=has_verdict, required_keys_present=verdict_match,
                expected_entities_f1=1.0 if revise_well_formed else 0.0,
                must_create_satisfied=verdict_match,
                must_reuse_satisfied=revise_well_formed,
                overall=round(overall, 3),
                note="PASS" if is_pass else "REVISE" if is_revise else "no verdict")


def _score_doubter(recorded: str, contract: Dict) -> Dict:
    """Doubter: contract-violation finder. Must cite contract terms, not implementer reasoning."""
    expected_findings = contract.get("expected_findings", [])
    found = sum(1 for f in expected_findings if f.lower() in recorded.lower())
    finding_recall = found / max(len(expected_findings), 1) if expected_findings else 1.0
    # Doubter must NOT leak implementer reasoning (context isolation)
    forbidden = contract.get("must_not_reference", [])
    leaks = any(f.lower() in recorded.lower() for f in forbidden)
    # Must structure findings
    has_structure = any(marker in recorded for marker in
                        ("ISSUE:", "FINDING:", "VIOLATION:", "- ", "## "))
    overall = 0.40 * finding_recall + 0.30 * (not leaks) + 0.30 * has_structure
    return dict(json_valid=has_structure, required_keys_present=finding_recall == 1.0,
                expected_entities_f1=round(finding_recall, 3),
                must_create_satisfied=not leaks, must_reuse_satisfied=has_structure,
                overall=round(overall, 3),
                note=f"{found}/{len(expected_findings)} findings")


def _score_critic(recorded: str, contract: Dict) -> Dict:
    """Critic: JSON verdict (SHIPPED or LOOP) with routes_by_agent if LOOP."""
    parsed = _extract_first_json(recorded) if recorded else None
    json_valid = parsed is not None
    if not parsed:
        return dict(json_valid=False, required_keys_present=False,
                    expected_entities_f1=0.0, must_create_satisfied=False,
                    must_reuse_satisfied=False, overall=0.0,
                    note="critic must emit JSON")
    verdict = parsed.get("verdict", "")
    expected = contract.get("expected_verdict")
    verdict_ok = (expected is None) or (verdict == expected)
    routes_ok = True
    if verdict == "LOOP":
        routes = parsed.get("routes_by_agent") or parsed.get("routes")
        routes_ok = isinstance(routes, (dict, list)) and bool(routes)
    overall = 0.30 + 0.35 * verdict_ok + 0.35 * routes_ok
    return dict(json_valid=True, required_keys_present=verdict_ok,
                expected_entities_f1=1.0 if routes_ok else 0.0,
                must_create_satisfied=verdict_ok, must_reuse_satisfied=routes_ok,
                overall=round(overall, 3),
                note=f"verdict={verdict}")


def _score_handoff(recorded: str, contract: Dict) -> Dict:
    """Handoff: compact runbook. Must cover required sections."""
    required_sections = contract.get("required_sections",
                                     ["files", "migration", "wire", "next"])
    found = sum(1 for s in required_sections if s.lower() in recorded.lower())
    section_coverage = found / max(len(required_sections), 1)
    # Compactness: handoff should be < 30% of typical conversation length
    is_compact = len(recorded) < contract.get("max_chars", 3000)
    overall = 0.60 * section_coverage + 0.40 * is_compact
    return dict(json_valid=True, required_keys_present=section_coverage == 1.0,
                expected_entities_f1=round(section_coverage, 3),
                must_create_satisfied=is_compact, must_reuse_satisfied=True,
                overall=round(overall, 3),
                note=f"{found}/{len(required_sections)} sections, {len(recorded)} chars")


_AGENT_SCORERS = {
    "architect":    _score_architect,
    "implementer":  _score_implementer,
    "test-author":  _score_test_author,
    "reviewer":     _score_reviewer,
    "doubter":      _score_doubter,
    "critic":       _score_critic,
    "handoff":      _score_handoff,
}


def score_replay(scenario: Dict[str, Any]) -> AgenticScore:
    """Score one recorded agent output against its contract.
    Dispatches by agent type — architect / implementer / test-author /
    reviewer / doubter / critic / handoff."""
    name = scenario["scenario"]
    agent = scenario.get("agent", "unknown")
    contract = scenario.get("expected_output_contract", {})
    recorded = scenario.get("recorded_output", "")

    scorer = _AGENT_SCORERS.get(agent, _score_architect)
    result = scorer(recorded, contract)

    return AgenticScore(
        scenario=name,
        agent=agent,
        json_valid=result["json_valid"],
        required_keys_present=result["required_keys_present"],
        expected_entities_f1=result["expected_entities_f1"],
        must_create_satisfied=result["must_create_satisfied"],
        must_reuse_satisfied=result["must_reuse_satisfied"],
        overall=result["overall"],
        passed=result["overall"] >= 0.85,
        note=result.get("note", ""),
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
