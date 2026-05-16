#!/usr/bin/env python3
"""
Phase 4 DDD: Repository Pattern Generator

Generates Repository interfaces and implementations.
Repositories provide collection-like access to aggregates, hiding persistence details.

Usage:
    python phase4_ddd_repository_pattern.py --aggregate Order --backend sqlalchemy

Input: Aggregate name and persistence backend
Output: Repository interface and concrete implementations
"""

import argparse
import json
from typing import Any, Optional, List


def generate_repository_interface(aggregate_name: str) -> str:
    """Generate Repository interface (contracts)."""

    interface_code = f'''
class {aggregate_name}Repository:
    """
    Repository Pattern: {{aggregate_name}}

    Hides persistence technology. Aggregate is loaded from/saved to repository
    without code knowing about SQL, NoSQL, files, etc.

    Contracts:
    - add(): Add new aggregate
    - remove(): Delete aggregate
    - find_by_id(): Retrieve by ID
    - find_by_spec(): Query by specification
    """

    def add(self, aggregate: {aggregate_name}Aggregate) -> None:
        """Save new aggregate to repository"""
        raise NotImplementedError()

    def remove(self, aggregate_id: str) -> None:
        """Delete aggregate from repository"""
        raise NotImplementedError()

    def find_by_id(self, aggregate_id: str) -> Optional[{aggregate_name}Aggregate]:
        """Retrieve aggregate by ID"""
        raise NotImplementedError()

    def find_all(self) -> List[{aggregate_name}Aggregate]:
        """Retrieve all aggregates"""
        raise NotImplementedError()

    def find_by_spec(self, spec: Any) -> List[{aggregate_name}Aggregate]:
        """Retrieve aggregates matching specification"""
        raise NotImplementedError()

    def size(self) -> int:
        """Count total aggregates"""
        raise NotImplementedError()

    def exists(self, aggregate_id: str) -> bool:
        """Check if aggregate exists"""
        raise NotImplementedError()
'''.replace("{{aggregate_name}}", aggregate_name)

    return interface_code


def generate_repository_sql(aggregate_name: str) -> str:
    """Generate SQL-based Repository implementation."""

    repo_code = f'''
class {aggregate_name}SQLRepository({aggregate_name}Repository):
    """SQL/ORM-based Repository for {{aggregate_name}}"""

    def __init__(self, session, model_class):
        self.session = session  # SQLAlchemy or similar
        self.model = model_class

    def add(self, aggregate: {aggregate_name}Aggregate) -> None:
        """Save aggregate to SQL database"""
        data = aggregate.to_dict()
        model_instance = self.model(**data)
        self.session.add(model_instance)
        self.session.flush()
        # TODO: Publish domain events

    def remove(self, aggregate_id: str) -> None:
        """Delete aggregate from database"""
        self.session.query(self.model).filter(
            self.model.id == aggregate_id
        ).delete()
        self.session.flush()

    def find_by_id(self, aggregate_id: str) -> Optional[{aggregate_name}Aggregate]:
        """Load aggregate from database"""
        row = self.session.query(self.model).filter(
            self.model.id == aggregate_id
        ).first()

        if not row:
            return None

        # Reconstruct aggregate from row
        return {aggregate_name}Aggregate.from_dict(row.to_dict())

    def find_all(self) -> List[{aggregate_name}Aggregate]:
        """Load all aggregates"""
        rows = self.session.query(self.model).all()
        return [
            {aggregate_name}Aggregate.from_dict(row.to_dict())
            for row in rows
        ]

    def find_by_spec(self, spec: Any) -> List[{aggregate_name}Aggregate]:
        """Query using specification pattern"""
        rows = self.session.query(self.model).all()
        return [
            {aggregate_name}Aggregate.from_dict(row.to_dict())
            for row in rows
            if spec.is_satisfied_by(row)
        ]

    def size(self) -> int:
        """Count aggregates"""
        return self.session.query(self.model).count()

    def exists(self, aggregate_id: str) -> bool:
        """Check existence"""
        return self.session.query(self.model).filter(
            self.model.id == aggregate_id
        ).first() is not None
'''.replace("{{aggregate_name}}", aggregate_name)

    return repo_code


def generate_repository_nosql(aggregate_name: str) -> str:
    """Generate NoSQL-based Repository implementation."""

    repo_code = f'''
class {aggregate_name}NoSQLRepository({aggregate_name}Repository):
    """NoSQL/Document-based Repository for {{aggregate_name}}"""

    def __init__(self, collection):
        self.collection = collection  # MongoDB, DynamoDB, etc.

    def add(self, aggregate: {aggregate_name}Aggregate) -> None:
        """Save aggregate to NoSQL store"""
        data = aggregate.to_dict()
        data["_id"] = aggregate.id
        self.collection.insert_one(data)
        # TODO: Publish domain events

    def remove(self, aggregate_id: str) -> None:
        """Delete aggregate from NoSQL store"""
        self.collection.delete_one({{"_id": aggregate_id}})

    def find_by_id(self, aggregate_id: str) -> Optional[{aggregate_name}Aggregate]:
        """Load aggregate from NoSQL"""
        doc = self.collection.find_one({{"_id": aggregate_id}})
        if not doc:
            return None
        doc.pop("_id")  # Remove NoSQL ID
        return {aggregate_name}Aggregate.from_dict(doc)

    def find_all(self) -> List[{aggregate_name}Aggregate]:
        """Load all aggregates"""
        docs = list(self.collection.find())
        aggregates = []
        for doc in docs:
            doc.pop("_id")
            aggregates.append({aggregate_name}Aggregate.from_dict(doc))
        return aggregates

    def find_by_spec(self, spec: Any) -> List[{aggregate_name}Aggregate]:
        """Query using specification"""
        docs = list(self.collection.find())
        aggregates = []
        for doc in docs:
            doc.pop("_id")
            agg = {aggregate_name}Aggregate.from_dict(doc)
            if spec.is_satisfied_by(agg):
                aggregates.append(agg)
        return aggregates

    def size(self) -> int:
        """Count aggregates"""
        return self.collection.count_documents({{}})

    def exists(self, aggregate_id: str) -> bool:
        """Check existence"""
        return self.collection.find_one({{"_id": aggregate_id}}) is not None
'''.replace("{{aggregate_name}}", aggregate_name)

    return repo_code


def generate_repository_memory(aggregate_name: str) -> str:
    """Generate in-memory Repository (for testing)."""

    repo_code = f'''
class {aggregate_name}MemoryRepository({aggregate_name}Repository):
    """In-memory Repository (for testing, prototyping)"""

    def __init__(self):
        self._store = {{}}  # aggregate_id -> aggregate

    def add(self, aggregate: {aggregate_name}Aggregate) -> None:
        """Store aggregate in memory"""
        self._store[aggregate.id] = aggregate
        # TODO: Publish domain events

    def remove(self, aggregate_id: str) -> None:
        """Remove from memory"""
        if aggregate_id in self._store:
            del self._store[aggregate_id]

    def find_by_id(self, aggregate_id: str) -> Optional[{aggregate_name}Aggregate]:
        """Retrieve from memory"""
        return self._store.get(aggregate_id)

    def find_all(self) -> List[{aggregate_name}Aggregate]:
        """Get all aggregates"""
        return list(self._store.values())

    def find_by_spec(self, spec: Any) -> List[{aggregate_name}Aggregate]:
        """Filter using specification"""
        return [agg for agg in self._store.values() if spec.is_satisfied_by(agg)]

    def size(self) -> int:
        """Count aggregates"""
        return len(self._store)

    def exists(self, aggregate_id: str) -> bool:
        """Check if exists"""
        return aggregate_id in self._store

    def clear(self) -> None:
        """Clear all (for testing)"""
        self._store.clear()
'''.replace("{{aggregate_name}}", aggregate_name)

    return repo_code


def generate_repositories(aggregate_name: str, backends: list) -> dict:
    """
    Generate Repository pattern implementations.

    Args:
        aggregate_name: Aggregate name (e.g., Order)
        backends: List of backends (e.g., [sql, nosql, memory])

    Returns:
        dict with all repository implementations
    """

    imports = '''from abc import ABC, abstractmethod
from typing import Any, Optional, List
from datetime import datetime


'''

    interface = generate_repository_interface(aggregate_name)

    backend_code = ""
    if "sql" in backends or "sqlalchemy" in backends:
        backend_code += "\n" + generate_repository_sql(aggregate_name)
    if "nosql" in backends or "mongodb" in backends:
        backend_code += "\n" + generate_repository_nosql(aggregate_name)
    if "memory" in backends or "test" in backends:
        backend_code += "\n" + generate_repository_memory(aggregate_name)

    module_doc = f'''"""
Repository Pattern for {{aggregate_name}}

Repositories provide collection-like access to aggregates.
Choose implementation based on persistence backend:
- SQLRepository: SQL database with ORM
- NoSQLRepository: Document store (MongoDB, DynamoDB)
- MemoryRepository: Testing, prototyping

All implementations satisfy {{aggregate_name}}Repository interface.
""".replace("{{aggregate_name}}", aggregate_name)

    complete_code = imports + module_doc + "\n" + interface + backend_code

    return {
        "code": complete_code,
        "aggregate": aggregate_name,
        "backends": backends,
        "backend_count": len(backends),
        "module": f"{aggregate_name.lower()}_repository.py",
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate Repository pattern for aggregate"
    )
    parser.add_argument(
        "--aggregate", required=True,
        help="Aggregate name (e.g., Order)"
    )
    parser.add_argument(
        "--backends", nargs="+", default=["sql"],
        help="Repository backends (sql, nosql, memory)"
    )
    parser.add_argument(
        "--output", choices=["json", "code"], default="code",
        help="Output format"
    )

    args = parser.parse_args()

    result = generate_repositories(args.aggregate, args.backends)

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
