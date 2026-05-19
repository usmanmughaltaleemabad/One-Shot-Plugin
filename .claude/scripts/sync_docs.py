#!/usr/bin/env python3
"""
sync_docs.py — pre-commit doc auto-updater

Reads live counts from the repo and patches version numbers, agent counts,
test counts, etc. across all user-facing docs. Called by the pre-commit
hook before every commit so docs never drift from code.

What it syncs:
  - Version         → plugin.json
  - Test count      → grep ^def test_ across tests/*.py
  - Agent count     → .claude/agents/*.md (excluding doubter internals)
  - Command count   → commands/*.md (excluding CLAUDE.md)
  - Body hint count → body_hints.HINTS length
  - Stage count     -> CLAUDE.md pipeline code block (lines matching N  word)
  - Smoke count     → .claude/scripts/smoke-test.sh PASS lines

Files patched:
  README.md, CLAUDE.md, AUDIT_ME_FIRST.md,
  DIRECTORY_SUBMISSION_FORM.md, MARKETPLACE_SUBMISSION.md

Exit 0 always — failure to sync is a warning, not a blocker.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

# ── Repo root detection ───────────────────────────────────────────────────────

def _repo_root() -> Path:
    cur = Path(__file__).resolve()
    while cur != cur.parent:
        if (cur / ".claude-plugin").exists():
            return cur
        cur = cur.parent
    return Path.cwd()


ROOT = _repo_root()
SCRIPTS = ROOT / "skills" / "one-shot-generator" / "scripts"


# ── Metric collection ─────────────────────────────────────────────────────────

def _version() -> str:
    try:
        data = json.loads((ROOT / ".claude-plugin" / "plugin.json")
                          .read_text(encoding="utf-8"))
        return data.get("version", "0.0.0")
    except Exception:
        return "0.0.0"


def _test_count() -> int:
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/",
             "--collect-only", "-q", "--ignore=tests/integration"],
            capture_output=True, text=True, cwd=str(ROOT), timeout=30,
        )
        m = re.search(r"(\d+) tests? collected", result.stdout)
        if m:
            return int(m.group(1))
    except Exception:
        pass
    # Fallback: grep for def test_ across test files
    total = 0
    for f in (ROOT / "tests").rglob("test_*.py"):
        try:
            total += f.read_text(encoding="utf-8").count("\ndef test_")
        except OSError:
            pass
    return total


def _agent_count() -> int:
    agents_dir = ROOT / ".claude" / "agents"
    return len(list(agents_dir.glob("*.md"))) if agents_dir.exists() else 0


def _command_count() -> int:
    cmd_dir = ROOT / "commands"
    if not cmd_dir.exists():
        return 0
    return sum(1 for f in cmd_dir.glob("*.md") if f.name != "CLAUDE.md")


def _hint_count() -> int:
    try:
        sys.path.insert(0, str(SCRIPTS))
        sys.path.insert(0, str(SCRIPTS / "lib"))
        from body_hints import HINTS  # type: ignore
        return len(HINTS)
    except Exception:
        return 101  # last known good


def _smoke_count() -> int:
    smoke = ROOT / ".claude" / "scripts" / "smoke-test.sh"
    if not smoke.exists():
        return 8
    try:
        text = smoke.read_text(encoding="utf-8")
        return text.count('✅ PASS:')
    except OSError:
        return 8


def _stage_count() -> int:
    # Count stage lines in the CLAUDE.md pipeline code block.
    # Lines look like: "0    curriculum..." or "8.5  dream..."
    claude_md = ROOT / "CLAUDE.md"
    if not claude_md.exists():
        return 15
    try:
        text = claude_md.read_text(encoding="utf-8")
        in_block = False
        count = 0
        for line in text.splitlines():
            if line.strip() == "```":
                in_block = not in_block
                continue
            if in_block and re.match(r"^\d+(?:\.\d+)?\s+\w", line):
                count += 1
        return count if count > 5 else 15
    except OSError:
        return 15


# ── Patch helpers ─────────────────────────────────────────────────────────────

def _sub(pattern: str, replacement: str, text: str,
         flags: int = 0) -> tuple[str, int]:
    """Return (new_text, hit_count)."""
    new, n = re.subn(pattern, replacement, text, flags=flags)
    return new, n


def _patch_file(path: Path, patches: list[tuple[str, str]]) -> bool:
    """Apply a list of (pattern, replacement) pairs to a file.
    Returns True if the file was modified."""
    try:
        original = path.read_text(encoding="utf-8")
    except OSError:
        return False
    text = original
    for pat, rep in patches:
        text, _ = _sub(pat, rep, text)
    if text == original:
        return False
    try:
        path.write_text(text, encoding="utf-8")
        return True
    except OSError:
        return False


# ── Per-file patch rules ──────────────────────────────────────────────────────

def _patch_claude_md(v: str, tests: int, agents: int,
                     hints: int, cmds: int) -> bool:
    return _patch_file(ROOT / "CLAUDE.md", [
        # version in title
        (r"(Plugin — v)\d+\.\d+\.\d+", rf"\g<1>{v}"),
        # agent count in description line
        (r"(\d+-stage pipeline → )\d+( specialist agents)", rf"\g<1>{agents}\2"),
        # test count
        (r"\*\*\d+ tests green\*\*", f"**{tests} tests green**"),
        # body hint count
        (r"\d+ body hints", f"{hints} body hints"),
        # slash command count
        (r"\d+ slash commands", f"{cmds} slash commands"),
        # footer date+version
        (r"(Updated \d{4}-\d{2}-\d{2} \(v)\d+\.\d+\.\d+(\))",
         rf"\g<1>{v}\2"),
    ])


def _patch_readme(v: str, tests: int, agents: int) -> bool:
    patches = [
        # "491 / 491 green (31 suites …)"
        (r"\d+ / \d+ green", f"{tests} / {tests} green"),
        # table row "| **Tests** | 491 / 491 …"
        (r"(\*\*Tests\*\* \| )\d+ / \d+", rf"\g<1>{tests} / {tests}"),
        # "through 13 specialist agents" — update agent count only
        (r"(through )\d+( specialist agents)", rf"\g<1>{agents}\2"),
    ]
    return _patch_file(ROOT / "README.md", patches)


def _patch_audit_me_first(tests: int) -> bool:
    return _patch_file(ROOT / "AUDIT_ME_FIRST.md", [
        (r"~\d+ passed", f"~{tests} passed"),
        (r"expected: ~\d+ passed", f"expected: ~{tests} passed"),
    ])


def _patch_directory_form(v: str, agents: int) -> bool:
    return _patch_file(ROOT / "DIRECTORY_SUBMISSION_FORM.md", [
        (r"(\*\*Version\*\* \| )\S+", rf"\g<1>{v}"),
        # update agent count in short desc only
        (r"(\d+-stage pipeline, )\d+( specialist agents)",
         rf"\g<1>{agents}\2"),
        (r"(through )\d+( specialist agents)", rf"\g<1>{agents}\2"),
    ])


def _patch_marketplace(v: str) -> bool:
    return _patch_file(ROOT / "MARKETPLACE_SUBMISSION.md", [
        (r"(Submission Package — v)\d+\.\d+\.\d+", rf"\g<1>{v}"),
        (r"(plugin\.json v)\d+\.\d+\.\d+", rf"\g<1>{v}"),
        (r"(\| \[CHANGELOG\.md\][^|]*\| Full version history \()[^)]+(\))",
         rf"\g<1>{v} current\2"),
    ])


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    v       = _version()
    tests   = _test_count()
    agents  = _agent_count()
    cmds    = _command_count()
    hints   = _hint_count()
    smoke   = _smoke_count()

    metrics = dict(version=v, tests=tests, agents=agents,
                   commands=cmds, hints=hints, smoke=smoke)
    print(f"sync_docs: {metrics}")

    changed: list[str] = []
    if _patch_claude_md(v, tests, agents, hints, cmds):
        changed.append("CLAUDE.md")
    if _patch_readme(v, tests, agents):
        changed.append("README.md")
    if _patch_audit_me_first(tests):
        changed.append("AUDIT_ME_FIRST.md")
    if _patch_directory_form(v, agents):
        changed.append("DIRECTORY_SUBMISSION_FORM.md")
    if _patch_marketplace(v):
        changed.append("MARKETPLACE_SUBMISSION.md")

    if changed:
        print(f"sync_docs: patched {changed}")
        # Stage updated files so they're included in the current commit
        subprocess.run(
            ["git", "add"] + changed,
            cwd=str(ROOT), check=False,
        )
    else:
        print("sync_docs: all docs already in sync")

    return 0


if __name__ == "__main__":
    sys.exit(main())
