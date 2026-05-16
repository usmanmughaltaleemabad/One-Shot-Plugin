#!/usr/bin/env python3
"""
Phase 4 DDD: Domain Events Generator

Generates Domain Event classes for capturing business-significant state changes.
Domain Events are published when aggregates change, enabling event sourcing and event-driven architecture.

Usage:
    python phase4_ddd_domain_events.py --aggregate Order --events OrderCreated OrderShipped OrderCancelled

Input: Aggregate name and event names
Output: Domain Event classes with schema validation
"""

import argparse
import json
from datetime import datetime
from typing import Any, Optional


def generate_domain_event(event_name: str, aggregate_name: str, attributes: dict) -> str:
    """
    Generate a single Domain Event class.

    Args:
        event_name: Event name (e.g., OrderCreated)
        aggregate_name: Aggregate that generates event (e.g., Order)
        attributes: Dict of attribute_name -> type (e.g., {"total": "Money", "items": "list"})

    Returns:
        str with Domain Event class code
    """

    # Build constructor parameters
    params = ", ".join([f"{name}: {type_}" for name, type_ in attributes.items()])

    # Build instance assignments
    assignments = "\n        ".join([
        f"self.{name} = {name}" for name in attributes.keys()
    ])

    event_code = f"""
class {event_name}:
    \"\"\"
    Domain Event: {event_name}

    Published when: {aggregate_name} state changes in a business-significant way
    Handled by: Event handlers, event store, event projections
    \"\"\"

    event_type = "{event_name}"
    aggregate_type = "{aggregate_name}"
    version = 1

    def __init__(
        self,
        aggregate_id: str,
        {params},
        timestamp: Optional[datetime] = None,
        event_id: Optional[str] = None
    ):
        self.event_id = event_id or str(uuid.uuid4())
        self.aggregate_id = aggregate_id
        self.aggregate_type = self.aggregate_type
        self.event_type = self.event_type
        self.timestamp = timestamp or datetime.utcnow()
        self.version = self.version
        {assignments}

    def to_dict(self) -> dict:
        \"\"\"Serialize event for storage/transmission\"\"\"
        return {{
            "event_id": self.event_id,
            "event_type": self.event_type,
            "aggregate_id": self.aggregate_id,
            "aggregate_type": self.aggregate_type,
            "timestamp": self.timestamp.isoformat(),
            "version": self.version,
            {", ".join(f"'{name}': self.{name}" for name in attributes.keys())}
        }}

    @classmethod
    def from_dict(cls, data: dict) -> "{event_name}":
        \"\"\"Deserialize event from storage\"\"\"
        return cls(
            aggregate_id=data["aggregate_id"],
            {", ".join(f"{name}=data['{name}']" for name in attributes.keys())},
            timestamp=datetime.fromisoformat(data["timestamp"]),
            event_id=data["event_id"]
        )

    def __repr__(self):
        attrs = ", ".join(f"{{k}}={{getattr(self, k)!r}}" for k in ["{}", {", ".join(f"'{name}'" for name in attributes.keys())}])
        return f"{event_name}(aggregate_id='{{self.aggregate_id}}', {{attrs}})"
"""

    return event_code


def generate_event_handler(event_name: str, aggregate_name: str) -> str:
    """Generate event handler interface and base implementation."""

    handler_name = f"{event_name}Handler"

    return f"""
class {handler_name}:
    \"\"\"Handler for {event_name} domain event\"\"\"

    def handle(self, event: {event_name}) -> None:
        \"\"\"
        Handle {event_name} event.

        Common handler responsibilities:
        - Update read models (projections)
        - Trigger side effects (send email, queue task)
        - Validate business rules
        - Update external systems

        Args:
            event: {event_name} event with aggregate state change
        \"\"\"
        raise NotImplementedError("Implement in concrete handler")


class {handler_name}UpdateProjection({handler_name}):
    \"\"\"Update read model projection on {event_name}\"\"\"

    def __init__(self, projection_store):
        self.projection_store = projection_store

    def handle(self, event: {event_name}) -> None:
        \"\"\"Update projection based on event data\"\"\"
        # TODO: Update read model
        # self.projection_store.update_projection(event)
        pass


class {handler_name}PublishNotification({handler_name}):
    \"\"\"Send notification on {event_name}\"\"\"

    def __init__(self, notification_service):
        self.notification_service = notification_service

    def handle(self, event: {event_name}) -> None:
        \"\"\"Send notification to users\"\"\"
        # TODO: Queue notification task
        # self.notification_service.notify(event)
        pass
"""


def generate_event_bus() -> str:
    """Generate Event Bus for publishing and subscribing to domain events."""

    return """
class EventBus:
    \"\"\"
    Event Bus: publish domain events, subscribe to handlers

    Responsibilities:
    - Store subscriptions (event type -> list of handlers)
    - Publish events to all subscribed handlers
    - Handle async event processing if needed
    - Log event history
    \"\"\"

    def __init__(self):
        self._subscriptions = {}  # event_type -> [handler, ...]
        self._event_history = []

    def subscribe(self, event_type: str, handler) -> None:
        \"\"\"Subscribe handler to event type\"\"\"
        if event_type not in self._subscriptions:
            self._subscriptions[event_type] = []
        self._subscriptions[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler) -> None:
        \"\"\"Unsubscribe handler from event type\"\"\"
        if event_type in self._subscriptions:
            self._subscriptions[event_type].remove(handler)

    def publish(self, event) -> None:
        \"\"\"Publish event to all subscribed handlers\"\"\"
        event_type = event.event_type

        # Record in history
        self._event_history.append(event)

        # Publish to handlers
        if event_type in self._subscriptions:
            for handler in self._subscriptions[event_type]:
                try:
                    handler.handle(event)
                except Exception as e:
                    # TODO: Log handler error
                    # Decide: retry, DLQ, or continue?
                    raise

    def get_events(self, aggregate_id: str = None) -> list:
        \"\"\"Get event history, optionally filtered by aggregate\"\"\"
        if not aggregate_id:
            return self._event_history
        return [e for e in self._event_history if e.aggregate_id == aggregate_id]

    def clear_history(self) -> None:
        \"\"\"Clear event history (for testing)\"\"\"
        self._event_history.clear()

    def __repr__(self):
        return f"EventBus(subscriptions={{self._subscriptions.keys()}}, history={{len(self._event_history)}} events)"
"""


def generate_domain_events(aggregate_name: str, event_names: list) -> dict:
    """
    Generate complete Domain Event system for aggregate.

    Args:
        aggregate_name: Name of aggregate (e.g., Order)
        event_names: List of event names (e.g., [OrderCreated, OrderShipped])

    Returns:
        dict with event classes, handlers, event bus, and metadata
    """

    imports = '''import uuid
import json
from datetime import datetime
from typing import Any, Optional
from abc import ABC, abstractmethod


'''

    # Generate events (with simple attributes for demo)
    event_code = "\n".join([
        generate_domain_event(event, aggregate_name, {"data": "dict"})
        for event in event_names
    ])

    # Generate handlers
    handler_code = "\n".join([
        generate_event_handler(event, aggregate_name)
        for event in event_names
    ])

    # Event Bus
    event_bus_code = generate_event_bus()

    # Module docstring
    module_doc = f'''"""
Domain Events for {{aggregate_name}} Aggregate

Domain Events represent business-significant changes in aggregate state.
They are:
- Immutable snapshots of what happened
- Stored for event sourcing
- Published to handlers for reactions (side effects, projections)
- Part of the ubiquitous language

Events: {{', '.join(event_names)}}
""".replace("{{aggregate_name}}", aggregate_name).replace("{{', '.join(event_names)}}", ", ".join(event_names))

    complete_code = imports + module_doc + "\n\n" + event_code + "\n\n" + handler_code + "\n\n" + event_bus_code

    return {
        "code": complete_code,
        "aggregate": aggregate_name,
        "events": event_names,
        "event_count": len(event_names),
        "handler_count": len(event_names),
        "has_event_bus": True,
        "module": f"{aggregate_name.lower()}_events.py",
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate Domain Events for aggregate"
    )
    parser.add_argument(
        "--aggregate", required=True,
        help="Aggregate name (e.g., Order)"
    )
    parser.add_argument(
        "--events", nargs="+", required=True,
        help="Event names (e.g., OrderCreated OrderShipped OrderCancelled)"
    )
    parser.add_argument(
        "--output", choices=["json", "code"], default="code",
        help="Output format"
    )

    args = parser.parse_args()

    result = generate_domain_events(args.aggregate, args.events)

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
