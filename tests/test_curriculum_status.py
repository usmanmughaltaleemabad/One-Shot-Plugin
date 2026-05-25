"""Tests for scripts/curriculum_status.py."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import curriculum_status  # noqa: E402


def _write(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")


def test_cold_loop_when_no_runtime(tmp_path: Path) -> None:
    seed = tmp_path / "seed.jsonl"
    runtime = tmp_path / "rt.jsonl"
    _write(seed, [{"id": "bd-001", "reason": "FK type mismatch"}])
    runtime.write_text("")
    s = curriculum_status.build_status(seed, runtime)
    assert s["loop_status"] == "cold"
    assert s["seed_entries"] == 1
    assert s["runtime_entries"] == 0
    assert s["runtime_share"] == 0.0


def test_warming_loop(tmp_path: Path) -> None:
    seed = tmp_path / "seed.jsonl"
    runtime = tmp_path / "rt.jsonl"
    _write(seed, [{"id": f"bd-{i}", "reason": f"seed {i}"} for i in range(10)])
    _write(runtime, [{"id": f"rt-{i}", "reason": f"runtime {i}", "timestamp": f"2026-05-{20+i:02d}"}
                     for i in range(5)])
    s = curriculum_status.build_status(seed, runtime)
    assert s["loop_status"] == "warming"
    assert s["runtime_entries"] == 5
    assert s["newest_runtime"] == "2026-05-24"


def test_active_loop_at_25_runtime(tmp_path: Path) -> None:
    seed = tmp_path / "seed.jsonl"
    runtime = tmp_path / "rt.jsonl"
    _write(seed, [{"id": "s1", "reason": "x"}])
    _write(runtime, [{"id": f"r{i}", "reason": f"r{i}"} for i in range(25)])
    s = curriculum_status.build_status(seed, runtime)
    assert s["loop_status"] == "active"


def test_mature_loop_at_100_runtime(tmp_path: Path) -> None:
    seed = tmp_path / "seed.jsonl"
    runtime = tmp_path / "rt.jsonl"
    _write(seed, [{"id": "s1", "reason": "x"}])
    _write(runtime, [{"id": f"r{i}", "reason": f"r{i}"} for i in range(100)])
    s = curriculum_status.build_status(seed, runtime)
    assert s["loop_status"] == "mature"


def test_missing_files_return_zero(tmp_path: Path) -> None:
    s = curriculum_status.build_status(
        tmp_path / "nope-seed.jsonl",
        tmp_path / "nope-runtime.jsonl",
    )
    assert s["seed_entries"] == 0
    assert s["runtime_entries"] == 0
    assert s["loop_status"] == "cold"


def test_topics_deduped(tmp_path: Path) -> None:
    seed = tmp_path / "seed.jsonl"
    runtime = tmp_path / "rt.jsonl"
    _write(seed, [
        {"id": "1", "reason": "FK type mismatch"},
        {"id": "2", "reason": "FK type mismatch"},  # duplicate topic
        {"id": "3", "reason": "Pagination envelope mismatch"},
    ])
    runtime.write_text("")
    s = curriculum_status.build_status(seed, runtime)
    assert len(s["topics_covered"]) == 2


def test_against_real_files() -> None:
    """Smoke test against the shipped curriculum files (no assertions about counts,
    just that the report builds successfully)."""
    s = curriculum_status.build_status()
    assert "loop_status" in s
    assert s["seed_entries"] >= 0
    assert s["runtime_entries"] >= 0
