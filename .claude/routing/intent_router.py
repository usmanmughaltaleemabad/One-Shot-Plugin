"""
Intent Router — Phase 3-T3

Routes feature requests to specialized agents based on detected intent,
complexity, and risk level. Includes similarity search for learning from
past requests stored in the knowledge store.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any

try:
    from intent_detector import IntentDetector, DetectionResult, IntentType, ComplexityLevel, RiskLevel
    from routing_matrix import RoutingMatrix, AgentSpec
except ImportError:
    # Fallback for test imports
    from .intent_detector import IntentDetector, DetectionResult, IntentType, ComplexityLevel, RiskLevel
    from .routing_matrix import RoutingMatrix, AgentSpec


@dataclass
class RoutingDecision:
    """Complete routing decision for a feature request."""
    request: str
    intent: IntentType
    complexity: ComplexityLevel
    risk: RiskLevel
    agent_name: str
    cost_estimate: float  # USD
    duration_estimate: float  # minutes
    confidence: float  # 0.0-1.0
    entities_detected: List[str]
    features_detected: List[str]
    special_handling: List[str]
    similar_past_requests: List[str]  # From knowledge store

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict."""
        return {
            "request": self.request,
            "intent": self.intent.value,
            "complexity": self.complexity.value,
            "risk": self.risk.value,
            "agent_name": self.agent_name,
            "cost_estimate": self.cost_estimate,
            "duration_estimate": self.duration_estimate,
            "confidence": self.confidence,
            "entities_detected": self.entities_detected,
            "features_detected": self.features_detected,
            "special_handling": self.special_handling,
            "similar_past_requests": self.similar_past_requests,
        }

    def to_json(self) -> str:
        """Serialize to JSON."""
        return json.dumps(self.to_dict(), indent=2)


class IntentRouter:
    """Routes feature requests to specialized agents."""

    def __init__(self, knowledge_store_path: Optional[Path] = None):
        """
        Initialize the router.

        Args:
            knowledge_store_path: Path to knowledge store for similarity search
        """
        self.detector = IntentDetector()
        self.knowledge_store_path = knowledge_store_path or Path(".beads/routing_decisions.jsonl")
        self._load_routing_history()

    def route(self, request: str, context: Optional[Dict[str, Any]] = None) -> RoutingDecision:
        """
        Route a feature request to the appropriate agent.

        Args:
            request: Natural language feature request
            context: Optional context dict with additional info

        Returns:
            RoutingDecision with agent recommendation and estimates
        """
        # Detect intent, complexity, and risk
        detection = self.detector.full_detection(request)

        # Get agent spec from routing matrix
        agent_spec = RoutingMatrix.get_agent(
            detection.intent,
            detection.complexity,
            detection.risk,
        )

        # Find similar past requests for learning
        similar_requests = self.find_similar_requests(request, top_k=3)

        # Create routing decision
        decision = RoutingDecision(
            request=request,
            intent=detection.intent,
            complexity=detection.complexity,
            risk=detection.risk,
            agent_name=agent_spec.name,
            cost_estimate=agent_spec.max_cost_estimate,
            duration_estimate=agent_spec.duration_estimate_minutes,
            confidence=detection.confidence,
            entities_detected=detection.entities_detected,
            features_detected=detection.features_detected,
            special_handling=agent_spec.special_handling,
            similar_past_requests=similar_requests,
        )

        # Store the decision for future learning
        self._store_routing_decision(decision)

        return decision

    def find_similar_requests(self, request: str, top_k: int = 3) -> List[str]:
        """
        Find similar past requests from routing history.

        Uses simple keyword overlap and entity matching (no ML needed).

        Args:
            request: Feature request to match
            top_k: Number of similar requests to return

        Returns:
            List of similar past request strings
        """
        if not self._routing_history:
            return []

        request_words = set(request.lower().split())
        similarities = []

        for past_decision in self._routing_history:
            past_words = set(past_decision.get("request", "").lower().split())
            overlap = len(request_words & past_words)
            similarity_score = overlap / len(request_words | past_words) if request_words | past_words else 0.0

            # Also boost score if intent and complexity match
            if (
                past_decision.get("intent") == ""  # Will be filled by user
                and past_decision.get("complexity") == ""  # Will be filled by user
            ):
                similarity_score *= 1.2

            if similarity_score > 0.2:  # Threshold for meaningful similarity
                similarities.append((past_decision.get("request", ""), similarity_score))

        # Sort by similarity score and return top_k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return [req for req, score in similarities[:top_k]]

    def apply_rules(
        self,
        intent: IntentType,
        complexity: ComplexityLevel,
        risk: RiskLevel,
    ) -> str:
        """
        Apply hardcoded routing rules to get agent name.

        This is the deterministic routing logic (can be tested independently).

        Args:
            intent: Detected intent type
            complexity: Detected complexity level
            risk: Detected risk level

        Returns:
            Recommended agent name
        """
        agent_spec = RoutingMatrix.get_agent(intent, complexity, risk)
        return agent_spec.name

    def estimate_cost(self, agent_spec: AgentSpec, tokens_estimate: int = 5000) -> float:
        """
        Estimate cost for a generation using the given agent.

        Args:
            agent_spec: Agent specification
            tokens_estimate: Estimated tokens to use

        Returns:
            Estimated cost in USD
        """
        return (tokens_estimate / 1000.0) * agent_spec.cost_per_token

    # Private helper methods

    def _load_routing_history(self):
        """Load routing history from file for similarity search."""
        self._routing_history = []
        if self.knowledge_store_path.exists():
            try:
                with open(self.knowledge_store_path, "r") as f:
                    for line in f:
                        if line.strip():
                            self._routing_history.append(json.loads(line))
            except Exception:
                pass  # Ignore load errors

    def _store_routing_decision(self, decision: RoutingDecision):
        """Store routing decision for future similarity search."""
        self.knowledge_store_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.knowledge_store_path, "a") as f:
            f.write(decision.to_json() + "\n")
        # Also update in-memory history
        self._routing_history.append(decision.to_dict())
