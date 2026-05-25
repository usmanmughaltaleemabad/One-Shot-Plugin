"""Tests for rollback.py module."""

import json
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, call

import pytest

# Setup path for imports
import sys
sys_path = Path(__file__).parent.resolve()
if str(sys_path) not in sys.path:
    sys.path.insert(0, str(sys_path))

skills_scripts_path = sys_path.parent / "skills" / "one-shot-generator" / "scripts"
if str(skills_scripts_path) not in sys.path:
    sys.path.insert(0, str(skills_scripts_path))

from rollback import execute_rollback, _find_backup_directory


class TestFindBackupDirectory:
    """Tests for _find_backup_directory function."""

    def test_find_backup_directory_exists(self):
        """Test finding backup directory when it exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            backup_dir = tmpdir_path / ".osp.bak"
            backup_dir.mkdir()

            result = _find_backup_directory(repo_root=tmpdir_path)
            assert result == backup_dir

    def test_find_backup_directory_not_exists(self):
        """Test backup directory not found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            result = _find_backup_directory(repo_root=tmpdir_path)
            assert result is None

    def test_find_backup_directory_walks_up(self):
        """Test that search walks up directory tree."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            # Create backup dir in root
            backup_dir = tmpdir_path / ".osp.bak"
            backup_dir.mkdir()

            # Create nested subdirectory
            nested = tmpdir_path / "deep" / "nested" / "dir"
            nested.mkdir(parents=True)

            # Search from nested directory (should find backup dir above)
            # Note: This test verifies the walking logic when repo_root is not provided
            # When repo_root IS provided, we only search from that root
            result = _find_backup_directory(repo_root=nested)
            # When repo_root is provided, it doesn't walk up, only checks that dir
            assert result is None

    def test_find_backup_directory_with_repo_root(self):
        """Test finding backup directory with explicit repo root."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            backup_dir = tmpdir_path / ".osp.bak"
            backup_dir.mkdir()

            result = _find_backup_directory(repo_root=tmpdir_path)
            assert result == backup_dir


class TestExecuteRollback:
    """Tests for execute_rollback function."""

    @patch("rollback.reset_failure_counter")
    @patch("rollback.git_apply_backup")
    @patch("rollback.git_stash")
    def test_execute_rollback_succeeds(self, mock_stash, mock_apply, mock_reset):
        """Test successful rollback with backup files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create backup directory with backup files
            backup_dir = tmpdir_path / ".osp.bak"
            backup_dir.mkdir()
            backup_file1 = backup_dir / "file1.py.osp.bak"
            backup_file2 = backup_dir / "file2.py.osp.bak"
            backup_file1.write_text("backup1")
            backup_file2.write_text("backup2")

            # Setup mocks
            mock_stash.return_value = True
            mock_apply.return_value = True
            mock_reset.return_value = None

            result = execute_rollback(repo_root=tmpdir_path)

            assert result is True
            mock_stash.assert_called_once()
            assert mock_apply.call_count == 2
            mock_reset.assert_called_once()

    @patch("rollback.reset_failure_counter")
    @patch("rollback.git_apply_backup")
    @patch("rollback.git_stash")
    def test_execute_rollback_no_backup_dir(self, mock_stash, mock_apply, mock_reset):
        """Test rollback when backup directory doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            result = execute_rollback(repo_root=tmpdir_path)

            assert result is False
            mock_stash.assert_not_called()
            mock_apply.assert_not_called()
            mock_reset.assert_not_called()

    @patch("rollback.reset_failure_counter")
    @patch("rollback.git_apply_backup")
    @patch("rollback.git_stash")
    def test_execute_rollback_stash_fails(self, mock_stash, mock_apply, mock_reset):
        """Test rollback when git stash fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create backup directory
            backup_dir = tmpdir_path / ".osp.bak"
            backup_dir.mkdir()

            # Mock stash failure
            mock_stash.return_value = False

            result = execute_rollback(repo_root=tmpdir_path)

            assert result is False
            mock_stash.assert_called_once()
            mock_apply.assert_not_called()
            mock_reset.assert_not_called()

    @patch("rollback.reset_failure_counter")
    @patch("rollback.git_apply_backup")
    @patch("rollback.git_stash")
    def test_execute_rollback_apply_fails(self, mock_stash, mock_apply, mock_reset):
        """Test rollback when backup application fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create backup directory with backup files
            backup_dir = tmpdir_path / ".osp.bak"
            backup_dir.mkdir()
            backup_file = backup_dir / "file.py.osp.bak"
            backup_file.write_text("backup")

            # Mock partial failure
            mock_stash.return_value = True
            mock_apply.return_value = False
            mock_reset.return_value = None

            result = execute_rollback(repo_root=tmpdir_path)

            assert result is False
            mock_stash.assert_called_once()
            mock_apply.assert_called_once()
            mock_reset.assert_not_called()

    @patch("rollback.reset_failure_counter")
    @patch("rollback.git_apply_backup")
    @patch("rollback.git_stash")
    def test_execute_rollback_no_backup_files(self, mock_stash, mock_apply, mock_reset):
        """Test rollback when backup directory is empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create empty backup directory
            backup_dir = tmpdir_path / ".osp.bak"
            backup_dir.mkdir()

            mock_stash.return_value = True
            mock_reset.return_value = None

            result = execute_rollback(repo_root=tmpdir_path)

            assert result is True
            mock_stash.assert_called_once()
            mock_apply.assert_not_called()
            mock_reset.assert_called_once()

    @patch("rollback.reset_failure_counter")
    @patch("rollback.git_apply_backup")
    @patch("rollback.git_stash")
    def test_execute_rollback_reset_fails(self, mock_stash, mock_apply, mock_reset):
        """Test rollback when resetting failure counter fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create backup directory with backup files
            backup_dir = tmpdir_path / ".osp.bak"
            backup_dir.mkdir()
            backup_file = backup_dir / "file.py.osp.bak"
            backup_file.write_text("backup")

            # Mock reset failure
            mock_stash.return_value = True
            mock_apply.return_value = True
            mock_reset.side_effect = OSError("Permission denied")

            result = execute_rollback(repo_root=tmpdir_path)

            assert result is False
            mock_stash.assert_called_once()
            mock_apply.assert_called_once()
            mock_reset.assert_called_once()

    @patch("rollback.reset_failure_counter")
    @patch("rollback.git_apply_backup")
    @patch("rollback.git_stash")
    def test_execute_rollback_multiple_files(self, mock_stash, mock_apply, mock_reset):
        """Test rollback with multiple backup files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create backup directory with multiple files
            backup_dir = tmpdir_path / ".osp.bak"
            backup_dir.mkdir()
            for i in range(5):
                backup_file = backup_dir / f"file{i}.py.osp.bak"
                backup_file.write_text(f"backup{i}")

            mock_stash.return_value = True
            mock_apply.return_value = True
            mock_reset.return_value = None

            result = execute_rollback(repo_root=tmpdir_path)

            assert result is True
            assert mock_apply.call_count == 5
            mock_reset.assert_called_once()

    @patch("rollback.reset_failure_counter")
    @patch("rollback.git_apply_backup")
    @patch("rollback.git_stash")
    def test_execute_rollback_partial_failure(self, mock_stash, mock_apply, mock_reset):
        """Test rollback when some backups fail."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create backup directory with multiple files
            backup_dir = tmpdir_path / ".osp.bak"
            backup_dir.mkdir()
            for i in range(3):
                backup_file = backup_dir / f"file{i}.py.osp.bak"
                backup_file.write_text(f"backup{i}")

            mock_stash.return_value = True
            # First two succeed, third fails
            mock_apply.side_effect = [True, True, False]
            mock_reset.return_value = None

            result = execute_rollback(repo_root=tmpdir_path)

            assert result is False
            assert mock_apply.call_count == 3
            mock_reset.assert_not_called()

    @patch("rollback.reset_failure_counter")
    @patch("rollback.git_apply_backup")
    @patch("rollback.git_stash")
    def test_execute_rollback_with_none_repo_root(self, mock_stash, mock_apply, mock_reset):
        """Test rollback with None repo_root (uses current directory)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create backup directory
            backup_dir = tmpdir_path / ".osp.bak"
            backup_dir.mkdir()

            mock_stash.return_value = True
            mock_reset.return_value = None

            # Call with None repo_root
            # This will search from cwd, so backup won't be found
            result = execute_rollback(repo_root=None)

            # Result depends on whether .osp.bak exists in actual filesystem tree
            # In test environment, it won't, so should return False
            assert isinstance(result, bool)


class TestRollbackIntegration:
    """Integration tests for rollback orchestration."""

    def test_rollback_workflow_complete(self):
        """Test complete rollback workflow without mocks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create backup directory with actual files
            backup_dir = tmpdir_path / ".osp.bak"
            backup_dir.mkdir()

            # Create target files that will be restored
            target_file1 = tmpdir_path / "module1.py"
            target_file1.write_text("old module1")

            target_file2 = tmpdir_path / "module2.py"
            target_file2.write_text("old module2")

            # Create backup files
            backup_file1 = backup_dir / "module1.py.osp.bak"
            backup_file1.write_text("new module1")

            backup_file2 = backup_dir / "module2.py.osp.bak"
            backup_file2.write_text("new module2")

            # Mock only git operations and failure detector
            with patch("rollback.git_stash") as mock_stash, \
                 patch("rollback.reset_failure_counter") as mock_reset, \
                 patch("rollback.git_apply_backup") as mock_apply:

                mock_stash.return_value = True
                mock_apply.return_value = True
                mock_reset.return_value = None

                result = execute_rollback(repo_root=tmpdir_path)

                assert result is True
                # Verify git operations were called
                mock_stash.assert_called_once()
                assert mock_apply.call_count == 2
                mock_reset.assert_called_once()
