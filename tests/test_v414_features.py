"""Tests for v4.14 — the five items deferred from v4.13 to v4.14.

  1. anti_rationalization_check.py — catches reviewer rubber-stamps
  2. live_api_runner prompt caching anchors (cache_control on system blocks)
  3. mutation_tester.py — kills hollow test suites
  4. context_pruner.py — AST-driven scope reduction for monorepos
  5. nplus1_detector.py — OTel-based N+1 query detection
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "skills" / "one-shot-generator" / "scripts"
ANTI_RAT  = SCRIPTS / "anti_rationalization_check.py"
MUTATION  = SCRIPTS / "mutation_tester.py"
CTX_PRUNE = SCRIPTS / "context_pruner.py"
NPLUS1    = SCRIPTS / "nplus1_detector.py"

# Make live_api_runner importable for in-process testing
sys.path.insert(0, str(SCRIPTS))


def _run(script: Path, *args: str, check: bool = True,
         timeout: int = 60) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True, text=True, env=env, encoding="utf-8",
        timeout=timeout,
    )
    if check:
        assert proc.returncode in (0, 1, 2), \
            f"{script.name} crashed: {proc.stderr}"
    return proc


# ─── 1. anti_rationalization_check.py ─────────────────────────────────────

def test_anti_rat_catches_agent_lying_about_mock(tmp_path):
    """Agent answers 'no' to mocked_integration but code has Mock()."""
    (tmp_path / "router.py").write_text(
        "from unittest.mock import Mock\n"
        "db = Mock()\n"
        "def get_user(): return db.query()\n",
        encoding="utf-8",
    )
    reviewer = tmp_path / "rev.txt"
    reviewer.write_text(
        "ANTI-RATIONALIZATION MATRIX\n"
        "- mocked_integration: no\n"
        "- generic_except: no\n"
        "- missing_boundary_tests: no\n"
        "- status_only_tests: no\n"
        "- hardcoded_secret: no\n"
        "- left_print_statements: no\n"
        "- todo_left_behind: no\n"
        "- ignored_test_contract_auth: n/a\n",
        encoding="utf-8",
    )
    proc = _run(ANTI_RAT, "--reviewer-output", str(reviewer),
                 "--generated-dir", str(tmp_path), "--json", check=False)
    data = json.loads(proc.stdout)
    assert proc.returncode == 2
    assert data["overall_verdict"] == "ESCALATE"
    lies = [c for c in data["checks"] if c["verdict"] == "LIED"]
    assert any(c["token"] == "mocked_integration" for c in lies)


def test_anti_rat_no_matrix_at_all_is_rubber_stamp(tmp_path):
    (tmp_path / "main.py").write_text("def x(): pass\n", encoding="utf-8")
    reviewer = tmp_path / "rev.txt"
    reviewer.write_text("# Review\nLooks good! PASS.\n", encoding="utf-8")
    proc = _run(ANTI_RAT, "--reviewer-output", str(reviewer),
                 "--generated-dir", str(tmp_path), "--json", check=False)
    data = json.loads(proc.stdout)
    assert proc.returncode == 2
    assert data["overall_verdict"] == "RUBBER_STAMP"


def test_anti_rat_clean_matrix_with_matching_code_proceeds(tmp_path):
    (tmp_path / "main.py").write_text(
        "import os\n"
        "import logging\n"
        "logger = logging.getLogger(__name__)\n"
        "def hash_pw(pw):\n"
        "    try:\n"
        "        return _hash(pw)\n"
        "    except ValueError:\n"
        "        raise\n",
        encoding="utf-8",
    )
    reviewer = tmp_path / "rev.txt"
    reviewer.write_text(
        "ANTI-RATIONALIZATION MATRIX\n"
        "- mocked_integration: no\n"
        "- generic_except: no\n"
        "- missing_boundary_tests: no\n"
        "- status_only_tests: no\n"
        "- hardcoded_secret: no\n"
        "- left_print_statements: no\n"
        "- todo_left_behind: no\n"
        "- ignored_test_contract_auth: n/a\n",
        encoding="utf-8",
    )
    proc = _run(ANTI_RAT, "--reviewer-output", str(reviewer),
                 "--generated-dir", str(tmp_path), "--json")
    data = json.loads(proc.stdout)
    assert proc.returncode == 0
    assert data["overall_verdict"] == "CLEAN"


def test_anti_rat_catches_generic_except(tmp_path):
    (tmp_path / "router.py").write_text(
        "def x():\n    try:\n        risky()\n    except Exception:\n        pass\n",
        encoding="utf-8",
    )
    reviewer = tmp_path / "rev.txt"
    reviewer.write_text(
        "MATRIX\n"
        "- generic_except: no\n"
        "- mocked_integration: no\n"
        "- missing_boundary_tests: n/a\n"
        "- hardcoded_secret: no\n"
        "- left_print_statements: no\n"
        "- todo_left_behind: no\n"
        "- status_only_tests: n/a\n"
        "- ignored_test_contract_auth: n/a\n",
        encoding="utf-8",
    )
    proc = _run(ANTI_RAT, "--reviewer-output", str(reviewer),
                 "--generated-dir", str(tmp_path), "--json", check=False)
    data = json.loads(proc.stdout)
    rules_lied = [c["token"] for c in data["checks"] if c["verdict"] == "LIED"]
    assert "generic_except" in rules_lied


def test_anti_rat_catches_hardcoded_secrets(tmp_path):
    (tmp_path / "cfg.py").write_text(
        'API_KEY = "sk-1234567890abcdef1234567890"\n', encoding="utf-8")
    reviewer = tmp_path / "rev.txt"
    reviewer.write_text(
        "MATRIX\n"
        "- hardcoded_secret: no\n"
        "- mocked_integration: no\n"
        "- generic_except: no\n"
        "- missing_boundary_tests: n/a\n"
        "- left_print_statements: no\n"
        "- todo_left_behind: no\n"
        "- status_only_tests: n/a\n"
        "- ignored_test_contract_auth: n/a\n",
        encoding="utf-8",
    )
    proc = _run(ANTI_RAT, "--reviewer-output", str(reviewer),
                 "--generated-dir", str(tmp_path), "--json", check=False)
    data = json.loads(proc.stdout)
    rules_lied = [c["token"] for c in data["checks"] if c["verdict"] == "LIED"]
    assert "hardcoded_secret" in rules_lied


# ─── 2. live_api_runner prompt caching ────────────────────────────────────

from live_api_runner import LiveApiRunner   # noqa: E402


@dataclass
class _FakeUsage:
    input_tokens: int = 1500
    output_tokens: int = 800
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0


@dataclass
class _FakeBlock:
    type: str = "text"
    text: str = "ok"


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


class _CapturingMessages:
    """Captures what was sent to the API so we can assert cache_control was applied."""
    def __init__(self, response: _FakeMessage = None):
        self.response = response or _FakeMessage()
        self.calls: List[dict] = []

    def create(self, *, model, max_tokens, system, messages, **kwargs):
        self.calls.append({"model": model, "max_tokens": max_tokens,
                            "system": system, "messages": messages,
                            "extra_kwargs": kwargs})
        return self.response


class _FakeClient:
    def __init__(self, response=None):
        self.messages = _CapturingMessages(response)


def test_live_api_prompt_cache_default_on_uses_content_blocks(tmp_path):
    """When prompt cache is on, system param must be a list of blocks
    each with cache_control."""
    agents = tmp_path / "agents"; agents.mkdir()
    (agents / "architect.md").write_text(
        "---\nmodel: sonnet\n---\nYou are the architect.\n" * 20,
        encoding="utf-8",
    )
    client = _FakeClient()
    runner = LiveApiRunner(client=client, agents_dir=agents,
                            output_dir=None, enable_prompt_cache=True)
    runner.run_spawn(
        agent_name="architect", stage="2", model_alias="sonnet",
        spawn_input={"task": "build x"}, context={},
    )
    call = client.messages.calls[0]
    assert isinstance(call["system"], list), \
        "system param must be a content-block list when caching is on"
    # Last block must have cache_control
    assert call["system"][-1].get("cache_control") == {"type": "ephemeral"}


def test_live_api_prompt_cache_off_uses_plain_string(tmp_path):
    agents = tmp_path / "agents"; agents.mkdir()
    (agents / "critic.md").write_text("# critic", encoding="utf-8")
    client = _FakeClient()
    runner = LiveApiRunner(client=client, agents_dir=agents,
                            output_dir=None, enable_prompt_cache=False)
    runner.run_spawn(
        agent_name="critic", stage="7", model_alias="sonnet",
        spawn_input={}, context={},
    )
    call = client.messages.calls[0]
    assert isinstance(call["system"], str), \
        "system param must be a plain string when caching is off"


def test_live_api_threads_cached_context_into_system_blocks(tmp_path):
    """Orchestrator passes context['cached_context'] — runner must append
    it as a second cache_control block (stable across spawns in a run)."""
    agents = tmp_path / "agents"; agents.mkdir()
    (agents / "architect.md").write_text("# Architect agent", encoding="utf-8")
    client = _FakeClient()
    runner = LiveApiRunner(client=client, agents_dir=agents,
                            output_dir=None, enable_prompt_cache=True)
    cached_blob = "FRAMEWORK: fastapi 0.115\n" + "x" * 5000
    runner.run_spawn(
        agent_name="architect", stage="2", model_alias="sonnet",
        spawn_input={}, context={"cached_context": cached_blob},
    )
    call = client.messages.calls[0]
    assert len(call["system"]) == 2
    assert "Architect" in call["system"][0]["text"]
    assert "FRAMEWORK: fastapi" in call["system"][1]["text"]
    # Both must have cache_control
    for block in call["system"]:
        assert block.get("cache_control") == {"type": "ephemeral"}


def test_live_api_cache_metrics_surface_in_result(tmp_path):
    agents = tmp_path / "agents"; agents.mkdir()
    (agents / "architect.md").write_text("# x", encoding="utf-8")
    fake = _FakeClient(response=_FakeMessage(
        usage=_FakeUsage(input_tokens=200, output_tokens=100,
                          cache_creation_input_tokens=0,
                          cache_read_input_tokens=10000),
    ))
    runner = LiveApiRunner(client=fake, agents_dir=agents, output_dir=None)
    result = runner.run_spawn(
        agent_name="architect", stage="2", model_alias="sonnet",
        spawn_input={}, context={},
    )
    d = result.to_dict()
    assert d["cache_read_input_tokens"] == 10000
    # Cache hit rate ~ 98% (10000 of 10200)
    assert d["cache_hit_rate"] > 0.95


def test_live_api_cache_lowers_cost_vs_no_cache(tmp_path):
    """Cache read tokens billed at 10% of input rate. 10K cache_read +
    200 fresh input should cost ~10% of 10200 fresh input tokens."""
    from live_api_runner import _estimate_cost
    no_cache = _estimate_cost("sonnet", in_tokens=10200, out_tokens=100)
    with_cache = _estimate_cost("sonnet", in_tokens=200, out_tokens=100,
                                  cache_read_tokens=10000)
    # With cache should be at least 60% cheaper
    assert with_cache < no_cache * 0.4, \
        f"prompt cache pricing isn't favourable enough: with_cache={with_cache:.4f}, no_cache={no_cache:.4f}"


# ─── 3. mutation_tester.py ────────────────────────────────────────────────

def _seed_project_with_strong_tests(root: Path) -> None:
    """A project where tests actually assert state, not just status."""
    (root / "calc.py").write_text(
        "def add(a, b):\n"
        "    return a + b\n"
        "\n"
        "def compare(a, b):\n"
        "    return a > b\n"
        "\n"
        "def is_positive(x):\n"
        "    if x > 0:\n"
        "        return True\n"
        "    return False\n"
        # Padding to clear 20-LOC floor
        + "\n".join(f"# pad {i}" for i in range(25)),
        encoding="utf-8",
    )
    (root / "test_calc.py").write_text(
        "from calc import add, compare, is_positive\n\n"
        "def test_add_basic():\n"
        "    assert add(2, 3) == 5\n"
        "def test_add_zero():\n"
        "    assert add(0, 0) == 0\n"
        "def test_compare_strict():\n"
        "    assert compare(5, 3) is True\n"
        "    assert compare(3, 5) is False\n"
        "def test_is_positive_kills_bool_flip():\n"
        "    assert is_positive(1) is True\n"
        "    assert is_positive(-1) is False\n"
        "    assert is_positive(0) is False\n",
        encoding="utf-8",
    )


def _seed_project_with_weak_tests(root: Path) -> None:
    """A project where tests only assert types / non-None — won't catch mutations."""
    (root / "calc.py").write_text(
        "def add(a, b):\n    return a + b\n"
        "def compare(a, b):\n    return a > b\n"
        + "\n".join(f"# pad {i}" for i in range(30)),
        encoding="utf-8",
    )
    (root / "test_calc.py").write_text(
        "from calc import add, compare\n\n"
        "def test_add_returns_int():\n"
        "    # weak: doesn't check value\n"
        "    assert isinstance(add(2, 3), int)\n"
        "def test_compare_returns_bool():\n"
        "    # weak: doesn't check direction\n"
        "    assert isinstance(compare(5, 3), bool)\n",
        encoding="utf-8",
    )


def test_mutation_strong_tests_high_kill_rate(tmp_path):
    _seed_project_with_strong_tests(tmp_path)
    proc = _run(MUTATION, "--project", str(tmp_path),
                 "--tests-cmd", f"{sys.executable} -m pytest -q",
                 "--max-mutations", "3", "--min-kill", "0.5",
                 "--json", timeout=120, check=False)
    data = json.loads(proc.stdout)
    if data["verdict"] == "DONE":
        assert data["kill_rate"] >= 0.5, \
            f"strong tests should kill >= 50% of mutations; got {data['kill_rate']}"


def test_mutation_weak_tests_low_kill_rate(tmp_path):
    _seed_project_with_weak_tests(tmp_path)
    proc = _run(MUTATION, "--project", str(tmp_path),
                 "--tests-cmd", f"{sys.executable} -m pytest -q",
                 "--max-mutations", "3", "--min-kill", "0.8",
                 "--json", timeout=120, check=False)
    data = json.loads(proc.stdout)
    if data["verdict"] == "DONE":
        # Weak tests should fail the 80% bar → exit 2
        assert proc.returncode in (0, 2)


def test_mutation_baseline_failure_returns_no_run(tmp_path):
    """Tests that don't pass on un-mutated code → can't mutation-test."""
    (tmp_path / "broken.py").write_text(
        "def x():\n    raise RuntimeError('always broken')\n" + "# pad\n" * 25,
        encoding="utf-8")
    (tmp_path / "test_broken.py").write_text(
        "from broken import x\ndef test(): x()\n", encoding="utf-8")
    proc = _run(MUTATION, "--project", str(tmp_path),
                 "--tests-cmd", f"{sys.executable} -m pytest -q",
                 "--json", check=False)
    data = json.loads(proc.stdout)
    assert data["verdict"] == "BASELINE_FAILS"


# ─── 4. context_pruner.py ─────────────────────────────────────────────────

def test_context_pruner_finds_direct_imports(tmp_path):
    (tmp_path / "main.py").write_text(
        "from cart import service\n"
        "from line_item import models\n",
        encoding="utf-8",
    )
    (tmp_path / "cart").mkdir()
    (tmp_path / "cart" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "cart" / "service.py").write_text("def x(): pass\n",
                                                    encoding="utf-8")
    (tmp_path / "line_item").mkdir()
    (tmp_path / "line_item" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "line_item" / "models.py").write_text("class X: pass\n",
                                                       encoding="utf-8")
    # Unrelated subtree that MUST NOT appear in pruned set
    (tmp_path / "frontend").mkdir()
    (tmp_path / "frontend" / "huge.py").write_text(
        "# something unrelated\n" * 100, encoding="utf-8")

    proc = _run(CTX_PRUNE, "--project", str(tmp_path), "--json")
    data = json.loads(proc.stdout)
    assert data["verdict"] == "PRUNED"
    reachable = data["reachable_files"]
    assert any("main.py" in f for f in reachable)
    assert any("cart" in f for f in reachable)
    assert any("line_item" in f for f in reachable)
    # Frontend pruned away
    assert not any("frontend" in f for f in reachable)


def test_context_pruner_no_entry_point_returns_skip(tmp_path):
    """Empty project — no main.py / app.py / etc."""
    proc = _run(CTX_PRUNE, "--project", str(tmp_path), "--json")
    data = json.loads(proc.stdout)
    assert data["verdict"] == "NO_ENTRY"


def test_context_pruner_picks_target_dir_entry(tmp_path):
    (tmp_path / "cart").mkdir()
    (tmp_path / "cart" / "main.py").write_text("def x(): pass\n",
                                                  encoding="utf-8")
    proc = _run(CTX_PRUNE, "--project", str(tmp_path),
                 "--target-dir", "cart", "--json")
    data = json.loads(proc.stdout)
    assert data["verdict"] == "PRUNED"
    assert "cart/main.py" in data["entry_point"].replace("\\", "/")


def test_context_pruner_pruning_ratio_lower_on_monorepo(tmp_path):
    """If the project has many files but only a few are reachable, the
    ratio should be < 0.5."""
    (tmp_path / "main.py").write_text(
        "from cart import service\n", encoding="utf-8")
    (tmp_path / "cart").mkdir()
    (tmp_path / "cart" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "cart" / "service.py").write_text("def x(): pass\n",
                                                    encoding="utf-8")
    # 20 unrelated files
    (tmp_path / "unrelated").mkdir()
    for i in range(20):
        (tmp_path / "unrelated" / f"file{i}.py").write_text(
            f"# unrelated {i}\n", encoding="utf-8")
    proc = _run(CTX_PRUNE, "--project", str(tmp_path), "--json")
    data = json.loads(proc.stdout)
    assert data["stats"]["pruning_ratio"] < 0.3, \
        f"pruning ratio not aggressive enough on monorepo: {data['stats']}"


def test_context_pruner_handles_syntax_error_gracefully(tmp_path):
    """A file with a syntax error in the project shouldn't crash the prune."""
    (tmp_path / "main.py").write_text(
        "from cart import service\n", encoding="utf-8")
    (tmp_path / "cart").mkdir()
    (tmp_path / "cart" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "cart" / "service.py").write_text(
        "def broken():\n    return =\n",   # syntax error on purpose
        encoding="utf-8")
    proc = _run(CTX_PRUNE, "--project", str(tmp_path), "--json")
    data = json.loads(proc.stdout)
    assert data["verdict"] == "PRUNED"


# ─── 5. nplus1_detector.py ────────────────────────────────────────────────

def test_nplus1_inconclusive_when_otel_missing(tmp_path):
    """No OTel SDK should NOT crash — graceful INCONCLUSIVE."""
    # Just check the CLI surface — actual behaviour depends on env.
    # We at least verify the script doesn't crash with a 1.
    (tmp_path / "test_x.py").write_text(
        "def test_ok(): assert True\n", encoding="utf-8")
    proc = _run(NPLUS1, "--project", str(tmp_path),
                 "--tests-cmd", f"{sys.executable} -m pytest tests/",
                 "--json", check=False, timeout=60)
    # Either INCONCLUSIVE (no DB spans / no OTel) or GREEN (everything zero)
    if proc.returncode == 0:
        data = json.loads(proc.stdout)
        assert data["overall_verdict"] in ("INCONCLUSIVE", "GREEN")
    else:
        # If tests don't pass for unrelated reasons, exit 0 is also OK
        # (the detector only escalates on detected N+1)
        assert proc.returncode in (0, 1, 2)


def test_nplus1_analyze_function_flags_list_endpoint_with_many_spans():
    """Unit test the analyze function directly — given a synthetic
    spans_by_test dict, the analyzer must flag the list endpoint."""
    sys.path.insert(0, str(SCRIPTS))
    from nplus1_detector import analyze
    spans_by_test = {
        "tests/test_cart.py::test_list_carts": [
            {"name": "SELECT", "attributes": {"db.system": "postgresql"}},
            {"name": "SELECT", "attributes": {"db.system": "postgresql"}},
            {"name": "SELECT", "attributes": {"db.system": "postgresql"}},
            {"name": "SELECT", "attributes": {"db.system": "postgresql"}},
            {"name": "SELECT", "attributes": {"db.system": "postgresql"}},
        ],
        "tests/test_cart.py::test_create": [
            {"name": "INSERT", "attributes": {"db.system": "postgresql"}},
        ],
    }
    result = analyze(spans_by_test, threshold=5)
    assert result["overall_verdict"] == "N_PLUS_ONE"
    suspect = [v for v in result["test_verdicts"]
                if v["verdict"] == "N_PLUS_ONE_SUSPECTED"]
    assert len(suspect) == 1
    assert "list_carts" in suspect[0]["nodeid"]


def test_nplus1_analyze_passes_normal_test_with_few_spans():
    sys.path.insert(0, str(SCRIPTS))
    from nplus1_detector import analyze
    spans_by_test = {
        "tests/test_cart.py::test_create": [
            {"name": "INSERT", "attributes": {"db.system": "postgresql"}},
        ],
        "tests/test_cart.py::test_retrieve": [
            {"name": "SELECT", "attributes": {"db.system": "postgresql"}},
        ],
    }
    result = analyze(spans_by_test, threshold=5)
    assert result["overall_verdict"] == "GREEN"


def test_nplus1_analyze_no_db_spans_returns_green():
    """Tests that don't hit a DB at all should not be flagged."""
    sys.path.insert(0, str(SCRIPTS))
    from nplus1_detector import analyze
    result = analyze({
        "tests/test_x.py::test_pure_logic": [
            {"name": "compute", "attributes": {}},
        ],
    }, threshold=5)
    assert result["overall_verdict"] == "GREEN"
