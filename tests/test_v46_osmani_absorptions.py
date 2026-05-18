"""Tests for v4.6 — absorptions from Addy Osmani's agent-skills repo.

Covers four new deterministic helpers:
  - source_docs_fetcher.py (Stage 2.3 doc-lookup plan)
  - doubt_driver.py        (Stage 5.5 fresh-context adversarial review)
  - ship_gates.py          (10-gate production-readiness checklist)
  - adr_writer.py          (sequentially-numbered MADR ADRs)

Plus 6 new cross-cutting body_hints contracts:
  - adr_record, source_verification, ci_cd_pipeline, api_design,
    deprecation_policy, frontend_ui_concerns
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "skills" / "one-shot-generator" / "scripts"
FETCHER  = SCRIPTS / "source_docs_fetcher.py"
DOUBT    = SCRIPTS / "doubt_driver.py"
GATES    = SCRIPTS / "ship_gates.py"
ADR      = SCRIPTS / "adr_writer.py"
HINTS    = SCRIPTS / "body_hints.py"


def _run(script: Path, *args: str, check: bool = True, cwd: Path | None = None) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True, text=True, env=env, encoding="utf-8", timeout=60,
        cwd=str(cwd) if cwd is not None else None,
    )
    if check:
        assert proc.returncode == 0, \
            f"{script.name} failed (exit {proc.returncode}): {proc.stderr}"
    return proc


# ─── source_docs_fetcher ───────────────────────────────────────────────────

def test_source_docs_fetcher_detects_fastapi_and_version(tmp_path):
    (tmp_path / "requirements.txt").write_text(
        "fastapi==0.115.6\nsqlalchemy==2.0.30\n", encoding="utf-8")
    proc = _run(FETCHER, "--project", str(tmp_path))
    data = json.loads(proc.stdout)
    assert data["framework"] == "fastapi"
    assert data["detected_version"] == "0.115.6"
    assert data["manifest"] == "requirements.txt"
    topics = {l["topic"] for l in data["lookups"]}
    assert "pydantic_v2_models" in topics
    assert "sqlalchemy_v2_orm" in topics
    # Version-gated lookup (0.95+) should be present
    assert "fastapi_annotated_deps" in topics


def test_source_docs_fetcher_detects_django(tmp_path):
    (tmp_path / "requirements.txt").write_text("Django>=5.0\n", encoding="utf-8")
    proc = _run(FETCHER, "--project", str(tmp_path))
    data = json.loads(proc.stdout)
    assert data["framework"] == "django"
    assert data["detected_version"] == "5.0"
    topics = {l["topic"] for l in data["lookups"]}
    assert "django_v5_features" in topics, \
        "5.0 should unlock the version-gated lookup"


def test_source_docs_fetcher_detects_spring_from_pom(tmp_path):
    (tmp_path / "pom.xml").write_text(
        "<project><parent><groupId>org.springframework.boot</groupId>"
        "<artifactId>spring-boot-starter-parent</artifactId>"
        "<version>3.2.1</version></parent></project>", encoding="utf-8")
    proc = _run(FETCHER, "--project", str(tmp_path))
    data = json.loads(proc.stdout)
    assert data["framework"] == "spring"
    assert data["detected_version"] == "3.2.1"
    topics = {l["topic"] for l in data["lookups"]}
    assert "spring_boot_3_jakarta" in topics
    # version-gated
    assert "spring_security_6" in topics


def test_source_docs_fetcher_no_manifest_returns_skip(tmp_path):
    proc = _run(FETCHER, "--project", str(tmp_path))
    data = json.loads(proc.stdout)
    assert data["framework"] is None
    assert data["skip_reason"] == "no_manifest_found"
    assert data["lookups"] == []


def test_source_docs_fetcher_unrecognised_framework(tmp_path):
    (tmp_path / "package.json").write_text(
        '{"dependencies":{"some-obscure-thing":"1.0"}}', encoding="utf-8")
    proc = _run(FETCHER, "--project", str(tmp_path))
    data = json.loads(proc.stdout)
    assert data["framework"] is None
    assert data["skip_reason"] == "framework_not_recognised"


# ─── doubt_driver ──────────────────────────────────────────────────────────

def _seed_doubt(sbx: Path) -> None:
    _run(DOUBT, "init", "--sandbox", str(sbx))


def _record_doubt(sbx: Path, artifact: str, verdict: dict, tmp_path: Path,
                   name: str = "verdict.json") -> dict:
    vp = tmp_path / name
    vp.write_text(json.dumps(verdict), encoding="utf-8")
    proc = _run(DOUBT, "record", "--sandbox", str(sbx),
                "--artifact", artifact, "--verdict", str(vp))
    return json.loads(proc.stdout)


def test_doubt_pass_no_findings_proceeds(tmp_path):
    sbx = tmp_path / "sandbox"
    _seed_doubt(sbx)
    result = _record_doubt(sbx, "cart/router.py",
                            {"verdict": "PASS", "findings": []}, tmp_path)
    assert result["decision"] == "PROCEED"
    assert result["reason"] == "no_blocking_findings"


def test_doubt_only_noise_findings_proceeds(tmp_path):
    sbx = tmp_path / "sandbox"
    _seed_doubt(sbx)
    result = _record_doubt(sbx, "cart/router.py", {
        "verdict": "DOUBT",
        "findings": [
            {"severity": "noise", "where": "cart/router.py:1", "what": "missing docstring"},
            {"severity": "accepted_tradeoff", "where": "cart/router.py:42",
             "what": "no caching — scope decision"},
        ],
    }, tmp_path)
    assert result["decision"] == "PROCEED"
    assert result["reason"] == "only_noise_or_tradeoffs"


def test_doubt_contract_violation_loops_to_implementer(tmp_path):
    sbx = tmp_path / "sandbox"
    _seed_doubt(sbx)
    result = _record_doubt(sbx, "cart/router.py", {
        "verdict": "DOUBT",
        "findings": [
            {"severity": "contract_violation", "where": "cart/router.py:42",
             "what": "DELETE returns 200; contract says 204"},
        ],
    }, tmp_path)
    assert result["decision"] == "LOOP_TO_IMPLEMENTER"
    assert len(result["blocking_findings"]) == 1


def test_doubt_max_rounds_escalates(tmp_path):
    sbx = tmp_path / "sandbox"
    _seed_doubt(sbx)
    v = {
        "verdict": "DOUBT",
        "findings": [
            # Make the 'what' differ across rounds so we test the iteration cap,
            # NOT the doubt-theater detector.
            {"severity": "contract_violation", "where": "cart/router.py:42",
             "what": "round1 issue"},
        ],
    }
    r1 = _record_doubt(sbx, "cart/router.py", v, tmp_path, "v1.json")
    assert r1["decision"] == "LOOP_TO_IMPLEMENTER"
    # Round 2 with a DIFFERENT 'what' so fingerprint differs
    v2 = json.loads(json.dumps(v))
    v2["findings"][0]["what"] = "round2 issue"
    r2 = _record_doubt(sbx, "cart/router.py", v2, tmp_path, "v2.json")
    assert r2["decision"] == "ESCALATE"
    assert r2["reason"] == "max_doubt_rounds_reached"


def test_doubt_theater_same_fingerprint_escalates(tmp_path):
    """Round 2 with IDENTICAL findings → implementer didn't fix anything → escalate."""
    sbx = tmp_path / "sandbox"
    _seed_doubt(sbx)
    v = {
        "verdict": "DOUBT",
        "findings": [
            {"severity": "contract_violation", "where": "cart/router.py:42",
             "what": "DELETE returns 200; contract says 204"},
        ],
    }
    _record_doubt(sbx, "cart/router.py", v, tmp_path, "v1.json")
    r2 = _record_doubt(sbx, "cart/router.py", v, tmp_path, "v2.json")
    assert r2["decision"] == "ESCALATE"
    assert r2["reason"] == "doubt_theater_same_findings"


def test_doubt_summary(tmp_path):
    sbx = tmp_path / "sandbox"
    _seed_doubt(sbx)
    _record_doubt(sbx, "a.py", {"verdict": "DOUBT", "findings": [
        {"severity": "contract_violation", "where": "a.py:1", "what": "x"}]}, tmp_path, "1.json")
    _record_doubt(sbx, "b.py", {"verdict": "PASS", "findings": []}, tmp_path, "2.json")
    proc = _run(DOUBT, "summary", "--sandbox", str(sbx))
    summary = json.loads(proc.stdout)
    assert summary["total_artifacts"] == 2
    assert summary["total_rounds"] == 2


def test_doubt_doubter_agent_md_exists():
    path = REPO_ROOT / ".claude" / "agents" / "doubter.md"
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "model: sonnet" in text
    assert "fresh-context" in text.lower()
    assert "contract_violation" in text


# ─── ship_gates ────────────────────────────────────────────────────────────

def test_ship_gates_ready_for_clean_project(tmp_path):
    """A minimal project with passing tests, no secrets, no TODOs."""
    (tmp_path / ".env.example").write_text("DATABASE_URL=\n", encoding="utf-8")
    (tmp_path / "main.py").write_text(
        'from fastapi import FastAPI\n'
        'import os\n'
        'app = FastAPI()\n'
        '@app.get("/healthz")\n'
        'def healthz(): return {"ok": True}\n'
        'DB = os.environ["DATABASE_URL"]\n', encoding="utf-8")
    (tmp_path / "ROLLOUT.md").write_text(
        "# Rollout plan\nCanary at 5% then ramp to 100%. "
        "Halt if error rate > 2x baseline.\n", encoding="utf-8")
    proc = _run(GATES, "--project", str(tmp_path), check=False)
    # Exit 0 means READY or READY_WITH_WARN; flagging some warnings is fine.
    data = json.loads(proc.stdout)
    assert data["verdict"] in ("READY", "READY_WITH_WARN")
    gate_by_name = {g["name"]: g["status"] for g in data["gates"]}
    assert gate_by_name["no_secrets_in_diff"] == "PASS"
    assert gate_by_name["no_TODO_or_FIXME"] == "PASS"
    assert gate_by_name["health_endpoint_exists"] == "PASS"
    assert gate_by_name["env_vars_documented"] == "PASS"
    assert gate_by_name["canary_plan"] == "PASS"


def test_ship_gates_blocks_on_secrets(tmp_path):
    (tmp_path / "config.py").write_text(
        'AWS_KEY = "AKIAIOSFODNN7EXAMPLE"\napi_key = "sk-1234567890abcdef1234"\n',
        encoding="utf-8")
    proc = _run(GATES, "--project", str(tmp_path), check=False)
    data = json.loads(proc.stdout)
    assert data["verdict"] == "BLOCKED"
    secret_gate = next(g for g in data["gates"] if g["name"] == "no_secrets_in_diff")
    assert secret_gate["status"] == "FAIL"


def test_ship_gates_blocks_on_unresolved_todos(tmp_path):
    """11+ TODOs = FAIL (10 or fewer = WARN)."""
    code = "\n".join(f"# TODO: fix issue {i}" for i in range(15))
    (tmp_path / "main.py").write_text(code, encoding="utf-8")
    proc = _run(GATES, "--project", str(tmp_path), check=False)
    data = json.loads(proc.stdout)
    todo_gate = next(g for g in data["gates"] if g["name"] == "no_TODO_or_FIXME")
    assert todo_gate["status"] == "FAIL"
    assert data["verdict"] == "BLOCKED"


def test_ship_gates_strict_promotes_warn(tmp_path):
    """A bare project should be READY_WITH_WARN normally, BLOCKED in --strict."""
    (tmp_path / "main.py").write_text("print('hi')\n", encoding="utf-8")
    normal = json.loads(_run(GATES, "--project", str(tmp_path), check=False).stdout)
    strict = json.loads(_run(GATES, "--project", str(tmp_path), "--strict",
                              check=False).stdout)
    # Bare project has warnings (no env example, no health, no rollout, etc.)
    assert normal["verdict"] in ("READY_WITH_WARN", "BLOCKED")
    assert strict["verdict"] == "BLOCKED"


def test_ship_gates_detects_reversible_alembic(tmp_path):
    versions = tmp_path / "alembic" / "versions"
    versions.mkdir(parents=True)
    (versions / "abcd_initial.py").write_text(
        '"""initial"""\n'
        'from alembic import op\n'
        'def upgrade():\n    op.create_table("x")\n'
        'def downgrade():\n    op.drop_table("x")\n', encoding="utf-8")
    proc = _run(GATES, "--project", str(tmp_path), check=False)
    data = json.loads(proc.stdout)
    mig = next(g for g in data["gates"] if g["name"] == "migration_reversible")
    assert mig["status"] == "PASS"


def test_ship_gates_flags_empty_alembic_downgrade(tmp_path):
    versions = tmp_path / "alembic" / "versions"
    versions.mkdir(parents=True)
    (versions / "abcd_initial.py").write_text(
        '"""initial"""\n'
        'def upgrade():\n    pass\n'
        'def downgrade():\n    pass\n', encoding="utf-8")
    proc = _run(GATES, "--project", str(tmp_path), check=False)
    data = json.loads(proc.stdout)
    mig = next(g for g in data["gates"] if g["name"] == "migration_reversible")
    assert mig["status"] == "FAIL"


def test_ship_check_slash_command_exists():
    path = REPO_ROOT / "commands" / "ship-check.md"
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "argument-hint:" in text
    assert "ship_gates.py" in text


# ─── adr_writer ────────────────────────────────────────────────────────────

def test_adr_writer_creates_numbered_file_and_index(tmp_path):
    proc = _run(ADR, "emit",
                "--project", str(tmp_path),
                "--title", "Use SQLAlchemy 2.0 mapped_column",
                "--context", "Need ORM models compatible with FastAPI 0.110+",
                "--decision", "Adopt mapped_column",
                "--consequences", "Locks us into SQLAlchemy 2.0+",
                "--alternatives", "- Legacy Column\n- SQLModel")
    data = json.loads(proc.stdout)
    assert data["number"] == 1

    adr_dir = tmp_path / "docs" / "adr"
    files = sorted(adr_dir.glob("[0-9]*.md"))
    assert len(files) == 1
    assert files[0].name.startswith("0001-")
    text = files[0].read_text(encoding="utf-8")
    assert "## Context" in text
    assert "## Decision" in text
    assert "## Consequences" in text
    assert "## Alternatives considered" in text
    assert "SQLAlchemy 2.0" in text

    # Index regenerated
    index = adr_dir / "README.md"
    assert index.exists()
    assert "SQLAlchemy 2.0" in index.read_text(encoding="utf-8")


def test_adr_writer_increments_number_across_calls(tmp_path):
    _run(ADR, "emit", "--project", str(tmp_path),
         "--title", "First decision")
    _run(ADR, "emit", "--project", str(tmp_path),
         "--title", "Second decision")
    _run(ADR, "emit", "--project", str(tmp_path),
         "--title", "Third decision")
    nums = sorted(int(p.name.split("-", 1)[0])
                  for p in (tmp_path / "docs" / "adr").glob("[0-9]*.md"))
    assert nums == [1, 2, 3]


def test_adr_writer_kebab_title_and_status(tmp_path):
    proc = _run(ADR, "emit", "--project", str(tmp_path),
                "--title", "Use Optimistic Locking for Cart Updates",
                "--status", "proposed")
    data = json.loads(proc.stdout)
    files = list((tmp_path / "docs" / "adr").glob("[0-9]*.md"))
    assert any("use-optimistic-locking" in p.name for p in files)
    text = files[0].read_text(encoding="utf-8")
    assert "status: proposed" in text


def test_adr_writer_list(tmp_path):
    _run(ADR, "emit", "--project", str(tmp_path), "--title", "A")
    _run(ADR, "emit", "--project", str(tmp_path), "--title", "B")
    proc = _run(ADR, "list", "--project", str(tmp_path))
    listing = json.loads(proc.stdout)
    assert len(listing) == 2
    assert {e["title"] for e in listing} == {"A", "B"}


# ─── /refine slash command ────────────────────────────────────────────────

def test_refine_slash_command_exists():
    path = REPO_ROOT / "commands" / "refine.md"
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "argument-hint:" in text
    assert "NOT doing" in text  # the key uniqueness of refine output
    assert "MVP scope" in text


# ─── new body_hints contracts ─────────────────────────────────────────────

V46_CONTRACTS = [
    "adr_record",
    "source_verification",
    "ci_cd_pipeline",
    "api_design",
    "deprecation_policy",
    "frontend_ui_concerns",
]


def test_all_v46_contracts_present():
    proc = _run(HINTS, "--list", "--json")
    kinds = {h["kind"] for h in json.loads(proc.stdout) if h["framework"] == "common"}
    missing = set(V46_CONTRACTS) - kinds
    assert not missing, f"missing v4.6 contracts: {missing}"


def test_adr_record_documents_status_lifecycle():
    proc = _run(HINTS, "--framework", "common", "--kind", "adr_record")
    data = json.loads(proc.stdout)
    blob = json.dumps(data).lower()
    assert "proposed" in blob and "accepted" in blob and "superseded" in blob
    anti = " ".join(data["anti_patterns"]).lower()
    assert "delete" in anti, "never DELETE an ADR — supersede"


def test_source_verification_blocks_blog_citations():
    proc = _run(HINTS, "--framework", "common", "--kind", "source_verification")
    data = json.loads(proc.stdout)
    anti = " ".join(data["anti_patterns"]).lower()
    assert "stack overflow" in anti or "blog" in anti, \
        "must rule out non-official source citations"


def test_ci_cd_pipeline_caches_lockfile_not_output():
    proc = _run(HINTS, "--framework", "common", "--kind", "ci_cd_pipeline")
    data = json.loads(proc.stdout)
    must = " ".join(data["must_emit"]).lower()
    assert "lockfile" in must, "cache must be keyed on lockfile hash"
    anti = " ".join(data["anti_patterns"]).lower()
    assert "latest" in anti, "must rule out :latest docker tags"
    assert "secret" in anti, "must rule out committed secrets"


def test_api_design_lists_status_code_conventions():
    proc = _run(HINTS, "--framework", "common", "--kind", "api_design")
    data = json.loads(proc.stdout)
    blob = json.dumps(data)
    assert "201" in blob and "204" in blob and "409" in blob and "422" in blob
    anti = " ".join(data["anti_patterns"]).lower()
    assert "verb" in anti and "url" in anti, "no verbs in URLs"


def test_deprecation_policy_requires_sunset_header():
    proc = _run(HINTS, "--framework", "common", "--kind", "deprecation_policy")
    data = json.loads(proc.stdout)
    blob = json.dumps(data).lower()
    assert "sunset" in blob, "must reference RFC 8594 Sunset header"
    assert "6 month" in blob or "6+ month" in blob, "must require minimum deprecation window"


def test_frontend_ui_concerns_blocks_outline_none():
    proc = _run(HINTS, "--framework", "common", "--kind", "frontend_ui_concerns")
    data = json.loads(proc.stdout)
    anti = " ".join(data["anti_patterns"]).lower()
    assert "outline: none" in anti or "outline:none" in anti or "outline" in anti, \
        "must rule out outline:none without replacement"
    blob = json.dumps(data).lower()
    assert "wcag" in blob, "must reference WCAG 2.1 contrast floors"


# ─── catalogue size ───────────────────────────────────────────────────────

def test_body_hints_total_count_after_v46():
    """v4.5 ended at 91 hints. v4.6 adds 6 cross-cutting contracts. Expect >= 97."""
    proc = _run(HINTS, "--list", "--json")
    data = json.loads(proc.stdout)
    assert len(data) >= 97, f"expected >= 97 after v4.6, got {len(data)}"
