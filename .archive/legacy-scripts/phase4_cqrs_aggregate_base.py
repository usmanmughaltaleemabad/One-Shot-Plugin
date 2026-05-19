#!/usr/bin/env python3
"""
Phase 4 CQRS: Aggregate Base Class

Base class for aggregates supporting CQRS pattern.

Combines:
- Command execution (write side)
- Event generation (immutable log)
- Eventual consistency (read models)
- Transaction management

Aggregates are bounded contexts. This base provides:
- Command handlers
- Event storage
- Transaction semantics
- Read model synchronization

Usage:
    python phase4_cqrs_aggregate_base.py --aggregate Order

Input: Aggregate name
Output: Base class with CQRS support
"""

import argparse
import json
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime


def generate_cqrs_aggregate_base() -> str:
    """Generate CQRS aggregate base class."""

    base = '''
class CQRSAggregate:
    """
    Base class for CQRS aggregates.

    Responsibilities:
    - Execute commands (modify state)
    - Generate events (record what happened)
    - Apply events (replay from event log)
    - Track uncommitted events
    - Support read model updates

    Transaction model:
    1. Load aggregate (replay events)
    2. Execute command → modify state, generate events
    3. Store events (write model)
    4. Publish events (trigger read model updates)
    5. Return to user
    """

    def __init__(self, aggregate_id: str, aggregate_type: str):
        self.aggregate_id = aggregate_id
        self.aggregate_type = aggregate_type
        self.version = 0  # Event count
        self.uncommitted_events = []
        self.uncommitted_changes = []
        self._is_new = True
        self._is_deleted = False

    # ===================
    # Command Execution
    # ===================

    def execute_command(self, command: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Execute command: modify state, generate events.

        Override in subclass with command routing logic.

        Args:
            command: Command dict with "command_type" and data

        Returns:
            List of generated events
        """
        command_type = command.get("command_type")

        if command_type == "Create":
            return self._handle_create(command)
        elif command_type == "Update":
            return self._handle_update(command)
        elif command_type == "Delete":
            return self._handle_delete(command)
        else:
            raise UnknownCommandException(f"Unknown command: {command_type}")

    def _handle_create(self, command: Dict) -> List[Dict]:
        """Handle Create command"""
        raise NotImplementedError()

    def _handle_update(self, command: Dict) -> List[Dict]:
        """Handle Update command"""
        raise NotImplementedError()

    def _handle_delete(self, command: Dict) -> List[Dict]:
        """Handle Delete command"""
        raise NotImplementedError()

    # ===================
    # Event Management
    # ===================

    def emit_event(self, event_type: str, event_data: Dict) -> None:
        """
        Generate event (record what happened).

        Called during command execution.
        Event stored in memory, persisted on save.

        Args:
            event_type: Type of event
            event_data: Event payload
        """
        event = {
            "event_id": f"{self.aggregate_id}-{self.version}-{event_type}",
            "aggregate_id": self.aggregate_id,
            "aggregate_type": self.aggregate_type,
            "event_type": event_type,
            "version": self.version + 1,
            "timestamp": datetime.utcnow().isoformat(),
            "data": event_data
        }

        self.uncommitted_events.append(event)
        self.version += 1

        # Apply to state
        self.apply_event(event)

    def get_uncommitted_events(self) -> List[Dict]:
        """Get events not yet persisted"""
        return self.uncommitted_events

    def mark_events_as_committed(self) -> None:
        """Clear uncommitted events after persistence"""
        self.uncommitted_events = []
        self._is_new = False

    def apply_event(self, event: Dict) -> None:
        """
        Apply event to state (replay).

        Called during load (event sourcing) and during command execution.
        Override in subclass to update aggregate state.

        Args:
            event: Event to apply
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

    def _apply_created(self, event: Dict) -> None:
        """Apply Created event to state"""
        raise NotImplementedError()

    def _apply_updated(self, event: Dict) -> None:
        """Apply Updated event to state"""
        raise NotImplementedError()

    def _apply_deleted(self, event: Dict) -> None:
        """Apply Deleted event to state"""
        raise NotImplementedError()

    # ===================
    # State Serialization
    # ===================

    def to_dict(self) -> Dict:
        """Serialize aggregate state"""
        raise NotImplementedError()

    @classmethod
    def from_dict(cls, data: Dict) -> "CQRSAggregate":
        """Deserialize aggregate state (from snapshot)"""
        raise NotImplementedError()

    # ===================
    # Invariants
    # ===================

    def assert_invariants(self) -> None:
        """
        Verify business rule invariants.

        Override in subclass to enforce domain rules.

        Raises:
            InvariantViolation: If invariant violated
        """
        pass

    # ===================
    # Deletion
    # ===================

    def delete(self) -> None:
        """Mark aggregate as deleted"""
        self._is_deleted = True
        self.emit_event("Deleted", {})

    def is_deleted(self) -> bool:
        """Check if aggregate is deleted"""
        return self._is_deleted

    # ===================
    # Transaction
    # ===================

    def is_new(self) -> bool:
        """Check if this is a new aggregate (not yet saved)"""
        return self._is_new

    def get_version(self) -> int:
        """Get current version (for optimistic locking)"""
        return self.version


class CQRSAggregateRepository:
    """
    Repository for CQRS aggregates.

    Responsibilities:
    - Load aggregate (replay from event store)
    - Save aggregate (persist events)
    - Update read models
    """

    def __init__(self, event_store, read_model_updater, correlation_tracker):
        self.event_store = event_store
        self.read_model_updater = read_model_updater
        self.correlation_tracker = correlation_tracker

    def load(self, aggregate_id: str, aggregate_class) -> CQRSAggregate:
        """
        Load aggregate from event store.

        Replays all events to reconstruct state.
        """
        events = self.event_store.get_events(aggregate_id)
        if not events:
            return None

        aggregate = aggregate_class(aggregate_id, aggregate_class.__name__)

        for event in events:
            aggregate.apply_event(event)
            aggregate.version = event.get("version", 0)

        aggregate.mark_events_as_committed()
        return aggregate

    def save(
        self,
        aggregate: CQRSAggregate,
        correlation_id: Optional[str] = None
    ) -> None:
        """
        Save aggregate (persist events, update read models).

        Process:
        1. Get uncommitted events
        2. Store in event store
        3. Publish to read model updaters
        4. Record in correlation log
        5. Mark as committed
        """
        events = aggregate.get_uncommitted_events()
        if not events:
            return

        # Store events (write model)
        self.event_store.append_events(aggregate.aggregate_id, events)

        # Update read models (eventual consistency)
        for event in events:
            self.read_model_updater.handle_event(event)

            # Record causality
            if correlation_id:
                self.correlation_tracker.record_event(
                    correlation_id=correlation_id,
                    event_id=event["event_id"],
                    event_type=event["event_type"],
                    sequence=events.index(event) + 1
                )

        # Mark as persisted
        aggregate.mark_events_as_committed()

    def delete(self, aggregate_id: str) -> None:
        """Delete aggregate"""
        aggregate = self.load(aggregate_id, CQRSAggregate)
        if aggregate:
            aggregate.delete()
            self.save(aggregate)


class UnknownCommandException(Exception):
    """Unknown command type"""
    pass


class UnknownEventException(Exception):
    """Unknown event type"""
    pass


class InvariantViolation(Exception):
    """Business rule invariant violated"""
    pass
'''

    return base


def generate_example_aggregate() -> str:
    """Generate example aggregate implementation."""

    example = '''
# Example: Order Aggregate

class OrderAggregate(CQRSAggregate):
    """Order aggregate with CQRS support"""

    def __init__(self, aggregate_id: str):
        super().__init__(aggregate_id, "Order")
        self.customer_id = None
        self.items = []
        self.total = 0
        self.status = "pending"

    # Command handlers
    def _handle_create(self, command: Dict) -> List[Dict]:
        """Create order"""
        if self.status != "pending":
            raise InvariantViolation("Cannot create: already created")

        self.emit_event("OrderCreated", {
            "customer_id": command["customer_id"],
            "items": command["items"],
            "total": command["total"]
        })

        return self.get_uncommitted_events()

    def _handle_update(self, command: Dict) -> List[Dict]:
        """Update order"""
        if self.status != "pending":
            raise InvariantViolation("Cannot update: order already confirmed")

        self.emit_event("OrderUpdated", {
            "items": command.get("items"),
            "total": command.get("total")
        })

        return self.get_uncommitted_events()

    def _handle_delete(self, command: Dict) -> List[Dict]:
        """Cancel order"""
        self.delete()
        return self.get_uncommitted_events()

    # Event handlers
    def _apply_created(self, event: Dict) -> None:
        data = event.get("data", {})
        self.customer_id = data.get("customer_id")
        self.items = data.get("items", [])
        self.total = data.get("total", 0)
        self.status = "created"

    def _apply_updated(self, event: Dict) -> None:
        data = event.get("data", {})
        if "items" in data:
            self.items = data["items"]
        if "total" in data:
            self.total = data["total"]

    def _apply_deleted(self, event: Dict) -> None:
        self.status = "cancelled"

    # Serialization
    def to_dict(self) -> Dict:
        return {
            "aggregate_id": self.aggregate_id,
            "version": self.version,
            "customer_id": self.customer_id,
            "items": self.items,
            "total": self.total,
            "status": self.status
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "OrderAggregate":
        agg = cls(data["aggregate_id"])
        agg.version = data["version"]
        agg.customer_id = data["customer_id"]
        agg.items = data["items"]
        agg.total = data["total"]
        agg.status = data["status"]
        return agg

    # Invariants
    def assert_invariants(self) -> None:
        if self.total < 0:
            raise InvariantViolation("Total cannot be negative")
        if not self.items:
            raise InvariantViolation("Order must have items")
'''

    return example


def generate_cqrs_base_system() -> dict:
    """Generate complete CQRS aggregate base system."""

    imports = '''from typing import Any, Dict, List, Optional
from datetime import datetime
from abc import ABC, abstractmethod


'''

    module_doc = '''"""
CQRS Aggregate Base Class

Foundation for aggregates in CQRS system.

Responsibilities:
1. Execute commands (write side): modify state
2. Generate events (immutable log): record changes
3. Apply events (replay): reconstruct state
4. Track uncommitted events: for persistence
5. Update read models (eventual): async consistency

Transaction:
User → Command → Aggregate.execute_command()
       → Aggregate.emit_event() [multiple]
       → Repository.save()
           → EventStore.append()
           → ReadModelUpdater.handle_event() [async]
           → CorrelationTracker.record()
       → return to user

Eventually consistent:
- Write model (events): immediately consistent
- Read models: consistent within milliseconds
"""
'''

    base = generate_cqrs_aggregate_base()
    example = generate_example_aggregate()

    complete_code = imports + module_doc + "\n" + base + "\n" + example

    return {
        "code": complete_code,
        "pattern": "CQRS Aggregate Base",
        "module": "cqrs_aggregate_base.py",
    }


def main():
    parser = argparse.ArgumentParser(description="Generate CQRS aggregate base")
    parser.add_argument("--aggregate", help="Aggregate name")
    parser.add_argument("--output", choices=["json", "code"], default="code")

    args = parser.parse_args()
    result = generate_cqrs_base_system()

    if args.output == "json":
        metadata = {k: v for k, v in result.items() if k != "code"}
        print(json.dumps(metadata, indent=2))
    else:
        print(result["code"])


if __name__ == "__main__":
    main()
