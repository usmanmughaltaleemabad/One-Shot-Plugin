#!/usr/bin/env python3
"""
Embedding Cache — v1.0.0

Optional sentence-transformers-backed semantic embedding caching.
- Stores embeddings in SQLite (.beads/embedding_cache.db)
- Lazy-loads sentence-transformers (optional dependency)
- Graceful fallback if ImportError (e.g., GPU unavailable, model not downloaded)

Usage:
    from embedding_cache import init_cache, get_embedding, cosine_similarity

    init_cache()
    emb1 = get_embedding("shopping cart with line items")
    emb2 = get_embedding("cart with discount rules")
    if emb1 and emb2:
        sim = cosine_similarity(emb1, emb2)
        print(f"Similarity: {sim:.3f}")
    else:
        print("Embeddings unavailable (sentence-transformers not installed)")
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path
from typing import Any, List, Optional

# Path to cache database
CACHE_DB = Path(".beads") / "embedding_cache.db"

# Model name (all-MiniLM-L6-v2 is lightweight, suitable for semantic similarity)
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# Cached model instance (lazy-loaded)
_MODEL_INSTANCE: Optional[Any] = None
_MODEL_FAILED: bool = False  # Flag: tried to load, failed


def init_cache() -> None:
    """Initialize SQLite cache for embeddings.

    Creates .beads/embedding_cache.db if it doesn't exist.
    Schema: embeddings (task_text TEXT PRIMARY KEY, embedding BLOB, created_at TIMESTAMP)
    """
    CACHE_DB.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(CACHE_DB)
    cursor = conn.cursor()

    # Create table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS embeddings (
            task_text TEXT PRIMARY KEY,
            embedding BLOB NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def _load_model() -> Optional[Any]:
    """Load sentence-transformers model on first use (lazy loading).

    Returns:
        The SentenceTransformer model, or None if import fails.
    """
    global _MODEL_INSTANCE, _MODEL_FAILED

    if _MODEL_FAILED:
        return None

    if _MODEL_INSTANCE is not None:
        return _MODEL_INSTANCE

    try:
        from sentence_transformers import SentenceTransformer
        _MODEL_INSTANCE = SentenceTransformer(MODEL_NAME)
        return _MODEL_INSTANCE
    except ImportError:
        # sentence-transformers not installed
        _MODEL_FAILED = True
        return None
    except Exception as e:
        # Other failure (download timeout, disk space, etc.)
        # Mark as failed so we don't retry on every call
        _MODEL_FAILED = True
        return None


def get_embedding(task_text: str) -> Optional[List[float]]:
    """Get embedding from cache or compute.

    Args:
        task_text: Text to embed (e.g., feature description).

    Returns:
        List[float] if embedding found/computed, None if sentence-transformers unavailable.
    """
    if not task_text or not task_text.strip():
        return None

    task_text = task_text.strip()

    # Try cache first
    try:
        conn = sqlite3.connect(CACHE_DB)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT embedding FROM embeddings WHERE task_text = ?",
            (task_text,)
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            # Deserialize embedding from BLOB
            import numpy as np
            embedding_bytes = row[0]
            embedding = np.frombuffer(embedding_bytes, dtype=np.float32).tolist()
            return embedding
    except Exception:
        # Ignore cache read errors; fall through to compute
        pass

    # Not in cache; try to compute
    model = _load_model()
    if model is None:
        return None

    try:
        # Compute embedding
        embeddings = model.encode([task_text], convert_to_tensor=False)
        embedding = embeddings[0].tolist() if hasattr(embeddings[0], 'tolist') else list(embeddings[0])

        # Store in cache
        import numpy as np
        embedding_bytes = np.array(embedding, dtype=np.float32).tobytes()

        conn = sqlite3.connect(CACHE_DB)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO embeddings (task_text, embedding) VALUES (?, ?)",
            (task_text, embedding_bytes)
        )
        conn.commit()
        conn.close()

        return embedding
    except Exception:
        # Compute failed; return None
        return None


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Compute cosine similarity between two vectors.

    Args:
        vec1: First vector (list of floats).
        vec2: Second vector (list of floats).

    Returns:
        Cosine similarity in range [-1, 1]. Returns 0.0 if either vector is zero-length.
    """
    if not vec1 or not vec2:
        return 0.0

    if len(vec1) != len(vec2):
        return 0.0

    # Compute dot product
    dot_product = sum(a * b for a, b in zip(vec1, vec2))

    # Compute norms
    norm1 = sum(a * a for a in vec1) ** 0.5
    norm2 = sum(b * b for b in vec2) ** 0.5

    # Avoid division by zero
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0

    return dot_product / (norm1 * norm2)


if __name__ == "__main__":
    # Simple CLI test
    import argparse

    parser = argparse.ArgumentParser(description="Test embedding cache")
    parser.add_argument("--init", action="store_true", help="Initialize cache")
    parser.add_argument("--text1", type=str, help="First text to embed")
    parser.add_argument("--text2", type=str, help="Second text to embed")
    args = parser.parse_args()

    if args.init:
        init_cache()
        print(f"Cache initialized at {CACHE_DB}")

    if args.text1:
        init_cache()
        emb1 = get_embedding(args.text1)
        if emb1:
            print(f"Embedding 1 (len={len(emb1)}): {emb1[:5]}...")
        else:
            print("Embedding 1: unavailable (sentence-transformers not installed or failed)")

        if args.text2:
            emb2 = get_embedding(args.text2)
            if emb2:
                print(f"Embedding 2 (len={len(emb2)}): {emb2[:5]}...")
                sim = cosine_similarity(emb1, emb2)
                print(f"Cosine similarity: {sim:.4f}")
            else:
                print("Embedding 2: unavailable")
