#!/usr/bin/env python3
"""
Phase 4 CQRS: Dead Letter Queue (DLQ) Handler

Handles failed event processing gracefully.
When projection update fails or event handler crashes,
event goes to DLQ instead of being lost.

DLQ: Append-only log of failures. Manual review, replay, reroute.

Usage:
    python phase4_dead_letter_queue_handler.py --aggregate Order --failure-mode projection_update

Input: Aggregate and failure scenario
Output: DLQ handler with recovery strategies
"""

import argparse
import json
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime


def generate_dlq_schema() -> str:
    """Generate DLQ table schema."""

    schema = '''
class DLQSchema:
    """
    Dead Letter Queue schema.

    Stores events that failed processing.

    Fields:
    - id: Unique DLQ entry ID
    - event_id: Which event failed
    - aggregate_id: Which aggregate
    - failure_reason: Exception message
    - failure_type: e.g., ProjectionUpdateFailed, HandlerCrashed
    - event_data: Full event payload
    - retry_count: How many times retried
    - routed_at: When routed to DLQ
    - resolved_at: When issue fixed + replayed
    - resolution_notes: How was it fixed
    """

    SQL = """
    CREATE TABLE IF NOT EXISTS dlq (
        id VARCHAR(255) PRIMARY KEY,
        event_id VARCHAR(255) NOT NULL,
        aggregate_id VARCHAR(255) NOT NULL,
        failure_reason TEXT NOT NULL,
        failure_type VARCHAR(255) NOT NULL,
        event_data JSON NOT NULL,
        retry_count INT DEFAULT 0,
        routed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        resolved_at TIMESTAMP NULL,
        resolution_notes TEXT,
        INDEX idx_aggregate (aggregate_id),
        INDEX idx_unresolved (resolved_at)
    )
    """
'''

    return schema


def generate_dlq_handler() -> str:
    """Generate DLQ handler."""

    handler = '''
class DeadLetterQueueHandler:
    """
    Dead Letter Queue: handles failed event processing.

    When event handler fails (after retries), route to DLQ.
    Never lose data. Enable manual investigation + replay.

    Lifecycle:
    1. Event processing fails
    2. Retries exhausted
    3. Route to DLQ
    4. Human reviews failure
    5. Fix issue
    6. Replay event (idempotent)
    """

    def __init__(self, dlq_store, event_replayer):
        self.dlq_store = dlq_store
        self.event_replayer = event_replayer

    def route_to_dlq(
        self,
        event: dict,
        exception: Exception,
        failure_type: str,
        retry_count: int
    ) -> None:
        """
        Route failed event to DLQ.

        Args:
            event: Event that failed processing
            exception: The exception that caused failure
            failure_type: Category (ProjectionUpdateFailed, etc.)
            retry_count: How many times was it retried
        """
        dlq_entry = {
            "id": f"dlq-{event.get('event_id')}",
            "event_id": event.get("event_id"),
            "aggregate_id": event.get("aggregate_id"),
            "failure_reason": str(exception),
            "failure_type": failure_type,
            "event_data": event,
            "retry_count": retry_count,
            "routed_at": datetime.utcnow().isoformat(),
            "resolved_at": None,
            "resolution_notes": None
        }

        self.dlq_store.insert(dlq_entry)

    def get_unresolved_dlq_entries(self, limit: int = 50) -> List[dict]:
        """Get DLQ entries waiting for resolution"""
        return self.dlq_store.find_unresolved(limit)

    def get_dlq_stats(self) -> dict:
        """Get DLQ statistics"""
        return {
            "total": self.dlq_store.count_all(),
            "unresolved": self.dlq_store.count_unresolved(),
            "resolved": self.dlq_store.count_resolved(),
            "by_failure_type": self.dlq_store.count_by_failure_type(),
            "oldest_unresolved": self.dlq_store.get_oldest_unresolved()
        }

    def replay_dlq_entry(
        self,
        dlq_id: str,
        handler: Callable,
        resolution_notes: str = ""
    ) -> bool:
        """
        Replay a DLQ entry with fixed handler.

        Args:
            dlq_id: DLQ entry ID
            handler: Fixed event handler
            resolution_notes: What was the fix

        Returns:
            True if replay succeeded
        """
        entry = self.dlq_store.get_by_id(dlq_id)
        if not entry:
            return False

        try:
            # Try processing with fixed handler
            handler(entry["event_data"])

            # Mark as resolved
            self.dlq_store.mark_resolved(dlq_id, resolution_notes)
            return True

        except Exception as e:
            # Still failing, leave in DLQ
            self.dlq_store.increment_retry_count(dlq_id)
            return False

    def bulk_replay_dlq(
        self,
        handler: Callable,
        failure_type: Optional[str] = None
    ) -> dict:
        """
        Bulk replay DLQ entries.

        Use case: Fixed bug in projection handler, replay all failed projections.

        Args:
            handler: Fixed event handler
            failure_type: Only replay specific failure type

        Returns:
            Statistics: {replayed, succeeded, still_failing}
        """
        entries = self.dlq_store.find_unresolved_by_type(failure_type)

        stats = {"replayed": 0, "succeeded": 0, "still_failing": 0}

        for entry in entries:
            stats["replayed"] += 1
            if self.replay_dlq_entry(entry["id"], handler):
                stats["succeeded"] += 1
            else:
                stats["still_failing"] += 1

        return stats
'''

    return handler


def generate_dlq_store() -> str:
    """Generate DLQ store implementations."""

    store = '''
class DLQStore:
    """Abstract DLQ store"""

    def insert(self, entry: dict) -> None:
        """Add entry to DLQ"""
        raise NotImplementedError()

    def find_unresolved(self, limit: int = 50) -> List[dict]:
        """Get unresolved DLQ entries"""
        raise NotImplementedError()

    def get_by_id(self, dlq_id: str) -> Optional[dict]:
        """Get specific DLQ entry"""
        raise NotImplementedError()

    def mark_resolved(self, dlq_id: str, notes: str) -> None:
        """Mark as resolved"""
        raise NotImplementedError()

    def increment_retry_count(self, dlq_id: str) -> None:
        """Increment retry counter"""
        raise NotImplementedError()


class SQLDLQStore(DLQStore):
    """SQL-based DLQ store"""

    def __init__(self, session, table):
        self.session = session
        self.table = table

    def insert(self, entry: dict) -> None:
        row = self.table(**entry)
        self.session.add(row)
        self.session.flush()

    def find_unresolved(self, limit: int = 50) -> List[dict]:
        rows = self.session.query(self.table).filter(
            self.table.resolved_at == None
        ).limit(limit).all()
        return [r.to_dict() for r in rows]

    def find_unresolved_by_type(self, failure_type: Optional[str] = None) -> List[dict]:
        query = self.session.query(self.table).filter(
            self.table.resolved_at == None
        )
        if failure_type:
            query = query.filter(self.table.failure_type == failure_type)
        return [r.to_dict() for r in query.all()]

    def get_by_id(self, dlq_id: str) -> Optional[dict]:
        row = self.session.query(self.table).filter(
            self.table.id == dlq_id
        ).first()
        return row.to_dict() if row else None

    def mark_resolved(self, dlq_id: str, notes: str) -> None:
        self.session.query(self.table).filter(
            self.table.id == dlq_id
        ).update({
            "resolved_at": datetime.utcnow(),
            "resolution_notes": notes
        })
        self.session.flush()

    def increment_retry_count(self, dlq_id: str) -> None:
        self.session.query(self.table).filter(
            self.table.id == dlq_id
        ).update({"retry_count": self.table.retry_count + 1})
        self.session.flush()

    def count_all(self) -> int:
        return self.session.query(self.table).count()

    def count_unresolved(self) -> int:
        return self.session.query(self.table).filter(
            self.table.resolved_at == None
        ).count()

    def count_resolved(self) -> int:
        return self.session.query(self.table).filter(
            self.table.resolved_at != None
        ).count()

    def count_by_failure_type(self) -> dict:
        results = self.session.query(
            self.table.failure_type,
            func.count(self.table.id)
        ).group_by(self.table.failure_type).all()
        return {t: c for t, c in results}

    def get_oldest_unresolved(self) -> Optional[str]:
        row = self.session.query(self.table).filter(
            self.table.resolved_at == None
        ).order_by(self.table.routed_at).first()
        return row.routed_at.isoformat() if row else None


class MemoryDLQStore(DLQStore):
    """In-memory DLQ store (for testing)"""

    def __init__(self):
        self._entries = {}

    def insert(self, entry: dict) -> None:
        self._entries[entry["id"]] = entry

    def find_unresolved(self, limit: int = 50) -> List[dict]:
        return [
            e for e in self._entries.values()
            if e.get("resolved_at") is None
        ][:limit]

    def find_unresolved_by_type(self, failure_type: Optional[str] = None) -> List[dict]:
        entries = [
            e for e in self._entries.values()
            if e.get("resolved_at") is None
        ]
        if failure_type:
            entries = [e for e in entries if e.get("failure_type") == failure_type]
        return entries

    def get_by_id(self, dlq_id: str) -> Optional[dict]:
        return self._entries.get(dlq_id)

    def mark_resolved(self, dlq_id: str, notes: str) -> None:
        if dlq_id in self._entries:
            self._entries[dlq_id]["resolved_at"] = datetime.utcnow().isoformat()
            self._entries[dlq_id]["resolution_notes"] = notes

    def increment_retry_count(self, dlq_id: str) -> None:
        if dlq_id in self._entries:
            self._entries[dlq_id]["retry_count"] += 1

    def count_all(self) -> int:
        return len(self._entries)

    def count_unresolved(self) -> int:
        return len([e for e in self._entries.values() if e.get("resolved_at") is None])

    def count_resolved(self) -> int:
        return len([e for e in self._entries.values() if e.get("resolved_at") is not None])

    def count_by_failure_type(self) -> dict:
        types = {}
        for e in self._entries.values():
            ft = e.get("failure_type")
            types[ft] = types.get(ft, 0) + 1
        return types

    def get_oldest_unresolved(self) -> Optional[str]:
        unresolved = [e for e in self._entries.values() if e.get("resolved_at") is None]
        if not unresolved:
            return None
        oldest = min(unresolved, key=lambda e: e["routed_at"])
        return oldest["routed_at"]
'''

    return store


def generate_dlq_system() -> dict:
    """Generate complete DLQ system."""

    imports = '''import uuid
import json
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from abc import ABC, abstractmethod


'''

    module_doc = '''"""
Dead Letter Queue (DLQ) Handler

Prevents event loss when processing fails.

Scenario:
1. Event arrives
2. Projection handler crashes
3. Without DLQ: event lost, data inconsistency
4. With DLQ: event stored, awaits fix + replay

Process:
1. Event processing fails
2. Retries exhausted
3. Route to DLQ (append-only log)
4. Manual investigation
5. Fix root cause
6. Replay event (idempotent)
7. Projections updated
8. Mark as resolved

Result: Zero event loss, full auditability.
"""
'''

    schema = generate_dlq_schema()
    handler = generate_dlq_handler()
    store = generate_dlq_store()

    complete_code = imports + module_doc + "\n" + schema + "\n" + handler + "\n" + store

    return {
        "code": complete_code,
        "pattern": "Dead Letter Queue",
        "module": "dead_letter_queue_handler.py",
    }


def main():
    parser = argparse.ArgumentParser(description="Generate DLQ handler")
    parser.add_argument("--aggregate", help="Aggregate name")
    parser.add_argument("--failure-mode", help="Failure scenario")
    parser.add_argument("--output", choices=["json", "code"], default="code")

    args = parser.parse_args()
    result = generate_dlq_system()

    if args.output == "json":
        metadata = {k: v for k, v in result.items() if k != "code"}
        print(json.dumps(metadata, indent=2))
    else:
        print(result["code"])


if __name__ == "__main__":
    main()
