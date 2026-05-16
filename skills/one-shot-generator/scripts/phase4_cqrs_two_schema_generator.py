#!/usr/bin/env python3
"""
Phase 4 CQRS: Two-Schema Generator

Generates separation of write schema (normalized) and read schema (denormalized).
Different databases, different structures, synchronized via events.

Usage:
    python phase4_cqrs_two_schema_generator.py --aggregate Order --write-db postgres --read-db elasticsearch

Input: Aggregate and database types
Output: Write/read schema generators
"""

import argparse
import json
from typing import Dict, Any


def generate_write_schema(aggregate_name: str) -> str:
    """Generate normalized write schema."""

    schema = f'''
# Write Schema (Normalized - ACID compliant)

# {{aggregate_name}}_write table
CREATE TABLE IF NOT EXISTS {{aggregate_name}}_write (
    id VARCHAR(255) PRIMARY KEY,
    version INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    data JSON NOT NULL,  -- Aggregate state
    INDEX idx_updated_at (updated_at)
);

class {{aggregate_name}}WriteModel:
    """
    Write Model: normalized, enforces invariants.

    Purpose: Save aggregate state, enforce business rules.
    Optimized for: transactions, consistency, updates.
    NOT optimized for: queries.
    """

    def save(self, aggregate) -> None:
        """Save aggregate to write DB"""
        # INSERT or UPDATE {{aggregate_name}}_write
        pass

    def load(self, aggregate_id: str):
        """Load aggregate for modification"""
        # SELECT FROM {{aggregate_name}}_write WHERE id = aggregate_id
        pass

    def delete(self, aggregate_id: str) -> None:
        """Delete aggregate"""
        # DELETE FROM {{aggregate_name}}_write WHERE id = aggregate_id
        pass
'''

    return schema.replace("{{aggregate_name}}", aggregate_name)


def generate_read_schema(aggregate_name: str) -> str:
    """Generate denormalized read schema."""

    schema = f'''
# Read Schema (Denormalized - Optimized for queries)

# {{aggregate_name}}_read index (e.g., Elasticsearch)
POST /{{aggregate_name}}-read/_mapping
{{
    "properties": {{
        "id": {{"type": "keyword"}},
        "status": {{"type": "keyword"}},
        "created_at": {{"type": "date"}},
        "total_amount": {{"type": "float"}},
        "customer_id": {{"type": "keyword"}},
        "items_count": {{"type": "integer"}},
        "description": {{"type": "text"}},  -- Full-text search
        "tags": {{"type": "keyword"}}
    }}
}}

class {{aggregate_name}}ReadModel:
    """
    Read Model: denormalized, optimized for queries.

    Purpose: Fast, flexible queries without complex JOINs.
    Optimized for: searches, filters, aggregations, reporting.
    NOT optimized for: transactions, consistency (eventual).

    Data comes from events (eventually consistent).
    Can be rebuilt from events.
    """

    def update_from_event(self, event: dict) -> None:
        """Update read model when event occurs"""
        # Index event data in Elasticsearch
        # No transaction needed (eventual consistency)
        pass

    def query(self, criteria: dict) -> list:
        """Search read model"""
        # Elasticsearch query (fast, flexible)
        # Example: find by status, date range, full-text search
        pass

    def rebuild(self, events: list) -> None:
        """Rebuild from events (recovery)"""
        # Clear existing index
        # Process all events, rebuild index
        pass
'''

    return schema.replace("{{aggregate_name}}", aggregate_name)


def generate_synchronization() -> str:
    """Generate write-read synchronization."""

    sync = '''
class WriteTReadSynchronizer:
    """
    Synchronizes write model and read model.

    Process:
    1. Aggregate modifies → event generated
    2. Event published to event bus
    3. Read model handler subscribes → updates read model
    4. Eventual consistency achieved (milliseconds to seconds)
    """

    def __init__(self, event_bus, read_model_updater):
        self.event_bus = event_bus
        self.read_model_updater = read_model_updater

        # Subscribe to all events
        self.event_bus.subscribe("*", self._on_event)

    def _on_event(self, event: dict) -> None:
        """Event occurred: update read model"""
        try:
            self.read_model_updater.handle_event(event)
        except Exception as e:
            # Log, retry, or move to DLQ
            # Read model can be rebuilt from events if needed
            pass


class TwoSchemaArchitecture:
    """
    Complete two-schema architecture.

    Write path (commands):
    User → Command → Handler → Write Model → Event → Event Bus

    Read path (queries):
    User → Query → Query Bus → Read Model (fast, denormalized)

    Synchronization:
    Event Bus → Read Model Handler → Update Read Model (eventual consistency)
    """

    def __init__(self):
        self.write_model = None  # Normalized DB
        self.read_model = None   # Denormalized index
        self.event_bus = None
        self.synchronizer = None

    def execute_command(self, command) -> str:
        """Execute command (write path)"""
        # 1. Load aggregate from write model
        # 2. Execute command (modify aggregate)
        # 3. Save aggregate (generate event)
        # 4. Publish event
        # (Async: Read model updates via event)
        pass

    def execute_query(self, query) -> list:
        """Execute query (read path)"""
        # 1. Query read model directly (fast!)
        # 2. No need to load aggregates
        # 3. Results are denormalized (ready to display)
        pass
'''

    return sync


def generate_schema_system(aggregate_name: str, write_db: str, read_db: str) -> dict:
    """Generate complete two-schema system."""

    imports = '''
from typing import Any, Dict, List, Optional


'''

    module_doc = f'''"""
Two-Schema Architecture for {{aggregate_name}}

Separate write (normalized) and read (denormalized) models.

Write Model:
- ACID transactions
- Enforces invariants
- Small, fast, consistent
- {{write_db}}

Read Model:
- Denormalized for queries
- Fast searches, filters
- Eventual consistency
- {{read_db}}

Synchronization:
- Event → Event Bus
- Event Bus → Read Model Handler
- Handler updates read model
- Milliseconds of lag (acceptable for most use cases)
""".replace("{{aggregate_name}}", aggregate_name).replace("{{write_db}}", write_db).replace("{{read_db}}", read_db)

    write_schema = generate_write_schema(aggregate_name)
    read_schema = generate_read_schema(aggregate_name)
    sync = generate_synchronization()

    complete_code = imports + module_doc + "\n" + write_schema + "\n" + read_schema + "\n" + sync

    return {
        "code": complete_code,
        "aggregate": aggregate_name,
        "write_database": write_db,
        "read_database": read_db,
        "pattern": "Two-Schema / CQRS Read/Write Separation",
        "module": f"{aggregate_name.lower()}_two_schema.py",
    }


def main():
    parser = argparse.ArgumentParser(description="Generate two-schema architecture")
    parser.add_argument("--aggregate", required=True, help="Aggregate name")
    parser.add_argument("--write-db", default="postgres", help="Write database")
    parser.add_argument("--read-db", default="elasticsearch", help="Read database")
    parser.add_argument("--output", choices=["json", "code"], default="code")

    args = parser.parse_args()
    result = generate_schema_system(args.aggregate, args.write_db, args.read_db)

    if args.output == "json":
        metadata = {k: v for k, v in result.items() if k != "code"}
        print(json.dumps(metadata, indent=2))
    else:
        print(result["code"])


if __name__ == "__main__":
    main()
