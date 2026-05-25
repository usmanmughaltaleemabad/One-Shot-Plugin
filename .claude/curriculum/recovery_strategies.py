"""
Recovery Strategies — Phase 3-T4

Common failure patterns and recovery actions for each stage:
- Identifies root causes
- Provides deterministic recovery actions
- Tracks success rates
- Escalates when recovery exhausted

Pattern library for 15+ common failure scenarios.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any


class RecoveryAction(str, Enum):
    """Recovery actions available."""
    RETRY = "retry"
    ADJUST_PARAMS = "adjust_params"
    REGENERATE = "regenerate"
    SIMPLIFY = "simplify"
    SKIP_STAGE = "skip_stage"
    ESCALATE = "escalate"
    FALLBACK = "fallback"


@dataclass
class FailurePattern:
    """A known failure pattern with recovery."""
    stage: str
    error_type: str
    root_cause: str
    indicators: List[str]  # Symptoms to detect this pattern
    recovery_actions: List[RecoveryAction]
    primary_action: RecoveryAction
    adjusted_params: Optional[Dict[str, Any]] = None
    success_rate: float = 0.7  # Expected success rate after recovery
    notes: str = ""


class RecoveryStrategies:
    """Library of recovery strategies for common failures."""

    # Pattern catalog
    PATTERNS: Dict[str, List[FailurePattern]] = {
        # Design stage failures
        "design": [
            FailurePattern(
                stage="design",
                error_type="relationship_validation_failed",
                root_cause="Implicit relationships not properly inferred",
                indicators=["FK validation", "relationship", "not found", "missing"],
                recovery_actions=[
                    RecoveryAction.ADJUST_PARAMS,
                    RecoveryAction.REGENERATE,
                    RecoveryAction.ESCALATE,
                ],
                primary_action=RecoveryAction.ADJUST_PARAMS,
                adjusted_params={"add_fk_explicitly": True, "relationship_depth": 1},
                success_rate=0.85,
                notes="Explicitly define FK columns in spec instead of inferring",
            ),
            FailurePattern(
                stage="design",
                error_type="spec_completeness_low",
                root_cause="Entity definitions lack sufficient detail",
                indicators=["incomplete", "missing fields", "insufficient", "entity"],
                recovery_actions=[
                    RecoveryAction.ADJUST_PARAMS,
                    RecoveryAction.ESCALATE,
                ],
                primary_action=RecoveryAction.ADJUST_PARAMS,
                adjusted_params={"min_fields_per_entity": 4, "add_timestamps": True},
                success_rate=0.80,
                notes="Add more fields and metadata (created_at, updated_at)",
            ),
            FailurePattern(
                stage="design",
                error_type="complex_relationships",
                root_cause="Too many or circular relationships",
                indicators=["circular", "too many", "relationship", "depth"],
                recovery_actions=[
                    RecoveryAction.SIMPLIFY,
                    RecoveryAction.ADJUST_PARAMS,
                    RecoveryAction.ESCALATE,
                ],
                primary_action=RecoveryAction.SIMPLIFY,
                adjusted_params={"max_relationships": 3, "max_depth": 2},
                success_rate=0.75,
                notes="Limit relationships to 1:N with max depth 2",
            ),
        ],
        # Implementation stage failures
        "implement": [
            FailurePattern(
                stage="implement",
                error_type="missing_imports",
                root_cause="Required modules not imported",
                indicators=["NameError", "import", "not defined", "undefined"],
                recovery_actions=[
                    RecoveryAction.ADJUST_PARAMS,
                    RecoveryAction.RETRY,
                ],
                primary_action=RecoveryAction.ADJUST_PARAMS,
                adjusted_params={"scan_for_missing_imports": True},
                success_rate=0.95,
                notes="Run import scanner; add missing imports before output",
            ),
            FailurePattern(
                stage="implement",
                error_type="syntax_error",
                root_cause="Generated code has syntax errors",
                indicators=["SyntaxError", "invalid syntax", "unexpected"],
                recovery_actions=[
                    RecoveryAction.SIMPLIFY,
                    RecoveryAction.REGENERATE,
                    RecoveryAction.ESCALATE,
                ],
                primary_action=RecoveryAction.SIMPLIFY,
                adjusted_params={"max_entities": 3, "skip_advanced_features": True},
                success_rate=0.80,
                notes="Reduce complexity; simplify entity definitions",
            ),
            FailurePattern(
                stage="implement",
                error_type="indentation_error",
                root_cause="Python indentation inconsistencies",
                indicators=["IndentationError", "unexpected indent", "dedent"],
                recovery_actions=[
                    RecoveryAction.REGENERATE,
                    RecoveryAction.ESCALATE,
                ],
                primary_action=RecoveryAction.REGENERATE,
                adjusted_params={"normalize_indentation": True},
                success_rate=0.85,
                notes="Regenerate with consistent indentation handling",
            ),
        ],
        # Verification stage failures
        "verify": [
            FailurePattern(
                stage="verify",
                error_type="patch_failed",
                root_cause="Patch couldn't be applied to generated code",
                indicators=["patch", "failed", "hunk", "reject"],
                recovery_actions=[
                    RecoveryAction.REGENERATE,
                    RecoveryAction.FALLBACK,
                    RecoveryAction.ESCALATE,
                ],
                primary_action=RecoveryAction.REGENERATE,
                adjusted_params={"regenerate_from_spec": True},
                success_rate=0.85,
                notes="Regenerate from spec instead of patching",
            ),
            FailurePattern(
                stage="verify",
                error_type="validation_failed",
                root_cause="Generated code fails validation rules",
                indicators=["validation", "failed", "rule", "violation"],
                recovery_actions=[
                    RecoveryAction.ADJUST_PARAMS,
                    RecoveryAction.REGENERATE,
                    RecoveryAction.ESCALATE,
                ],
                primary_action=RecoveryAction.ADJUST_PARAMS,
                adjusted_params={"skip_advanced_features": True},
                success_rate=0.75,
                notes="Remove advanced features; stick to basics",
            ),
        ],
        # Review stage failures
        "review": [
            FailurePattern(
                stage="review",
                error_type="security_issue",
                root_cause="Code has potential security vulnerabilities",
                indicators=["security", "vulnerability", "injection", "sql"],
                recovery_actions=[
                    RecoveryAction.REGENERATE,
                    RecoveryAction.ADJUST_PARAMS,
                    RecoveryAction.ESCALATE,
                ],
                primary_action=RecoveryAction.ADJUST_PARAMS,
                adjusted_params={"enforce_security_patterns": True},
                success_rate=0.80,
                notes="Enforce parameterized queries and input validation",
            ),
            FailurePattern(
                stage="review",
                error_type="performance_issue",
                root_cause="Code has performance problems",
                indicators=["performance", "slow", "n+1", "inefficient"],
                recovery_actions=[
                    RecoveryAction.ADJUST_PARAMS,
                    RecoveryAction.REGENERATE,
                    RecoveryAction.ESCALATE,
                ],
                primary_action=RecoveryAction.ADJUST_PARAMS,
                adjusted_params={"add_indexes": True, "add_caching": True},
                success_rate=0.70,
                notes="Add database indexes and result caching",
            ),
        ],
        # Ship stage failures
        "ship": [
            FailurePattern(
                stage="ship",
                error_type="integration_error",
                root_cause="Wiring code into main project failed",
                indicators=["integration", "wiring", "import", "main"],
                recovery_actions=[
                    RecoveryAction.ADJUST_PARAMS,
                    RecoveryAction.RETRY,
                    RecoveryAction.ESCALATE,
                ],
                primary_action=RecoveryAction.ADJUST_PARAMS,
                adjusted_params={"dry_run_wiring": True, "validate_imports": True},
                success_rate=0.90,
                notes="Always dry-run wiring; validate all imports first",
            ),
            FailurePattern(
                stage="ship",
                error_type="naming_conflict",
                root_cause="Generated code conflicts with existing code",
                indicators=["conflict", "exists", "duplicate", "name"],
                recovery_actions=[
                    RecoveryAction.ADJUST_PARAMS,
                    RecoveryAction.REGENERATE,
                    RecoveryAction.ESCALATE,
                ],
                primary_action=RecoveryAction.ADJUST_PARAMS,
                adjusted_params={"add_namespace_prefix": True},
                success_rate=0.85,
                notes="Add prefix or namespace to avoid conflicts",
            ),
        ],
        # Critic stage failures
        "critic": [
            FailurePattern(
                stage="critic",
                error_type="test_failure",
                root_cause="Generated tests fail or fixtures are incomplete",
                indicators=["test", "failed", "assert", "fixture"],
                recovery_actions=[
                    RecoveryAction.SIMPLIFY,
                    RecoveryAction.ADJUST_PARAMS,
                    RecoveryAction.REGENERATE,
                    RecoveryAction.ESCALATE,
                ],
                primary_action=RecoveryAction.SIMPLIFY,
                adjusted_params={"max_entities": 2, "add_minimal_fixtures": True},
                success_rate=0.80,
                notes="Reduce entities; provide minimal fixture scaffolding",
            ),
            FailurePattern(
                stage="critic",
                error_type="coverage_gap",
                root_cause="Test coverage below target threshold",
                indicators=["coverage", "low", "threshold", "gap"],
                recovery_actions=[
                    RecoveryAction.ADJUST_PARAMS,
                    RecoveryAction.REGENERATE,
                    RecoveryAction.ESCALATE,
                ],
                primary_action=RecoveryAction.ADJUST_PARAMS,
                adjusted_params={"target_coverage": 70, "focus_on_core": True},
                success_rate=0.85,
                notes="Focus on core logic coverage (70% minimum)",
            ),
            FailurePattern(
                stage="critic",
                error_type="fixture_error",
                root_cause="Test fixtures have errors",
                indicators=["fixture", "error", "setup", "teardown"],
                recovery_actions=[
                    RecoveryAction.ADJUST_PARAMS,
                    RecoveryAction.SIMPLIFY,
                    RecoveryAction.ESCALATE,
                ],
                primary_action=RecoveryAction.ADJUST_PARAMS,
                adjusted_params={"use_mock_fixtures": True},
                success_rate=0.75,
                notes="Use mocks instead of real fixtures",
            ),
        ],
        # Record stage failures
        "record": [
            FailurePattern(
                stage="record",
                error_type="graph_accuracy",
                root_cause="Generated codebase graph is inaccurate",
                indicators=["graph", "accuracy", "node", "edge"],
                recovery_actions=[
                    RecoveryAction.REGENERATE,
                    RecoveryAction.ESCALATE,
                ],
                primary_action=RecoveryAction.REGENERATE,
                adjusted_params={"rescan_codebase": True},
                success_rate=0.90,
                notes="Rescan codebase from scratch",
            ),
            FailurePattern(
                stage="record",
                error_type="bead_quality",
                root_cause="Learned facts (beads) are low quality",
                indicators=["bead", "quality", "relevance", "similar"],
                recovery_actions=[
                    RecoveryAction.ADJUST_PARAMS,
                    RecoveryAction.ESCALATE,
                ],
                primary_action=RecoveryAction.ADJUST_PARAMS,
                adjusted_params={"filter_low_quality_beads": True},
                success_rate=0.80,
                notes="Filter low-quality beads; keep high-confidence facts",
            ),
        ],
    }

    @classmethod
    def get_patterns_for_stage(cls, stage: str) -> List[FailurePattern]:
        """Get all failure patterns for a stage."""
        return cls.PATTERNS.get(stage, [])

    @classmethod
    def find_pattern(
        cls, stage: str, error_type: str
    ) -> Optional[FailurePattern]:
        """Find a specific failure pattern."""
        patterns = cls.PATTERNS.get(stage, [])
        for pattern in patterns:
            if pattern.error_type == error_type:
                return pattern
        return None

    @classmethod
    def match_pattern_by_indicator(
        cls, stage: str, error_message: str
    ) -> Optional[FailurePattern]:
        """Find pattern by matching error message against indicators."""
        patterns = cls.PATTERNS.get(stage, [])
        error_lower = error_message.lower()

        for pattern in patterns:
            for indicator in pattern.indicators:
                if indicator.lower() in error_lower:
                    return pattern

        return None

    @classmethod
    def get_all_patterns(cls) -> List[FailurePattern]:
        """Get all patterns across all stages."""
        all_patterns = []
        for stage_patterns in cls.PATTERNS.values():
            all_patterns.extend(stage_patterns)
        return all_patterns

    @classmethod
    def suggest_recovery(
        cls, stage: str, error_type: str, error_message: str = ""
    ) -> Optional[Dict[str, Any]]:
        """
        Suggest recovery action for an error.

        Args:
            stage: Stage where error occurred
            error_type: Type of error
            error_message: Optional full error message

        Returns:
            Recovery suggestion or None
        """
        # First try exact type match
        pattern = cls.find_pattern(stage, error_type)

        # Fall back to indicator match
        if not pattern and error_message:
            pattern = cls.match_pattern_by_indicator(stage, error_message)

        if not pattern:
            return None

        return {
            "pattern": pattern.error_type,
            "root_cause": pattern.root_cause,
            "recovery_action": pattern.primary_action.value,
            "adjusted_params": pattern.adjusted_params or {},
            "expected_success_rate": pattern.success_rate,
            "notes": pattern.notes,
        }
