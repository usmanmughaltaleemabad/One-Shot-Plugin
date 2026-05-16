#!/usr/bin/env python3
"""
Phase 4 DDD: Aggregate Design Generator

Generates Aggregate Root pattern with entity composition, value objects, and invariant enforcement.
Takes domain concept and generates: Aggregate Root, Entities, Value Objects, Repository interface.

Usage:
    python phase4_ddd_aggregate_design.py --aggregate Order --entities LineItem Payment --values Money Status

Input: Domain aggregate concept (e.g., Order, ShoppingCart, BlogPost)
Output: Complete Aggregate pattern with invariant enforcement
"""

import argparse
import json
import sys
from datetime import datetime
from typing import Any


def generate_aggregate_root(aggregate_name: str, entities: list, value_objects: list) -> dict:
    """
    Generate Aggregate Root class with composition and invariant enforcement.

    Args:
        aggregate_name: Name of the aggregate (e.g., Order)
        entities: List of entity names within aggregate (e.g., [LineItem, Payment])
        value_objects: List of value object names (e.g., [Money, Status])

    Returns:
        dict with code sections for models.py, aggregates.py, repository.py
    """

    # Generate Value Objects first
    value_object_code = "\n".join([
        f"""
class {vo}:
    \"\"\"Value Object: {vo}\"\"\"
    def __init__(self, value: Any):
        self._validate(value)
        self._value = value

    def _validate(self, value: Any) -> None:
        if not value:
            raise ValueError(f"{vo} cannot be empty")

    @property
    def value(self) -> Any:
        return self._value

    def __eq__(self, other):
        if not isinstance(other, {vo}):
            return False
        return self._value == other._value

    def __hash__(self):
        return hash(self._value)

    def __repr__(self):
        return f"{vo}({self._value!r})"
"""
        for vo in value_objects
    ])

    # Generate Entities
    entity_code = "\n".join([
        f"""
class {entity}:
    \"\"\"Entity: {entity} (part of {aggregate_name} aggregate)\"\"\"
    def __init__(self, id: str, **kwargs):
        self._id = id
        self._data = kwargs
        self._validate_invariants()

    @property
    def id(self) -> str:
        return self._id

    def _validate_invariants(self) -> None:
        \"\"\"Validate entity invariants after state change\"\"\"
        if not self._id:
            raise ValueError(f"{entity} must have an ID")

    def to_dict(self) -> dict:
        return {{"id": self._id, **self._data}}

    def __eq__(self, other):
        if not isinstance(other, {entity}):
            return False
        return self._id == other._id

    def __hash__(self):
        return hash(self._id)
"""
        for entity in entities
    ])

    # Generate Aggregate Root
    aggregate_code = f"""
class {aggregate_name}Aggregate:
    \"\"\"
    Aggregate Root: {aggregate_name}

    Enforces business invariants and coordinates changes across Entities and Value Objects.
    All external references use the Aggregate ID, not internal entity references.
    \"\"\"

    def __init__(self, id: str, **kwargs):
        self._id = id
        self._version = 1
        self._created_at = datetime.utcnow()
        self._updated_at = self._created_at
        self._changes: list = []
        self._data = kwargs
        self._entities = {{}}
        self._value_objects = {{}}
        self._validate_invariants()

    @property
    def id(self) -> str:
        \"\"\"Aggregate ID: external identifier\"\"\"
        return self._id

    @property
    def version(self) -> int:
        \"\"\"Version for optimistic locking\"\"\"
        return self._version

    @property
    def changes(self) -> list:
        \"\"\"Uncommitted domain events\"\"\"
        return self._changes

    def add_entity(self, entity_type: str, entity_id: str, **data) -> None:
        \"\"\"
        Add entity to aggregate (enforces composition).

        Args:
            entity_type: Type of entity (e.g., 'LineItem', 'Payment')
            entity_id: Unique entity ID within aggregate
            **data: Entity data

        Raises:
            ValueError: If invariants violated
        \"\"\"
        if not entity_id:
            raise ValueError(f"Entity ID required for {{entity_type}}")

        key = f"{{entity_type}}_{{entity_id}}"
        self._entities[key] = {{"type": entity_type, "id": entity_id, **data}}
        self._record_change(f"EntityAdded", {{"type": entity_type, "id": entity_id}})
        self._validate_invariants()

    def set_value_object(self, vo_name: str, value: Any) -> None:
        \"\"\"
        Set value object (immutable replacement).

        Args:
            vo_name: Name of value object (e.g., 'Status', 'Money')
            value: New value
        \"\"\"
        old_value = self._value_objects.get(vo_name)
        self._value_objects[vo_name] = value
        self._record_change(
            f"{{vo_name}}Changed",
            {{"old": old_value, "new": value}}
        )
        self._validate_invariants()

    def _validate_invariants(self) -> None:
        \"\"\"Validate {{aggregate_name}} business invariants\"\"\"
        if not self._id:
            raise ValueError(f"{{aggregate_name}} must have an ID")

        # Add domain-specific invariants:
        # - Total value must be positive
        # - Status transitions must be valid
        # - Required entities must be present
        # Example:
        # if self._value_objects.get('Money', 0) < 0:
        #     raise ValueError("{{aggregate_name}} value cannot be negative")

    def _record_change(self, event_type: str, data: dict) -> None:
        \"\"\"Record domain event for event sourcing\"\"\"
        self._changes.append({{
            "event_type": event_type,
            "aggregate_id": self._id,
            "aggregate_type": "{aggregate_name}",
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
            "version": self._version
        }})
        self._version += 1
        self._updated_at = datetime.utcnow()

    def mark_changes_as_committed(self) -> None:
        \"\"\"Clear uncommitted changes after persistence\"\"\"
        self._changes.clear()

    def to_dict(self) -> dict:
        \"\"\"Serialize aggregate to dict\"\"\"
        return {{
            "id": self._id,
            "version": self._version,
            "created_at": self._created_at.isoformat(),
            "updated_at": self._updated_at.isoformat(),
            "entities": self._entities,
            "value_objects": self._value_objects,
            "data": self._data
        }}

    def __repr__(self):
        return f"{aggregate_name}(id={self._id!r}, version={{self._version}})"
"""

    # Generate Repository interface
    repository_code = f"""
class {aggregate_name}Repository:
    \"\"\"
    Repository Pattern: {aggregate_name}Aggregate

    Hides persistence details. All load/save operations go through this interface.
    Can be backed by SQL, NoSQL, Event Store, etc.
    \"\"\"

    def save(self, aggregate: {aggregate_name}Aggregate) -> None:
        \"\"\"Save aggregate and its uncommitted changes\"\"\"
        raise NotImplementedError("Implement in concrete repository")

    def load(self, aggregate_id: str) -> {aggregate_name}Aggregate:
        \"\"\"Load aggregate by ID\"\"\"
        raise NotImplementedError("Implement in concrete repository")

    def delete(self, aggregate_id: str) -> None:
        \"\"\"Delete aggregate\"\"\"
        raise NotImplementedError("Implement in concrete repository")

    def find_by_spec(self, specification: Any) -> list:
        \"\"\"Find aggregates matching specification\"\"\"
        raise NotImplementedError("Implement in concrete repository")


class {aggregate_name}RepositorySQL:
    \"\"\"SQL implementation of {{aggregate_name}}Repository\"\"\"

    def __init__(self, db_session):
        self.db = db_session

    def save(self, aggregate: {aggregate_name}Aggregate) -> None:
        # TODO: Persist aggregate to SQL
        # 1. Insert/update {aggregate_name} row
        # 2. Insert/update related {entities} rows
        # 3. Record domain events if event sourcing enabled
        aggregate.mark_changes_as_committed()

    def load(self, aggregate_id: str) -> {aggregate_name}Aggregate:
        # TODO: Load from SQL
        # 1. Load {aggregate_name} row
        # 2. Load related {entities}
        # 3. Reconstruct aggregate
        pass

    def delete(self, aggregate_id: str) -> None:
        # TODO: Delete from SQL (cascade to entities)
        pass

    def find_by_spec(self, specification: Any) -> list:
        # TODO: Query using specification pattern
        pass
"""

    return {
        "value_objects": value_object_code,
        "entities": entity_code,
        "aggregate_root": aggregate_code,
        "repository": repository_code,
        "summary": {
            "aggregate": aggregate_name,
            "entities": entities,
            "value_objects": value_objects,
            "module": f"{aggregate_name.lower()}.py",
            "classes_generated": len(entities) + len(value_objects) + 3
        }
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate Aggregate Root pattern with DDD"
    )
    parser.add_argument(
        "--aggregate", required=True,
        help="Name of aggregate root (e.g., Order)"
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
        "--output", choices=["json", "code"], default="code",
        help="Output format"
    )

    args = parser.parse_args()

    result = generate_aggregate_root(
        args.aggregate,
        args.entities or [],
        args.values or []
    )

    if args.output == "json":
        print(json.dumps(result["summary"], indent=2))
    else:
        print("# Value Objects")
        print(result["value_objects"])
        print("\n# Entities")
        print(result["entities"])
        print("\n# Aggregate Root")
        print(result["aggregate_root"])
        print("\n# Repository Pattern")
        print(result["repository"])
        print("\n# Summary")
        print(json.dumps(result["summary"], indent=2))


if __name__ == "__main__":
    main()
