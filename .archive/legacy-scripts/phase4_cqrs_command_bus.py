#!/usr/bin/env python3
"""
Phase 4 CQRS: Command Bus

Routes commands to handlers. Commands represent user intent (CreateOrder, PublishPost).
Synchronous, transactional, modifies state.

Usage:
    python phase4_cqrs_command_bus.py --aggregate Order --commands CreateOrder CancelOrder

Input: Aggregate and command names
Output: Command bus with typed command handlers
"""

import argparse
import json
from typing import Any, Callable, Dict, Optional
from abc import ABC, abstractmethod


def generate_command_class(command_name: str) -> str:
    """Generate command class."""

    cmd_code = f'''
class {command_name}:
    """
    Command: {command_name}

    Represents user intent to make a change.
    Commands are:
    - Imperative: "Do this"
    - Synchronous: expects result
    - Transactional: all-or-nothing
    - Request-based: one per user action
    """

    def __init__(self, **data):
        self.data = data
        self.timestamp = datetime.utcnow()
        self.command_id = str(uuid.uuid4())

    def to_dict(self) -> dict:
        return {{
            "command_id": self.command_id,
            "command_type": type(self).__name__,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data
        }}

    def __repr__(self):
        return f"{command_name}(id={{self.command_id}})"
'''

    return cmd_code


def generate_command_handler(command_name: str, aggregate_name: str) -> str:
    """Generate command handler."""

    handler_code = f'''
class {command_name}Handler:
    """Handler for {command_name} command"""

    def __init__(self, repository, event_bus, transaction_manager=None):
        self.repository = repository
        self.event_bus = event_bus
        self.transaction_manager = transaction_manager

    def handle(self, command: {command_name}) -> str:
        """
        Handle {command_name} command.

        Steps:
        1. Load aggregate
        2. Execute business logic
        3. Save aggregate
        4. Publish domain events
        5. Return aggregate ID

        Returns:
            Aggregate ID

        Raises:
            Exception: Command validation or business rule failure
        """
        tx = self._begin_transaction()

        try:
            # Step 1: Validate command
            self._validate_command(command)

            # Step 2: Load aggregate
            aggregate = self.repository.load(command.data.get("id"))
            if not aggregate:
                raise {{aggregate_name}}NotFound(command.data.get("id"))

            # Step 3: Execute business logic
            # TODO: aggregate.{command_name[0].lower() + command_name[1:]}(command)

            # Step 4: Save aggregate
            self.repository.save(aggregate)

            # Step 5: Publish domain events
            for event in aggregate.changes:
                self.event_bus.publish(event)
                aggregate.mark_changes_as_committed()

            self._commit_transaction(tx)
            return aggregate.id

        except Exception as e:
            self._rollback_transaction(tx)
            raise

    def _validate_command(self, command: {command_name}) -> None:
        """Validate command preconditions"""
        # TODO: Add validation logic
        pass

    def _begin_transaction(self):
        if self.transaction_manager:
            return self.transaction_manager.begin()
        return None

    def _commit_transaction(self, tx):
        if tx and self.transaction_manager:
            self.transaction_manager.commit(tx)

    def _rollback_transaction(self, tx):
        if tx and self.transaction_manager:
            self.transaction_manager.rollback(tx)
'''.replace("{{aggregate_name}}", aggregate_name).replace("{{command_name}}", command_name).replace("{{command_name[0].lower() + command_name[1:]}}", command_name[0].lower() + command_name[1:])

    return handler_code


def generate_command_bus() -> str:
    """Generate command bus."""

    bus_code = '''
class CommandBus:
    """
    Command Bus: routes commands to handlers

    Registry maps command type → handler instance.
    Handles transactions, error recovery, logging.
    """

    def __init__(self, transaction_manager=None):
        self._handlers = {}  # command_type -> handler instance
        self._transaction_manager = transaction_manager

    def register(self, command_type: type, handler) -> None:
        """Register command handler"""
        command_name = command_type.__name__
        self._handlers[command_name] = handler

    def execute(self, command) -> Any:
        """
        Execute command synchronously.

        Args:
            command: Command instance

        Returns:
            Result from command handler (typically aggregate ID)

        Raises:
            UnknownCommandException: Handler not registered
            CommandException: Command validation or execution failed
        """
        command_name = type(command).__name__

        if command_name not in self._handlers:
            raise UnknownCommandException(f"No handler for {command_name}")

        handler = self._handlers[command_name]
        return handler.handle(command)

    def __repr__(self):
        return f"CommandBus({len(self._handlers)} handlers)"


class CommandException(Exception):
    """Base exception for command execution"""
    pass


class UnknownCommandException(CommandException):
    """Handler not registered for command"""
    pass
'''

    return bus_code


def generate_cqrs_command_system(aggregate_name: str, commands: list) -> dict:
    """
    Generate complete CQRS command system.

    Args:
        aggregate_name: Aggregate name (e.g., Order)
        commands: Command names (e.g., [CreateOrder, CancelOrder])

    Returns:
        dict with command system code
    """

    imports = '''import uuid
from datetime import datetime
from typing import Any, Callable, Dict, Optional
from abc import ABC, abstractmethod


'''

    module_doc = f'''"""
CQRS Command Bus for {{aggregate_name}}

Commands represent user intent to modify state.
Command Bus routes commands to handlers.
Handlers load aggregate, execute logic, save, publish events.

Pattern: User → Command → CommandBus → CommandHandler → Aggregate → Repository → EventBus
""".replace("{{aggregate_name}}", aggregate_name)

    # Generate all commands
    command_classes = "\n".join([
        generate_command_class(cmd)
        for cmd in commands
    ])

    # Generate all handlers
    handler_classes = "\n".join([
        generate_command_handler(cmd, aggregate_name)
        for cmd in commands
    ])

    # Command bus
    bus = generate_command_bus()

    # Usage example
    example = f'''
# Example Usage

# Create command bus
command_bus = CommandBus()

# Register handlers
order_repository = {{aggregate_name}}MemoryRepository()
event_bus = EventBus()

command_bus.register(CreateOrder, CreateOrderHandler(order_repository, event_bus))
command_bus.register(CancelOrder, CancelOrderHandler(order_repository, event_bus))

# Execute command
try:
    command = CreateOrder(customer_id="123", total=99.99)
    order_id = command_bus.execute(command)
    print(f"Order created: {{order_id}}")
except CommandException as e:
    print(f"Command failed: {{e}}")
'''.replace("{{aggregate_name}}", aggregate_name)

    complete_code = imports + module_doc + "\n" + command_classes + "\n" + handler_classes + "\n" + bus + "\n" + example

    return {
        "code": complete_code,
        "aggregate": aggregate_name,
        "commands": commands,
        "command_count": len(commands),
        "module": f"{aggregate_name.lower()}_commands.py",
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate CQRS command bus"
    )
    parser.add_argument(
        "--aggregate", required=True,
        help="Aggregate name (e.g., Order)"
    )
    parser.add_argument(
        "--commands", nargs="+", required=True,
        help="Command names (e.g., CreateOrder CancelOrder)"
    )
    parser.add_argument(
        "--output", choices=["json", "code"], default="code",
        help="Output format"
    )

    args = parser.parse_args()

    result = generate_cqrs_command_system(args.aggregate, args.commands)

    if args.output == "json":
        metadata = {k: v for k, v in result.items() if k != "code"}
        print(json.dumps(metadata, indent=2))
    else:
        print(result["code"])


if __name__ == "__main__":
    main()
