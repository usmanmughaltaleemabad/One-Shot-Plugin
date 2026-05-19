#!/usr/bin/env python3
"""
Phase 4 Saga Compensation Strategy

Advanced patterns for saga compensating transactions.

Sagas are long-running transactions across multiple aggregates.
When a step fails, undo previous steps (compensations).

Compensation challenges:
1. Partial undo: step 1 succeeded, step 2 failed, can we undo step 1?
2. Idempotency: compensation ran twice (crash), safe?
3. Compensation failure: undo failed. Now what?
4. Reconciliation: what if we can't undo (order shipped)?

Strategies:
1. Pessimistic: lock resources upfront
2. Optimistic: assume success, compensate on failure
3. Semantic undo: reverse operation (refund, not delete)
4. Reconciliation: detect drift and fix
5. Manual intervention: escalate to human for unrecoverable cases

Usage:
    python phase4_saga_compensation_strategy.py --strategy semantic-undo

Input: Compensation strategy
Output: Implementation with patterns and examples
"""

import argparse
import json
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime


def generate_compensation_strategies() -> str:
    """Generate compensation strategy implementations."""

    strategies = '''
class CompensationStrategy:
    """Base class for compensation strategies"""

    def compensate(self, step: Dict, context: Dict) -> bool:
        """
        Execute compensation for failed step.

        Args:
            step: Step information (name, aggregate_id, etc.)
            context: Saga context (data, state)

        Returns:
            True if compensation succeeded
        """
        raise NotImplementedError()

    def is_compensable(self, step: Dict) -> bool:
        """Check if step can be compensated"""
        raise NotImplementedError()


class SemanticUndoStrategy(CompensationStrategy):
    """
    Semantic undo: reverse operation instead of delete.

    Example: Payment processed → compensation is Refund, not Delete

    Why?
    - Audit trail: shows refund happened
    - Idempotent: refunding twice just applies once
    - Recoverable: if refund fails, can retry
    """

    def __init__(self, compensation_handlers: Dict[str, Callable]):
        self.handlers = compensation_handlers

    def compensate(self, step: Dict, context: Dict) -> bool:
        """Execute semantic compensation"""
        step_name = step.get("name")
        compensation_type = step.get("compensation_type")

        handler = self.handlers.get(compensation_type)
        if not handler:
            return False

        try:
            # Execute semantic undo
            handler(step, context)
            return True
        except Exception as e:
            print(f"Compensation failed: {e}")
            return False

    def is_compensable(self, step: Dict) -> bool:
        """All steps with handlers are compensable"""
        compensation_type = step.get("compensation_type")
        return compensation_type in self.handlers

    @staticmethod
    def build_order_compensation_handlers() -> Dict[str, Callable]:
        """Example: order compensation handlers"""
        return {
            "refund_payment": lambda step, ctx: refund_payment(
                ctx["payment_id"],
                ctx["amount"]
            ),
            "deallocate_inventory": lambda step, ctx: deallocate_inventory(
                ctx["inventory_allocation_id"]
            ),
            "cancel_shipment": lambda step, ctx: cancel_shipment(
                ctx["shipment_id"]
            ),
            "notify_customer": lambda step, ctx: notify_customer(
                ctx["customer_id"],
                "Order cancelled"
            )
        }


class IdempotentCompensationStrategy(CompensationStrategy):
    """
    Idempotent compensation: safe to run multiple times.

    Problem: compensation fails mid-execution, saga retries.
    If compensation isn't idempotent, bad state.

    Solution: ensure compensation is idempotent.
    - Check if already compensated
    - Only execute if needed
    - Mark as compensated

    Example:
    Compensation: Refund payment
    - Check: already refunded?
    - If yes: skip (idempotent)
    - If no: execute refund, mark as refunded
    """

    def __init__(self, idempotency_store):
        self.idempotency_store = idempotency_store

    def compensate(self, step: Dict, context: Dict) -> bool:
        """Execute idempotent compensation"""
        step_id = step.get("step_id")
        compensation_id = f"comp-{step_id}"

        # Check: already compensated?
        if self.idempotency_store.is_compensated(compensation_id):
            return True  # Already done, idempotent skip

        try:
            # Execute compensation
            result = self._do_compensate(step, context)

            # Mark as compensated
            self.idempotency_store.mark_compensated(compensation_id)

            return result
        except Exception as e:
            return False

    def _do_compensate(self, step: Dict, context: Dict) -> bool:
        """Override: actual compensation logic"""
        raise NotImplementedError()

    def is_compensable(self, step: Dict) -> bool:
        """All steps are compensable with idempotency"""
        return True


class ReconciliationStrategy(CompensationStrategy):
    """
    Reconciliation: detect drift and fix manually.

    Problem: some operations can't be undone (order shipped).

    Solution: detect drift, escalate to human.
    - Compensation can't undo the action
    - Record in reconciliation log
    - Human reviews and resolves
    - Manual compensation in system
    """

    def __init__(self, reconciliation_queue):
        self.reconciliation_queue = reconciliation_queue
        self.uncompensable_steps = []

    def compensate(self, step: Dict, context: Dict) -> bool:
        """Escalate uncompensable steps"""
        if not self.is_compensable(step):
            # Queue for manual reconciliation
            self.reconciliation_queue.add({
                "step": step,
                "context": context,
                "reason": "Cannot automatically compensate",
                "timestamp": datetime.utcnow().isoformat(),
                "status": "pending"
            })

            self.uncompensable_steps.append(step)
            return False  # Compensation failed (needs manual intervention)

        return True  # Compensation possible

    def is_compensable(self, step: Dict) -> bool:
        """Check if step can be compensated"""
        compensable_types = ["payment", "inventory", "notification"]
        step_type = step.get("type")
        return step_type in compensable_types

    def get_pending_reconciliations(self) -> List[Dict]:
        """Get all pending reconciliations awaiting human action"""
        return self.reconciliation_queue.get_pending()

    def resolve_reconciliation(
        self,
        reconciliation_id: str,
        resolution: str
    ) -> bool:
        """Human resolves reconciliation"""
        return self.reconciliation_queue.mark_resolved(
            reconciliation_id,
            resolution
        )
'''

    return strategies


def generate_compensation_handler() -> str:
    """Generate compensation handler."""

    handler = '''
class CompensationHandler:
    """
    Manages compensation execution.

    Responsibilities:
    1. Execute compensations in reverse order
    2. Track compensation status
    3. Retry on failure
    4. Escalate if unrecoverable
    """

    def __init__(self, strategy: CompensationStrategy):
        self.strategy = strategy
        self.compensation_log = []
        self.max_retries = 3

    def compensate_saga(
        self,
        saga_steps: List[Dict],
        saga_context: Dict
    ) -> Dict:
        """
        Execute all compensations.

        Runs in reverse order (undo step N, then N-1, etc).

        Returns:
            {
                "success": bool,
                "compensated": [step names that were undone],
                "failed": [step names that failed to undo],
                "uncompensable": [steps that can't be undone]
            }
        """
        compensated = []
        failed = []
        uncompensable = []

        # Compensate in reverse order
        for step in reversed(saga_steps):
            if not self.strategy.is_compensable(step):
                uncompensable.append(step.get("name"))
                continue

            # Try compensation
            success = self._compensate_with_retry(step, saga_context)

            if success:
                compensated.append(step.get("name"))
                self.compensation_log.append({
                    "step": step.get("name"),
                    "status": "compensated",
                    "timestamp": datetime.utcnow().isoformat()
                })
            else:
                failed.append(step.get("name"))
                self.compensation_log.append({
                    "step": step.get("name"),
                    "status": "failed",
                    "timestamp": datetime.utcnow().isoformat()
                })

        return {
            "success": len(failed) == 0 and len(uncompensable) == 0,
            "compensated": compensated,
            "failed": failed,
            "uncompensable": uncompensable
        }

    def _compensate_with_retry(
        self,
        step: Dict,
        saga_context: Dict
    ) -> bool:
        """Execute compensation with retries"""
        for attempt in range(self.max_retries):
            try:
                success = self.strategy.compensate(step, saga_context)
                if success:
                    return True
            except Exception as e:
                if attempt < self.max_retries - 1:
                    # Retry
                    continue
                else:
                    # Last attempt failed
                    return False

        return False

    def get_compensation_log(self) -> List[Dict]:
        """Get history of compensations"""
        return self.compensation_log
'''

    return handler


def generate_compensation_patterns() -> str:
    """Generate common compensation patterns."""

    patterns = '''
class CompensationPatterns:
    """Common compensation patterns"""

    @staticmethod
    def refund_payment(payment_id: str, amount: float) -> None:
        """Pattern: Refund (payment compensation)"""
        # Semantic undo: create refund transaction
        refund = {
            "type": "Refund",
            "original_payment_id": payment_id,
            "amount": amount,
            "timestamp": datetime.utcnow().isoformat()
        }
        # Store refund (idempotent: same refund_id = skip)
        # Update payment status: refunded

    @staticmethod
    def deallocate_inventory(allocation_id: str) -> None:
        """Pattern: Deallocate (inventory compensation)"""
        # Semantic undo: release reserved inventory
        # Check: still reserved?
        # If yes: release
        # Update status: released

    @staticmethod
    def cancel_order(order_id: str) -> None:
        """Pattern: Cancel (order compensation)"""
        # Semantic undo: change status to cancelled
        # Send notification to customer
        # Release any locks

    @staticmethod
    def notify_customer_compensation(
        customer_id: str,
        message: str
    ) -> None:
        """Pattern: Notification (always compensable)"""
        # Send notification
        # Log event
        # Track status: sent

    @staticmethod
    def mark_manual_review(
        saga_id: str,
        reason: str
    ) -> None:
        """Pattern: Manual intervention needed"""
        # Create support ticket
        # Alert operations team
        # Set status: awaiting_manual_resolution
'''

    return patterns


def generate_compensation_system() -> dict:
    """Generate complete compensation system."""

    imports = '''from typing import Any, Callable, Dict, List, Optional
from datetime import datetime


'''

    module_doc = '''"""
Saga Compensation Strategy

Advanced patterns for saga compensating transactions.

Saga = distributed transaction across multiple aggregates.
Example: Order → Payment → Inventory → Shipping

Step 1: CreateOrder ✓
Step 2: ProcessPayment ✓
Step 3: AllocateInventory ✗ FAILS

Now what? Undo steps 1 and 2.

Compensation challenges:
1. Partial undo: can we undo step 1?
2. Idempotency: if compensation crashes, can we retry safely?
3. Failures: what if undo also fails?
4. Unrecoverable: some operations can't be undone

Strategies:

1. SEMANTIC UNDO
   - Refund instead of delete payment
   - Deallocate instead of delete inventory
   - Why: audit trail, idempotent, reversible

2. IDEMPOTENT COMPENSATION
   - Check if already compensated
   - Skip if done (safe to retry)
   - Example: refund payment twice → safe (idempotent)

3. RECONCILIATION
   - Some steps can't be undone (shipped order)
   - Escalate to human
   - Manual compensation in system
   - Example: Order shipped → customer support resolves

Example: Order Saga Compensation

Step 1: ReservePayment
  Compensation: RefundPayment (semantic undo, idempotent)

Step 2: AllocateInventory
  Compensation: DeallocateInventory (semantic undo, idempotent)

Step 3: CreateShipment
  Compensation: None (can't undo shipped order)
  → Escalate to reconciliation queue

Result:
- Payment refunded
- Inventory deallocated
- Shipment marked for manual review
- Customer support contacts customer
"""
'''

    strategies = generate_compensation_strategies()
    handler = generate_compensation_handler()
    patterns = generate_compensation_patterns()

    complete_code = imports + module_doc + "\n" + strategies + "\n" + handler + "\n" + patterns

    return {
        "code": complete_code,
        "pattern": "Saga Compensation Strategy",
        "module": "saga_compensation_strategy.py",
    }


def main():
    parser = argparse.ArgumentParser(description="Generate saga compensation strategy")
    parser.add_argument("--strategy", help="Compensation strategy")
    parser.add_argument("--output", choices=["json", "code"], default="code")

    args = parser.parse_args()
    result = generate_compensation_system()

    if args.output == "json":
        metadata = {k: v for k, v in result.items() if k != "code"}
        print(json.dumps(metadata, indent=2))
    else:
        print(result["code"])


if __name__ == "__main__":
    main()
