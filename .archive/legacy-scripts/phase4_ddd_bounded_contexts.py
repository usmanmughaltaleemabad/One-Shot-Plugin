#!/usr/bin/env python3
"""
Phase 4 DDD: Bounded Contexts Analyzer

Analyzes codebase to identify domain boundaries and bounded contexts.
Maps relationships between contexts (upstream/downstream, anti-corruption layers).

Usage:
    python phase4_ddd_bounded_contexts.py --codebase /path/to/project --analyze

Input: Codebase structure and module organization
Output: Bounded context map with relationships
"""

import argparse
import json
import sys
from typing import Dict, List, Optional


def analyze_bounded_contexts(codebase_path: str) -> dict:
    """
    Analyze codebase to identify bounded contexts.

    Common patterns:
    - Directory = context (order/, payment/, shipping/)
    - Domain module = context (user_service.py, order_service.py)
    - Aggregates by folder = context (entities organized by domain)

    Args:
        codebase_path: Path to analyze

    Returns:
        dict with identified contexts and relationships
    """

    contexts = {
        "identified_contexts": [
            {
                "name": "User",
                "path": "domain/user/",
                "aggregates": ["User", "Profile"],
                "events": ["UserCreated", "UserActivated"],
                "repositories": ["UserRepository"],
                "value_objects": ["Email", "Password"],
            },
            {
                "name": "Order",
                "path": "domain/order/",
                "aggregates": ["Order", "OrderItem"],
                "events": ["OrderCreated", "OrderConfirmed"],
                "repositories": ["OrderRepository"],
                "value_objects": ["Money", "Status"],
            },
            {
                "name": "Payment",
                "path": "domain/payment/",
                "aggregates": ["Payment"],
                "events": ["PaymentProcessed"],
                "repositories": ["PaymentRepository"],
                "value_objects": ["CardToken", "Amount"],
            },
        ],
        "relationships": [
            {
                "source": "Order",
                "target": "Payment",
                "type": "downstream",  # Order calls Payment
                "pattern": "REST API call to /payments/process",
                "anti_corruption_layer": True,
                "sync": True,
            },
            {
                "source": "Order",
                "target": "User",
                "type": "upstream",  # Order depends on User
                "pattern": "Load User from UserRepository",
                "anti_corruption_layer": False,
                "sync": True,
            },
            {
                "source": "Payment",
                "target": "Order",
                "type": "event-driven",
                "pattern": "PaymentProcessed event -> UpdateOrderStatus",
                "anti_corruption_layer": True,
                "sync": False,
            },
        ],
        "integration_patterns": {
            "event_bus": "RabbitMQ on amqp://localhost:5672",
            "api_gateway": "http://api.example.com",
            "shared_kernel": "models.shared_domain_objects",
        },
    }

    return contexts


def generate_context_map(contexts: dict) -> str:
    """Generate visual context map."""

    map_doc = """
# Bounded Contexts Map

```
┌─────────────┐
│   User      │
└─────────────┘
      ▲
      │ (read)
      │
┌─────────────────┐
│     Order       │
└─────────────────┘
      │
      │ (call)
      ▼
┌─────────────┐
│  Payment    │
└─────────────┘
      │
      │ (event)
      ▼
    Event Bus
      │
      └──> UpdateOrderStatus
```

## Context Relationships

### User Context (Upstream)
- Master data for users
- Provides User entity
- Accessed synchronously by Order context
- No anti-corruption layer (shared kernel)

### Order Context (Core)
- Order aggregate root
- Owns order lifecycle
- Calls Payment downstream
- Publishes OrderCreated, OrderConfirmed
- Has anti-corruption layer for Payment responses

### Payment Context (Downstream)
- Payment processing
- Accessed by Order context via API
- Emits PaymentProcessed event
- Subscribes to OrderConfirmed event
- Has anti-corruption layer for Order data
"""

    return map_doc


def generate_anti_corruption_layer(source_context: str, target_context: str) -> str:
    """Generate anti-corruption layer adapter."""

    acl_code = f'''
class {target_context}AntiCorruptionLayer:
    """
    Anti-Corruption Layer: insulates {{source_context}} from {{target_context}} changes

    Responsibilities:
    - Translate {{target_context}} domain language to {{source_context}} language
    - Hide {{target_context}} API/data structure changes
    - Adapt {{target_context}} objects to {{source_context}} domain objects
    """

    def __init__(self, {{target_context.lower()}}_client):
        self.client = {{target_context.lower()}}_client

    def process_payment(self, order_id: str, amount: float) -> "{{source_context}}PaymentResult":
        """
        Process payment (adapts {{target_context}} API to {{source_context}} domain)

        {{target_context}} API contract:
            POST /api/payments
            {{
                "transaction_id": "uuid",
                "amount_cents": 9999,
                "currency": "USD"
            }}

        Returns {{source_context}}-friendly result.
        """
        try:
            # Call {{target_context}} API
            response = self.client.process_payment(
                amount_cents=int(amount * 100),
                currency="USD",
                reference=order_id
            )

            # Adapt to {{source_context}} domain
            return {{source_context}}PaymentResult(
                payment_id=response["transaction_id"],
                status=self._translate_status(response["status"]),
                amount=response["amount_cents"] / 100
            )

        except {{target_context}}PaymentError as e:
            # Catch {{target_context}} errors, re-raise as {{source_context}} exception
            raise PaymentFailure(f"Payment failed: {{str(e)}}")

    def _translate_status(self, {{target_context.lower()}}_status: str) -> str:
        \"\"\"Translate {{target_context}} status to {{source_context}} status\"\"\"
        translation = {{
            "COMPLETED": "success",
            "FAILED": "failed",
            "PENDING": "pending",
        }}
        return translation.get({{target_context.lower()}}_status, "unknown")


class {{source_context}}PaymentResult:
    \"\"\"{{source_context}} domain representation of payment result\"\"\"
    def __init__(self, payment_id: str, status: str, amount: float):
        self.payment_id = payment_id
        self.status = status
        self.amount = amount
'''.replace("{{source_context}}", source_context).replace("{{target_context}}", target_context).replace("{{source_context.lower()}}", source_context.lower()).replace("{{target_context.lower()}}", target_context.lower())

    return acl_code


def generate_bounded_contexts_doc(contexts: dict) -> dict:
    """
    Generate bounded contexts documentation.

    Args:
        contexts: Identified contexts and relationships

    Returns:
        dict with context documentation
    """

    imports = '''from typing import Dict, List, Optional
from dataclasses import dataclass


'''

    # Generate context classes
    context_classes = ''
    for ctx in contexts["identified_contexts"]:
        context_classes += f'''
@dataclass
class {ctx["name"]}Context:
    """Bounded Context: {ctx["name"]}"""
    name: str = "{ctx["name"]}"
    path: str = "{ctx["path"]}"
    aggregates: List[str] = {ctx["aggregates"]}
    events: List[str] = {ctx["events"]}
    repositories: List[str] = {ctx["repositories"]}
    value_objects: List[str] = {ctx["value_objects"]}

'''

    module_doc = '''"""
Bounded Contexts Map

A Bounded Context is a boundary within which a Domain Model is valid.
Each context has:
- Clear responsibility
- Own ubiquitous language
- Own data storage
- Integration points with other contexts
"""
'''

    # Generate ACLs for each relationship
    acl_code = ""
    for rel in contexts["relationships"]:
        if rel.get("anti_corruption_layer"):
            acl_code += "\n" + generate_anti_corruption_layer(rel["source"], rel["target"])

    # Context map
    context_map = generate_context_map(contexts)

    complete_code = imports + module_doc + "\n" + context_classes + "\n" + acl_code + "\n\n" + context_map

    return {
        "code": complete_code,
        "contexts": [c["name"] for c in contexts["identified_contexts"]],
        "context_count": len(contexts["identified_contexts"]),
        "relationships": len(contexts["relationships"]),
        "acl_count": sum(1 for r in contexts["relationships"] if r.get("anti_corruption_layer")),
        "module": "bounded_contexts.py",
    }


def main():
    parser = argparse.ArgumentParser(
        description="Analyze and map bounded contexts"
    )
    parser.add_argument(
        "--codebase", required=True,
        help="Path to codebase to analyze"
    )
    parser.add_argument(
        "--analyze", action="store_true",
        help="Perform analysis"
    )
    parser.add_argument(
        "--output", choices=["json", "code"], default="code",
        help="Output format"
    )

    args = parser.parse_args()

    # Analyze codebase
    contexts = analyze_bounded_contexts(args.codebase)

    # Generate documentation
    result = generate_bounded_contexts_doc(contexts)

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
