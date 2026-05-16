#!/usr/bin/env python3
"""
Phase 4 CQRS: Outbox Pattern

Ensures reliable event publishing. Events are written alongside aggregate,
atomically. Then published asynchronously.

Solves: What if aggregate saves but event publish fails?
Answer: Event is in outbox. Retry until success.

Usage:
    python phase4_outbox_pattern.py --aggregate Order --broker rabbitmq

Input: Aggregate name and message broker type
Output: Outbox implementation with reliable publishing
"""

import argparse
import json
from typing import Any, List, Optional
from datetime import datetime


def generate_outbox_table_schema() -> str:
    """Generate schema for outbox table."""

    schema = '''
class OutboxSchema:
    """
    Outbox table schema.

    Stores unpublished domain events.

    Fields:
    - id: Unique outbox entry ID
    - aggregate_id: Which aggregate generated the event
    - event_type: Type of event
    - event_data: Full event payload (JSON)
    - published_at: NULL until published, then timestamp
    - retry_count: Number of publish attempts
    - created_at: When event was recorded
    """

    # SQL Schema
    SQL = """
    CREATE TABLE IF NOT EXISTS outbox (
        id VARCHAR(255) PRIMARY KEY,
        aggregate_id VARCHAR(255) NOT NULL,
        event_type VARCHAR(255) NOT NULL,
        event_data JSON NOT NULL,
        published_at TIMESTAMP NULL,
        retry_count INT DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_aggregate (aggregate_id),
        INDEX idx_published (published_at)
    )
    """
'''

    return schema


def generate_outbox_handler() -> str:
    """Generate outbox handler (records + publishes)."""

    handler = '''
class OutboxHandler:
    """
    Outbox handler: records events for reliable publishing.

    Usage:
    1. Save aggregate (transaction 1)
    2. Write event to outbox (same transaction)
    3. Commit
    4. Async: read outbox, publish, mark as published
    """

    def __init__(self, outbox_store, event_publisher):
        self.outbox_store = outbox_store
        self.event_publisher = event_publisher

    def record_event(self, event: dict) -> None:
        """
        Record event to outbox (called during aggregate save).

        Within same transaction as aggregate save.
        If aggregate save fails, event is not recorded (atomic).

        Args:
            event: Domain event
        """
        outbox_entry = {
            "id": str(uuid.uuid4()),
            "aggregate_id": event.get("aggregate_id"),
            "event_type": event.get("event_type"),
            "event_data": event,
            "published_at": None,
            "retry_count": 0,
            "created_at": datetime.utcnow().isoformat()
        }

        self.outbox_store.insert(outbox_entry)

    def publish_unpublished_events(self) -> None:
        """
        Find unpublished events and publish them.

        Called periodically (every 5-10 seconds).
        Guarantees: every event eventually published (idempotent).

        Process:
        1. Query outbox WHERE published_at IS NULL
        2. For each: try publishing
        3. If success: mark published_at = now
        4. If failure: increment retry_count
        """
        unpublished = self.outbox_store.find_unpublished()

        for entry in unpublished:
            try:
                # Publish to broker
                self.event_publisher.publish(entry["event_data"])

                # Mark as published
                self.outbox_store.mark_published(entry["id"])

            except Exception as e:
                # Retry later
                self.outbox_store.increment_retry_count(entry["id"])

                if entry["retry_count"] > 5:
                    # After 5 retries, move to DLQ
                    self.outbox_store.move_to_dlq(entry["id"])

    def get_publishing_stats(self) -> dict:
        """Get outbox statistics"""
        return {
            "total": self.outbox_store.count_all(),
            "unpublished": self.outbox_store.count_unpublished(),
            "published": self.outbox_store.count_published(),
            "dlq": self.outbox_store.count_dlq(),
        }
'''

    return handler


def generate_outbox_stores() -> str:
    """Generate outbox storage implementations."""

    stores = '''
class OutboxStore:
    """Abstract outbox store"""

    def insert(self, entry: dict) -> None:
        """Record event to outbox"""
        raise NotImplementedError()

    def find_unpublished(self, limit: int = 100) -> List[dict]:
        """Get unpublished events"""
        raise NotImplementedError()

    def mark_published(self, entry_id: str) -> None:
        """Mark event as published"""
        raise NotImplementedError()

    def increment_retry_count(self, entry_id: str) -> None:
        """Increment retry counter"""
        raise NotImplementedError()


class SQLOutboxStore(OutboxStore):
    """SQL-based outbox store"""

    def __init__(self, session, table):
        self.session = session
        self.table = table

    def insert(self, entry: dict) -> None:
        row = self.table(**entry)
        self.session.add(row)
        self.session.flush()

    def find_unpublished(self, limit: int = 100) -> List[dict]:
        rows = self.session.query(self.table).filter(
            self.table.published_at == None
        ).limit(limit).all()
        return [r.to_dict() for r in rows]

    def mark_published(self, entry_id: str) -> None:
        self.session.query(self.table).filter(
            self.table.id == entry_id
        ).update({"published_at": datetime.utcnow()})
        self.session.flush()

    def increment_retry_count(self, entry_id: str) -> None:
        self.session.query(self.table).filter(
            self.table.id == entry_id
        ).update({"retry_count": self.table.retry_count + 1})
        self.session.flush()

    def count_unpublished(self) -> int:
        return self.session.query(self.table).filter(
            self.table.published_at == None
        ).count()

    def count_published(self) -> int:
        return self.session.query(self.table).filter(
            self.table.published_at != None
        ).count()


class MemoryOutboxStore(OutboxStore):
    """In-memory outbox store (for testing)"""

    def __init__(self):
        self._entries = {}

    def insert(self, entry: dict) -> None:
        self._entries[entry["id"]] = entry

    def find_unpublished(self, limit: int = 100) -> List[dict]:
        return [
            e for e in self._entries.values()
            if e.get("published_at") is None
        ][:limit]

    def mark_published(self, entry_id: str) -> None:
        if entry_id in self._entries:
            self._entries[entry_id]["published_at"] = datetime.utcnow().isoformat()

    def increment_retry_count(self, entry_id: str) -> None:
        if entry_id in self._entries:
            self._entries[entry_id]["retry_count"] += 1

    def count_unpublished(self) -> int:
        return len([e for e in self._entries.values() if e.get("published_at") is None])

    def count_published(self) -> int:
        return len([e for e in self._entries.values() if e.get("published_at") is not None])
'''

    return stores


def generate_outbox_system(aggregate_name: str, broker_type: str = "rabbitmq") -> dict:
    """Generate complete outbox pattern system."""

    imports = '''import uuid
import json
from datetime import datetime
from typing import Any, List, Optional
from abc import ABC, abstractmethod


'''

    module_doc = f'''"""
Outbox Pattern for {{aggregate_name}}

Reliable event publishing without 2-phase commit.

Problem:
- Aggregate saves: ✓
- Event publishes: ✓
- But what if publish crashes before success response?
- Event might be lost or duplicated.

Solution: Outbox Pattern
1. Aggregate saves
2. Event recorded to outbox (same transaction)
3. Commit (atomic: both succeed or both fail)
4. Async: read outbox, publish, mark as published
5. If publish fails, retry (idempotent)
6. Guarantee: every event published eventually

Implementation:
- Outbox table: stores unpublished events
- Async publisher: polls outbox every 5-10 seconds
- Idempotent: publishing same event twice is safe
""".replace("{{aggregate_name}}", aggregate_name)

    schema = generate_outbox_table_schema()
    handler = generate_outbox_handler()
    stores = generate_outbox_stores()

    complete_code = imports + module_doc + "\n" + schema + "\n" + handler + "\n" + stores

    return {
        "code": complete_code,
        "aggregate": aggregate_name,
        "broker": broker_type,
        "pattern": "Outbox",
        "module": f"{aggregate_name.lower()}_outbox.py",
    }


def main():
    parser = argparse.ArgumentParser(description="Generate outbox pattern")
    parser.add_argument("--aggregate", required=True, help="Aggregate name")
    parser.add_argument("--broker", default="rabbitmq", help="Message broker type")
    parser.add_argument("--output", choices=["json", "code"], default="code")

    args = parser.parse_args()
    result = generate_outbox_system(args.aggregate, args.broker)

    if args.output == "json":
        metadata = {k: v for k, v in result.items() if k != "code"}
        print(json.dumps(metadata, indent=2))
    else:
        print(result["code"])


if __name__ == "__main__":
    main()
