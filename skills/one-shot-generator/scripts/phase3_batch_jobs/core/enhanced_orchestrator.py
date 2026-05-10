"""
Enhanced Orchestrator - OneShot-inspired stateful job orchestration

Coordinates Phase 3 batch job infrastructure with:
- Vault-centric state management
- Checkpoint-based resumption
- Budget enforcement
- Comprehensive audit trails
- Human-in-the-loop approval gates
"""

from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import json

from job_vault import JobVault, JobStatus, WorkLogEntry
from checkpoint_manager import CheckpointManager, ExponentialBackoffStrategy
from budget_gate import BudgetGate, BudgetDecision


class EnhancedOrchestrator:
    """
    Stateful job orchestrator inspired by OneShot.

    Responsibilities:
    - Manage job lifecycle with persistent state
    - Coordinate job execution with checkpoints
    - Enforce budget and spending limits
    - Maintain audit trail of all operations
    - Support resumption after failures
    """

    def __init__(
        self,
        vault_dir: str = "./job_vault",
        framework: str = "django",
        language: str = "python"
    ):
        self.vault_dir = vault_dir
        self.framework = framework
        self.language = language

        # Core components
        self.vault = JobVault(vault_dir)
        self.checkpoint_manager = CheckpointManager(vault_dir)
        self.budget_gate = BudgetGate(vault_dir)

        # Retry strategy
        self.retry_strategy = ExponentialBackoffStrategy(
            base_delay=5,
            max_retries=3,
            retriable_errors=["timeout", "temporary_failure", "resource_busy"]
        )

    def create_job(
        self,
        job_id: str,
        job_config: Dict[str, Any]
    ) -> str:
        """
        Create new job in vault.

        Args:
            job_id: unique job identifier
            job_config: job configuration (budget, timeouts, etc.)

        Returns: job directory path
        """
        print(f"[Orchestrator] Creating job: {job_id}")

        # Create vault entry
        job_dir = self.vault.create_job(
            job_id,
            job_config,
            self.framework,
            self.language
        )

        # Log creation
        self.vault.append_work_log(
            job_id,
            WorkLogEntry(
                timestamp=self._timestamp(),
                agent="orchestrator",
                action="create_job",
                result=f"Job created in {job_dir}",
            )
        )

        print(f"[Orchestrator] Job created: {job_dir}")
        return job_dir

    def resume_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Resume job from checkpoint.

        Returns: resumption context or None if no checkpoint exists
        """
        if not self.checkpoint_manager.can_resume(job_id):
            print(f"[Orchestrator] No checkpoint found for {job_id}")
            return None

        print(f"[Orchestrator] Resuming job from checkpoint: {job_id}")

        context = self.checkpoint_manager.get_resumption_context(job_id)

        self.vault.append_work_log(
            job_id,
            WorkLogEntry(
                timestamp=self._timestamp(),
                agent="orchestrator",
                action="resume_from_checkpoint",
                result=f"Resumed from checkpoint {context['checkpoint_id']}",
                checkpoint=context["state"],
            )
        )

        return context

    def execute_with_budget_check(
        self,
        job_id: str,
        operation: str,
        estimated_cost: float,
        executor_func,
        *args,
        **kwargs
    ) -> Tuple[bool, Any]:
        """
        Execute operation with budget enforcement.

        Args:
            job_id: job ID
            operation: operation name
            estimated_cost: estimated cost in dollars
            executor_func: function to execute
            args, kwargs: arguments for executor_func

        Returns: (success, result)
        """
        # Check budget
        decision, reason = self.budget_gate.check_operation_cost(
            job_id,
            operation,
            estimated_cost,
            approval_required_above=50.0
        )

        print(f"[Orchestrator] Budget check for {operation}: {decision.value}")
        print(f"  Reason: {reason}")

        if decision == BudgetDecision.DENIED:
            self.vault.append_work_log(
                job_id,
                WorkLogEntry(
                    timestamp=self._timestamp(),
                    agent="orchestrator",
                    action=operation,
                    result="DENIED",
                    error=f"Budget exceeded: {reason}",
                )
            )
            return False, None

        if decision == BudgetDecision.NEEDS_APPROVAL:
            # Record requirement for approval
            self.budget_gate.require_approval(
                job_id,
                operation,
                reason,
                approver="human"
            )
            print(f"[Orchestrator] Waiting for approval on {operation}")
            return False, {"status": "awaiting_approval", "reason": reason}

        if decision == BudgetDecision.PAUSED_BUDGET_LIMIT:
            self.budget_gate.set_pause_on_budget_limit(job_id)
            print(f"[Orchestrator] Job paused: budget limit reached")
            return False, {"status": "paused", "reason": reason}

        # Execute operation
        try:
            print(f"[Orchestrator] Executing {operation}...")
            result = executor_func(*args, **kwargs)

            # Record actual cost
            self.budget_gate.record_operation(
                job_id,
                operation,
                estimated_cost,
                f"Operation {operation} completed"
            )

            self.vault.append_work_log(
                job_id,
                WorkLogEntry(
                    timestamp=self._timestamp(),
                    agent="orchestrator",
                    action=operation,
                    result="SUCCESS",
                )
            )

            return True, result

        except Exception as e:
            error_msg = str(e)

            self.vault.append_work_log(
                job_id,
                WorkLogEntry(
                    timestamp=self._timestamp(),
                    agent="orchestrator",
                    action=operation,
                    result="FAILED",
                    error=error_msg,
                )
            )

            return False, {"status": "error", "error": error_msg}

    def create_checkpoint(
        self,
        job_id: str,
        state: Dict[str, Any]
    ) -> str:
        """
        Create resumable checkpoint.

        Returns: checkpoint filename
        """
        checkpoint_file = self.vault.create_checkpoint(job_id, state)

        self.vault.append_work_log(
            job_id,
            WorkLogEntry(
                timestamp=self._timestamp(),
                agent="orchestrator",
                action="create_checkpoint",
                result=f"Checkpoint created: {checkpoint_file}",
                checkpoint=state,
            )
        )

        print(f"[Orchestrator] Checkpoint created: {checkpoint_file}")
        return checkpoint_file

    def handle_failure(
        self,
        job_id: str,
        error: str,
        should_retry: bool = True
    ) -> Dict[str, Any]:
        """
        Handle job failure with retry decision.

        Returns: failure summary with retry info
        """
        manifest = self.vault.get_job_manifest(job_id)
        retry_count = manifest.get("retry_count", 0)

        # Determine if retriable
        can_retry = self.retry_strategy.should_retry(error, retry_count)

        if should_retry and can_retry:
            delay = self.retry_strategy.get_delay(retry_count)
            self.checkpoint_manager.mark_retry(job_id, error)

            summary = {
                "status": "will_retry",
                "retry_count": retry_count + 1,
                "delay_seconds": delay,
                "error": error,
            }

            self.vault.append_work_log(
                job_id,
                WorkLogEntry(
                    timestamp=self._timestamp(),
                    agent="orchestrator",
                    action="handle_failure",
                    result=f"Marked for retry (attempt {retry_count + 1})",
                    error=error,
                )
            )

            print(f"[Orchestrator] Job marked for retry: {job_id}")
            return summary

        else:
            # Terminal failure
            self.vault.update_job_status(
                job_id,
                JobStatus.FAILED,
                f"Terminal failure: {error}"
            )

            summary = self.checkpoint_manager.create_failure_summary(job_id)

            self.vault.append_work_log(
                job_id,
                WorkLogEntry(
                    timestamp=self._timestamp(),
                    agent="orchestrator",
                    action="handle_failure",
                    result="Terminal failure",
                    error=error,
                )
            )

            print(f"[Orchestrator] Job failed (terminal): {job_id}")
            return summary

    def record_decision(
        self,
        job_id: str,
        decision: str,
        rationale: str,
        alternatives: List[str],
        chosen: str,
        impact: str
    ):
        """
        Record strategic decision in vault.

        Enables transparency and auditability.
        """
        self.vault.record_decision(
            job_id,
            decision,
            rationale,
            alternatives,
            chosen,
            impact
        )

        print(f"[Orchestrator] Decision recorded: {decision}")

    def complete_job(self, job_id: str, result: Dict[str, Any]):
        """
        Mark job as completed and store result.

        Args:
            job_id: job ID
            result: job result to store
        """
        self.vault.update_job_status(job_id, JobStatus.COMPLETED)
        self.vault.store_result(job_id, "job_result", result)

        self.vault.append_work_log(
            job_id,
            WorkLogEntry(
                timestamp=self._timestamp(),
                agent="orchestrator",
                action="complete_job",
                result="Job completed",
            )
        )

        # Print summary
        summary = self.vault.get_job_summary(job_id)
        spending = self.budget_gate.get_job_spending_summary(job_id)

        print(f"\n[Orchestrator] Job completed: {job_id}")
        print(f"  Status: {summary['status']}")
        print(f"  Total cost: ${spending['total_spent']:.2f}")
        print(f"  Checkpoints: {summary['checkpoints']}")
        print(f"  Retries: {summary['retry_count']}")

    def get_job_audit_trail(self, job_id: str) -> Dict[str, Any]:
        """
        Get complete audit trail for job.

        Returns: audit summary with all logs and metadata
        """
        job_dir = Path(self.vault_dir) / "jobs" / f"job-{job_id}"

        return {
            "job_id": job_id,
            "summary": self.vault.get_job_summary(job_id),
            "spending": self.budget_gate.get_job_spending_summary(job_id),
            "manifest": self.vault.get_job_manifest(job_id),
            "work_log": self._read_file(job_dir / "work_log.md"),
            "decisions": self._read_file(job_dir / "decisions.md"),
        }

    def list_jobs(self) -> List[Dict[str, Any]]:
        """List all jobs with summaries"""
        jobs = self.vault.list_jobs()
        return [self.vault.get_job_summary(job_id) for job_id in jobs]

    # Private helpers
    def _timestamp(self) -> str:
        """Get ISO 8601 timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"

    def _read_file(self, path: Path) -> str:
        """Safely read file"""
        if not path.exists():
            return ""
        with open(path) as f:
            return f.read()


def create_enhanced_orchestrator(
    framework: str = "django",
    language: str = "python",
    vault_dir: str = "./job_vault"
) -> EnhancedOrchestrator:
    """Factory function for orchestrator"""
    return EnhancedOrchestrator(vault_dir, framework, language)
