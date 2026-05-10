"""
Checkpoint Manager - Resumable job execution from failures

Enables:
- Creating checkpoints at key decision points
- Resuming jobs from last successful checkpoint
- Tracking retry count and failure history
- Smart retry strategies (exponential backoff, jitter)
"""

from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
import random
import json
from pathlib import Path


class CheckpointManager:
    """Manage job checkpoints and resumption"""

    def __init__(self, vault_dir: str = "./job_vault"):
        self.vault_dir = Path(vault_dir)

    def can_resume(self, job_id: str) -> bool:
        """Check if job can be resumed from checkpoint"""
        job_dir = self.vault_dir / "jobs" / f"job-{job_id}"
        manifest_file = job_dir / "manifest.json"

        if not manifest_file.exists():
            return False

        with open(manifest_file) as f:
            manifest = json.load(f)

        return bool(manifest.get("checkpoints", []))

    def get_resumption_context(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the state to resume from.

        Returns: checkpoint state or None
        """
        job_dir = self.vault_dir / "jobs" / f"job-{job_id}"
        manifest_file = job_dir / "manifest.json"

        with open(manifest_file) as f:
            manifest = json.load(f)

        checkpoints = manifest.get("checkpoints", [])
        if not checkpoints:
            return None

        latest = checkpoints[-1]
        checkpoint_file = job_dir / "checkpoints" / latest["file"]

        with open(checkpoint_file) as f:
            checkpoint_data = json.load(f)

        return {
            "checkpoint_id": checkpoint_data["checkpoint_id"],
            "timestamp": checkpoint_data["timestamp"],
            "state": checkpoint_data["state"],
            "retry_count": manifest.get("retry_count", 0),
        }

    def calculate_backoff(self, retry_count: int, base_delay: int = 5) -> int:
        """
        Calculate exponential backoff with jitter.

        Prevents thundering herd problem.
        """
        # Exponential: 5s, 10s, 20s, 40s, 80s
        delay = base_delay * (2 ** retry_count)

        # Add jitter: ±10%
        jitter = random.randint(-10, 10)
        jittered_delay = int(delay * (1 + jitter / 100))

        return jittered_delay

    def should_retry(
        self,
        job_id: str,
        max_retries: int = 3,
        error_types_retriable: Optional[list] = None
    ) -> bool:
        """
        Determine if job should be retried.

        Args:
            job_id: job ID
            max_retries: maximum retry attempts
            error_types_retriable: list of retriable error types
                (e.g., ["timeout", "temporary_failure", "resource_busy"])

        Returns: True if should retry, False otherwise
        """
        job_dir = self.vault_dir / "jobs" / f"job-{job_id}"
        manifest_file = job_dir / "manifest.json"

        with open(manifest_file) as f:
            manifest = json.load(f)

        retry_count = manifest.get("retry_count", 0)

        # Max retries exceeded
        if retry_count >= max_retries:
            return False

        # Check last error type
        if error_types_retriable:
            last_error = manifest.get("last_error", "")
            is_retriable = any(
                error_type in last_error
                for error_type in error_types_retriable
            )
            if not is_retriable:
                return False

        return True

    def mark_retry(self, job_id: str, error: str):
        """
        Mark job for retry and increment retry counter.

        Called when a failure occurs but the job can be retried.
        """
        job_dir = self.vault_dir / "jobs" / f"job-{job_id}"
        manifest_file = job_dir / "manifest.json"

        with open(manifest_file) as f:
            manifest = json.load(f)

        manifest["retry_count"] = manifest.get("retry_count", 0) + 1
        manifest["last_error"] = error
        manifest["last_error_at"] = datetime.utcnow().isoformat() + "Z"
        manifest["status"] = "retriable_failure"

        with open(manifest_file, "w") as f:
            json.dump(manifest, f, indent=2, default=str)

    def create_failure_summary(self, job_id: str) -> Dict[str, Any]:
        """Create summary of failure for debugging"""
        job_dir = self.vault_dir / "jobs" / f"job-{job_id}"
        manifest_file = job_dir / "manifest.json"

        with open(manifest_file) as f:
            manifest = json.load(f)

        checkpoints = manifest.get("checkpoints", [])
        latest_checkpoint = checkpoints[-1] if checkpoints else None

        return {
            "job_id": job_id,
            "status": manifest.get("status"),
            "retry_count": manifest.get("retry_count", 0),
            "last_error": manifest.get("last_error"),
            "last_error_at": manifest.get("last_error_at"),
            "last_checkpoint": {
                "id": latest_checkpoint["id"],
                "timestamp": latest_checkpoint["timestamp"],
            } if latest_checkpoint else None,
            "work_log_file": str(job_dir / "work_log.md"),
        }

    def validate_checkpoint_consistency(self, job_id: str) -> bool:
        """
        Validate that checkpoint state is consistent.

        Returns True if all checkpoint data exists and is readable.
        """
        job_dir = self.vault_dir / "jobs" / f"job-{job_id}"
        manifest_file = job_dir / "manifest.json"

        if not manifest_file.exists():
            return False

        try:
            with open(manifest_file) as f:
                manifest = json.load(f)

            checkpoints_dir = job_dir / "checkpoints"
            for cp in manifest.get("checkpoints", []):
                cp_file = checkpoints_dir / cp["file"]
                if not cp_file.exists():
                    return False

                with open(cp_file) as f:
                    json.load(f)  # Validate JSON

            return True
        except Exception:
            return False


class RetryStrategy:
    """Pluggable retry strategy"""

    def should_retry(self, error: str, retry_count: int) -> bool:
        """Determine if error is retriable"""
        raise NotImplementedError

    def get_delay(self, retry_count: int) -> int:
        """Get delay in seconds before retry"""
        raise NotImplementedError


class ExponentialBackoffStrategy(RetryStrategy):
    """Exponential backoff with jitter"""

    def __init__(
        self,
        base_delay: int = 5,
        max_retries: int = 3,
        retriable_errors: Optional[list] = None
    ):
        self.base_delay = base_delay
        self.max_retries = max_retries
        self.retriable_errors = retriable_errors or [
            "timeout",
            "temporary_failure",
            "resource_busy",
            "rate_limit",
        ]

    def should_retry(self, error: str, retry_count: int) -> bool:
        """Check if error is retriable and retry limit not exceeded"""
        if retry_count >= self.max_retries:
            return False

        return any(e in error.lower() for e in self.retriable_errors)

    def get_delay(self, retry_count: int) -> int:
        """Calculate backoff delay"""
        delay = self.base_delay * (2 ** retry_count)
        jitter = random.randint(-10, 10)
        return int(delay * (1 + jitter / 100))


class CircuitBreakerStrategy(RetryStrategy):
    """
    Circuit breaker: fail fast if too many errors.

    Prevents cascading failures.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout_seconds: int = 60
    ):
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout_seconds = timeout_seconds

    def should_retry(self, error: str, retry_count: int) -> bool:
        """Always retriable until threshold reached"""
        return retry_count < self.failure_threshold

    def get_delay(self, retry_count: int) -> int:
        """Longer delay as retries increase"""
        # After threshold, circuit opens - use timeout
        if retry_count >= self.failure_threshold:
            return self.timeout_seconds
        return (retry_count + 1) * 10
