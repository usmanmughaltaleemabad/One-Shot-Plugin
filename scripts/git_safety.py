"""Safe git operations for rollback and commit management."""

import subprocess
from pathlib import Path
from typing import List


def git_stash() -> bool:
    """Stash uncommitted changes safely.

    Returns:
        True if stash succeeded, False otherwise.
    """
    try:
        result = subprocess.run(
            ["git", "stash"],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"Error stashing changes: {e}")
        return False


def git_apply_backup(backup_path: Path) -> bool:
    """Apply .osp.bak file safely.

    Restores a backup file by copying its content to the target location
    (backup_path with .osp.bak suffix removed).

    Args:
        backup_path: Path to the backup file (typically *.osp.bak)

    Returns:
        True if backup was applied successfully, False otherwise.
    """
    try:
        backup_path = Path(backup_path)

        # Verify backup exists
        if not backup_path.exists():
            print(f"Backup file not found: {backup_path}")
            return False

        # Determine target path by removing .osp.bak suffix
        target_path = backup_path.with_suffix("")
        if str(target_path).endswith(".osp"):
            target_path = Path(str(target_path)[:-4])

        # Copy backup content to target
        target_path.write_bytes(backup_path.read_bytes())
        return True

    except (OSError, IOError) as e:
        print(f"Error applying backup: {e}")
        return False


def git_commit_safe(message: str, files: List[str]) -> bool:
    """Commit with safety checks.

    Verifies all files exist, stages them, and commits with the given message.

    Args:
        message: Commit message
        files: List of file paths to commit

    Returns:
        True if commit succeeded, False otherwise.
    """
    try:
        # Verify each file exists
        for file in files:
            file_path = Path(file)
            if not file_path.exists():
                print(f"File not found: {file}")
                return False

        # Add files to staging area
        add_result = subprocess.run(
            ["git", "add"] + files,
            capture_output=True,
            text=True,
            timeout=30
        )
        if add_result.returncode != 0:
            print(f"Failed to stage files: {add_result.stderr}")
            return False

        # Commit with message
        commit_result = subprocess.run(
            ["git", "commit", "-m", message],
            capture_output=True,
            text=True,
            timeout=30
        )
        return commit_result.returncode == 0

    except (OSError, subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"Error during commit: {e}")
        return False
