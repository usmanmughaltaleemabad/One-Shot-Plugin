import subprocess
import json
import os
from pathlib import Path
import tempfile
import shutil


def test_session_start_hook_runs_docs_drift_check(tmp_path):
    """Test that session-start hook runs docs-drift check and creates docs-state.json."""
    # Copy the hook and necessary scripts to temp directory
    repo_root = Path(__file__).parent.parent

    # Create necessary directories
    (tmp_path / ".claude" / "hooks").mkdir(parents=True, exist_ok=True)
    (tmp_path / "scripts").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".beads").mkdir(parents=True, exist_ok=True)

    # Copy the hook script
    hook_src = repo_root / ".claude" / "hooks" / "session-start.sh"
    hook_dst = tmp_path / ".claude" / "hooks" / "session-start.sh"
    shutil.copy(hook_src, hook_dst)

    # Copy codebase_diff.py
    script_src = repo_root / "scripts" / "codebase_diff.py"
    script_dst = tmp_path / "scripts" / "codebase_diff.py"
    shutil.copy(script_src, script_dst)

    # Copy phase-status.md
    docs_src = repo_root / "docs" / "phase-status.md"
    docs_dst = tmp_path / "docs" / "phase-status.md"
    if docs_src.exists():
        docs_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(docs_src, docs_dst)

    # Run the hook from the temp directory with UTF-8 encoding
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    result = subprocess.run(
        ["bash", ".claude/hooks/session-start.sh"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        encoding='utf-8',
        env=env
    )

    # Verify the hook ran successfully
    assert result.returncode == 0, f"Hook failed with code {result.returncode}: {result.stderr}"

    # Check that docs-drift message appears in output
    output = result.stdout if result.stdout else ""
    assert "[Hook] Running docs-drift check..." in output, \
        f"Hook didn't print docs-drift message. Output: {output[:500]}"

    # Verify docs-state.json was created
    docs_state_file = tmp_path / ".beads" / "docs-state.json"
    assert docs_state_file.exists(), f"docs-state.json was not created at {docs_state_file}"

    # Verify it contains valid JSON with codebase structure
    with open(docs_state_file, encoding='utf-8') as f:
        content = json.load(f)
        # Should be a dict with file keys
        assert isinstance(content, dict), "docs-state.json should contain a JSON object"


def test_session_start_hook_gracefully_handles_missing_script(tmp_path):
    """Test that hook gracefully handles missing codebase_diff.py."""
    # Copy the hook only
    repo_root = Path(__file__).parent.parent

    (tmp_path / ".claude" / "hooks").mkdir(parents=True, exist_ok=True)
    (tmp_path / ".beads").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs").mkdir(parents=True, exist_ok=True)

    hook_src = repo_root / ".claude" / "hooks" / "session-start.sh"
    hook_dst = tmp_path / ".claude" / "hooks" / "session-start.sh"
    shutil.copy(hook_src, hook_dst)

    # Create minimal phase-status.md
    (tmp_path / "docs" / "phase-status.md").write_text("# Status\n| **0** | Status |", encoding='utf-8')

    # Run the hook without codebase_diff.py present
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    result = subprocess.run(
        ["bash", ".claude/hooks/session-start.sh"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        encoding='utf-8',
        env=env
    )

    # Verify the hook still ran successfully
    assert result.returncode == 0, f"Hook failed: {result.stderr}"

    # Check that it emits skip message
    output = result.stdout if result.stdout else ""
    assert "Skipping docs-drift check" in output, \
        f"Hook didn't print skip message. Output: {output[:500]}"

    # Verify docs-state.json was NOT created
    docs_state_file = tmp_path / ".beads" / "docs-state.json"
    assert not docs_state_file.exists(), f"docs-state.json should not be created when script is missing"


def test_session_start_hook_file_exists():
    """Test that the session-start.sh hook file exists and contains docs-drift check."""
    repo_root = Path(__file__).parent.parent
    hook_file = repo_root / ".claude" / "hooks" / "session-start.sh"

    assert hook_file.exists(), f"Hook file not found at {hook_file}"

    hook_content = hook_file.read_text(encoding='utf-8')
    assert "docs-drift check" in hook_content, "Hook should mention docs-drift check"
    assert "scripts/codebase_diff.py" in hook_content, "Hook should reference codebase_diff.py"
    assert ".beads/docs-state.json" in hook_content, "Hook should write to docs-state.json"
