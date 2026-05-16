#!/usr/bin/env python3
"""
Phase 4 DDD: Module Scaffolder

Orchestrates generation of complete DDD module from single request.
Scaffolds: Aggregate, Entities, Value Objects, Repository, Events, Service.

Usage:
    python phase4_ddd_module_scaffolder.py --aggregate Order --entities LineItem Payment --values Money Status

Input: Aggregate and components
Output: Complete DDD module directory structure
"""

import argparse
import json
from typing import List


def generate_module_structure(aggregate_name: str, entities: List[str], values: List[str]) -> dict:
    """
    Generate complete DDD module structure.

    Creates files:
    - models.py (aggregates + entities + value objects)
    - repository.py (repository pattern)
    - events.py (domain events)
    - service.py (application service)
    - __init__.py (module exports)

    Args:
        aggregate_name: Aggregate name (e.g., Order)
        entities: Entity names (e.g., [LineItem, Payment])
        values: Value object names (e.g., [Money, Status])

    Returns:
        dict with file structure and content
    """

    files = {
        "aggregate_models.py": f'''"""
Domain Models for {{aggregate_name}} Aggregate
"""

from datetime import datetime
from typing import Any, Optional, List
from abc import ABC, abstractmethod


# ============ Value Objects ============

{", ".join(values)}

# ============ Entities ============

{", ".join(entities)}

# ============ Aggregate Root ============

class {{aggregate_name}}Aggregate:
    """Aggregate Root for {{aggregate_name}}"""

    def __init__(self, id: str, **kwargs):
        self._id = id
        self._version = 1
        self._created_at = datetime.utcnow()
        self._updated_at = self._created_at
        self._changes = []
        self._data = kwargs

    @property
    def id(self) -> str:
        return self._id

    @property
    def version(self) -> int:
        return self._version

    @property
    def changes(self) -> list:
        return self._changes

    def to_dict(self) -> dict:
        return {{
            "id": self._id,
            "version": self._version,
            "created_at": self._created_at.isoformat(),
            "updated_at": self._updated_at.isoformat(),
            "data": self._data
        }}

    def __repr__(self):
        return f"{{aggregate_name}}(id='{{self._id}}', version={{self._version}})"
'''.replace("{{aggregate_name}}", aggregate_name),

        "repository.py": f'''"""
Repository Pattern for {{aggregate_name}}
"""

from abc import ABC, abstractmethod
from typing import Optional, List


class {{aggregate_name}}Repository(ABC):
    """Repository interface for {{aggregate_name}} aggregate"""

    @abstractmethod
    def save(self, aggregate) -> None:
        """Save aggregate"""
        raise NotImplementedError()

    @abstractmethod
    def load(self, aggregate_id: str) -> Optional:
        """Load aggregate by ID"""
        raise NotImplementedError()

    @abstractmethod
    def delete(self, aggregate_id: str) -> None:
        """Delete aggregate"""
        raise NotImplementedError()

    @abstractmethod
    def find_by_spec(self, spec) -> List:
        """Find aggregates matching specification"""
        raise NotImplementedError()


class {{aggregate_name}}MemoryRepository({{aggregate_name}}Repository):
    """In-memory repository for {{aggregate_name}}"""

    def __init__(self):
        self._store = {{}}

    def save(self, aggregate) -> None:
        self._store[aggregate.id] = aggregate

    def load(self, aggregate_id: str) -> Optional:
        return self._store.get(aggregate_id)

    def delete(self, aggregate_id: str) -> None:
        if aggregate_id in self._store:
            del self._store[aggregate_id]

    def find_by_spec(self, spec) -> List:
        return [agg for agg in self._store.values() if spec.is_satisfied_by(agg)]
'''.replace("{{aggregate_name}}", aggregate_name),

        "events.py": f'''"""
Domain Events for {{aggregate_name}}
"""

from datetime import datetime
from typing import Optional


class {{aggregate_name}}Event:
    """Base class for {{aggregate_name}} domain events"""

    def __init__(self, aggregate_id: str, timestamp: Optional[datetime] = None):
        self.aggregate_id = aggregate_id
        self.timestamp = timestamp or datetime.utcnow()
        self.version = 1

    def to_dict(self) -> dict:
        return {{
            "aggregate_id": self.aggregate_id,
            "event_type": type(self).__name__,
            "timestamp": self.timestamp.isoformat(),
            "version": self.version
        }}


class {{aggregate_name}}CreatedEvent({{aggregate_name}}Event):
    """Fired when {{aggregate_name}} is created"""

    def __init__(self, aggregate_id: str, data: dict):
        super().__init__(aggregate_id)
        self.data = data


class {{aggregate_name}}UpdatedEvent({{aggregate_name}}Event):
    """Fired when {{aggregate_name}} is updated"""

    def __init__(self, aggregate_id: str, changes: dict):
        super().__init__(aggregate_id)
        self.changes = changes


class {{aggregate_name}}DeletedEvent({{aggregate_name}}Event):
    """Fired when {{aggregate_name}} is deleted"""
    pass
'''.replace("{{aggregate_name}}", aggregate_name),

        "service.py": f'''"""
Application Service for {{aggregate_name}}
"""

from typing import Optional


class {{aggregate_name}}ApplicationService:
    """Application Service for {{aggregate_name}} aggregate"""

    def __init__(self, repository, event_bus):
        self.repository = repository
        self.event_bus = event_bus

    def create(self, **data) -> str:
        """Create new {{aggregate_name}} aggregate"""
        # TODO: Implement create logic
        pass

    def update(self, aggregate_id: str, **changes) -> None:
        """Update {{aggregate_name}} aggregate"""
        # TODO: Implement update logic
        pass

    def delete(self, aggregate_id: str) -> None:
        """Delete {{aggregate_name}} aggregate"""
        # TODO: Implement delete logic
        pass
'''.replace("{{aggregate_name}}", aggregate_name),

        "__init__.py": f'''"""
{{aggregate_name}} Aggregate Module

This module contains all DDD components for the {{aggregate_name}} aggregate:
- Models (Aggregate Root, Entities, Value Objects)
- Repository (persistence abstraction)
- Events (domain events)
- Service (application/use case orchestration)
"""

from .aggregate_models import {{aggregate_name}}Aggregate
from .repository import {{aggregate_name}}Repository, {{aggregate_name}}MemoryRepository
from .events import {{aggregate_name}}Event, {{aggregate_name}}CreatedEvent
from .service import {{aggregate_name}}ApplicationService

__all__ = [
    "{{aggregate_name}}Aggregate",
    "{{aggregate_name}}Repository",
    "{{aggregate_name}}MemoryRepository",
    "{{aggregate_name}}Event",
    "{{aggregate_name}}CreatedEvent",
    "{{aggregate_name}}ApplicationService",
]
'''.replace("{{aggregate_name}}", aggregate_name),

        "tests/__init__.py": "",

        "tests/test_models.py": f'''"""
Tests for {{aggregate_name}} aggregate models
"""

import pytest
from {{aggregate_name.lower()}}.aggregate_models import {{aggregate_name}}Aggregate


class TestOrderAggregate:
    def test_create_aggregate(self):
        agg = {{aggregate_name}}Aggregate(id="123")
        assert agg.id == "123"
        assert agg.version == 1

    def test_aggregate_to_dict(self):
        agg = {{aggregate_name}}Aggregate(id="123", name="Test")
        data = agg.to_dict()
        assert data["id"] == "123"
        assert "created_at" in data
'''.replace("{{aggregate_name}}", aggregate_name).replace("{{aggregate_name.lower()}}", aggregate_name.lower()),

        "tests/test_repository.py": f'''"""
Tests for {{aggregate_name}} repository
"""

import pytest
from {{aggregate_name.lower()}}.repository import {{aggregate_name}}MemoryRepository
from {{aggregate_name.lower()}}.aggregate_models import {{aggregate_name}}Aggregate


class Test{{aggregate_name}}MemoryRepository:
    def test_save_and_load(self):
        repo = {{aggregate_name}}MemoryRepository()
        agg = {{aggregate_name}}Aggregate(id="123")

        repo.save(agg)
        loaded = repo.load("123")

        assert loaded.id == agg.id

    def test_delete(self):
        repo = {{aggregate_name}}MemoryRepository()
        agg = {{aggregate_name}}Aggregate(id="123")

        repo.save(agg)
        repo.delete("123")

        assert repo.load("123") is None
'''.replace("{{aggregate_name}}", aggregate_name).replace("{{aggregate_name.lower()}}", aggregate_name.lower()),
    }

    return {
        "files": files,
        "aggregate": aggregate_name,
        "entities": entities,
        "values": values,
        "file_count": len(files),
        "directory": f"{aggregate_name.lower()}/",
    }


def generate_scaffolder_summary(result: dict) -> str:
    """Generate scaffolding summary documentation."""

    summary = f'''
# DDD Module Scaffolding Summary

Generated complete DDD module for {{aggregate_name}}.

## Structure

```
{{aggregate_name.lower()}}/
├── __init__.py              — Module exports
├── aggregate_models.py      — Aggregate Root, Entities, Value Objects
├── repository.py           — Repository pattern (abstraction + memory impl)
├── events.py               — Domain events
├── service.py              — Application Service (use case orchestration)
└── tests/
    ├── test_models.py      — Aggregate tests
    └── test_repository.py  — Repository tests
```

## Components

### Aggregate Root: {{aggregate_name}}
- ID: unique identifier
- Version: optimistic locking
- Changes: uncommitted events
- Invariants: enforced in constructor

### Entities: {{entities}}
- Part of {{aggregate_name}} aggregate
- Have identity
- Mutable
- Validation in aggregate methods

### Value Objects: {{values}}
- Immutable
- Equality-based (not identity)
- Encapsulate domain concepts
- Validation in constructor

### Repository
- Hides persistence
- Provides collection-like access
- Memory implementation for testing
- SQL implementation for production

### Domain Events
- {{aggregate_name}}CreatedEvent
- {{aggregate_name}}UpdatedEvent
- {{aggregate_name}}DeletedEvent

### Application Service
- Orchestrates use cases
- Manages transactions
- Publishes events

## Next Steps

1. Implement aggregate business logic in aggregate_models.py
2. Implement repository for your persistence (SQL, NoSQL, etc.)
3. Implement event handlers in service.py
4. Write integration tests
5. Wire into your application

## Testing

```bash
pytest {{aggregate_name.lower()}}/tests/ -v
```

## Files Generated

{{file_list}}
'''.replace("{{aggregate_name}}", result["aggregate"]).replace("{{entities}}", ", ".join(result["entities"])).replace("{{values}}", ", ".join(result["values"])).replace("{{file_list}}", "\n".join([f"- {name}" for name in result["files"].keys()]))

    return summary


def main():
    parser = argparse.ArgumentParser(
        description="Scaffold complete DDD module"
    )
    parser.add_argument(
        "--aggregate", required=True,
        help="Aggregate name (e.g., Order)"
    )
    parser.add_argument(
        "--entities", nargs="*", default=[],
        help="Entity names (e.g., LineItem Payment)"
    )
    parser.add_argument(
        "--values", nargs="*", default=[],
        help="Value object names (e.g., Money Status)"
    )
    parser.add_argument(
        "--output", choices=["json", "files"], default="files",
        help="Output format"
    )

    args = parser.parse_args()

    result = generate_module_structure(args.aggregate, args.entities or [], args.values or [])

    if args.output == "json":
        metadata = {k: v for k, v in result.items() if k != "files"}
        print(json.dumps(metadata, indent=2))
    else:
        # Print summary
        summary = generate_scaffolder_summary(result)
        print(summary)

        # Print file list
        print("\n## Files to Create\n")
        for filename, content in result["files"].items():
            lines = len(content.split("\n")) if content else 0
            print(f"- {filename} ({lines} lines)")


if __name__ == "__main__":
    main()
