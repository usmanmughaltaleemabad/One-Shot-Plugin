"""
Knowledge Store — Semantic learning and fact storage for one-shot-prompting

Components:
  - fact_schema: KnowledgeFact, FactType, FactMetadata dataclasses
  - embedding_engine: EmbeddingEngine with sentence-transformers + fallback
  - knowledge_store: KnowledgeStore with SQLite + JSONL storage
  - curriculum_v2: CurriculumV2 integration layer

Example:
    from .claude.knowledge import KnowledgeStore, CurriculumV2, KnowledgeFact

    # Direct store usage
    store = KnowledgeStore(db_path=".beads/knowledge.db")
    similar = store.search("shopping cart with items", top_k=5)

    # Curriculum integration
    curric = CurriculumV2(store)
    cost = curric.get_cost_estimates(entity_count=5)
    curric.record_successful_generation(
        "shopping cart", entity_count=5, cost_usd=0.78, generation_time_sec=15.0
    )
"""

from .fact_schema import KnowledgeFact, FactType, FactMetadata
from .embedding_engine import EmbeddingEngine
from .knowledge_store import KnowledgeStore
from .curriculum_v2 import CurriculumV2

__all__ = [
    "KnowledgeFact",
    "FactType",
    "FactMetadata",
    "EmbeddingEngine",
    "KnowledgeStore",
    "CurriculumV2",
]
