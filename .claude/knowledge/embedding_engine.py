"""
Embedding Engine — v1.0.0

Wraps sentence-transformers with graceful fallback when not installed.
Provides cosine similarity computation for semantic search.

Uses all-MiniLM-L6-v2 model: 384-dim embeddings, ~86MB on disk.
Lazy loads model on first use to avoid startup overhead.

API:
    engine = EmbeddingEngine()
    vec1 = engine.embed("shopping cart with line items")
    vec2 = engine.embed("e-commerce cart items")
    sim = engine.similarity(vec1, vec2)  # 0.0-1.0

Graceful Fallback:
    If sentence-transformers is unavailable:
    - embed() returns None
    - similarity() returns 0.0 for None inputs
    - Search falls back to keyword matching
"""

from __future__ import annotations

import logging
import math
from typing import Optional, List

logger = logging.getLogger(__name__)


class EmbeddingEngine:
    """Semantic embedding with optional sentence-transformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize engine (lazy-loads model on first embed)."""
        self.model_name = model_name
        self._model = None
        self._tokenizer = None
        self._available = self._check_availability()

    def _check_availability(self) -> bool:
        """Check if sentence-transformers is installed."""
        try:
            import sentence_transformers  # noqa: F401
            return True
        except ImportError:
            logger.debug(
                "sentence-transformers not installed; "
                "embedding disabled (fallback to keyword search)"
            )
            return False

    def _load_model(self) -> None:
        """Lazy-load the embedding model on first use."""
        if self._model is not None:
            return
        if not self._available:
            return

        try:
            from sentence_transformers import SentenceTransformer
            logger.debug(f"Loading embedding model {self.model_name}...")
            self._model = SentenceTransformer(self.model_name)
            logger.debug(f"Model loaded: {self.model_name}")
        except Exception as e:
            logger.warning(f"Failed to load embedding model: {e}")
            self._available = False
            self._model = None

    def embed(self, text: str) -> Optional[List[float]]:
        """
        Embed text to 384-dim vector (all-MiniLM-L6-v2).

        Returns:
            384-element list if available, None if sentence-transformers unavailable.
        """
        if not text or not isinstance(text, str):
            return None

        if not self._available:
            return None

        self._load_model()
        if self._model is None:
            return None

        try:
            # Convert to list to ensure JSON serialization
            embedding = self._model.encode(text, convert_to_tensor=False)
            return embedding.tolist() if hasattr(embedding, "tolist") else list(embedding)
        except Exception as e:
            logger.warning(f"Embedding failed for text: {e}")
            return None

    @staticmethod
    def cosine_similarity(vec1: Optional[List[float]], vec2: Optional[List[float]]) -> float:
        """
        Compute cosine similarity between two vectors.

        Returns:
            Similarity score 0.0-1.0 (1.0 = identical).
            Returns 0.0 if either vector is None or empty.
        """
        if vec1 is None or vec2 is None:
            return 0.0
        if not vec1 or not vec2:
            return 0.0
        if len(vec1) != len(vec2):
            return 0.0

        # Compute dot product
        dot_product = sum(a * b for a, b in zip(vec1, vec2))

        # Compute magnitudes
        mag1 = math.sqrt(sum(a * a for a in vec1))
        mag2 = math.sqrt(sum(b * b for b in vec2))

        if mag1 == 0.0 or mag2 == 0.0:
            return 0.0

        return dot_product / (mag1 * mag2)

    def similarity(self, vec1: Optional[List[float]], vec2: Optional[List[float]]) -> float:
        """Wrapper around cosine_similarity for instance method."""
        return self.cosine_similarity(vec1, vec2)

    def batch_embed(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Embed multiple texts efficiently.

        Returns:
            List of embeddings (or None for unavailable texts).
        """
        if not self._available:
            return [None] * len(texts)

        self._load_model()
        if self._model is None:
            return [None] * len(texts)

        try:
            embeddings = self._model.encode(texts, convert_to_tensor=False)
            return [
                e.tolist() if hasattr(e, "tolist") else list(e)
                for e in embeddings
            ]
        except Exception as e:
            logger.warning(f"Batch embedding failed: {e}")
            return [None] * len(texts)

    def is_available(self) -> bool:
        """Check if embeddings are available."""
        return self._available
