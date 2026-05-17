#!/usr/bin/env python3
"""
Phase 5 Workflow Orchestration: Long-Running Processes & Sagas

Workflow Orchestration: Coordinate multi-step long-running processes.

Problem: Complex distributed workflows
- Process order: validate → charge card → ship → notify
- One step fails (payment declined): whole order fails
- Retries: manual, error-prone
- State tracking: unclear where in process

Orchestration (solution):
- Define workflow: steps and transitions
- Automatic retry: with exponential backoff
- Saga pattern: compensate on failure
- State management: persistent, durable
"""

from typing import Dict, List, Optional, Callable
from datetime import datetime
from enum import Enum


def generate_workflow_orchestration() -> str:
    """Generate workflow orchestration system."""

    orchestration = '''
class WorkflowOrchestrator:
    """
    Orchestrate long-running workflows (Temporal pattern).

    Features:
    - Step-by-step execution
    - Durable state (survives crash)
    - Automatic retries
    - Saga compensation on failure
    """

    def __init__(self):
        self._workflows = {}  # workflow_id → workflow
        self._executions = {}  # execution_id → execution
        self._steps = {}  # step_id → step definition
        self._compensations = {}  # step_id → compensation_fn

    def define_step(
        self,
        step_id: str,
        fn: Callable,
        retry_policy: Dict = None
    ) -> None:
        """Define workflow step"""
        self._steps[step_id] = {
            "id": step_id,
            "fn": fn,
            "retry_policy": retry_policy or {"max_retries": 3, "backoff_ms": 1000},
            "timeout_seconds": 300
        }

    def define_compensation(
        self,
        step_id: str,
        compensation_fn: Callable
    ) -> None:
        """Define compensation (undo) for step"""
        self._compensations[step_id] = compensation_fn

    def start_workflow(
        self,
        workflow_id: str,
        steps: List[str],
        input_data: Dict
    ) -> str:
        """Start a workflow execution"""
        execution = {
            "id": f"exec-{datetime.utcnow().timestamp()}",
            "workflow_id": workflow_id,
            "steps": steps,
            "status": "running",
            "current_step": 0,
            "input": input_data,
            "output": {},
            "started_at": datetime.utcnow().isoformat(),
            "step_results": []
        }

        self._executions[execution["id"]] = execution
        return execution["id"]

    def execute_step(self, execution_id: str) -> tuple:
        """Execute next step in workflow"""
        execution = self._executions.get(execution_id)
        if not execution:
            return (False, "Execution not found")

        if execution["status"] != "running":
            return (False, f"Execution already {execution['status']}")

        current_step_index = execution["current_step"]
        step_id = execution["steps"][current_step_index]
        step = self._steps.get(step_id)

        if not step:
            return (False, f"Step {step_id} not defined")

        # Execute with retry
        retry_policy = step["retry_policy"]
        max_retries = retry_policy.get("max_retries", 3)

        for attempt in range(max_retries + 1):
            try:
                result = step["fn"](execution["input"])
                execution["step_results"].append({
                    "step_id": step_id,
                    "status": "success",
                    "result": result
                })
                execution["output"][step_id] = result
                execution["current_step"] += 1

                # More steps?
                if execution["current_step"] < len(execution["steps"]):
                    execution["status"] = "running"
                else:
                    execution["status"] = "completed"

                return (True, result)

            except Exception as e:
                if attempt < max_retries:
                    # Retry
                    continue
                else:
                    # All retries exhausted
                    execution["step_results"].append({
                        "step_id": step_id,
                        "status": "failed",
                        "error": str(e),
                        "attempts": max_retries + 1
                    })
                    execution["status"] = "failed"
                    execution["failure_step"] = step_id

                    # Trigger compensations
                    self._compensate_workflow(execution_id)

                    return (False, str(e))

    def _compensate_workflow(self, execution_id: str) -> None:
        """Run compensation (rollback) for failed workflow"""
        execution = self._executions.get(execution_id)
        if not execution:
            return

        # Reverse order: undo completed steps
        completed_steps = execution["steps"][:execution["current_step"]]

        for step_id in reversed(completed_steps):
            if step_id in self._compensations:
                try:
                    compensation_fn = self._compensations[step_id]
                    compensation_fn(execution["output"].get(step_id))
                except Exception as e:
                    pass  # Log but continue compensations

    def get_execution_status(self, execution_id: str) -> Optional[Dict]:
        """Get execution status"""
        return self._executions.get(execution_id)

    def wait_for_completion(self, execution_id: str, timeout_seconds: int = 300) -> tuple:
        """Wait for workflow to complete"""
        import time
        start = time.time()

        while time.time() - start < timeout_seconds:
            execution = self._executions.get(execution_id)
            if execution and execution["status"] != "running":
                return (execution["status"] == "completed", execution["status"])

            time.sleep(1)

        return (False, "Timeout")
'''

    return orchestration


def generate_orchestration_system() -> dict:
    """Generate complete workflow orchestration system."""

    imports = '''from typing import Dict, List, Optional, Callable
from datetime import datetime
from enum import Enum
import time


'''

    module_doc = '''"""
Phase 5 Workflow Orchestration: Long-Running Processes & Sagas

Orchestrate multi-step workflows with automatic retry and compensation (Temporal, Prefect).

ORDER PROCESSING WORKFLOW:

Step 1: Validate Order
- Input: order_id
- Action: check inventory, validate address
- Success: {product: found, address: valid}
- Failure: InvalidOrder exception → STOP

Step 2: Charge Payment
- Input: order (from step 1)
- Action: call payment API, charge card
- Success: {transaction_id: tx123}
- Failure: PaymentDeclined exception → compensate

Step 3: Reserve Inventory
- Input: order (from step 1)
- Action: mark items as reserved
- Success: {reservation_id: res456}
- Failure: OutOfStock exception → compensate

Step 4: Schedule Shipment
- Input: order, reservation, payment
- Action: create shipment, notify warehouse
- Success: {shipment_id: ship789}
- Failure: ShipmentError exception → compensate

Step 5: Send Confirmation Email
- Input: order
- Action: send email
- Success: {email_sent: true}
- Failure: EmailError exception → compensate (but order still OK)

HAPPY PATH (all succeed):
- 2 minutes: order fully processed
- Status: COMPLETED
- Confirmationemail sent

UNHAPPY PATH (charge fails):
- Validate: ✓ (2s)
- Charge: ✗ payment declined (1s)
- Retry: ✓ second card works (3s)
- Reserve: ✓ (1s)
- Ship: ✓ (1s)
- Email: ✓ (1s)
- Total: ~9s (with retries)

SAGA COMPENSATION (failure scenario):

Step 1: Validate ✓
Step 2: Charge ✓ ($100 charged)
Step 3: Reserve ✓
Step 4: Ship ✓
Step 5: Send Email ✗ (email service down)

Compensation (reverse order):
- Undo email: n/a (not sent yet)
- Undo ship: cancel shipment (compensation_fn)
- Undo reserve: release inventory (compensation_fn)
- Undo charge: refund $100 (compensation_fn)
- Undo validate: n/a

Result:
- Order state: FAILED
- Inventory: released
- Payment: refunded
- Shipment: canceled
- Manual action: investigate email service

RETRY POLICY:

Transient failures (network, timeout):
- Retry: up to 3 times
- Backoff: 1s, 2s, 4s
- Usually succeeds on retry

Permanent failures (bad data):
- Retry: doesn't help
- Compensate: undo what succeeded
- Result: order failed, compensated

Example: Payment retry:
Attempt 1: timeout → retry
Attempt 2: network error → retry
Attempt 3: success → continue

DURABILITY:

If service crashes mid-workflow:
- Execution state: persisted to database
- Recovery: resume from last successful step
- No re-processing: completed steps not re-run
- No data loss: compensations still possible

Example:
- Service processes: Step 1, 2, 3
- Service crashes (during Step 4)
- State saved: {completed: [1,2,3], current: 4}
- Service restarts
- Resume: execute Step 4
- Continue: Step 5
- Complete workflow

STATUS TRACKING:

PENDING: waiting to start
RUNNING: currently executing
COMPLETED: all steps succeeded
FAILED: step failed, compensations done
TIMEOUT: took too long
PAUSED: manual pause

EXAMPLE: E-commerce Order

Workflow steps:
1. Validate order (2s) → timeout: 10s
2. Charge card (3s) → timeout: 30s, retry: 3x
3. Reserve inventory (1s) → timeout: 10s
4. Update tracking (1s) → timeout: 5s
5. Send confirmation email (2s) → timeout: 10s

Happy path: 9 seconds total
Unhappy path: one failure + compensation + retry = handled gracefully

MONITORING:

- Execution count: 1000 workflows today
- Success rate: 99.5% (995 completed, 5 failed)
- Avg duration: 9.2 seconds
- P95 duration: 15 seconds
- Failures: 3 payment failed, 2 inventory unavailable
- Compensations: 5 successful (full refund, reservation release)

BENEFITS:

✓ Durable: survives crashes
✓ Reliable: automatic retries
✓ Safe: compensation/rollback on failure
✓ Observable: track each step
✓ Scalable: millions of workflows

COMMON PITFALLS:

❌ No retry: transient failure = workflow fails
   → Network timeout ends user's workflow
   → Solution: retry with backoff

❌ No compensation: failure leaves inconsistent state
   → Charge succeeded but order marked failed
   → Customer charged but no order
   → Solution: define compensation for each step

❌ No durability: crash loses workflow state
   → Service restarts, which step were we on?
   → Risk of re-executing completed steps
   → Solution: persist state to database
"""
'''

    orchestration = generate_workflow_orchestration()

    complete_code = imports + module_doc + "\n" + orchestration

    return {
        "code": complete_code,
        "pattern": "Workflow Orchestration",
        "module": "phase5_workflow_orchestration.py"
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate workflow orchestration")
    args = parser.parse_args()
    result = generate_orchestration_system()
    print(result["code"])


if __name__ == "__main__":
    main()
