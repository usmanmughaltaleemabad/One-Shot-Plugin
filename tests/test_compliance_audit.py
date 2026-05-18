"""Tests for compliance_audit.py — runs the Anthropic Software Directory
Policy checklist against the repo.

Also asserts the repo itself currently passes (regression guard: if a
future commit removes TROUBLESHOOTING.md / a required field / etc.,
the suite catches it before submission breaks).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "skills" / "one-shot-generator" / "scripts"
AUDIT = SCRIPTS / "compliance_audit.py"


def _run(*args: str, check: bool = True, cwd: Path | None = None,
         timeout: int = 30) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        [sys.executable, str(AUDIT), *args],
        capture_output=True, text=True, env=env, encoding="utf-8",
        timeout=timeout, cwd=str(cwd) if cwd else None,
    )
    if check:
        assert proc.returncode in (0, 1, 2), \
            f"audit crashed: {proc.stderr}"
    return proc


def _seed_minimal_repo(tmp_path: Path) -> Path:
    """Create a bare-minimum repo with the placeholders the audit expects.
    Tests then mutate it to assert each check fires correctly."""
    repo = tmp_path / "fake-repo"
    repo.mkdir()
    # Required files (each > 100 chars so they pass the size check)
    for name in ("PRIVACY.md", "SUPPORT.md", "README.md", "CHANGELOG.md",
                  "TROUBLESHOOTING.md", "SECURITY.md"):
        (repo / name).write_text("# " + name + "\n" + "x" * 200,
                                  encoding="utf-8")
    (repo / "LICENSE").write_text("MIT License\n" + "x" * 200, encoding="utf-8")
    # plugin.json
    (repo / ".claude-plugin").mkdir()
    (repo / ".claude-plugin" / "plugin.json").write_text(json.dumps({
        "name": "test", "version": "0.1.0", "author": {"name": "x"},
        "license": "MIT", "description": "test plugin",
    }), encoding="utf-8")
    # commands dir with 1 valid command
    (repo / "commands").mkdir()
    (repo / "commands" / "test.md").write_text(
        "---\n"
        "description: Test command\n"
        "argument-hint: [args]\n"
        "allowed-tools: Bash\n"
        "destructive: false\n"
        "read-only: true\n"
        "---\n\nBody\n",
        encoding="utf-8",
    )
    # tests dir with placeholders
    (repo / "tests").mkdir()
    for i in range(5):
        (repo / "tests" / f"test_x{i}.py").write_text(
            "def test_ok(): assert True\n", encoding="utf-8")
    # 3 example prompts in cookbook
    docs = repo / "docs"
    docs.mkdir()
    (docs / "cookbook.md").write_text(
        "# Examples\n\n"
        "```bash\n/one-shot \"build cart\" @./project\n```\n\n"
        "```bash\n/one-shot \"add auth\" @./project --review\n```\n\n"
        "```bash\n/one-shot \"new feature\" @./project --apply\n```\n",
        encoding="utf-8",
    )
    return repo


# ─── Self-audit: the REAL repo must pass ──────────────────────────────────

def test_real_repo_audit_passes():
    """The repo at this commit must satisfy the directory policy. If a
    future commit breaks compliance, this test fails before submission."""
    proc = _run("--repo-root", str(REPO_ROOT))
    data = json.loads(_run("--repo-root", str(REPO_ROOT), "--json").stdout)
    assert data["verdict"] in ("READY_FOR_DIRECTORY", "READY_WITH_WARN"), \
        (f"Repo failed compliance: {data['summary']}\n"
         + "\n".join(f"  [{c['status']}] {c['name']}: {c['detail']}"
                     for c in data["checks"]
                     if c["status"] == "FAIL"))


# ─── Missing-doc detection ────────────────────────────────────────────────

def test_audit_flags_missing_troubleshooting(tmp_path):
    repo = _seed_minimal_repo(tmp_path)
    (repo / "TROUBLESHOOTING.md").unlink()
    proc = _run("--repo-root", str(repo), "--json", check=False)
    data = json.loads(proc.stdout)
    assert proc.returncode == 2
    failures = [c for c in data["checks"]
                 if c["status"] == "FAIL"
                 and "troubleshoot" in c["name"].lower()]
    assert failures, "TROUBLESHOOTING.md missing should be a FAIL"


def test_audit_flags_missing_privacy(tmp_path):
    repo = _seed_minimal_repo(tmp_path)
    (repo / "PRIVACY.md").unlink()
    proc = _run("--repo-root", str(repo), "--json", check=False)
    data = json.loads(proc.stdout)
    assert proc.returncode == 2
    failures = [c for c in data["checks"]
                 if c["status"] == "FAIL"
                 and "privacy" in c["name"].lower()]
    assert failures


def test_audit_flags_missing_license(tmp_path):
    repo = _seed_minimal_repo(tmp_path)
    (repo / "LICENSE").unlink()
    proc = _run("--repo-root", str(repo), "--json", check=False)
    data = json.loads(proc.stdout)
    failures = [c for c in data["checks"]
                 if c["status"] == "FAIL"
                 and "license" in c["name"].lower()]
    assert failures


def test_audit_warns_on_short_documentation(tmp_path):
    repo = _seed_minimal_repo(tmp_path)
    # Replace with stub (<100 chars)
    (repo / "PRIVACY.md").write_text("# Privacy\nshort\n", encoding="utf-8")
    proc = _run("--repo-root", str(repo), "--json", check=False)
    data = json.loads(proc.stdout)
    warnings = [c for c in data["checks"]
                 if c["status"] == "WARN"
                 and "privacy" in c["name"].lower()]
    assert warnings, "should warn on suspiciously-short PRIVACY.md"


# ─── Plugin manifest checks ───────────────────────────────────────────────

def test_audit_flags_missing_manifest(tmp_path):
    repo = _seed_minimal_repo(tmp_path)
    shutil.rmtree(repo / ".claude-plugin")
    proc = _run("--repo-root", str(repo), "--json", check=False)
    data = json.loads(proc.stdout)
    assert proc.returncode == 2
    failures = [c for c in data["checks"]
                 if c["status"] == "FAIL"
                 and "manifest" in c["category"].lower()]
    assert failures


def test_audit_flags_manifest_missing_required_field(tmp_path):
    repo = _seed_minimal_repo(tmp_path)
    (repo / ".claude-plugin" / "plugin.json").write_text(json.dumps({
        "name": "test", "version": "0.1.0",   # missing author, license, description
    }), encoding="utf-8")
    proc = _run("--repo-root", str(repo), "--json", check=False)
    data = json.loads(proc.stdout)
    assert proc.returncode == 2
    failures = {c["name"] for c in data["checks"]
                 if c["status"] == "FAIL"
                 and "manifest_field" in c["name"]}
    assert "manifest_field_author" in failures
    assert "manifest_field_license" in failures
    assert "manifest_field_description" in failures


# ─── Slash command checks ────────────────────────────────────────────────

def test_audit_flags_command_missing_frontmatter(tmp_path):
    repo = _seed_minimal_repo(tmp_path)
    (repo / "commands" / "bad.md").write_text(
        "# A command\n\nNo frontmatter\n", encoding="utf-8")
    proc = _run("--repo-root", str(repo), "--json", check=False)
    data = json.loads(proc.stdout)
    assert proc.returncode == 2
    failures = [c for c in data["checks"]
                 if c["status"] == "FAIL"
                 and "frontmatter" in c["name"].lower()]
    assert failures


def test_audit_flags_command_name_too_long(tmp_path):
    repo = _seed_minimal_repo(tmp_path)
    huge = "x" * 80
    (repo / "commands" / f"{huge}.md").write_text(
        "---\ndescription: x\nargument-hint: []\nallowed-tools: Bash\n---\n",
        encoding="utf-8",
    )
    proc = _run("--repo-root", str(repo), "--json", check=False)
    data = json.loads(proc.stdout)
    failures = [c for c in data["checks"]
                 if c["status"] == "FAIL"
                 and "name_length" in c["name"]]
    assert failures


def test_audit_warns_command_missing_argument_hint(tmp_path):
    repo = _seed_minimal_repo(tmp_path)
    (repo / "commands" / "nohint.md").write_text(
        "---\ndescription: x\nallowed-tools: Bash\n---\n",
        encoding="utf-8",
    )
    proc = _run("--repo-root", str(repo), "--json", check=False)
    data = json.loads(proc.stdout)
    warns = [c for c in data["checks"]
              if c["status"] == "WARN"
              and "argument_hint" in c["name"]]
    assert warns


# ─── Branding checks (forbidden Anthropic-endorsement claims) ────────────

def test_audit_flags_unauthorised_anthropic_partnership_claim(tmp_path):
    repo = _seed_minimal_repo(tmp_path)
    (repo / "README.md").write_text(
        "# My Plugin\n\nOfficial by Anthropic.\n" + "x" * 200,
        encoding="utf-8",
    )
    proc = _run("--repo-root", str(repo), "--json", check=False)
    data = json.loads(proc.stdout)
    failures = [c for c in data["checks"]
                 if c["status"] == "FAIL"
                 and c["category"] == "branding"]
    assert failures, "must catch unauthorised endorsement claims"


def test_audit_clean_branding(tmp_path):
    repo = _seed_minimal_repo(tmp_path)
    proc = _run("--repo-root", str(repo), "--json")
    data = json.loads(proc.stdout)
    branding = [c for c in data["checks"] if c["category"] == "branding"]
    # All branding checks must pass for minimal repo
    assert all(c["status"] == "PASS" for c in branding)


# ─── Strict mode ──────────────────────────────────────────────────────────

def test_audit_strict_promotes_warn_to_fail(tmp_path):
    repo = _seed_minimal_repo(tmp_path)
    # Short PRIVACY.md → WARN under normal, FAIL under strict
    (repo / "PRIVACY.md").write_text("# x\nshort", encoding="utf-8")
    normal = _run("--repo-root", str(repo), check=False)
    strict = _run("--repo-root", str(repo), "--strict", check=False)
    assert normal.returncode == 0   # WARN is OK
    assert strict.returncode == 2   # WARN promoted to fail


# ─── Tool annotations on real commands ───────────────────────────────────

def test_all_real_commands_have_annotations():
    """Every command in the real repo must declare destructive: + read-only:
    in its frontmatter (per directory policy tool annotations)."""
    commands_dir = REPO_ROOT / "commands"
    missing: list[str] = []
    for path in commands_dir.glob("*.md"):
        if path.name == "CLAUDE.md":
            continue
        text = path.read_text(encoding="utf-8")
        front = text.split("---", 2)[1] if text.startswith("---") else ""
        if "destructive:" not in front or "read-only:" not in front:
            missing.append(path.name)
    assert not missing, (
        f"commands missing tool annotations: {missing}. "
        f"Add 'destructive: true|false' + 'read-only: true|false' "
        f"to the frontmatter."
    )


def test_no_command_name_exceeds_64_chars():
    """Per directory policy — tool names ≤ 64 chars."""
    commands_dir = REPO_ROOT / "commands"
    too_long = [p.stem for p in commands_dir.glob("*.md")
                 if len(p.stem) > 64 and p.name != "CLAUDE.md"]
    assert not too_long, f"slash commands exceed 64 chars: {too_long}"
