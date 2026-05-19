"""Tests for v4.7 — integration tightening + remaining Osmani absorptions.

Covers:
  - learnings_hub dashboard subcommand (trend + drift detection)
  - /adr slash command exists with valid frontmatter
  - /dashboard slash command exists
  - 4 new cross-cutting hints: performance_optimization, error_recovery,
    debugging_strategy, git_workflow
  - SKILL.md updated: doubt-driven defaults on, ship-check runs before
    --apply, ADR emission alongside spec.json
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "skills" / "one-shot-generator" / "scripts"
HUB = SCRIPTS / "learnings_hub.py"
HINTS = SCRIPTS / "body_hints.py"


def _run(script: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True, text=True, env=env, encoding="utf-8", timeout=30,
    )
    if check:
        assert proc.returncode == 0, \
            f"{script.name} failed (exit {proc.returncode}): {proc.stderr}"
    return proc


def _seed_registry(repo: Path, rows: list[dict]) -> None:
    """Write a fake learnings.jsonl directly so tests can control timestamps."""
    reg = repo / ".claude" / "registry"
    reg.mkdir(parents=True, exist_ok=True)
    with (reg / "learnings.jsonl").open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def _iso(d: datetime) -> str:
    return d.replace(microsecond=0, tzinfo=None).isoformat() + "Z"


# ─── learnings_hub dashboard ────────────────────────────────────────────────

def test_dashboard_flags_degrading_agent(tmp_path):
    """Recent success rate drops > 15 points vs prior window → drift_flag=degrading."""
    now = datetime.now()
    rows = []
    # Prior window: 10 successes for architect (30-60 days ago)
    for i in range(10):
        rows.append({"ts": _iso(now - timedelta(days=45)),
                     "agent_id": "local/architect", "task_keywords": [],
                     "outcome": "succeeded", "duration_ms": 0,
                     "cost_usd": None, "notes": ""})
    # Recent window: 4 succ + 6 fail = 40% rate (well below 100% baseline)
    for i in range(4):
        rows.append({"ts": _iso(now - timedelta(days=5)),
                     "agent_id": "local/architect", "task_keywords": [],
                     "outcome": "succeeded", "duration_ms": 0,
                     "cost_usd": None, "notes": ""})
    for i in range(6):
        rows.append({"ts": _iso(now - timedelta(days=3)),
                     "agent_id": "local/architect", "task_keywords": [],
                     "outcome": "failed", "duration_ms": 0,
                     "cost_usd": None, "notes": ""})
    _seed_registry(tmp_path, rows)

    proc = _run(HUB, "--repo-root", str(tmp_path), "dashboard")
    data = json.loads(proc.stdout)
    arch = next(a for a in data["agents"] if a["agent_id"] == "local/architect")
    assert arch["drift_flag"] == "degrading", \
        f"40% recent vs 100% prior should flag degrading; got {arch['drift_flag']} (drift={arch['drift']})"
    assert arch["drift"] < 0
    assert data["overall"]["agents_degrading"] == 1


def test_dashboard_no_baseline_when_only_recent_data(tmp_path):
    now = datetime.now()
    rows = [{"ts": _iso(now - timedelta(days=2)),
             "agent_id": "local/architect", "task_keywords": [],
             "outcome": "succeeded", "duration_ms": 0,
             "cost_usd": None, "notes": ""}]
    _seed_registry(tmp_path, rows)
    proc = _run(HUB, "--repo-root", str(tmp_path), "dashboard")
    data = json.loads(proc.stdout)
    arch = next(a for a in data["agents"] if a["agent_id"] == "local/architect")
    assert arch["drift_flag"] == "no_baseline"
    assert arch["prior_sample_count"] == 0


def test_dashboard_stable_when_rates_match(tmp_path):
    now = datetime.now()
    rows = []
    # 5 succ + 5 fail in BOTH windows
    for window_offset in (45, 5):
        for outcome in (["succeeded"] * 5 + ["failed"] * 5):
            rows.append({"ts": _iso(now - timedelta(days=window_offset)),
                         "agent_id": "local/architect", "task_keywords": [],
                         "outcome": outcome, "duration_ms": 0,
                         "cost_usd": None, "notes": ""})
    _seed_registry(tmp_path, rows)
    proc = _run(HUB, "--repo-root", str(tmp_path), "dashboard")
    data = json.loads(proc.stdout)
    arch = next(a for a in data["agents"] if a["agent_id"] == "local/architect")
    assert arch["drift_flag"] == "stable"


def test_dashboard_respects_custom_window(tmp_path):
    """--window-days=7 vs default 30 should give different segmentations."""
    now = datetime.now()
    rows = []
    # 5 succ in days 0-6
    for _ in range(5):
        rows.append({"ts": _iso(now - timedelta(days=2)),
                     "agent_id": "local/critic", "task_keywords": [],
                     "outcome": "succeeded", "duration_ms": 0,
                     "cost_usd": None, "notes": ""})
    # 5 fail in days 7-14
    for _ in range(5):
        rows.append({"ts": _iso(now - timedelta(days=10)),
                     "agent_id": "local/critic", "task_keywords": [],
                     "outcome": "failed", "duration_ms": 0,
                     "cost_usd": None, "notes": ""})
    _seed_registry(tmp_path, rows)

    # Default 30-day window: all 10 rows are 'recent' → 50% rate, no prior baseline
    default = json.loads(_run(HUB, "--repo-root", str(tmp_path),
                              "dashboard").stdout)
    crit_default = next(a for a in default["agents"]
                        if a["agent_id"] == "local/critic")
    assert crit_default["recent_sample_count"] == 10

    # 7-day window: recent=5 (succ), prior=5 (fail) → recent 100% vs prior 0% → warming
    short = json.loads(_run(HUB, "--repo-root", str(tmp_path),
                            "dashboard", "--window-days", "7").stdout)
    crit_short = next(a for a in short["agents"]
                      if a["agent_id"] == "local/critic")
    assert crit_short["recent_sample_count"] == 5
    assert crit_short["prior_sample_count"] == 5
    assert crit_short["drift_flag"] == "warming"


def test_dashboard_respects_custom_drift_threshold(tmp_path):
    """A 10-point drop should be 'stable' at default 0.15 threshold but
    'degrading' at 0.05."""
    now = datetime.now()
    rows = []
    # Prior: 10 succ
    for _ in range(10):
        rows.append({"ts": _iso(now - timedelta(days=45)),
                     "agent_id": "local/x", "task_keywords": [],
                     "outcome": "succeeded", "duration_ms": 0,
                     "cost_usd": None, "notes": ""})
    # Recent: 9 succ + 1 fail = 90%
    for _ in range(9):
        rows.append({"ts": _iso(now - timedelta(days=5)),
                     "agent_id": "local/x", "task_keywords": [],
                     "outcome": "succeeded", "duration_ms": 0,
                     "cost_usd": None, "notes": ""})
    rows.append({"ts": _iso(now - timedelta(days=5)),
                 "agent_id": "local/x", "task_keywords": [],
                 "outcome": "failed", "duration_ms": 0,
                 "cost_usd": None, "notes": ""})
    _seed_registry(tmp_path, rows)

    default = json.loads(_run(HUB, "--repo-root", str(tmp_path),
                              "dashboard").stdout)
    sensitive = json.loads(_run(HUB, "--repo-root", str(tmp_path),
                                 "dashboard", "--drift-threshold", "0.05").stdout)
    a_default = next(a for a in default["agents"] if a["agent_id"] == "local/x")
    a_sensitive = next(a for a in sensitive["agents"] if a["agent_id"] == "local/x")
    assert a_default["drift_flag"] == "stable"
    assert a_sensitive["drift_flag"] == "degrading"


# ─── /adr + /dashboard slash commands ──────────────────────────────────────

def test_adr_slash_command_exists():
    path = REPO_ROOT / "commands" / "adr.md"
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "argument-hint:" in text
    assert "adr_writer.py" in text
    assert "emit" in text and "list" in text


def test_dashboard_slash_command_exists():
    path = REPO_ROOT / "commands" / "dashboard.md"
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "argument-hint:" in text
    assert "dashboard" in text.lower()
    assert "degrading" in text.lower()


# ─── 4 new cross-cutting hints ─────────────────────────────────────────────

V47_CONTRACTS = [
    "performance_optimization",
    "error_recovery",
    "debugging_strategy",
    "git_workflow",
]


def test_all_v47_contracts_present():
    proc = _run(HINTS, "--list", "--json")
    kinds = {h["kind"] for h in json.loads(proc.stdout) if h["framework"] == "common"}
    missing = set(V47_CONTRACTS) - kinds
    assert not missing, f"missing v4.7 contracts: {missing}"


def test_performance_optimization_demands_measurement():
    proc = _run(HINTS, "--framework", "common", "--kind", "performance_optimization")
    data = json.loads(proc.stdout)
    anti = " ".join(data["anti_patterns"]).lower()
    assert "without a profiler" in anti or "profiler" in anti
    assert "n+1" in anti, "N+1 must be called out as the dominant slowdown"
    blob = json.dumps(data).lower()
    assert "p95" in blob and "p99" in blob, "must measure tail latency, not just mean"


def test_error_recovery_keeps_http_at_boundary():
    proc = _run(HINTS, "--framework", "common", "--kind", "error_recovery")
    data = json.loads(proc.stdout)
    anti = " ".join(data["anti_patterns"]).lower()
    assert "httpexception" in anti or "http" in anti, \
        "service layer must not throw HTTP exceptions"
    assert "200" in anti and "error" in anti, \
        "must rule out 200 + {error: ...} pattern"
    must = " ".join(data["must_emit"]).lower()
    assert "request_id" in must or "request id" in must


def test_debugging_strategy_requires_reproduction():
    proc = _run(HINTS, "--framework", "common", "--kind", "debugging_strategy")
    data = json.loads(proc.stdout)
    anti = " ".join(data["anti_patterns"]).lower()
    assert "can't reproduce" in anti or "cannot reproduce" in anti
    must = " ".join(data["must_emit"]).lower()
    assert "failing test" in must, "must require a failing test before the fix"


def test_git_workflow_blocks_force_push_to_main():
    proc = _run(HINTS, "--framework", "common", "--kind", "git_workflow")
    data = json.loads(proc.stdout)
    anti = " ".join(data["anti_patterns"]).lower()
    assert "force-push" in anti or "force push" in anti
    assert "shared branch" in anti or "main" in anti
    assert "wip" in anti or "fix\"" in anti, "must warn against worthless commit messages"


# ─── SKILL.md integration tightening ───────────────────────────────────────

def test_skill_md_marks_doubt_driven_as_default_on():
    from conftest import pipeline_text
    text = pipeline_text()
    assert "Stage 5.5" in text
    assert "DEFAULT ON" in text, \
        "doubt-driven must be marked default-on, not opt-in"
    # the opt-out flag is mentioned
    assert "--no-doubt" in text


def test_skill_md_runs_ship_gates_before_apply():
    from conftest import pipeline_text
    text = pipeline_text()
    assert "ship_gates.py" in text, \
        "ship_gates must be wired into the apply flow"
    assert "--no-ship-check" in text, "opt-out flag must be documented"
    assert "BLOCKED" in text and "READY" in text


def test_skill_md_emits_adr_alongside_spec():
    from conftest import pipeline_text
    text = pipeline_text()
    assert "adr_writer.py" in text, "ADR writer must be invoked from SKILL.md"
    assert "--no-adr" in text, "opt-out flag must be documented"


# ─── catalogue size ────────────────────────────────────────────────────────

def test_body_hints_total_count_after_v47():
    """v4.6 ended at 97. v4.7 adds 4 cross-cutting contracts. Expect >= 101."""
    proc = _run(HINTS, "--list", "--json")
    data = json.loads(proc.stdout)
    assert len(data) >= 101, f"expected >= 101 after v4.7, got {len(data)}"
