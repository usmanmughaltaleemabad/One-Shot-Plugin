"""
Tests for knowledge store — fact schema, embedding, storage, search, consolidation

Tests all components:
  - fact_schema: Serialization, validation, metadata
  - embedding_engine: Embedding, similarity, graceful fallback
  - knowledge_store: Add, search, consolidate, decay
  - curriculum_v2: Integration with store
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

# Add .claude/knowledge to path
REPO_ROOT = Path(__file__).parent.parent
KNOWLEDGE_PATH = REPO_ROOT / ".claude" / "knowledge"
sys.path.insert(0, str(KNOWLEDGE_PATH.parent))
sys.path.insert(0, str(REPO_ROOT))

# Import from knowledge module
import importlib.util

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

# Load modules
fact_schema = load_module("fact_schema", KNOWLEDGE_PATH / "fact_schema.py")
embedding_engine = load_module("embedding_engine", KNOWLEDGE_PATH / "embedding_engine.py")
knowledge_store = load_module("knowledge_store", KNOWLEDGE_PATH / "knowledge_store.py")
curriculum_v2 = load_module("curriculum_v2", KNOWLEDGE_PATH / "curriculum_v2.py")

# Extract classes
KnowledgeFact = fact_schema.KnowledgeFact
FactType = fact_schema.FactType
FactMetadata = fact_schema.FactMetadata
EmbeddingEngine = embedding_engine.EmbeddingEngine
KnowledgeStore = knowledge_store.KnowledgeStore
CurriculumV2 = curriculum_v2.CurriculumV2


class TestFactSchema:
    """Tests for KnowledgeFact and FactMetadata."""

    def test_fact_creation(self):
        """Test creating a basic fact."""
        fact = KnowledgeFact(
            id="kf-001",
            type=FactType.entity_pattern,
            content="Shopping cart with 5 items",
        )
        assert fact.id == "kf-001"
        assert fact.type == FactType.entity_pattern
        assert fact.content == "Shopping cart with 5 items"
        assert fact.embedding is None
        assert fact.metadata.success_count == 0
        assert fact.metadata.decay_score == 1.0

    def test_fact_with_embedding(self):
        """Test fact with embedding vector."""
        embedding = [0.1] * 384
        fact = KnowledgeFact(
            id="kf-001",
            type=FactType.cost_calibration,
            content="5 entities cost $0.78",
            embedding=embedding,
        )
        assert fact.embedding == embedding
        assert len(fact.embedding) == 384

    def test_fact_metadata_datetime(self):
        """Test metadata with datetime fields."""
        now = datetime.now()
        metadata = FactMetadata(
            created_at=now,
            success_count=3,
            failure_count=1,
            last_used=now,
        )
        assert metadata.created_at == now
        assert metadata.success_count == 3
        assert metadata.failure_count == 1

    def test_fact_to_dict_and_back(self):
        """Test serialization roundtrip."""
        fact = KnowledgeFact(
            id="kf-001",
            type=FactType.error_recovery,
            content="Fix FK type mismatch",
            embedding=[0.5] * 384,
        )
        fact.metadata.success_count = 5

        # Serialize
        d = fact.to_dict()
        assert d["id"] == "kf-001"
        assert d["type"] == "error_recovery"
        assert len(d["embedding"]) == 384

        # Deserialize
        fact2 = KnowledgeFact.from_dict(d)
        assert fact2.id == fact.id
        assert fact2.type == fact.type
        assert fact2.content == fact.content
        assert fact2.metadata.success_count == 5

    def test_fact_to_json_and_back(self):
        """Test JSON serialization roundtrip."""
        fact = KnowledgeFact(
            id="kf-001",
            type=FactType.api_design,
            content="REST API with pagination",
        )
        json_str = fact.to_json(include_embedding=False)
        assert isinstance(json_str, str)

        fact2 = KnowledgeFact.from_json(json_str)
        assert fact2.id == fact.id
        assert fact2.content == fact.content

    def test_fact_metadata_from_dict_iso_datetime(self):
        """Test metadata deserialization with ISO datetime strings."""
        now = datetime.now()
        metadata_dict = {
            "created_at": now.isoformat(),
            "success_count": 2,
            "failure_count": 0,
            "last_used": now.isoformat(),
            "decay_score": 0.9,
        }
        metadata = FactMetadata.from_dict(metadata_dict)
        assert metadata.success_count == 2
        assert metadata.decay_score == 0.9


class TestEmbeddingEngine:
    """Tests for EmbeddingEngine."""

    def test_engine_creation(self):
        """Test creating an embedding engine."""
        engine = EmbeddingEngine()
        assert engine.model_name == "all-MiniLM-L6-v2"
        assert isinstance(engine.is_available(), bool)

    def test_cosine_similarity_identical_vectors(self):
        """Test cosine similarity for identical vectors."""
        v1 = [1.0, 0.0, 0.0]
        v2 = [1.0, 0.0, 0.0]
        sim = EmbeddingEngine.cosine_similarity(v1, v2)
        assert abs(sim - 1.0) < 0.001

    def test_cosine_similarity_orthogonal_vectors(self):
        """Test cosine similarity for orthogonal vectors."""
        v1 = [1.0, 0.0]
        v2 = [0.0, 1.0]
        sim = EmbeddingEngine.cosine_similarity(v1, v2)
        assert abs(sim - 0.0) < 0.001

    def test_cosine_similarity_opposite_vectors(self):
        """Test cosine similarity for opposite vectors."""
        v1 = [1.0, 0.0]
        v2 = [-1.0, 0.0]
        sim = EmbeddingEngine.cosine_similarity(v1, v2)
        assert abs(sim - (-1.0)) < 0.001

    def test_cosine_similarity_with_none(self):
        """Test cosine similarity with None inputs."""
        assert EmbeddingEngine.cosine_similarity(None, [1.0]) == 0.0
        assert EmbeddingEngine.cosine_similarity([1.0], None) == 0.0
        assert EmbeddingEngine.cosine_similarity(None, None) == 0.0

    def test_cosine_similarity_different_lengths(self):
        """Test cosine similarity with different length vectors."""
        v1 = [1.0, 0.0]
        v2 = [1.0, 0.0, 0.0]
        sim = EmbeddingEngine.cosine_similarity(v1, v2)
        assert sim == 0.0

    def test_embed_graceful_fallback(self):
        """Test embedding gracefully handles unavailable library."""
        engine = EmbeddingEngine()
        # If sentence-transformers available, embed returns list
        # If not available, returns None (graceful fallback)
        result = engine.embed("test text")
        assert result is None or isinstance(result, list)

    def test_batch_embed(self):
        """Test batch embedding."""
        engine = EmbeddingEngine()
        texts = ["text 1", "text 2", "text 3"]
        results = engine.batch_embed(texts)
        assert len(results) == 3
        # Each result is None or a list
        for result in results:
            assert result is None or isinstance(result, list)


class TestKnowledgeStore:
    """Tests for KnowledgeStore."""

    def test_store_creation(self):
        """Test creating a knowledge store."""
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "knowledge.db"
            store = KnowledgeStore(db_path=db_path)
            assert store.db_path == db_path
            store.close()

    def test_add_fact_and_load(self):
        """Test adding and loading facts."""
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "knowledge.db"
            store = KnowledgeStore(db_path=db_path)

            fact = KnowledgeFact(
                id="kf-001",
                type=FactType.entity_pattern,
                content="Shopping cart with items",
            )
            fact_id = store.add_fact(fact)
            assert fact_id == "kf-001"

            # Load and verify
            facts = store._load_all_facts()
            assert len(facts) == 1
            assert facts[0].id == "kf-001"

            store.close()

    def test_emit_fact_convenience(self):
        """Test emit_fact convenience method."""
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "knowledge.db"
            store = KnowledgeStore(db_path=db_path)

            fact_id = store.emit_fact(
                "Order with 5 entities: cost $0.78",
                fact_type="cost_calibration",
            )
            assert fact_id.startswith("kf-")

            facts = store._load_all_facts()
            assert len(facts) == 1
            assert facts[0].type == FactType.cost_calibration

            store.close()

    def test_search_returns_list(self):
        """Test search returns a list of facts."""
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "knowledge.db"
            store = KnowledgeStore(db_path=db_path)

            # Add a fact
            store.emit_fact("Shopping cart system", fact_type="entity_pattern")

            # Search
            results = store.search("shopping cart", top_k=5)
            assert isinstance(results, list)

            store.close()

    def test_search_respects_top_k(self):
        """Test search respects top_k parameter."""
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "knowledge.db"
            store = KnowledgeStore(db_path=db_path)

            # Add multiple facts
            for i in range(10):
                store.emit_fact(f"Fact {i}", fact_type="entity_pattern")

            results = store.search("Fact", top_k=3)
            assert len(results) <= 3

            store.close()

    def test_get_stats(self):
        """Test getting store statistics."""
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "knowledge.db"
            store = KnowledgeStore(db_path=db_path)

            store.emit_fact("Fact 1", fact_type="entity_pattern")
            store.emit_fact("Fact 2", fact_type="cost_calibration")

            stats = store.get_stats()
            assert "total_facts" in stats
            assert "by_type" in stats
            assert stats["total_facts"] == 2
            assert stats["by_type"]["entity_pattern"] == 1
            assert stats["by_type"]["cost_calibration"] == 1

            store.close()

    def test_decay_facts(self):
        """Test fact decay scoring."""
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "knowledge.db"
            store = KnowledgeStore(db_path=db_path)

            fact = KnowledgeFact(
                id="kf-001",
                type=FactType.entity_pattern,
                content="Test fact",
                metadata=FactMetadata(
                    created_at=datetime.now() - timedelta(days=15)
                ),
            )
            store.add_fact(fact)

            # Decay facts
            updated = store.decay_facts(days_old=30)
            assert updated >= 1

            facts = store._load_all_facts()
            # Fact is 15 days old, so decay should be 0.5
            assert 0.4 < facts[0].metadata.decay_score < 0.6

            store.close()

    def test_consolidate_facts(self):
        """Test fact consolidation."""
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "knowledge.db"
            store = KnowledgeStore(db_path=db_path)

            # Add facts
            store.emit_fact("Fact 1", fact_type="entity_pattern")
            store.emit_fact("Fact 2", fact_type="entity_pattern")
            store.emit_fact("Fact 3", fact_type="entity_pattern")

            result = store.consolidate_facts()
            assert isinstance(result, dict)
            assert "merged_count" in result
            assert "archived_count" in result

            store.close()

    def test_store_with_jsonl_fallback(self):
        """Test JSONL fallback when SQLite unavailable."""
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "knowledge.db"
            jsonl_path = Path(tmpdir) / "knowledge.jsonl"

            # Create store with SQLite disabled
            store = KnowledgeStore(db_path=db_path, use_sqlite=False)
            assert store._use_jsonl

            fact_id = store.emit_fact("Test fact", fact_type="entity_pattern")
            assert fact_id.startswith("kf-")

            # Verify fact was written to JSONL
            assert jsonl_path.exists() or store.jsonl_path.exists()

            store.close()


class TestCurriculumV2:
    """Tests for CurriculumV2 integration."""

    def test_curriculum_creation(self):
        """Test creating a curriculum instance."""
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "knowledge.db"
            store = KnowledgeStore(db_path=db_path)
            curric = CurriculumV2(store=store)
            assert curric.store is store
            store.close()

    def test_get_similar_generations_empty(self):
        """Test similar generations when store is empty."""
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "knowledge.db"
            store = KnowledgeStore(db_path=db_path)
            curric = CurriculumV2(store=store)

            results = curric.get_similar_generations("shopping cart")
            assert results == []

            store.close()

    def test_record_successful_generation(self):
        """Test recording a successful generation."""
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "knowledge.db"
            store = KnowledgeStore(db_path=db_path)
            curric = CurriculumV2(store=store)

            fact_id = curric.record_successful_generation(
                feature_description="Shopping cart",
                entity_count=5,
                cost_usd=0.78,
                generation_time_sec=15.0,
            )
            assert fact_id.startswith("kf-")

            facts = store._load_all_facts()
            assert len(facts) >= 2  # entity_pattern + cost_calibration

            store.close()

    def test_record_failed_generation(self):
        """Test recording a failed generation."""
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "knowledge.db"
            store = KnowledgeStore(db_path=db_path)
            curric = CurriculumV2(store=store)

            fact_id = curric.record_failed_generation(
                feature_description="Shopping cart",
                error_type="FK type mismatch",
                error_message="Column type int != string",
                recovery_strategy="Check spec.json types",
            )
            assert fact_id.startswith("kf-")

            facts = store._load_all_facts()
            assert len(facts) == 1
            assert facts[0].type == FactType.error_recovery

            store.close()

    def test_get_cost_estimates(self):
        """Test getting cost estimates."""
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "knowledge.db"
            store = KnowledgeStore(db_path=db_path)
            curric = CurriculumV2(store=store)

            # Record some successful generations with cost
            for i in range(3):
                curric.record_successful_generation(
                    feature_description="Test",
                    entity_count=5,
                    cost_usd=0.78,
                    generation_time_sec=10.0,
                )

            cost = curric.get_cost_estimates(entity_count=5)
            # Cost should be None or a float if embeddings available
            assert cost is None or isinstance(cost, float)

            store.close()

    def test_get_error_patterns(self):
        """Test getting error patterns."""
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "knowledge.db"
            store = KnowledgeStore(db_path=db_path)
            curric = CurriculumV2(store=store)

            # Record some error patterns
            curric.record_failed_generation(
                feature_description="Test",
                error_type="FK type mismatch",
                error_message="int != string",
                recovery_strategy="Fix types",
            )

            patterns = curric.get_error_patterns("FK type")
            assert isinstance(patterns, list)
            # May be empty if embeddings unavailable

            store.close()

    def test_consolidate_curriculum(self):
        """Test curriculum consolidation."""
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "knowledge.db"
            store = KnowledgeStore(db_path=db_path)
            curric = CurriculumV2(store=store)

            # Add multiple facts
            for i in range(5):
                curric.record_successful_generation(
                    feature_description=f"Feature {i}",
                    entity_count=5,
                    cost_usd=0.75 + i * 0.01,
                    generation_time_sec=12.0 + i,
                )

            result = curric.consolidate()
            assert "merged_count" in result
            assert "archived_count" in result

            store.close()

    def test_get_curriculum_stats(self):
        """Test getting curriculum stats."""
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "knowledge.db"
            store = KnowledgeStore(db_path=db_path)
            curric = CurriculumV2(store=store)

            curric.record_successful_generation(
                feature_description="Test",
                entity_count=4,
                cost_usd=0.72,
                generation_time_sec=11.0,
            )

            stats = curric.get_stats()
            assert "total_facts" in stats
            assert stats["total_facts"] >= 1

            store.close()


class TestIntegration:
    """Integration tests combining multiple components."""

    def test_end_to_end_workflow(self):
        """Test complete workflow: record, search, consolidate."""
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "knowledge.db"
            store = KnowledgeStore(db_path=db_path)
            curric = CurriculumV2(store=store)

            # Record successful generations
            for i in range(3):
                curric.record_successful_generation(
                    feature_description="E-commerce shopping cart",
                    entity_count=4 + i,
                    cost_usd=0.70 + i * 0.05,
                    generation_time_sec=12.0 + i * 2,
                )

            # Record a failure
            curric.record_failed_generation(
                feature_description="Shopping cart",
                error_type="FK constraint",
                error_message="Foreign key type mismatch",
                recovery_strategy="Align column types",
            )

            # Get stats
            stats = curric.get_stats()
            assert stats["total_facts"] >= 4

            # Consolidate
            result = curric.consolidate()
            assert "merged_count" in result

            # Get similar generations (may return empty if no embeddings)
            similar = curric.get_similar_generations(
                "shopping cart with items"
            )
            assert isinstance(similar, list)

            store.close()

    def test_fact_persistence_across_instances(self):
        """Test that facts persist across store instances."""
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "knowledge.db"

            # First instance: add a fact
            store1 = KnowledgeStore(db_path=db_path)
            store1.emit_fact("Test fact", fact_type="entity_pattern")
            store1.close()

            # Second instance: load the fact
            store2 = KnowledgeStore(db_path=db_path)
            facts = store2._load_all_facts()
            assert len(facts) == 1
            assert facts[0].content == "Test fact"
            store2.close()
