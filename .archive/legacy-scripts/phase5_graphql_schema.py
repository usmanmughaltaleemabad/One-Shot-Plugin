#!/usr/bin/env python3
"""
Phase 5 GraphQL: Schema and Resolvers

GraphQL: Query language for APIs.

Problems with REST:
- Over-fetching: get extra fields you don't need
- Under-fetching: need multiple requests
- No schema: unclear what fields exist
- Versioning: break clients with /v2 endpoints

GraphQL:
- Client requests exactly what it needs
- Single request, no over/under-fetching
- Self-documenting (schema describes API)
- No versioning (fields are additive)

GraphQL structure:
- Schema: describes types and operations
- Resolvers: fetch data for each field
- Queries: read data
- Mutations: write data
- Subscriptions: real-time updates

Usage:
    python phase5_graphql_schema.py --resource Order

Input: Resource type
Output: GraphQL schema with resolvers
"""

import argparse
import json
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime


def generate_graphql_schema() -> str:
    """Generate GraphQL schema."""

    schema = '''
class GraphQLSchema:
    """
    GraphQL schema definition.

    Schema defines:
    - Types: Order, User, Payment
    - Fields: Order has id, customer, total, items
    - Queries: getOrder(id), listOrders()
    - Mutations: createOrder(), updateOrder()
    - Subscriptions: orderUpdated()
    """

    # Example: Order schema
    ORDER_SCHEMA = """
    type Order {
        id: ID!
        customer: Customer!
        items: [OrderItem!]!
        total: Float!
        status: OrderStatus!
        createdAt: DateTime!
    }

    type Customer {
        id: ID!
        name: String!
        email: String!
    }

    type OrderItem {
        id: ID!
        product: Product!
        quantity: Int!
        price: Float!
    }

    type Product {
        id: ID!
        name: String!
        description: String
        price: Float!
    }

    enum OrderStatus {
        PENDING
        CONFIRMED
        SHIPPED
        DELIVERED
        CANCELLED
    }

    type Query {
        getOrder(id: ID!): Order
        listOrders(
            limit: Int
            offset: Int
            status: OrderStatus
        ): [Order!]!
        searchOrders(query: String!): [Order!]!
    }

    type Mutation {
        createOrder(input: CreateOrderInput!): Order!
        updateOrder(id: ID!, input: UpdateOrderInput!): Order!
        cancelOrder(id: ID!): Order!
    }

    input CreateOrderInput {
        customerId: ID!
        items: [OrderItemInput!]!
    }

    input OrderItemInput {
        productId: ID!
        quantity: Int!
    }

    input UpdateOrderInput {
        items: [OrderItemInput!]
        status: OrderStatus
    }

    type Subscription {
        orderUpdated(id: ID!): Order!
        orderCreated: Order!
    }
    """
'''

    return schema


def generate_resolvers() -> str:
    """Generate resolver functions."""

    resolvers = '''
class GraphQLResolvers:
    """
    Resolver functions fetch data for each field.

    Resolver: (parent, args, context) → result

    parent: parent object (Order for Order.customer)
    args: arguments (getOrder(id: "123"))
    context: shared context (db, auth, cache)
    """

    def __init__(self, data_loader):
        self.data_loader = data_loader

    # Query Resolvers
    def resolve_get_order(self, args: Dict, context: Dict) -> Optional[Dict]:
        """Query: getOrder(id)"""
        order_id = args.get("id")
        return self.data_loader.load_order(order_id)

    def resolve_list_orders(self, args: Dict, context: Dict) -> List[Dict]:
        """Query: listOrders(limit, offset, status)"""
        limit = args.get("limit", 10)
        offset = args.get("offset", 0)
        status = args.get("status")

        return self.data_loader.list_orders(
            limit=limit,
            offset=offset,
            status=status
        )

    def resolve_search_orders(self, args: Dict, context: Dict) -> List[Dict]:
        """Query: searchOrders(query)"""
        query = args.get("query")
        return self.data_loader.search_orders(query)

    # Mutation Resolvers
    def resolve_create_order(self, args: Dict, context: Dict) -> Dict:
        """Mutation: createOrder(input)"""
        input_data = args.get("input")
        customer_id = input_data.get("customerId")
        items = input_data.get("items", [])

        order = self.data_loader.create_order(customer_id, items)

        # Notify subscribers of new order
        context.get("pubsub", {}).publish("order_created", order)

        return order

    def resolve_update_order(self, args: Dict, context: Dict) -> Dict:
        """Mutation: updateOrder(id, input)"""
        order_id = args.get("id")
        input_data = args.get("input")

        order = self.data_loader.update_order(order_id, input_data)

        # Notify subscribers
        context.get("pubsub", {}).publish(f"order_updated_{order_id}", order)

        return order

    def resolve_cancel_order(self, args: Dict, context: Dict) -> Dict:
        """Mutation: cancelOrder(id)"""
        order_id = args.get("id")
        order = self.data_loader.cancel_order(order_id)

        context.get("pubsub", {}).publish(f"order_updated_{order_id}", order)

        return order

    # Field Resolvers
    def resolve_order_customer(self, order: Dict, args: Dict, context: Dict) -> Dict:
        """Order.customer field"""
        return self.data_loader.load_customer(order["customer_id"])

    def resolve_order_items(self, order: Dict, args: Dict, context: Dict) -> List[Dict]:
        """Order.items field"""
        return self.data_loader.load_order_items(order["id"])

    # Subscription Resolvers
    def resolve_order_updated(self, args: Dict, context: Dict):
        """Subscription: orderUpdated(id)"""
        order_id = args.get("id")
        pubsub = context.get("pubsub")

        # Subscribe to updates for this order
        async def order_updates():
            async for order in pubsub.subscribe(f"order_updated_{order_id}"):
                yield order

        return order_updates()
'''

    return resolvers


def generate_execution_engine() -> str:
    """Generate GraphQL execution engine."""

    engine = '''
class GraphQLExecutionEngine:
    """Execute GraphQL queries/mutations/subscriptions"""

    def __init__(self, schema: str, resolvers: GraphQLResolvers):
        self.schema = schema
        self.resolvers = resolvers

    def execute_query(
        self,
        query: str,
        variables: Optional[Dict] = None,
        context: Optional[Dict] = None
    ) -> Dict:
        """Execute GraphQL query"""
        # Parse query
        # Validate against schema
        # Execute resolvers
        # Return results

        result = {
            "data": {},
            "errors": []
        }

        # Simplified execution (real GraphQL is complex)
        if "getOrder" in query:
            order_id = variables.get("id")
            result["data"]["order"] = self.resolvers.resolve_get_order(
                {"id": order_id},
                context or {}
            )

        return result

    def execute_mutation(
        self,
        mutation: str,
        variables: Optional[Dict] = None,
        context: Optional[Dict] = None
    ) -> Dict:
        """Execute GraphQL mutation"""
        result = {
            "data": {},
            "errors": []
        }

        if "createOrder" in mutation:
            result["data"]["order"] = self.resolvers.resolve_create_order(
                {"input": variables},
                context or {}
            )

        return result

    def subscribe(
        self,
        subscription: str,
        variables: Optional[Dict] = None,
        context: Optional[Dict] = None
    ):
        """Subscribe to GraphQL subscription"""
        if "orderUpdated" in subscription:
            return self.resolvers.resolve_order_updated(variables or {}, context or {})
'''

    return engine


def generate_graphql_system() -> dict:
    """Generate complete GraphQL system."""

    imports = '''from typing import Any, Callable, Dict, List, Optional
from datetime import datetime


'''

    module_doc = '''"""
Phase 5 GraphQL: Schema and Resolvers

Query language and execution engine for APIs.

GraphQL vs REST:

REST endpoint: GET /orders/123
- Returns full order: id, customer, items, status, payment, shipping
- Client gets everything, whether needed or not (over-fetching)

GraphQL query:
query {
  order(id: "123") {
    id
    customer { name }
    total
  }
}
- Returns only requested fields
- No over-fetching
- Single request (no N+1 queries)

GraphQL structure:
1. Schema: describe types and operations
2. Resolvers: fetch data for each field
3. Execution: run resolvers, assemble result

Example resolvers:

Query: getOrder(id: "123")
- Call: resolve_get_order(args={"id": "123"})
- Fetch: SELECT * FROM orders WHERE id = "123"
- Return: order object

Nested field: order.customer
- Call: resolve_order_customer(parent=order, ...)
- Fetch: SELECT * FROM customers WHERE id = order.customer_id
- Return: customer object

Mutation: createOrder(input: {...})
- Call: resolve_create_order(args={"input": {...}}, ...)
- Save: INSERT INTO orders (...)
- Notify: pubsub.publish("order_created", order)
- Return: new order

Subscription: orderUpdated(id: "123")
- Subscribe to: order_updated_123
- When order changes:
  - Resolver fires
  - Client receives update in real-time

Benefits over REST:
✓ No over-fetching (only request what you need)
✓ No under-fetching (single request for related data)
✓ Self-documenting (schema describes API)
✓ No versioning (add fields without /v2)
✓ Real-time updates (subscriptions)
✓ Efficient: less bandwidth
"""
'''

    schema_def = generate_graphql_schema()
    resolvers = generate_resolvers()
    engine = generate_execution_engine()

    complete_code = imports + module_doc + "\n" + schema_def + "\n" + resolvers + "\n" + engine

    return {
        "code": complete_code,
        "pattern": "GraphQL Schema and Resolvers",
        "module": "phase5_graphql_schema.py",
    }


def main():
    parser = argparse.ArgumentParser(description="Generate GraphQL schema")
    parser.add_argument("--resource", help="Resource type")
    parser.add_argument("--output", choices=["json", "code"], default="code")

    args = parser.parse_args()
    result = generate_graphql_system()

    if args.output == "json":
        metadata = {k: v for k, v in result.items() if k != "code"}
        print(json.dumps(metadata, indent=2))
    else:
        print(result["code"])


if __name__ == "__main__":
    main()
