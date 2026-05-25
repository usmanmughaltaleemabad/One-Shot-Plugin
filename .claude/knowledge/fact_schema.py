"""
Knowledge Fact Schema — v1.0.0

Defines the data structures for storing and managing learned facts from
generations and failures. Facts are tagged with types (entity patterns,
error recoveries, cost estimates) and embeddable with semantic vectors.

Fact Lifecycle:
  1. Emit: Generated during successful generation (stage 8)
  2. Search: Retrieved semantically on new generation (stage 0)
  3. Decay: Age-scored over 30 days (older facts less relevant)
  4. Consolidate: Merge similar facts (>0.85 similarity) daily

Example:
    fact = KnowledgeFact(
        id="kf-001",
        type=FactType.entity_pattern,
        content="Order with 5 entities: avg cost $0.78",
        embedding=None,  # Set by embedding_engine
        metadata=FactMetadata(
            created_at=datetime.now(),
            success_count=3,
            failure_count=0,
        )
    )
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class FactType(str, Enum):
    """Category tags for different types of learned facts."""
    entity_pattern = "entity_pattern"
    error_recovery = "error_recovery"
    cost_calibration = "cost_calibration"
    api_design = "api_design"


@dataclass
class FactMetadata:
    """Metadata tracking and decay scoring for a fact."""
    created_at: datetime
    success_count: int = 0
    failure_count: int = 0
    last_used: Optional[datetime] = None
    decay_score: float = 1.0  # 1.0 (fresh) → 0.0 (stale) over 30 days

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> FactMetadata:
        """Reconstruct from dict, handling datetime strings."""
        created_at = d.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        last_used = d.get("last_used")
        if isinstance(last_used, str):
            last_used = datetime.fromisoformat(last_used)

        return cls(
            created_at=created_at,
            success_count=d.get("success_count", 0),
            failure_count=d.get("failure_count", 0),
            last_used=last_used,
            decay_score=float(d.get("decay_score", 1.0)),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict, converting datetimes to ISO strings."""
        return {
            "created_at": self.created_at.isoformat(),
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "decay_score": self.decay_score,
        }


@dataclass
class KnowledgeFact:
    """A single learned fact with semantic embedding."""
    id: str
    type: FactType
    content: str
    embedding: Optional[List[float]] = None
    metadata: FactMetadata = field(default_factory=lambda: FactMetadata(
        created_at=datetime.now()
    ))

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> KnowledgeFact:
        """Reconstruct from dict."""
        type_val = d.get("type")
        if isinstance(type_val, str):
            type_val = FactType(type_val)

        metadata_dict = d.get("metadata")
        if isinstance(metadata_dict, dict):
            metadata = FactMetadata.from_dict(metadata_dict)
        else:
            metadata = FactMetadata(created_at=datetime.now())

        return cls(
            id=d.get("id", ""),
            type=type_val,
            content=d.get("content", ""),
            embedding=d.get("embedding"),
            metadata=metadata,
        )

    def to_dict(self, include_embedding: bool = True) -> Dict[str, Any]:
        """Serialize to dict."""
        result = {
            "id": self.id,
            "type": self.type.value,
            "content": self.content,
            "metadata": self.metadata.to_dict(),
        }
        if include_embedding and self.embedding is not None:
            result["embedding"] = self.embedding
        return result

    def to_json(self, include_embedding: bool = True) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(include_embedding=include_embedding))

    @classmethod
    def from_json(cls, json_str: str) -> KnowledgeFact:
        """Deserialize from JSON string."""
        d = json.loads(json_str)
        return cls.from_dict(d)

    def __repr__(self) -> str:
        embedding_str = (
            f"[{len(self.embedding)} dims]" if self.embedding else "None"
        )
        return (
            f"KnowledgeFact(id={self.id!r}, type={self.type.value}, "
            f"embedding={embedding_str}, success={self.metadata.success_count})"
        )
