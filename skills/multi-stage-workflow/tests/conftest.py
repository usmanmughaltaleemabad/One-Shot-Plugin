"""Shared fixtures for multi-stage-workflow tests."""

import json
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_project():
    """Create a temporary test project with sample entities."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)

        # Create sample entities
        models_dir = project_path / "models"
        models_dir.mkdir()

        # Cart model
        (models_dir / "cart.py").write_text("""
class Cart:
    def __init__(self, user_id, total_price=0.0):
        self.id = None
        self.user_id = user_id
        self.total_price = total_price
        self.items = []

    def add_item(self, item):
        self.items.append(item)

    def calculate_total(self):
        return sum(item.price for item in self.items)
""")

        # LineItem model
        (models_dir / "lineitem.py").write_text("""
class LineItem:
    def __init__(self, cart_id, product_id, quantity, price):
        self.id = None
        self.cart_id = cart_id
        self.product_id = product_id
        self.quantity = quantity
        self.price = price

    def subtotal(self):
        return self.quantity * self.price
""")

        # Discount model
        (models_dir / "discount.py").write_text("""
class Discount:
    def __init__(self, cart_id, code, percentage):
        self.id = None
        self.cart_id = cart_id
        self.code = code
        self.percentage = percentage

    def apply(self, amount):
        return amount * (1 - self.percentage / 100)
""")

        # Auth middleware
        auth_dir = project_path / "auth"
        auth_dir.mkdir()
        (auth_dir / "middleware.py").write_text("""
def auth_required(func):
    def wrapper(*args, **kwargs):
        user = get_current_user()
        if not user:
            raise PermissionError("User not authenticated")
        return func(*args, **kwargs)
    return wrapper

def get_current_user():
    return None
""")

        yield project_path


@pytest.fixture
def sample_search_result():
    """Sample Stage 1 (Search) output."""
    return {
        "stage": "search",
        "query": "cart patterns",
        "patterns_found": [
            {
                "entity": "Cart",
                "files": ["models/cart.py"],
                "lines": [1, 2, 10, 15],
                "snippet": "class Cart:\n    def __init__(self, user_id, total_price=0.0):",
            },
            {
                "entity": "LineItem",
                "files": ["models/lineitem.py"],
                "lines": [1, 2, 10],
                "snippet": "class LineItem:\n    def __init__(self, cart_id, product_id, quantity, price):",
            },
            {
                "entity": "Discount",
                "files": ["models/discount.py"],
                "lines": [1, 2, 5],
                "snippet": "class Discount:\n    def __init__(self, cart_id, code, percentage):",
            },
        ],
        "total_matches": 3,
    }


@pytest.fixture
def sample_analysis_result():
    """Sample Stage 2 (Analyze) output."""
    return {
        "stage": "analyze",
        "entities": [
            {
                "name": "Cart",
                "fields": ["id", "user_id", "total_price", "items"],
                "inferred_types": {
                    "id": "integer",
                    "user_id": "integer",
                    "total_price": "float",
                    "items": "list",
                },
                "relationships": [{"type": "has_many", "target": "LineItem"}],
            },
            {
                "name": "LineItem",
                "fields": ["id", "cart_id", "product_id", "quantity", "price"],
                "inferred_types": {
                    "id": "integer",
                    "cart_id": "integer",
                    "product_id": "integer",
                    "quantity": "integer",
                    "price": "float",
                },
                "relationships": [{"type": "belongs_to", "target": "Cart"}],
            },
            {
                "name": "Discount",
                "fields": ["id", "cart_id", "code", "percentage"],
                "inferred_types": {
                    "id": "integer",
                    "cart_id": "integer",
                    "code": "string",
                    "percentage": "float",
                },
                "relationships": [{"type": "belongs_to", "target": "Cart"}],
            },
        ],
        "relationships": [
            {
                "from": "Cart",
                "to": "LineItem",
                "type": "one_to_many",
                "foreign_key": "cart_id",
            },
            {
                "from": "Cart",
                "to": "Discount",
                "type": "one_to_many",
                "foreign_key": "cart_id",
            },
        ],
    }


@pytest.fixture
def sample_generation_result():
    """Sample Stage 3 (Generate) output."""
    return {
        "stage": "generate",
        "spec": {
            "name": "shopping_cart",
            "version": "1.0.0",
            "entities": [
                {
                    "name": "Cart",
                    "description": "Shopping cart aggregating line items",
                    "properties": [
                        {"name": "id", "type": "integer", "primary_key": True},
                        {"name": "user_id", "type": "integer", "foreign_key": True},
                        {
                            "name": "total_price",
                            "type": "float",
                            "nullable": False,
                            "default": 0.0,
                        },
                        {
                            "name": "created_at",
                            "type": "datetime",
                            "nullable": False,
                        },
                    ],
                },
                {
                    "name": "LineItem",
                    "description": "Individual item in a shopping cart",
                    "properties": [
                        {"name": "id", "type": "integer", "primary_key": True},
                        {"name": "cart_id", "type": "integer", "foreign_key": True},
                        {"name": "product_id", "type": "integer", "foreign_key": True},
                        {"name": "quantity", "type": "integer", "nullable": False},
                        {"name": "price", "type": "float", "nullable": False},
                    ],
                },
                {
                    "name": "Discount",
                    "description": "Discount applied to shopping cart",
                    "properties": [
                        {"name": "id", "type": "integer", "primary_key": True},
                        {"name": "cart_id", "type": "integer", "foreign_key": True},
                        {"name": "code", "type": "string", "nullable": False},
                        {"name": "percentage", "type": "float", "nullable": False},
                    ],
                },
            ],
        },
        "implementation_steps": [
            "1. Create Cart model with user_id and total_price",
            "2. Create LineItem model with cart_id FK",
            "3. Create Discount model with cart_id FK",
            "4. Add validation for total_price >= 0",
            "5. Add constraint that cart can have multiple line items and discounts",
        ],
        "cost_estimate": "$0.37",
        "effort_estimate": "4-6 hours",
    }


@pytest.fixture
def workflow_state(sample_search_result, sample_analysis_result, sample_generation_result):
    """Complete workflow state after all 3 stages."""
    return {
        "id": "mswf-2026-05-25T10:00:00",
        "task": "find cart patterns, analyze, design new cart feature",
        "project": "/tmp/test-project",
        "stages": {
            "search": sample_search_result,
            "analyze": sample_analysis_result,
            "generate": sample_generation_result,
        },
    }
