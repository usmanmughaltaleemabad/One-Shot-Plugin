"""Tests for hooks/block-bad-commands.sh (PreToolUse Bash guard)."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

HOOK = Path(__file__).parent.parent / "hooks" / "block-bad-commands.sh"

pytestmark = pytest.mark.skipif(shutil.which("bash") is None, reason="bash not available")


def run_hook(command, tmp_path):
    """Feed the hook a PreToolUse event for `command`; return (exit code, stderr)."""
    return run_hook_raw(json.dumps({"tool_input": {"command": command}}), tmp_path)


def run_hook_raw(event, tmp_path):
    """Feed the hook an arbitrary stdin payload; return (exit code, stderr)."""
    result = subprocess.run(
        ["bash", str(HOOK)],
        input=event,
        capture_output=True,
        text=True,
        encoding="utf-8",
        # Point the version check at an empty dir so it is skipped.
        env={"PATH": "/usr/bin:/bin:/usr/local/bin", "CLAUDE_PLUGIN_ROOT": str(tmp_path)},
    )
    return result.returncode, result.stderr


@pytest.mark.parametrize(
    "command",
    [
        "git push --force origin main",
        "git push -f origin main",
        "git push -uf origin main",
        "git push --force-with-lease origin main",
        "git push origin main --force",
        "git push origin +main",
        "git push origin +feature:main",
    ],
)
def test_blocks_force_push_to_main(command, tmp_path):
    code, err = run_hook(command, tmp_path)
    assert code == 2
    assert "Force push to main is blocked" in err


@pytest.mark.parametrize(
    "command",
    [
        "git push origin main",
        "git push --follow-tags origin main",
        "git push -f origin feature-branch",
        "git push origin domain-fix",
        # "-form" in a branch name is not "-f", and "main" in a later
        # chained command is not a push target.
        "git push -u origin contact-form-fix && gh pr create --base main",
    ],
)
def test_allows_non_force_pushes_and_other_branches(command, tmp_path):
    code, _ = run_hook(command, tmp_path)
    assert code == 0


@pytest.mark.parametrize(
    "command",
    [
        "git add .env.local",
        "git add config/secrets.yml",
        'git commit -m "add credentials file"',
    ],
)
def test_blocks_committing_env_and_secrets(command, tmp_path):
    code, err = run_hook(command, tmp_path)
    assert code == 2
    assert "Do not commit .env files or credentials" in err


@pytest.mark.parametrize(
    "command",
    [
        # Mentioning these words outside git add/commit must not be blocked.
        "vercel env add TURNSTILE_SECRET production",
        "jq .secret widget.json",
        "ls ~/.aws/credentials",
    ],
)
def test_allows_secret_words_outside_git_add_commit(command, tmp_path):
    code, _ = run_hook(command, tmp_path)
    assert code == 0


@pytest.mark.parametrize(
    "event",
    [
        json.dumps({"tool_input": {"command": ""}}),
        json.dumps({"tool_input": {}}),
        json.dumps({"tool_input": None}),
        json.dumps({}),
        "",
        "not json",
    ],
    ids=["empty-command", "no-command", "null-tool-input", "no-tool-input", "empty-stdin", "invalid-json"],
)
def test_malformed_or_empty_input_is_allowed_without_error(event, tmp_path):
    code, err = run_hook_raw(event, tmp_path)
    assert code == 0
    assert "ERROR" not in err
