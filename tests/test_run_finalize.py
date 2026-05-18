"""Tests for the run_finalize wiring (v4.5).

run_finalize closes the loop between the critic loop driver and the
learnings hub. Given a sandbox containing a loop state plus a list of
agents that ran, it derives a per-agent outcome and writes one row per
agent to .claude/registry/learnings.jsonl via learnings_hub.

Tests use a temporary --repo-root so they never write to the real
registry. The driver helper is also exercised end-to-end here to make
sure the contract between the two scripts stays in sync.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "skills" / "one-shot-generator" / "scripts"
DRIVER = SCRIPTS / "critic_loop_driver.py"
FINALIZE = SCRIPTS / "run_finalize.py"


def _run(script: Path, *args: str, cwd: Path | None = None,
         check: bool = True) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True, text=True, env=env, encoding="utf-8", timeout=30,
        cwd=str(cwd) if cwd is not None else None,
    )
    if check:
        assert proc.returncode == 0, \
            f"{script.name} failed (exit {proc.returncode}): {proc.stderr}"
    return proc


def _seed_loop(sandbox: Path, verdict: dict, tmp_path: Path) -> None:
    """Helper: run driver init + record once with the supplied verdict."""
    _run(DRIVER, "init", "--sandbox", str(sandbox))
    vp = tmp_path / "verdict.json"
    vp.write_text(json.dumps(verdict), encoding="utf-8")
    _run(DRIVER, "record", "--sandbox", str(sandbox), "--verdict", str(vp))


def _sandbox_repo(tmp_path: Path) -> Path:
    """Create an isolated 'plugin repo' that mirrors the structure
    run_finalize expects (just .claude/registry/ — learnings_hub script
    is reached via sys.executable + absolute path, not via cwd lookup)."""
    repo = tmp_path / "fake-repo"
    (repo / ".claude" / "registry").mkdir(parents=True)
    # learnings_hub also needs access to its sibling scripts via lib/.
    # Since run_finalize shells out using SCRIPTS/learnings_hub.py with
    # cwd=repo, learnings_hub will write to repo/.claude/registry/. Good.
    # But it imports lib.base_script — needs sys.path. The script itself
    # adds scripts/ to sys.path via bootstrap_runtime, so all we need is
    # for it to RUN from the actual scripts dir. That's already what
    # subprocess uses (sys.executable + absolute script path), with cwd
    # set to the repo so its relative LEARNINGS_PATH resolves into the
    # fake repo. Done.
    return repo


def _read_learnings(repo: Path) -> list[dict]:
    path = repo / ".claude" / "registry" / "learnings.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


# ─── SHIPPED: everyone succeeds ─────────────────────────────────────────────

def test_shipped_records_one_succeeded_row_per_agent(tmp_path):
    repo = _sandbox_repo(tmp_path)
    sbx = tmp_path / "sandbox"
    _seed_loop(sbx, {"verdict": "SHIPPED"}, tmp_path)

    agents = "architect,implementer,test-author,reviewer,wirer,critic"
    proc = _run(FINALIZE,
                "--sandbox", str(sbx),
                "--agents", agents,
                "--task-keywords", "shopping cart with line items and discounts",
                "--repo-root", str(repo))
    summary = json.loads(proc.stdout)

    assert summary["final_verdict"] == "SHIPPED"
    assert summary["iterations"] == 0
    assert len(summary["recorded"]) == 6

    rows = _read_learnings(repo)
    assert len(rows) == 6
    assert all(r["outcome"] == "succeeded" for r in rows)
    agent_ids = {r["agent_id"] for r in rows}
    assert agent_ids == {
        "local/architect", "local/implementer", "local/test-author",
        "local/reviewer", "local/wirer", "local/critic",
    }


def test_shipped_records_extracted_keywords(tmp_path):
    repo = _sandbox_repo(tmp_path)
    sbx = tmp_path / "sandbox"
    _seed_loop(sbx, {"verdict": "SHIPPED"}, tmp_path)

    _run(FINALIZE,
         "--sandbox", str(sbx),
         "--agents", "architect",
         "--task-keywords", "build a shopping cart with line items and discounts",
         "--repo-root", str(repo))

    rows = _read_learnings(repo)
    assert len(rows) == 1
    kw = rows[0]["task_keywords"]
    # Stop-words filtered out
    assert "build" not in kw
    assert "a" not in kw
    assert "with" not in kw
    # Real content kept
    assert "shopping" in kw and "cart" in kw and "discounts" in kw


# ─── ESCALATE: agents in failing buckets get 'failed' ──────────────────────

def test_escalate_marks_failing_buckets_only(tmp_path):
    """Implementer + test-author own the failing routes; reviewer + wirer
    did their work and shouldn't be punished for the critic loop failing."""
    repo = _sandbox_repo(tmp_path)
    sbx = tmp_path / "sandbox"

    # Seed: a LOOP verdict where implementer + test-author own failures
    _run(DRIVER, "init", "--sandbox", str(sbx))
    verdict = {
        "verdict": "LOOP",
        "routes": [
            {"nodeid": "t::a", "route_to": "implementer", "reason": "x"},
            {"nodeid": "t::b", "route_to": "test-author", "reason": "y"},
        ],
    }
    vp = tmp_path / "v.json"
    vp.write_text(json.dumps(verdict), encoding="utf-8")
    _run(DRIVER, "record", "--sandbox", str(sbx), "--verdict", str(vp))

    proc = _run(FINALIZE,
                "--sandbox", str(sbx),
                "--agents", "architect,implementer,test-author,reviewer,wirer",
                "--task-keywords", "auth flow",
                "--repo-root", str(repo))
    summary = json.loads(proc.stdout)

    by_agent = {r["agent_id"]: r["outcome"] for r in summary["recorded"]}
    assert by_agent["local/implementer"] == "failed"
    assert by_agent["local/test-author"] == "failed"
    assert by_agent["local/architect"] == "succeeded"
    assert by_agent["local/reviewer"] == "succeeded"
    assert by_agent["local/wirer"] == "succeeded"

    # Persisted file reflects the same
    rows = _read_learnings(repo)
    file_outcomes = {r["agent_id"]: r["outcome"] for r in rows}
    assert file_outcomes == by_agent


# ─── error paths ───────────────────────────────────────────────────────────

def test_missing_sandbox_state_returns_exit_2(tmp_path):
    repo = _sandbox_repo(tmp_path)
    sbx = tmp_path / "never-initialized"
    sbx.mkdir()
    proc = _run(FINALIZE,
                "--sandbox", str(sbx),
                "--agents", "architect",
                "--task-keywords", "x",
                "--repo-root", str(repo),
                check=False)
    assert proc.returncode == 2
    assert "loop state" in proc.stderr.lower()


def test_empty_agents_returns_exit_1(tmp_path):
    repo = _sandbox_repo(tmp_path)
    sbx = tmp_path / "sandbox"
    _seed_loop(sbx, {"verdict": "SHIPPED"}, tmp_path)
    proc = _run(FINALIZE,
                "--sandbox", str(sbx),
                "--agents", "  ,  ,  ",   # all whitespace
                "--task-keywords", "x",
                "--repo-root", str(repo),
                check=False)
    assert proc.returncode == 1
    assert "agents" in proc.stderr.lower()


# ─── agent id prefixing (local vs external) ────────────────────────────────

def test_external_agent_ids_keep_their_namespace(tmp_path):
    """An agent like 'claude-code/code-reviewer' must keep its full id —
    only bare names get the 'local/' prefix."""
    repo = _sandbox_repo(tmp_path)
    sbx = tmp_path / "sandbox"
    _seed_loop(sbx, {"verdict": "SHIPPED"}, tmp_path)
    _run(FINALIZE,
         "--sandbox", str(sbx),
         "--agents", "architect,claude-code/code-reviewer,plan/Plan",
         "--task-keywords", "feature",
         "--repo-root", str(repo))
    ids = {r["agent_id"] for r in _read_learnings(repo)}
    assert "local/architect" in ids
    assert "claude-code/code-reviewer" in ids
    assert "plan/Plan" in ids


# ─── /learnings slash command exists with valid frontmatter ────────────────

def test_learnings_slash_command_registered():
    path = REPO_ROOT / "commands" / "learnings.md"
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "argument-hint:" in text
    assert "allowed-tools: Bash" in text
    assert "learnings_hub.py" in text
    assert "top-agents" in text
