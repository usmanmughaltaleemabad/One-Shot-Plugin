#!/usr/bin/env python3
"""
Phase 4 DDD: Entity Design Generator

Generates Entity classes (objects with identity, mutable, part of aggregate).
Entities differ from Value Objects: they have a persistent ID and can change over time.

Usage:
    python phase4_ddd_entity_design.py --aggregate Order --entities LineItem Payment --identity-type uuid

Input: Entity names and identity strategy
Output: Entity classes with identity, equality, lifecycle methods
"""

import argparse
import json
from typing import Any, Optional
from datetime import datetime


def generate_entity(entity_name: str, aggregate_name: str, identity_type: str = "uuid") -> str:
    """
    Generate Entity class with identity and lifecycle management.

    Args:
        entity_name: Entity name (e.g., LineItem)
        aggregate_name: Parent aggregate (e.g., Order)
        identity_type: Identity strategy (uuid, database-id, composite-key)

    Returns:
        str with Entity class code
    """

    if identity_type == "uuid":
        id_generation = "self._id = id or str(uuid.uuid4())"
        id_validation = "if not id: id = str(uuid.uuid4())"
    elif identity_type == "database-id":
        id_generation = "self._id = id  # Assigned by database"
        id_validation = "if not id: raise ValueError('Database ID required')"
    else:
        id_generation = "self._id = id or f'{aggregate_name}_{datetime.utcnow().timestamp()}'"
        id_validation = "if not id: id = f'{aggregate_name}_{datetime.utcnow().timestamp()}'"

    entity_code = f"""
class {entity_name}:
    \"\"\"
    Entity: {entity_name}

    Part of {aggregate_name} aggregate.
    Has persistent identity (can be looked up by ID).
    Mutable: can change state after creation.
    Lifecycle: created -> active -> archived.
    \"\"\"

    def __init__(
        self,
        id: Optional[str] = None,
        **kwargs
    ):
        {id_validation}
        {id_generation}
        self._created_at = datetime.utcnow()
        self._updated_at = self._created_at
        self._version = 1
        self._archived = False
        self._data = kwargs

    @property
    def id(self) -> str:
        \"\"\"Entity ID: persistent identifier\"\"\"
        return self._id

    @property
    def version(self) -> int:
        \"\"\"Version for optimistic locking\"\"\"
        return self._version

    @property
    def is_archived(self) -> bool:
        \"\"\"Check if entity is archived\"\"\"
        return self._archived

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    def update(self, **changes) -> None:
        \"\"\"Update entity state\"\"\"
        if self._archived:
            raise ValueError(f"Cannot update archived {{type(self).__name__}}")

        self._data.update(changes)
        self._version += 1
        self._updated_at = datetime.utcnow()

    def archive(self) -> None:
        \"\"\"Archive entity (soft delete)\"\"\"
        self._archived = True
        self._version += 1
        self._updated_at = datetime.utcnow()

    def restore(self) -> None:
        \"\"\"Restore archived entity\"\"\"
        self._archived = False
        self._version += 1
        self._updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        \"\"\"Serialize entity\"\"\"
        return {{
            "id": self._id,
            "version": self._version,
            "created_at": self._created_at.isoformat(),
            "updated_at": self._updated_at.isoformat(),
            "archived": self._archived,
            **self._data
        }}

    def __eq__(self, other):
        \"\"\"Entities are equal if they have same ID\"\"\"
        if not isinstance(other, {entity_name}):
            return False
        return self._id == other._id

    def __hash__(self):
        \"\"\"Hash by ID\"\"\"
        return hash(self._id)

    def __repr__(self):
        return f"{entity_name}(id='{{self._id}}', version={{self._version}})"
"""

    return entity_code


def generate_entity_factory(entity_name: str) -> str:
    """Generate Factory pattern for creating entities."""

    factory_code = f"""
class {entity_name}Factory:
    \"\"\"Factory for creating {{entity_name}} entities with validation\"\"\"

    @staticmethod
    def create(id: Optional[str] = None, **data) -> {entity_name}:
        \"\"\"
        Create new {{entity_name}} entity.

        Args:
            id: Entity ID (auto-generated if not provided)
            **data: Entity attributes

        Returns:
            {{entity_name}} instance with valid initial state

        Raises:
            ValueError: If data violates entity invariants
        \"\"\"
        # Validate required fields
        # TODO: Add domain-specific validation

        entity = {entity_name}(id=id, **data)
        return entity

    @staticmethod
    def create_from_dict(data: dict) -> {entity_name}:
        \"\"\"Reconstruct entity from persisted data (e.g., from database)\"\"\"
        entity = {entity_name}(id=data.get("id"), **data)
        entity._version = data.get("version", 1)
        entity._archived = data.get("archived", False)
        return entity
"""

    return factory_code


def generate_entity_specification() -> str:
    """Generate Specification pattern for entity queries."""

    spec_code = """
class EntitySpecification:
    \"\"\"Specification pattern for querying entities\"\"\"

    def is_satisfied_by(self, entity) -> bool:
        \"\"\"Check if entity satisfies specification\"\"\"
        raise NotImplementedError()

    def and_spec(self, other: "EntitySpecification") -> "CompositeSpecification":
        return CompositeSpecification(self, other, "AND")

    def or_spec(self, other: "EntitySpecification") -> "CompositeSpecification":
        return CompositeSpecification(self, other, "OR")


class CompositeSpecification(EntitySpecification):
    def __init__(self, left: EntitySpecification, right: EntitySpecification, operator: str):
        self.left = left
        self.right = right
        self.operator = operator

    def is_satisfied_by(self, entity) -> bool:
        if self.operator == "AND":
            return self.left.is_satisfied_by(entity) and self.right.is_satisfied_by(entity)
        elif self.operator == "OR":
            return self.left.is_satisfied_by(entity) or self.right.is_satisfied_by(entity)


class ActiveEntitySpecification(EntitySpecification):
    \"\"\"Specification: entity is not archived\"\"\"
    def is_satisfied_by(self, entity) -> bool:
        return not entity.is_archived


class ArchiveAfterDaysSpecification(EntitySpecification):
    \"\"\"Specification: entity created more than N days ago\"\"\"
    def __init__(self, days: int):
        self.days = days

    def is_satisfied_by(self, entity) -> bool:
        age = (datetime.utcnow() - entity.created_at).days
        return age > self.days
"""

    return spec_code


def generate_entities(entity_names: list, aggregate_name: str, identity_type: str = "uuid") -> dict:
    """
    Generate Entity classes for aggregate.

    Args:
        entity_names: List of entity names (e.g., [LineItem, Payment])
        aggregate_name: Parent aggregate (e.g., Order)
        identity_type: Identity strategy

    Returns:
        dict with entity classes and metadata
    """

    imports = '''import uuid
from datetime import datetime
from typing import Any, Optional
from abc import ABC, abstractmethod


'''

    entity_code = "\n".join([
        generate_entity(name, aggregate_name, identity_type)
        for name in entity_names
    ])

    factory_code = "\n".join([
        generate_entity_factory(name)
        for name in entity_names
    ])

    spec_code = generate_entity_specification()

    module_doc = f'''"""
Entities for {{aggregate_name}} Aggregate

Entities have:
- Identity: persistent ID
- Lifecycle: created, active, archived
- Mutability: can change state
- Equality: compared by ID, not value

Entities: {{', '.join(entity_names)}}
""".replace("{{aggregate_name}}", aggregate_name).replace("{{', '.join(entity_names)}}", ", ".join(entity_names))

    complete_code = imports + module_doc + "\n\n" + entity_code + "\n\n" + factory_code + "\n\n" + spec_code

    return {
        "code": complete_code,
        "aggregate": aggregate_name,
        "entities": entity_names,
        "entity_count": len(entity_names),
        "factory_count": len(entity_names),
        "identity_type": identity_type,
        "module": f"{aggregate_name.lower()}_entities.py",
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate Entity classes for aggregate"
    )
    parser.add_argument(
        "--aggregate", required=True,
        help="Aggregate name (e.g., Order)"
    )
    parser.add_argument(
        "--entities", nargs="+", required=True,
        help="Entity names (e.g., LineItem Payment)"
    )
    parser.add_argument(
        "--identity-type", choices=["uuid", "database-id", "composite-key"], default="uuid",
        help="Identity strategy"
    )
    parser.add_argument(
        "--output", choices=["json", "code"], default="code",
        help="Output format"
    )

    args = parser.parse_args()

    result = generate_entities(args.entities, args.aggregate, args.identity_type)

    if args.output == "json":
        metadata = {k: v for k, v in result.items() if k != "code"}
        print(json.dumps(metadata, indent=2))
    else:
        print(result["code"])
        print("\n# Metadata")
        metadata = {k: v for k, v in result.items() if k != "code"}
        print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
