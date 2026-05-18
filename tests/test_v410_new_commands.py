"""Tests for v4.10 new slash commands.

Adds 4 commands inspired by addyosmani/agent-skills coverage gaps:

  /perf-audit    — scans for N+1, hot-path blockers, memory hazards;
                   surfaces framework-specific profiler tooling
  /interview     — extracts clarifying questions before /refine
                   (pure SKILL.md, no backing script — tests just check
                   the slash command exists and has the right frontmatter)
  /browser-test  — drives chrome-devtools MCP for FE feature validation
                   (also pure SKILL.md, just the slash command)
  /context       — emits a CLAUDE.md skeleton from a project's stack
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
COMMANDS = REPO_ROOT / "commands"
PERF_AUDIT = SCRIPTS / "perf_audit.py"
CONTEXT_WRITER = SCRIPTS / "context_writer.py"


def _run(script: Path, *args: str, check: bool = True,
         timeout: int = 30) -> subprocess.CompletedProcess:
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


# ─── /perf-audit — slash command + script ──────────────────────────────────

def test_perf_audit_slash_command_exists():
    path = COMMANDS / "perf-audit.md"
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "argument-hint:" in text
    assert "perf_audit.py" in text
    assert "n_plus_one" in text.lower() or "N+1" in text
    assert "profiler" in text.lower()


def test_perf_audit_detects_fastapi(tmp_path):
    (tmp_path / "requirements.txt").write_text(
        "fastapi==0.115.6\nsqlalchemy==2.0.30\n", encoding="utf-8")
    proc = _run(PERF_AUDIT, "--project", str(tmp_path), "--json")
    data = json.loads(proc.stdout)
    assert data["framework"] == "fastapi"
    # tooling map should include py-spy + EXPLAIN ANALYZE
    tools = [t["tool"] for t in data["framework_tooling"]]
    assert any("py-spy" in t for t in tools)
    assert any("EXPLAIN" in t for t in tools)


def test_perf_audit_finds_n_plus_one_sqlalchemy(tmp_path):
    """SQLAlchemy query inside a for-loop without options(joinedload) — warning."""
    (tmp_path / "requirements.txt").write_text(
        "fastapi\nsqlalchemy\n", encoding="utf-8")
    (tmp_path / "views.py").write_text(
        "from sqlalchemy.orm import Session\n"
        "def list_carts(db):\n"
        "    for cart in db.query(Cart).filter(Cart.active == True):\n"
        "        print(cart.line_items)\n",
        encoding="utf-8",
    )
    proc = _run(PERF_AUDIT, "--project", str(tmp_path), "--json")
    data = json.loads(proc.stdout)
    rules = {f["rule_id"] for f in data["findings"]}
    assert "n_plus_one_sqlalchemy" in rules
    assert data["summary"]["warning"] >= 1


def test_perf_audit_finds_sync_http_in_async(tmp_path):
    (tmp_path / "requirements.txt").write_text("fastapi\n", encoding="utf-8")
    (tmp_path / "handlers.py").write_text(
        "import requests\n"
        "async def handle(request):\n"
        "    x = 1\n"
        "    return requests.get('http://x')\n",
        encoding="utf-8",
    )
    proc = _run(PERF_AUDIT, "--project", str(tmp_path), "--json")
    data = json.loads(proc.stdout)
    rules = {f["rule_id"] for f in data["findings"]}
    assert "sync_http_in_async" in rules


def test_perf_audit_finds_bcrypt_sync(tmp_path):
    (tmp_path / "auth.py").write_text(
        "import bcrypt\n"
        "def hash_pw(pw):\n"
        "    return bcrypt.hashpw(pw, bcrypt.gensalt())\n",
        encoding="utf-8",
    )
    proc = _run(PERF_AUDIT, "--project", str(tmp_path), "--json")
    data = json.loads(proc.stdout)
    rules = {f["rule_id"] for f in data["findings"]}
    assert "bcrypt_sync_in_hot_path" in rules


def test_perf_audit_severity_filter(tmp_path):
    """`--severity warning` hides info-only findings."""
    (tmp_path / "src.py").write_text(
        "data = file.read()\n"          # info-only: unbounded_file_read
        "import bcrypt\n"
        "def x(): bcrypt.hashpw(b'a', b'b')\n",   # warning: bcrypt sync
        encoding="utf-8",
    )
    all_ = json.loads(_run(PERF_AUDIT, "--project", str(tmp_path),
                            "--json").stdout)
    warn_only = json.loads(_run(PERF_AUDIT, "--project", str(tmp_path),
                                  "--severity", "warning", "--json").stdout)
    assert all_["summary"]["info"] >= 1
    assert warn_only["summary"]["info"] == 0
    assert warn_only["summary"]["warning"] >= 1


def test_perf_audit_strict_exits_2_on_warning(tmp_path):
    (tmp_path / "auth.py").write_text(
        "import bcrypt\ndef x(): bcrypt.hashpw(b'a', b'b')\n",
        encoding="utf-8",
    )
    proc = _run(PERF_AUDIT, "--project", str(tmp_path), "--strict",
                 check=False)
    assert proc.returncode == 2


def test_perf_audit_clean_project_no_findings(tmp_path):
    (tmp_path / "requirements.txt").write_text("fastapi\n", encoding="utf-8")
    (tmp_path / "main.py").write_text(
        "from fastapi import FastAPI\napp = FastAPI()\n",
        encoding="utf-8",
    )
    proc = _run(PERF_AUDIT, "--project", str(tmp_path), "--json")
    data = json.loads(proc.stdout)
    assert data["summary"]["total"] == 0
    assert data["framework"] == "fastapi"


# ─── /interview — slash command only (no backing script) ──────────────────

def test_interview_slash_command_exists():
    path = COMMANDS / "interview.md"
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "argument-hint:" in text
    # Must reference the 3-round structure to enforce the discipline
    assert "Round 1" in text and "Round 2" in text and "Round 3" in text
    # Hard rule: max question cap mentioned
    assert "6 questions" in text or "Maximum 6" in text
    # Output template includes restatement + open questions
    assert "Refined feature (after interview)" in text


# ─── /browser-test — slash command only ───────────────────────────────────

def test_browser_test_slash_command_exists():
    path = COMMANDS / "browser-test.md"
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "argument-hint:" in text
    assert "chrome-devtools" in text.lower()
    # Must reference the right MCP tool prefixes
    assert "mcp__chrome-devtools__" in text
    # Must include the structured-report output format
    assert "Verdict" in text or "verdict" in text


# ─── /context — slash command + script ────────────────────────────────────

def test_context_slash_command_exists():
    path = COMMANDS / "context.md"
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "argument-hint:" in text
    assert "context_writer.py" in text
    assert "CLAUDE.md" in text


def test_context_writer_detects_fastapi(tmp_path):
    (tmp_path / "requirements.txt").write_text(
        "fastapi==0.115.6\nsqlalchemy==2.0.30\nalembic==1.13\n"
        "pytest==8.2\nruff==0.4\nmypy==1.10\n",
        encoding="utf-8",
    )
    proc = _run(CONTEXT_WRITER, "--project", str(tmp_path), "--json")
    data = json.loads(proc.stdout)
    assert data["language"] == "python"
    assert data["framework"] == "fastapi"
    assert data["framework_version"] == "0.115.6"
    assert data["orm"] == "sqlalchemy"
    assert data["migration_tool"] == "alembic"
    assert data["test_runner"] == "pytest"
    assert data["linter"] == "ruff"
    assert data["type_checker"] == "mypy"


def test_context_writer_writes_claude_md(tmp_path):
    (tmp_path / "requirements.txt").write_text(
        "fastapi==0.115.6\nsqlalchemy==2.0.30\n", encoding="utf-8")
    proc = _run(CONTEXT_WRITER, "--project", str(tmp_path))
    data = json.loads(proc.stdout)
    assert data["status"] == "written"
    out = Path(data["out_path"])
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "Project Context for Claude" in content
    assert "fastapi" in content
    assert "## Stack" in content
    assert "## Conventions Claude MUST follow" in content
    assert "## Conventions Claude must NEVER do" in content
    assert "(fill in)" in content   # has placeholders for human edit


def test_context_writer_refuses_overwrite_without_force(tmp_path):
    (tmp_path / "requirements.txt").write_text("fastapi\n", encoding="utf-8")
    (tmp_path / "CLAUDE.md").write_text("# Pre-existing\n", encoding="utf-8")
    proc = _run(CONTEXT_WRITER, "--project", str(tmp_path), check=False)
    assert proc.returncode == 2
    # Original file preserved
    assert "Pre-existing" in (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")


def test_context_writer_force_overwrites(tmp_path):
    (tmp_path / "requirements.txt").write_text("fastapi\n", encoding="utf-8")
    (tmp_path / "CLAUDE.md").write_text("# Pre-existing\n", encoding="utf-8")
    _run(CONTEXT_WRITER, "--project", str(tmp_path), "--force")
    content = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    assert "Pre-existing" not in content
    assert "Project Context for Claude" in content


def test_context_writer_append_keeps_existing(tmp_path):
    (tmp_path / "requirements.txt").write_text("fastapi\n", encoding="utf-8")
    (tmp_path / "CLAUDE.md").write_text("# Pre-existing\n", encoding="utf-8")
    _run(CONTEXT_WRITER, "--project", str(tmp_path), "--append")
    content = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    assert "Pre-existing" in content
    assert "Project Context for Claude" in content
    assert "Auto-appended" in content


def test_context_writer_detects_django(tmp_path):
    (tmp_path / "requirements.txt").write_text(
        "Django>=5.0\npsycopg2-binary\n", encoding="utf-8")
    proc = _run(CONTEXT_WRITER, "--project", str(tmp_path), "--json")
    data = json.loads(proc.stdout)
    assert data["framework"] == "django"
    assert data["migration_tool"] == "django-migrations"


def test_context_writer_detects_nestjs(tmp_path):
    (tmp_path / "package.json").write_text(
        '{"dependencies": {"@nestjs/core": "^10.0.0", '
        '"typeorm": "^0.3.0"}, "devDependencies": '
        '{"jest": "^29.0", "typescript": "^5.0"}}',
        encoding="utf-8",
    )
    proc = _run(CONTEXT_WRITER, "--project", str(tmp_path), "--json")
    data = json.loads(proc.stdout)
    assert data["framework"] == "nestjs"
    assert data["orm"] == "typeorm"
    assert data["test_runner"] == "jest"
    assert data["language"] == "typescript"


def test_context_writer_detects_spring(tmp_path):
    (tmp_path / "pom.xml").write_text(
        "<project><parent><groupId>org.springframework.boot</groupId>"
        "<artifactId>spring-boot-starter-parent</artifactId>"
        "<version>3.2.1</version></parent></project>",
        encoding="utf-8",
    )
    proc = _run(CONTEXT_WRITER, "--project", str(tmp_path), "--json")
    data = json.loads(proc.stdout)
    assert data["framework"] == "spring"
    assert data["framework_version"] == "3.2.1"
    assert data["language"] == "java"
    assert data["test_runner"] == "junit"
    assert data["migration_tool"] == "flyway"


def test_context_writer_emits_framework_specific_commands(tmp_path):
    """Different frameworks → different 'How to run things' blocks."""
    # Django
    (tmp_path / "requirements.txt").write_text("Django>=5\n", encoding="utf-8")
    _run(CONTEXT_WRITER, "--project", str(tmp_path), "--force")
    dj = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    assert "python manage.py" in dj


# ─── slash command count crossed 29 ────────────────────────────────────────

def test_slash_command_count_crossed_28():
    """v4.10 adds 4 commands (/perf-audit, /interview, /browser-test,
    /context). Expect >= 28 user-facing markdown command files
    (excluding commands/CLAUDE.md and README.md)."""
    md_files = list(COMMANDS.glob("*.md"))
    user_facing = [p for p in md_files
                    if p.name not in {"CLAUDE.md", "README.md"}]
    assert len(user_facing) >= 28, \
        f"expected >= 28 slash commands, got {len(user_facing)}"
    # The 4 new ones must all be present
    names = {p.name for p in md_files}
    for required in ("perf-audit.md", "interview.md",
                      "browser-test.md", "context.md"):
        assert required in names, f"missing slash command: {required}"
