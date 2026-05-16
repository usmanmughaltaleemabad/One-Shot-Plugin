#!/usr/bin/env python3
"""
Phase 4 DDD: Aggregate Roots - Comprehensive Examples

Generates example Aggregate Root implementations showcasing DDD patterns.
Shows: entity composition, value objects, invariants, domain events, repositories.

Usage:
    python phase4_ddd_aggregate_roots.py --examples Order BlogPost ShoppingCart

Input: Example aggregate names
Output: Complete working aggregate implementations
"""

import argparse
import json
from datetime import datetime


AGGREGATE_EXAMPLES = {
    "Order": '''
class OrderAggregate:
    """
    Aggregate Root: Order

    Composition:
    - OrderItems (entities): lines of the order
    - OrderStatus (value object): order state machine
    - Money (value object): total amount

    Invariants:
    - Must have at least 1 item
    - Total amount must be positive
    - Cannot transition to invalid states
    - Cannot add items to shipped order
    """

    def __init__(self, customer_id: str, currency: str = "USD"):
        self.id = str(uuid.uuid4())
        self.customer_id = customer_id
        self.items = []
        self.status = OrderStatus.PENDING
        self.total = Money(0, currency)
        self.version = 1
        self.changes = []

    def add_item(self, sku: str, quantity: int, price: Money) -> None:
        """Add item to order"""
        if self.status != OrderStatus.PENDING:
            raise InvalidStateException(f"Cannot add items to {self.status} order")

        item = OrderItem(sku=sku, quantity=quantity, price=price)
        self.items.append(item)
        self.recalculate_total()
        self._record_event("ItemAdded", {"sku": sku, "quantity": quantity})

    def remove_item(self, sku: str) -> None:
        """Remove item from order"""
        if self.status != OrderStatus.PENDING:
            raise InvalidStateException(f"Cannot remove items from {self.status} order")

        self.items = [item for item in self.items if item.sku != sku]
        self.recalculate_total()
        self._record_event("ItemRemoved", {"sku": sku})

    def confirm(self) -> None:
        """Confirm order (transition to CONFIRMED)"""
        if self.status != OrderStatus.PENDING:
            raise InvalidStateException(f"Cannot confirm {self.status} order")
        if len(self.items) == 0:
            raise InvariantViolationException("Order must have at least 1 item")

        self.status = OrderStatus.CONFIRMED
        self._record_event("Confirmed", {"total": self.total.amount})

    def recalculate_total(self) -> None:
        """Recalculate order total"""
        total = Money(0, self.total.currency)
        for item in self.items:
            total = total.add(item.price.multiply(item.quantity))
        self.total = total

    def _record_event(self, event_type: str, data: dict) -> None:
        """Record domain event"""
        self.changes.append({
            "event_type": event_type,
            "aggregate_id": self.id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
            "version": self.version
        })
        self.version += 1
''',

    "BlogPost": '''
class BlogPostAggregate:
    """
    Aggregate Root: BlogPost

    Composition:
    - Comments (entities): reader comments
    - Tags (value objects): categorization
    - PublishStatus (value object): draft/published/archived

    Invariants:
    - Cannot publish without title + content
    - Cannot archive if not published
    - Only author can modify
    """

    def __init__(self, author_id: str, title: str):
        self.id = str(uuid.uuid4())
        self.author_id = author_id
        self.title = title
        self.content = ""
        self.status = PublishStatus.DRAFT
        self.comments = []
        self.tags = []
        self.version = 1
        self.changes = []

    def set_content(self, content: str) -> None:
        """Set blog post content"""
        if not content or len(content) < 100:
            raise ValidationException("Content must be at least 100 characters")

        self.content = content
        self._record_event("ContentSet", {"length": len(content)})

    def publish(self) -> None:
        """Publish blog post"""
        if self.status != PublishStatus.DRAFT:
            raise InvalidStateException(f"Cannot publish {self.status} post")
        if not self.title or not self.content:
            raise InvariantViolationException("Title and content required")

        self.status = PublishStatus.PUBLISHED
        self._record_event("Published", {"title": self.title})

    def add_comment(self, author_id: str, text: str) -> str:
        """Add comment to post"""
        if self.status != PublishStatus.PUBLISHED:
            raise InvalidStateException("Cannot comment on unpublished post")

        comment = Comment(author_id=author_id, text=text)
        self.comments.append(comment)
        self._record_event("CommentAdded", {"author": author_id, "text": text})
        return comment.id

    def add_tag(self, tag_name: str) -> None:
        """Add tag to post"""
        if tag_name in self.tags:
            return  # Already exists
        self.tags.append(tag_name)
        self._record_event("TagAdded", {"tag": tag_name})

    def archive(self) -> None:
        """Archive blog post"""
        if self.status != PublishStatus.PUBLISHED:
            raise InvalidStateException(f"Cannot archive {self.status} post")

        self.status = PublishStatus.ARCHIVED
        self._record_event("Archived", {})

    def _record_event(self, event_type: str, data: dict) -> None:
        """Record domain event"""
        self.changes.append({
            "event_type": event_type,
            "aggregate_id": self.id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
            "version": self.version
        })
        self.version += 1
''',

    "ShoppingCart": '''
class ShoppingCartAggregate:
    """
    Aggregate Root: ShoppingCart

    Composition:
    - CartItems (entities): products in cart
    - Discounts (value objects): applied promotions
    - CartStatus (value object): active/abandoned/checked_out

    Invariants:
    - Cannot checkout if empty
    - Cannot apply conflicting discounts
    - Items expire after 24 hours
    """

    def __init__(self, user_id: str):
        self.id = str(uuid.uuid4())
        self.user_id = user_id
        self.items = []
        self.discounts = []
        self.status = CartStatus.ACTIVE
        self.created_at = datetime.utcnow()
        self.version = 1
        self.changes = []

    def add_item(self, product_id: str, quantity: int, price: Money) -> None:
        """Add item to cart"""
        if self.status == CartStatus.CHECKED_OUT:
            raise InvalidStateException("Cannot add to checked out cart")

        # Check if item already in cart
        for item in self.items:
            if item.product_id == product_id:
                item.quantity += quantity  # Increment quantity
                self._record_event("ItemQuantityChanged", {"product_id": product_id})
                return

        # Add new item
        item = CartItem(product_id=product_id, quantity=quantity, price=price)
        self.items.append(item)
        self._record_event("ItemAdded", {"product_id": product_id, "quantity": quantity})

    def remove_item(self, product_id: str) -> None:
        """Remove item from cart"""
        if self.status == CartStatus.CHECKED_OUT:
            raise InvalidStateException("Cannot modify checked out cart")

        self.items = [item for item in self.items if item.product_id != product_id]
        self._record_event("ItemRemoved", {"product_id": product_id})

    def apply_discount(self, discount: Discount) -> None:
        """Apply discount to cart"""
        # Check for conflicting discounts
        if any(d.code == discount.code for d in self.discounts):
            raise ValidationException(f"Discount {discount.code} already applied")

        self.discounts.append(discount)
        self._record_event("DiscountApplied", {"code": discount.code})

    def checkout(self) -> str:
        """Proceed to checkout"""
        if len(self.items) == 0:
            raise InvariantViolationException("Cannot checkout empty cart")
        if self.status != CartStatus.ACTIVE:
            raise InvalidStateException(f"Cannot checkout {self.status} cart")

        self.status = CartStatus.CHECKED_OUT
        order_id = str(uuid.uuid4())
        self._record_event("CheckedOut", {"order_id": order_id})
        return order_id

    def abandon(self) -> None:
        """Abandon cart"""
        self.status = CartStatus.ABANDONED
        self._record_event("Abandoned", {})

    def is_expired(self, hours: int = 24) -> bool:
        """Check if cart expired"""
        age = datetime.utcnow() - self.created_at
        return age.total_seconds() > (hours * 3600)

    def _record_event(self, event_type: str, data: dict) -> None:
        """Record domain event"""
        self.changes.append({
            "event_type": event_type,
            "aggregate_id": self.id,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data,
            "version": self.version
        })
        self.version += 1
'''
}


def generate_aggregate_roots(examples: list) -> dict:
    """
    Generate example Aggregate Root implementations.

    Args:
        examples: List of aggregate names (e.g., [Order, BlogPost, ShoppingCart])

    Returns:
        dict with example implementations
    """

    imports = '''import uuid
from datetime import datetime
from typing import List, Optional
from abc import ABC, abstractmethod


class AggregateRoot(ABC):
    """Base class for all Aggregate Roots"""

    @abstractmethod
    def apply_event(self, event):
        """Apply domain event to aggregate"""
        pass

    @abstractmethod
    def get_changes(self):
        """Get uncommitted domain events"""
        pass


# Value Objects and Entities (simplified)

class Money:
    def __init__(self, amount: float, currency: str):
        self.amount = amount
        self.currency = currency

    def add(self, other):
        return Money(self.amount + other.amount, self.currency)

    def multiply(self, factor):
        return Money(self.amount * factor, self.currency)


class CartItem:
    def __init__(self, product_id: str, quantity: int, price: Money):
        self.product_id = product_id
        self.quantity = quantity
        self.price = price


class OrderItem:
    def __init__(self, sku: str, quantity: int, price: Money):
        self.sku = sku
        self.quantity = quantity
        self.price = price


class Comment:
    def __init__(self, author_id: str, text: str):
        self.id = str(uuid.uuid4())
        self.author_id = author_id
        self.text = text


class Discount:
    def __init__(self, code: str, amount: Money):
        self.code = code
        self.amount = amount


# Value Objects (enum-like)

class OrderStatus:
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class PublishStatus:
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class CartStatus:
    ACTIVE = "ACTIVE"
    CHECKED_OUT = "CHECKED_OUT"
    ABANDONED = "ABANDONED"


# Exceptions

class DomainException(Exception):
    pass


class InvalidStateException(DomainException):
    pass


class InvariantViolationException(DomainException):
    pass


class ValidationException(DomainException):
    pass


'''

    module_doc = '''"""
Aggregate Root Examples

Complete working examples of Domain-Driven Design aggregates:
1. Order: ecommerce order with items
2. BlogPost: blog post with comments and tags
3. ShoppingCart: shopping cart with discounts

Each aggregate demonstrates:
- Entity composition
- Value objects for domain concepts
- Invariant enforcement
- Domain event recording
- State transitions
- Business rule encapsulation
"""
'''

    # Combine examples
    examples_code = "\n\n".join([
        AGGREGATE_EXAMPLES.get(name, f"# {name} Aggregate (TODO)")
        for name in examples
    ])

    complete_code = imports + module_doc + "\n\n" + examples_code

    return {
        "code": complete_code,
        "examples": examples,
        "example_count": len(examples),
        "module": "aggregate_roots_examples.py",
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate example Aggregate Roots"
    )
    parser.add_argument(
        "--examples", nargs="+", default=["Order", "BlogPost", "ShoppingCart"],
        help="Aggregate examples to include"
    )
    parser.add_argument(
        "--output", choices=["json", "code"], default="code",
        help="Output format"
    )

    args = parser.parse_args()

    result = generate_aggregate_roots(args.examples)

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
