"""Tests for git_safety.py module."""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from git_safety import git_apply_backup, git_commit_safe, git_stash


class TestGitStash:
    """Tests for git_stash function."""

    @patch("git_safety.subprocess.run")
    def test_git_stash_succeeds(self, mock_run):
        """Test successful git stash operation."""
        mock_run.return_value = Mock(returncode=0)
        result = git_stash()
        assert result is True
        mock_run.assert_called_once()
        args, kwargs = mock_run.call_args
        assert args[0] == ["git", "stash"]
        assert kwargs["capture_output"] is True

    @patch("git_safety.subprocess.run")
    def test_git_stash_fails(self, mock_run):
        """Test failed git stash operation."""
        mock_run.return_value = Mock(returncode=1)
        result = git_stash()
        assert result is False

    @patch("git_safety.subprocess.run")
    def test_git_stash_timeout(self, mock_run):
        """Test git stash timeout."""
        mock_run.side_effect = subprocess.TimeoutExpired("git", 30)
        result = git_stash()
        assert result is False

    @patch("git_safety.subprocess.run")
    def test_git_stash_file_not_found(self, mock_run):
        """Test git stash with missing git command."""
        mock_run.side_effect = FileNotFoundError("git not found")
        result = git_stash()
        assert result is False


class TestGitApplyBackup:
    """Tests for git_apply_backup function."""

    def test_git_apply_backup_succeeds(self):
        """Test successful backup application."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create a backup file
            backup_file = tmpdir_path / "test.osp.bak"
            backup_file.write_text("backup content")

            # Apply backup
            result = git_apply_backup(backup_file)

            # Verify result and target file
            assert result is True
            target_file = tmpdir_path / "test"
            assert target_file.exists()
            assert target_file.read_text() == "backup content"

    def test_git_apply_backup_missing_file(self):
        """Test backup application with missing backup file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            backup_file = tmpdir_path / "nonexistent.osp.bak"
            result = git_apply_backup(backup_file)
            assert result is False

    def test_git_apply_backup_removes_osp_suffix(self):
        """Test that .osp.bak suffix is properly removed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create backup with .osp.bak suffix
            backup_file = tmpdir_path / "module.py.osp.bak"
            backup_file.write_text("module code")

            result = git_apply_backup(backup_file)

            assert result is True
            # Target should be module.py with both .osp.bak removed
            target_file = tmpdir_path / "module.py"
            assert target_file.exists()
            assert target_file.read_text() == "module code"

    @patch("git_safety.Path.read_bytes")
    def test_git_apply_backup_io_error(self, mock_read):
        """Test backup application with IO error."""
        mock_read.side_effect = IOError("Permission denied")
        with tempfile.TemporaryDirectory() as tmpdir:
            backup_file = Path(tmpdir) / "test.osp.bak"
            backup_file.write_text("content")
            result = git_apply_backup(backup_file)
            assert result is False


class TestGitCommitSafe:
    """Tests for git_commit_safe function."""

    @patch("git_safety.subprocess.run")
    def test_git_commit_safe_succeeds(self, mock_run):
        """Test successful git commit operation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create test files
            file1 = tmpdir_path / "file1.py"
            file1.write_text("code")
            file2 = tmpdir_path / "file2.py"
            file2.write_text("more code")

            # Mock subprocess calls
            mock_run.side_effect = [
                Mock(returncode=0),  # git add
                Mock(returncode=0)   # git commit
            ]

            result = git_commit_safe(
                "test commit",
                [str(file1), str(file2)]
            )

            assert result is True
            assert mock_run.call_count == 2

    def test_git_commit_safe_missing_file(self):
        """Test commit with missing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            file1 = tmpdir_path / "exists.py"
            file1.write_text("code")
            file2 = tmpdir_path / "nonexistent.py"

            result = git_commit_safe(
                "test commit",
                [str(file1), str(file2)]
            )

            assert result is False

    @patch("git_safety.subprocess.run")
    def test_git_commit_safe_add_fails(self, mock_run):
        """Test commit when git add fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            file1 = tmpdir_path / "file.py"
            file1.write_text("code")

            # Mock git add failure
            mock_run.return_value = Mock(
                returncode=1,
                stderr="error"
            )

            result = git_commit_safe(
                "test commit",
                [str(file1)]
            )

            assert result is False

    @patch("git_safety.subprocess.run")
    def test_git_commit_safe_commit_fails(self, mock_run):
        """Test commit when git commit fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            file1 = tmpdir_path / "file.py"
            file1.write_text("code")

            # Mock git add succeeds, commit fails
            mock_run.side_effect = [
                Mock(returncode=0),  # git add succeeds
                Mock(returncode=1, stderr="error")  # git commit fails
            ]

            result = git_commit_safe(
                "test commit",
                [str(file1)]
            )

            assert result is False

    @patch("git_safety.subprocess.run")
    def test_git_commit_safe_timeout(self, mock_run):
        """Test commit with timeout."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            file1 = tmpdir_path / "file.py"
            file1.write_text("code")

            mock_run.side_effect = subprocess.TimeoutExpired("git", 30)

            result = git_commit_safe(
                "test commit",
                [str(file1)]
            )

            assert result is False

    @patch("git_safety.subprocess.run")
    def test_git_commit_safe_file_not_found(self, mock_run):
        """Test commit with missing git command."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            file1 = tmpdir_path / "file.py"
            file1.write_text("code")

            mock_run.side_effect = FileNotFoundError("git not found")

            result = git_commit_safe(
                "test commit",
                [str(file1)]
            )

            assert result is False

    @patch("git_safety.subprocess.run")
    def test_git_commit_safe_empty_file_list(self, mock_run):
        """Test commit with empty file list."""
        mock_run.side_effect = [
            Mock(returncode=0),  # git add with empty list
            Mock(returncode=0)   # git commit
        ]

        result = git_commit_safe(
            "test commit",
            []
        )

        assert result is True
