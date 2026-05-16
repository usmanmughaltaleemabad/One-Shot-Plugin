#!/usr/bin/env python3
"""
Phase 4 DDD: Value Object Library Generator

Generates domain-specific Value Objects (immutable, equality-based, no identity).
Value Objects encapsulate domain concepts like Money, Status, Email, etc.

Usage:
    python phase4_ddd_value_object_library.py --domain ecommerce --concepts Money Price Quantity

Input: Domain and value object concepts
Output: Complete Value Object implementations with validation
"""

import argparse
import json
from typing import Any
from abc import ABC, abstractmethod


VALUE_OBJECT_TEMPLATES = {
    "Money": """
class Money:
    \"\"\"Money Value Object: amount + currency\"\"\"

    def __init__(self, amount: float, currency: str = "USD"):
        if amount < 0:
            raise ValueError(f"Money amount cannot be negative: {{amount}}")
        if not isinstance(currency, str) or len(currency) != 3:
            raise ValueError(f"Currency must be 3-letter code: {{currency}}")

        self._amount = round(amount, 2)
        self._currency = currency.upper()

    @property
    def amount(self) -> float:
        return self._amount

    @property
    def currency(self) -> str:
        return self._currency

    def add(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError(f"Cannot add different currencies: {{self.currency}} + {{other.currency}}")
        return Money(self.amount + other.amount, self.currency)

    def multiply(self, factor: float) -> "Money":
        return Money(self.amount * factor, self.currency)

    def __eq__(self, other):
        if not isinstance(other, Money):
            return False
        return self.amount == other.amount and self.currency == other.currency

    def __lt__(self, other):
        if self.currency != other.currency:
            raise ValueError(f"Cannot compare different currencies")
        return self.amount < other.amount

    def __le__(self, other):
        return self == other or self < other

    def __hash__(self):
        return hash((self.amount, self.currency))

    def __repr__(self):
        return f"Money({{self.amount}}, '{{self.currency}}')"
""",

    "Email": """
class Email:
    \"\"\"Email Value Object: validated email address\"\"\"

    def __init__(self, value: str):
        self._validate(value)
        self._value = value.lower()

    def _validate(self, email: str) -> None:
        if not isinstance(email, str) or not email:
            raise ValueError("Email must be non-empty string")
        if "@" not in email or len(email) < 5:
            raise ValueError(f"Invalid email format: {{email}}")

    @property
    def value(self) -> str:
        return self._value

    @property
    def domain(self) -> str:
        return self._value.split("@")[1]

    @property
    def local_part(self) -> str:
        return self._value.split("@")[0]

    def __eq__(self, other):
        if not isinstance(other, Email):
            return False
        return self._value == other._value

    def __hash__(self):
        return hash(self._value)

    def __repr__(self):
        return f"Email('{{self._value}}')"
""",

    "Status": """
class Status:
    \"\"\"Status Value Object: enumerated status with transitions\"\"\"

    VALID_STATUSES = {"DRAFT", "SUBMITTED", "APPROVED", "REJECTED", "ARCHIVED"}

    TRANSITIONS = {
        "DRAFT": {"SUBMITTED", "ARCHIVED"},
        "SUBMITTED": {"APPROVED", "REJECTED", "DRAFT"},
        "APPROVED": {"ARCHIVED"},
        "REJECTED": {"DRAFT"},
        "ARCHIVED": set()
    }

    def __init__(self, value: str):
        if value not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status: {{value}}. Must be one of {{self.VALID_STATUSES}}")
        self._value = value

    @property
    def value(self) -> str:
        return self._value

    def can_transition_to(self, new_status: str) -> bool:
        \"\"\"Check if transition is allowed\"\"\"
        return new_status in self.TRANSITIONS.get(self._value, set())

    def transition_to(self, new_status: str) -> "Status":
        \"\"\"Transition to new status (immutable operation)\"\"\"
        if not self.can_transition_to(new_status):
            raise ValueError(f"Cannot transition from {{self._value}} to {{new_status}}")
        return Status(new_status)

    def __eq__(self, other):
        if not isinstance(other, Status):
            return False
        return self._value == other._value

    def __hash__(self):
        return hash(self._value)

    def __repr__(self):
        return f"Status('{{self._value}}')"
""",

    "Quantity": """
class Quantity:
    \"\"\"Quantity Value Object: integer >= 0\"\"\"

    def __init__(self, value: int):
        if not isinstance(value, int) or value < 0:
            raise ValueError(f"Quantity must be non-negative integer: {{value}}")
        self._value = value

    @property
    def value(self) -> int:
        return self._value

    def add(self, other: "Quantity") -> "Quantity":
        return Quantity(self.value + other.value)

    def subtract(self, other: "Quantity") -> "Quantity":
        result = self.value - other.value
        if result < 0:
            raise ValueError(f"Quantity cannot be negative")
        return Quantity(result)

    def multiply(self, factor: int) -> "Quantity":
        return Quantity(self.value * factor)

    def __eq__(self, other):
        if not isinstance(other, Quantity):
            return False
        return self.value == other.value

    def __lt__(self, other):
        return self.value < other.value

    def __le__(self, other):
        return self.value <= other.value

    def __hash__(self):
        return hash(self.value)

    def __repr__(self):
        return f"Quantity({{self.value}})"
""",
}


def generate_value_objects(concepts: list, domain: str) -> dict:
    """
    Generate Value Object implementations for domain concepts.

    Args:
        concepts: List of value object names (e.g., [Money, Email, Status])
        domain: Domain name (e.g., ecommerce, content, finance)

    Returns:
        dict with generated code and metadata
    """

    code_sections = {}
    unknown_concepts = []

    for concept in concepts:
        if concept in VALUE_OBJECT_TEMPLATES:
            code_sections[concept] = VALUE_OBJECT_TEMPLATES[concept]
        else:
            unknown_concepts.append(concept)

    # Generate generic value object for unknown concepts
    for concept in unknown_concepts:
        code_sections[concept] = f"""
class {concept}:
    \"\"\"Value Object: {concept}\"\"\"

    def __init__(self, value: Any):
        self._validate(value)
        self._value = value

    def _validate(self, value: Any) -> None:
        \"\"\"Override to add domain-specific validation\"\"\"
        if value is None:
            raise ValueError(f"{concept} cannot be None")

    @property
    def value(self) -> Any:
        return self._value

    def __eq__(self, other):
        if not isinstance(other, {concept}):
            return False
        return self._value == other._value

    def __hash__(self):
        return hash(str(self._value))

    def __repr__(self):
        return f"{concept}({{self._value!r}})"
"""

    # Build module code
    module_code = '''"""
Value Objects for {{domain}} domain

Value Objects are:
- Immutable: cannot change after creation
- Equality-based: equality means same value, not same reference
- No identity: no ID, only the value matters
- Validated: enforces domain rules in constructor
"""

from typing import Any
from abc import ABC, abstractmethod


'''.replace("{{domain}}", domain)

    module_code += "\n\n".join(code_sections.values())

    # Add factory/registry
    module_code += f"""


class ValueObjectRegistry:
    \"\"\"Registry for value objects in {{domain}} domain\"\"\"

    _objects = {{
        {", ".join(f"'{concept}': {concept}" for concept in concepts)}
    }}

    @classmethod
    def create(cls, vo_type: str, value: Any):
        \"\"\"Factory method to create value objects\"\"\"
        if vo_type not in cls._objects:
            raise ValueError(f"Unknown value object: {{vo_type}}")
        return cls._objects[vo_type](value)

    @classmethod
    def list_objects(cls) -> list:
        \"\"\"List available value objects\"\"\"
        return list(cls._objects.keys())
""".replace("{{domain}}", domain)

    return {
        "code": module_code,
        "concepts": concepts,
        "domain": domain,
        "module": f"{domain}_value_objects.py",
        "value_object_count": len(concepts),
        "builtin_count": len([c for c in concepts if c in VALUE_OBJECT_TEMPLATES]),
        "generic_count": len([c for c in concepts if c not in VALUE_OBJECT_TEMPLATES]),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate Value Objects for domain"
    )
    parser.add_argument(
        "--domain", required=True,
        help="Domain name (e.g., ecommerce, content)"
    )
    parser.add_argument(
        "--concepts", nargs="+", required=True,
        help="Value object concepts (e.g., Money Email Status Quantity)"
    )
    parser.add_argument(
        "--output", choices=["json", "code"], default="code",
        help="Output format"
    )

    args = parser.parse_args()

    result = generate_value_objects(args.concepts, args.domain)

    if args.output == "json":
        metadata = {k: v for k, v in result.items() if k != "code"}
        print(json.dumps(metadata, indent=2))
    else:
        print(result["code"])
        print("\n# Metadata")
        print(json.dumps(
            {k: v for k, v in result.items() if k != "code"},
            indent=2
        ))


if __name__ == "__main__":
    main()
