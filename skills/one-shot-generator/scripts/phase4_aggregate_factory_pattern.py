#!/usr/bin/env python3
"""
Phase 4 Aggregate Factory Pattern

Creates aggregates with proper dependencies injected.

Problem: Aggregates have dependencies
- Event store
- Repository
- Validators
- Event bus
- Cache
- Correlation tracker

Hard-code them? No → tightly coupled, hard to test.

Solution: Factory pattern with dependency injection.
- Register dependencies
- Factory creates aggregates with all dependencies
- Clean code, testable, decoupled

Usage:
    python phase4_aggregate_factory_pattern.py --aggregate Order

Input: Aggregate name
Output: Factory with DI container
"""

import argparse
import json
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime


def generate_aggregate_factory() -> str:
    """Generate aggregate factory."""

    factory = '''
class AggregateFactory:
    """
    Factory for creating aggregates with dependencies.

    Manages:
    1. Dependency registration
    2. Aggregate instantiation
    3. Dependency injection
    4. Lifecycle management

    Usage:
    factory = AggregateFactory()
    factory.register_dependency("event_store", event_store)
    factory.register_dependency("cache", cache)
    order = factory.create_aggregate(OrderAggregate, "order-123")
    """

    def __init__(self):
        self._dependencies = {}
        self._factories = {}

    def register_dependency(self, name: str, instance: Any) -> None:
        """Register a dependency"""
        self._dependencies[name] = instance

    def register_factory(self, aggregate_type: str, factory_fn: Callable) -> None:
        """Register custom factory for aggregate type"""
        self._factories[aggregate_type] = factory_fn

    def get_dependency(self, name: str) -> Optional[Any]:
        """Get registered dependency"""
        return self._dependencies.get(name)

    def create_aggregate(
        self,
        aggregate_class,
        aggregate_id: str,
        **kwargs
    ) -> Any:
        """
        Create aggregate with dependencies injected.

        Args:
            aggregate_class: Aggregate class
            aggregate_id: ID of aggregate
            **kwargs: Additional arguments

        Returns:
            Aggregate instance with dependencies
        """
        aggregate_type = aggregate_class.__name__

        # Check for custom factory
        if aggregate_type in self._factories:
            return self._factories[aggregate_type](aggregate_id, **kwargs)

        # Create with standard DI
        aggregate = aggregate_class(aggregate_id)

        # Inject dependencies
        if hasattr(aggregate, "set_event_store"):
            aggregate.set_event_store(self._dependencies.get("event_store"))

        if hasattr(aggregate, "set_repository"):
            aggregate.set_repository(self._dependencies.get("repository"))

        if hasattr(aggregate, "set_cache"):
            aggregate.set_cache(self._dependencies.get("cache"))

        if hasattr(aggregate, "set_event_bus"):
            aggregate.set_event_bus(self._dependencies.get("event_bus"))

        if hasattr(aggregate, "set_correlation_tracker"):
            aggregate.set_correlation_tracker(
                self._dependencies.get("correlation_tracker")
            )

        if hasattr(aggregate, "set_validators"):
            aggregate.set_validators(self._dependencies.get("validators", []))

        return aggregate

    def create_aggregate_with_events(
        self,
        aggregate_class,
        aggregate_id: str,
        events: List[Dict]
    ) -> Any:
        """
        Create aggregate and replay events.

        Used when loading from event store.
        """
        aggregate = self.create_aggregate(aggregate_class, aggregate_id)

        # Replay events
        for event in events:
            aggregate.apply_event(event)

        aggregate.mark_events_as_committed()
        return aggregate
'''

    return factory


def generate_dependency_container() -> str:
    """Generate DI container."""

    container = '''
class DependencyContainer:
    """
    IoC container for managing dependencies.

    Patterns:
    1. Singleton: one instance (event_store, cache)
    2. Transient: new instance each time (validators)
    3. Factory: custom creation logic (aggregates)
    """

    def __init__(self):
        self._singletons = {}
        self._factories = {}
        self._transient = {}

    def register_singleton(self, name: str, factory_fn: Callable) -> None:
        """Register singleton (created once, reused)"""
        self._singletons[name] = None  # Will be created on first use
        self._factories[name] = factory_fn

    def register_transient(self, name: str, factory_fn: Callable) -> None:
        """Register transient (created each time)"""
        self._transient[name] = factory_fn

    def register_factory(self, name: str, factory_fn: Callable) -> None:
        """Register factory (custom creation)"""
        self._factories[name] = factory_fn

    def resolve(self, name: str) -> Any:
        """
        Resolve dependency.

        If singleton and already created: return cached
        If singleton and not created: create and cache
        If transient: create new each time
        """
        # Check singleton cache
        if name in self._singletons:
            if self._singletons[name] is None:
                # Create singleton
                factory = self._factories[name]
                self._singletons[name] = factory()
            return self._singletons[name]

        # Check transient
        if name in self._transient:
            factory = self._transient[name]
            return factory()

        # Check factory
        if name in self._factories:
            factory = self._factories[name]
            return factory()

        raise DependencyNotFound(f"Dependency '{name}' not registered")

    def resolve_all(self, *names: str) -> List[Any]:
        """Resolve multiple dependencies"""
        return [self.resolve(name) for name in names]

    def build_container_report(self) -> Dict:
        """Debug: show what's registered"""
        return {
            "singletons": list(self._singletons.keys()),
            "transient": list(self._transient.keys()),
            "factories": list(self._factories.keys())
        }


class DependencyNotFound(Exception):
    """Dependency not registered"""
    pass
'''

    return container


def generate_configuration() -> str:
    """Generate configuration builder."""

    config = '''
class FactoryConfiguration:
    """
    Fluent configuration builder for factory.

    Example:
    (FactoryConfiguration()
        .with_event_store(PostgresEventStore(...))
        .with_cache(MemoryCache())
        .with_validators([UniqueEmailValidator(), ...])
        .build())
    """

    def __init__(self):
        self.factory = AggregateFactory()
        self.container = DependencyContainer()

    def with_event_store(self, event_store: Any) -> "FactoryConfiguration":
        """Register event store"""
        self.factory.register_dependency("event_store", event_store)
        self.container.register_singleton("event_store", lambda: event_store)
        return self

    def with_repository(self, repository: Any) -> "FactoryConfiguration":
        """Register repository"""
        self.factory.register_dependency("repository", repository)
        self.container.register_singleton("repository", lambda: repository)
        return self

    def with_cache(self, cache: Any) -> "FactoryConfiguration":
        """Register cache"""
        self.factory.register_dependency("cache", cache)
        self.container.register_singleton("cache", lambda: cache)
        return self

    def with_event_bus(self, event_bus: Any) -> "FactoryConfiguration":
        """Register event bus"""
        self.factory.register_dependency("event_bus", event_bus)
        self.container.register_singleton("event_bus", lambda: event_bus)
        return self

    def with_correlation_tracker(self, tracker: Any) -> "FactoryConfiguration":
        """Register correlation tracker"""
        self.factory.register_dependency("correlation_tracker", tracker)
        return self

    def with_validators(self, validators: List[Any]) -> "FactoryConfiguration":
        """Register validators"""
        self.factory.register_dependency("validators", validators)
        return self

    def with_custom_factory(
        self,
        aggregate_type: str,
        factory_fn: Callable
    ) -> "FactoryConfiguration":
        """Register custom factory for aggregate type"""
        self.factory.register_factory(aggregate_type, factory_fn)
        return self

    def build(self) -> AggregateFactory:
        """Build configured factory"""
        return self.factory

    def build_with_container(self) -> tuple:
        """Build factory + container"""
        return (self.factory, self.container)
'''

    return config


def generate_example_usage() -> str:
    """Generate example usage."""

    example = '''
# Example: OrderAggregate with DI

class OrderAggregate:
    """Order aggregate with dependency injection"""

    def __init__(self, aggregate_id: str):
        self.aggregate_id = aggregate_id
        self.event_store = None
        self.cache = None
        self.validators = []
        self.correlation_tracker = None

    def set_event_store(self, event_store) -> None:
        self.event_store = event_store

    def set_cache(self, cache) -> None:
        self.cache = cache

    def set_validators(self, validators: List) -> None:
        self.validators = validators

    def set_correlation_tracker(self, tracker) -> None:
        self.correlation_tracker = tracker

    def create_order(self, command: Dict) -> None:
        # Validate using injected validators
        for validator in self.validators:
            validator.validate(command)

        # Emit event
        self.emit_event("OrderCreated", command)

        # Record in cache if available
        if self.cache:
            self.cache.cache_aggregate(self.aggregate_id, self)

        # Record correlation if available
        if self.correlation_tracker:
            self.correlation_tracker.record_command(
                command_id=command.get("command_id"),
                aggregate_id=self.aggregate_id
            )


# Setup

event_store = PostgresEventStore(connection_string)
cache = CQRSCache(event_store)
validators = [
    EmailValidator(),
    AmountValidator(),
    InventoryValidator()
]

factory = (FactoryConfiguration()
    .with_event_store(event_store)
    .with_cache(cache)
    .with_validators(validators)
    .build())

# Usage

order = factory.create_aggregate(OrderAggregate, "order-123")
order.create_order({
    "customer_email": "alice@example.com",
    "items": [...],
    "total": 100
})
'''

    return example


def generate_factory_system() -> dict:
    """Generate complete factory system."""

    imports = '''from typing import Any, Callable, Dict, List, Optional
from datetime import datetime


'''

    module_doc = '''"""
Aggregate Factory Pattern

Creates aggregates with dependency injection.

Problem: Aggregates need many dependencies
- Event store (load/save events)
- Cache (avoid replaying)
- Validators (enforce invariants)
- Event bus (publish events)
- Correlation tracker (audit trail)

Hard-coding dependencies?
- Tightly coupled
- Hard to test (can't mock dependencies)
- Repeated code
- Breaks single responsibility

Solution: Factory with DI
- Dependencies registered in container
- Factory creates aggregates with all deps
- Easy to test (mock dependencies)
- Clean, decoupled code

Patterns:
1. Singleton: one EventStore per app
2. Transient: new Validator each time
3. Factory: custom aggregate creation

Example:
(FactoryConfiguration()
    .with_event_store(PostgresEventStore)
    .with_cache(MemoryCache)
    .with_validators([EmailValidator, AmountValidator])
    .build())
"""
'''

    factory = generate_aggregate_factory()
    container = generate_dependency_container()
    config = generate_configuration()
    example = generate_example_usage()

    complete_code = imports + module_doc + "\n" + factory + "\n" + container + "\n" + config + "\n" + example

    return {
        "code": complete_code,
        "pattern": "Aggregate Factory",
        "module": "aggregate_factory_pattern.py",
    }


def main():
    parser = argparse.ArgumentParser(description="Generate aggregate factory pattern")
    parser.add_argument("--aggregate", help="Aggregate name")
    parser.add_argument("--output", choices=["json", "code"], default="code")

    args = parser.parse_args()
    result = generate_factory_system()

    if args.output == "json":
        metadata = {k: v for k, v in result.items() if k != "code"}
        print(json.dumps(metadata, indent=2))
    else:
        print(result["code"])


if __name__ == "__main__":
    main()
