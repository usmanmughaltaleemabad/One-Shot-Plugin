#!/usr/bin/env python3
"""
Phase 4 CQRS: Query Bus

Routes queries to read model handlers. Queries are read-only, fast, optimized for display.
Separate from write model (commands). Achieves eventual consistency.

Usage:
    python phase4_cqrs_query_bus.py --aggregate Order --queries GetOrder ListOrders GetOrderByCustomer

Input: Query names
Output: Query handlers and read model optimization
"""

import argparse
import json
from typing import Any, List, Optional


def generate_query_class(query_name: str) -> str:
    """Generate query class."""

    query_code = f'''
class {query_name}:
    """
    Query: {query_name}

    Queries:
    - Ask for data (read-only)
    - Optimized for display
    - Hit read model (projection)
    - Fast (indexes, denormalization)
    - Eventually consistent with write model
    """

    def __init__(self, **criteria):
        self.criteria = criteria
        self.query_id = str(uuid.uuid4())

    def to_dict(self) -> dict:
        return {{
            "query_id": self.query_id,
            "query_type": type(self).__name__,
            "criteria": self.criteria
        }}

    def __repr__(self):
        return f"{query_name}(id={{self.query_id}})"
'''

    return query_code


def generate_query_handler(query_name: str) -> str:
    """Generate query handler (read model access)."""

    handler_code = f'''
class {query_name}Handler:
    """Handler for {query_name} query"""

    def __init__(self, read_model_store):
        self.read_model_store = read_model_store

    def handle(self, query: {query_name}) -> Any:
        """
        Execute query against read model.

        Read models are denormalized, indexed for fast queries.
        Data comes from event stream via projections.

        Returns:
            Query result (typically list of DTOs or single DTO)
        """
        # TODO: Query read model
        # Example: return self.read_model_store.find(query.criteria)
        pass
'''

    return handler_code


def generate_query_bus() -> str:
    """Generate query bus."""

    bus_code = '''
class QueryBus:
    """
    Query Bus: routes queries to read model handlers

    Queries hit projections/read models (not aggregates).
    Fast, optimized for display.
    Eventually consistent with write model.
    """

    def __init__(self):
        self._handlers = {}  # query_type -> handler instance

    def register(self, query_type: type, handler) -> None:
        """Register query handler"""
        query_name = query_type.__name__
        self._handlers[query_name] = handler

    def execute(self, query) -> Any:
        """
        Execute query synchronously.

        Returns:
            Data from read model

        Raises:
            UnknownQueryException: Handler not registered
        """
        query_name = type(query).__name__

        if query_name not in self._handlers:
            raise UnknownQueryException(f"No handler for {query_name}")

        handler = self._handlers[query_name]
        return handler.handle(query)

    def __repr__(self):
        return f"QueryBus({len(self._handlers)} handlers)"


class QueryException(Exception):
    """Base exception for query execution"""
    pass


class UnknownQueryException(QueryException):
    """Handler not registered for query"""
    pass
'''

    return bus_code


def generate_read_model_store() -> str:
    """Generate read model storage interface."""

    store = '''
class ReadModelStore:
    """
    Read Model Store: persistence for denormalized query data

    Read models are:
    - Denormalized (optimized for queries)
    - Indexed (fast lookups)
    - Updated from event stream (eventual consistency)
    - Can be rebuilt from events
    """

    def find(self, criteria: dict) -> list:
        """Find entities matching criteria"""
        raise NotImplementedError()

    def find_one(self, id: str):
        """Find single entity by ID"""
        raise NotImplementedError()

    def update(self, id: str, data: dict) -> None:
        """Update read model when event occurs"""
        raise NotImplementedError()

    def delete(self, id: str) -> None:
        """Delete from read model"""
        raise NotImplementedError()

    def rebuild(self, events: list) -> None:
        """Rebuild read model from events"""
        raise NotImplementedError()


class MemoryReadModelStore(ReadModelStore):
    """In-memory read model (testing)"""

    def __init__(self):
        self._data = {}  # id -> entity

    def find(self, criteria: dict) -> list:
        """Filter entities"""
        return [e for e in self._data.values() if self._matches(e, criteria)]

    def find_one(self, id: str):
        """Find by ID"""
        return self._data.get(id)

    def update(self, id: str, data: dict) -> None:
        """Update or insert"""
        self._data[id] = {**self._data.get(id, {}), **data}

    def delete(self, id: str) -> None:
        """Delete"""
        if id in self._data:
            del self._data[id]

    def rebuild(self, events: list) -> None:
        """Rebuild from events"""
        self._data.clear()
        for event in events:
            if event.get("event_type") == "Created":
                self.update(event["aggregate_id"], event.get("data", {}))
            elif event.get("event_type") == "Updated":
                self.update(event["aggregate_id"], event.get("data", {}))
            elif event.get("event_type") == "Deleted":
                self.delete(event["aggregate_id"])

    def _matches(self, entity: dict, criteria: dict) -> bool:
        """Check if entity matches criteria"""
        for key, value in criteria.items():
            if entity.get(key) != value:
                return False
        return True

    def __repr__(self):
        return f"MemoryReadModelStore({len(self._data)} entities)"
'''

    return store


def generate_query_system(queries: list) -> dict:
    """
    Generate complete CQRS Query system.

    Args:
        queries: Query names (e.g., [GetOrder, ListOrders])

    Returns:
        dict with query system code
    """

    imports = '''import uuid
from typing import Any, List, Optional
from abc import ABC, abstractmethod


'''

    module_doc = '''"""
CQRS Query Bus

Queries access read models (projections) instead of aggregates.
Read models are optimized for specific queries (denormalized, indexed).
Eventually consistent with write model via event stream.

Pattern: User → Query → QueryBus → QueryHandler → ReadModel
Eventual Consistency: Write Model updates → Events → Projections update ReadModel
"""
'''

    # Generate all queries
    query_classes = "\n".join([
        generate_query_class(q)
        for q in queries
    ])

    # Generate all handlers
    handler_classes = "\n".join([
        generate_query_handler(q)
        for q in queries
    ])

    # Query bus
    bus = generate_query_bus()

    # Read model store
    store = generate_read_model_store()

    # Usage example
    example = f'''
# Example Usage

# Create query bus
query_bus = QueryBus()

# Create read model store
read_model_store = MemoryReadModelStore()

# Register handlers
query_bus.register({queries[0]}, {queries[0]}Handler(read_model_store))

# Execute query
try:
    query = {queries[0]}(id="123")
    result = query_bus.execute(query)
    print(f"Result: {{result}}")
except QueryException as e:
    print(f"Query failed: {{e}}")

# Rebuild read model from events (when events arrive)
# events = event_store.get_all_events()
# read_model_store.rebuild(events)
'''

    complete_code = imports + module_doc + "\n" + query_classes + "\n" + handler_classes + "\n" + bus + "\n" + store + "\n" + example

    return {
        "code": complete_code,
        "queries": queries,
        "query_count": len(queries),
        "module": "queries.py",
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate CQRS query bus"
    )
    parser.add_argument(
        "--queries", nargs="+", required=True,
        help="Query names (e.g., GetOrder ListOrders)"
    )
    parser.add_argument(
        "--output", choices=["json", "code"], default="code",
        help="Output format"
    )

    args = parser.parse_args()

    result = generate_query_system(args.queries)

    if args.output == "json":
        metadata = {k: v for k, v in result.items() if k != "code"}
        print(json.dumps(metadata, indent=2))
    else:
        print(result["code"])


if __name__ == "__main__":
    main()
