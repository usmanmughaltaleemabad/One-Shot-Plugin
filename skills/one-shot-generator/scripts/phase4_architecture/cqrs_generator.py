#!/usr/bin/env python3
"""CQRS Generator - Command Query Responsibility Segregation

Generates:
- Command handlers (write side)
- Query handlers (read side)
- Command bus (command routing)
- Query bus (query routing)
- Event handlers (reaction to changes)
- Read models (optimized queries)
"""

import sys
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.base_script import setup_logging, timed_run, check_budget

__version__ = "0.7.0"
logger = setup_logging(__name__)


class CQRSGenerator:
    """Generates CQRS architecture patterns."""

    def __init__(self, framework: str):
        self.framework = framework.lower()

    def generate(self) -> Dict[str, str]:
        files = {}
        files['cqrs/command.py'] = self._command()
        files['cqrs/query.py'] = self._query()
        files['cqrs/command_bus.py'] = self._command_bus()
        files['cqrs/query_bus.py'] = self._query_bus()
        files['cqrs/event_handler.py'] = self._event_handler()
        files['cqrs/read_model.py'] = self._read_model()
        files['cqrs/README.md'] = self._readme()
        return files

    def _command(self) -> str:
        return '''"""Commands - Write Operations"""

from abc import ABC, abstractmethod
from typing import Any
from dataclasses import dataclass


class Command(ABC):
    """Base command - intent to change state"""

    @property
    def command_id(self) -> str:
        """Unique command ID"""
        return getattr(self, '_command_id', None)


@dataclass
class CreateOrderCommand(Command):
    """Command to create an order"""
    customer_id: str
    items: list
    shipping_address: str
    total_amount: float


@dataclass
class CancelOrderCommand(Command):
    """Command to cancel an order"""
    order_id: str
    reason: str


@dataclass
class UpdateInventoryCommand(Command):
    """Command to update inventory"""
    product_id: str
    quantity_change: int
    reason: str


class CommandHandler(ABC):
    """Handler for a specific command"""

    @abstractmethod
    def handle(self, command: Command) -> Any:
        """Handle the command"""
        pass


class CreateOrderHandler(CommandHandler):
    """Handle CreateOrderCommand"""

    def __init__(self, order_repository, event_publisher):
        self.order_repository = order_repository
        self.event_publisher = event_publisher

    def handle(self, command: CreateOrderCommand) -> str:
        """Execute order creation"""
        # Validate command
        if not command.customer_id:
            raise ValueError("Customer ID required")

        # Create aggregate
        order = Order(command.customer_id)
        for item in command.items:
            order.add_item(item["product_id"], item["quantity"], item["price"])

        # Save
        self.order_repository.save(order)

        # Publish events
        for event in order.get_uncommitted_events():
            self.event_publisher.publish(event)

        return order.id
'''

    def _query(self) -> str:
        return '''"""Queries - Read Operations"""

from abc import ABC, abstractmethod
from typing import Any, List


class Query(ABC):
    """Base query - request for data"""
    pass


class GetOrderQuery(Query):
    """Query to get order details"""
    def __init__(self, order_id: str):
        self.order_id = order_id


class ListOrdersQuery(Query):
    """Query to list orders for customer"""
    def __init__(self, customer_id: str, limit: int = 10, offset: int = 0):
        self.customer_id = customer_id
        self.limit = limit
        self.offset = offset


class SearchOrdersQuery(Query):
    """Query to search orders"""
    def __init__(self, status: str = None, date_from = None, date_to = None):
        self.status = status
        self.date_from = date_from
        self.date_to = date_to


class QueryHandler(ABC):
    """Handler for a specific query"""

    @abstractmethod
    def handle(self, query: Query) -> Any:
        """Handle the query"""
        pass


class GetOrderQueryHandler(QueryHandler):
    """Handle GetOrderQuery"""

    def __init__(self, order_read_model):
        self.order_read_model = order_read_model

    def handle(self, query: GetOrderQuery) -> dict:
        """Execute order lookup"""
        return self.order_read_model.get_by_id(query.order_id)


class ListOrdersQueryHandler(QueryHandler):
    """Handle ListOrdersQuery"""

    def __init__(self, order_read_model):
        self.order_read_model = order_read_model

    def handle(self, query: ListOrdersQuery) -> List[dict]:
        """Get orders for customer"""
        return self.order_read_model.find_by_customer(
            query.customer_id,
            limit=query.limit,
            offset=query.offset
        )
'''

    def _command_bus(self) -> str:
        return '''"""Command Bus - Routes Commands to Handlers"""

from typing import Dict, Type
import logging

logger = logging.getLogger(__name__)


class CommandBus:
    """Routes commands to appropriate handlers"""

    def __init__(self):
        self.handlers: Dict[Type, any] = {}

    def register_handler(self, command_type: Type, handler):
        """Register handler for command type"""
        self.handlers[command_type] = handler
        logger.info(f"Registered handler for {command_type.__name__}")

    def execute(self, command):
        """Execute command"""
        command_type = type(command)

        if command_type not in self.handlers:
            raise ValueError(f"No handler for {command_type.__name__}")

        handler = self.handlers[command_type]
        logger.info(f"Executing {command_type.__name__}")

        try:
            result = handler.handle(command)
            logger.info(f"Command {command_type.__name__} succeeded")
            return result
        except Exception as e:
            logger.error(f"Command {command_type.__name__} failed: {e}")
            raise


class SyncCommandBus(CommandBus):
    """Synchronous command bus"""

    def execute(self, command):
        return super().execute(command)


class AsyncCommandBus(CommandBus):
    """Asynchronous command bus (with event loop)"""

    async def execute(self, command):
        """Execute command asynchronously"""
        command_type = type(command)

        if command_type not in self.handlers:
            raise ValueError(f"No handler for {command_type.__name__}")

        handler = self.handlers[command_type]
        return await handler.handle(command)
'''

    def _query_bus(self) -> str:
        return '''"""Query Bus - Routes Queries to Handlers"""

from typing import Dict, Type
import logging

logger = logging.getLogger(__name__)


class QueryBus:
    """Routes queries to appropriate handlers"""

    def __init__(self):
        self.handlers: Dict[Type, any] = {}

    def register_handler(self, query_type: Type, handler):
        """Register handler for query type"""
        self.handlers[query_type] = handler
        logger.debug(f"Registered query handler for {query_type.__name__}")

    def execute(self, query):
        """Execute query"""
        query_type = type(query)

        if query_type not in self.handlers:
            raise ValueError(f"No handler for {query_type.__name__}")

        handler = self.handlers[query_type]
        logger.debug(f"Executing {query_type.__name__}")

        try:
            result = handler.handle(query)
            logger.debug(f"Query {query_type.__name__} succeeded")
            return result
        except Exception as e:
            logger.error(f"Query {query_type.__name__} failed: {e}")
            raise


class CachedQueryBus(QueryBus):
    """Query bus with result caching"""

    def __init__(self, ttl_seconds: int = 3600):
        super().__init__()
        self.cache = {}
        self.ttl_seconds = ttl_seconds

    def execute(self, query):
        """Execute query with caching"""
        query_key = f"{type(query).__name__}:{str(query.__dict__)}"

        if query_key in self.cache:
            logger.debug(f"Cache hit for {type(query).__name__}")
            return self.cache[query_key]

        result = super().execute(query)
        self.cache[query_key] = result
        return result

    def invalidate_cache(self, query_type):
        """Invalidate cache for query type"""
        keys_to_delete = [k for k in self.cache if k.startswith(query_type.__name__)]
        for key in keys_to_delete:
            del self.cache[key]
        logger.info(f"Invalidated cache for {query_type.__name__}")
'''

    def _event_handler(self) -> str:
        return '''"""Event Handlers - React to Domain Events"""

from abc import ABC, abstractmethod
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class EventHandler(ABC):
    """Handler for domain events"""

    @abstractmethod
    def handle(self, event):
        """Handle the event"""
        pass


class UpdateReadModelEventHandler(EventHandler):
    """Update read model when domain event occurs"""

    def __init__(self, read_model):
        self.read_model = read_model

    def handle(self, event):
        """Update read model"""
        logger.info(f"Updating read model for {type(event).__name__}")

        if hasattr(event, "aggregate_id"):
            self.read_model.update(event.aggregate_id, event)


class SendEmailEventHandler(EventHandler):
    """Send email when event occurs"""

    def __init__(self, email_service):
        self.email_service = email_service

    def handle(self, event):
        """Send email"""
        if hasattr(event, "customer_email"):
            logger.info(f"Sending email for {type(event).__name__}")
            self.email_service.send(
                to=event.customer_email,
                subject=f"{type(event).__name__}",
                body=str(event)
            )


class EventBus:
    """Publishes events to handlers"""

    def __init__(self):
        self.handlers: Dict[str, List[EventHandler]] = {}

    def subscribe(self, event_type: str, handler: EventHandler):
        """Subscribe handler to event type"""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
        logger.info(f"Subscribed {handler.__class__.__name__} to {event_type}")

    def publish(self, event):
        """Publish event to all subscribers"""
        event_type = type(event).__name__
        logger.info(f"Publishing {event_type}")

        if event_type not in self.handlers:
            logger.debug(f"No subscribers for {event_type}")
            return

        for handler in self.handlers[event_type]:
            try:
                handler.handle(event)
            except Exception as e:
                logger.error(f"Error handling {event_type}: {e}")
'''

    def _read_model(self) -> str:
        return '''"""Read Models - Optimized for Queries"""

from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class ReadModel:
    """Denormalized data for fast queries"""

    def __init__(self, name: str):
        self.name = name
        self.data = {}

    def update(self, key: str, data: dict):
        """Update read model"""
        self.data[key] = data
        logger.debug(f"Updated {self.name}: {key}")

    def get_by_id(self, key: str) -> Optional[dict]:
        """Get by ID"""
        return self.data.get(key)

    def find_all(self) -> List[dict]:
        """Get all"""
        return list(self.data.values())

    def find_by_property(self, property_name: str, value) -> List[dict]:
        """Find by property value"""
        return [d for d in self.data.values() if d.get(property_name) == value]

    def clear(self):
        """Clear read model (for rebuilding)"""
        self.data.clear()
        logger.info(f"Cleared {self.name}")


class OrderReadModel(ReadModel):
    """Read model for orders"""

    def __init__(self):
        super().__init__("orders")

    def find_by_customer(self, customer_id: str, limit: int = 10, offset: int = 0) -> List[dict]:
        """Find orders by customer"""
        customer_orders = self.find_by_property("customer_id", customer_id)
        return customer_orders[offset:offset + limit]

    def find_by_status(self, status: str) -> List[dict]:
        """Find orders by status"""
        return self.find_by_property("status", status)

    def get_customer_total(self, customer_id: str) -> float:
        """Get total spent by customer"""
        orders = self.find_by_customer(customer_id)
        return sum(o.get("total_amount", 0) for o in orders)
'''

    def _readme(self) -> str:
        return '''# CQRS - Command Query Responsibility Segregation

## Write Side: Commands

Define intent to change state:

```python
from cqrs.command import CreateOrderCommand, CancelOrderCommand

# Commands are simple data holders
cmd = CreateOrderCommand(
    customer_id="customer-1",
    items=[{"product_id": "p1", "quantity": 2}],
    shipping_address="123 Main St",
    total_amount=99.99
)

# Route to handler via command bus
command_bus.execute(cmd)
```

## Read Side: Queries

Request data without side effects:

```python
from cqrs.query import GetOrderQuery, ListOrdersQuery

# Queries are simple data holders
query = GetOrderQuery(order_id="order-123")
order = query_bus.execute(query)

# Get multiple orders
query = ListOrdersQuery(customer_id="customer-1", limit=10)
orders = query_bus.execute(query)
```

## Command Bus

Routes commands to handlers:

```python
from cqrs.command_bus import CommandBus

bus = CommandBus()
bus.register_handler(CreateOrderCommand, CreateOrderHandler(repo, publisher))
bus.register_handler(CancelOrderCommand, CancelOrderHandler(repo, publisher))

bus.execute(CreateOrderCommand(...))
```

## Query Bus

Routes queries to handlers (with optional caching):

```python
from cqrs.query_bus import CachedQueryBus

bus = CachedQueryBus(ttl_seconds=3600)
bus.register_handler(GetOrderQuery, GetOrderQueryHandler(read_model))

# First call hits handler
result = bus.execute(GetOrderQuery("order-1"))

# Second call returns from cache
result = bus.execute(GetOrderQuery("order-1"))
```

## Event Handlers

React to changes:

```python
from cqrs.event_handler import UpdateReadModelEventHandler, EventBus

event_bus = EventBus()

# Update read model when order created
handler = UpdateReadModelEventHandler(order_read_model)
event_bus.subscribe("OrderCreatedEvent", handler)

# Send email when order shipped
email_handler = SendEmailEventHandler(email_service)
event_bus.subscribe("OrderShippedEvent", email_handler)
```

## Read Models

Denormalized data optimized for reads:

```python
from cqrs.read_model import OrderReadModel

read_model = OrderReadModel()

# Get by customer (pre-aggregated)
orders = read_model.find_by_customer("customer-1")

# Get customer total spent (already aggregated)
total = read_model.get_customer_total("customer-1")
```

## Full Flow

```
Write Side:
1. Receive CreateOrderCommand
2. Create Order aggregate
3. Aggregate emits OrderCreatedEvent
4. Save aggregate to repository
5. Publish OrderCreatedEvent

Read Side:
1. EventHandler receives OrderCreatedEvent
2. Updates OrderReadModel with new order data
3. Denormalized data ready for fast queries
```

## Benefits

- **Write and Read scaling**: Scale write and read separately
- **Read optimization**: Optimize read model schema for fast queries
- **Temporal queries**: Keep historical read models
- **Simple handlers**: Each command handler is simple and focused
- **Complex queries**: Complex queries become simple lookups

## Example: E-commerce Orders

```
Commands:
- CreateOrderCommand
- AddItemCommand
- CheckoutCommand
- ShipOrderCommand
- DeliverOrderCommand

Queries:
- GetOrderQuery
- ListOrdersQuery
- SearchOrdersQuery
- GetCustomerStatsQuery (pre-aggregated)
```
'''


def main():
    with timed_run("cqrs_generator") as timer:
        logger.debug("Testing CQRS generation")
        gen = CQRSGenerator("python")
        files = gen.generate()
        logger.debug(f"Generated {len(files)} CQRS files")
        for filepath in files:
            print(f"  ✓ {filepath}")
        check_budget("cqrs_generator", timer.elapsed_ms, logger)


if __name__ == '__main__':
    main()
