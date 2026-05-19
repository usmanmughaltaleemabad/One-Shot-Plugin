#!/usr/bin/env python3
"""
Phase 4 Event Sourcing: Event Versioning

Handles event schema evolution.
Events are immutable, but schemas change over time.

Strategies:
- Upcasting: new handlers understand old event formats
- Dualing: run old + new logic
- Snapshots: old events → new format

Usage:
    python phase4_event_versioning.py --event OrderCreated --versions 1 2 3

Input: Event name and schema versions
Output: Event versioning with upcasting logic
"""

import argparse
import json
from typing import Any, Dict, Callable, Optional


def generate_event_versioning() -> str:
    """Generate event versioning infrastructure."""

    versioning = '''
class EventVersion:
    """Represents an event schema version"""

    def __init__(self, version: int, schema: dict, upcast_fn: Optional[Callable] = None):
        self.version = version
        self.schema = schema  # Field definitions
        self.upcast_fn = upcast_fn  # Function to convert old→new format

    def upcast(self, event_dict: dict) -> dict:
        """Convert event from previous version to this version"""
        if not self.upcast_fn:
            return event_dict
        return self.upcast_fn(event_dict)


class EventVersionRegistry:
    """
    Manages all event versions.

    When loading old events, automatically upcast to latest schema.
    """

    def __init__(self):
        self._versions = {}  # event_type -> [versions]
        self._latest = {}  # event_type -> latest version

    def register_event(self, event_type: str, versions: List[EventVersion]) -> None:
        """Register all versions of an event type"""
        self._versions[event_type] = {v.version: v for v in versions}
        self._latest[event_type] = max(v.version for v in versions)

    def upcast_event(self, event: dict) -> dict:
        """
        Upcast event to latest version.

        Process:
        1. Get event type and current version
        2. Apply upcasting functions version by version
        3. Return event in latest schema

        Args:
            event: Event dict with "event_type" and "version"

        Returns:
            Event in latest schema version
        """
        event_type = event.get("event_type")
        current_version = event.get("version", 1)

        if event_type not in self._versions:
            return event  # Unknown type, return as-is

        latest_version = self._latest[event_type]
        result = event.copy()

        # Apply upcasting from current version → latest
        for v in range(current_version + 1, latest_version + 1):
            if v in self._versions[event_type]:
                version_obj = self._versions[event_type][v]
                result = version_obj.upcast(result)
                result["version"] = v

        return result


class EventUpcaster:
    """Base class for event upcasting logic"""

    @staticmethod
    def upcast_v1_to_v2(event: dict) -> dict:
        """Example: Add new required field with default"""
        # V1: {{id, name}}
        # V2: {{id, name, status="PENDING"}}
        if "status" not in event:
            event["status"] = "PENDING"
        return event

    @staticmethod
    def upcast_v2_to_v3(event: dict) -> dict:
        """Example: Rename field"""
        # V2: {{id, name}}
        # V3: {{id, display_name}} (rename "name" -> "display_name")
        if "name" in event and "display_name" not in event:
            event["display_name"] = event.pop("name")
        return event
'''

    return versioning


def generate_event_migration_strategies() -> str:
    """Generate event migration strategies."""

    strategies = '''
class EventMigrationStrategy:
    """Base class for event migration strategies"""

    def migrate(self, event: dict) -> dict:
        """Migrate event to new format"""
        raise NotImplementedError()


class UpcasterStrategy(EventMigrationStrategy):
    """
    Upcasting: new handlers understand old formats.

    When old event arrives:
    1. Recognize old schema (check version)
    2. Apply upcasting function(s)
    3. Return event in new schema

    Pros: Simple, no storage changes
    Cons: Handler complexity (must understand all versions)
    """

    def __init__(self, registry: EventVersionRegistry):
        self.registry = registry

    def migrate(self, event: dict) -> dict:
        """Upcast event to latest version"""
        return self.registry.upcast_event(event)


class DualtingStrategy(EventMigrationStrategy):
    """
    Dualing: run old + new logic in parallel.

    For critical events, keep supporting old AND new simultaneously.
    Compare results. Migrate only when confident.

    Pros: Safe, can verify new logic is correct
    Cons: Overhead of running both
    """

    def __init__(self, old_handler: Callable, new_handler: Callable):
        self.old_handler = old_handler
        self.new_handler = new_handler
        self.divergences = []

    def migrate(self, event: dict) -> dict:
        """Run both handlers, check for divergence"""
        old_result = self.old_handler(event)
        new_result = self.new_handler(event)

        if old_result != new_result:
            self.divergences.append({{
                "event_id": event.get("event_id"),
                "old": old_result,
                "new": new_result
            }})

        return new_result  # Use new result


class SnapshotMigrationStrategy(EventMigrationStrategy):
    """
    Snapshot migration: create new snapshots with migrated events.

    For large-scale migrations, snapshot events to new format.

    Pros: One-time cost, fast queries afterward
    Cons: Requires downtime/careful orchestration
    """

    def __init__(self, snapshot_store, event_store):
        self.snapshot_store = snapshot_store
        self.event_store = event_store

    def migrate(self, event: dict) -> dict:
        """Create snapshot from old events"""
        # Load all events for aggregate
        # Upcast each
        # Create snapshot at new version
        pass
'''

    return strategies


def generate_versioning_system() -> dict:
    """Generate complete event versioning system."""

    imports = '''from typing import Any, Dict, Callable, List, Optional


'''

    module_doc = '''"""
Event Versioning: Handle schema evolution

Events are immutable facts. But schemas change.

Challenge: Old events have old schema. New handlers expect new schema.

Solution: Versioning + Upcasting

When loading event:
1. Check version
2. If old, upcast to new schema
3. Handler receives event in expected format

Strategies:
- Upcasting: Implicit conversion when loading
- Dualing: Run old + new in parallel
- Snapshots: Snapshot→new schema one-time
"""
'''

    versioning = generate_event_versioning()
    strategies = generate_event_migration_strategies()

    # Example
    example = '''
# Example Usage

# Define versions
v1_schema = {"id": str, "name": str}
v2_schema = {"id": str, "name": str, "status": str}
v3_schema = {"id": str, "display_name": str, "status": str}

# Register versions with upcasting
registry = EventVersionRegistry()

versions = [
    EventVersion(1, v1_schema),
    EventVersion(2, v2_schema, upcast_fn=EventUpcaster.upcast_v1_to_v2),
    EventVersion(3, v3_schema, upcast_fn=EventUpcaster.upcast_v2_to_v3)
]

registry.register_event("OrderCreated", versions)

# Old event arrives
old_event = {
    "event_type": "OrderCreated",
    "version": 1,
    "id": "order-123",
    "name": "Widget"
}

# Automatic upcasting
new_event = registry.upcast_event(old_event)
# Result: {"event_type": "OrderCreated", "version": 3, "id": "order-123", "display_name": "Widget", "status": "PENDING"}
'''

    complete_code = imports + module_doc + "\n" + versioning + "\n" + strategies + "\n" + example

    return {
        "code": complete_code,
        "capabilities": ["upcasting", "dualing", "snapshots", "migration"],
        "module": "event_versioning.py",
    }


def main():
    parser = argparse.ArgumentParser(description="Generate event versioning")
    parser.add_argument("--event", help="Event type")
    parser.add_argument("--versions", nargs="+", type=int, help="Version numbers")
    parser.add_argument("--output", choices=["json", "code"], default="code")

    args = parser.parse_args()
    result = generate_versioning_system()

    if args.output == "json":
        metadata = {k: v for k, v in result.items() if k != "code"}
        print(json.dumps(metadata, indent=2))
    else:
        print(result["code"])


if __name__ == "__main__":
    main()
