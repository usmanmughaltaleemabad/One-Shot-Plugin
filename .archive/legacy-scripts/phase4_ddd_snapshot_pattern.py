#!/usr/bin/env python3
"""
Phase 4 DDD: Snapshot Pattern Generator

Generates Snapshot pattern for event sourcing optimization.
Snapshots cache aggregate state at intervals to avoid replaying all events.

Usage:
    python phase4_ddd_snapshot_pattern.py --aggregate Order --snapshot-interval 50

Input: Aggregate name and snapshot frequency
Output: Snapshot classes and event replay optimization
"""

import argparse
import json
from datetime import datetime
from typing import Any, Optional


def generate_snapshot_class(aggregate_name: str) -> str:
    """Generate Snapshot class for aggregate."""

    snapshot_code = f'''
class {aggregate_name}Snapshot:
    """
    Snapshot of {{aggregate_name}} state at specific version.

    Snapshots avoid replaying all events from beginning.
    Instead: load snapshot -> replay events from snapshot version.

    Storage: Save to snapshot store when aggregate version % interval == 0
    """

    def __init__(
        self,
        aggregate_id: str,
        version: int,
        state: dict,
        timestamp: Optional[datetime] = None
    ):
        self.aggregate_id = aggregate_id
        self.version = version  # Version when snapshot was taken
        self.state = state  # Full aggregate state
        self.timestamp = timestamp or datetime.utcnow()

    def to_dict(self) -> dict:
        """Serialize snapshot for storage"""
        return {{
            "aggregate_id": self.aggregate_id,
            "version": self.version,
            "state": self.state,
            "timestamp": self.timestamp.isoformat()
        }}

    @classmethod
    def from_dict(cls, data: dict) -> "{aggregate_name}Snapshot":
        """Deserialize snapshot from storage"""
        return cls(
            aggregate_id=data["aggregate_id"],
            version=data["version"],
            state=data["state"],
            timestamp=datetime.fromisoformat(data["timestamp"])
        )

    def to_aggregate(self) -> {aggregate_name}Aggregate:
        """Reconstruct aggregate from snapshot"""
        # TODO: Create aggregate from snapshot state
        return {aggregate_name}Aggregate.from_dict(self.state)

    def __repr__(self):
        return f"{aggregate_name}Snapshot(id='{{self.aggregate_id}}', version={{self.version}})"
'''

    return snapshot_code.replace("{{aggregate_name}}", aggregate_name)


def generate_snapshot_store() -> str:
    """Generate Snapshot Store interface and implementations."""

    store_code = '''
class SnapshotStore:
    """Abstract Snapshot Store interface"""

    def save(self, snapshot: "Snapshot") -> None:
        """Save snapshot"""
        raise NotImplementedError()

    def load(self, aggregate_id: str, max_version: int = None) -> Optional["Snapshot"]:
        """Load latest snapshot (optionally before specific version)"""
        raise NotImplementedError()

    def delete(self, aggregate_id: str) -> None:
        """Delete snapshots for aggregate"""
        raise NotImplementedError()


class SQLSnapshotStore(SnapshotStore):
    """SQL-based Snapshot Store"""

    def __init__(self, session, model_class):
        self.session = session
        self.model = model_class

    def save(self, snapshot: "Snapshot") -> None:
        row = self.model(
            aggregate_id=snapshot.aggregate_id,
            version=snapshot.version,
            state=json.dumps(snapshot.state),
            timestamp=snapshot.timestamp
        )
        self.session.add(row)
        self.session.flush()

    def load(self, aggregate_id: str, max_version: int = None) -> Optional["Snapshot"]:
        query = self.session.query(self.model).filter(
            self.model.aggregate_id == aggregate_id
        )
        if max_version:
            query = query.filter(self.model.version <= max_version)

        row = query.order_by(self.model.version.desc()).first()
        if not row:
            return None

        return Snapshot.from_dict({
            "aggregate_id": row.aggregate_id,
            "version": row.version,
            "state": json.loads(row.state),
            "timestamp": row.timestamp.isoformat()
        })

    def delete(self, aggregate_id: str) -> None:
        self.session.query(self.model).filter(
            self.model.aggregate_id == aggregate_id
        ).delete()
        self.session.flush()


class MemorySnapshotStore(SnapshotStore):
    """In-memory Snapshot Store (testing)"""

    def __init__(self):
        self._store = {}  # aggregate_id -> [snapshots sorted by version]

    def save(self, snapshot: "Snapshot") -> None:
        if snapshot.aggregate_id not in self._store:
            self._store[snapshot.aggregate_id] = []
        self._store[snapshot.aggregate_id].append(snapshot)

    def load(self, aggregate_id: str, max_version: int = None) -> Optional["Snapshot"]:
        if aggregate_id not in self._store:
            return None

        snapshots = self._store[aggregate_id]
        if max_version:
            snapshots = [s for s in snapshots if s.version <= max_version]

        return max(snapshots, key=lambda s: s.version) if snapshots else None

    def delete(self, aggregate_id: str) -> None:
        if aggregate_id in self._store:
            del self._store[aggregate_id]
'''

    return store_code


def generate_event_store_with_snapshots(aggregate_name: str) -> str:
    """Generate Event Store that uses snapshots for optimization."""

    store_code = f'''
class {aggregate_name}EventStoreWithSnapshots:
    """
    Event Store with Snapshot optimization.

    Strategy:
    1. Save snapshot every N events (e.g., 50)
    2. When loading: find latest snapshot + replay events after
    3. If no snapshot: replay from beginning
    """

    SNAPSHOT_INTERVAL = 50  # Create snapshot every 50 events

    def __init__(self, event_store, snapshot_store):
        self.event_store = event_store
        self.snapshot_store = snapshot_store

    def save(self, aggregate: {aggregate_name}Aggregate) -> None:
        \"\"\"
        Save aggregate events and optionally create snapshot.

        Creates snapshot if: aggregate.version % SNAPSHOT_INTERVAL == 0
        \"\"\"
        # Save events
        for event in aggregate.changes:
            self.event_store.append_event(event)

        # Create snapshot at intervals
        if aggregate.version % self.SNAPSHOT_INTERVAL == 0:
            snapshot = {aggregate_name}Snapshot(
                aggregate_id=aggregate.id,
                version=aggregate.version,
                state=aggregate.to_dict()
            )
            self.snapshot_store.save(snapshot)

        aggregate.mark_changes_as_committed()

    def load(self, aggregate_id: str) -> {aggregate_name}Aggregate:
        \"\"\"
        Load aggregate from snapshot + events.

        Optimization:
        - If snapshot exists: start from snapshot, replay events after
        - If no snapshot: replay from beginning
        \"\"\"
        # Try to load snapshot
        snapshot = self.snapshot_store.load(aggregate_id)

        if snapshot:
            # Start from snapshot state
            aggregate = snapshot.to_aggregate()
            start_version = snapshot.version + 1
        else:
            # No snapshot: create empty aggregate
            aggregate = {aggregate_name}Aggregate(id=aggregate_id)
            start_version = 1

        # Replay events after snapshot version
        events = self.event_store.get_events(aggregate_id, start_version)
        for event in events:
            aggregate._apply_event(event)

        return aggregate

    def delete(self, aggregate_id: str) -> None:
        \"\"\"Delete aggregate and snapshots\"\"\"
        self.event_store.delete_events(aggregate_id)
        self.snapshot_store.delete(aggregate_id)

    def compact_snapshots(self, aggregate_id: str) -> None:
        \"\"\"
        Compact snapshots (delete old ones, keep latest).

        Reduces storage: keep only most recent snapshot.
        \"\"\"
        latest = self.snapshot_store.load(aggregate_id)
        if latest:
            # Delete all and re-save only latest
            self.snapshot_store.delete(aggregate_id)
            self.snapshot_store.save(latest)
'''

    return store_code.replace("{{aggregate_name}}", aggregate_name)


def generate_snapshots(aggregate_name: str, interval: int = 50) -> dict:
    """
    Generate Snapshot pattern for aggregate.

    Args:
        aggregate_name: Aggregate name (e.g., Order)
        interval: Snapshot frequency (create every N events)

    Returns:
        dict with snapshot classes and event store
    """

    imports = '''import json
from datetime import datetime
from typing import Any, Optional, List


'''

    module_doc = f'''"""
Snapshot Pattern for {{aggregate_name}}

Snapshots optimize event replay by caching aggregate state.

Problem: With event sourcing, loading aggregate requires replaying ALL events.
This is slow for aggregates with thousands of events.

Solution: Create snapshot every N events. Load snapshot + replay only recent events.

Performance:
- Without snapshots: O(n) where n = total event count
- With snapshots: O(m) where m = events since snapshot (much smaller)

Example:
- 1000 events total, snapshot every 50 events
- Without: replay 1000 events
- With: find latest snapshot (at ~1000), replay ~0 events
- Speedup: 50-100x faster
""".replace("{{aggregate_name}}", aggregate_name)

    snapshot = generate_snapshot_class(aggregate_name)
    snapshot_store = generate_snapshot_store()
    event_store = generate_event_store_with_snapshots(aggregate_name)

    complete_code = imports + module_doc + "\n" + snapshot + "\n" + snapshot_store + "\n" + event_store

    return {
        "code": complete_code,
        "aggregate": aggregate_name,
        "interval": interval,
        "pattern": "Snapshot",
        "module": f"{aggregate_name.lower()}_snapshot.py",
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate Snapshot pattern for event sourcing"
    )
    parser.add_argument(
        "--aggregate", required=True,
        help="Aggregate name (e.g., Order)"
    )
    parser.add_argument(
        "--snapshot-interval", type=int, default=50,
        help="Create snapshot every N events"
    )
    parser.add_argument(
        "--output", choices=["json", "code"], default="code",
        help="Output format"
    )

    args = parser.parse_args()

    result = generate_snapshots(args.aggregate, args.snapshot_interval)

    if args.output == "json":
        metadata = {k: v for k, v in result.items() if k != "code"}
        print(json.dumps(metadata, indent=2))
    else:
        print(result["code"])
        print("\n# Metadata")
        metadata = {k: v for k, v in result.items() if k != "code"}
        print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
