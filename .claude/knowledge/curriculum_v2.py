"""
Curriculum v2 — Semantic-based learning from past generations

Replaces binary curriculum (pass/fail) with semantic search over
learned facts. Provides:

  - get_similar_generations(): Find similar past generations
  - get_cost_estimates(): Predict cost based on entity count
  - get_error_patterns(): Find recovery strategies for error types
  - update_with_generation(): Record facts from successful generation

API:
    curric = CurriculumV2()
    similar = curric.get_similar_generations("shopping cart with 4 items")
    cost = curric.get_cost_estimates(entity_count=5)
    errors = curric.get_error_patterns("FK type mismatch")
    curric.update_with_generation(cost=0.78, entity_count=5)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

try:
    from .fact_schema import KnowledgeFact, FactType
    from .knowledge_store import KnowledgeStore
except ImportError:
    # Fallback for direct imports
    from fact_schema import KnowledgeFact, FactType
    from knowledge_store import KnowledgeStore

logger = logging.getLogger(__name__)


class CurriculumV2:
    """Semantic curriculum backed by knowledge store."""

    def __init__(self, store: Optional[KnowledgeStore] = None):
        """
        Initialize curriculum.

        Args:
            store: Optional KnowledgeStore instance. If None, creates new one.
        """
        self.store = store or KnowledgeStore()

    def get_similar_generations(
        self,
        feature_description: str,
        top_k: int = 5,
    ) -> List[KnowledgeFact]:
        """
        Find similar past generations by semantic search.

        Args:
            feature_description: Feature description (e.g., "shopping cart with items")
            top_k: Number of results to return

        Returns:
            List of similar KnowledgeFact entries
        """
        if not feature_description:
            return []

        # Search for entity_pattern and api_design facts
        facts = self.store.search(
            feature_description,
            top_k=top_k,
            fact_type=FactType.entity_pattern,
        )

        # Also search api_design if not enough results
        if len(facts) < top_k:
            additional = self.store.search(
                feature_description,
                top_k=top_k - len(facts),
                fact_type=FactType.api_design,
            )
            facts.extend(additional)

        return facts

    def get_cost_estimates(
        self,
        entity_count: int,
        feature_description: str = "",
    ) -> Optional[float]:
        """
        Estimate cost for a generation based on past observations.

        Args:
            entity_count: Number of entities in the schema
            feature_description: Optional feature description for context

        Returns:
            Estimated cost in USD, or None if no data available
        """
        query = f"cost {entity_count} entities"
        if feature_description:
            query = f"{feature_description} cost {entity_count} entities"

        facts = self.store.search(
            query,
            top_k=5,
            fact_type=FactType.cost_calibration,
        )

        if not facts:
            return None

        # Extract cost from fact content (format: "...avg cost $X.XX")
        costs = []
        import re
        for fact in facts:
            match = re.search(r"\$([0-9.]+)", fact.content)
            if match:
                try:
                    costs.append(float(match.group(1)))
                except ValueError:
                    pass

        if not costs:
            return None

        # Return median cost
        costs.sort()
        return costs[len(costs) // 2]

    def get_error_patterns(
        self,
        error_type: str,
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Get recovery strategies for a known error type.

        Args:
            error_type: Error description (e.g., "FK type mismatch")
            top_k: Number of strategies to return

        Returns:
            List of recovery strategies with content and success_count
        """
        if not error_type:
            return []

        facts = self.store.search(
            error_type,
            top_k=top_k,
            fact_type=FactType.error_recovery,
        )

        return [
            {
                "id": fact.id,
                "content": fact.content,
                "success_count": fact.metadata.success_count,
                "failure_count": fact.metadata.failure_count,
            }
            for fact in facts
        ]

    def record_successful_generation(
        self,
        feature_description: str,
        entity_count: int,
        cost_usd: float,
        generation_time_sec: float,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Record a successful generation as facts in the knowledge store.

        Args:
            feature_description: What was generated
            entity_count: Number of entities
            cost_usd: Cost in USD
            generation_time_sec: Generation time in seconds
            extra_metadata: Optional additional metadata

        Returns:
            Fact ID
        """
        # Create entity_pattern fact
        entity_fact_content = (
            f"{feature_description} with {entity_count} entities "
            f"(cost ${cost_usd:.2f}, time {generation_time_sec:.1f}s)"
        )
        entity_fact_id = self.store.emit_fact(
            entity_fact_content,
            fact_type=FactType.entity_pattern.value,
            metadata={"success_count": 1},
        )

        # Create cost_calibration fact
        cost_fact_content = (
            f"Entity count {entity_count}: avg cost ${cost_usd:.2f}"
        )
        self.store.emit_fact(
            cost_fact_content,
            fact_type=FactType.cost_calibration.value,
            metadata={"success_count": 1},
        )

        return entity_fact_id

    def record_failed_generation(
        self,
        feature_description: str,
        error_type: str,
        error_message: str,
        recovery_strategy: Optional[str] = None,
    ) -> str:
        """
        Record a failed generation as an error_recovery fact.

        Args:
            feature_description: What was being generated
            error_type: Type of error
            error_message: Full error message
            recovery_strategy: Optional recovery hint

        Returns:
            Fact ID
        """
        fact_content = (
            f"Error in {feature_description}: {error_type}\n"
            f"Message: {error_message}"
        )
        if recovery_strategy:
            fact_content += f"\nRecovery: {recovery_strategy}"

        fact_id = self.store.emit_fact(
            fact_content,
            fact_type=FactType.error_recovery.value,
            metadata={"failure_count": 1},
        )

        return fact_id

    def get_stats(self) -> Dict[str, Any]:
        """Get curriculum statistics."""
        return self.store.get_stats()

    def consolidate(self) -> Dict[str, int]:
        """
        Run consolidation (merge similar facts, archive old ones).

        Returns:
            {"merged_count": int, "archived_count": int}
        """
        # Update decay scores first
        self.store.decay_facts()

        # Consolidate facts
        return self.store.consolidate_facts()
