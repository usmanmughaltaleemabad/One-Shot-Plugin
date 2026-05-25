"""
Knowledge Store — v1.0.0

Primary storage: SQLite with vector table (if available)
Fallback: JSONL for systems without sqlite3.ext.

Manages fact lifecycle:
  - add_fact(): Store with embedding
  - search(): Semantic + keyword search
  - emit_fact(): Create fact from string
  - decay_facts(): Age-score facts (1.0 → 0.0 over 30 days)
  - consolidate_facts(): Merge similar facts (>0.85 similarity)
  - get_stats(): Usage metrics

API:
    store = KnowledgeStore(db_path=".beads/knowledge.db")
    fact_id = store.emit_fact(
        "Order with 5 entities: avg cost $0.78",
        fact_type="cost_calibration"
    )
    similar = store.search("e-commerce 4 entities", top_k=5)
    stats = store.get_stats()
"""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

try:
    from .fact_schema import KnowledgeFact, FactType, FactMetadata
    from .embedding_engine import EmbeddingEngine
except ImportError:
    # Fallback for direct imports
    from fact_schema import KnowledgeFact, FactType, FactMetadata
    from embedding_engine import EmbeddingEngine

logger = logging.getLogger(__name__)


class KnowledgeStore:
    """Semantic knowledge store with SQLite + JSONL fallback."""

    def __init__(
        self,
        db_path: Optional[Path] = None,
        jsonl_path: Optional[Path] = None,
        use_sqlite: bool = True,
    ):
        """
        Initialize knowledge store.

        Args:
            db_path: SQLite database path (default: .beads/knowledge.db)
            jsonl_path: JSONL fallback path (default: .beads/knowledge.jsonl)
            use_sqlite: Try SQLite first, fallback to JSONL
        """
        self.db_path = Path(db_path or ".beads/knowledge.db")
        self.jsonl_path = Path(jsonl_path or ".beads/knowledge.jsonl")
        self.use_sqlite = use_sqlite
        self.embedding_engine = EmbeddingEngine()
        self._conn = None
        self._use_jsonl = False

        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Try to initialize SQLite
        if self.use_sqlite:
            self._init_sqlite()
        else:
            self._use_jsonl = True

    def _init_sqlite(self) -> None:
        """Initialize SQLite database with vector table."""
        try:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
            cursor = self._conn.cursor()

            # Create facts table with embedding (stored as JSON)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_facts (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    embedding TEXT,
                    created_at TEXT NOT NULL,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    last_used TEXT,
                    decay_score REAL DEFAULT 1.0
                )
            """)

            # Create index on type for faster queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_type ON knowledge_facts(type)
            """)

            self._conn.commit()
            logger.debug(f"SQLite store initialized: {self.db_path}")
        except Exception as e:
            logger.warning(f"SQLite initialization failed, falling back to JSONL: {e}")
            self._use_jsonl = True
            self._conn = None

    def add_fact(self, fact: KnowledgeFact) -> str:
        """
        Add a fact to the store.

        Args:
            fact: KnowledgeFact to store

        Returns:
            Fact ID
        """
        # Generate embedding if not present and available
        if fact.embedding is None and self.embedding_engine.is_available():
            fact.embedding = self.embedding_engine.embed(fact.content)

        if self._use_jsonl or self._conn is None:
            self._add_fact_jsonl(fact)
        else:
            self._add_fact_sqlite(fact)

        return fact.id

    def _add_fact_sqlite(self, fact: KnowledgeFact) -> None:
        """Store fact in SQLite."""
        try:
            cursor = self._conn.cursor()
            embedding_json = (
                json.dumps(fact.embedding) if fact.embedding else None
            )
            cursor.execute("""
                INSERT OR REPLACE INTO knowledge_facts (
                    id, type, content, embedding,
                    created_at, success_count, failure_count, last_used, decay_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                fact.id,
                fact.type.value,
                fact.content,
                embedding_json,
                fact.metadata.created_at.isoformat(),
                fact.metadata.success_count,
                fact.metadata.failure_count,
                fact.metadata.last_used.isoformat() if fact.metadata.last_used else None,
                fact.metadata.decay_score,
            ))
            self._conn.commit()
        except Exception as e:
            logger.error(f"Failed to add fact to SQLite: {e}")
            self._use_jsonl = True
            self._add_fact_jsonl(fact)

    def _add_fact_jsonl(self, fact: KnowledgeFact) -> None:
        """Store fact in JSONL fallback."""
        try:
            with open(self.jsonl_path, "a", encoding="utf-8") as f:
                f.write(fact.to_json() + "\n")
        except Exception as e:
            logger.error(f"Failed to add fact to JSONL: {e}")

    def search(
        self,
        query: str,
        top_k: int = 5,
        fact_type: Optional[FactType] = None,
        min_decay_score: float = 0.0,
    ) -> List[KnowledgeFact]:
        """
        Search knowledge store semantically.

        Args:
            query: Search query text
            top_k: Number of results to return
            fact_type: Filter by fact type (optional)
            min_decay_score: Only return facts with decay_score >= this

        Returns:
            List of matching facts, sorted by relevance and decay
        """
        if not query or not isinstance(query, str):
            return []

        facts = self._load_all_facts()
        if not facts:
            return []

        # Compute similarity for each fact
        query_embedding = self.embedding_engine.embed(query)
        scored_facts = []

        for fact in facts:
            # Apply filters
            if fact_type and fact.type != fact_type:
                continue
            if fact.metadata.decay_score < min_decay_score:
                continue

            # Compute semantic similarity if embeddings available
            if query_embedding and fact.embedding:
                semantic_sim = self.embedding_engine.similarity(
                    query_embedding, fact.embedding
                )
            else:
                semantic_sim = 0.0

            # Apply decay scoring: relevance * decay_score
            final_score = semantic_sim * fact.metadata.decay_score

            scored_facts.append((fact, final_score))

        # Sort by score, highest first
        scored_facts.sort(key=lambda x: x[1], reverse=True)

        return [fact for fact, _score in scored_facts[:top_k]]

    def emit_fact(
        self,
        content: str,
        fact_type: str = "entity_pattern",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create and store a fact (convenience method).

        Args:
            content: Fact text
            fact_type: Type (default: entity_pattern)
            metadata: Optional metadata dict (success_count, failure_count, etc.)

        Returns:
            Fact ID
        """
        import uuid
        fact_id = f"kf-{uuid.uuid4().hex[:12]}"

        # Create fact with optional metadata overrides
        fact_meta = FactMetadata(created_at=datetime.now())
        if metadata:
            if "success_count" in metadata:
                fact_meta.success_count = metadata["success_count"]
            if "failure_count" in metadata:
                fact_meta.failure_count = metadata["failure_count"]

        fact = KnowledgeFact(
            id=fact_id,
            type=FactType(fact_type),
            content=content,
            metadata=fact_meta,
        )

        return self.add_fact(fact)

    def get_stats(self) -> Dict[str, Any]:
        """Get store statistics."""
        facts = self._load_all_facts()

        stats = {
            "total_facts": len(facts),
            "by_type": {},
            "memory_usage_bytes": 0,
            "avg_decay_score": 0.0,
        }

        for fact_type in FactType:
            count = sum(1 for f in facts if f.type == fact_type)
            stats["by_type"][fact_type.value] = count

        if facts:
            stats["avg_decay_score"] = sum(
                f.metadata.decay_score for f in facts
            ) / len(facts)
            # Rough estimate: ~1.5KB per fact
            stats["memory_usage_bytes"] = len(facts) * 1500

        return stats

    def decay_facts(self, days_old: int = 30) -> int:
        """
        Update decay scores based on age.

        Facts age from 1.0 (fresh) to 0.0 (stale) over 30 days.

        Returns:
            Number of facts updated
        """
        facts = self._load_all_facts()
        if not facts:
            return 0

        now = datetime.now()
        cutoff = now - timedelta(days=days_old)
        updated = 0

        for fact in facts:
            age_days = (now - fact.metadata.created_at).days
            if age_days > days_old:
                fact.metadata.decay_score = 0.0
            else:
                # Linear decay: fresh (0 days) = 1.0, stale (30 days) = 0.0
                fact.metadata.decay_score = 1.0 - (age_days / days_old)

            # Store updated fact
            self.add_fact(fact)
            updated += 1

        return updated

    def consolidate_facts(
        self,
        similarity_threshold: float = 0.85,
        keep_top_n: int = 10,
    ) -> Dict[str, int]:
        """
        Merge similar facts and keep only top-N by relevance.

        Groups facts by type, merges similar ones (> threshold),
        keeps top-N most successful.

        Returns:
            {"merged_count": int, "archived_count": int}
        """
        facts = self._load_all_facts()
        if not facts:
            return {"merged_count": 0, "archived_count": 0}

        merged_count = 0
        archived_count = 0

        # Group by type
        by_type = {}
        for fact in facts:
            if fact.type not in by_type:
                by_type[fact.type] = []
            by_type[fact.type].append(fact)

        # Process each type
        for fact_type, type_facts in by_type.items():
            # Merge similar facts
            merged = self._merge_similar_facts(
                type_facts, similarity_threshold
            )
            merged_count += len(type_facts) - len(merged)

            # Keep top-N by success
            sorted_facts = sorted(
                merged,
                key=lambda f: f.metadata.success_count,
                reverse=True,
            )

            # Archive low-scoring facts
            for fact in sorted_facts[keep_top_n:]:
                # Mark for archival (set decay to 0)
                fact.metadata.decay_score = 0.0
                self.add_fact(fact)
                archived_count += 1

            # Update high-scoring facts
            for fact in sorted_facts[:keep_top_n]:
                self.add_fact(fact)

        return {
            "merged_count": merged_count,
            "archived_count": archived_count,
        }

    def _merge_similar_facts(
        self,
        facts: List[KnowledgeFact],
        threshold: float = 0.85,
    ) -> List[KnowledgeFact]:
        """Merge facts that are highly similar (> threshold)."""
        if not facts or len(facts) < 2:
            return facts

        kept = []
        merged_ids = set()

        for fact in facts:
            if fact.id in merged_ids:
                continue

            # Find all similar facts
            similar = [fact]
            for other in facts:
                if other.id == fact.id or other.id in merged_ids:
                    continue

                if (
                    fact.embedding and other.embedding and
                    self.embedding_engine.similarity(
                        fact.embedding, other.embedding
                    ) > threshold
                ):
                    similar.append(other)
                    merged_ids.add(other.id)

            # Merge similar facts: combine success/failure counts
            if len(similar) > 1:
                merged_fact = similar[0]
                for other in similar[1:]:
                    merged_fact.metadata.success_count += (
                        other.metadata.success_count
                    )
                    merged_fact.metadata.failure_count += (
                        other.metadata.failure_count
                    )
                    merged_ids.add(other.id)

            kept.append(similar[0])

        return kept

    def _load_all_facts(self) -> List[KnowledgeFact]:
        """Load all facts from storage."""
        if self._use_jsonl or self._conn is None:
            return self._load_facts_jsonl()
        return self._load_facts_sqlite()

    def _load_facts_sqlite(self) -> List[KnowledgeFact]:
        """Load all facts from SQLite."""
        try:
            cursor = self._conn.cursor()
            cursor.execute("SELECT * FROM knowledge_facts")
            rows = cursor.fetchall()

            facts = []
            for row in rows:
                metadata = FactMetadata(
                    created_at=datetime.fromisoformat(row["created_at"]),
                    success_count=row["success_count"],
                    failure_count=row["failure_count"],
                    last_used=(
                        datetime.fromisoformat(row["last_used"])
                        if row["last_used"]
                        else None
                    ),
                    decay_score=row["decay_score"],
                )

                embedding = None
                if row["embedding"]:
                    try:
                        embedding = json.loads(row["embedding"])
                    except json.JSONDecodeError:
                        pass

                fact = KnowledgeFact(
                    id=row["id"],
                    type=FactType(row["type"]),
                    content=row["content"],
                    embedding=embedding,
                    metadata=metadata,
                )
                facts.append(fact)

            return facts
        except Exception as e:
            logger.error(f"Failed to load facts from SQLite: {e}")
            return []

    def _load_facts_jsonl(self) -> List[KnowledgeFact]:
        """Load all facts from JSONL."""
        if not self.jsonl_path.exists():
            return []

        facts = []
        try:
            with open(self.jsonl_path, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        fact = KnowledgeFact.from_json(line)
                        facts.append(fact)
                    except json.JSONDecodeError:
                        logger.debug(f"Skipping invalid JSON line: {line}")
        except Exception as e:
            logger.error(f"Failed to load facts from JSONL: {e}")

        return facts

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
