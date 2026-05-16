#!/usr/bin/env python3
"""
Phase 4 Saga Pattern + Event Sourcing

Combines two patterns:
- Saga: Distributed transaction spanning multiple aggregates
- Event Sourcing: Immutable event log with replay capability

Why combine?
- Sagas need compensating transactions (undo)
- Event sourcing provides full history
- Together: complete auditability + reliability

Pattern:
1. Saga step 1: aggregate changes, events generated
2. Saga step 2: different aggregate, more events
3. If step 3 fails: replay saga history, apply compensations
4. Full event log: recover saga state at any point

Usage:
    python phase4_saga_event_sourcing.py --saga PaymentSaga --steps 3

Input: Saga name and number of steps
Output: Saga with event sourcing support
"""

import argparse
import json
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime


def generate_saga_event_schema() -> str:
    """Generate schema for saga events."""

    schema = '''
class SagaEventSchema:
    """
    Saga execution events stored in event store.

    Fields:
    - saga_id: Unique saga execution ID
    - saga_type: e.g., PaymentSaga, OrderFulfillmentSaga
    - event_type: SagaStarted, StepExecuted, CompensationStarted, SagaCompleted
    - aggregate_id: Which aggregate involved
    - step_name: Which step in saga
    - step_result: Success/failure/compensating
    - event_data: Full context
    - timestamp: When step occurred
    """

    SQL = """
    CREATE TABLE IF NOT EXISTS saga_events (
        event_id VARCHAR(255) PRIMARY KEY,
        saga_id VARCHAR(255) NOT NULL,
        saga_type VARCHAR(255) NOT NULL,
        aggregate_id VARCHAR(255) NOT NULL,
        event_type VARCHAR(50) NOT NULL,  -- SagaStarted, StepExecuted, etc.
        step_name VARCHAR(255),
        step_result VARCHAR(50),  -- success, failure, compensating
        event_data JSON NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        INDEX idx_saga (saga_id),
        INDEX idx_aggregate (aggregate_id),
        INDEX idx_type (saga_type)
    );

    CREATE TABLE IF NOT EXISTS saga_state (
        saga_id VARCHAR(255) PRIMARY KEY,
        saga_type VARCHAR(255) NOT NULL,
        status VARCHAR(50) NOT NULL,  -- running, completed, compensating, failed
        current_step INT,
        completed_steps INT DEFAULT 0,
        failed_step VARCHAR(255),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    );
    """
'''

    return schema


def generate_saga_base_class() -> str:
    """Generate base saga class with event sourcing."""

    saga = '''
class EventSourcingSaga:
    """
    Base saga class with event sourcing.

    Sagas are long-running transactions across multiple aggregates.
    Events are immutable log of saga progress.
    On failure, replay events to understand what happened.

    Lifecycle:
    1. SagaStarted event
    2. StepExecuted events (one per successful step)
    3. On failure: CompensationStarted events (undo steps in reverse)
    4. SagaCompleted or SagaFailed event
    """

    def __init__(self, saga_id: str, saga_type: str, event_store, correlation_tracker):
        self.saga_id = saga_id
        self.saga_type = saga_type
        self.event_store = event_store
        self.correlation_tracker = correlation_tracker
        self.executed_steps = []
        self.compensations = []
        self.status = "running"

    def start(self, initial_data: dict) -> None:
        """Record saga start"""
        event = {
            "event_id": f"saga-start-{self.saga_id}",
            "saga_id": self.saga_id,
            "saga_type": self.saga_type,
            "event_type": "SagaStarted",
            "event_data": initial_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.event_store.append(event)

    def execute_step(
        self,
        step_name: str,
        aggregate_id: str,
        handler: Callable,
        compensation: Callable,
        handler_args: dict
    ) -> bool:
        """
        Execute saga step.

        Args:
            step_name: Name of step
            aggregate_id: Affected aggregate
            handler: Function to execute
            compensation: Function to undo step
            handler_args: Arguments to pass to handler

        Returns:
            True if step succeeded
        """
        try:
            # Execute step
            result = handler(**handler_args)

            # Record success
            event = {
                "event_id": f"saga-step-{self.saga_id}-{step_name}",
                "saga_id": self.saga_id,
                "aggregate_id": aggregate_id,
                "event_type": "StepExecuted",
                "step_name": step_name,
                "step_result": "success",
                "event_data": {
                    "step": step_name,
                    "result": result
                },
                "timestamp": datetime.utcnow().isoformat()
            }

            self.event_store.append(event)
            self.executed_steps.append(step_name)
            self.compensations.append((step_name, compensation, handler_args))

            return True

        except Exception as e:
            # Record failure
            event = {
                "event_id": f"saga-step-{self.saga_id}-{step_name}-failed",
                "saga_id": self.saga_id,
                "aggregate_id": aggregate_id,
                "event_type": "StepFailed",
                "step_name": step_name,
                "step_result": "failure",
                "event_data": {
                    "step": step_name,
                    "error": str(e)
                },
                "timestamp": datetime.utcnow().isoformat()
            }

            self.event_store.append(event)
            self.status = "failed"
            return False

    def compensate(self) -> None:
        """
        Undo all executed steps (reverse order).

        When saga fails, compensations undo the work.
        """
        self.status = "compensating"

        # Undo in reverse order
        for step_name, compensation_fn, args in reversed(self.compensations):
            try:
                compensation_fn(**args)

                event = {
                    "event_id": f"saga-compensation-{self.saga_id}-{step_name}",
                    "saga_id": self.saga_id,
                    "event_type": "CompensationExecuted",
                    "step_name": step_name,
                    "step_result": "compensating",
                    "event_data": {
                        "step": step_name,
                        "compensation": "success"
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }

                self.event_store.append(event)

            except Exception as e:
                # Compensation failed — serious issue
                event = {
                    "event_id": f"saga-compensation-{self.saga_id}-{step_name}-failed",
                    "saga_id": self.saga_id,
                    "event_type": "CompensationFailed",
                    "step_name": step_name,
                    "step_result": "compensation_failed",
                    "event_data": {
                        "step": step_name,
                        "error": str(e)
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }

                self.event_store.append(event)

    def complete(self) -> None:
        """Mark saga as completed"""
        self.status = "completed"

        event = {
            "event_id": f"saga-complete-{self.saga_id}",
            "saga_id": self.saga_id,
            "event_type": "SagaCompleted",
            "event_data": {
                "saga": self.saga_type,
                "steps_executed": len(self.executed_steps)
            },
            "timestamp": datetime.utcnow().isoformat()
        }

        self.event_store.append(event)

    def get_history(self) -> List[dict]:
        """Get full event history of saga"""
        return self.event_store.get_events_by_saga_id(self.saga_id)

    def replay(self) -> None:
        """Replay saga from event log (recovery)"""
        events = self.get_history()

        self.executed_steps = []
        self.compensations = []

        for event in events:
            if event["event_type"] == "StepExecuted":
                self.executed_steps.append(event["step_name"])
            elif event["event_type"] == "SagaCompleted":
                self.status = "completed"
            elif event["event_type"] == "StepFailed":
                self.status = "failed"
'''

    return saga


def generate_saga_orchestrator() -> str:
    """Generate saga orchestrator."""

    orch = '''
class SagaOrchestrator:
    """
    Orchestrates sagas.

    Manages saga lifecycle:
    1. Create saga
    2. Execute steps
    3. Handle failures
    4. Compensate if needed
    5. Complete
    """

    def __init__(self, event_store, saga_state_store):
        self.event_store = event_store
        self.saga_state_store = saga_state_store
        self._sagas = {}

    def create_saga(
        self,
        saga_type: str,
        initial_data: dict
    ) -> EventSourcingSaga:
        """Create new saga instance"""
        saga_id = f"saga-{saga_type}-{datetime.utcnow().timestamp()}"
        saga = EventSourcingSaga(
            saga_id=saga_id,
            saga_type=saga_type,
            event_store=self.event_store,
            correlation_tracker=None
        )
        saga.start(initial_data)
        self._sagas[saga_id] = saga
        self.saga_state_store.create_saga_state(saga_id, saga_type)
        return saga

    def execute_saga(self, saga: EventSourcingSaga, steps: List[dict]) -> bool:
        """
        Execute saga steps.

        Args:
            saga: Saga instance
            steps: [
                {
                    "name": "step1",
                    "aggregate_id": "order-123",
                    "handler": function_to_execute,
                    "compensation": function_to_undo,
                    "args": {}
                },
                ...
            ]

        Returns:
            True if saga completed
        """
        for step in steps:
            success = saga.execute_step(
                step_name=step["name"],
                aggregate_id=step["aggregate_id"],
                handler=step["handler"],
                compensation=step["compensation"],
                handler_args=step["args"]
            )

            if not success:
                # Step failed, compensate
                saga.compensate()
                self.saga_state_store.update_saga_status(
                    saga.saga_id,
                    "failed"
                )
                return False

        saga.complete()
        self.saga_state_store.update_saga_status(saga.saga_id, "completed")
        return True

    def get_saga_history(self, saga_id: str) -> List[dict]:
        """Get full event history of saga"""
        saga = self._sagas.get(saga_id)
        if saga:
            return saga.get_history()
        return []

    def recover_saga(self, saga_id: str) -> Optional[EventSourcingSaga]:
        """
        Recover saga from event store (after crash).

        Reconstruct saga state by replaying events.
        """
        saga_state = self.saga_state_store.get_saga_state(saga_id)
        if not saga_state:
            return None

        saga = EventSourcingSaga(
            saga_id=saga_id,
            saga_type=saga_state["saga_type"],
            event_store=self.event_store,
            correlation_tracker=None
        )

        saga.replay()
        self._sagas[saga_id] = saga
        return saga
'''

    return orch


def generate_saga_system() -> dict:
    """Generate complete saga + event sourcing system."""

    imports = '''import uuid
import json
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional
from abc import ABC, abstractmethod


'''

    module_doc = '''"""
Saga Pattern with Event Sourcing

Combines: Saga (distributed transactions) + Event Sourcing (immutable log)

Saga: Multi-step transaction across multiple aggregates.
Problem: What if step 3 fails? Need to undo steps 1-2 (compensating transactions).

Event Sourcing: Every saga step recorded as immutable event.
Benefit: Full audit trail. Recover saga state at any point.

Together: Sagas with full history + replay capability.

Example: Order → Payment → Inventory → Shipping

Step 1: CreateOrder (aggregate: Order) ✓
Step 2: ProcessPayment (aggregate: Payment) ✓
Step 3: AllocateInventory (aggregate: Inventory) ✗ FAILED

What happened?
- Without sagas: Order created, payment taken, but inventory fails. Now we have inconsistent state.
- With sagas: Undo ProcessPayment (refund), undo CreateOrder (cancel).
- Event log: Full history of what happened.

Recovery:
- Saga crashed mid-step? Replay event log, understand state, resume from step 3.
- Compensation failed? Event log shows it. Investigate.
"""
'''

    schema = generate_saga_event_schema()
    saga_base = generate_saga_base_class()
    orchestrator = generate_saga_orchestrator()

    complete_code = imports + module_doc + "\n" + schema + "\n" + saga_base + "\n" + orchestrator

    return {
        "code": complete_code,
        "pattern": "Saga with Event Sourcing",
        "module": "saga_event_sourcing.py",
    }


def main():
    parser = argparse.ArgumentParser(description="Generate saga with event sourcing")
    parser.add_argument("--saga", help="Saga name")
    parser.add_argument("--steps", type=int, help="Number of steps")
    parser.add_argument("--output", choices=["json", "code"], default="code")

    args = parser.parse_args()
    result = generate_saga_system()

    if args.output == "json":
        metadata = {k: v for k, v in result.items() if k != "code"}
        print(json.dumps(metadata, indent=2))
    else:
        print(result["code"])


if __name__ == "__main__":
    main()
