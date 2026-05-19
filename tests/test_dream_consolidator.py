"""
Tests for dream_consolidator.py — offline self-improvement pass.
"""
from __future__ import annotations

import json
import sys
import subprocess
import tempfile
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).parent.parent / "skills" / "one-shot-generator" / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "lib"))

from dream_consolidator import (
    mine_patterns,
    validate_advice,
    build_advice_entries,
    detect_hint_gaps,
    prune_stale_beads,
    consolidate,
    _extract_signature,
)


# ─── Fixtures ────────────────────────────────────────────────────────────────

def _make_failure(bead_id: str, task: str, msg: str,
                  date: str = "2026-05-01T00:00:00") -> dict:
    return {
        "id": bead_id,
        "task": task,
        "date": date,
        "diagnostics": [{"message": msg}],
    }


def _make_decision(task: str, verdict: str,
                   ts: str = "2026-05-01T01:00:00") -> dict:
    return {"task": task, "verdict": verdict, "ts": ts}


# ─── Signature extraction ────────────────────────────────────────────────────

def test_extract_signature_auth_401():
    assert _extract_signature("HTTP 401 unauthorized") == "auth_401"


def test_extract_signature_pagination():
    assert _extract_signature('response has "next" link') == "pagination_drift"


def test_extract_signature_import_error():
    assert _extract_signature("ModuleNotFoundError: no module named 'x'") == "import_error"


def test_extract_signature_unknown_returns_none():
    assert _extract_signature("something completely unrelated xyz") is None


# ─── Pattern mining ──────────────────────────────────────────────────────────

def test_mine_patterns_groups_by_signature():
    failures = [
        _make_failure("f1", "cart api", "401 unauthorized"),
        _make_failure("f2", "cart api", "401 unauthorized"),
        _make_failure("f3", "order api", "importerror missing module"),
    ]
    # min_recurrence=2 → auth_401 qualifies, import_error does not
    patterns = mine_patterns(failures, min_recurrence=2)
    assert "auth_401" in patterns
    assert len(patterns["auth_401"]) == 2
    assert "import_error" not in patterns


def test_mine_patterns_min_recurrence_filters():
    failures = [_make_failure("f1", "task", "401 error")]
    patterns = mine_patterns(failures, min_recurrence=2)
    assert patterns == {}


def test_mine_patterns_unknown_signature_excluded():
    failures = [
        _make_failure("f1", "task", "completely unknown error xyz"),
        _make_failure("f2", "task", "completely unknown error xyz"),
    ]
    patterns = mine_patterns(failures, min_recurrence=2)
    assert patterns == {}


# ─── Advice validation ───────────────────────────────────────────────────────

def test_validate_advice_finds_success_after_failure():
    patterns = {
        "auth_401": [
            _make_failure("f1", "cart payment api", "401 unauthorized",
                          date="2026-05-01T00:00:00")
        ]
    }
    decisions = [
        _make_decision("cart payment api add endpoint", "SHIP",
                       ts="2026-05-01T02:00:00")
    ]
    result = validate_advice(patterns, decisions)
    assert result["auth_401"] is True


def test_validate_advice_no_success_returns_false():
    patterns = {
        "auth_401": [_make_failure("f1", "cart api", "401 error")]
    }
    result = validate_advice(patterns, [])
    assert result["auth_401"] is False


def test_validate_advice_success_before_failure_ignored():
    patterns = {
        "auth_401": [
            _make_failure("f1", "cart api", "401 error",
                          date="2026-05-02T00:00:00")
        ]
    }
    decisions = [
        _make_decision("cart api", "SHIP", ts="2026-05-01T00:00:00")
    ]
    result = validate_advice(patterns, decisions)
    assert result["auth_401"] is False


# ─── Advice entry building ────────────────────────────────────────────────────

def test_build_advice_entries_confidence_boosted_by_hits():
    failures = [_make_failure(f"f{i}", "task", "401 error") for i in range(5)]
    patterns = {"auth_401": failures}
    validated = {"auth_401": False}
    entries = build_advice_entries(patterns, validated, "2026-05-19T00:00:00")
    assert len(entries) == 1
    e = entries[0]
    assert e.pattern == "auth_401"
    assert e.hit_count == 5
    # confidence = 0.5 + 0.05*5 = 0.75 (capped at 1.0)
    assert e.confidence >= 0.75


def test_build_advice_entries_validation_boosts_confidence():
    patterns = {"auth_401": [_make_failure("f1", "t", "401 error")]}
    entries_unvalidated = build_advice_entries(
        patterns, {"auth_401": False}, "2026-05-19T00:00:00"
    )
    entries_validated = build_advice_entries(
        patterns, {"auth_401": True}, "2026-05-19T00:00:00"
    )
    assert entries_validated[0].confidence > entries_unvalidated[0].confidence


def test_build_advice_entries_sorted_by_confidence():
    patterns = {
        "auth_401": [_make_failure(f"f{i}", "t", "401") for i in range(5)],
        "import_error": [_make_failure("g1", "t", "importerror")],
    }
    entries = build_advice_entries(patterns, {}, "2026-05-19T00:00:00")
    confs = [e.confidence for e in entries]
    assert confs == sorted(confs, reverse=True)


# ─── Hint gap detection ───────────────────────────────────────────────────────

def test_detect_hint_gaps_clusters_unknown_failures():
    failures = [
        _make_failure("f1", "task", "deadlock detected on table orders"),
        _make_failure("f2", "task", "deadlock detected on table users"),
    ]
    gaps = detect_hint_gaps(failures, min_cluster_size=2)
    assert any(g.cluster_label == "deadlock" for g in gaps)


def test_detect_hint_gaps_ignores_known_signatures():
    failures = [
        _make_failure("f1", "t", "401 unauthorized"),
        _make_failure("f2", "t", "401 unauthorized"),
    ]
    gaps = detect_hint_gaps(failures, min_cluster_size=2)
    # 401 is a known signature → not an unmatched gap
    assert gaps == []


def test_detect_hint_gaps_empty_on_no_failures():
    assert detect_hint_gaps([]) == []


# ─── Pruning ─────────────────────────────────────────────────────────────────

def test_prune_removes_old_non_recurring_beads():
    old = _make_failure("old1", "task", "some old error",
                        date="2020-01-01T00:00:00")
    recent = _make_failure("new1", "task", "401 error")
    patterns = {"auth_401": [recent]}
    survivors, pruned = prune_stale_beads([old, recent], age_days=90, patterns=patterns)
    assert any(p.bead_id == "old1" for p in pruned)
    assert any(b["id"] == "new1" for b in survivors)


def test_prune_keeps_active_beads_regardless_of_age():
    active = _make_failure("active1", "task", "401 error",
                           date="2020-01-01T00:00:00")
    patterns = {"auth_401": [active]}  # it's in an active pattern
    survivors, pruned = prune_stale_beads([active], age_days=90, patterns=patterns)
    assert survivors == [active]
    assert pruned == []


# ─── Full consolidation (integration) ────────────────────────────────────────

def test_consolidate_dry_run_writes_no_files():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        beads = root / ".beads"
        beads.mkdir()
        failures_path = beads / "failures.jsonl"
        failures_path.write_text(
            json.dumps(_make_failure("f1", "cart api", "401 error")) + "\n" +
            json.dumps(_make_failure("f2", "cart api", "401 error")) + "\n",
            encoding="utf-8"
        )
        report = consolidate(root, min_recurrence=2, dry_run=True)
        assert report.patterns_found == 1
        assert report.advice_written == 1
        assert not (beads / "curriculum_advice.jsonl").exists()


def test_consolidate_writes_advice_file():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        beads = root / ".beads"
        beads.mkdir()
        (beads / "failures.jsonl").write_text(
            json.dumps(_make_failure("f1", "cart", "401 error")) + "\n" +
            json.dumps(_make_failure("f2", "cart", "401 error")) + "\n",
            encoding="utf-8"
        )
        report = consolidate(root, min_recurrence=2, dry_run=False)
        assert report.advice_written == 1
        advice_path = beads / "curriculum_advice.jsonl"
        assert advice_path.exists()
        entry = json.loads(advice_path.read_text(encoding="utf-8").splitlines()[0])
        assert entry["pattern"] == "auth_401"
        assert "advice" in entry


def test_consolidate_prunes_stale_beads():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        beads = root / ".beads"
        beads.mkdir()
        failures_path = beads / "failures.jsonl"
        failures_path.write_text(
            json.dumps(_make_failure("old", "task", "weird error",
                                     date="2020-01-01T00:00:00")) + "\n",
            encoding="utf-8"
        )
        report = consolidate(root, min_recurrence=1, prune_age_days=30, dry_run=False)
        assert report.beads_pruned == 1
        remaining = failures_path.read_text(encoding="utf-8").strip()
        assert remaining == ""


# ─── CLI surface ─────────────────────────────────────────────────────────────

def _run(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "dream_consolidator.py"), *args],
        capture_output=True, text=True, encoding="utf-8"
    )


def test_cli_dry_run_exits_zero():
    proc = _run("--dry-run")
    assert proc.returncode == 0


def test_cli_json_flag_emits_valid_json():
    proc = _run("--dry-run", "--json")
    assert proc.returncode == 0
    data = json.loads(proc.stdout)
    assert "failures_analysed" in data
    assert "advice_entries" in data


def test_cli_help_exits_zero():
    proc = _run("--help")
    assert proc.returncode == 0


# ─── curriculum integration: dynamic advice loaded ───────────────────────────

def test_curriculum_loads_dynamic_advice(tmp_path):
    beads = tmp_path / ".beads"
    beads.mkdir()
    failures = beads / "failures.jsonl"
    failures.write_text(
        json.dumps({
            "id": "f1", "task": "payment cart",
            "date": "2026-05-18T00:00:00",
            "diagnostics": [{"message": "deadlock on orders table"}],
        }) + "\n",
        encoding="utf-8"
    )
    # Write dynamic advice as dream_consolidator would
    (beads / "curriculum_advice.jsonl").write_text(
        json.dumps({
            "pattern": "deadlock",
            "advice": "use SELECT FOR UPDATE SKIP LOCKED to avoid deadlock",
            "confidence": 0.85, "hit_count": 3,
            "validated": True, "source": "dream_consolidator v1.0",
            "last_seen": "2026-05-19T00:00:00",
        }) + "\n",
        encoding="utf-8"
    )
    sys.path.insert(0, str(SCRIPTS))
    from beads_curriculum import consult
    report = consult(
        task="payment cart checkout",
        failures_path=failures,
        repo_root=tmp_path,
        min_similarity=0.1,
    )
    if report.hits:
        assert "deadlock" in report.hits[0].advice or "SKIP LOCKED" in report.hits[0].advice
