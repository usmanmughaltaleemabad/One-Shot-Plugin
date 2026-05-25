"""
Test Suite for Advanced Curriculum (Phase 3-T4)

Tests for:
- StageCurriculum: Per-stage metrics and learning
- WorkflowOrchestrator: Multi-stage workflow execution
- RecoveryStrategies: Failure patterns and recovery actions
- CurriculumV3: Integrated curriculum

20+ tests validating all components.
"""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".claude"))

from curriculum.stage_curriculum import (
    StageCurriculum,
    StageMetrics,
    StageStats,
)
from curriculum.workflow_orchestrator import (
    WorkflowOrchestrator,
    WorkflowResult,
    WorkflowStatus,
    StageStatus,
    StageResult,
)
from curriculum.recovery_strategies import RecoveryStrategies, RecoveryAction
from curriculum.curriculum_v3 import CurriculumV3


class TestStageCurriculum:
    """Tests for StageCurriculum."""

    def test_record_stage_attempt_success(self):
        """Test recording a successful stage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            curriculum = StageCurriculum(store_path=Path(tmpdir) / "stages.jsonl")
            metric_id = curriculum.record_stage_attempt(
                stage="design",
                success=True,
                duration=5.0,
                cost=0.1,
            )
            assert metric_id is not None
            assert "design" in metric_id

    def test_record_stage_attempt_failure(self):
        """Test recording a failed stage with error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            curriculum = StageCurriculum(store_path=Path(tmpdir) / "stages.jsonl")
            metric_id = curriculum.record_stage_attempt(
                stage="implement",
                success=False,
                duration=10.0,
                cost=0.2,
                error_type="missing_imports",
                error_message="NameError: name 'os' is not defined",
                recovery_applied="auto_add_imports",
            )
            assert metric_id is not None
            assert len(curriculum._metrics) == 1
            assert not curriculum._metrics[0].success
            assert curriculum._metrics[0].error_type == "missing_imports"

    def test_get_stage_stats_empty(self):
        """Test getting stats for stage with no data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            curriculum = StageCurriculum(store_path=Path(tmpdir) / "stages.jsonl")
            stats = curriculum.get_stage_stats("design")
            assert stats is None

    def test_get_stage_stats_with_data(self):
        """Test getting aggregated stats for a stage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            curriculum = StageCurriculum(store_path=Path(tmpdir) / "stages.jsonl")

            # Record multiple attempts
            curriculum.record_stage_attempt("design", True, 5.0, 0.1)
            curriculum.record_stage_attempt("design", True, 6.0, 0.11)
            curriculum.record_stage_attempt("design", False, 8.0, 0.12)

            stats = curriculum.get_stage_stats("design")
            assert stats is not None
            assert stats.success_count == 2
            assert stats.failure_count == 1
            assert stats.success_rate == 2 / 3
            assert stats.total_attempts == 3

    def test_recommend_stage_params_low_success_rate(self):
        """Test parameter recommendations for low success rate."""
        with tempfile.TemporaryDirectory() as tmpdir:
            curriculum = StageCurriculum(store_path=Path(tmpdir) / "stages.jsonl")

            # Record failing attempts
            for _ in range(7):
                curriculum.record_stage_attempt("design", False, 5.0, 0.1)
            for _ in range(3):
                curriculum.record_stage_attempt("design", True, 5.0, 0.1)

            params = curriculum.recommend_stage_params("design")
            assert "max_retries" in params
            assert params["max_retries"] == 3

    def test_get_recovery_strategies(self):
        """Test getting recovery strategies for a failure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            curriculum = StageCurriculum(store_path=Path(tmpdir) / "stages.jsonl")

            strategies = curriculum.get_recovery_strategies(
                "design",
                "relationship_validation_failed",
            )
            assert len(strategies) > 0
            assert strategies[0].recovery_action == "add_explicit_fk_columns"

    def test_get_all_stage_stats(self):
        """Test getting stats for all stages."""
        with tempfile.TemporaryDirectory() as tmpdir:
            curriculum = StageCurriculum(store_path=Path(tmpdir) / "stages.jsonl")

            curriculum.record_stage_attempt("design", True, 5.0, 0.1)
            curriculum.record_stage_attempt("implement", True, 10.0, 0.2)

            all_stats = curriculum.get_all_stage_stats()
            assert "design" in all_stats
            assert "implement" in all_stats

    def test_stage_history(self):
        """Test retrieving stage history."""
        with tempfile.TemporaryDirectory() as tmpdir:
            curriculum = StageCurriculum(store_path=Path(tmpdir) / "stages.jsonl")

            for i in range(15):
                curriculum.record_stage_attempt(
                    "design",
                    i % 2 == 0,
                    5.0 + i,
                    0.1 + i * 0.01,
                )

            history = curriculum.get_stage_history("design", limit=5)
            assert len(history) == 5


class TestWorkflowOrchestrator:
    """Tests for WorkflowOrchestrator."""

    def test_initialization(self):
        """Test orchestrator initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            orchestrator = WorkflowOrchestrator(
                store_path=Path(tmpdir) / "workflows.jsonl"
            )
            assert "standard" in orchestrator.workflow_paths
            assert "fast_track" in orchestrator.workflow_paths

    def test_execute_stage_success(self):
        """Test executing a successful stage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            orchestrator = WorkflowOrchestrator(
                store_path=Path(tmpdir) / "workflows.jsonl"
            )

            def dummy_executor(stage, context):
                return {"cost": 0.1, "artifacts": {}}

            result = orchestrator.execute_stage(
                "design",
                dummy_executor,
                context={},
            )
            assert result.status == StageStatus.SUCCESS
            assert result.stage == "design"

    def test_execute_stage_failure(self):
        """Test executing a failed stage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            orchestrator = WorkflowOrchestrator(
                store_path=Path(tmpdir) / "workflows.jsonl"
            )

            def failing_executor(stage, context):
                raise ValueError("Test error")

            result = orchestrator.execute_stage(
                "design",
                failing_executor,
                context={},
            )
            assert result.status == StageStatus.FAILED
            assert "Test error" in result.error

    def test_handle_stage_failure_missing_imports(self):
        """Test handling missing imports error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            orchestrator = WorkflowOrchestrator(
                store_path=Path(tmpdir) / "workflows.jsonl"
            )

            recovery = orchestrator.handle_stage_failure(
                stage="implement",
                error="NameError: name 'os' is not defined",
                attempt=0,
                context={},
            )
            assert recovery["should_retry"] is True
            assert recovery["recovery_action"] == "auto_add_imports"

    def test_handle_stage_failure_relationship_validation(self):
        """Test handling relationship validation error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            orchestrator = WorkflowOrchestrator(
                store_path=Path(tmpdir) / "workflows.jsonl"
            )

            recovery = orchestrator.handle_stage_failure(
                stage="design",
                error="FK validation error: relationship not found",
                attempt=0,
                context={},
            )
            assert recovery["should_retry"] is True
            assert recovery["recovery_action"] == "add_explicit_fk_columns"

    def test_execute_workflow_all_succeed(self):
        """Test executing workflow where all stages succeed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            orchestrator = WorkflowOrchestrator(
                store_path=Path(tmpdir) / "workflows.jsonl"
            )

            def dummy_executor(stage, context):
                return {"cost": 0.1, "artifacts": {}}

            result = orchestrator.execute_workflow(
                intent="create_shopping_cart",
                complexity="simple",
                workflow_path="fast_track",
                stage_executors={"planning": dummy_executor},
            )
            assert result.status == WorkflowStatus.SUCCESS
            assert result.intent == "create_shopping_cart"
            assert len(result.stage_results) > 0

    def test_workflow_result_serialization(self):
        """Test WorkflowResult serialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            orchestrator = WorkflowOrchestrator(
                store_path=Path(tmpdir) / "workflows.jsonl"
            )

            def dummy_executor(stage, context):
                return {"cost": 0.1}

            result = orchestrator.execute_workflow(
                intent="test_intent",
                complexity="simple",
                workflow_path="fast_track",
                stage_executors={"planning": dummy_executor},
            )

            # Serialize and deserialize
            result_dict = result.to_dict()
            assert result_dict["status"] == "success"
            assert result_dict["intent"] == "test_intent"

    def test_get_workflow_stats(self):
        """Test getting workflow statistics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            orchestrator = WorkflowOrchestrator(
                store_path=Path(tmpdir) / "workflows.jsonl"
            )

            def dummy_executor(stage, context):
                return {"cost": 0.1}

            # Execute a few workflows
            for i in range(3):
                orchestrator.execute_workflow(
                    intent=f"intent_{i}",
                    complexity="simple",
                    workflow_path="fast_track",
                    stage_executors={"planning": dummy_executor},
                )

            stats = orchestrator.get_workflow_stats()
            assert stats["total_workflows"] == 3

    def test_workflow_history(self):
        """Test retrieving workflow history."""
        with tempfile.TemporaryDirectory() as tmpdir:
            orchestrator = WorkflowOrchestrator(
                store_path=Path(tmpdir) / "workflows.jsonl"
            )

            def dummy_executor(stage, context):
                return {"cost": 0.1}

            # Execute workflows with same intent
            for i in range(5):
                orchestrator.execute_workflow(
                    intent="test_intent",
                    complexity="simple",
                    workflow_path="fast_track",
                    stage_executors={"planning": dummy_executor},
                )

            history = orchestrator.get_workflow_history(
                intent="test_intent", limit=3
            )
            assert len(history) == 3


class TestRecoveryStrategies:
    """Tests for RecoveryStrategies."""

    def test_get_patterns_for_stage(self):
        """Test getting patterns for a stage."""
        patterns = RecoveryStrategies.get_patterns_for_stage("design")
        assert len(patterns) > 0

    def test_find_pattern_exact_match(self):
        """Test finding pattern by exact error type."""
        pattern = RecoveryStrategies.find_pattern(
            "design",
            "relationship_validation_failed",
        )
        assert pattern is not None
        assert pattern.error_type == "relationship_validation_failed"

    def test_find_pattern_no_match(self):
        """Test finding pattern with no match."""
        pattern = RecoveryStrategies.find_pattern("design", "nonexistent_error")
        assert pattern is None

    def test_match_pattern_by_indicator(self):
        """Test matching pattern by error message indicator."""
        pattern = RecoveryStrategies.match_pattern_by_indicator(
            "implement",
            "NameError: name 'os' is not defined (import)",
        )
        assert pattern is not None
        assert pattern.error_type == "missing_imports"

    def test_suggest_recovery_exact_type(self):
        """Test suggesting recovery for known error type."""
        suggestion = RecoveryStrategies.suggest_recovery(
            stage="design",
            error_type="relationship_validation_failed",
        )
        assert suggestion is not None
        assert suggestion["recovery_action"] == "adjust_params"
        assert suggestion["adjusted_params"].get("add_fk_explicitly") is True

    def test_suggest_recovery_by_indicator(self):
        """Test suggesting recovery by matching error message."""
        suggestion = RecoveryStrategies.suggest_recovery(
            stage="implement",
            error_type="",
            error_message="SyntaxError: invalid syntax",
        )
        assert suggestion is not None
        assert suggestion["pattern"] == "syntax_error"

    def test_get_all_patterns(self):
        """Test getting all patterns."""
        all_patterns = RecoveryStrategies.get_all_patterns()
        assert len(all_patterns) >= 15  # At least 15 patterns

    def test_pattern_recovery_actions(self):
        """Test that patterns have valid recovery actions."""
        all_patterns = RecoveryStrategies.get_all_patterns()
        for pattern in all_patterns:
            assert isinstance(pattern.primary_action, RecoveryAction)
            assert pattern.success_rate > 0.5  # All should have reasonable success


class TestCurriculumV3:
    """Tests for CurriculumV3."""

    def test_initialization(self):
        """Test curriculum V3 initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stage_curric = StageCurriculum(
                store_path=Path(tmpdir) / "stages.jsonl"
            )
            orchestrator = WorkflowOrchestrator(
                store_path=Path(tmpdir) / "workflows.jsonl"
            )
            curriculum = CurriculumV3(
                stage_curriculum=stage_curric,
                workflow_orchestrator=orchestrator,
            )
            assert curriculum is not None

    def test_get_recommended_workflow_simple(self):
        """Test workflow recommendation for simple intent."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stage_curric = StageCurriculum(
                store_path=Path(tmpdir) / "stages.jsonl"
            )
            orchestrator = WorkflowOrchestrator(
                store_path=Path(tmpdir) / "workflows.jsonl"
            )
            curriculum = CurriculumV3(
                stage_curriculum=stage_curric,
                workflow_orchestrator=orchestrator,
            )

            rec = curriculum.get_recommended_workflow(
                intent="simple_feature",
                complexity="simple",
                risk_level="low",
            )
            assert rec["workflow_path"] == "fast_track"

    def test_get_recommended_workflow_complex(self):
        """Test workflow recommendation for complex intent."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stage_curric = StageCurriculum(
                store_path=Path(tmpdir) / "stages.jsonl"
            )
            orchestrator = WorkflowOrchestrator(
                store_path=Path(tmpdir) / "workflows.jsonl"
            )
            curriculum = CurriculumV3(
                stage_curriculum=stage_curric,
                workflow_orchestrator=orchestrator,
            )

            rec = curriculum.get_recommended_workflow(
                intent="complex_feature",
                complexity="complex",
                risk_level="high",
            )
            assert rec["workflow_path"] == "standard"

    def test_get_estimated_cost_and_duration(self):
        """Test cost and duration estimation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stage_curric = StageCurriculum(
                store_path=Path(tmpdir) / "stages.jsonl"
            )
            orchestrator = WorkflowOrchestrator(
                store_path=Path(tmpdir) / "workflows.jsonl"
            )
            curriculum = CurriculumV3(
                stage_curriculum=stage_curric,
                workflow_orchestrator=orchestrator,
            )

            cost, duration = curriculum.get_estimated_cost_and_duration(
                intent="test",
                complexity="simple",
            )
            assert cost > 0
            assert duration > 0

    def test_get_risk_mitigations_low_risk(self):
        """Test risk mitigations for low risk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stage_curric = StageCurriculum(
                store_path=Path(tmpdir) / "stages.jsonl"
            )
            orchestrator = WorkflowOrchestrator(
                store_path=Path(tmpdir) / "workflows.jsonl"
            )
            curriculum = CurriculumV3(
                stage_curriculum=stage_curric,
                workflow_orchestrator=orchestrator,
            )

            mitigations = curriculum.get_risk_mitigations(
                intent="test", risk_level="low"
            )
            # Low risk should have minimal mitigations
            assert isinstance(mitigations, list)

    def test_get_risk_mitigations_high_risk(self):
        """Test risk mitigations for high risk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stage_curric = StageCurriculum(
                store_path=Path(tmpdir) / "stages.jsonl"
            )
            orchestrator = WorkflowOrchestrator(
                store_path=Path(tmpdir) / "workflows.jsonl"
            )
            curriculum = CurriculumV3(
                stage_curriculum=stage_curric,
                workflow_orchestrator=orchestrator,
            )

            mitigations = curriculum.get_risk_mitigations(
                intent="test", risk_level="high"
            )
            # High risk should have multiple mitigations
            assert len(mitigations) > 2

    def test_get_curriculum_insights(self):
        """Test getting comprehensive curriculum insights."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stage_curric = StageCurriculum(
                store_path=Path(tmpdir) / "stages.jsonl"
            )
            orchestrator = WorkflowOrchestrator(
                store_path=Path(tmpdir) / "workflows.jsonl"
            )

            # Record some data
            stage_curric.record_stage_attempt(
                "design", True, 5.0, 0.1
            )
            stage_curric.record_stage_attempt(
                "implement", True, 10.0, 0.2
            )

            curriculum = CurriculumV3(
                stage_curriculum=stage_curric,
                workflow_orchestrator=orchestrator,
            )

            insights = curriculum.get_curriculum_insights()
            assert "stage_stats" in insights
            assert "workflow_stats" in insights
            assert "recovery_effectiveness" in insights

    def test_execute_with_curriculum(self):
        """Test executing generation with curriculum guidance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stage_curric = StageCurriculum(
                store_path=Path(tmpdir) / "stages.jsonl"
            )
            orchestrator = WorkflowOrchestrator(
                store_path=Path(tmpdir) / "workflows.jsonl"
            )
            curriculum = CurriculumV3(
                stage_curriculum=stage_curric,
                workflow_orchestrator=orchestrator,
            )

            def dummy_executor(stage, context):
                return {"cost": 0.1, "artifacts": {}}

            result = curriculum.execute_with_curriculum(
                intent="test_intent",
                complexity="simple",
                stage_executors={"planning": dummy_executor},
            )
            assert result.status == WorkflowStatus.SUCCESS
            assert len(curriculum.stage_curriculum._metrics) > 0


class TestIntegration:
    """Integration tests across components."""

    def test_end_to_end_workflow_with_recovery(self):
        """Test end-to-end workflow with recovery."""
        with tempfile.TemporaryDirectory() as tmpdir:
            stage_curric = StageCurriculum(
                store_path=Path(tmpdir) / "stages.jsonl"
            )
            orchestrator = WorkflowOrchestrator(
                store_path=Path(tmpdir) / "workflows.jsonl"
            )
            curriculum = CurriculumV3(
                stage_curriculum=stage_curric,
                workflow_orchestrator=orchestrator,
            )

            # Execute workflow
            def dummy_executor(stage, context):
                return {"cost": 0.1, "artifacts": {}}

            result = curriculum.execute_with_curriculum(
                intent="shopping_cart",
                complexity="moderate",
                stage_executors={"planning": dummy_executor},
            )

            # Verify recording
            assert result.status == WorkflowStatus.SUCCESS
            stats = stage_curric.get_all_stage_stats()
            assert len(stats) > 0

    def test_curriculum_learning_from_multiple_generations(self):
        """Test curriculum learning improves over multiple generations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            curriculum = CurriculumV3(
                stage_curriculum=StageCurriculum(
                    store_path=Path(tmpdir) / "stages.jsonl"
                ),
                workflow_orchestrator=WorkflowOrchestrator(
                    store_path=Path(tmpdir) / "workflows.jsonl"
                ),
            )

            # Simulate multiple generations
            for i in range(5):
                curriculum.stage_curriculum.record_stage_attempt(
                    stage="design",
                    success=i >= 2,  # Improve after 2 failures
                    duration=5.0 - i * 0.5,
                    cost=0.15 - i * 0.01,
                )

            stats = curriculum.stage_curriculum.get_stage_stats("design")
            assert stats is not None
            assert stats.success_rate == 0.6  # 3 successes out of 5

    def test_recovery_effectiveness_tracking(self):
        """Test tracking recovery effectiveness."""
        with tempfile.TemporaryDirectory() as tmpdir:
            curriculum = CurriculumV3(
                stage_curriculum=StageCurriculum(
                    store_path=Path(tmpdir) / "stages.jsonl"
                ),
                workflow_orchestrator=WorkflowOrchestrator(
                    store_path=Path(tmpdir) / "workflows.jsonl"
                ),
            )

            # Record failures with recovery
            for i in range(5):
                curriculum.stage_curriculum.record_stage_attempt(
                    stage="implement",
                    success=i % 2 == 0,
                    duration=10.0,
                    cost=0.2,
                    error_type="missing_imports",
                    error_message="Import error",
                    recovery_applied="auto_add_imports",
                )

            stats = curriculum.stage_curriculum.get_stage_stats("implement")
            assert stats is not None
            assert "auto_add_imports" in stats.recovery_success_rate
