"""Tests for live_api_runner — headless SDK-driven agent runner.

The runner replaces the Task-spawn path with direct Anthropic SDK calls,
closing the 'must have Claude Code session' caveat. These tests use a
FakeAnthropic client (never hit the network) to verify:

  - graceful skip when ANTHROPIC_API_KEY missing / anthropic not installed
  - per-agent prompt building (architect / implementer / reviewer / ...)
  - model alias resolution (sonnet → claude-sonnet-4-6, etc.)
  - token + cost accounting per spawn
  - per-spawn JSON persistence to output_dir
  - implementer-{snake} canonical-name normalisation
  - agentic_session_driver --mode live-api dispatches into the runner
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import patch

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "skills" / "one-shot-generator" / "scripts"
AGENTS = REPO_ROOT / "agents"

# Make the scripts dir importable so we can drive the runner in-process.
sys.path.insert(0, str(SCRIPTS))

from live_api_runner import (   # noqa: E402
    LiveApiRunner, RunResult, build_user_prompt, load_agent_md,
    probe_environment, resolve_model, _estimate_cost,
    PROMPT_BUILDERS, TOKEN_PRICES_USD_PER_M,
)


# ─── Fake Anthropic client (never hits the network) ────────────────────────

@dataclass
class _FakeUsage:
    input_tokens: int = 1500
    output_tokens: int = 800


@dataclass
class _FakeBlock:
    type: str = "text"
    text: str = "(fake response body)"


@dataclass
class _FakeMessage:
    stop_reason: str = "end_turn"
    usage: _FakeUsage = None
    content: List[Any] = None

    def __post_init__(self):
        if self.usage is None:
            self.usage = _FakeUsage()
        if self.content is None:
            self.content = [_FakeBlock()]


class _FakeMessages:
    """Captures the LAST .create() call so tests can assert what was sent."""
    def __init__(self, response: _FakeMessage = None):
        self.response = response or _FakeMessage()
        self.calls: List[Dict[str, Any]] = []

    def create(self, *, model, max_tokens, system, messages):
        self.calls.append({
            "model": model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": messages,
        })
        return self.response


class FakeAnthropic:
    def __init__(self, response: _FakeMessage = None):
        self.messages = _FakeMessages(response)


# ─── probe_environment ─────────────────────────────────────────────────────

def test_probe_environment_returns_skip_when_no_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    skip = probe_environment()
    # Either "anthropic_sdk_not_installed" or "missing_anthropic_api_key" —
    # both are valid skip reasons depending on whether the SDK package is
    # in the test env. Both are gracefully-degrading outcomes.
    assert skip is not None
    assert skip.status == "skipped"
    assert skip.reason in {"anthropic_sdk_not_installed", "missing_anthropic_api_key"}
    assert skip.fix   # actionable fix string


def test_probe_environment_passes_with_key_when_sdk_available(monkeypatch):
    """When the SDK IS available AND key IS set, probe returns None."""
    pytest.importorskip("anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-fake")
    assert probe_environment() is None


# ─── Model alias resolution ────────────────────────────────────────────────

def test_resolve_model_aliases():
    assert resolve_model("sonnet").startswith("claude-")
    assert resolve_model("haiku").startswith("claude-")
    # Unknown alias passes through unchanged (caller's choice)
    assert resolve_model("custom-id") == "custom-id"


# ─── Agent.md loading ──────────────────────────────────────────────────────

def test_load_agent_md_returns_body_and_frontmatter(tmp_path):
    md = tmp_path / "ag.md"
    md.write_text("---\nname: ag\nmodel: sonnet\n---\n\nYou are an agent.\n",
                  encoding="utf-8")
    out = load_agent_md(tmp_path, "ag")
    assert "model: sonnet" in out["frontmatter"]
    assert "You are an agent" in out["body"]


def test_load_agent_md_handles_implementer_canonical_name(tmp_path):
    """implementer-cart, implementer-line_item, ... all resolve to
    .claude/agents/implementer.md."""
    md = tmp_path / "implementer.md"
    md.write_text("# Implementer\n", encoding="utf-8")
    out = load_agent_md(tmp_path, "implementer-cart")
    assert "Implementer" in out["body"]


def test_load_agent_md_missing_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_agent_md(tmp_path, "does-not-exist")


# ─── Prompt builders ───────────────────────────────────────────────────────

def test_architect_prompt_includes_task_and_domain_model():
    prompt = build_user_prompt(
        "architect",
        spawn_input={"task": "build a shopping cart", "entity_count": 3},
        context={"domain_model": {"entities": [{"name": "Cart"}]},
                 "graph_summary": "FastAPI project, SQLAlchemy"},
    )
    assert "build a shopping cart" in prompt
    assert "Cart" in prompt
    assert "spec.json" in prompt.lower()
    # Architect must demand JSON-only response
    assert "json" in prompt.lower()


def test_implementer_prompt_includes_file_path_and_kind():
    prompt = build_user_prompt(
        "implementer-cart",
        spawn_input={"entity": "Cart"},
        context={"target_file": "cart/router.py",
                 "file_kind": "fastapi_router",
                 "body_hint": {"language": "python"},
                 "spec_excerpt": {"name": "Cart"}},
    )
    assert "cart/router.py" in prompt
    assert "fastapi_router" in prompt
    assert "Cart" in prompt
    # Implementer must demand bare file content
    assert "ONLY the file content" in prompt or "only the file content" in prompt.lower()


def test_reviewer_prompt_includes_generated_files():
    prompt = build_user_prompt(
        "reviewer",
        spawn_input={},
        context={"generated_files": {"cart/router.py": "import x"}},
    )
    assert "cart/router.py" in prompt
    assert "import x" in prompt
    assert "verdict" in prompt.lower()


def test_critic_prompt_emits_ship_or_loop_format():
    prompt = build_user_prompt(
        "critic",
        spawn_input={},
        context={"pytest_output": "3 passed in 0.1s"},
    )
    assert "SHIPPED" in prompt
    assert "LOOP" in prompt
    assert "routes" in prompt.lower()


def test_unknown_agent_falls_back_to_generic_prompt():
    prompt = build_user_prompt(
        "some-future-agent",
        spawn_input={"x": 1},
        context={"y": 2},
    )
    assert "some-future-agent" in prompt
    assert "agent.md" in prompt.lower()


# ─── LiveApiRunner.run_spawn ───────────────────────────────────────────────

def test_run_spawn_calls_client_with_correct_model_and_persists(tmp_path):
    # Stage a fake .claude/agents directory with a minimal agent.md
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    (agents_dir / "architect.md").write_text(
        "---\nmodel: sonnet\n---\nYou are the architect.", encoding="utf-8")

    out_dir = tmp_path / "out"
    fake = FakeAnthropic(response=_FakeMessage(
        usage=_FakeUsage(input_tokens=2500, output_tokens=1200),
        content=[_FakeBlock(text='{"entities":[],"feature":"test"}')],
    ))
    runner = LiveApiRunner(client=fake, agents_dir=agents_dir, output_dir=out_dir)

    result = runner.run_spawn(
        agent_name="architect",
        stage="2-architect",
        model_alias="sonnet",
        spawn_input={"task": "build feature x"},
        context={"graph_summary": "fastapi project"},
    )

    # Client was called correctly. v4.14: system is now a content-block
    # list (with cache_control markers); handle both string and list shapes.
    assert len(fake.messages.calls) == 1
    call = fake.messages.calls[0]
    assert call["model"].startswith("claude-")
    system = call["system"]
    if isinstance(system, list):
        system_text = " ".join(b.get("text", "") for b in system).lower()
    else:
        system_text = system.lower()
    assert "architect" in system_text
    assert "build feature x" in call["messages"][0]["content"]

    # Result has the right shape
    assert result.agent_name == "architect"
    assert result.input_tokens == 2500
    assert result.output_tokens == 1200
    assert result.stop_reason == "end_turn"
    assert '{"entities":[],"feature":"test"}' in result.text
    assert result.cost_usd > 0   # sonnet pricing

    # Persisted to disk
    persisted = list(out_dir.glob("*.json"))
    assert len(persisted) == 1
    data = json.loads(persisted[0].read_text(encoding="utf-8"))
    assert data["agent_name"] == "architect"
    assert data["text"].startswith("{")


def test_run_spawn_resolves_implementer_canonical_name(tmp_path):
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    (agents_dir / "implementer.md").write_text(
        "---\nmodel: haiku\n---\nYou implement files.", encoding="utf-8")

    runner = LiveApiRunner(client=FakeAnthropic(),
                            agents_dir=agents_dir, output_dir=None)

    # Spawn name is implementer-{snake}; agent.md is just implementer.md
    result = runner.run_spawn(
        agent_name="implementer-shopping_cart",
        stage="3-implementer-parallel",
        model_alias="haiku",
        spawn_input={"entity": "ShoppingCart"},
        context={"target_file": "shopping_cart/router.py",
                 "file_kind": "fastapi_router",
                 "body_hint": {},
                 "spec_excerpt": {}},
    )
    assert result.agent_name == "implementer-shopping_cart"
    # System prompt came from implementer.md. v4.14: system is a
    # content-block list with cache_control; coerce to text for assertion.
    call = runner.client.messages.calls[0]
    system = call["system"]
    if isinstance(system, list):
        system_text = " ".join(b.get("text", "") for b in system).lower()
    else:
        system_text = system.lower()
    assert "implement files" in system_text


def test_run_spawn_costs_haiku_cheaper_than_sonnet(tmp_path):
    """Haiku must produce a lower cost_usd than sonnet for the same token count."""
    sonnet_cost = _estimate_cost("sonnet", 1000, 500)
    haiku_cost  = _estimate_cost("haiku",  1000, 500)
    assert haiku_cost < sonnet_cost, \
        f"haiku ({haiku_cost}) must be cheaper than sonnet ({sonnet_cost})"


def test_run_spawn_skips_persistence_when_output_dir_none(tmp_path):
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    (agents_dir / "critic.md").write_text("# critic", encoding="utf-8")
    runner = LiveApiRunner(client=FakeAnthropic(),
                            agents_dir=agents_dir, output_dir=None)
    result = runner.run_spawn(
        agent_name="critic", stage="7-critic", model_alias="sonnet",
        spawn_input={}, context={"pytest_output": "1 passed"},
    )
    assert result.persisted_to is None


def test_run_spawn_handles_multi_block_response(tmp_path):
    """Some Anthropic responses include multiple text blocks — runner
    must concatenate them, not lose any."""
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    (agents_dir / "architect.md").write_text("# architect", encoding="utf-8")
    fake = FakeAnthropic(response=_FakeMessage(content=[
        _FakeBlock(type="text", text="block 1"),
        _FakeBlock(type="text", text="block 2"),
    ]))
    runner = LiveApiRunner(client=fake, agents_dir=agents_dir, output_dir=None)
    result = runner.run_spawn(
        agent_name="architect", stage="2", model_alias="sonnet",
        spawn_input={}, context={},
    )
    assert "block 1" in result.text and "block 2" in result.text


# ─── pricing constants sanity ──────────────────────────────────────────────

def test_token_prices_present_for_sonnet_and_haiku():
    assert "sonnet" in TOKEN_PRICES_USD_PER_M
    assert "haiku" in TOKEN_PRICES_USD_PER_M
    for tier in ("sonnet", "haiku"):
        assert TOKEN_PRICES_USD_PER_M[tier]["input"] > 0
        assert TOKEN_PRICES_USD_PER_M[tier]["output"] > 0
        # Output is always more expensive than input on Anthropic pricing
        assert (TOKEN_PRICES_USD_PER_M[tier]["output"]
                > TOKEN_PRICES_USD_PER_M[tier]["input"])


# ─── agentic_session_driver --mode live-api dispatch ──────────────────────

def test_session_driver_live_api_skips_gracefully_without_key(tmp_path, monkeypatch):
    """When the env can't support live-api, the driver must return a
    clean skip JSON and exit 0 — never crash."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    spec = {
        "feature": "test", "framework": "fastapi", "test_contract": {},
        "entities": [{"name": "X", "snake_name": "x", "action": "create",
                      "attributes": []}],
        "api_surface": [], "wiring": {}, "relationships": [],
        "graph_imports": {},
    }
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env.pop("ANTHROPIC_API_KEY", None)
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "agentic_session_driver.py"),
         "--mode", "live-api", "--spec", str(spec_path)],
        capture_output=True, text=True, env=env, encoding="utf-8", timeout=15,
    )
    assert proc.returncode == 0
    out = json.loads(proc.stdout)
    assert out["status"] == "skipped"
    assert "fix" in out and out["fix"]


# ─── all real agent.md files are loadable ─────────────────────────────────

def test_every_real_agent_md_loadable():
    """Every .claude/agents/{name}.md must parse without crashing."""
    for path in AGENTS.glob("*.md"):
        out = load_agent_md(AGENTS, path.stem)
        assert out["body"], f"{path} has empty body"


def test_known_agents_have_prompt_builders():
    """The 7 agents the session driver spawns must all have prompt builders
    so live-api mode doesn't fall back to the generic template."""
    expected = {"architect", "implementer", "test-author", "reviewer",
                 "service-author", "critic", "wirer"}
    assert expected <= set(PROMPT_BUILDERS.keys()), \
        f"missing builders: {expected - set(PROMPT_BUILDERS.keys())}"
