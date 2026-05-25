"""
Advanced Curriculum Package — Phase 3-T4

Components:
- StageCurriculum: Per-stage metrics and learning
- WorkflowOrchestrator: Multi-stage workflow execution
- RecoveryStrategies: Failure patterns and recovery actions
- CurriculumV3: Integrated advanced curriculum

Public API:
    from .curriculum import (
        StageCurriculum,
        StageMetrics,
        StageStats,
        WorkflowOrchestrator,
        WorkflowResult,
        WorkflowPath,
        RecoveryStrategies,
        FailurePattern,
        CurriculumV3,
    )
"""

from .stage_curriculum import (
    StageCurriculum,
    StageMetrics,
    StageStats,
    RecoveryStrategy,
)
from .workflow_orchestrator import (
    WorkflowOrchestrator,
    WorkflowResult,
    WorkflowPath,
    StageResult,
    WorkflowStatus,
    StageStatus,
)
from .recovery_strategies import (
    RecoveryStrategies,
    FailurePattern,
    RecoveryAction,
)
from .curriculum_v3 import CurriculumV3

__all__ = [
    # Stage Curriculum
    "StageCurriculum",
    "StageMetrics",
    "StageStats",
    "RecoveryStrategy",
    # Workflow Orchestrator
    "WorkflowOrchestrator",
    "WorkflowResult",
    "WorkflowPath",
    "StageResult",
    "WorkflowStatus",
    "StageStatus",
    # Recovery Strategies
    "RecoveryStrategies",
    "FailurePattern",
    "RecoveryAction",
    # Curriculum V3
    "CurriculumV3",
]
