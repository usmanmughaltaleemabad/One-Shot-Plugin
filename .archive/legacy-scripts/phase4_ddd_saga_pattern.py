#!/usr/bin/env python3
"""
Phase 4 DDD: Saga Pattern Generator

Generates Saga pattern for orchestrating long-running transactions across aggregates.
Sagas maintain consistency without distributed transactions (2-phase commit).

Usage:
    python phase4_ddd_saga_pattern.py --saga OrderSaga --steps CreateOrder ProcessPayment ShipOrder --compensations

Input: Saga name and steps
Output: Saga orchestration with compensating transactions
"""

import argparse
import json
from typing import Any, Optional, List
from enum import Enum


class SagaStepStatus(Enum):
    """Saga step execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"
    FAILED = "failed"


def generate_saga_step(step_name: str, saga_name: str) -> str:
    """Generate a Saga step definition."""

    step_code = f'''
class {step_name}Step:
    """Saga step: {step_name}"""

    def __init__(self):
        self.status = SagaStepStatus.PENDING
        self.result = None
        self.error = None

    def execute(self, context: dict) -> Any:
        """
        Execute step action.

        Args:
            context: Saga context (data shared between steps)

        Returns:
            Step result

        Raises:
            Exception: Step failure (triggers compensation)
        """
        try:
            self.status = SagaStepStatus.RUNNING
            # TODO: Implement action
            # Example: context['order_id'] = create_order(context['order'])
            self.status = SagaStepStatus.COMPLETED
            return self.result
        except Exception as e:
            self.error = e
            self.status = SagaStepStatus.FAILED
            raise

    def compensate(self, context: dict) -> None:
        """
        Compensate (rollback) step action on saga failure.

        Args:
            context: Saga context

        Raises:
            Exception: Compensation failure (critical - may need manual intervention)
        """
        try:
            if self.status == SagaStepStatus.COMPLETED:
                self.status = SagaStepStatus.COMPENSATING
                # TODO: Implement compensation
                # Example: cancel_order(context['order_id'])
                self.status = SagaStepStatus.COMPENSATED
        except Exception as e:
            raise SagaCompensationFailure(
                f"Failed to compensate {{type(self).__name__}}: {{str(e)}}"
            )
'''

    return step_code.replace("{{type(self).__name__}}", step_name)


def generate_saga_orchestrator(saga_name: str, steps: list) -> str:
    """Generate Saga orchestrator."""

    # Build step sequence
    step_definitions = "\n        ".join([
        f"self.{step[0].lower() + step[1:]} = {step}Step()"
        for step in steps
    ])

    # Build execution sequence
    step_executions = "\n            ".join([
        f'self._execute_step(self.{step[0].lower() + step[1:]}, "{step}", context)'
        for step in steps
    ])

    # Build compensation sequence (reverse)
    step_compensations = "\n            ".join([
        f'self._compensate_step(self.{step[0].lower() + step[1:]}, "{step}", context)'
        for step in reversed(steps)
    ])

    orchestrator_code = f'''
class {saga_name}:
    """
    Saga: {saga_name}

    Orchestrates a long-running transaction across multiple aggregates.
    Maintains consistency without distributed transactions.

    Steps: {', '.join(steps)}

    On failure, compensating transactions run in reverse order.
    """

    def __init__(self):
        {step_definitions}
        self.status = SagaStepStatus.PENDING
        self.context = {{}}

    def execute(self, **initial_data) -> dict:
        """
        Execute saga to completion.

        Args:
            **initial_data: Initial context data

        Returns:
            Saga context (final state)

        Raises:
            SagaFailure: Saga failed and was compensated
        """
        self.context = initial_data
        self.status = SagaStepStatus.RUNNING

        try:
            # Execute all steps in sequence
            {step_executions}

            self.status = SagaStepStatus.COMPLETED
            return self.context

        except Exception as e:
            self.status = SagaStepStatus.FAILED
            # Compensate all completed steps in reverse
            {step_compensations}
            raise SagaFailure(f"{{saga_name}} failed: {{str(e)}}")

    def _execute_step(self, step, step_name: str, context: dict) -> None:
        \"\"\"Execute step and record result\"\"\"
        try:
            result = step.execute(context)
            context[f"{{step_name}}_result"] = result
        except Exception as e:
            raise SagaStepFailure(f"Step {{step_name}} failed: {{str(e)}}", step_name)

    def _compensate_step(self, step, step_name: str, context: dict) -> None:
        \"\"\"Compensate step on saga failure\"\"\"
        try:
            step.compensate(context)
        except SagaCompensationFailure as e:
            # Compensation failure is critical
            raise SagaCriticalFailure(f"Cannot compensate {{step_name}}: {{str(e)}}")

    def __repr__(self):
        return f"{{saga_name}}(status={{self.status.value}})"
'''.replace("{{saga_name}}", saga_name).replace("{{', '.join(steps)}}", ", ".join(steps))

    return orchestrator_code


def generate_saga_exceptions() -> str:
    """Generate Saga exception classes."""

    exceptions = '''
class SagaException(Exception):
    """Base class for saga exceptions"""
    pass


class SagaFailure(SagaException):
    """Saga failed and was compensated"""
    pass


class SagaStepFailure(SagaException):
    """A saga step failed"""
    def __init__(self, message: str, step_name: str):
        super().__init__(message)
        self.step_name = step_name


class SagaCompensationFailure(SagaException):
    """Compensation (rollback) of a step failed"""
    pass


class SagaCriticalFailure(SagaException):
    """Critical saga failure - manual intervention required"""
    pass
'''

    return exceptions


def generate_sagas(saga_name: str, steps: list) -> dict:
    """
    Generate Saga orchestration pattern.

    Args:
        saga_name: Saga name (e.g., OrderSaga)
        steps: List of step names (e.g., [CreateOrder, ProcessPayment, ShipOrder])

    Returns:
        dict with saga code and metadata
    """

    imports = '''from enum import Enum
from typing import Any, Optional, List
from abc import ABC, abstractmethod


'''

    module_doc = f'''"""
Saga Pattern: {{saga_name}}

Sagas orchestrate long-running transactions across multiple aggregates.
Unlike 2-phase commit, sagas use compensating transactions for consistency.

Steps (in order):
{{steps_list}}

Failure Handling:
- If any step fails, all completed steps are compensated in reverse
- Compensation is idempotent (safe to retry)
- If compensation fails, SagaCriticalFailure is raised (may need manual intervention)

Example:
    saga = {{saga_name}}()
    try:
        result = saga.execute(order_id="123", total=99.99)
    except SagaFailure:
        # Saga failed and was compensated - system is consistent
        pass
""".replace("{{saga_name}}", saga_name).replace("{{steps_list}}", "\n".join([f"- {step}" for step in steps]))

    status_enum = '''
class SagaStepStatus(Enum):
    """Saga step status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    COMPENSATING = "compensating"
    COMPENSATED = "compensated"
    FAILED = "failed"
'''

    # Generate all steps
    all_steps = "\n\n".join([
        generate_saga_step(step, saga_name)
        for step in steps
    ])

    exceptions = generate_saga_exceptions()
    orchestrator = generate_saga_orchestrator(saga_name, steps)

    complete_code = (
        imports + module_doc + "\n" + status_enum + "\n" +
        all_steps + "\n" + exceptions + "\n" + orchestrator
    )

    return {
        "code": complete_code,
        "saga": saga_name,
        "steps": steps,
        "step_count": len(steps),
        "module": f"{saga_name.lower()}.py",
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate Saga pattern orchestration"
    )
    parser.add_argument(
        "--saga", required=True,
        help="Saga name (e.g., OrderSaga)"
    )
    parser.add_argument(
        "--steps", nargs="+", required=True,
        help="Step names in order (e.g., CreateOrder ProcessPayment ShipOrder)"
    )
    parser.add_argument(
        "--output", choices=["json", "code"], default="code",
        help="Output format"
    )

    args = parser.parse_args()

    result = generate_sagas(args.saga, args.steps)

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
