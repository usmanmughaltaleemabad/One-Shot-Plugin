#!/usr/bin/env python3
"""
Live API Runner — v1.0.0  (headless SDK-driven agent spawns)

The agentic pipeline default path requires a live Claude Code session
because subprocess scripts can't spawn `Task` agents. This module
provides the missing path: a runner that drives the same agents via
direct Anthropic SDK calls. Unlocks:
  - CI batch runs of /one-shot against a spec.json
  - Scheduled `cron`-style re-generations
  - Programmatic invocation from automation pipelines
  - Eval harness runs without a Claude Code shell

The runner is consciously decoupled from the orchestrator: it takes a
single AgentSpawn + a context dict, calls the SDK, persists the
response, and returns the parsed result. The orchestrator (or
agentic_session_driver.py --mode live-api) is responsible for ordering,
dependency injection between agents, and post-processing.

Graceful degradation: the runner returns a structured skip-reason when
the Anthropic SDK is not installed OR ANTHROPIC_API_KEY is missing.
Tests use a fake client; production uses the real SDK.

CLI is exposed via agentic_session_driver.py --mode live-api. This file
is the importable library + a thin CLI for one-shot single-agent runs.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Protocol

from lib.base_script import bootstrap_runtime, setup_logging
bootstrap_runtime()
logger = setup_logging(__name__)


# ─── Model alias resolution ─────────────────────────────────────────────────

# Maps the alias the orchestrator uses ("sonnet" / "haiku") to the
# concrete Anthropic model ID. Centralised so a model swap is one edit.
MODEL_ALIASES: Dict[str, str] = {
    "sonnet": "claude-sonnet-4-6",
    "haiku":  "claude-haiku-4-5-20251001",
}


def resolve_model(alias: str) -> str:
    return MODEL_ALIASES.get(alias, alias)


# ─── Anthropic client surface (protocol — for mocking in tests) ────────────

class AnthropicLike(Protocol):
    """Subset of the Anthropic client we use. Real `anthropic.Anthropic`
    satisfies this; tests pass in a FakeAnthropic implementing the same
    shape so we never hit the network."""
    messages: Any


# ─── Skip reasons (returned instead of crashing when env is incomplete) ────

@dataclass
class SkipResult:
    status: str = "skipped"
    reason: str = ""
    fix: str = ""

    def to_dict(self) -> Dict:
        return {"status": self.status, "reason": self.reason, "fix": self.fix}


def probe_environment() -> Optional[SkipResult]:
    """Returns a SkipResult if live-api mode cannot run, else None."""
    try:
        import anthropic  # noqa: F401
    except ImportError:
        return SkipResult(
            reason="anthropic_sdk_not_installed",
            fix="pip install anthropic",
        )
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return SkipResult(
            reason="missing_anthropic_api_key",
            fix="export ANTHROPIC_API_KEY=sk-ant-...",
        )
    return None


def make_anthropic_client():
    """Build a real Anthropic client. Raises if env isn't ready —
    callers should call probe_environment() first."""
    from anthropic import Anthropic   # local import so the file is
    return Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


# ─── Agent.md loading ──────────────────────────────────────────────────────

_FRONTMATTER = re.compile(r"^---\n(.+?)\n---\n", re.DOTALL)


def load_agent_md(agents_dir: Path, agent_name: str) -> Dict[str, str]:
    """Load .claude/agents/{name}.md. Returns {frontmatter_raw, body}.

    The frontmatter contains `model: sonnet|haiku` and `tools: ...`.
    The body is the agent's full natural-language instructions —
    becomes the system prompt for the API call.

    Implementer agents are named `implementer-{snake}` at spawn time;
    they all share `.claude/agents/implementer.md`. Same for test-author."""
    # Normalise: strip per-entity suffix from implementer agents.
    canonical = agent_name
    for prefix in ("implementer-",):
        if canonical.startswith(prefix):
            canonical = "implementer"
            break

    path = agents_dir / f"{canonical}.md"
    if not path.exists():
        raise FileNotFoundError(
            f"agent.md not found: {path}. Looked for canonical name "
            f"'{canonical}' (from spawn name '{agent_name}')."
        )
    text = path.read_text(encoding="utf-8")
    m = _FRONTMATTER.match(text)
    if m:
        body = text[m.end():]
        frontmatter = m.group(1)
    else:
        body = text
        frontmatter = ""
    return {"frontmatter": frontmatter, "body": body, "path": str(path)}


# ─── Prompt builders (one per agent role) ──────────────────────────────────

# Generic shape: each builder takes (spawn, context) and returns a
# string. The orchestrator passes context = {"spec": dict, "scaffold_plan": dict, ...}
# Each builder only reads the fields it needs.

def _architect_prompt(spawn_input: Dict[str, Any], context: Dict[str, Any]) -> str:
    task = spawn_input.get("task") or context.get("task") or "(no task supplied)"
    graph_summary = context.get("graph_summary", "(no codebase graph)")
    domain_model = context.get("domain_model", {})
    curriculum = context.get("curriculum_hits", "none")
    # v4.11: source_excerpts now flow into the architect (was implementer-only).
    # Caught by Gemini review — architect needs current API conventions WHILE
    # designing the spec, not after.
    source_excerpts = context.get(
        "source_excerpts",
        "(none — Stage 1.8 source-driven lookup skipped or no manifest detected)",
    )
    return (
        f"Task: {task}\n\n"
        f"Domain model (from extract_domain_model.py):\n"
        f"{json.dumps(domain_model, indent=2)}\n\n"
        f"Existing codebase (summary):\n{graph_summary}\n\n"
        f"Past failures matching this task:\n{curriculum}\n\n"
        f"Official-doc excerpts at the project's pinned framework version "
        f"(treat as canonical, override any conflicting training-data instinct):\n"
        f"{source_excerpts}\n\n"
        f"Produce spec.json following the architect.md schema. Return ONLY "
        f"the JSON object — no prose, no Markdown fences. Validate that "
        f"every entity has 'name', 'snake_name', 'plural', 'action', "
        f"'attributes'; that relationships use the 'has_many' / 'belongs_to' "
        f"vocabulary; that test_contract is fully populated."
    )


def _implementer_prompt(spawn_input: Dict[str, Any], context: Dict[str, Any]) -> str:
    entity = spawn_input.get("entity") or "(unknown entity)"
    file_path = context.get("target_file", "")
    file_kind = context.get("file_kind", "")
    hint = context.get("body_hint", {})
    spec_excerpt = context.get("spec_excerpt", {})
    source_excerpts = context.get("source_excerpts", "(none — training-data fallback)")
    return (
        f"Generate ONE file: {file_path}\n"
        f"File kind: {file_kind}\n"
        f"Target entity: {entity}\n\n"
        f"Body hint (idiomatic-pattern contract):\n{json.dumps(hint, indent=2)}\n\n"
        f"Spec excerpt:\n{json.dumps(spec_excerpt, indent=2)}\n\n"
        f"Official-doc excerpts (Stage 2.3 source-driven, treat as canonical):\n"
        f"{source_excerpts}\n\n"
        f"Return ONLY the file content — no prose, no Markdown fences. "
        f"The first non-blank line must be valid code."
    )


def _test_author_prompt(spawn_input: Dict[str, Any], context: Dict[str, Any]) -> str:
    entity_count = spawn_input.get("entity_count", 0)
    spec = context.get("spec", {})
    framework = spec.get("framework", "fastapi")
    return (
        f"You are the test-author agent. You see ONLY spec.json — never the "
        f"implementer's output.\n\n"
        f"Framework: {framework}\n"
        f"Spec: {json.dumps(spec, indent=2)}\n\n"
        f"Generate test files (pytest / jest / JUnit / go test per the "
        f"framework's body_hint test convention). Target {entity_count} entity "
        f"surface(s). Tests must align with test_contract — DO NOT assert auth "
        f"unless test_contract.auth != 'none'. Return tests as a single document "
        f"with `# === FILE: path/to/file.py ===` markers between each file."
    )


def _reviewer_prompt(spawn_input: Dict[str, Any], context: Dict[str, Any]) -> str:
    files = context.get("generated_files", {})
    return (
        f"You are the reviewer. Read each file and decide PASS or REVISE.\n\n"
        f"Generated files:\n"
        + "\n\n".join(f"=== {p} ===\n{c}" for p, c in files.items())
        + "\n\nReturn JSON: {verdict: 'PASS' | 'REVISE', "
          "findings: [{severity, where, what, fix_hint}]}."
    )


def _service_author_prompt(spawn_input: Dict[str, Any], context: Dict[str, Any]) -> str:
    invariants = spawn_input.get("invariants_count", 0)
    spec = context.get("spec", {})
    return (
        f"You are the service-author agent. Generate the service layer for "
        f"entities with invariants ({invariants} invariants total).\n\n"
        f"Spec: {json.dumps(spec, indent=2)}\n\n"
        f"Service methods must enforce every invariant explicitly. Wrap "
        f"multi-write operations in a transaction. Emit events on state "
        f"transitions. Never embed HTTP errors (router's job). Return code "
        f"with `# === FILE: path/to/service.py ===` markers."
    )


def _critic_prompt(spawn_input: Dict[str, Any], context: Dict[str, Any]) -> str:
    test_output = context.get("pytest_output", "(no pytest output)")
    return (
        f"You are the critic. Pytest output below — emit a verdict.\n\n"
        f"```\n{test_output}\n```\n\n"
        f"If all tests pass: emit `{{\"verdict\": \"SHIPPED\"}}`.\n"
        f"If any fail: emit `{{\"verdict\": \"LOOP\", \"routes\": [...]}}` "
        f"where each route is {{nodeid, route_to (implementer|test-author|"
        f"architect|reviewer), reason, file, traceback}}."
    )


def _wirer_prompt(spawn_input: Dict[str, Any], context: Dict[str, Any]) -> str:
    plan = context.get("wire_plan", {})
    return (
        f"You are the wirer. Apply this plan to the project's main entrypoint:\n\n"
        f"{json.dumps(plan, indent=2)}\n\n"
        f"Return a unified diff. Do NOT include other files. Preserve "
        f"existing imports + middleware."
    )


PROMPT_BUILDERS: Dict[str, Callable[[Dict[str, Any], Dict[str, Any]], str]] = {
    "architect":      _architect_prompt,
    "implementer":    _implementer_prompt,
    "test-author":    _test_author_prompt,
    "reviewer":       _reviewer_prompt,
    "service-author": _service_author_prompt,
    "critic":         _critic_prompt,
    "wirer":          _wirer_prompt,
}


def build_user_prompt(agent_name: str, spawn_input: Dict[str, Any],
                       context: Dict[str, Any]) -> str:
    """Resolve the agent's canonical name and call its prompt builder.
    Falls back to a generic prompt for unknown agents."""
    canonical = agent_name
    for prefix in ("implementer-",):
        if canonical.startswith(prefix):
            canonical = "implementer"
    builder = PROMPT_BUILDERS.get(canonical)
    if builder is None:
        return (
            f"Agent: {agent_name}\n"
            f"Input: {json.dumps(spawn_input, indent=2)}\n"
            f"Context keys: {sorted(context.keys())}\n\n"
            f"Follow your agent.md instructions. Return the expected artifact."
        )
    return builder(spawn_input, context)


# ─── Runner ────────────────────────────────────────────────────────────────

@dataclass
class RunResult:
    agent_name: str
    stage: str
    model_used: str
    stop_reason: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    text: str
    persisted_to: Optional[str] = None
    # v4.14: prompt-cache metrics (when SDK reports them)
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0

    def to_dict(self) -> Dict:
        return {
            "agent_name": self.agent_name,
            "stage": self.stage,
            "model_used": self.model_used,
            "stop_reason": self.stop_reason,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cache_creation_input_tokens": self.cache_creation_input_tokens,
            "cache_read_input_tokens": self.cache_read_input_tokens,
            "cache_hit_rate": (
                round(self.cache_read_input_tokens
                      / max(self.input_tokens + self.cache_read_input_tokens, 1), 3)
            ),
            "cost_usd": round(self.cost_usd, 6),
            "text_chars": len(self.text),
            "persisted_to": self.persisted_to,
        }


# Per-token pricing — kept on this side of the wire so tests can assert
# cost accounting without hitting the API. Numbers are illustrative and
# should be calibrated from learnings.jsonl by cost_calibrator.py.
TOKEN_PRICES_USD_PER_M = {
    "sonnet": {"input": 3.00, "output": 15.00},
    "haiku":  {"input": 0.80, "output": 4.00},
}


def _estimate_cost(model_alias: str, in_tokens: int, out_tokens: int,
                    *, cache_creation_tokens: int = 0,
                    cache_read_tokens: int = 0) -> float:
    """v4.14: cache pricing model.
        regular input:  $X / M tokens
        cache creation: $X * 1.25 / M  (one-time write cost)
        cache read:     $X * 0.10 / M  (90% cheaper than regular input)
    """
    prices = TOKEN_PRICES_USD_PER_M.get(model_alias,
                                          TOKEN_PRICES_USD_PER_M["sonnet"])
    input_rate = prices["input"]
    total = (
        in_tokens * input_rate
        + out_tokens * prices["output"]
        + cache_creation_tokens * input_rate * 1.25
        + cache_read_tokens * input_rate * 0.10
    )
    return total / 1_000_000


class LiveApiRunner:
    """One-call runner. Pass in a client (real or mock) + paths, then
    call run_spawn() per agent. The runner doesn't orchestrate; it just
    handles the SDK call + persistence."""

    def __init__(self,
                 client: AnthropicLike,
                 agents_dir: Path,
                 output_dir: Optional[Path] = None,
                 *,
                 max_tokens: int = 4096,
                 enable_prompt_cache: bool = True):
        """`enable_prompt_cache=True` (default) structures the system
        prompt as a list with cache_control markers so Anthropic caches
        the heavy, slow-changing parts across spawns. With 10+ agents
        per run and the same agent.md / body_hints / domain_model each
        time, this typically cuts input-token billing by ~75% and
        wall-clock latency by ~2x.

        Set to False if the underlying SDK doesn't support
        cache_control (older `anthropic` < 0.40)."""
        self.client = client
        self.agents_dir = agents_dir
        self.output_dir = output_dir
        self.max_tokens = max_tokens
        self.enable_prompt_cache = enable_prompt_cache
        if output_dir is not None:
            output_dir.mkdir(parents=True, exist_ok=True)

    def _build_system_payload(self, agent_md_body: str,
                                cached_context: Optional[str] = None) -> Any:
        """Build the `system` parameter for messages.create.

        When prompt caching is enabled, we structure it as a list of
        content blocks with cache_control on the heavy, stable parts:
          1. agent.md body (rarely changes — perfect cache target)
          2. cached_context (project graph, body_hints, source_excerpts —
             changes per spec but stable across the spawns in ONE run)

        When disabled, returns the plain string (legacy behaviour)."""
        if not self.enable_prompt_cache:
            if cached_context:
                return agent_md_body + "\n\n" + cached_context
            return agent_md_body

        # Cached-list form. The cache_control marker on the LAST block
        # caches everything up to and including it.
        blocks: List[Dict[str, Any]] = [
            {
                "type": "text",
                "text": agent_md_body,
                "cache_control": {"type": "ephemeral"},
            }
        ]
        if cached_context:
            blocks.append({
                "type": "text",
                "text": cached_context,
                "cache_control": {"type": "ephemeral"},
            })
        return blocks

    def run_spawn(self,
                  agent_name: str,
                  stage: str,
                  model_alias: str,
                  spawn_input: Dict[str, Any],
                  context: Dict[str, Any]) -> RunResult:
        agent_md = load_agent_md(self.agents_dir, agent_name)
        system_prompt_body = agent_md["body"]
        # Pull stable, multi-spawn context out of the user prompt so it
        # lives in the cached system slot. The orchestrator can opt in
        # by populating context["cached_context"] with the bundled
        # codebase graph + body_hints + source_excerpts blob.
        cached_context = context.get("cached_context")
        user_prompt = build_user_prompt(agent_name, spawn_input, context)
        model_id = resolve_model(model_alias)

        system_payload = self._build_system_payload(system_prompt_body,
                                                      cached_context)

        # Some clients (the FakeAnthropic used in tests) accept the call
        # but don't understand cache_control — silently strip if create()
        # raises TypeError on the kwargs.
        create_kwargs: Dict[str, Any] = dict(
            model=model_id,
            max_tokens=self.max_tokens,
            system=system_payload,
            messages=[{"role": "user", "content": user_prompt}],
        )
        try:
            response = self.client.messages.create(**create_kwargs)
        except TypeError as e:
            # Likely an old SDK that doesn't accept content-block system —
            # fall back to plain string + retry once.
            logger.warning("client.messages.create rejected cached system "
                            "payload (%s); falling back to plain string", e)
            create_kwargs["system"] = system_prompt_body
            if cached_context:
                create_kwargs["messages"][0]["content"] = (
                    cached_context + "\n\n" + user_prompt)
            response = self.client.messages.create(**create_kwargs)

        text_parts: List[str] = []
        for block in response.content:
            # Anthropic blocks have a .type and (for text) a .text attribute.
            if getattr(block, "type", "") == "text":
                text_parts.append(getattr(block, "text", ""))
        text = "\n".join(text_parts)

        in_tokens = response.usage.input_tokens
        out_tokens = response.usage.output_tokens
        # v4.14: pick up cache hit metrics when the SDK exposes them.
        # `cache_read_input_tokens` are billed at ~10% of the input rate;
        # `cache_creation_input_tokens` are billed at ~125% of input rate
        # (one-time cost to write the cache entry).
        cache_creation = getattr(response.usage, "cache_creation_input_tokens", 0) or 0
        cache_read = getattr(response.usage, "cache_read_input_tokens", 0) or 0
        cost = _estimate_cost(model_alias, in_tokens, out_tokens,
                                cache_creation_tokens=cache_creation,
                                cache_read_tokens=cache_read)

        result = RunResult(
            agent_name=agent_name,
            stage=stage,
            model_used=model_id,
            stop_reason=response.stop_reason,
            input_tokens=in_tokens,
            output_tokens=out_tokens,
            cost_usd=cost,
            text=text,
            cache_creation_input_tokens=cache_creation,
            cache_read_input_tokens=cache_read,
        )
        if self.output_dir is not None:
            out_path = self.output_dir / f"{stage}-{agent_name}.json"
            out_path.write_text(json.dumps({
                "agent_name": agent_name,
                "stage": stage,
                "model_used": model_id,
                "stop_reason": response.stop_reason,
                "input_tokens": in_tokens,
                "output_tokens": out_tokens,
                "cost_usd": round(cost, 6),
                "user_prompt": user_prompt,
                "system_prompt_chars": len(system_prompt),
                "text": text,
            }, indent=2), encoding="utf-8")
            result.persisted_to = str(out_path)
        return result


# ─── CLI — single-agent invocation (most users go through the session driver) ─

def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        description="Run ONE agent live against the Anthropic API. "
                    "Most callers use agentic_session_driver.py --mode live-api "
                    "instead; this CLI is for ad-hoc / debugging."
    )
    p.add_argument("--agent", required=True,
                   help="Agent name (architect, implementer, reviewer, ...).")
    p.add_argument("--stage", default="ad-hoc",
                   help="Pipeline stage label for the output filename.")
    p.add_argument("--model", default="sonnet", choices=["sonnet", "haiku"])
    p.add_argument("--input-json", type=Path,
                   help="JSON file with the spawn_input dict.")
    p.add_argument("--context-json", type=Path,
                   help="JSON file with the context dict.")
    p.add_argument("--agents-dir", type=Path,
                   default=Path(".claude/agents"))
    p.add_argument("--out", type=Path, default=None,
                   help="Output dir for the per-spawn JSON record.")
    args = p.parse_args(argv if argv is not None else sys.argv[1:])

    skip = probe_environment()
    if skip is not None:
        print(json.dumps(skip.to_dict(), indent=2))
        return 0   # graceful no-op; not a failure

    spawn_input = (
        json.loads(args.input_json.read_text(encoding="utf-8"))
        if args.input_json and args.input_json.exists()
        else {}
    )
    context = (
        json.loads(args.context_json.read_text(encoding="utf-8"))
        if args.context_json and args.context_json.exists()
        else {}
    )

    client = make_anthropic_client()
    runner = LiveApiRunner(
        client=client,
        agents_dir=args.agents_dir,
        output_dir=args.out,
    )
    result = runner.run_spawn(
        agent_name=args.agent,
        stage=args.stage,
        model_alias=args.model,
        spawn_input=spawn_input,
        context=context,
    )
    print(json.dumps(result.to_dict(), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
