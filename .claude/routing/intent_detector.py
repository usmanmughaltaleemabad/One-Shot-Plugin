"""
Intent Detection — Phase 3-T3

Parses user requests and detects:
  - Intent type (simple_crud, complex_multi_entity, real_time_system, etc.)
  - Complexity level (low, medium, high, enterprise)
  - Risk level (experimental, standard, production_critical)

Uses keyword patterns, entity counting, and feature analysis.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Set, List


class IntentType(str, Enum):
    """Classified intent of the feature request."""
    simple_crud = "simple_crud"
    complex_multi_entity = "complex_multi_entity"
    real_time_system = "real_time_system"
    payment_system = "payment_system"
    api_design = "api_design"
    admin_panel = "admin_panel"
    integration = "integration"
    data_pipeline = "data_pipeline"


class ComplexityLevel(str, Enum):
    """Detected complexity of the feature."""
    low = "low"
    medium = "medium"
    high = "high"
    enterprise = "enterprise"


class RiskLevel(str, Enum):
    """Risk classification of the feature."""
    experimental = "experimental"
    standard = "standard"
    production_critical = "production_critical"


@dataclass
class DetectionResult:
    """Result of intent detection analysis."""
    intent: IntentType
    complexity: ComplexityLevel
    risk: RiskLevel
    entities_detected: List[str]
    features_detected: List[str]
    keywords: List[str]
    confidence: float  # 0.0 to 1.0


class IntentDetector:
    """Detects intent, complexity, and risk from user requests."""

    # Keyword patterns for each intent type
    INTENT_KEYWORDS = {
        IntentType.simple_crud: {
            "keywords": ["crud", "create read update delete", "list", "show", "edit", "delete"],
            "weight": 1.0,
        },
        IntentType.complex_multi_entity: {
            "keywords": ["relationship", "join", "association", "many-to-many", "has_many", "belongs_to",
                        "nested", "hierarchical", "tree", "graph", "complex domain"],
            "weight": 1.0,
        },
        IntentType.real_time_system: {
            "keywords": ["real-time", "websocket", "live", "streaming", "push", "notification",
                        "socket.io", "broadcast", "channel", "subscribe", "publish"],
            "weight": 1.0,
        },
        IntentType.payment_system: {
            "keywords": ["payment", "stripe", "transaction", "invoice", "billing", "subscription",
                        "refund", "checkout", "cart", "money", "currency", "purchase", "order"],
            "weight": 1.0,
        },
        IntentType.api_design: {
            "keywords": ["api", "rest", "endpoint", "graphql", "schema", "serializer",
                        "request", "response", "authentication", "authorization"],
            "weight": 1.0,
        },
        IntentType.admin_panel: {
            "keywords": ["dashboard", "admin", "reporting", "analytics", "metrics", "chart",
                        "visualization", "grid", "table", "bulk", "export", "import"],
            "weight": 1.0,
        },
        IntentType.integration: {
            "keywords": ["integration", "external", "third-party", "api call", "webhook", "oauth",
                        "sync", "import", "export", "connect", "service"],
            "weight": 1.0,
        },
        IntentType.data_pipeline: {
            "keywords": ["pipeline", "batch", "job", "processing", "cron", "schedule",
                        "background", "queue", "worker", "async", "bulk operation"],
            "weight": 1.0,
        },
    }

    # Common entity names to detect
    ENTITY_PATTERNS = {
        "user": r"\b(user|account|profile|member|person|customer|admin)\b",
        "order": r"\b(order|purchase|transaction|invoice|payment)\b",
        "product": r"\b(product|item|sku|good|commodity)\b",
        "category": r"\b(category|tag|label|type|classification)\b",
        "review": r"\b(review|rating|comment|feedback)\b",
        "comment": r"\b(comment|note|remark|message)\b",
        "file": r"\b(file|document|attachment|upload|image|photo)\b",
        "notification": r"\b(notification|alert|message|email|sms)\b",
        "permission": r"\b(permission|role|access|privilege|auth)\b",
    }

    # Risk keywords
    SECURITY_KEYWORDS = {
        "keywords": ["security", "authentication", "authorization", "permission", "access control",
                    "sensitive", "private", "encrypted", "password", "token", "session"],
        "score": 1.0,
    }

    COMPLIANCE_KEYWORDS = {
        "keywords": ["compliance", "gdpr", "hipaa", "pci", "audit", "legal", "regulatory", "regulation"],
        "score": 1.0,
    }

    PRODUCTION_CRITICAL_KEYWORDS = {
        "keywords": ["production", "critical", "mission", "core", "essential", "must", "always",
                    "zero downtime", "high availability", "sla"],
        "score": 1.0,
    }

    def detect_intent(self, request: str) -> IntentType:
        """Detect primary intent from request."""
        result = self._score_intents(request)
        if result:
            return result[0][0]  # Return intent with highest score
        return IntentType.simple_crud  # Default fallback

    def detect_complexity(self, request: str, intent: IntentType) -> ComplexityLevel:
        """Detect complexity level based on request details."""
        # Count entities
        entity_count = self._count_entities(request)

        # Count relationships and complexity markers
        relationship_count = len(re.findall(r"\b(has_many|has_one|belongs_to|many_to_many|relationship|hierarchical)\b", request, re.IGNORECASE))
        feature_count = self._count_feature_mentions(request)
        api_endpoint_count = len(re.findall(r"\b(endpoint|route|api|path)\b", request, re.IGNORECASE))

        # Calculate complexity score
        complexity_score = (entity_count * 2.0) + (relationship_count * 3.0) + (feature_count * 0.8) + (api_endpoint_count * 0.5)

        # Adjust for intent type
        if intent == IntentType.real_time_system:
            complexity_score += 2.0
        elif intent == IntentType.payment_system:
            complexity_score += 2.5
        elif intent == IntentType.integration:
            complexity_score += 1.5
        elif intent == IntentType.complex_multi_entity:
            complexity_score += 1.5

        if complexity_score > 12:
            return ComplexityLevel.enterprise
        elif complexity_score > 7:
            return ComplexityLevel.high
        elif complexity_score > 3:
            return ComplexityLevel.medium
        else:
            return ComplexityLevel.low

    def detect_risk(self, intent: IntentType, complexity: ComplexityLevel) -> RiskLevel:
        """Detect risk level based on intent and complexity."""
        risk_score = 0.0

        # Inherent risk by intent type
        if intent == IntentType.payment_system:
            risk_score += 4.0
        elif intent == IntentType.real_time_system:
            risk_score += 3.5
        elif intent == IntentType.api_design:
            risk_score += 1.5
        elif intent == IntentType.integration:
            risk_score += 1.5

        # Risk by complexity
        if complexity == ComplexityLevel.enterprise:
            risk_score += 2.0
        elif complexity == ComplexityLevel.high:
            risk_score += 1.5

        if risk_score >= 3.5:
            return RiskLevel.production_critical
        elif risk_score >= 1.5:
            return RiskLevel.standard
        else:
            return RiskLevel.experimental

    def full_detection(self, request: str) -> DetectionResult:
        """Perform full intent detection analysis."""
        intent = self.detect_intent(request)
        complexity = self.detect_complexity(request, intent)
        risk = self.detect_risk(intent, complexity)

        entities = self._extract_entities(request)
        features = self._extract_features(request)
        keywords = self._extract_keywords(request, intent)
        confidence = self._calculate_confidence(request, intent)

        return DetectionResult(
            intent=intent,
            complexity=complexity,
            risk=risk,
            entities_detected=entities,
            features_detected=features,
            keywords=keywords,
            confidence=confidence,
        )

    # Private helper methods

    def _score_intents(self, request: str) -> list[tuple[IntentType, float]]:
        """Score all intent types against the request."""
        request_lower = request.lower()
        scores: dict[IntentType, float] = {intent: 0.0 for intent in IntentType}

        for intent, keyword_info in self.INTENT_KEYWORDS.items():
            for keyword in keyword_info["keywords"]:
                if keyword.lower() in request_lower or re.search(rf"\b{re.escape(keyword)}\b", request_lower, re.IGNORECASE):
                    scores[intent] += keyword_info["weight"]

        # Sort by score (descending)
        return sorted(scores.items(), key=lambda x: x[1], reverse=True)

    def _count_entities(self, request: str) -> int:
        """Count distinct entities mentioned in request."""
        count = 0
        for entity_name in self.ENTITY_PATTERNS:
            pattern = self.ENTITY_PATTERNS[entity_name]
            matches = re.findall(pattern, request, re.IGNORECASE)
            if matches:
                count += 1
        return count

    def _extract_entities(self, request: str) -> List[str]:
        """Extract specific entities mentioned in request."""
        entities = []
        for entity_name, pattern in self.ENTITY_PATTERNS.items():
            if re.search(pattern, request, re.IGNORECASE):
                entities.append(entity_name)
        return entities

    def _count_feature_mentions(self, request: str) -> int:
        """Count major features mentioned."""
        features = [
            "list", "create", "read", "update", "delete", "search", "filter", "sort",
            "pagination", "export", "import", "bulk", "validation", "notification",
            "permission", "audit", "analytics", "reporting", "workflow", "state",
            "versioning", "caching", "real-time", "api", "webhook"
        ]
        count = 0
        for feature in features:
            if re.search(rf"\b{feature}\b", request, re.IGNORECASE):
                count += 1
        return count

    def _extract_features(self, request: str) -> List[str]:
        """Extract specific features mentioned."""
        features = [
            "list", "create", "read", "update", "delete", "search", "filter", "sort",
            "pagination", "export", "import", "bulk", "validation", "notification",
            "permission", "audit", "analytics", "reporting", "workflow", "state",
            "versioning", "caching", "real-time", "api", "webhook", "webhook"
        ]
        detected = []
        for feature in features:
            if re.search(rf"\b{feature}\b", request, re.IGNORECASE):
                detected.append(feature)
        return detected

    def _extract_keywords(self, request: str, intent: IntentType) -> List[str]:
        """Extract keywords that matched for the detected intent."""
        request_lower = request.lower()
        matched_keywords = []

        for keyword in self.INTENT_KEYWORDS[intent]["keywords"]:
            if keyword.lower() in request_lower or re.search(rf"\b{re.escape(keyword)}\b", request_lower, re.IGNORECASE):
                matched_keywords.append(keyword)

        return matched_keywords

    def _calculate_confidence(self, request: str, intent: IntentType) -> float:
        """Calculate confidence score for intent detection (0.0-1.0)."""
        # If we found multiple matching keywords, confidence is higher
        keywords_matched = self._extract_keywords(request, intent)
        keyword_confidence = min(len(keywords_matched) / 3.0, 1.0)

        # Longer, more detailed requests have higher confidence
        request_length = len(request.split())
        length_confidence = min(request_length / 20.0, 1.0)

        # Average the two signals
        confidence = (keyword_confidence + length_confidence) / 2.0
        return round(confidence, 2)
