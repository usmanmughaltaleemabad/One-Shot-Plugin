"""
Tests for embedding_cache.py (optional sentence-transformers support).

Covers:
  - init_cache() creates SQLite database
  - get_embedding() stores/retrieves from cache
  - Graceful fallback when sentence-transformers unavailable
  - cosine_similarity() correctness on various vectors
"""

import sqlite3
import sys
import tempfile
from pathlib import Path
from unittest import mock

import pytest

# Add scripts to path
REPO_ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = REPO_ROOT / "skills" / "one-shot-generator" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import embedding_cache


@pytest.fixture
def temp_cache_dir(tmp_path):
    """Temporarily override CACHE_DB to use a temp directory."""
    orig_cache_db = embedding_cache.CACHE_DB
    temp_db = tmp_path / ".beads" / "embedding_cache.db"
    embedding_cache.CACHE_DB = temp_db
    embedding_cache._MODEL_INSTANCE = None
    embedding_cache._MODEL_FAILED = False
    yield temp_db
    embedding_cache.CACHE_DB = orig_cache_db
    embedding_cache._MODEL_INSTANCE = None
    embedding_cache._MODEL_FAILED = False


class TestInitCache:
    """Test cache initialization."""

    def test_init_cache_creates_directory(self, temp_cache_dir):
        """init_cache() creates .beads directory if missing."""
        embedding_cache.init_cache()
        assert temp_cache_dir.parent.exists()

    def test_init_cache_creates_database(self, temp_cache_dir):
        """init_cache() creates SQLite database file."""
        embedding_cache.init_cache()
        assert temp_cache_dir.exists()

    def test_init_cache_creates_table(self, temp_cache_dir):
        """init_cache() creates embeddings table with correct schema."""
        embedding_cache.init_cache()

        conn = sqlite3.connect(temp_cache_dir)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='embeddings'"
        )
        table = cursor.fetchone()
        conn.close()

        assert table is not None, "embeddings table not created"

    def test_init_cache_idempotent(self, temp_cache_dir):
        """init_cache() can be called multiple times safely."""
        embedding_cache.init_cache()
        embedding_cache.init_cache()  # Should not raise
        assert temp_cache_dir.exists()


class TestCosineSimilarity:
    """Test cosine_similarity() on various inputs."""

    def test_cosine_similarity_identical_vectors(self):
        """Cosine similarity of identical vectors is 1.0."""
        vec = [1.0, 2.0, 3.0]
        sim = embedding_cache.cosine_similarity(vec, vec)
        assert abs(sim - 1.0) < 1e-6

    def test_cosine_similarity_orthogonal_vectors(self):
        """Cosine similarity of orthogonal vectors is 0.0."""
        vec1 = [1.0, 0.0]
        vec2 = [0.0, 1.0]
        sim = embedding_cache.cosine_similarity(vec1, vec2)
        assert abs(sim - 0.0) < 1e-6

    def test_cosine_similarity_opposite_vectors(self):
        """Cosine similarity of opposite vectors is -1.0."""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [-1.0, -2.0, -3.0]
        sim = embedding_cache.cosine_similarity(vec1, vec2)
        assert abs(sim - (-1.0)) < 1e-6

    def test_cosine_similarity_partial_overlap(self):
        """Cosine similarity with partial overlap is between 0 and 1."""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.7, 0.7, 0.0]
        sim = embedding_cache.cosine_similarity(vec1, vec2)
        assert 0.0 < sim < 1.0
        # dot = 1*0.7 + 0*0.7 + 0*0 = 0.7
        # norm1 = 1, norm2 = sqrt(0.7^2 + 0.7^2) = sqrt(0.98) = 0.9899...
        # sim = 0.7 / 0.9899... = 0.7071...
        assert abs(sim - 0.7071067811865476) < 1e-5

    def test_cosine_similarity_zero_vector(self):
        """Cosine similarity with zero vector returns 0.0."""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [0.0, 0.0, 0.0]
        sim = embedding_cache.cosine_similarity(vec1, vec2)
        assert sim == 0.0

    def test_cosine_similarity_empty_vectors(self):
        """Cosine similarity with empty vectors returns 0.0."""
        sim = embedding_cache.cosine_similarity([], [])
        assert sim == 0.0

    def test_cosine_similarity_mismatched_lengths(self):
        """Cosine similarity with mismatched lengths returns 0.0."""
        vec1 = [1.0, 2.0]
        vec2 = [1.0, 2.0, 3.0]
        sim = embedding_cache.cosine_similarity(vec1, vec2)
        assert sim == 0.0

    def test_cosine_similarity_normalized_unit_vectors(self):
        """Cosine similarity of normalized unit vectors."""
        # [1, 1] and [1, -1] are unit vectors (after normalization)
        vec1 = [1.0, 1.0]
        vec2 = [1.0, -1.0]
        # dot = 1 * 1 + 1 * (-1) = 0
        # norm1 = sqrt(2), norm2 = sqrt(2)
        # sim = 0 / 2 = 0
        sim = embedding_cache.cosine_similarity(vec1, vec2)
        assert abs(sim - 0.0) < 1e-6


class TestGetEmbeddingWithoutModel:
    """Test get_embedding() graceful fallback when model unavailable."""

    def test_get_embedding_fallback_on_import_error(self, temp_cache_dir):
        """get_embedding() returns None if sentence-transformers unavailable."""
        embedding_cache.init_cache()

        # Mock _load_model to return None (simulating ImportError)
        with mock.patch.object(embedding_cache, '_load_model', return_value=None):
            result = embedding_cache.get_embedding("test text")
            assert result is None

    def test_get_embedding_empty_text_returns_none(self, temp_cache_dir):
        """get_embedding() returns None for empty/whitespace text."""
        embedding_cache.init_cache()
        assert embedding_cache.get_embedding("") is None
        assert embedding_cache.get_embedding("   ") is None


class TestGetEmbeddingWithCache:
    """Test get_embedding() caching behavior (without actual model)."""

    def test_get_embedding_caches_result(self, temp_cache_dir):
        """get_embedding() stores and retrieves embeddings from cache."""
        embedding_cache.init_cache()

        # Mock _load_model and SentenceTransformer
        mock_embedding = [0.1, 0.2, 0.3, 0.4]

        def mock_load_model():
            mock_model = mock.Mock()
            mock_model.encode.return_value = [mock_embedding]
            return mock_model

        with mock.patch.object(embedding_cache, '_load_model', side_effect=mock_load_model):
            # First call: computes and caches
            result1 = embedding_cache.get_embedding("shopping cart")
            assert result1 is not None

            # Second call: should come from cache (mock won't be called)
            # Reset the mock to verify it's not called again
            embedding_cache._MODEL_INSTANCE = None
            embedding_cache._MODEL_FAILED = False

            # If retrieval is from cache, it will succeed even without the model
            with mock.patch.object(embedding_cache, '_load_model', return_value=None):
                result2 = embedding_cache.get_embedding("shopping cart")
                # Should get result from cache, not None
                assert result2 is not None

    def test_get_embedding_strips_whitespace(self, temp_cache_dir):
        """get_embedding() treats "text " and "text" as same cache key."""
        embedding_cache.init_cache()

        mock_embedding = [0.1, 0.2, 0.3, 0.4]

        def mock_load_model():
            mock_model = mock.Mock()
            mock_model.encode.return_value = [mock_embedding]
            return mock_model

        with mock.patch.object(embedding_cache, '_load_model', side_effect=mock_load_model):
            result1 = embedding_cache.get_embedding("test  ")
            assert result1 is not None

            # Reset model state
            embedding_cache._MODEL_INSTANCE = None
            embedding_cache._MODEL_FAILED = False

            # Retrieve without whitespace; should come from cache
            with mock.patch.object(embedding_cache, '_load_model', return_value=None):
                result2 = embedding_cache.get_embedding("test")
                assert result2 is not None


class TestCacheDatabase:
    """Test SQLite backend directly."""

    def test_cache_stores_embedding_blob(self, temp_cache_dir):
        """Cache stores embeddings as BLOB."""
        embedding_cache.init_cache()

        # Manually insert an embedding as blob
        import numpy as np
        test_embedding = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        test_bytes = test_embedding.tobytes()

        conn = sqlite3.connect(temp_cache_dir)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO embeddings (task_text, embedding) VALUES (?, ?)",
            ("test task", test_bytes)
        )
        conn.commit()
        conn.close()

        # Verify it's there
        conn = sqlite3.connect(temp_cache_dir)
        cursor = conn.cursor()
        cursor.execute("SELECT embedding FROM embeddings WHERE task_text = ?", ("test task",))
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        retrieved_bytes = row[0]
        retrieved = np.frombuffer(retrieved_bytes, dtype=np.float32)
        assert np.allclose(retrieved, test_embedding)

    def test_cache_timestamp_created(self, temp_cache_dir):
        """Cache tracks creation timestamp."""
        embedding_cache.init_cache()

        import numpy as np
        test_embedding = np.array([0.1, 0.2, 0.3], dtype=np.float32).tobytes()

        conn = sqlite3.connect(temp_cache_dir)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO embeddings (task_text, embedding) VALUES (?, ?)",
            ("test task", test_embedding)
        )
        conn.commit()

        # Verify created_at is set
        cursor.execute("SELECT created_at FROM embeddings WHERE task_text = ?", ("test task",))
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert row[0] is not None  # Timestamp should be set


class TestLoadModelLazyLoading:
    """Test lazy loading and caching of sentence-transformers model."""

    def test_load_model_returns_none_on_import_error(self):
        """_load_model() returns None if sentence-transformers not installed."""
        # Mock the import to fail
        import builtins
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "sentence_transformers":
                raise ImportError("sentence-transformers not installed")
            return original_import(name, *args, **kwargs)

        with mock.patch("builtins.__import__", side_effect=mock_import):
            embedding_cache._MODEL_INSTANCE = None
            embedding_cache._MODEL_FAILED = False
            result = embedding_cache._load_model()
            assert result is None
            assert embedding_cache._MODEL_FAILED

    def test_load_model_caches_instance(self):
        """_load_model() caches the model instance on repeated calls."""
        # Test the caching behavior by directly setting the cached instance
        embedding_cache._MODEL_INSTANCE = None
        embedding_cache._MODEL_FAILED = False

        # Create a mock model
        mock_model = mock.Mock()
        embedding_cache._MODEL_INSTANCE = mock_model

        # Call _load_model twice; both should return the cached instance
        result1 = embedding_cache._load_model()
        result2 = embedding_cache._load_model()

        assert result1 is mock_model
        assert result2 is mock_model
        assert result1 is result2
