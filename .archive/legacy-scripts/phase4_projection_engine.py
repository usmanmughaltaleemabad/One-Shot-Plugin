#!/usr/bin/env python3
"""
Phase 4 CQRS: Projection Engine

Updates read models (denormalized query data) when domain events occur.
Projections keep read models in sync with write model (eventually).

Usage:
    python phase4_projection_engine.py --aggregate Order --projections OrderListView OrderDetailView

Input: Aggregate and projection names
Output: Projection handlers and sync logic
"""

import argparse
import json
from typing import Any, Callable, Dict, List, Optional


def generate_projection(projection_name: str) -> str:
    """Generate projection handler."""

    proj_code = f'''
class {projection_name}:
    """
    Projection: {projection_name}

    Denormalized read model optimized for specific queries.
    Updated via event handlers.

    Lifecycle:
    - Created: empty state
    - Event arrives → handler updates data
    - Query hits projection → fast read
    """

    def __init__(self, store):
        self.store = store
        self.name = "{projection_name}"

    def handle_event(self, event: dict) -> None:
        """
        Update projection when event occurs.

        Args:
            event: Domain event
        """
        event_type = event.get("event_type")

        if event_type == "Created":
            self._on_created(event)
        elif event_type == "Updated":
            self._on_updated(event)
        elif event_type == "Deleted":
            self._on_deleted(event)

    def _on_created(self, event: dict) -> None:
        """Handle Created event"""
        # Update read model based on event data
        pass

    def _on_updated(self, event: dict) -> None:
        """Handle Updated event"""
        # Merge changes into read model
        pass

    def _on_deleted(self, event: dict) -> None:
        """Handle Deleted event"""
        # Remove from read model
        pass

    def rebuild(self, events: List[dict]) -> None:
        """Rebuild projection from all events"""
        for event in events:
            self.handle_event(event)
'''

    return proj_code


def generate_projection_engine() -> str:
    """Generate projection engine that coordinates all projections."""

    engine = '''
class ProjectionEngine:
    """
    Projection Engine: coordinates updates to all read models.

    Responsibilities:
    - Route events to projection handlers
    - Handle eventual consistency
    - Manage projection rebuilds
    - Track last processed event
    """

    def __init__(self):
        self._projections = {}  # name -> projection handler
        self._last_processed_event_id = None

    def register_projection(self, name: str, projection) -> None:
        """Register projection handler"""
        self._projections[name] = projection

    def handle_event(self, event: dict) -> None:
        """
        Process domain event: update all projections.

        Called when event arrives from event bus.

        Args:
            event: Domain event
        """
        # Update all projections
        for projection in self._projections.values():
            try:
                projection.handle_event(event)
            except Exception as e:
                # TODO: Log error, possibly DLQ to retry later
                raise ProjectionUpdateFailure(f"Failed to update projection: {str(e)}")

        # Track progress (for crash recovery)
        self._last_processed_event_id = event.get("event_id")

    def rebuild_projections(self, events: List[dict]) -> None:
        """
        Rebuild all projections from event stream.

        Use case: Recovery after crash, new projection added

        Args:
            events: All events in order
        """
        for projection in self._projections.values():
            projection.rebuild(events)

    def get_last_processed_event_id(self) -> Optional[str]:
        """For crash recovery: know which events were already processed"""
        return self._last_processed_event_id

    def __repr__(self):
        return f"ProjectionEngine({len(self._projections)} projections)"


class ProjectionUpdateFailure(Exception):
    """Projection update failed"""
    pass
'''

    return engine


def generate_event_handler_registry() -> str:
    """Generate registry mapping events to projection handlers."""

    registry = '''
class ProjectionEventHandlerRegistry:
    """
    Maps events to projection handlers.

    When event occurs, route to appropriate projection handlers.
    """

    def __init__(self, projection_engine):
        self.engine = projection_engine
        self._handlers = {}  # event_type -> [projection handlers]

    def subscribe_to_event(self, event_type: str, projection) -> None:
        """Subscribe projection to event type"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(projection)

    def publish_event(self, event: dict) -> None:
        """
        Publish event to interested projections.

        Called by event bus. Routes to specific handlers based on event type.

        Args:
            event: Domain event
        """
        event_type = event.get("event_type")

        # Route to specific handlers
        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                try:
                    handler.handle_event(event)
                except Exception as e:
                    # Log and continue (at least one projection updated)
                    # TODO: Implement DLQ for failed updates
                    pass

        # Also update via engine (broadcasts to all)
        self.engine.handle_event(event)
'''

    return registry


def generate_projections_system(aggregate_name: str, projections: list) -> dict:
    """Generate complete projection system."""

    imports = '''from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod


'''

    module_doc = f'''"""
Projection Engine for {{aggregate_name}}

Projections are denormalized read models.

Write Model (Commands/Aggregates):
  - Normalized, enforces invariants
  - Slow for complex queries

Read Model (Projections):
  - Denormalized, optimized for queries
  - Built from events
  - Eventually consistent

Pattern: Event → ProjectionEngine → Update all Projections
""".replace("{{aggregate_name}}", aggregate_name)

    # Generate projections
    proj_classes = "\n".join([
        generate_projection(p)
        for p in projections
    ])

    # Engine
    engine = generate_projection_engine()

    # Registry
    registry = generate_event_handler_registry()

    # Example usage
    example = f'''
# Example Usage

# Create projection engine
engine = ProjectionEngine()

# Create and register projections
{{aggregate_name.lower()}}_list = {{aggregate_name}}ListProjection(list_store)
{{aggregate_name.lower()}}_detail = {{aggregate_name}}DetailProjection(detail_store)

engine.register_projection("list", {{aggregate_name.lower()}}_list)
engine.register_projection("detail", {{aggregate_name.lower()}}_detail)

# When event arrives from event bus
event = event_store.get_event("order-123")
engine.handle_event(event)  # Updates both projections

# On crash recovery
all_events = event_store.get_all_events()
engine.rebuild_projections(all_events)
'''

    complete_code = imports + module_doc + "\n" + proj_classes + "\n" + engine + "\n" + registry + "\n" + example.replace("{{aggregate_name}}", aggregate_name).replace("{{aggregate_name.lower()}}", aggregate_name.lower())

    return {
        "code": complete_code,
        "aggregate": aggregate_name,
        "projections": projections,
        "projection_count": len(projections),
        "module": f"{aggregate_name.lower()}_projections.py",
    }


def main():
    parser = argparse.ArgumentParser(description="Generate projection engine")
    parser.add_argument("--aggregate", required=True, help="Aggregate name")
    parser.add_argument("--projections", nargs="+", required=True, help="Projection names")
    parser.add_argument("--output", choices=["json", "code"], default="code")

    args = parser.parse_args()
    result = generate_projections_system(args.aggregate, args.projections)

    if args.output == "json":
        metadata = {k: v for k, v in result.items() if k != "code"}
        print(json.dumps(metadata, indent=2))
    else:
        print(result["code"])


if __name__ == "__main__":
    main()
