"""Tests for scripts/cost_stats.py.

Verifies aggregation logic against synthetic observation logs.
Does NOT test the real .beads/cost_observations.jsonl — that's a moving target.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import cost_stats  # noqa: E402


def _write_obs(path: Path, rows: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def test_empty_log_returns_zero_confidence(tmp_path: Path) -> None:
    log = tmp_path / "obs.jsonl"
    log.write_text("")
    observations = cost_stats._load_observations(log)
    report = cost_stats.build_report(observations, cost_stats._PRICING_FALLBACK)
    assert report["samples"] == 0
    assert report["confidence"] == "none"
    assert report["agents"] == {}


def test_six_architect_runs_yield_low_confidence(tmp_path: Path) -> None:
    log = tmp_path / "obs.jsonl"
    _write_obs(log, [
        {"agent": "architect", "model": "sonnet", "input": 14000, "output": 12000},
        {"agent": "architect", "model": "sonnet", "input": 14000, "output": 11000},
        {"agent": "architect", "model": "sonnet", "input": 13000, "output": 14000},
        {"agent": "architect", "model": "sonnet", "input": 13000, "output": 12000},
        {"agent": "architect", "model": "sonnet", "input": 13000, "output": 14000},
        {"agent": "architect", "model": "sonnet", "input": 13000, "output": 13000},
    ])
    observations = cost_stats._load_observations(log)
    report = cost_stats.build_report(observations, cost_stats._PRICING_FALLBACK)
    assert report["samples"] == 6
    assert report["confidence"] == "low"
    assert "architect" in report["agents"]
    assert report["agents"]["architect"]["runs"] == 6
    # Sonnet input 13-14k @ $3/M + output 11-14k @ $15/M ≈ $0.20-$0.25
    assert 0.15 < report["agents"]["architect"]["cost_usd_p50"] < 0.30


def test_confidence_thresholds(tmp_path: Path) -> None:
    """20 samples → low-medium, 50 → medium, 100 → high."""
    log = tmp_path / "obs.jsonl"
    base = {"agent": "architect", "model": "sonnet", "input": 10000, "output": 10000}

    _write_obs(log, [base] * 20)
    r = cost_stats.build_report(cost_stats._load_observations(log), cost_stats._PRICING_FALLBACK)
    assert r["confidence"] == "low-medium"

    _write_obs(log, [base] * 50)
    r = cost_stats.build_report(cost_stats._load_observations(log), cost_stats._PRICING_FALLBACK)
    assert r["confidence"] == "medium"

    _write_obs(log, [base] * 100)
    r = cost_stats.build_report(cost_stats._load_observations(log), cost_stats._PRICING_FALLBACK)
    assert r["confidence"] == "high"


def test_per_agent_breakdown(tmp_path: Path) -> None:
    log = tmp_path / "obs.jsonl"
    _write_obs(log, [
        {"agent": "architect", "model": "sonnet", "input": 13000, "output": 12000},
        {"agent": "implementer", "model": "haiku", "input": 8000, "output": 6000},
        {"agent": "implementer", "model": "haiku", "input": 9000, "output": 7000},
        {"agent": "reviewer", "model": "sonnet", "input": 5000, "output": 3000},
    ])
    observations = cost_stats._load_observations(log)
    report = cost_stats.build_report(observations, cost_stats._PRICING_FALLBACK)
    assert set(report["agents"]) == {"architect", "implementer", "reviewer"}
    assert report["agents"]["implementer"]["runs"] == 2
    # Haiku is cheaper than sonnet → implementer cost < architect cost
    assert report["agents"]["implementer"]["cost_usd_p50"] < report["agents"]["architect"]["cost_usd_p50"]


def test_invalid_jsonl_lines_skipped(tmp_path: Path) -> None:
    log = tmp_path / "obs.jsonl"
    log.write_text(
        '{"agent": "architect", "model": "sonnet", "input": 1000, "output": 1000}\n'
        'not valid json\n'
        '\n'
        '{"agent": "architect", "model": "sonnet", "input": 2000, "output": 2000}\n'
    )
    observations = cost_stats._load_observations(log)
    assert len(observations) == 2


def test_missing_log_returns_empty(tmp_path: Path) -> None:
    observations = cost_stats._load_observations(tmp_path / "nope.jsonl")
    assert observations == []


def test_unknown_model_yields_none_cost(tmp_path: Path) -> None:
    """Defensive: an observation with an unrecognised model shouldn't crash."""
    log = tmp_path / "obs.jsonl"
    _write_obs(log, [{"agent": "architect", "model": "future-model-9", "input": 1000, "output": 1000}])
    observations = cost_stats._load_observations(log)
    report = cost_stats.build_report(observations, cost_stats._PRICING_FALLBACK)
    assert report["agents"]["architect"]["cost_usd_p50"] is None
