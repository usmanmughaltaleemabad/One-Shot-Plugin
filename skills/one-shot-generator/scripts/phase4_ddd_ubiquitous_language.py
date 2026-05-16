#!/usr/bin/env python3
"""
Phase 4 DDD: Ubiquitous Language - Domain Dictionary Extractor

Extracts and documents the Ubiquitous Language (domain terminology) from a codebase.
The Ubiquitous Language is shared between developers and domain experts.

Usage:
    python phase4_ddd_ubiquitous_language.py --codebase /path/to/project --domain ecommerce

Input: Codebase path and domain name
Output: Domain dictionary with term definitions
"""

import argparse
import json
from typing import Dict, List


def extract_ubiquitous_language(domain: str) -> dict:
    """
    Extract ubiquitous language from domain.

    In a real implementation, this would parse code to find:
    - Class names (entities, value objects, aggregates)
    - Method names (behaviors, use cases)
    - Domain event names
    - Exception names
    - Repository names

    For now, return example domain language.
    """

    # Example domain language for ecommerce
    language = {
        "ecommerce": {
            "Aggregate Roots": {
                "Order": "Customer request to purchase products at specific price and time",
                "ShoppingCart": "Temporary collection of items before purchase",
                "Catalog": "Product listing with pricing and availability",
            },
            "Entities": {
                "OrderItem": "Single line of an order (product + quantity + price)",
                "Customer": "Person who places orders and receives shipments",
                "Payment": "Financial transaction for order settlement",
            },
            "Value Objects": {
                "Money": "Amount in specific currency (immutable)",
                "Address": "Physical location (street, city, country)",
                "OrderStatus": "Order state (Pending, Confirmed, Shipped, Delivered)",
                "SKU": "Stock Keeping Unit - unique product identifier",
            },
            "Domain Events": {
                "OrderCreated": "Customer placed order",
                "OrderConfirmed": "Order validated and confirmed",
                "OrderShipped": "Order left warehouse",
                "OrderDelivered": "Order received by customer",
                "PaymentProcessed": "Payment cleared successfully",
                "InventoryReserved": "Items reserved for order",
            },
            "Services": {
                "OrderService": "Orchestrates order creation and confirmation",
                "PaymentService": "Handles payment processing and settlement",
                "ShippingService": "Manages order shipment and tracking",
                "InventoryService": "Tracks product availability",
            },
            "Repositories": {
                "OrderRepository": "Persist/retrieve orders from storage",
                "CustomerRepository": "Persist/retrieve customers",
                "CatalogRepository": "Query product catalog",
            },
            "Policies": {
                "PaymentPolicy": "Rules for accepting/rejecting payments",
                "ShippingPolicy": "Rules for calculating shipping costs",
                "DiscountPolicy": "Rules for applying discounts",
            },
            "Use Cases": {
                "PlaceOrder": "Customer adds items to cart and purchases",
                "CancelOrder": "Customer or support cancels order",
                "TrackShipment": "Customer views order shipment status",
                "ProcessRefund": "Support initiates money back to customer",
            }
        }
    }

    return language.get(domain, {"domain": domain, "terms": {}})


def generate_domain_dictionary(domain: str) -> str:
    """Generate domain dictionary document."""

    language = extract_ubiquitous_language(domain)

    dict_doc = f'''
# Ubiquitous Language Dictionary — {{domain}}

Shared language between developers and domain experts.
Used in code, conversations, design discussions, and documentation.

---

## Aggregate Roots

Entities with lifecycle, identity, and responsibility for invariants.

{{aggregates_list}}

---

## Entities

Objects with identity, mutable, part of aggregate.

{{entities_list}}

---

## Value Objects

Immutable, equality-based, describe attributes.

{{values_list}}

---

## Domain Events

Business-significant state changes.

{{events_list}}

---

## Services

Stateless behaviors that don't belong to any entity.

{{services_list}}

---

## Repositories

Collection-like interfaces for accessing aggregates.

{{repositories_list}}

---

## Policies

Business rules and constraints.

{{policies_list}}

---

## Use Cases

How customers/actors interact with system.

{{use_cases_list}}

---

## Key Relationships

```
Customer
  ├── Places → Order (Aggregate Root)
  │     ├── Contains → OrderItem (Entity)
  │     ├── Has → OrderStatus (Value Object)
  │     └── Generates → OrderCreated (Domain Event)
  │
  ├── Pays with → Payment (Entity)
  └── Ships to → Address (Value Object)
```

---

## Anti-Corruption Glossary

Terms from external systems NOT used in domain code:

- "Customer Account" (external) ← Translation → "Customer" (domain)
- "Purchase Transaction" (external) ← Translation → "Order" (domain)
- "Fulfillment" (external) ← Translation → "Shipment" (domain)

When integrating with external systems, translate at bounded context boundaries.
Never let external terminology leak into domain code.

---

## Principles

1. **Unified Language**: Same terms used by developers AND domain experts
2. **Code Reflects Domain**: Class names, method names match ubiquitous language
3. **Evolve Together**: When domain understanding changes, code and language evolve together
4. **Document Decisions**: When terms are ambiguous, document the decision
5. **No Translation**: Avoid mental translation (developers thinking "entity" when code says "model")
'''

    # Build dictionary sections
    aggregates_list = ""
    if "Aggregate Roots" in language:
        for agg, desc in language["Aggregate Roots"].items():
            aggregates_list += f"- **{agg}**: {desc}\n"

    entities_list = ""
    if "Entities" in language:
        for ent, desc in language["Entities"].items():
            entities_list += f"- **{ent}**: {desc}\n"

    values_list = ""
    if "Value Objects" in language:
        for val, desc in language["Value Objects"].items():
            values_list += f"- **{val}**: {desc}\n"

    events_list = ""
    if "Domain Events" in language:
        for evt, desc in language["Domain Events"].items():
            events_list += f"- **{evt}**: {desc}\n"

    services_list = ""
    if "Services" in language:
        for svc, desc in language["Services"].items():
            services_list += f"- **{svc}**: {desc}\n"

    repositories_list = ""
    if "Repositories" in language:
        for repo, desc in language["Repositories"].items():
            repositories_list += f"- **{repo}**: {desc}\n"

    policies_list = ""
    if "Policies" in language:
        for pol, desc in language["Policies"].items():
            policies_list += f"- **{pol}**: {desc}\n"

    use_cases_list = ""
    if "Use Cases" in language:
        for uc, desc in language["Use Cases"].items():
            use_cases_list += f"- **{uc}**: {desc}\n"

    return dict_doc.replace("{{domain}}", domain).replace("{{aggregates_list}}", aggregates_list.strip()).replace("{{entities_list}}", entities_list.strip()).replace("{{values_list}}", values_list.strip()).replace("{{events_list}}", events_list.strip()).replace("{{services_list}}", services_list.strip()).replace("{{repositories_list}}", repositories_list.strip()).replace("{{policies_list}}", policies_list.strip()).replace("{{use_cases_list}}", use_cases_list.strip())


def generate_ubiquitous_language(domain: str) -> dict:
    """
    Generate ubiquitous language documentation.

    Args:
        domain: Domain name (e.g., ecommerce)

    Returns:
        dict with language definitions and documentation
    """

    language = extract_ubiquitous_language(domain)
    dictionary = generate_domain_dictionary(domain)

    # Count terms
    term_count = 0
    for category in language.values():
        if isinstance(category, dict):
            for subcategory in category.values():
                if isinstance(subcategory, dict):
                    term_count += len(subcategory)

    return {
        "domain": domain,
        "language": language,
        "dictionary": dictionary,
        "term_count": term_count,
        "documentation": "Ubiquitous Language Dictionary (see output for details)",
    }


def main():
    parser = argparse.ArgumentParser(
        description="Extract and document ubiquitous language"
    )
    parser.add_argument(
        "--codebase", default=".",
        help="Path to codebase (optional)"
    )
    parser.add_argument(
        "--domain", required=True,
        help="Domain name (e.g., ecommerce, content, payments)"
    )
    parser.add_argument(
        "--output", choices=["json", "doc"], default="doc",
        help="Output format"
    )

    args = parser.parse_args()

    result = generate_ubiquitous_language(args.domain)

    if args.output == "json":
        print(json.dumps(result["language"], indent=2))
    else:
        print(result["dictionary"])
        print("\n# Language Summary")
        print(json.dumps({k: v for k, v in result.items() if k not in ["language", "dictionary"]}, indent=2))


if __name__ == "__main__":
    main()
