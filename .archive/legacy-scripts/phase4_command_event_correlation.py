#!/usr/bin/env python3
"""
Phase 4 CQRS: Command-Event Correlation

Tracks relationship: Command → Events

Why?
- Audit trail: which command caused which events?
- Debugging: event happened, trace back to originating command
- Causality: understand event ordering and dependencies
- Compliance: prove which command triggered each change

Usage:
    python phase4_command_event_correlation.py --command CreateOrder --events OrderCreated OrderConfirmed

Input: Command and resulting events
Output: Correlation tracking with causality chains
"""

import argparse
import json
from typing import Any, Dict, List, Optional
from datetime import datetime


def generate_correlation_schema() -> str:
    """Generate correlation tracking schema."""

    schema = '''
class CorrelationSchema:
    """
    Command-Event Correlation schema.

    Maps commands to events they generate.

    Fields:
    - correlation_id: Unique ID linking command + events
    - command_id: Which command
    - command_type: e.g., CreateOrder, UpdateOrder
    - command_data: Command input
    - user_id: Who executed command
    - timestamp: When command executed
    - event_ids: Which events were generated
    - event_types: Types of events
    - status: completed, failed, partial
    """

    SQL = """
    CREATE TABLE IF NOT EXISTS command_event_correlation (
        correlation_id VARCHAR(255) PRIMARY KEY,
        command_id VARCHAR(255) NOT NULL,
        command_type VARCHAR(255) NOT NULL,
        aggregate_id VARCHAR(255) NOT NULL,
        command_data JSON NOT NULL,
        user_id VARCHAR(255),
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status VARCHAR(50) DEFAULT 'pending',  -- pending, completed, failed, partial
        INDEX idx_command (command_id),
        INDEX idx_aggregate (aggregate_id),
        INDEX idx_correlation (correlation_id)
    );

    CREATE TABLE IF NOT EXISTS event_causality (
        id VARCHAR(255) PRIMARY KEY,
        event_id VARCHAR(255) NOT NULL,
        correlation_id VARCHAR(255) NOT NULL,
        command_id VARCHAR(255) NOT NULL,
        event_type VARCHAR(255) NOT NULL,
        sequence INT NOT NULL,  -- Order of event in command
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_event (event_id),
        INDEX idx_correlation (correlation_id),
        INDEX idx_sequence (sequence)
    );
    """
'''

    return schema


def generate_correlation_tracker() -> str:
    """Generate command-event correlation tracker."""

    tracker = '''
class CommandEventCorrelation:
    """
    Tracks command → event causality.

    Usage:
    1. Command arrives
    2. Create correlation ID
    3. Execute command, collect generated events
    4. Record: correlation_id + [event_ids]
    5. Query: given event, find originating command
    """

    def __init__(self, correlation_store):
        self.store = correlation_store

    def start_command(
        self,
        command_id: str,
        command_type: str,
        aggregate_id: str,
        command_data: dict,
        user_id: Optional[str] = None
    ) -> str:
        """
        Start tracking a command.

        Returns:
            correlation_id: Use this when recording events
        """
        correlation_id = f"corr-{command_id}-{datetime.utcnow().timestamp()}"

        self.store.create_correlation(
            correlation_id=correlation_id,
            command_id=command_id,
            command_type=command_type,
            aggregate_id=aggregate_id,
            command_data=command_data,
            user_id=user_id
        )

        return correlation_id

    def record_event(
        self,
        correlation_id: str,
        event_id: str,
        event_type: str,
        sequence: int
    ) -> None:
        """Record event as result of command"""
        self.store.create_causality(
            event_id=event_id,
            correlation_id=correlation_id,
            event_type=event_type,
            sequence=sequence
        )

    def record_events(
        self,
        correlation_id: str,
        events: List[dict]
    ) -> None:
        """Record all events from command"""
        for i, event in enumerate(events, start=1):
            self.record_event(
                correlation_id=correlation_id,
                event_id=event.get("event_id"),
                event_type=event.get("event_type"),
                sequence=i
            )

    def complete_command(self, correlation_id: str, status: str = "completed") -> None:
        """Mark command as completed"""
        self.store.update_correlation_status(correlation_id, status)

    def get_command_for_event(self, event_id: str) -> Optional[dict]:
        """
        Reverse lookup: given event, find command.

        Use case: Event happened, debug: what caused it?
        """
        causality = self.store.get_causality_by_event(event_id)
        if not causality:
            return None

        correlation = self.store.get_correlation_by_id(causality["correlation_id"])
        return correlation

    def get_events_for_command(self, command_id: str) -> List[dict]:
        """
        Forward lookup: given command, find events.

        Use case: Executed command, verify events generated.
        """
        correlation = self.store.get_correlation_by_command(command_id)
        if not correlation:
            return []

        causalities = self.store.get_causalities_by_correlation(
            correlation["correlation_id"]
        )
        return causalities

    def get_causality_chain(self, aggregate_id: str) -> List[dict]:
        """
        Get full causality chain for aggregate.

        Timeline of commands and events: what happened, in order.

        Returns:
            List of {command, events, timestamp, user}
        """
        correlations = self.store.get_correlations_by_aggregate(aggregate_id)
        result = []

        for corr in correlations:
            events = self.store.get_causalities_by_correlation(corr["correlation_id"])
            result.append({
                "command_id": corr["command_id"],
                "command_type": corr["command_type"],
                "user": corr.get("user_id"),
                "timestamp": corr["timestamp"],
                "events": events,
                "status": corr["status"]
            })

        return result

    def get_correlation_stats(self, aggregate_id: str) -> dict:
        """Statistics for aggregate"""
        correlations = self.store.get_correlations_by_aggregate(aggregate_id)
        return {
            "total_commands": len(correlations),
            "completed": sum(1 for c in correlations if c["status"] == "completed"),
            "failed": sum(1 for c in correlations if c["status"] == "failed"),
            "average_events_per_command": sum(
                len(self.store.get_causalities_by_correlation(c["correlation_id"]))
                for c in correlations
            ) / len(correlations) if correlations else 0
        }
'''

    return tracker


def generate_correlation_store() -> str:
    """Generate correlation store implementations."""

    store = '''
class CorrelationStore:
    """Abstract correlation store"""

    def create_correlation(self, **kwargs) -> None:
        raise NotImplementedError()

    def create_causality(self, **kwargs) -> None:
        raise NotImplementedError()

    def get_correlation_by_id(self, correlation_id: str) -> Optional[dict]:
        raise NotImplementedError()

    def get_correlation_by_command(self, command_id: str) -> Optional[dict]:
        raise NotImplementedError()

    def get_correlations_by_aggregate(self, aggregate_id: str) -> List[dict]:
        raise NotImplementedError()

    def get_causalities_by_correlation(self, correlation_id: str) -> List[dict]:
        raise NotImplementedError()

    def get_causality_by_event(self, event_id: str) -> Optional[dict]:
        raise NotImplementedError()

    def update_correlation_status(self, correlation_id: str, status: str) -> None:
        raise NotImplementedError()


class SQLCorrelationStore(CorrelationStore):
    """SQL-based correlation store"""

    def __init__(self, session, correlation_table, causality_table):
        self.session = session
        self.corr_table = correlation_table
        self.cause_table = causality_table

    def create_correlation(self, **kwargs) -> None:
        row = self.corr_table(**kwargs)
        self.session.add(row)
        self.session.flush()

    def create_causality(self, **kwargs) -> None:
        row = self.cause_table(**kwargs)
        self.session.add(row)
        self.session.flush()

    def get_correlation_by_id(self, correlation_id: str) -> Optional[dict]:
        row = self.session.query(self.corr_table).filter(
            self.corr_table.correlation_id == correlation_id
        ).first()
        return row.to_dict() if row else None

    def get_correlation_by_command(self, command_id: str) -> Optional[dict]:
        row = self.session.query(self.corr_table).filter(
            self.corr_table.command_id == command_id
        ).first()
        return row.to_dict() if row else None

    def get_correlations_by_aggregate(self, aggregate_id: str) -> List[dict]:
        rows = self.session.query(self.corr_table).filter(
            self.corr_table.aggregate_id == aggregate_id
        ).all()
        return [r.to_dict() for r in rows]

    def get_causalities_by_correlation(self, correlation_id: str) -> List[dict]:
        rows = self.session.query(self.cause_table).filter(
            self.cause_table.correlation_id == correlation_id
        ).order_by(self.cause_table.sequence).all()
        return [r.to_dict() for r in rows]

    def get_causality_by_event(self, event_id: str) -> Optional[dict]:
        row = self.session.query(self.cause_table).filter(
            self.cause_table.event_id == event_id
        ).first()
        return row.to_dict() if row else None

    def update_correlation_status(self, correlation_id: str, status: str) -> None:
        self.session.query(self.corr_table).filter(
            self.corr_table.correlation_id == correlation_id
        ).update({"status": status})
        self.session.flush()


class MemoryCorrelationStore(CorrelationStore):
    """In-memory correlation store (for testing)"""

    def __init__(self):
        self._correlations = {}
        self._causalities = {}

    def create_correlation(self, **kwargs) -> None:
        self._correlations[kwargs["correlation_id"]] = kwargs

    def create_causality(self, **kwargs) -> None:
        self._causalities[kwargs["id"]] = kwargs

    def get_correlation_by_id(self, correlation_id: str) -> Optional[dict]:
        return self._correlations.get(correlation_id)

    def get_correlation_by_command(self, command_id: str) -> Optional[dict]:
        for corr in self._correlations.values():
            if corr.get("command_id") == command_id:
                return corr
        return None

    def get_correlations_by_aggregate(self, aggregate_id: str) -> List[dict]:
        return [
            c for c in self._correlations.values()
            if c.get("aggregate_id") == aggregate_id
        ]

    def get_causalities_by_correlation(self, correlation_id: str) -> List[dict]:
        causes = [
            c for c in self._causalities.values()
            if c.get("correlation_id") == correlation_id
        ]
        return sorted(causes, key=lambda x: x.get("sequence", 0))

    def get_causality_by_event(self, event_id: str) -> Optional[dict]:
        for cause in self._causalities.values():
            if cause.get("event_id") == event_id:
                return cause
        return None

    def update_correlation_status(self, correlation_id: str, status: str) -> None:
        if correlation_id in self._correlations:
            self._correlations[correlation_id]["status"] = status
'''

    return store


def generate_correlation_system() -> dict:
    """Generate complete correlation system."""

    imports = '''import uuid
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod


'''

    module_doc = '''"""
Command-Event Correlation

Tracks: which command caused which events?

Why?
- Audit trail: prove causality
- Debugging: event happened → what command caused it?
- Compliance: link user action → system changes
- Understanding: visualize command → event causality chains

Process:
1. User executes command
2. Create correlation_id
3. Command handler generates events
4. Record: correlation_id + event_ids
5. Query: given event, find command
6. Query: given command, find events
7. Causality chain: all commands + events for aggregate

Example:
User: "Create order"
Command: CreateOrder(user_id, items)
Correlation: corr-001
Events: OrderCreated, PaymentProcessed, InventoryAllocated
Timeline: Command 1:02pm → Event 1:02pm → Event 1:02:01pm → Event 1:02:05pm
Result: Audit trail of what user did and what system events occurred.
"""
'''

    schema = generate_correlation_schema()
    tracker = generate_correlation_tracker()
    store = generate_correlation_store()

    complete_code = imports + module_doc + "\n" + schema + "\n" + tracker + "\n" + store

    return {
        "code": complete_code,
        "pattern": "Command-Event Correlation",
        "module": "command_event_correlation.py",
    }


def main():
    parser = argparse.ArgumentParser(description="Generate command-event correlation")
    parser.add_argument("--command", help="Command type")
    parser.add_argument("--events", nargs="+", help="Resulting event types")
    parser.add_argument("--output", choices=["json", "code"], default="code")

    args = parser.parse_args()
    result = generate_correlation_system()

    if args.output == "json":
        metadata = {k: v for k, v in result.items() if k != "code"}
        print(json.dumps(metadata, indent=2))
    else:
        print(result["code"])


if __name__ == "__main__":
    main()
