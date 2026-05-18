#!/usr/bin/env python3
"""
Agentic Session Driver — Tier 9 (Production multi-agent orchestration)

Headless driver that orchestrates the FULL agentic pipeline against a
spec.json without requiring a live Claude Code session. Useful for:

  - CI agentic-eval runs (with recorded responses)
  - Plugin developers stress-testing the orchestration
  - Cost calibration: actual end-to-end token measurement
  - Production batch operations ("apply this spec to 20 projects")

Two execution modes:

  --mode dry-run     Print what would be spawned, in order, with token
                     estimates. No agent invocations. Free.

  --mode record      Like dry-run but ALSO writes a recording template
                     to .tmp/sessions/{ts}/agent-{name}.json with the
                     expected input + an empty `recorded_output` slot.
                     A Claude Code session then fills the slots and
                     re-runs in --mode replay.

  --mode replay      Reads recorded outputs from previous --mode record
                     runs and scores them against the agent-md contract.

Cannot spawn live Task agents from a subprocess — that requires Claude
Code's runtime. For live agentic runs, use the SKILL.md flow.

CLI:
    agentic_session_driver.py --spec spec.json --mode dry-run
    agentic_session_driver.py --spec spec.json --mode record --out .tmp/sessions/run-001/
    agentic_session_driver.py --replay-dir .tmp/sessions/run-001/ --mode replay
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from lib.base_script import bootstrap_runtime, setup_logging
bootstrap_runtime()

logger = setup_logging(__name__)


# ─── Pipeline structure ─────────────────────────────────────────────────────

@dataclass
class AgentSpawn:
    stage: str
    agent_name: str
    subagent_type: str       # how to spawn via Task
    model: str
    estimated_tokens: int
    estimated_usd: float
    input_summary: Dict[str, Any]
    parallel_with: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class SessionPlan:
    feature: str
    framework: str
    spawns: List[AgentSpawn]
    total_estimated_usd: float

    def to_dict(self) -> Dict:
        return {
            "feature": self.feature,
            "framework": self.framework,
            "spawns": [s.to_dict() for s in self.spawns],
            "total_estimated_usd": round(self.total_estimated_usd, 4),
        }


# ─── Token estimates (from cost_budget.py PER_AGENT_TOKEN_ESTIMATES) ────────

_AGENT_COSTS = {
    "architect":      {"model": "sonnet", "tokens": 25000, "usd": 0.10},
    "service-author": {"model": "sonnet", "tokens": 18000, "usd": 0.08},
    "implementer":    {"model": "haiku",  "tokens": 16000, "usd": 0.01},
    "test-author":    {"model": "sonnet", "tokens": 20000, "usd": 0.12},
    "reviewer":       {"model": "sonnet", "tokens": 19500, "usd": 0.09},
    "wirer":          {"model": "haiku",  "tokens": 6500,  "usd": 0.005},
    "critic":         {"model": "sonnet", "tokens": 8000,  "usd": 0.03},
}


# ─── Plan builder ───────────────────────────────────────────────────────────

def build_session_plan(spec: Dict[str, Any]) -> SessionPlan:
    """Translate spec.json → ordered list of agent spawns."""
    spawns: List[AgentSpawn] = []
    feature = spec.get("feature", "")
    framework = spec.get("framework", "fastapi")
    entities_to_create = [
        e for e in spec.get("entities", []) if e.get("action") == "create"
    ]
    has_invariants = any(
        e.get("invariants") for e in entities_to_create
    ) or spec.get("intent") == "auth"

    # Stage 2: architect
    arch_cost = _AGENT_COSTS["architect"]
    spawns.append(AgentSpawn(
        stage="2-architect",
        agent_name="architect",
        subagent_type="general-purpose",
        model=arch_cost["model"],
        estimated_tokens=arch_cost["tokens"],
        estimated_usd=arch_cost["usd"],
        input_summary={"task": feature, "entity_count": len(entities_to_create)},
    ))

    # Stage 2.7: service-author (only when invariants present)
    if has_invariants:
        svc = _AGENT_COSTS["service-author"]
        spawns.append(AgentSpawn(
            stage="2.7-service",
            agent_name="service-author",
            subagent_type="general-purpose",
            model=svc["model"],
            estimated_tokens=svc["tokens"],
            estimated_usd=svc["usd"],
            input_summary={"entities_with_invariants":
                           sum(1 for e in entities_to_create if e.get("invariants"))},
        ))

    # Stage 3: implementer per entity + 1 test-author (PARALLEL)
    impl = _AGENT_COSTS["implementer"]
    test_auth = _AGENT_COSTS["test-author"]
    parallel_names = []
    for ent in entities_to_create:
        agent_label = f"implementer-{ent.get('snake_name', ent['name'])}"
        parallel_names.append(agent_label)
        spawns.append(AgentSpawn(
            stage="3-implementer-parallel",
            agent_name=agent_label,
            subagent_type="general-purpose",
            model=impl["model"],
            estimated_tokens=impl["tokens"],
            estimated_usd=impl["usd"],
            input_summary={"entity": ent.get("name")},
        ))
    parallel_names.append("test-author")
    spawns.append(AgentSpawn(
        stage="3-implementer-parallel",
        agent_name="test-author",
        subagent_type="general-purpose",
        model=test_auth["model"],
        estimated_tokens=test_auth["tokens"],
        estimated_usd=test_auth["usd"],
        input_summary={"entity_count": len(entities_to_create)},
        parallel_with=parallel_names[:-1],
    ))

    # Stage 5: reviewer
    rev = _AGENT_COSTS["reviewer"]
    spawns.append(AgentSpawn(
        stage="5-reviewer",
        agent_name="reviewer",
        subagent_type="general-purpose",
        model=rev["model"],
        estimated_tokens=rev["tokens"],
        estimated_usd=rev["usd"],
        input_summary={"files_count": len(entities_to_create) * 4 + 1},
    ))

    # Stage 7: critic
    crt = _AGENT_COSTS["critic"]
    spawns.append(AgentSpawn(
        stage="7-critic",
        agent_name="critic",
        subagent_type="general-purpose",
        model=crt["model"],
        estimated_tokens=crt["tokens"],
        estimated_usd=crt["usd"],
        input_summary={"runs_pytest": True},
    ))

    total = sum(s.estimated_usd for s in spawns)
    return SessionPlan(
        feature=feature, framework=framework,
        spawns=spawns, total_estimated_usd=total,
    )


# ─── Record / Replay ────────────────────────────────────────────────────────

def write_recording_templates(plan: SessionPlan, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for i, spawn in enumerate(plan.spawns, start=1):
        template = {
            "stage": spawn.stage,
            "agent_name": spawn.agent_name,
            "subagent_type": spawn.subagent_type,
            "model_recommended": spawn.model,
            "input_summary": spawn.input_summary,
            "parallel_with": spawn.parallel_with,
            "recorded_output": None,   # Claude session fills this in
            "recorded_tokens": None,
            "recorded_duration_ms": None,
            "instructions": (
                "1. In a Claude Code session with the plugin installed, "
                "spawn this agent via Task() with the agent_name as a hint. "
                "2. Capture the agent's response text. "
                "3. Fill in recorded_output, recorded_tokens "
                "(from <usage> block), recorded_duration_ms."
            ),
        }
        path = out_dir / f"{i:02d}-{spawn.agent_name}.json"
        path.write_text(json.dumps(template, indent=2), encoding="utf-8")
    plan_path = out_dir / "_plan.json"
    plan_path.write_text(json.dumps(plan.to_dict(), indent=2), encoding="utf-8")


def replay_recordings(replay_dir: Path) -> Dict:
    if not replay_dir.is_dir():
        raise FileNotFoundError(f"replay directory missing: {replay_dir}")
    plan_file = replay_dir / "_plan.json"
    plan_data = json.loads(plan_file.read_text(encoding="utf-8")) \
        if plan_file.exists() else {}
    recordings = []
    for path in sorted(replay_dir.glob("[0-9]*.json")):
        try:
            recordings.append(json.loads(path.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue
    completed = sum(1 for r in recordings if r.get("recorded_output"))
    return {
        "plan": plan_data,
        "recordings_count": len(recordings),
        "completed": completed,
        "ready_to_score": completed == len(recordings) and recordings,
        "recordings": recordings,
    }


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Drive the full agentic pipeline against a spec.json"
    )
    parser.add_argument("--spec", help="Path to spec.json (dry-run / record modes)")
    parser.add_argument("--mode",
                        choices=["dry-run", "record", "replay", "live-api"],
                        default="dry-run")
    parser.add_argument("--out", default=None,
                        help="Output dir for --mode record / --mode live-api")
    parser.add_argument("--replay-dir",
                        help="Recordings dir for --mode replay")
    parser.add_argument("--agents-dir", default=".claude/agents",
                        help="Agents directory for --mode live-api")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.mode == "replay":
        if not args.replay_dir:
            parser.error("--mode replay requires --replay-dir")
        result = replay_recordings(Path(args.replay_dir).resolve())
        print(json.dumps(result, indent=2))
        return

    if args.mode == "live-api":
        # Live SDK-driven mode. Closes the "subprocess can't spawn Task
        # agents" caveat — uses anthropic SDK directly. Graceful no-op
        # when SDK missing / API key unset (so CI can still execute the
        # command without hard-failing).
        if not args.spec:
            parser.error("--mode live-api requires --spec")
        try:
            from live_api_runner import (
                LiveApiRunner, make_anthropic_client, probe_environment,
            )
        except ImportError:
            print(json.dumps({"status": "error",
                              "reason": "live_api_runner_module_missing"},
                              indent=2))
            return
        skip = probe_environment()
        if skip is not None:
            print(json.dumps(skip.to_dict(), indent=2))
            return
        spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
        plan = build_session_plan(spec)
        out_dir = Path(
            args.out or f".tmp/sessions/live-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}"
        ).resolve()
        runner = LiveApiRunner(
            client=make_anthropic_client(),
            agents_dir=Path(args.agents_dir),
            output_dir=out_dir,
        )
        results = []
        for spawn in plan.spawns:
            try:
                r = runner.run_spawn(
                    agent_name=spawn.agent_name,
                    stage=spawn.stage,
                    model_alias=spawn.model,
                    spawn_input=spawn.input_summary,
                    context={"spec": spec},
                )
                results.append(r.to_dict())
            except Exception as e:
                results.append({"agent_name": spawn.agent_name,
                                "stage": spawn.stage,
                                "error": f"{type(e).__name__}: {e}"})
        summary = {
            "status": "completed",
            "out_dir": str(out_dir),
            "spawns_run": len(results),
            "total_input_tokens": sum(r.get("input_tokens", 0) for r in results),
            "total_output_tokens": sum(r.get("output_tokens", 0) for r in results),
            "total_cost_usd": round(
                sum(r.get("cost_usd", 0) for r in results), 6),
            "results": results,
        }
        print(json.dumps(summary, indent=2))
        return

    if not args.spec:
        parser.error("--mode dry-run/record requires --spec")
    spec = json.loads(Path(args.spec).read_text(encoding="utf-8"))
    plan = build_session_plan(spec)

    if args.mode == "record":
        if not args.out:
            args.out = f".tmp/sessions/run-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}"
        out_dir = Path(args.out).resolve()
        write_recording_templates(plan, out_dir)
        print(f"wrote {len(plan.spawns)} recording templates to {out_dir}")
        print(json.dumps(plan.to_dict(), indent=2))
        return

    # dry-run
    if args.json:
        print(json.dumps(plan.to_dict(), indent=2))
    else:
        print(f"AGENTIC SESSION PLAN — {plan.feature}")
        print(f"  framework:     {plan.framework}")
        print(f"  agent spawns:  {len(plan.spawns)}")
        print(f"  est. cost:     ${plan.total_estimated_usd:.4f}")
        print()
        last_stage = None
        for spawn in plan.spawns:
            if spawn.stage != last_stage:
                print(f"  Stage {spawn.stage}")
                last_stage = spawn.stage
            parallel = " (parallel)" if spawn.parallel_with else ""
            print(f"    • {spawn.agent_name:<30} "
                  f"{spawn.model:<7} ~{spawn.estimated_tokens:>6}t "
                  f"${spawn.estimated_usd:.4f}{parallel}")


if __name__ == "__main__":
    main()
