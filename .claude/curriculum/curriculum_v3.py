"""
Curriculum V3 — Phase 3-T4

Advanced curriculum integrating:
- KnowledgeStore (semantic search over past generations)
- StageCurriculum (per-stage metrics and learning)
- WorkflowOrchestrator (multi-stage workflow execution)
- IntentRouter (intent-based routing)
- RecoveryStrategies (failure pattern library)

Provides:
- get_recommended_workflow(): Suggest optimal workflow for intent+complexity
- get_estimated_cost_and_duration(): Predict cost and time
- get_risk_mitigations(): Suggest mitigations for identified risks
- execute_with_curriculum(): Run generation with curriculum-guided optimization
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

try:
    from .stage_curriculum import StageCurriculum, StageStats
    from .workflow_orchestrator import (
        WorkflowOrchestrator,
        WorkflowResult,
        WorkflowPath,
    )
    from .recovery_strategies import RecoveryStrategies, FailurePattern
except ImportError:
    # Fallback for direct imports
    from stage_curriculum import StageCurriculum, StageStats
    from workflow_orchestrator import (
        WorkflowOrchestrator,
        WorkflowResult,
        WorkflowPath,
    )
    from recovery_strategies import RecoveryStrategies, FailurePattern

logger = logging.getLogger(__name__)


class CurriculumV3:
    """Advanced curriculum for multi-stage workflow optimization."""

    def __init__(
        self,
        stage_curriculum: Optional[StageCurriculum] = None,
        workflow_orchestrator: Optional[WorkflowOrchestrator] = None,
    ):
        """
        Initialize curriculum V3.

        Args:
            stage_curriculum: Optional StageCurriculum instance
            workflow_orchestrator: Optional WorkflowOrchestrator instance
        """
        self.stage_curriculum = stage_curriculum or StageCurriculum()
        self.workflow_orchestrator = workflow_orchestrator or WorkflowOrchestrator()
        self.recovery_strategies = RecoveryStrategies()

    def get_recommended_workflow(
        self,
        intent: str,
        complexity: str,
        risk_level: str = "medium",
    ) -> Dict[str, Any]:
        """
        Recommend optimal workflow path for intent and complexity.

        Args:
            intent: User intent (e.g., "create_shopping_cart")
            complexity: Complexity level ("simple", "moderate", "complex")
            risk_level: Risk level ("low", "medium", "high")

        Returns:
            Recommendation dict with workflow_path, rationale, and parameters
        """
        # Select workflow path based on complexity and risk
        if complexity == "simple" and risk_level == "low":
            workflow_path = "fast_track"
            rationale = "Simple feature with low risk: use fast track (skip review/critic)"
        elif "implement" in intent and "test" in intent:
            workflow_path = "parallel_implement"
            rationale = "Implementation + testing: use parallel path"
        else:
            workflow_path = "standard"
            rationale = "Standard workflow for all stages"

        # Get historical stats for this intent
        similar_workflows = self.workflow_orchestrator.get_workflow_history(
            intent=intent, limit=5
        )

        # Estimate cost and duration
        cost_estimate, duration_estimate = self.get_estimated_cost_and_duration(
            intent, complexity
        )

        return {
            "workflow_path": workflow_path,
            "rationale": rationale,
            "estimated_cost_usd": cost_estimate,
            "estimated_duration_minutes": duration_estimate,
            "similar_past_workflows": len(similar_workflows),
            "recommended_parameters": self._recommend_parameters(intent, complexity),
            "risk_mitigations": self.get_risk_mitigations(intent, risk_level),
        }

    def get_estimated_cost_and_duration(
        self,
        intent: str,
        complexity: str,
    ) -> Tuple[float, float]:
        """
        Estimate cost and duration for a generation.

        Args:
            intent: User intent
            complexity: Complexity level

        Returns:
            (estimated_cost_usd, estimated_duration_minutes)
        """
        # Base estimates by complexity
        complexity_multipliers = {
            "simple": (0.2, 2),      # cost, duration (minutes)
            "moderate": (0.5, 5),
            "complex": (1.0, 10),
        }

        base_cost, base_duration = complexity_multipliers.get(
            complexity, (0.5, 5)
        )

        # Adjust based on historical data
        similar_workflows = self.workflow_orchestrator.get_workflow_history(
            intent=intent, limit=10
        )

        if similar_workflows:
            avg_cost = sum(w.total_cost for w in similar_workflows) / len(
                similar_workflows
            )
            avg_duration = sum(w.total_duration for w in similar_workflows) / len(
                similar_workflows
            )
            # Weight historical data with base estimates
            estimated_cost = (avg_cost * 0.7) + (base_cost * 0.3)
            estimated_duration = (avg_duration * 0.7) + (base_duration * 0.3)
        else:
            estimated_cost = base_cost
            estimated_duration = base_duration / 60  # Convert to minutes

        return estimated_cost, estimated_duration

    def get_risk_mitigations(
        self,
        intent: str,
        risk_level: str,
    ) -> List[Dict[str, Any]]:
        """
        Get risk mitigations for identified risks.

        Args:
            intent: User intent
            risk_level: Risk level ("low", "medium", "high")

        Returns:
            List of mitigation recommendations
        """
        mitigations: List[Dict[str, Any]] = []

        # Risk mitigations based on risk level
        if risk_level in ["medium", "high"]:
            # Check for common failure patterns
            all_patterns = self.recovery_strategies.get_all_patterns()
            high_risk_patterns = [
                p for p in all_patterns
                if p.stage in ["design", "implement", "critic"]
            ]

            for pattern in high_risk_patterns[:3]:  # Top 3 patterns
                mitigations.append(
                    {
                        "stage": pattern.stage,
                        "pattern": pattern.error_type,
                        "mitigation": f"Be prepared for: {pattern.root_cause}",
                        "recovery_action": pattern.primary_action.value,
                        "expected_success_rate": pattern.success_rate,
                    }
                )

        if risk_level == "high":
            # Add extra validation and review checkpoints
            mitigations.extend(
                [
                    {
                        "stage": "design",
                        "pattern": "spec_validation",
                        "mitigation": "Perform extra validation of spec before implementation",
                        "recovery_action": "validate_spec",
                    },
                    {
                        "stage": "critic",
                        "pattern": "extended_testing",
                        "mitigation": "Run extended test suite with high coverage targets",
                        "recovery_action": "increase_test_coverage",
                        "target_coverage": 85,
                    },
                ]
            )

        return mitigations

    def execute_with_curriculum(
        self,
        intent: str,
        complexity: str,
        stage_executors: Optional[Dict[str, callable]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> WorkflowResult:
        """
        Execute generation with curriculum-guided optimization.

        Args:
            intent: User intent
            complexity: Complexity level
            stage_executors: Optional custom stage executors
            context: Optional execution context

        Returns:
            WorkflowResult from orchestrator
        """
        # Get recommended workflow
        recommendation = self.get_recommended_workflow(intent, complexity)
        workflow_path = recommendation["workflow_path"]

        # Merge recommended parameters with context
        execution_context = dict(context or {})
        execution_context.update(recommendation.get("recommended_parameters", {}))

        # Execute workflow
        result = self.workflow_orchestrator.execute_workflow(
            intent=intent,
            complexity=complexity,
            workflow_path=workflow_path,
            stage_executors=stage_executors,
            context=execution_context,
        )

        # Record stage metrics
        for stage_result in result.stage_results:
            self.stage_curriculum.record_stage_attempt(
                stage=stage_result.stage,
                success=(stage_result.status.value == "success"),
                duration=stage_result.duration,
                cost=stage_result.cost,
                error_type=None,
                error_message=stage_result.error,
                recovery_applied=stage_result.recovery_applied,
            )

        return result

    def get_curriculum_insights(self) -> Dict[str, Any]:
        """Get comprehensive curriculum insights."""
        insights: Dict[str, Any] = {
            "stage_stats": {},
            "workflow_stats": {},
            "recovery_effectiveness": {},
            "recommendations": {},
        }

        # Collect stage statistics
        all_stats = self.stage_curriculum.get_all_stage_stats()
        for stage, stats in all_stats.items():
            insights["stage_stats"][stage] = {
                "success_rate": stats.success_rate,
                "avg_cost": stats.avg_cost,
                "avg_duration": stats.avg_duration,
                "common_errors": stats.common_errors,
            }

        # Workflow statistics
        workflow_stats = self.workflow_orchestrator.get_workflow_stats()
        insights["workflow_stats"] = workflow_stats

        # Recovery effectiveness
        for stage, stats in all_stats.items():
            if stats.recovery_success_rate:
                insights["recovery_effectiveness"][stage] = (
                    stats.recovery_success_rate
                )

        # Generate recommendations for low-performing stages
        for stage, stats in all_stats.items():
            if stats.success_rate < 0.7:
                insights["recommendations"][stage] = (
                    f"Stage {stage} has low success rate ({stats.success_rate:.1%}). "
                    f"Consider: {self.stage_curriculum.recommend_stage_params(stage)}"
                )

        return insights

    # Private helper methods

    def _recommend_parameters(
        self, intent: str, complexity: str
    ) -> Dict[str, Any]:
        """Recommend parameters based on intent and complexity."""
        params: Dict[str, Any] = {}

        if complexity == "simple":
            params["max_entities"] = 3
            params["skip_advanced_features"] = True
        elif complexity == "moderate":
            params["max_entities"] = 5
            params["add_indexes"] = True
        elif complexity == "complex":
            params["max_entities"] = 8
            params["add_caching"] = True
            params["enable_parallelization"] = True

        # Adjust based on stage stats
        stats_by_stage = self.stage_curriculum.get_all_stage_stats()
        for stage, stats in stats_by_stage.items():
            if stats.success_rate < 0.7:
                stage_params = self.stage_curriculum.recommend_stage_params(stage)
                params.update(stage_params)

        return params
