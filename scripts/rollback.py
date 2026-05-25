#!/usr/bin/env python3
"""
Rollback Orchestrator — v1.0.0

Orchestrates autonomous recovery by rolling back to the last successful .osp.bak state.
This module coordinates git_safety operations with failure_detector to restore a known-good
state when consecutive failures exceed a threshold.

CLI:
    python rollback.py --threshold 3
    python rollback.py --threshold 3 --repo-root /path/to/repo
    python rollback.py --check-only  (check if rollback should trigger without executing)
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

# Setup path for imports from parent and sibling modules
sys_path = Path(__file__).parent.resolve()
if str(sys_path) not in sys.path:
    sys.path.insert(0, str(sys_path))

# Import git_safety functions
try:
    from git_safety import git_apply_backup, git_stash
except ImportError as e:
    print(f"Error importing git_safety: {e}", file=sys.stderr)
    sys.exit(1)

# Import failure_detector functions from sibling skills directory
skills_scripts_path = sys_path.parent / "skills" / "one-shot-generator" / "scripts"
if str(skills_scripts_path) not in sys.path:
    sys.path.insert(0, str(skills_scripts_path))

try:
    from failure_detector import (
        reset_failure_counter,
        should_trigger_rollback,
        load_failure_state,
    )
except ImportError as e:
    print(f"Error importing failure_detector: {e}", file=sys.stderr)
    sys.exit(1)


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def _find_backup_directory(repo_root: Optional[Path] = None) -> Optional[Path]:
    """Locate .osp.bak directory.

    Args:
        repo_root: Optional repo root to search from. If None, searches from cwd.

    Returns:
        Path to .osp.bak directory if found, None otherwise.
    """
    if repo_root:
        search_root = repo_root.resolve()
    else:
        search_root = Path.cwd().resolve()

    backup_dir = search_root / ".osp.bak"
    if backup_dir.exists() and backup_dir.is_dir():
        return backup_dir

    # Walk up from cwd if no repo_root specified
    if not repo_root:
        cur = search_root
        while cur != cur.parent:
            backup_dir = cur / ".osp.bak"
            if backup_dir.exists() and backup_dir.is_dir():
                return backup_dir
            cur = cur.parent

    return None


def execute_rollback(repo_root: Optional[Path] = None) -> bool:
    """Rollback to last successful .osp.bak state.

    Executes the following steps:
    1. Check if .osp.bak directory exists
    2. Stash uncommitted changes via git_stash()
    3. For each *.osp.bak file in .osp.bak/:
       - Apply the backup using git_apply_backup()
    4. Reset the failure counter via reset_failure_counter()
    5. Return True if all operations succeeded

    Args:
        repo_root: Optional repo root path. Auto-discovered if None.

    Returns:
        True if rollback succeeded, False otherwise.
    """
    if repo_root:
        repo_root = repo_root.resolve()

    logger.info("Starting rollback orchestration...")

    # Step 1: Check if .osp.bak directory exists
    backup_dir = _find_backup_directory(repo_root=repo_root)
    if not backup_dir:
        logger.error("Backup directory (.osp.bak) not found. Cannot rollback.")
        return False

    logger.info(f"Found backup directory: {backup_dir}")

    # Step 2: Stash uncommitted changes
    logger.info("Stashing uncommitted changes...")
    if not git_stash():
        logger.error("Failed to stash changes. Rollback aborted.")
        return False

    logger.info("Changes stashed successfully.")

    # Step 3: Apply each backup file
    backup_files = list(backup_dir.glob("*.osp.bak"))
    if not backup_files:
        logger.warning("No backup files found in .osp.bak directory.")
        # Still reset counter as directory exists
        try:
            reset_failure_counter(repo_root=repo_root)
            logger.info("Failure counter reset (no backups to apply).")
            return True
        except Exception as e:
            logger.error(f"Failed to reset failure counter: {e}")
            return False

    logger.info(f"Found {len(backup_files)} backup files to restore.")

    all_succeeded = True
    for backup_file in backup_files:
        logger.info(f"Applying backup: {backup_file.name}")
        if not git_apply_backup(backup_file):
            logger.error(f"Failed to apply backup: {backup_file.name}")
            all_succeeded = False
        else:
            logger.info(f"Successfully applied: {backup_file.name}")

    if not all_succeeded:
        logger.error("One or more backups failed to apply.")
        return False

    # Step 4: Reset failure counter on success
    logger.info("Resetting failure counter...")
    try:
        reset_failure_counter(repo_root=repo_root)
        logger.info("Failure counter reset successfully.")
    except Exception as e:
        logger.error(f"Failed to reset failure counter: {e}")
        return False

    logger.info("Rollback completed successfully.")
    return True


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Orchestrate autonomous recovery via rollback to .osp.bak state"
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=3,
        help="Consecutive failure threshold for rollback trigger (default: 3)",
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Plugin repo root (auto-discovered if not provided)",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Check if rollback should trigger without executing",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force rollback regardless of threshold",
    )
    args = parser.parse_args()

    repo_root = None
    if args.repo_root:
        repo_root = Path(args.repo_root).resolve()

    # Determine if rollback should trigger
    should_rollback = args.force or should_trigger_rollback(
        threshold=args.threshold,
        repo_root=repo_root,
    )

    if args.check_only:
        state = load_failure_state(repo_root=repo_root)
        consecutive = state.get("consecutive_failures", 0)
        print(f"Consecutive failures: {consecutive} / Threshold: {args.threshold}")
        print(f"Should trigger rollback: {should_rollback}")
        sys.exit(0 if should_rollback else 1)

    if not should_rollback:
        logger.info(
            "Rollback not triggered (failures < threshold). "
            "Use --force to override."
        )
        print("Rollback not triggered (failures < threshold)")
        return

    # Execute rollback
    success = execute_rollback(repo_root=repo_root)
    if success:
        print("Rollback executed successfully.")
        sys.exit(0)
    else:
        print("Rollback failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
