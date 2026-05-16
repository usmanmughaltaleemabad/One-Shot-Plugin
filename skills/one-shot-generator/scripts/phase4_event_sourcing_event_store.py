#!/usr/bin/env python3
"""
Phase 4 Event Sourcing: Event Store

Persists all domain events. Aggregate state is reconstructed by replaying events.
Event Store is the source of truth for state changes.

Usage:
    python phase4_event_sourcing_event_store.py --aggregate Order --backends sql memory

Input: Aggregate name and backend types
Output: Event Store implementations
"""

import argparse
import json
from typing import List, Optional
from datetime import datetime


def generate_event_store_interface() -> str:
    """Generate Event Store interface."""

    interface = '''
class EventStore:
    """Abstract Event Store interface"""

    def append_event(self, event: dict) -> None:
        """Append event to stream"""
        raise NotImplementedError()

    def get_events(self, aggregate_id: str, from_version: int = 1) -> List[dict]:
        """Get all events for aggregate (optionally from specific version)"""
        raise NotImplementedError()

    def get_event_stream(self, aggregate_id: str) -> "EventStream":
        """Get event stream for aggregate"""
        raise NotImplementedError()

    def get_all_events(self, event_type: str = None) -> List[dict]:
        """Get all events (optionally filtered by type)"""
        raise NotImplementedError()


class EventStream:
    """
    Immutable stream of events for an aggregate.

    Provides:
    - Temporal query (events up to timestamp)
    - Filtering (by event type)
    - Aggregation (state reconstruction)
    """

    def __init__(self, aggregate_id: str, events: List[dict]):
        self.aggregate_id = aggregate_id
        self.events = events

    def replay(self, aggregate):
        """Replay events into aggregate (reconstructs state)"""
        for event in self.events:
            aggregate.apply_event(event)
        return aggregate

    def at_version(self, version: int):
        """Get events up to specific version"""
        return EventStream(
            self.aggregate_id,
            [e for e in self.events if e.get("version", 0) <= version]
        )

    def at_timestamp(self, timestamp: datetime):
        """Get events up to timestamp"""
        return EventStream(
            self.aggregate_id,
            [e for e in self.events if datetime.fromisoformat(e.get("timestamp")) <= timestamp]
        )

    def of_type(self, event_type: str):
        """Filter events by type"""
        return EventStream(
            self.aggregate_id,
            [e for e in self.events if e.get("event_type") == event_type]
        )

    def __len__(self):
        return len(self.events)

    def __repr__(self):
        return f"EventStream({self.aggregate_id}, {len(self.events)} events)"
'''

    return interface


def generate_memory_event_store() -> str:
    """Generate in-memory Event Store."""

    store = '''
class MemoryEventStore(EventStore):
    """In-memory Event Store (testing, prototyping)"""

    def __init__(self):
        self._events = []  # Global event log
        self._streams = {}  # aggregate_id -> [events]

    def append_event(self, event: dict) -> None:
        """Append event"""
        self._events.append(event)

        aggregate_id = event.get("aggregate_id")
        if aggregate_id not in self._streams:
            self._streams[aggregate_id] = []
        self._streams[aggregate_id].append(event)

    def get_events(self, aggregate_id: str, from_version: int = 1) -> List[dict]:
        """Get events for aggregate"""
        if aggregate_id not in self._streams:
            return []
        return [e for e in self._streams[aggregate_id] if e.get("version", 0) >= from_version]

    def get_event_stream(self, aggregate_id: str) -> EventStream:
        """Get event stream"""
        events = self.get_events(aggregate_id)
        return EventStream(aggregate_id, events)

    def get_all_events(self, event_type: str = None) -> List[dict]:
        """Get all events"""
        if not event_type:
            return self._events
        return [e for e in self._events if e.get("event_type") == event_type]

    def clear(self):
        """Clear all events (for testing)"""
        self._events.clear()
        self._streams.clear()

    def __repr__(self):
        return f"MemoryEventStore({len(self._events)} events)"
'''

    return store


def generate_sql_event_store() -> str:
    """Generate SQL-based Event Store."""

    store = '''
class SQLEventStore(EventStore):
    """SQL-based Event Store"""

    def __init__(self, session, table):
        self.session = session
        self.table = table

    def append_event(self, event: dict) -> None:
        """Append event to database"""
        row = self.table(
            aggregate_id=event["aggregate_id"],
            event_type=event["event_type"],
            version=event["version"],
            timestamp=datetime.fromisoformat(event["timestamp"]),
            data=json.dumps(event.get("data", {}))
        )
        self.session.add(row)
        self.session.flush()

    def get_events(self, aggregate_id: str, from_version: int = 1) -> List[dict]:
        """Get events from database"""
        rows = self.session.query(self.table).filter(
            self.table.aggregate_id == aggregate_id,
            self.table.version >= from_version
        ).order_by(self.table.version).all()

        return [
            {
                "aggregate_id": r.aggregate_id,
                "event_type": r.event_type,
                "version": r.version,
                "timestamp": r.timestamp.isoformat(),
                "data": json.loads(r.data)
            }
            for r in rows
        ]

    def get_event_stream(self, aggregate_id: str) -> EventStream:
        """Get event stream from database"""
        events = self.get_events(aggregate_id)
        return EventStream(aggregate_id, events)

    def get_all_events(self, event_type: str = None) -> List[dict]:
        """Get all events"""
        query = self.session.query(self.table)
        if event_type:
            query = query.filter(self.table.event_type == event_type)
        rows = query.order_by(self.table.timestamp).all()

        return [
            {
                "aggregate_id": r.aggregate_id,
                "event_type": r.event_type,
                "version": r.version,
                "timestamp": r.timestamp.isoformat(),
                "data": json.loads(r.data)
            }
            for r in rows
        ]
'''

    return store


def generate_event_store_system(aggregate_name: str, backends: list) -> dict:
    """
    Generate complete Event Store system.

    Args:
        aggregate_name: Aggregate name (e.g., Order)
        backends: Backend types (sql, memory)

    Returns:
        dict with Event Store implementations
    """

    imports = '''import json
import uuid
from datetime import datetime
from typing import List, Optional
from abc import ABC, abstractmethod


'''

    module_doc = f'''"""
Event Sourcing: Event Store for {{aggregate_name}}

Event Store persists all domain events.
Aggregate state is derived by replaying events.

Event = immutable fact that happened
Event Store = append-only log of all events
Replay = reconstruct state by running events

Benefits:
- Complete audit trail
- Time travel (state at any point)
- Event-driven architecture
- Temporal queries
- Easy testing (can rerun events)

Backends: {{', '.join(backends)}}
""".replace("{{aggregate_name}}", aggregate_name).replace("{{', '.join(backends)}}", ", ".join(backends))

    interface = generate_event_store_interface()

    backend_code = ""
    if "memory" in backends or "test" in backends:
        backend_code += "\n" + generate_memory_event_store()
    if "sql" in backends or "sqlalchemy" in backends:
        backend_code += "\n" + generate_sql_event_store()

    complete_code = imports + module_doc + "\n" + interface + backend_code

    return {
        "code": complete_code,
        "aggregate": aggregate_name,
        "backends": backends,
        "module": f"{aggregate_name.lower()}_event_store.py",
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate Event Store"
    )
    parser.add_argument(
        "--aggregate", required=True,
        help="Aggregate name (e.g., Order)"
    )
    parser.add_argument(
        "--backends", nargs="+", default=["memory"],
        help="Backend types (memory, sql)"
    )
    parser.add_argument(
        "--output", choices=["json", "code"], default="code",
        help="Output format"
    )

    args = parser.parse_args()

    result = generate_event_store_system(args.aggregate, args.backends)

    if args.output == "json":
        metadata = {k: v for k, v in result.items() if k != "code"}
        print(json.dumps(metadata, indent=2))
    else:
        print(result["code"])


if __name__ == "__main__":
    main()
