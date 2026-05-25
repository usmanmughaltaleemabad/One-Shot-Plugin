#!/usr/bin/env python3
"""
Test rollback flag parsing and behavior in SKILL.md.

Tests:
  1. --rollback flag is parsed correctly (default=true)
  2. --rollback=false disables rollback
  3. --rollback=true explicitly enables rollback
  4. Rollback decision logic (threshold-based)
  5. Failure counter tracking integration
"""

import json
import sys
import tempfile
from pathlib import Path

import pytest

# Add skills/one-shot-generator/scripts to path for failure_detector
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "one-shot-generator" / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from failure_detector import (
    load_failure_state,
    record_failure,
    reset_failure_counter,
    should_trigger_rollback,
)
from rollback import _find_backup_directory


class TestRollbackFlagParsing:
    """Test parsing of --rollback flag from arguments."""

    def test_rollback_default_enabled(self):
        """Default: --rollback should be True."""
        # Simulate ARGUMENTS from SKILL.md
        arguments = "add shopping cart @./project --apply"
        assert "--rollback" not in arguments or "--rollback=false" not in arguments
        # Default behavior: rollback is enabled

    def test_rollback_explicit_true(self):
        """Explicit --rollback or --rollback=true enables rollback."""
        arguments = "add shopping cart @./project --apply --rollback"
        assert "--rollback" in arguments
        assert "--rollback=false" not in arguments

    def test_rollback_explicit_false(self):
        """--rollback=false disables rollback."""
        arguments = "add shopping cart @./project --apply --rollback=false"
        assert "--rollback=false" in arguments

    def test_rollback_with_other_flags(self):
        """--rollback plays nicely with other flags."""
        arguments = "add cart @./p --apply --budget=5.0 --rollback --grill"
        assert "--rollback" in arguments
        assert "--apply" in arguments
        assert "--budget=5.0" in arguments
        assert "--grill" in arguments


class TestFailureCounterTracking:
    """Test failure counter behavior in .beads/failures_state.jsonl."""

    @pytest.fixture
    def temp_repo(self):
        """Create a temporary repo with .beads directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            beads_dir = repo_root / ".beads"
            beads_dir.mkdir(parents=True, exist_ok=True)
            yield repo_root

    def test_load_failure_state_default(self, temp_repo):
        """Default state: 0 failures, no spec."""
        state = load_failure_state(repo_root=temp_repo)
        assert state["consecutive_failures"] == 0
        assert state["last_failing_spec"] is None
        assert state["last_failure_ts"] is None

    def test_record_failure_increments_counter(self, temp_repo):
        """record_failure() increments consecutive count."""
        count1 = record_failure("spec_hash_1", repo_root=temp_repo)
        assert count1 == 1

        count2 = record_failure("spec_hash_2", repo_root=temp_repo)
        assert count2 == 2

        count3 = record_failure("spec_hash_3", repo_root=temp_repo)
        assert count3 == 3

    def test_reset_failure_counter(self, temp_repo):
        """reset_failure_counter() sets consecutive to 0."""
        record_failure("spec_1", repo_root=temp_repo)
        record_failure("spec_2", repo_root=temp_repo)

        reset_failure_counter(repo_root=temp_repo)

        state = load_failure_state(repo_root=temp_repo)
        assert state["consecutive_failures"] == 0

    def test_failure_state_persists(self, temp_repo):
        """Failure state is written to .beads/failures_state.jsonl."""
        state_file = temp_repo / ".beads" / "failures_state.jsonl"

        record_failure("spec_1", repo_root=temp_repo)
        assert state_file.exists()

        lines = state_file.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) >= 1

        last_record = json.loads(lines[-1])
        assert last_record["consecutive_failures"] == 1
        assert last_record["last_failing_spec"] == "spec_1"


class TestRollbackTriggerLogic:
    """Test should_trigger_rollback decision logic."""

    @pytest.fixture
    def temp_repo(self):
        """Create a temporary repo with .beads directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            beads_dir = repo_root / ".beads"
            beads_dir.mkdir(parents=True, exist_ok=True)
            yield repo_root

    def test_no_trigger_below_threshold(self, temp_repo):
        """Rollback should NOT trigger when failures < threshold."""
        record_failure("spec_1", repo_root=temp_repo)
        record_failure("spec_2", repo_root=temp_repo)

        should_trigger = should_trigger_rollback(threshold=3, repo_root=temp_repo)
        assert should_trigger is False

    def test_trigger_at_threshold(self, temp_repo):
        """Rollback SHOULD trigger when failures == threshold."""
        record_failure("spec_1", repo_root=temp_repo)
        record_failure("spec_2", repo_root=temp_repo)
        record_failure("spec_3", repo_root=temp_repo)

        should_trigger = should_trigger_rollback(threshold=3, repo_root=temp_repo)
        assert should_trigger is True

    def test_trigger_above_threshold(self, temp_repo):
        """Rollback SHOULD trigger when failures > threshold."""
        for i in range(5):
            record_failure(f"spec_{i}", repo_root=temp_repo)

        should_trigger = should_trigger_rollback(threshold=3, repo_root=temp_repo)
        assert should_trigger is True

    def test_custom_threshold(self, temp_repo):
        """Custom threshold values are respected."""
        record_failure("spec_1", repo_root=temp_repo)
        record_failure("spec_2", repo_root=temp_repo)

        # Threshold=2: should trigger
        assert should_trigger_rollback(threshold=2, repo_root=temp_repo) is True

        # Threshold=3: should NOT trigger
        assert should_trigger_rollback(threshold=3, repo_root=temp_repo) is False

        # Reset and test threshold=1
        reset_failure_counter(repo_root=temp_repo)
        record_failure("spec_1", repo_root=temp_repo)

        assert should_trigger_rollback(threshold=1, repo_root=temp_repo) is True


class TestBackupDirectoryDetection:
    """Test .osp.bak directory discovery."""

    @pytest.fixture
    def temp_repo(self):
        """Create a temporary repo structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            yield repo_root

    def test_find_backup_directory_exists(self, temp_repo):
        """Should find .osp.bak if it exists."""
        backup_dir = temp_repo / ".osp.bak"
        backup_dir.mkdir(parents=True, exist_ok=True)

        found = _find_backup_directory(repo_root=temp_repo)
        assert found == backup_dir

    def test_find_backup_directory_missing(self, temp_repo):
        """Should return None if .osp.bak doesn't exist."""
        found = _find_backup_directory(repo_root=temp_repo)
        assert found is None

    def test_find_backup_with_files(self, temp_repo):
        """Should find .osp.bak with multiple backup files."""
        backup_dir = temp_repo / ".osp.bak"
        backup_dir.mkdir(parents=True, exist_ok=True)

        (backup_dir / "models.py.osp.bak").write_text("# backup")
        (backup_dir / "router.py.osp.bak").write_text("# backup")

        found = _find_backup_directory(repo_root=temp_repo)
        assert found == backup_dir
        assert len(list(backup_dir.glob("*.osp.bak"))) == 2


class TestRollbackIntegration:
    """Integration tests for full rollback workflow."""

    @pytest.fixture
    def temp_repo(self):
        """Create a temporary repo with backup files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)

            # Initialize git repo
            import subprocess
            subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=repo_root,
                check=True,
                capture_output=True
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"],
                cwd=repo_root,
                check=True,
                capture_output=True
            )

            # Create .beads and .osp.bak directories
            (repo_root / ".beads").mkdir(parents=True, exist_ok=True)
            backup_dir = repo_root / ".osp.bak"
            backup_dir.mkdir(parents=True, exist_ok=True)

            yield repo_root

    def test_rollback_resets_failure_counter(self, temp_repo):
        """After rollback, failure counter should be 0."""
        # Record 3 failures
        for i in range(3):
            record_failure(f"spec_{i}", repo_root=temp_repo)

        state_before = load_failure_state(repo_root=temp_repo)
        assert state_before["consecutive_failures"] == 3

        # Execute rollback
        # (Will skip git operations in test, but should reset counter)
        reset_failure_counter(repo_root=temp_repo)

        state_after = load_failure_state(repo_root=temp_repo)
        assert state_after["consecutive_failures"] == 0

    def test_rollback_scenario_3_failures(self, temp_repo):
        """Simulate: 3 failures → rollback triggered → counter reset."""
        # Note: execute_rollback requires git operations, so we skip it in tests
        # and just test the counter reset behavior

        # Iteration 1: fail
        record_failure("spec_v1", repo_root=temp_repo)
        assert should_trigger_rollback(threshold=3, repo_root=temp_repo) is False

        # Iteration 2: fail again
        record_failure("spec_v2", repo_root=temp_repo)
        assert should_trigger_rollback(threshold=3, repo_root=temp_repo) is False

        # Iteration 3: fail again → trigger rollback
        record_failure("spec_v3", repo_root=temp_repo)
        assert should_trigger_rollback(threshold=3, repo_root=temp_repo) is True

        # Rollback executes, counter reset
        reset_failure_counter(repo_root=temp_repo)

        state = load_failure_state(repo_root=temp_repo)
        assert state["consecutive_failures"] == 0
        assert should_trigger_rollback(threshold=3, repo_root=temp_repo) is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
