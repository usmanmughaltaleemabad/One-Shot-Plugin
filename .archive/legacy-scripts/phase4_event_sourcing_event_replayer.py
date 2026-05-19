#!/usr/bin/env python3
"""
Phase 4 Event Sourcing: Event Replayer

Rebuilds aggregate state from event stream.
Critical for: loading aggregates, rebuilding from snapshots, temporal queries.

Usage:
    python phase4_event_sourcing_event_replayer.py --aggregate Order --events 100

Input: Aggregate class and event count
Output: Event replay logic with versioning support
"""

import argparse
import json
from typing import List, Any, Optional


def generate_event_replayer(aggregate_name: str) -> str:
    """Generate event replayer for aggregate."""

    replayer_code = f'''
class {aggregate_name}EventReplayer:
    """
    Replays events to reconstruct {{aggregate_name}} state.

    Process:
    1. Start with empty aggregate
    2. Apply each event in sequence
    3. Aggregate state is reconstructed

    Enables:
    - Loading aggregates from event store
    - Rebuilding from snapshots (start from snapshot state)
    - Temporal queries (state at any point in time)
    """

    def __init__(self, aggregate_class):
        self.aggregate_class = aggregate_class

    def replay_events(self, aggregate_id: str, events: List[dict]) -> Any:
        """
        Replay events into new aggregate.

        Args:
            aggregate_id: ID of aggregate to create
            events: List of events in order

        Returns:
            Reconstructed aggregate with state applied
        """
        # Create empty aggregate
        aggregate = self.aggregate_class(id=aggregate_id)

        # Apply each event in sequence
        for event in events:
            aggregate.apply_event(event)

        # Aggregate now has full state from replayed events
        return aggregate

    def replay_events_from_snapshot(
        self,
        aggregate_id: str,
        snapshot: dict,
        events_after: List[dict]
    ) -> Any:
        """
        Replay from snapshot + events.

        Optimization: instead of replaying all events, start from snapshot
        and only replay events that happened after.

        Args:
            aggregate_id: Aggregate ID
            snapshot: Snapshot state (can be dict or Snapshot object)
            events_after: Events after snapshot version

        Returns:
            Reconstructed aggregate
        """
        # Reconstruct from snapshot state
        if isinstance(snapshot, dict):
            aggregate = self.aggregate_class.from_dict(snapshot)
        else:
            aggregate = snapshot.to_aggregate()

        # Apply only events after snapshot
        for event in events_after:
            aggregate.apply_event(event)

        return aggregate

    def replay_events_at_version(
        self,
        aggregate_id: str,
        events: List[dict],
        target_version: int
    ) -> Any:
        """
        Temporal query: replay events up to specific version.

        Use case: "What was the state at version 50?"

        Args:
            aggregate_id: Aggregate ID
            events: All events
            target_version: Maximum version to apply

        Returns:
            Aggregate state at target version
        """
        aggregate = self.aggregate_class(id=aggregate_id)

        for event in events:
            if event.get("version", 0) > target_version:
                break
            aggregate.apply_event(event)

        return aggregate

    def replay_events_at_timestamp(
        self,
        aggregate_id: str,
        events: List[dict],
        target_timestamp: str
    ) -> Any:
        """
        Temporal query: replay events up to timestamp.

        Use case: "What was the state at 2026-05-16 12:00:00?"

        Args:
            aggregate_id: Aggregate ID
            events: All events
            target_timestamp: ISO format timestamp

        Returns:
            Aggregate state at target timestamp
        """
        from datetime import datetime

        aggregate = self.aggregate_class(id=aggregate_id)
        target_dt = datetime.fromisoformat(target_timestamp)

        for event in events:
            event_dt = datetime.fromisoformat(event.get("timestamp", ""))
            if event_dt > target_dt:
                break
            aggregate.apply_event(event)

        return aggregate

    def get_aggregate_history(
        self,
        aggregate_id: str,
        events: List[dict]
    ) -> List[dict]:
        """
        Get timeline of aggregate states (version by version).

        Use case: "Show me how this order changed over time"

        Returns:
            List of (version, state) tuples
        """
        aggregate = self.aggregate_class(id=aggregate_id)
        history = []

        for event in events:
            aggregate.apply_event(event)
            history.append({{
                "version": event.get("version"),
                "timestamp": event.get("timestamp"),
                "event_type": event.get("event_type"),
                "state": aggregate.to_dict()
            }})

        return history
'''

    return replayer_code.replace("{{aggregate_name}}", aggregate_name)


def generate_aggregate_apply_event_interface() -> str:
    """Generate interface for aggregates to support event replay."""

    interface = '''
class EventSourcedAggregate:
    """
    Base class for aggregates that support event sourcing.

    Subclasses must implement apply_event() to handle each event type.
    """

    def apply_event(self, event: dict) -> None:
        """
        Apply event to aggregate (changes state).

        Called during replay. Event represents what happened.

        Args:
            event: Domain event with type and data
        """
        event_type = event.get("event_type")

        if event_type == "Created":
            self._apply_created(event)
        elif event_type == "Updated":
            self._apply_updated(event)
        elif event_type == "Deleted":
            self._apply_deleted(event)
        else:
            raise UnknownEventException(f"Cannot apply {event_type}")

    def _apply_created(self, event: dict) -> None:
        """Apply Created event"""
        raise NotImplementedError()

    def _apply_updated(self, event: dict) -> None:
        """Apply Updated event"""
        raise NotImplementedError()

    def _apply_deleted(self, event: dict) -> None:
        """Apply Deleted event"""
        raise NotImplementedError()

    @classmethod
    def from_dict(cls, data: dict) -> "EventSourcedAggregate":
        """Reconstruct from dict (e.g., from snapshot)"""
        raise NotImplementedError()

    def to_dict(self) -> dict:
        """Serialize to dict"""
        raise NotImplementedError()


class UnknownEventException(Exception):
    """Event type not recognized"""
    pass
'''

    return interface


def generate_replayer_tests() -> str:
    """Generate test examples for replayer."""

    tests = '''
# Test Examples

import pytest

class TestEventReplayer:
    """Test event replayer"""

    def test_replay_events_reconstructs_state(self):
        """Replaying events should reconstruct aggregate state"""
        replayer = OrderEventReplayer(OrderAggregate)

        events = [
            {{
                "event_type": "Created",
                "aggregate_id": "order-123",
                "version": 1,
                "timestamp": "2026-05-16T10:00:00",
                "data": {{"customer": "Alice", "total": 100}}
            }},
            {{
                "event_type": "Updated",
                "aggregate_id": "order-123",
                "version": 2,
                "timestamp": "2026-05-16T10:05:00",
                "data": {{"total": 150}}
            }}
        ]

        order = replayer.replay_events("order-123", events)

        assert order.id == "order-123"
        assert order.version == 2
        assert order.total == 150

    def test_replay_from_snapshot_skips_early_events(self):
        """Replaying from snapshot should only apply events after snapshot"""
        replayer = OrderEventReplayer(OrderAggregate)

        snapshot = {{"id": "order-123", "version": 5, "total": 500}}
        events_after = [
            {{
                "event_type": "Updated",
                "version": 6,
                "timestamp": "2026-05-16T10:10:00",
                "data": {{"total": 600}}
            }}
        ]

        order = replayer.replay_events_from_snapshot("order-123", snapshot, events_after)

        assert order.version == 6
        assert order.total == 600

    def test_temporal_query_at_version(self):
        """Should reconstruct state at specific version"""
        replayer = OrderEventReplayer(OrderAggregate)

        events = [
            {{"event_type": "Created", "version": 1, "data": {{"total": 100}}}},
            {{"event_type": "Updated", "version": 2, "data": {{"total": 200}}}},
            {{"event_type": "Updated", "version": 3, "data": {{"total": 300}}}}
        ]

        # State at version 2
        order_v2 = replayer.replay_events_at_version("order-123", events, 2)
        assert order_v2.version == 2
        assert order_v2.total == 200

    def test_get_aggregate_history(self):
        """Should return timeline of states"""
        replayer = OrderEventReplayer(OrderAggregate)

        events = [
            {{"event_type": "Created", "version": 1, "timestamp": "2026-05-16T10:00:00"}},
            {{"event_type": "Updated", "version": 2, "timestamp": "2026-05-16T10:05:00"}},
        ]

        history = replayer.get_aggregate_history("order-123", events)

        assert len(history) == 2
        assert history[0]["version"] == 1
        assert history[1]["version"] == 2
'''

    return tests


def generate_event_replayer_system(aggregate_name: str) -> dict:
    """Generate complete event replayer system."""

    imports = '''from typing import List, Any, Optional
from datetime import datetime
from abc import ABC, abstractmethod


'''

    module_doc = f'''"""
Event Replayer for {{aggregate_name}}

Rebuilds aggregate state by replaying events.

Why replay?
- Loading aggregates from event store
- Rebuilding from snapshots (optimization)
- Temporal queries (state at any point)
- Testing (replay events in different order)

Performance:
- With snapshots: O(events since snapshot) instead of O(all events)
- Typical case: 50-100 events to replay (milliseconds)
- Worst case: thousands of events, still acceptable
""".replace("{{aggregate_name}}", aggregate_name)

    replayer = generate_event_replayer(aggregate_name)
    interface = generate_aggregate_apply_event_interface()
    tests = generate_replayer_tests()

    complete_code = imports + module_doc + "\n" + interface + "\n" + replayer + "\n" + tests

    return {
        "code": complete_code,
        "aggregate": aggregate_name,
        "capabilities": ["replay_from_beginning", "replay_from_snapshot", "temporal_queries", "history"],
        "module": f"{aggregate_name.lower()}_replayer.py",
    }


def main():
    parser = argparse.ArgumentParser(description="Generate event replayer")
    parser.add_argument("--aggregate", required=True, help="Aggregate name (e.g., Order)")
    parser.add_argument("--output", choices=["json", "code"], default="code")

    args = parser.parse_args()
    result = generate_event_replayer_system(args.aggregate)

    if args.output == "json":
        metadata = {k: v for k, v in result.items() if k != "code"}
        print(json.dumps(metadata, indent=2))
    else:
        print(result["code"])


if __name__ == "__main__":
    main()
