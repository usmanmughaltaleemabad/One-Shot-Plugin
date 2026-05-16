#!/usr/bin/env python3
"""
Phase 4 CQRS: Testing Helpers

Testing utilities for CQRS systems.

Challenges:
- Eventual consistency: read models lag behind writes
- Event sourcing: must verify full event log, not just final state
- Sagas: complex multi-step workflows with compensations
- Commands: typed routing, multiple handlers
- Correlation: track command → events

Helpers:
- Given-When-Then style test builders
- Event assertion utilities
- Eventual consistency waits
- Saga workflow testing
- Projection update verification

Usage:
    python phase4_cqrs_testing_helpers.py --test-type command

Input: Test scenario type
Output: Testing helper utilities and examples
"""

import argparse
import json
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime
import time


def generate_given_when_then_builder() -> str:
    """Generate GWT test builder."""

    gwt = '''
class GivenWhenThenBuilder:
    """
    Given-When-Then test builder for CQRS.

    Pattern:
    Given(aggregate_state) → When(command) → Then(events|side_effects)

    Example:
    (Given()
        .with_event(OrderCreated(...))
        .with_event(OrderConfirmed(...))
    .when_command(AddItem(...))
    .then_event_emitted(ItemAdded)
    .then_event_not_emitted(OrderCancelled)
    .verify())
    """

    def __init__(self, aggregate_class):
        self.aggregate_class = aggregate_class
        self.initial_events = []
        self.command = None
        self.aggregate = None
        self.emitted_events = []
        self.expected_events = []
        self.unexpected_events = []

    def given_event(self, event: Dict) -> "GivenWhenThenBuilder":
        """Given: aggregate has this event in history"""
        self.initial_events.append(event)
        return self

    def given_events(self, events: List[Dict]) -> "GivenWhenThenBuilder":
        """Given: aggregate has these events"""
        self.initial_events.extend(events)
        return self

    def when_command(self, command: Dict) -> "GivenWhenThenBuilder":
        """When: execute this command"""
        # Reconstruct aggregate from initial events
        self.aggregate = self.aggregate_class(command["aggregate_id"])
        for event in self.initial_events:
            self.aggregate.apply_event(event)

        # Execute command
        self.emitted_events = self.aggregate.execute_command(command)
        return self

    def then_event_emitted(self, event_type: str) -> "GivenWhenThenBuilder":
        """Then: verify event type was emitted"""
        self.expected_events.append(event_type)
        return self

    def then_events_emitted(self, event_types: List[str]) -> "GivenWhenThenBuilder":
        """Then: verify multiple event types"""
        self.expected_events.extend(event_types)
        return self

    def then_event_not_emitted(self, event_type: str) -> "GivenWhenThenBuilder":
        """Then: verify event type was NOT emitted"""
        self.unexpected_events.append(event_type)
        return self

    def then_event_count(self, count: int) -> "GivenWhenThenBuilder":
        """Then: verify exact number of events emitted"""
        assert len(self.emitted_events) == count, \
            f"Expected {count} events, got {len(self.emitted_events)}"
        return self

    def then_aggregate_state(self, assertion: Callable) -> "GivenWhenThenBuilder":
        """Then: verify aggregate state with custom assertion"""
        assertion(self.aggregate)
        return self

    def verify(self) -> bool:
        """Execute all assertions"""
        # Check expected events
        emitted_types = [e.get("event_type") for e in self.emitted_events]

        for expected in self.expected_events:
            assert expected in emitted_types, \
                f"Expected event {expected} not emitted. Got: {emitted_types}"

        # Check unexpected events
        for unexpected in self.unexpected_events:
            assert unexpected not in emitted_types, \
                f"Unexpected event {unexpected} was emitted"

        return True

    def build_test_report(self) -> Dict:
        """Generate test report"""
        return {
            "initial_events": len(self.initial_events),
            "command": self.command,
            "emitted_events": self.emitted_events,
            "expected": self.expected_events,
            "unexpected": self.unexpected_events,
            "passed": self.verify()
        }
'''

    return gwt


def generate_event_assertion_helpers() -> str:
    """Generate event assertion utilities."""

    helpers = '''
class EventAssertions:
    """Assertions for event-based testing"""

    @staticmethod
    def assert_event_emitted(events: List[Dict], event_type: str) -> None:
        """Assert event type was emitted"""
        types = [e.get("event_type") for e in events]
        assert event_type in types, \
            f"Event {event_type} not found. Emitted: {types}"

    @staticmethod
    def assert_event_not_emitted(events: List[Dict], event_type: str) -> None:
        """Assert event type was NOT emitted"""
        types = [e.get("event_type") for e in events]
        assert event_type not in types, \
            f"Event {event_type} should not be emitted. Found in: {types}"

    @staticmethod
    def assert_event_count(events: List[Dict], count: int) -> None:
        """Assert exact number of events"""
        assert len(events) == count, \
            f"Expected {count} events, got {len(events)}"

    @staticmethod
    def assert_event_sequence(events: List[Dict], sequence: List[str]) -> None:
        """Assert events in specific order"""
        types = [e.get("event_type") for e in events]
        assert types == sequence, \
            f"Event sequence mismatch. Expected {sequence}, got {types}"

    @staticmethod
    def assert_event_data(event: Dict, key: str, expected_value: Any) -> None:
        """Assert event contains expected data"""
        actual = event.get("data", {}).get(key)
        assert actual == expected_value, \
            f"Event data mismatch. Expected {key}={expected_value}, got {actual}"

    @staticmethod
    def get_event_by_type(events: List[Dict], event_type: str) -> Optional[Dict]:
        """Get first event of type"""
        for event in events:
            if event.get("event_type") == event_type:
                return event
        return None

    @staticmethod
    def get_events_by_type(events: List[Dict], event_type: str) -> List[Dict]:
        """Get all events of type"""
        return [e for e in events if e.get("event_type") == event_type]
'''

    return helpers


def generate_eventual_consistency_waiter() -> str:
    """Generate eventual consistency waiter."""

    waiter = '''
class EventualConsistencyWaiter:
    """
    Wait for eventual consistency in CQRS systems.

    Read models lag behind write model.
    Use this to wait for projections to catch up.

    Example:
    (EventualConsistencyWaiter(read_model_store)
        .wait_until_event_projected(event_id, projection_name)
        .verify_projection_state(projection_name, assertion))
    """

    def __init__(self, read_model_store, timeout_seconds=5):
        self.read_model_store = read_model_store
        self.timeout = timeout_seconds
        self.start_time = None

    def wait_until_event_projected(
        self,
        event_id: str,
        projection_name: str
    ) -> "EventualConsistencyWaiter":
        """
        Wait until event appears in projection.

        Polls projection until event found or timeout.
        """
        self.start_time = time.time()

        while time.time() - self.start_time < self.timeout:
            projection = self.read_model_store.get_projection(projection_name)
            if self._event_in_projection(projection, event_id):
                return self

            time.sleep(0.1)  # Poll every 100ms

        raise TimeoutError(
            f"Event {event_id} not projected to {projection_name} "
            f"within {self.timeout} seconds"
        )

    def _event_in_projection(self, projection: Dict, event_id: str) -> bool:
        """Check if event is in projection"""
        # Depends on projection structure
        # Override for specific projections
        if isinstance(projection, list):
            return any(e.get("event_id") == event_id for e in projection)
        elif isinstance(projection, dict):
            return event_id in str(projection)
        return False

    def wait_until_count(
        self,
        projection_name: str,
        expected_count: int
    ) -> "EventualConsistencyWaiter":
        """Wait until projection has N items"""
        self.start_time = time.time()

        while time.time() - self.start_time < self.timeout:
            projection = self.read_model_store.get_projection(projection_name)
            if len(projection) == expected_count:
                return self

            time.sleep(0.1)

        projection = self.read_model_store.get_projection(projection_name)
        raise TimeoutError(
            f"Projection {projection_name} count is {len(projection)}, "
            f"expected {expected_count} within {self.timeout} seconds"
        )

    def verify_projection_state(
        self,
        projection_name: str,
        assertion: Callable
    ) -> bool:
        """Verify projection with custom assertion"""
        projection = self.read_model_store.get_projection(projection_name)
        assertion(projection)
        return True
'''

    return waiter


def generate_saga_test_builder() -> str:
    """Generate saga test builder."""

    saga_test = '''
class SagaTestBuilder:
    """Test builder for sagas"""

    def __init__(self, saga_class):
        self.saga_class = saga_class
        self.saga = None
        self.steps = []
        self.compensations_executed = []

    def with_step(
        self,
        step_name: str,
        aggregate_id: str,
        handler: Callable,
        compensation: Callable,
        args: Dict
    ) -> "SagaTestBuilder":
        """Add step to saga"""
        self.steps.append({
            "name": step_name,
            "aggregate_id": aggregate_id,
            "handler": handler,
            "compensation": compensation,
            "args": args
        })
        return self

    def execute_saga(self) -> "SagaTestBuilder":
        """Execute saga"""
        self.saga = self.saga_class("test-saga")
        self.saga.start({})

        for step in self.steps:
            success = self.saga.execute_step(
                step_name=step["name"],
                aggregate_id=step["aggregate_id"],
                handler=step["handler"],
                compensation=step["compensation"],
                handler_args=step["args"]
            )

            if not success:
                self.saga.compensate()
                break

        return self

    def then_saga_completed(self) -> bool:
        """Assert saga completed"""
        assert self.saga.status == "completed", \
            f"Saga status is {self.saga.status}, expected completed"
        return True

    def then_saga_failed(self) -> bool:
        """Assert saga failed"""
        assert self.saga.status == "failed", \
            f"Saga status is {self.saga.status}, expected failed"
        return True

    def then_step_executed(self, step_name: str) -> bool:
        """Assert step was executed"""
        assert step_name in self.saga.executed_steps, \
            f"Step {step_name} not executed. Executed: {self.saga.executed_steps}"
        return True

    def then_all_compensations_executed(self) -> bool:
        """Assert all compensations ran"""
        assert len(self.saga.compensations) > 0, \
            "No compensations executed"
        return True
'''

    return saga_test


def generate_test_examples() -> str:
    """Generate test examples."""

    examples = '''
# Example Tests

def test_order_creation():
    """Test: Create order"""
    (GivenWhenThenBuilder(OrderAggregate)
        .when_command({
            "command_type": "Create",
            "aggregate_id": "order-123",
            "customer_id": "cust-456",
            "items": [{"sku": "item-1", "qty": 2}],
            "total": 100
        })
        .then_event_emitted("OrderCreated")
        .then_event_count(1)
        .verify())


def test_order_cancellation():
    """Test: Cancel order with status invariant"""
    (GivenWhenThenBuilder(OrderAggregate)
        .given_event({
            "event_type": "OrderCreated",
            "data": {"customer_id": "cust-456", "total": 100}
        })
        .when_command({
            "command_type": "Delete",
            "aggregate_id": "order-123"
        })
        .then_event_emitted("Deleted")
        .verify())


def test_projection_eventual_consistency():
    """Test: Projection updates eventually"""
    waiter = EventualConsistencyWaiter(read_model_store, timeout_seconds=5)

    # Create order (write model)
    event_id = create_order()

    # Wait for read model
    waiter.wait_until_event_projected(event_id, "OrderListProjection")

    # Verify projection
    waiter.verify_projection_state(
        "OrderListProjection",
        lambda proj: assert_order_in_list(proj, event_id)
    )


def test_saga_success_path():
    """Test: Saga completes all steps"""
    saga_test = (SagaTestBuilder(PaymentSaga)
        .with_step(
            "ReservePayment",
            "payment-123",
            lambda: reserve_payment(),
            lambda: release_payment(),
            {}
        )
        .with_step(
            "AllocateInventory",
            "inventory-123",
            lambda: allocate_inventory(),
            lambda: deallocate_inventory(),
            {}
        )
        .execute_saga()
        .then_saga_completed()
        .then_step_executed("ReservePayment")
        .then_step_executed("AllocateInventory"))


def test_saga_compensation():
    """Test: Saga compensates on failure"""
    saga_test = (SagaTestBuilder(PaymentSaga)
        .with_step(
            "Step1",
            "agg-1",
            lambda: succeed(),
            lambda: undo_step1(),
            {}
        )
        .with_step(
            "Step2",
            "agg-2",
            lambda: fail_with_error(),  # This fails
            lambda: undo_step2(),
            {}
        )
        .execute_saga()
        .then_saga_failed()
        .then_all_compensations_executed())
'''

    return examples


def generate_testing_helpers_system() -> dict:
    """Generate complete testing helpers system."""

    imports = '''import time
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime


'''

    module_doc = '''"""
CQRS Testing Helpers

Utilities for testing CQRS systems.

Challenges in testing CQRS:
1. Eventually consistent: read models lag
2. Event-based: verify event log, not just state
3. Complex workflows: sagas with compensation
4. Typed commands: multiple command types
5. Correlation: track causality

Solutions:
1. GivenWhenThenBuilder: fluent DSL for command tests
2. EventAssertions: verify events
3. EventualConsistencyWaiter: wait for projections
4. SagaTestBuilder: test workflows
5. Event verification: count, sequence, data

Example:
(GivenWhenThenBuilder(OrderAggregate)
    .given_event(OrderCreated(...))
    .when_command(AddItem(...))
    .then_event_emitted(ItemAdded)
    .verify())
"""
'''

    gwt = generate_given_when_then_builder()
    assertions = generate_event_assertion_helpers()
    waiter = generate_eventual_consistency_waiter()
    saga = generate_saga_test_builder()
    examples = generate_test_examples()

    complete_code = imports + module_doc + "\n" + gwt + "\n" + assertions + "\n" + waiter + "\n" + saga + "\n" + examples

    return {
        "code": complete_code,
        "pattern": "CQRS Testing Helpers",
        "module": "cqrs_testing_helpers.py",
    }


def main():
    parser = argparse.ArgumentParser(description="Generate CQRS testing helpers")
    parser.add_argument("--test-type", help="Test scenario type")
    parser.add_argument("--output", choices=["json", "code"], default="code")

    args = parser.parse_args()
    result = generate_testing_helpers_system()

    if args.output == "json":
        metadata = {k: v for k, v in result.items() if k != "code"}
        print(json.dumps(metadata, indent=2))
    else:
        print(result["code"])


if __name__ == "__main__":
    main()
