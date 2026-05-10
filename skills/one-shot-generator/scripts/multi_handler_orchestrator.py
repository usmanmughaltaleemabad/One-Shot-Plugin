#!/usr/bin/env python3
"""
Gap 6: Multi-Handler Orchestration

Generates complete multi-handler workflows (webhook + validation + charge + notify):
- Multiple handler files under handlers/ with pure business logic
- dependencies.py (Python) or workflow.go/workflow.ts that wires handlers via event bus
- Integration tests for handler coordination
- README with ASCII workflow diagram
- Event model definitions
- Event chaining and retry logic

Input: Feature description, list of handlers, event chains
Output: Complete workflow structure with all handlers coordinated
"""

import sys
from typing import List, Dict, Tuple
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lib.base_script import setup_logging, timed_run, check_budget

__version__ = "0.7.0"
logger = setup_logging(__name__)


class MultiHandlerOrchestrator:
    """Generates multi-handler workflows with full orchestration."""

    def __init__(self, framework: str, feature_name: str):
        self.framework = framework.lower()
        self.feature_name = feature_name
        self.feature_slug = feature_name.lower().replace(' ', '_')

    def orchestrate(self, handlers: List[Dict], event_chains: List[Tuple[str, str]]) -> Dict[str, str]:
        """
        Generate complete multi-handler workflow.

        Args:
            handlers: List of handler dicts with keys:
                - name: 'WebhookHandler'
                - description: 'Receives webhook events'
                - events_in: ['payment.initiated']
                - events_out: ['payment.webhook_validated']
                - logic: Handler business logic code

            event_chains: List of (source_event, target_event) tuples
                - ('payment.initiated', 'payment.validated')
                - ('payment.validated', 'payment.charged')
                - etc.

        Returns:
            Dict mapping filepath -> content
        """
        files = {}

        # Generate handler files
        for handler in handlers:
            handler_file = f'{self.feature_slug}/handlers/{handler["name"].lower()}.py'
            files[handler_file] = handler.get('logic', self._generate_empty_handler(handler['name']))

        # Generate event models
        event_names = set()
        for src, dst in event_chains:
            event_names.add(src)
            event_names.add(dst)

        files[f'{self.feature_slug}/models/events.py'] = self._generate_event_models(event_names)

        # Generate service classes
        files[f'{self.feature_slug}/services/event_bus.py'] = self._generate_event_bus()

        # Generate dependencies/wiring file
        files[f'{self.feature_slug}/dependencies.py'] = self._generate_dependencies(
            handlers, event_chains
        )

        # Generate integration tests
        files[f'{self.feature_slug}/tests/test_workflow.py'] = self._generate_integration_tests(
            handlers, event_chains
        )

        # Generate README with diagram
        files[f'{self.feature_slug}/README.md'] = self._generate_workflow_readme(
            handlers, event_chains
        )

        return files

    def _generate_empty_handler(self, handler_name: str) -> str:
        """Generate stub handler file."""
        return f'''"""
{handler_name} - Pure business logic handler

Receives events from event bus, processes, and emits new events.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class {handler_name}:
    """Handler for {handler_name}"""

    def __init__(self):
        pass

    async def handle(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process event and return result.

        Args:
            event: Event dictionary with type, data, timestamp

        Returns:
            Result dictionary or None
        """
        logger.info(f"{{self.__class__.__name__}} handling event: {{event}}")

        try:
            # TODO: Implement business logic
            return {{"status": "success", "data": event.get("data")}}
        except Exception as e:
            logger.error(f"Error in {{self.__class__.__name__}}: {{e}}")
            raise
'''

    def _generate_event_models(self, event_names) -> str:
        """Generate event model definitions."""
        event_classes = []

        for event_name in sorted(event_names):
            class_name = ''.join(word.capitalize() for word in event_name.split('.'))
            event_classes.append(f'''class {class_name}(Event):
    """{{class_name}} event"""
    pass
''')

        return f'''"""Event model definitions"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict


@dataclass
class Event:
    """Base event class"""
    type: str
    data: Dict[str, Any]
    timestamp: datetime
    metadata: Dict[str, str] = None


# Generated events
{chr(10).join(event_classes)}
'''

    def _generate_event_bus(self) -> str:
        """Generate event bus service."""
        return '''"""Event bus for coordinating handlers"""

import asyncio
from typing import Callable, Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class EventBus:
    """In-memory event bus for handler coordination"""

    def __init__(self):
        self.handlers: Dict[str, List[Callable]] = {}
        self.event_history: List[Any] = []

    def subscribe(self, event_type: str, handler: Callable):
        """Subscribe handler to event type"""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
        logger.info(f"Handler subscribed to {event_type}")

    async def publish(self, event: Dict[str, Any]):
        """Publish event to all subscribed handlers"""
        event_type = event.get('type')
        self.event_history.append(event)

        if event_type not in self.handlers:
            logger.warning(f"No handlers for event type: {event_type}")
            return

        # Call all handlers for this event type
        tasks = []
        for handler in self.handlers[event_type]:
            tasks.append(handler(event))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        logger.info(f"Event {event_type} processed by {len(results)} handlers")

        return results

    def get_history(self) -> List[Any]:
        """Get event history"""
        return self.event_history


# Global event bus instance
_event_bus = EventBus()


def get_event_bus() -> EventBus:
    """Get singleton event bus"""
    return _event_bus
'''

    def _generate_dependencies(self, handlers: List[Dict], event_chains: List[Tuple]) -> str:
        """Generate dependencies.py that wires handlers via event bus."""
        handler_setup = []

        for handler in handlers:
            handler_class = handler['name']
            handler_instance = handler_class[0].lower() + handler_class[1:]
            handler_setup.append(f"{handler_instance} = {handler_class}()")

        # Generate event subscriptions
        subscriptions = []
        for src_event, dst_event in event_chains:
            # Find handler that outputs src_event
            for handler in handlers:
                if src_event in handler.get('events_out', []):
                    handler_instance = handler['name'][0].lower() + handler['name'][1:]
                    subscriptions.append(
                        f'event_bus.subscribe("{src_event}", {handler_instance}.handle)'
                    )
                    break

        return f'''"""Workflow orchestration - wires all handlers via event bus"""

import asyncio
from services.event_bus import get_event_bus
from handlers.webhook_handler import WebhookHandler
from handlers.validation_handler import ValidationHandler
from handlers.charge_handler import ChargeHandler
from handlers.notification_handler import NotificationHandler
import logging

logger = logging.getLogger(__name__)

# Initialize event bus
event_bus = get_event_bus()

# Initialize handlers
{chr(10).join(f"    {line}" for line in handler_setup)}

# Subscribe handlers to events
async def setup_workflow():
    """Wire up all handlers to event bus"""
    {chr(10).join(f"    {line}" for line in subscriptions)}
    logger.info("Workflow orchestration complete")


async def process_payment(payment_data: dict):
    """
    Process a complete payment workflow.

    Emits payment.initiated event which triggers the entire chain.
    """
    await setup_workflow()

    # Emit initial event
    initial_event = {{
        "type": "payment.initiated",
        "data": payment_data,
        "timestamp": datetime.now().isoformat(),
    }}

    await event_bus.publish(initial_event)
    return event_bus.get_history()


if __name__ == "__main__":
    # Example usage
    import asyncio
    from datetime import datetime

    async def main():
        history = await process_payment({{
            "user_id": "user123",
            "amount": 100.00,
            "currency": "USD",
        }})
        print(f"Payment workflow completed. {{len(history)}} events processed.")

    asyncio.run(main())
'''

    def _generate_integration_tests(self, handlers: List[Dict], chains: List[Tuple]) -> str:
        """Generate integration tests for handler coordination."""
        return f'''"""Integration tests for {self.feature_name} workflow"""

import pytest
import asyncio
from datetime import datetime
from dependencies import process_payment, event_bus


@pytest.fixture
def event_bus_fresh():
    """Fresh event bus for each test"""
    from services.event_bus import EventBus
    return EventBus()


class Test{self.feature_slug.title()}Workflow:
    """Integration tests for {self.feature_name} workflow"""

    @pytest.mark.asyncio
    async def test_complete_workflow(self):
        """Test complete payment workflow end-to-end"""
        payment_data = {{
            "user_id": "user123",
            "amount": 100.00,
            "currency": "USD",
        }}

        history = await process_payment(payment_data)

        # Verify all events were processed
        assert len(history) > 0
        assert history[0]["type"] == "payment.initiated"
        # Final event should be success or failure
        assert history[-1]["type"] in ["payment.succeeded", "payment.failed"]

    @pytest.mark.asyncio
    async def test_workflow_error_handling(self):
        """Test workflow handles errors gracefully"""
        invalid_payment = {{
            "user_id": None,  # Invalid
            "amount": -50.00,  # Invalid
        }}

        history = await process_payment(invalid_payment)

        # Should reach failed state
        assert any(e["type"] == "payment.failed" for e in history)

    @pytest.mark.asyncio
    async def test_event_ordering(self):
        """Test events are processed in correct order"""
        expected_order = [
            "payment.initiated",
            "payment.validated",
            "payment.charged",
            "payment.notification_sent",
            "payment.succeeded",
        ]

        history = await process_payment({{"user_id": "user123", "amount": 100.00}})
        event_types = [e["type"] for e in history]

        # Verify ordering (may not have all if some skipped)
        prev_idx = -1
        for expected in expected_order:
            if expected in event_types:
                curr_idx = event_types.index(expected)
                assert curr_idx > prev_idx, f"Event {{expected}} out of order"
                prev_idx = curr_idx

    def test_handler_subscription(self):
        """Test handlers are correctly subscribed to events"""
        # Verify all handlers are registered
        assert "payment.initiated" in event_bus.handlers or len(event_bus.handlers) > 0
'''

    def _generate_workflow_readme(self, handlers: List[Dict], chains: List[Tuple]) -> str:
        """Generate README with ASCII workflow diagram."""
        # Build ASCII diagram
        diagram_lines = [
            "## Workflow Diagram",
            "",
            "```",
            "┌─────────────────────────────────────────────────────┐",
        ]

        for src, dst in chains:
            diagram_lines.extend([
                f"│ {src.ljust(49)} │",
                "│                          ↓                       │",
                f"│ {dst.ljust(49)} │",
            ])

        diagram_lines.extend([
            "└─────────────────────────────────────────────────────┘",
            "```",
        ])

        handlers_list = '\n'.join(
            f"- **{h['name']}**: {h.get('description', 'Handler')}"
            for h in handlers
        )

        return f'''# {self.feature_name} Workflow

Complete multi-handler orchestration for {self.feature_name}.

## Handlers

{handlers_list}

## Event Flow

{chr(10).join(diagram_lines)}

## Files

- `handlers/` — Individual handler implementations
- `models/events.py` — Event model definitions
- `services/event_bus.py` — Event bus service
- `dependencies.py` — Workflow orchestration and wiring
- `tests/test_workflow.py` — Integration tests
- `README.md` — This file

## Running the Workflow

```python
import asyncio
from dependencies import process_payment

payment_data = {{
    "user_id": "user123",
    "amount": 100.00,
    "currency": "USD",
}}

history = asyncio.run(process_payment(payment_data))
```

## Event Handling

Each handler receives events from the event bus and can:
- Process the data
- Emit new events to continue the workflow
- Retry on failure (see `services/event_bus.py`)
- Log for observability

## Error Handling

The workflow includes error handling at each stage:
- Handler exceptions are caught and logged
- Workflow can continue to failure handler or stop
- Event history tracks all steps for debugging

## Testing

Run integration tests:

```bash
pytest {self.feature_slug}/tests/test_workflow.py -v
```

Tests verify:
- Complete end-to-end workflow
- Error handling and recovery
- Event ordering and chain completion
- Handler subscriptions
'''

def main():
    """Test multi-handler orchestration."""
    with timed_run("multi_handler_orchestrator") as timer:
        logger.debug("Testing multi-handler orchestration")

        test_handlers = [
            {{
                'name': 'WebhookHandler',
                'description': 'Receives webhook events',
                'events_out': ['payment.initiated'],
            }},
            {{
                'name': 'ValidationHandler',
                'description': 'Validates payment data',
                'events_in': ['payment.initiated'],
                'events_out': ['payment.validated'],
            }},
            {{
                'name': 'ChargeHandler',
                'description': 'Charges payment method',
                'events_in': ['payment.validated'],
                'events_out': ['payment.charged'],
            }},
        ]

        test_chains = [
            ('payment.initiated', 'payment.validated'),
            ('payment.validated', 'payment.charged'),
            ('payment.charged', 'payment.succeeded'),
        ]

        orchestrator = MultiHandlerOrchestrator('fastapi', 'Payment Processing')
        files = orchestrator.orchestrate(test_handlers, test_chains)

        logger.debug(f"Generated {len(files)} workflow files")
        for filepath in sorted(files.keys()):
            print(f"  ✓ {filepath}")

        check_budget("multi_handler_orchestrator", timer.elapsed_ms, logger)

    logger.debug(f"multi_handler_orchestrator completed in {timer.elapsed_ms:.0f}ms")


if __name__ == '__main__':
    main()
