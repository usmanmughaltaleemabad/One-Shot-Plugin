"""
Stage Curriculum — Phase 3-T4

Tracks per-stage metrics and statistics for the multi-stage workflow:
- Planning: cost estimation accuracy, feature detection accuracy
- Design: spec completeness, relationship correctness
- Implementation: code quality, test coverage, security issues
- Verify: patch success rate, fix accuracy
- Review: security findings, performance issues
- Ship: integration issues, wiring errors
- Critic: test failures, coverage gaps
- Record: graph accuracy, bead quality

Provides:
- record_stage_attempt(): Track stage execution with metrics
- get_stage_stats(): Query success rates and performance
- get_recovery_strategies(): Find recovery actions for stage failures
- recommend_stage_params(): Suggest optimized parameters
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger(__name__)


@dataclass
class StageMetrics:
    """Metrics for a single stage execution."""
    stage: str
    success: bool
    duration: float  # seconds
    cost: float  # USD
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    recovery_applied: Optional[str] = None
    extra_metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict."""
        return asdict(self)


@dataclass
class StageStats:
    """Aggregated statistics for a stage."""
    stage: str
    total_attempts: int
    success_count: int
    failure_count: int
    success_rate: float  # 0.0-1.0
    avg_duration: float  # seconds
    avg_cost: float  # USD
    common_errors: Dict[str, int]  # error_type -> count
    recovery_success_rate: Dict[str, float]  # recovery_type -> success_rate


@dataclass
class RecoveryStrategy:
    """Recovery strategy for a stage failure."""
    error_type: str
    recovery_action: str
    success_rate: float  # 0.0-1.0
    applicability: str  # "always", "conditional", "experimental"
    adjusted_params: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class StageCurriculum:
    """Tracks per-stage metrics and learning."""

    def __init__(self, store_path: Optional[Path] = None):
        """
        Initialize stage curriculum.

        Args:
            store_path: Path to JSONL file for stage metrics (default: .beads/stage_metrics.jsonl)
        """
        self.store_path = Path(store_path or ".beads/stage_metrics.jsonl")
        self.store_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing metrics
        self._metrics: List[StageMetrics] = self._load_metrics()

        # Stage definitions
        self.stages = [
            "planning",      # Stage 0
            "design",        # Stage 1-2
            "implement",     # Stage 3
            "verify",        # Stage 4
            "review",        # Stage 5
            "ship",          # Stage 6
            "critic",        # Stage 7
            "record",        # Stage 8
        ]

    def record_stage_attempt(
        self,
        stage: str,
        success: bool,
        duration: float,
        cost: float,
        error_type: Optional[str] = None,
        error_message: Optional[str] = None,
        recovery_applied: Optional[str] = None,
        extra_metrics: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Record a stage execution attempt.

        Args:
            stage: Stage name (e.g., "design", "verify")
            success: Whether the stage succeeded
            duration: Execution duration in seconds
            cost: Cost in USD
            error_type: Type of error if failed
            error_message: Full error message if failed
            recovery_applied: Recovery action applied if any
            extra_metrics: Additional metrics to record

        Returns:
            Metric ID (timestamp + stage)
        """
        metric = StageMetrics(
            stage=stage,
            success=success,
            duration=duration,
            cost=cost,
            error_type=error_type,
            error_message=error_message,
            recovery_applied=recovery_applied,
            extra_metrics=extra_metrics or {},
        )

        self._metrics.append(metric)
        self._save_metrics()

        metric_id = f"{metric.timestamp}:{stage}"
        logger.debug(f"Recorded stage attempt: {metric_id}")

        return metric_id

    def get_stage_stats(self, stage: str) -> Optional[StageStats]:
        """
        Get aggregated statistics for a stage.

        Args:
            stage: Stage name

        Returns:
            StageStats or None if no data available
        """
        stage_metrics = [m for m in self._metrics if m.stage == stage]
        if not stage_metrics:
            return None

        success_count = sum(1 for m in stage_metrics if m.success)
        failure_count = len(stage_metrics) - success_count
        total = len(stage_metrics)

        avg_duration = sum(m.duration for m in stage_metrics) / total
        avg_cost = sum(m.cost for m in stage_metrics) / total

        # Common errors
        common_errors: Dict[str, int] = {}
        for metric in stage_metrics:
            if metric.error_type:
                common_errors[metric.error_type] = common_errors.get(metric.error_type, 0) + 1

        # Recovery success rates
        recovery_success: Dict[str, Tuple[int, int]] = {}  # recovery -> (success, total)
        for metric in stage_metrics:
            if metric.recovery_applied:
                if metric.recovery_applied not in recovery_success:
                    recovery_success[metric.recovery_applied] = (0, 0)
                success_delta = 1 if metric.success else 0
                s, t = recovery_success[metric.recovery_applied]
                recovery_success[metric.recovery_applied] = (s + success_delta, t + 1)

        recovery_success_rate = {
            recovery: (s / t if t > 0 else 0.0)
            for recovery, (s, t) in recovery_success.items()
        }

        return StageStats(
            stage=stage,
            total_attempts=total,
            success_count=success_count,
            failure_count=failure_count,
            success_rate=success_count / total if total > 0 else 0.0,
            avg_duration=avg_duration,
            avg_cost=avg_cost,
            common_errors=common_errors,
            recovery_success_rate=recovery_success_rate,
        )

    def get_all_stage_stats(self) -> Dict[str, StageStats]:
        """Get statistics for all stages."""
        result = {}
        for stage in self.stages:
            stats = self.get_stage_stats(stage)
            if stats:
                result[stage] = stats
        return result

    def recommend_stage_params(
        self,
        stage: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Recommend optimized parameters for a stage based on history.

        Args:
            stage: Stage name
            context: Optional context (e.g., {"entity_count": 5, "complexity": "high"})

        Returns:
            Dictionary of recommended parameters
        """
        stats = self.get_stage_stats(stage)
        if not stats:
            return {}

        recommendations: Dict[str, Any] = {}

        # If success rate is low, recommend more retries
        if stats.success_rate < 0.7:
            recommendations["max_retries"] = 3
            recommendations["retry_strategy"] = "exponential_backoff"

        # If average cost is high, recommend parameter reduction
        if stats.avg_cost > 1.0:
            recommendations["reduce_entity_count"] = True
            recommendations["use_simplified_spec"] = True

        # Recommend recovery strategies for common errors
        if stats.common_errors:
            top_error = max(stats.common_errors.items(), key=lambda x: x[1])
            recommendations["likely_error"] = top_error[0]
            recommendations["prepare_recovery"] = True

        # If high duration, consider parallelization
        if stats.avg_duration > 60.0:  # > 1 minute
            recommendations["enable_parallelization"] = True

        return recommendations

    def get_recovery_strategies(
        self,
        stage: str,
        error_type: str,
        top_k: int = 3,
    ) -> List[RecoveryStrategy]:
        """
        Get recovery strategies for a stage failure.

        Args:
            stage: Stage name
            error_type: Error type
            top_k: Maximum strategies to return

        Returns:
            List of RecoveryStrategy objects
        """
        # Built-in recovery strategies
        strategies = self._get_builtin_strategies(stage, error_type)

        # Calculate success rates from history
        for strategy in strategies:
            success_rate = self._calculate_strategy_success_rate(
                stage, error_type, strategy.recovery_action
            )
            strategy.success_rate = success_rate

        # Sort by success rate
        strategies.sort(key=lambda s: s.success_rate, reverse=True)

        return strategies[:top_k]

    def _get_builtin_strategies(
        self, stage: str, error_type: str
    ) -> List[RecoveryStrategy]:
        """Get built-in recovery strategies for a stage and error type."""
        strategies: Dict[str, Dict[str, List[RecoveryStrategy]]] = {
            "design": {
                "relationship_validation_failed": [
                    RecoveryStrategy(
                        error_type="relationship_validation_failed",
                        recovery_action="add_explicit_fk_columns",
                        success_rate=0.85,
                        applicability="always",
                        adjusted_params={"add_fk_explicitly": True},
                        notes="Explicitly define FK columns instead of relying on inference",
                    ),
                    RecoveryStrategy(
                        error_type="relationship_validation_failed",
                        recovery_action="simplify_relationships",
                        success_rate=0.75,
                        applicability="conditional",
                        adjusted_params={"max_relationship_depth": 2},
                        notes="Reduce relationship nesting depth",
                    ),
                ],
                "spec_completeness_low": [
                    RecoveryStrategy(
                        error_type="spec_completeness_low",
                        recovery_action="expand_entity_definitions",
                        success_rate=0.80,
                        applicability="always",
                        adjusted_params={"min_fields_per_entity": 4},
                        notes="Add more fields to each entity",
                    ),
                ],
            },
            "implement": {
                "missing_imports": [
                    RecoveryStrategy(
                        error_type="missing_imports",
                        recovery_action="auto_add_imports",
                        success_rate=0.95,
                        applicability="always",
                        adjusted_params={"scan_for_missing_imports": True},
                        notes="Run import scanner before final generation",
                    ),
                ],
                "syntax_error": [
                    RecoveryStrategy(
                        error_type="syntax_error",
                        recovery_action="reduce_entity_count",
                        success_rate=0.80,
                        applicability="conditional",
                        adjusted_params={"max_entities": 3},
                        notes="Reduce number of entities for simpler code",
                    ),
                ],
            },
            "verify": {
                "patch_failed": [
                    RecoveryStrategy(
                        error_type="patch_failed",
                        recovery_action="regenerate_from_spec",
                        success_rate=0.85,
                        applicability="always",
                        notes="Regenerate implementation from spec instead of patching",
                    ),
                ],
            },
            "critic": {
                "test_failure": [
                    RecoveryStrategy(
                        error_type="test_failure",
                        recovery_action="reduce_entity_count",
                        success_rate=0.80,
                        applicability="conditional",
                        adjusted_params={"max_entities": 2},
                        notes="Fewer entities = simpler fixtures",
                    ),
                    RecoveryStrategy(
                        error_type="test_failure",
                        recovery_action="add_fixture_stubs",
                        success_rate=0.75,
                        applicability="always",
                        adjusted_params={"add_minimal_fixtures": True},
                        notes="Provide minimal fixture scaffolding",
                    ),
                ],
                "coverage_gap": [
                    RecoveryStrategy(
                        error_type="coverage_gap",
                        recovery_action="focus_on_core_logic",
                        success_rate=0.85,
                        applicability="always",
                        adjusted_params={"target_coverage": 70},
                        notes="Focus on core path coverage (70% is sufficient)",
                    ),
                ],
            },
            "ship": {
                "integration_error": [
                    RecoveryStrategy(
                        error_type="integration_error",
                        recovery_action="validate_wiring_dry_run",
                        success_rate=0.90,
                        applicability="always",
                        adjusted_params={"dry_run_wiring": True},
                        notes="Always dry-run before applying changes",
                    ),
                ],
            },
        }

        # Get stage strategies
        stage_strategies = strategies.get(stage, {})
        error_strategies = stage_strategies.get(error_type, [])

        # Always include a generic fallback
        if not error_strategies:
            error_strategies = [
                RecoveryStrategy(
                    error_type=error_type,
                    recovery_action="retry_with_reduced_complexity",
                    success_rate=0.60,
                    applicability="conditional",
                    adjusted_params={"reduce_complexity": True},
                    notes="Generic fallback: reduce complexity and retry",
                ),
            ]

        return error_strategies

    def _calculate_strategy_success_rate(
        self, stage: str, error_type: str, recovery_action: str
    ) -> float:
        """Calculate success rate for a recovery strategy from historical data."""
        matching_metrics = [
            m for m in self._metrics
            if m.stage == stage
            and m.error_type == error_type
            and m.recovery_applied == recovery_action
        ]

        if not matching_metrics:
            return 0.5  # Unknown recovery -> neutral confidence

        success_count = sum(1 for m in matching_metrics if m.success)
        return success_count / len(matching_metrics)

    def get_stage_history(
        self, stage: str, limit: int = 10
    ) -> List[StageMetrics]:
        """Get recent execution history for a stage."""
        stage_metrics = [m for m in self._metrics if m.stage == stage]
        return stage_metrics[-limit:]

    # Private helper methods

    def _load_metrics(self) -> List[StageMetrics]:
        """Load metrics from JSONL file."""
        metrics = []
        if self.store_path.exists():
            try:
                with open(self.store_path, "r") as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line)
                            metric = StageMetrics(
                                stage=data["stage"],
                                success=data["success"],
                                duration=data["duration"],
                                cost=data["cost"],
                                timestamp=data.get("timestamp"),
                                error_type=data.get("error_type"),
                                error_message=data.get("error_message"),
                                recovery_applied=data.get("recovery_applied"),
                                extra_metrics=data.get("extra_metrics", {}),
                            )
                            metrics.append(metric)
            except Exception as e:
                logger.warning(f"Error loading stage metrics: {e}")
        return metrics

    def _save_metrics(self) -> None:
        """Save metrics to JSONL file."""
        try:
            with open(self.store_path, "w") as f:
                for metric in self._metrics:
                    f.write(json.dumps(metric.to_dict()) + "\n")
        except Exception as e:
            logger.error(f"Error saving stage metrics: {e}")
