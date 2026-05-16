#!/usr/bin/env python3
"""
Phase 4 DDD: Application Service Generator

Generates Application Services (orchestrators for use cases).
Application Services coordinate between Aggregates, Repositories, and Domain Services.
They handle transaction boundaries and cross-cutting concerns.

Usage:
    python phase4_ddd_application_service.py --aggregate Order --use-cases CreateOrder UpdateOrderStatus CancelOrder

Input: Aggregate and use case names
Output: Application Service classes with transaction management
"""

import argparse
import json
from typing import Any, Optional
from abc import ABC, abstractmethod


def generate_use_case(use_case_name: str, aggregate_name: str) -> str:
    """Generate a Use Case within an Application Service."""

    service_method = use_case_name[0].lower() + use_case_name[1:]  # camelCase

    use_case_code = f"""
    def {service_method}(self, command: "{aggregate_name}{use_case_name}Command") -> str:
        \"\"\"
        Use Case: {use_case_name}

        Responsibilities:
        1. Validate command
        2. Load aggregate from repository
        3. Call aggregate business method
        4. Save aggregate
        5. Publish domain events
        6. Handle transactions

        Args:
            command: Command with use case parameters

        Returns:
            Aggregate ID

        Raises:
            ValueError: If business invariants violated
            {{aggregate_name}}NotFound: If aggregate not found
        \"\"\"
        try:
            # Step 1: Validate command
            command.validate()

            # Step 2: Load aggregate
            aggregate = self.repository.load(command.aggregate_id)
            if not aggregate:
                raise {{aggregate_name}}NotFound(command.aggregate_id)

            # Step 3: Execute business logic
            # TODO: aggregate.{service_method}(command)

            # Step 4: Save aggregate
            self.repository.save(aggregate)

            # Step 5: Publish domain events
            for event in aggregate.changes:
                self.event_bus.publish(event)

            # Step 6: Clear uncommitted events
            aggregate.mark_changes_as_committed()

            return aggregate.id

        except Exception as e:
            # TODO: Log error
            raise
"""

    return use_case_code.replace("{{aggregate_name}}", aggregate_name)


def generate_command_classes(use_case_names: list, aggregate_name: str) -> str:
    """Generate Command classes for use cases."""

    commands = "\n".join([
        f"""
class {aggregate_name}{use_case}Command:
    \"\"\"Command: {use_case}\"\"\"

    def __init__(self, aggregate_id: str, **data):
        self.aggregate_id = aggregate_id
        self.data = data

    def validate(self) -> None:
        \"\"\"Validate command preconditions\"\"\"
        if not self.aggregate_id:
            raise ValueError(f"aggregate_id required")
        # TODO: Add use case-specific validation

    def __repr__(self):
        return f"{aggregate_name}{use_case}Command(aggregate_id='{{self.aggregate_id}}')"
"""
        for use_case in use_case_names
    ])

    return commands


def generate_application_service(aggregate_name: str, use_cases: list) -> dict:
    """
    Generate Application Service class for aggregate.

    Args:
        aggregate_name: Aggregate name (e.g., Order)
        use_cases: List of use case names (e.g., [CreateOrder, UpdateStatus])

    Returns:
        dict with service code and metadata
    """

    imports = '''import uuid
from datetime import datetime
from typing import Any, Optional
from abc import ABC, abstractmethod


class DomainException(Exception):
    """Base class for domain exceptions"""
    pass


'''

    use_case_methods = "\n".join([
        generate_use_case(uc, aggregate_name)
        for uc in use_cases
    ])

    command_classes = generate_command_classes(use_cases, aggregate_name)

    service_code = f'''
class {aggregate_name}ApplicationService:
    \"\"\"
    Application Service: {aggregate_name}

    Orchestrates use cases for {{aggregate_name}} aggregate.
    Coordinates: Repository, Domain Events, Business Rules.
    Manages transaction boundaries.
    \"\"\"

    def __init__(self, repository, event_bus, transaction_manager=None):
        self.repository = repository
        self.event_bus = event_bus
        self.transaction_manager = transaction_manager

{use_case_methods}

    def _begin_transaction(self):
        \"\"\"Start transaction\"\"\"
        if self.transaction_manager:
            return self.transaction_manager.begin()
        return None

    def _commit_transaction(self, tx):
        \"\"\"Commit transaction\"\"\"
        if tx and self.transaction_manager:
            self.transaction_manager.commit(tx)

    def _rollback_transaction(self, tx):
        \"\"\"Rollback transaction on error\"\"\"
        if tx and self.transaction_manager:
            self.transaction_manager.rollback(tx)


class {aggregate_name}NotFound(DomainException):
    \"\"\"Raised when aggregate not found in repository\"\"\"
    def __init__(self, aggregate_id: str):
        super().__init__(f"{aggregate_name} '{{aggregate_id}}' not found")
        self.aggregate_id = aggregate_id


{command_classes}


class {aggregate_name}CommandHandler:
    \"\"\"
    Command Handler: dispatches commands to service.

    In CQRS, commands go through handler -> service -> repository.
    Provides a seam for logging, validation, authorization.
    \"\"\"

    def __init__(self, service: {aggregate_name}ApplicationService):
        self.service = service

    def handle(self, command) -> str:
        \"\"\"
        Handle command by dispatching to service method.

        Args:
            command: Command instance

        Returns:
            Aggregate ID after processing

        Raises:
            DomainException: On business rule violation
        \"\"\"
        command_type = type(command).__name__

        if command_type == "{aggregate_name}CreateCommand":
            return self.service.create(command)
        # TODO: Add dispatcher for other command types
        else:
            raise ValueError(f"Unknown command: {{command_type}}")
'''.replace("{{aggregate_name}}", aggregate_name)

    module_doc = f'''"""
Application Services for {{aggregate_name}}

Application Services are:
- Orchestrators of business logic
- Manage transaction boundaries
- Publish domain events
- Handle cross-cutting concerns (logging, auth)
- One service per aggregate (by domain events)
- Thin: delegate to domain logic, not contain it

Use Cases: {{', '.join(use_cases)}}
""".replace("{{aggregate_name}}", aggregate_name).replace("{{', '.join(use_cases)}}", ", ".join(use_cases))

    complete_code = imports + module_doc + "\n" + service_code

    return {
        "code": complete_code,
        "aggregate": aggregate_name,
        "use_cases": use_cases,
        "use_case_count": len(use_cases),
        "module": f"{aggregate_name.lower()}_service.py",
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate Application Service for aggregate"
    )
    parser.add_argument(
        "--aggregate", required=True,
        help="Aggregate name (e.g., Order)"
    )
    parser.add_argument(
        "--use-cases", nargs="+", required=True,
        help="Use case names (e.g., CreateOrder UpdateStatus CancelOrder)"
    )
    parser.add_argument(
        "--output", choices=["json", "code"], default="code",
        help="Output format"
    )

    args = parser.parse_args()

    result = generate_application_service(args.aggregate, args.use_cases)

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
