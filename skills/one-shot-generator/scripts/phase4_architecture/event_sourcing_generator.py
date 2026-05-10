#!/usr/bin/env python3
"""Event Sourcing Generator - Store State as Sequence of Events

Generates:
- Event store (immutable log)
- Event replayer (reconstruct state)
- Snapshot manager (optimization)
- Projections (read models from events)
"""

import sys
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.base_script import setup_logging, timed_run, check_budget

__version__ = "0.7.0"
logger = setup_logging(__name__)


class EventSourcingGenerator:
    """Generates event sourcing patterns."""

    def __init__(self, framework: str):
        self.framework = framework.lower()

    def generate(self) -> Dict[str, str]:
        files = {}
        files['event_sourcing/event_store.py'] = self._event_store()
        files['event_sourcing/event_replayer.py'] = self._event_replayer()
        files['event_sourcing/snapshot.py'] = self._snapshot()
        files['event_sourcing/projection.py'] = self._projection()
        files['event_sourcing/README.md'] = self._readme()
        return files

    def _event_store(self) -> str:
        return '''"""Event Store - Immutable Event Log"""

from typing import List, Dict
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class StoredEvent:
    """Event in event store"""
    event_id: str
    aggregate_id: str
    aggregate_type: str
    event_type: str
    payload: dict
    sequence: int
    timestamp: datetime


class EventStore:
    """Append-only event log"""

    def __init__(self):
        self.events: Dict[str, List[StoredEvent]] = {}
        self.sequence_counter = 0

    def append(self, aggregate_id: str, aggregate_type: str, event_type: str, payload: dict) -> StoredEvent:
        """Append event (immutable)"""
        self.sequence_counter += 1

        stored_event = StoredEvent(
            event_id=f"{aggregate_id}-{self.sequence_counter}",
            aggregate_id=aggregate_id,
            aggregate_type=aggregate_type,
            event_type=event_type,
            payload=payload,
            sequence=self.sequence_counter,
            timestamp=datetime.now()
        )

        if aggregate_id not in self.events:
            self.events[aggregate_id] = []

        self.events[aggregate_id].append(stored_event)
        logger.info(f"Appended {event_type} to {aggregate_id}")
        return stored_event

    def get_events(self, aggregate_id: str) -> List[StoredEvent]:
        """Get all events for aggregate"""
        return self.events.get(aggregate_id, [])

    def get_events_after_sequence(self, aggregate_id: str, sequence: int) -> List[StoredEvent]:
        """Get events after sequence number (for snapshots)"""
        events = self.get_events(aggregate_id)
        return [e for e in events if e.sequence > sequence]

    def get_all_events(self, event_type: str = None) -> List[StoredEvent]:
        """Get all events, optionally filtered by type"""
        all_events = []
        for event_list in self.events.values():
            all_events.extend(event_list)

        if event_type:
            all_events = [e for e in all_events if e.event_type == event_type]

        return sorted(all_events, key=lambda e: e.timestamp)

    def is_immutable(self) -> bool:
        """Event store is immutable (cannot delete/update)"""
        return True
'''

    def _event_replayer(self) -> str:
        return '''"""Event Replayer - Reconstruct State from Events"""

from typing import List, Any
import logging

logger = logging.getLogger(__name__)


class EventReplayer:
    """Reconstructs aggregate state from events"""

    def __init__(self, event_store):
        self.event_store = event_store

    def replay(self, aggregate_id: str, aggregate_class) -> Any:
        """Reconstruct aggregate by replaying events"""
        events = self.event_store.get_events(aggregate_id)

        if not events:
            return None

        # Create new instance
        aggregate = aggregate_class(aggregate_id)

        # Replay each event
        for event in events:
            logger.debug(f"Replaying {event.event_type} on {aggregate_id}")
            aggregate.apply_event(event)

        return aggregate

    def replay_from_snapshot(self, aggregate_id: str, snapshot: 'Snapshot') -> Any:
        """Reconstruct aggregate from snapshot + events"""
        # Restore from snapshot
        aggregate = snapshot.state

        # Replay events after snapshot
        events = self.event_store.get_events_after_sequence(aggregate_id, snapshot.sequence)
        for event in events:
            logger.debug(f"Replaying {event.event_type} on {aggregate_id}")
            aggregate.apply_event(event)

        return aggregate
'''

    def _snapshot(self) -> str:
        return '''"""Snapshots - Optimize Event Replay"""

from dataclasses import dataclass
from typing import Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class Snapshot:
    """Snapshot of aggregate state"""
    aggregate_id: str
    state: Any
    sequence: int
    timestamp: datetime


class SnapshotStore:
    """Store snapshots for faster reconstruction"""

    def __init__(self, event_store, snapshot_frequency: int = 100):
        self.event_store = event_store
        self.snapshot_frequency = snapshot_frequency
        self.snapshots = {}

    def save_snapshot(self, aggregate_id: str, state: Any, sequence: int):
        """Save snapshot"""
        snapshot = Snapshot(
            aggregate_id=aggregate_id,
            state=state,
            sequence=sequence,
            timestamp=datetime.now()
        )
        self.snapshots[aggregate_id] = snapshot
        logger.info(f"Saved snapshot for {aggregate_id} at sequence {sequence}")
        return snapshot

    def get_snapshot(self, aggregate_id: str) -> Snapshot:
        """Get latest snapshot"""
        return self.snapshots.get(aggregate_id)

    def should_snapshot(self, aggregate_id: str, current_sequence: int) -> bool:
        """Check if should create snapshot"""
        snapshot = self.get_snapshot(aggregate_id)

        if not snapshot:
            # Create first snapshot
            return current_sequence >= self.snapshot_frequency

        # Create new snapshot if enough events since last
        events_since = current_sequence - snapshot.sequence
        return events_since >= self.snapshot_frequency

    def delete_old_snapshots(self, aggregate_id: str):
        """Delete old snapshots (keep only latest)"""
        if aggregate_id in self.snapshots:
            # In practice, keep multiple snapshots for version control
            pass
'''

    def _projection(self) -> str:
        return '''"""Projections - Read Models from Event Stream"""

from typing import Dict, List, Any
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class Projection(ABC):
    """Base projection (read model built from events)"""

    @abstractmethod
    def handle_event(self, event):
        """Handle event and update projection"""
        pass

    @abstractmethod
    def get_projection(self, key: str) -> Any:
        """Get projection state"""
        pass


class OrderProjection(Projection):
    """Projection: Orders by customer"""

    def __init__(self):
        self.data = {}

    def handle_event(self, event):
        """Update projection when event occurs"""
        if event.event_type == "OrderCreatedEvent":
            customer_id = event.payload["customer_id"]
            if customer_id not in self.data:
                self.data[customer_id] = {"orders": [], "total": 0.0}
            self.data[customer_id]["orders"].append(event.payload)

        elif event.event_type == "OrderItemAddedEvent":
            customer_id = event.payload["customer_id"]
            amount = event.payload["amount"]
            self.data[customer_id]["total"] += amount

    def get_projection(self, customer_id: str) -> Dict:
        """Get customer orders"""
        return self.data.get(customer_id, {"orders": [], "total": 0.0})

    def get_customer_total_spent(self, customer_id: str) -> float:
        """Get total spent"""
        return self.data.get(customer_id, {}).get("total", 0.0)


class ProjectionManager:
    """Manages multiple projections"""

    def __init__(self, event_store):
        self.event_store = event_store
        self.projections: Dict[str, Projection] = {}

    def register_projection(self, name: str, projection: Projection):
        """Register projection"""
        self.projections[name] = projection
        logger.info(f"Registered projection: {name}")

    def rebuild_projections(self):
        """Rebuild all projections from event log"""
        logger.info("Rebuilding projections...")

        all_events = self.event_store.get_all_events()

        for event in all_events:
            for projection in self.projections.values():
                projection.handle_event(event)

        logger.info("Projections rebuilt")

    def get_projection(self, name: str, key: str) -> Any:
        """Get projection data"""
        if name not in self.projections:
            raise ValueError(f"Unknown projection: {name}")

        return self.projections[name].get_projection(key)
'''

    def _readme(self) -> str:
        return '''# Event Sourcing - Store State as Sequence of Events

## Core Idea

Instead of storing current state, store ALL state changes as events:

```
Database:
Event 1: AccountCreatedEvent(customer_id=1)
Event 2: MoneyDepositedEvent(customer_id=1, amount=100)
Event 3: MoneyWithdrawnEvent(customer_id=1, amount=30)
Event 4: MoneyDepositedEvent(customer_id=1, amount=50)

Current state: balance = 120
```

## Event Store

Immutable append-only log:

```python
from event_sourcing.event_store import EventStore

store = EventStore()

# Append events (never delete or update)
store.append(
    aggregate_id="customer-1",
    aggregate_type="Customer",
    event_type="DepositedEvent",
    payload={"amount": 100}
)

# Get all events for aggregate
events = store.get_events("customer-1")
```

## Event Replayer

Reconstruct aggregate from events:

```python
from event_sourcing.event_replayer import EventReplayer

replayer = EventReplayer(store)

# Replay all events to reconstruct current state
account = replayer.replay("customer-1", Account)
print(account.balance)  # 120
```

## Snapshots

Optimize replay for old aggregates:

```python
from event_sourcing.snapshot import SnapshotStore

snapshot_store = SnapshotStore(event_store, snapshot_frequency=100)

# After 100 events, create snapshot
if snapshot_store.should_snapshot("customer-1", current_seq):
    snapshot_store.save_snapshot("customer-1", account_state, current_seq)

# Later, restore from snapshot + replay only new events
snapshot = snapshot_store.get_snapshot("customer-1")
account = replayer.replay_from_snapshot("customer-1", snapshot)
```

## Projections

Build read models from event stream:

```python
from event_sourcing.projection import OrderProjection, ProjectionManager

projection = OrderProjection()
manager = ProjectionManager(event_store)
manager.register_projection("orders", projection)

# Rebuild projection from all events
manager.rebuild_projections()

# Query projection (instant lookups)
customer_orders = manager.get_projection("orders", "customer-1")
```

## Benefits

- **Complete history**: Never lose change history
- **Audit trail**: See exactly what happened and when
- **Temporal queries**: Ask "what was state at time X?"
- **Event replay**: Reconstruct any state from events
- **Offline-first**: Build projections async after events
- **Multiple read models**: Build different projections for different queries

## Trade-offs

- **Complexity**: More complex than traditional CRUD
- **Consistency**: Eventual consistency for read models
- **Storage**: Store all events (but compress/archive old ones)

## Typical Flow

```
1. User action → Create command
2. Command handler → Generate events
3. Append events to event store
4. Async: Projections consume events, update read models
5. Queries hit read models (fast, eventually consistent)
```

## Example: Bank Account

```python
class Account(AggregateRoot):
    def __init__(self, account_id):
        super().__init__(account_id)
        self.balance = 0

    def deposit(self, amount):
        self.add_event(DepositedEvent(self.id, amount))

    def apply_event(self, event):
        if isinstance(event, DepositedEvent):
            self.balance += event.amount
        elif isinstance(event, WithdrawnEvent):
            self.balance -= event.amount
```
'''


def main():
    with timed_run("event_sourcing_generator") as timer:
        logger.debug("Testing Event Sourcing generation")
        gen = EventSourcingGenerator("python")
        files = gen.generate()
        logger.debug(f"Generated {len(files)} Event Sourcing files")
        for filepath in files:
            print(f"  ✓ {filepath}")
        check_budget("event_sourcing_generator", timer.elapsed_ms, logger)


if __name__ == '__main__':
    main()
