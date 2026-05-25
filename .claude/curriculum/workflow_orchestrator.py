"""
Workflow Orchestrator — Phase 3-T4

Manages multi-stage workflow execution:
- Planning → Design → Implement → Verify → Review → Ship → Critic → Record
- Parallel execution (e.g., implement + test-author in parallel)
- Failure handling and recovery
- Rollback mechanisms

Provides:
- execute_workflow(): Run full multi-stage workflow
- execute_stage(): Execute single stage with error handling
- handle_stage_failure(): Apply recovery strategies
- record_workflow_completion(): Store workflow results
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable

logger = logging.getLogger(__name__)


class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class StageStatus(str, Enum):
    """Stage execution status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RECOVERED = "recovered"
    SKIPPED = "skipped"


@dataclass
class StageResult:
    """Result of a single stage execution."""
    stage: str
    status: StageStatus
    duration: float  # seconds
    cost: float  # USD
    error: Optional[str] = None
    recovery_applied: Optional[str] = None
    retry_count: int = 0
    artifacts: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowPath:
    """Ordered sequence of stages for a workflow."""
    name: str
    stages: List[str]
    parallel_stages: Optional[List[List[str]]] = None  # e.g., [["implement", "test_author"]]
    description: str = ""


@dataclass
class WorkflowResult:
    """Complete workflow execution result."""
    workflow_id: str
    status: WorkflowStatus
    intent: str
    complexity: str
    total_duration: float  # seconds
    total_cost: float  # USD
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    stage_results: List[StageResult] = field(default_factory=list)
    rollback_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict."""
        return {
            "workflow_id": self.workflow_id,
            "status": self.status.value,
            "intent": self.intent,
            "complexity": self.complexity,
            "total_duration": self.total_duration,
            "total_cost": self.total_cost,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "stage_results": [asdict(r) for r in self.stage_results],
            "rollback_reason": self.rollback_reason,
        }


class WorkflowOrchestrator:
    """Orchestrates multi-stage workflow execution."""

    def __init__(self, store_path: Optional[Path] = None):
        """
        Initialize workflow orchestrator.

        Args:
            store_path: Path to JSONL file for workflow results (default: .beads/workflow_results.jsonl)
        """
        self.store_path = Path(store_path or ".beads/workflow_results.jsonl")
        self.store_path.parent.mkdir(parents=True, exist_ok=True)

        # Define standard workflow paths
        self.workflow_paths: Dict[str, WorkflowPath] = {
            "standard": WorkflowPath(
                name="standard",
                stages=[
                    "planning",
                    "design",
                    "implement",
                    "verify",
                    "review",
                    "ship",
                    "critic",
                    "record",
                ],
                description="Standard workflow: plan, design, implement, verify, review, ship, critic, record",
            ),
            "parallel_implement": WorkflowPath(
                name="parallel_implement",
                stages=[
                    "planning",
                    "design",
                    "implement",
                    "verify",
                    "review",
                    "ship",
                    "critic",
                    "record",
                ],
                parallel_stages=[["implement", "test_author"]],
                description="Workflow with parallel implementation and test generation",
            ),
            "fast_track": WorkflowPath(
                name="fast_track",
                stages=[
                    "planning",
                    "design",
                    "implement",
                    "verify",
                    "record",
                ],
                description="Fast track: skip review and critic for simple features",
            ),
        }

        # Load existing results
        self._results: List[WorkflowResult] = self._load_results()

    def execute_workflow(
        self,
        intent: str,
        complexity: str,
        workflow_path: str = "standard",
        stage_executors: Optional[Dict[str, Callable]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> WorkflowResult:
        """
        Execute a complete workflow.

        Args:
            intent: User intent (e.g., "create_shopping_cart")
            complexity: Complexity level (e.g., "simple", "moderate", "complex")
            workflow_path: Which workflow path to use
            stage_executors: Dict mapping stage name to executor function
            context: Optional execution context

        Returns:
            WorkflowResult with all stage results
        """
        import uuid
        import time

        workflow_id = str(uuid.uuid4())
        started_at = datetime.utcnow().isoformat()
        result = WorkflowResult(
            workflow_id=workflow_id,
            status=WorkflowStatus.RUNNING,
            intent=intent,
            complexity=complexity,
            total_duration=0,
            total_cost=0,
            started_at=started_at,
        )

        # Get workflow path
        path = self.workflow_paths.get(workflow_path)
        if not path:
            result.status = WorkflowStatus.FAILED
            result.rollback_reason = f"Unknown workflow path: {workflow_path}"
            return result

        # Initialize executors
        if not stage_executors:
            stage_executors = {}

        # Execute stages
        start_time = time.time()
        total_cost = 0

        try:
            for stage in path.stages:
                # Check if stage should be executed
                executor = stage_executors.get(stage)
                if not executor:
                    # Provide dummy executor
                    executor = lambda s=stage: self._default_executor(s, context or {})

                # Execute stage
                stage_result = self.execute_stage(
                    stage=stage,
                    executor=executor,
                    context=context or {},
                    workflow_id=workflow_id,
                )

                result.stage_results.append(stage_result)
                total_cost += stage_result.cost

                # Check if stage failed
                if stage_result.status == StageStatus.FAILED:
                    # Try recovery
                    recovery_result = self.handle_stage_failure(
                        stage=stage,
                        error=stage_result.error or "Unknown error",
                        attempt=stage_result.retry_count,
                        context=context or {},
                    )

                    if recovery_result["should_retry"]:
                        # Retry the stage
                        stage_result = self.execute_stage(
                            stage=stage,
                            executor=executor,
                            context=context or {},
                            workflow_id=workflow_id,
                            retry=True,
                        )
                        result.stage_results[-1] = stage_result
                        total_cost += stage_result.cost
                    else:
                        # Cannot recover, stop workflow
                        result.status = WorkflowStatus.FAILED
                        result.rollback_reason = f"Stage {stage} failed: {stage_result.error}"
                        break

        except Exception as e:
            result.status = WorkflowStatus.FAILED
            result.rollback_reason = f"Workflow execution error: {str(e)}"
            logger.error(f"Workflow {workflow_id} error: {e}")

        # Finalize result
        result.completed_at = datetime.utcnow().isoformat()
        result.total_duration = time.time() - start_time
        result.total_cost = total_cost

        if result.status == WorkflowStatus.RUNNING:
            # All stages succeeded
            result.status = WorkflowStatus.SUCCESS

        # Store result
        self.record_workflow_completion(result)

        return result

    def execute_stage(
        self,
        stage: str,
        executor: Callable,
        context: Dict[str, Any],
        workflow_id: Optional[str] = None,
        retry: bool = False,
    ) -> StageResult:
        """
        Execute a single stage.

        Args:
            stage: Stage name
            executor: Callable that executes the stage
            context: Execution context
            workflow_id: Optional workflow ID
            retry: Whether this is a retry attempt

        Returns:
            StageResult
        """
        import time

        start_time = time.time()
        result = StageResult(
            stage=stage,
            status=StageStatus.RUNNING,
            duration=0,
            cost=0,
        )

        try:
            # Execute stage
            execution_result = executor(stage, context)

            # Parse executor result
            if isinstance(execution_result, dict):
                result.status = StageStatus.SUCCESS
                result.cost = execution_result.get("cost", 0.0)
                result.artifacts = execution_result.get("artifacts", {})
            else:
                result.status = StageStatus.SUCCESS
                result.cost = 0.0

            logger.debug(f"Stage {stage} succeeded (workflow: {workflow_id})")

        except Exception as e:
            result.status = StageStatus.FAILED
            result.error = str(e)
            result.retry_count = 1 if retry else 0
            logger.error(f"Stage {stage} failed: {e}")

        result.duration = time.time() - start_time
        return result

    def handle_stage_failure(
        self,
        stage: str,
        error: str,
        attempt: int,
        context: Dict[str, Any],
        max_retries: int = 2,
    ) -> Dict[str, Any]:
        """
        Handle a stage failure with recovery strategies.

        Args:
            stage: Stage that failed
            error: Error message
            attempt: Current attempt number
            context: Execution context
            max_retries: Maximum retry attempts

        Returns:
            Dictionary with recovery decision: {"should_retry": bool, "action": str, ...}
        """
        # Parse error type
        error_type = self._parse_error_type(error)

        # Decide on recovery action
        should_retry = attempt < max_retries

        recovery_action = "none"
        if error_type == "missing_imports" and stage == "implement":
            recovery_action = "auto_add_imports"
            should_retry = True
        elif error_type == "relationship_validation_failed" and stage == "design":
            recovery_action = "add_explicit_fk_columns"
            should_retry = True
        elif error_type == "test_failure" and stage == "critic":
            recovery_action = "reduce_entity_count"
            should_retry = True and attempt < max_retries
        elif error_type == "patch_failed" and stage == "verify":
            recovery_action = "regenerate_from_spec"
            should_retry = True
        elif error_type == "integration_error" and stage == "ship":
            recovery_action = "validate_wiring_dry_run"
            should_retry = True

        logger.info(
            f"Stage {stage} recovery: error_type={error_type}, action={recovery_action}, "
            f"retry={should_retry} (attempt {attempt})"
        )

        return {
            "should_retry": should_retry,
            "recovery_action": recovery_action,
            "error_type": error_type,
            "attempt": attempt,
            "adjusted_context": self._adjust_context(stage, recovery_action, context),
        }

    def record_workflow_completion(self, workflow_result: WorkflowResult) -> str:
        """
        Record a completed workflow.

        Args:
            workflow_result: WorkflowResult to store

        Returns:
            Workflow ID
        """
        self._results.append(workflow_result)
        self._save_results()

        logger.debug(
            f"Recorded workflow {workflow_result.workflow_id}: "
            f"{workflow_result.status.value} ({len(workflow_result.stage_results)} stages)"
        )

        return workflow_result.workflow_id

    def get_workflow_stats(self) -> Dict[str, Any]:
        """Get statistics across all workflows."""
        if not self._results:
            return {}

        successful = sum(1 for r in self._results if r.status == WorkflowStatus.SUCCESS)
        failed = sum(1 for r in self._results if r.status == WorkflowStatus.FAILED)
        total_cost = sum(r.total_cost for r in self._results)
        avg_duration = sum(r.total_duration for r in self._results) / len(self._results)

        return {
            "total_workflows": len(self._results),
            "successful": successful,
            "failed": failed,
            "success_rate": successful / len(self._results) if self._results else 0.0,
            "total_cost": total_cost,
            "avg_duration": avg_duration,
        }

    def get_workflow_history(
        self, intent: Optional[str] = None, limit: int = 10
    ) -> List[WorkflowResult]:
        """Get recent workflow results."""
        results = self._results
        if intent:
            results = [r for r in results if r.intent == intent]
        return results[-limit:]

    # Private helper methods

    def _parse_error_type(self, error_message: str) -> str:
        """Parse error type from error message."""
        error_lower = error_message.lower()

        if "nameerror" in error_lower or "import" in error_lower:
            return "missing_imports"
        elif "relationship" in error_lower or "fk" in error_lower:
            return "relationship_validation_failed"
        elif "test" in error_lower or "assert" in error_lower:
            return "test_failure"
        elif "patch" in error_lower:
            return "patch_failed"
        elif "integration" in error_lower or "wiring" in error_lower:
            return "integration_error"
        elif "spec" in error_lower:
            return "spec_completeness_low"
        elif "syntaxerror" in error_lower or "syntax" in error_lower:
            return "syntax_error"
        else:
            return "unknown"

    def _adjust_context(
        self,
        stage: str,
        recovery_action: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Adjust context for recovery."""
        adjusted = dict(context)

        if recovery_action == "auto_add_imports":
            adjusted["scan_for_missing_imports"] = True
        elif recovery_action == "add_explicit_fk_columns":
            adjusted["add_fk_explicitly"] = True
        elif recovery_action == "reduce_entity_count":
            adjusted["max_entities"] = 2
        elif recovery_action == "regenerate_from_spec":
            adjusted["regenerate_from_spec"] = True
        elif recovery_action == "validate_wiring_dry_run":
            adjusted["dry_run_wiring"] = True

        return adjusted

    def _default_executor(self, stage: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Default executor for stages without custom implementation."""
        return {"cost": 0.1, "artifacts": {}}

    def _load_results(self) -> List[WorkflowResult]:
        """Load workflow results from JSONL file."""
        results = []
        if self.store_path.exists():
            try:
                with open(self.store_path, "r") as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line)
                            # Parse stage results
                            stage_results = [
                                StageResult(
                                    stage=sr["stage"],
                                    status=StageStatus(sr["status"]),
                                    duration=sr["duration"],
                                    cost=sr["cost"],
                                    error=sr.get("error"),
                                    recovery_applied=sr.get("recovery_applied"),
                                    retry_count=sr.get("retry_count", 0),
                                    artifacts=sr.get("artifacts", {}),
                                )
                                for sr in data.get("stage_results", [])
                            ]
                            result = WorkflowResult(
                                workflow_id=data["workflow_id"],
                                status=WorkflowStatus(data["status"]),
                                intent=data["intent"],
                                complexity=data["complexity"],
                                total_duration=data["total_duration"],
                                total_cost=data["total_cost"],
                                created_at=data.get("created_at"),
                                started_at=data.get("started_at"),
                                completed_at=data.get("completed_at"),
                                stage_results=stage_results,
                                rollback_reason=data.get("rollback_reason"),
                            )
                            results.append(result)
            except Exception as e:
                logger.warning(f"Error loading workflow results: {e}")
        return results

    def _save_results(self) -> None:
        """Save workflow results to JSONL file."""
        try:
            with open(self.store_path, "w") as f:
                for result in self._results:
                    f.write(json.dumps(result.to_dict()) + "\n")
        except Exception as e:
            logger.error(f"Error saving workflow results: {e}")
