#!/usr/bin/env python3
"""Saga Generator - Distributed Transaction Orchestration

Generates:
- Saga orchestrator (coordinates steps)
- Compensating transactions (rollback)
- Saga steps (each step of transaction)
- Step history (track progress)
"""

import sys
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.base_script import setup_logging, timed_run, check_budget

__version__ = "0.7.0"
logger = setup_logging(__name__)


class SagaGenerator:
    """Generates saga pattern for distributed transactions."""

    def __init__(self, framework: str):
        self.framework = framework.lower()

    def generate(self) -> Dict[str, str]:
        files = {}
        files['sagas/saga.py'] = self._saga()
        files['sagas/saga_step.py'] = self._saga_step()
        files['sagas/compensating_transaction.py'] = self._compensating()
        files['sagas/saga_history.py'] = self._saga_history()
        files['sagas/README.md'] = self._readme()
        return files

    def _saga(self) -> str:
        return '''"""Saga Orchestrator - Coordinates Distributed Transactions"""

from typing import List, Dict, Any
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SagaStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    COMPENSATING = "compensating"
    FAILED = "failed"


class Saga:
    """Orchestrates distributed transaction across multiple services"""

    def __init__(self, saga_id: str, saga_name: str):
        self.saga_id = saga_id
        self.saga_name = saga_name
        self.status = SagaStatus.PENDING
        self.steps: List['SagaStep'] = []
        self.completed_steps: List[str] = []
        self.compensations: Dict[str, Any] = {}

    def add_step(self, step: 'SagaStep'):
        """Add step to saga"""
        self.steps.append(step)
        logger.info(f"Added step {step.step_name} to saga {self.saga_id}")

    def execute(self) -> bool:
        """Execute saga (all steps)"""
        logger.info(f"Executing saga {self.saga_id}: {self.saga_name}")
        self.status = SagaStatus.IN_PROGRESS

        for step in self.steps:
            try:
                logger.info(f"Executing step: {step.step_name}")
                result = step.execute()

                if not result:
                    logger.error(f"Step {step.step_name} failed")
                    self.compensate()
                    self.status = SagaStatus.FAILED
                    return False

                self.completed_steps.append(step.step_name)
                self.compensations[step.step_name] = step

            except Exception as e:
                logger.error(f"Step {step.step_name} threw exception: {e}")
                self.compensate()
                self.status = SagaStatus.FAILED
                return False

        self.status = SagaStatus.COMPLETED
        logger.info(f"Saga {self.saga_id} completed successfully")
        return True

    def compensate(self):
        """Rollback completed steps"""
        logger.warning(f"Compensating saga {self.saga_id}")
        self.status = SagaStatus.COMPENSATING

        # Rollback in reverse order
        for step_name in reversed(self.completed_steps):
            try:
                step = self.compensations[step_name]
                logger.info(f"Compensating step: {step_name}")
                step.compensate()
            except Exception as e:
                logger.error(f"Compensation of {step_name} failed: {e}")

        logger.warning(f"Saga {self.saga_id} compensated")

    def get_status(self) -> Dict[str, Any]:
        """Get saga status"""
        return {
            "saga_id": self.saga_id,
            "saga_name": self.saga_name,
            "status": self.status.value,
            "completed_steps": self.completed_steps,
            "total_steps": len(self.steps),
        }
'''

    def _saga_step(self) -> str:
        return '''"""Saga Step - Individual Step in Transaction"""

from abc import ABC, abstractmethod
from typing import Any
import logging

logger = logging.getLogger(__name__)


class SagaStep(ABC):
    """Single step in saga"""

    def __init__(self, step_name: str):
        self.step_name = step_name

    @abstractmethod
    def execute(self) -> bool:
        """Execute step"""
        pass

    @abstractmethod
    def compensate(self) -> bool:
        """Compensate (rollback) step"""
        pass


class ReserveInventoryStep(SagaStep):
    """Step: Reserve inventory"""

    def __init__(self, inventory_service, items: dict):
        super().__init__("ReserveInventory")
        self.inventory_service = inventory_service
        self.items = items
        self.reservation_id = None

    def execute(self) -> bool:
        """Reserve items"""
        logger.info(f"Reserving inventory: {self.items}")
        try:
            self.reservation_id = self.inventory_service.reserve(self.items)
            return bool(self.reservation_id)
        except Exception as e:
            logger.error(f"Inventory reservation failed: {e}")
            return False

    def compensate(self) -> bool:
        """Release reservation"""
        logger.info(f"Releasing reservation: {self.reservation_id}")
        try:
            self.inventory_service.release(self.reservation_id)
            return True
        except Exception as e:
            logger.error(f"Inventory release failed: {e}")
            return False


class ProcessPaymentStep(SagaStep):
    """Step: Process payment"""

    def __init__(self, payment_service, amount: float, customer_id: str):
        super().__init__("ProcessPayment")
        self.payment_service = payment_service
        self.amount = amount
        self.customer_id = customer_id
        self.transaction_id = None

    def execute(self) -> bool:
        """Charge customer"""
        logger.info(f"Charging customer {self.customer_id}: ${self.amount}")
        try:
            self.transaction_id = self.payment_service.charge(
                self.customer_id,
                self.amount
            )
            return bool(self.transaction_id)
        except Exception as e:
            logger.error(f"Payment failed: {e}")
            return False

    def compensate(self) -> bool:
        """Refund payment"""
        logger.info(f"Refunding transaction: {self.transaction_id}")
        try:
            self.payment_service.refund(self.transaction_id)
            return True
        except Exception as e:
            logger.error(f"Refund failed: {e}")
            return False


class ShipOrderStep(SagaStep):
    """Step: Ship order"""

    def __init__(self, shipping_service, order_id: str, address: str):
        super().__init__("ShipOrder")
        self.shipping_service = shipping_service
        self.order_id = order_id
        self.address = address
        self.shipment_id = None

    def execute(self) -> bool:
        """Create shipment"""
        logger.info(f"Shipping order {self.order_id} to {self.address}")
        try:
            self.shipment_id = self.shipping_service.create_shipment(
                self.order_id,
                self.address
            )
            return bool(self.shipment_id)
        except Exception as e:
            logger.error(f"Shipment creation failed: {e}")
            return False

    def compensate(self) -> bool:
        """Cancel shipment"""
        logger.info(f"Canceling shipment: {self.shipment_id}")
        try:
            self.shipping_service.cancel_shipment(self.shipment_id)
            return True
        except Exception as e:
            logger.error(f"Shipment cancellation failed: {e}")
            return False
'''

    def _compensating(self) -> str:
        return '''"""Compensating Transactions - Rollback Operations"""

from typing import Callable
import logging

logger = logging.getLogger(__name__)


class CompensatingTransaction:
    """Represents rollback for a completed transaction"""

    def __init__(self, original_operation: str, compensation_fn: Callable):
        self.original_operation = original_operation
        self.compensation_fn = compensation_fn

    def compensate(self) -> bool:
        """Execute compensation"""
        logger.info(f"Compensating: {self.original_operation}")
        try:
            self.compensation_fn()
            return True
        except Exception as e:
            logger.error(f"Compensation failed: {e}")
            return False


class CompensationChain:
    """Chain of compensating transactions"""

    def __init__(self):
        self.compensations: list = []

    def add_compensation(self, compensation: CompensatingTransaction):
        """Add compensation (executed in reverse order)"""
        self.compensations.append(compensation)

    def execute_all(self) -> bool:
        """Execute all compensations in reverse order"""
        logger.info(f"Executing {len(self.compensations)} compensations")

        # Reverse order: undo most recent first
        for compensation in reversed(self.compensations):
            if not compensation.compensate():
                return False

        return True

    def clear(self):
        """Clear compensation chain"""
        self.compensations.clear()
'''

    def _saga_history(self) -> str:
        return '''"""Saga History - Track Saga Progress"""

from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class SagaStepRecord:
    """Record of saga step execution"""
    step_name: str
    start_time: datetime
    end_time: datetime = None
    status: str = "in_progress"
    error: str = None


class SagaHistory:
    """Track saga execution progress"""

    def __init__(self, saga_id: str):
        self.saga_id = saga_id
        self.started_at = datetime.now()
        self.ended_at = None
        self.steps: List[SagaStepRecord] = []
        self.status = "in_progress"

    def record_step_start(self, step_name: str):
        """Record step start"""
        record = SagaStepRecord(
            step_name=step_name,
            start_time=datetime.now()
        )
        self.steps.append(record)
        logger.info(f"Recorded step start: {step_name}")

    def record_step_success(self, step_name: str):
        """Record step success"""
        for step in self.steps:
            if step.step_name == step_name:
                step.end_time = datetime.now()
                step.status = "completed"
                logger.info(f"Recorded step success: {step_name}")
                break

    def record_step_failure(self, step_name: str, error: str):
        """Record step failure"""
        for step in self.steps:
            if step.step_name == step_name:
                step.end_time = datetime.now()
                step.status = "failed"
                step.error = error
                logger.error(f"Recorded step failure: {step_name}: {error}")
                break

    def finalize(self, status: str):
        """Finalize saga"""
        self.ended_at = datetime.now()
        self.status = status
        logger.info(f"Saga {self.saga_id} finalized: {status}")

    def get_duration_seconds(self) -> float:
        """Get saga duration"""
        end_time = self.ended_at or datetime.now()
        return (end_time - self.started_at).total_seconds()

    def get_summary(self) -> Dict[str, Any]:
        """Get saga summary"""
        return {
            "saga_id": self.saga_id,
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "duration_seconds": self.get_duration_seconds(),
            "steps": [
                {
                    "name": s.step_name,
                    "status": s.status,
                    "error": s.error,
                }
                for s in self.steps
            ]
        }
'''

    def _readme(self) -> str:
        return '''# Sagas - Distributed Transaction Coordination

## Problem

Transactions across multiple services (inventory, payment, shipping):

```
1. Reserve inventory ✓
2. Process payment ✗ FAILS
3. Ship order ✗ NEVER RUNS

What about the inventory reservation?
```

## Solution: Saga Pattern

Coordinate multiple operations with compensating transactions:

```python
from sagas.saga import Saga
from sagas.saga_step import ReserveInventoryStep, ProcessPaymentStep, ShipOrderStep

saga = Saga("order-123", "CreateOrder")

saga.add_step(ReserveInventoryStep(inventory_service, items))
saga.add_step(ProcessPaymentStep(payment_service, 99.99, "customer-1"))
saga.add_step(ShipOrderStep(shipping_service, "order-123", "123 Main St"))

# Execute all steps, rollback on failure
success = saga.execute()

if not success:
    # Automatically rolls back completed steps
    print(saga.get_status())
```

## Saga Flow

```
EXECUTE:
1. Reserve inventory → SUCCESS
2. Process payment → SUCCESS
3. Ship order → FAILS

COMPENSATE (reverse order):
3. Cancel shipment (never ran)
2. Refund payment → SUCCESS
1. Release inventory → SUCCESS

Result: Distributed consistency
```

## Two Approaches

### Orchestration (Recommended)

Saga coordinator directs each step:

```python
saga = OrderSaga()
saga.add_step(ReserveInventory())
saga.add_step(ProcessPayment())
saga.add_step(ShipOrder())
saga.execute()  # Coordinator owns flow
```

**Pros**: Clear flow, easy to understand
**Cons**: Coordinator becomes single point of failure

### Choreography

Services listen for events and respond:

```
1. OrderService: Create Order → publishes OrderCreatedEvent
2. InventoryService: Listens → Reserves inventory
3. PaymentService: Listens → Processes payment
4. ShippingService: Listens → Ships order
```

**Pros**: Decoupled, scalable
**Cons**: Complex flow, hard to debug

## Key Benefits

- **Consistency**: Maintains consistency across services
- **Rollback**: Automatic compensation on failure
- **Visibility**: Track exactly which steps succeeded
- **Resilience**: Handles service failures gracefully

## Example: Order Processing

```python
saga = Saga("order-456", "ProcessOrder")

# Step 1: Reserve inventory
saga.add_step(ReserveInventoryStep(
    inventory_service,
    items={"product-1": 2, "product-2": 1}
))

# Step 2: Process payment
saga.add_step(ProcessPaymentStep(
    payment_service,
    amount=199.99,
    customer_id="customer-5"
))

# Step 3: Ship order
saga.add_step(ShipOrderStep(
    shipping_service,
    order_id="order-456",
    address="456 Oak Ave, Springfield, IL 62701"
))

# Execute (with automatic rollback on failure)
if saga.execute():
    print("Order processed successfully")
else:
    print("Order processing failed, rolled back")
```
'''


def main():
    with timed_run("saga_generator") as timer:
        logger.debug("Testing Saga generation")
        gen = SagaGenerator("python")
        files = gen.generate()
        logger.debug(f"Generated {len(files)} Saga files")
        for filepath in files:
            print(f"  ✓ {filepath}")
        check_budget("saga_generator", timer.elapsed_ms, logger)


if __name__ == '__main__':
    main()
