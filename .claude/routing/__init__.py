"""
Intent-Based Routing — Phase 3-T3

Public API exports for the intent-based routing system.
"""

from intent_detector import (
    IntentDetector,
    IntentType,
    ComplexityLevel,
    RiskLevel,
    DetectionResult,
)
from intent_router import IntentRouter, RoutingDecision
from routing_matrix import RoutingMatrix, AgentSpec

__all__ = [
    "IntentDetector",
    "IntentType",
    "ComplexityLevel",
    "RiskLevel",
    "DetectionResult",
    "IntentRouter",
    "RoutingDecision",
    "RoutingMatrix",
    "AgentSpec",
]
