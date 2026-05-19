#!/usr/bin/env python3
"""
Phase 4 DDD: Specification Pattern Generator

Generates Specification pattern for composable business rules and queries.
Specifications encapsulate domain knowledge about what makes an object valid/interesting.

Usage:
    python phase4_ddd_specification_pattern.py --aggregate Order --specs IsPaidOrder IsOverdue CanBeCancelled

Input: Aggregate and specification names
Output: Reusable, composable specification classes
"""

import argparse
import json
from abc import ABC, abstractmethod


def generate_specification(spec_name: str, aggregate_name: str) -> str:
    """Generate individual specification class."""

    spec_code = f'''
class {spec_name}Specification:
    """Specification: {spec_name}"""

    def is_satisfied_by(self, {aggregate_name.lower()}) -> bool:
        \"\"\"
        Check if {{aggregate_name}} satisfies this specification.

        Returns:
            True if {{aggregate_name}} matches the business rule, False otherwise
        \"\"\"
        raise NotImplementedError(f"Implement for {{type(self).__name__}}")

    def and_spec(self, other: "Specification") -> "CompositeSpecification":
        """Combine with AND operator"""
        return CompositeSpecification(self, other, "AND")

    def or_spec(self, other: "Specification") -> "CompositeSpecification":
        """Combine with OR operator"""
        return CompositeSpecification(self, other, "OR")

    def not_spec(self) -> "NotSpecification":
        """Negate specification"""
        return NotSpecification(self)

    def __and__(self, other):
        return self.and_spec(other)

    def __or__(self, other):
        return self.or_spec(other)

    def __invert__(self):
        return self.not_spec()
'''

    return spec_code.replace("{{aggregate_name}}", aggregate_name).replace("{{aggregate_name.lower()}}", aggregate_name.lower())


def generate_composite_specs() -> str:
    """Generate composite specification classes."""

    composite_code = '''
class CompositeSpecification:
    """Combines two specifications with logical operator"""

    def __init__(self, left: "Specification", right: "Specification", operator: str):
        self.left = left
        self.right = right
        self.operator = operator

    def is_satisfied_by(self, obj) -> bool:
        if self.operator == "AND":
            return self.left.is_satisfied_by(obj) and self.right.is_satisfied_by(obj)
        elif self.operator == "OR":
            return self.left.is_satisfied_by(obj) or self.right.is_satisfied_by(obj)
        raise ValueError(f"Unknown operator: {self.operator}")

    def and_spec(self, other: "Specification") -> "CompositeSpecification":
        return CompositeSpecification(self, other, "AND")

    def or_spec(self, other: "Specification") -> "CompositeSpecification":
        return CompositeSpecification(self, other, "OR")

    def __repr__(self):
        return f"({self.left!r} {self.operator} {self.right!r})"


class NotSpecification:
    """Negates a specification"""

    def __init__(self, spec: "Specification"):
        self.spec = spec

    def is_satisfied_by(self, obj) -> bool:
        return not self.spec.is_satisfied_by(obj)

    def __repr__(self):
        return f"NOT({self.spec!r})"
'''

    return composite_code


def generate_example_implementations(aggregate_name: str) -> str:
    """Generate example specification implementations."""

    examples = f'''
# Example Implementations for {{aggregate_name}}

class IsPaidSpecification(Specification):
    """{{aggregate_name}} is paid in full"""

    def is_satisfied_by(self, {{aggregate_name.lower()}}) -> bool:
        return {{aggregate_name.lower()}}.status == "PAID"


class IsOverdueSpecification(Specification):
    """{{aggregate_name}} is overdue"""

    def is_satisfied_by(self, {{aggregate_name.lower()}}) -> bool:
        from datetime import datetime, timedelta
        due_date = {{aggregate_name.lower()}}.due_date
        return due_date < datetime.utcnow()


class CanBeCancelledSpecification(Specification):
    """{{aggregate_name}} can be cancelled (not shipped, not paid)"""

    def is_satisfied_by(self, {{aggregate_name.lower()}}) -> bool:
        valid_statuses = {{"PENDING", "CREATED"}}
        return {{aggregate_name.lower()}}.status in valid_statuses


class HasHighValueSpecification(Specification):
    """{{aggregate_name}} value exceeds threshold"""

    def __init__(self, threshold: float = 1000.0):
        self.threshold = threshold

    def is_satisfied_by(self, {{aggregate_name.lower()}}) -> bool:
        return {{aggregate_name.lower()}}.total_amount >= self.threshold


# Usage Examples:

# Single specification
is_paid = IsPaidSpecification()
if is_paid.is_satisfied_by(order):
    # Process paid order
    pass

# Composite specification (AND)
is_paid_and_overdue = (
    IsPaidSpecification() &
    IsOverdueSpecification()
)
overdue_paid_orders = [o for o in orders if is_paid_and_overdue.is_satisfied_by(o)]

# Composite specification (OR)
can_process = (
    IsPaidSpecification() |
    HasHighValueSpecification(5000)
)
processable = [o for o in orders if can_process.is_satisfied_by(o)]

# Negation
not_paid = ~IsPaidSpecification()
unpaid_orders = [o for o in orders if not_paid.is_satisfied_by(o)]

# In Repository.find_by_spec()
class OrderRepository:
    def find_all_overdue(self):
        return self.find_by_spec(IsOverdueSpecification())

    def find_all_urgent(self):
        return self.find_by_spec(
            IsOverdueSpecification() & ~IsPaidSpecification()
        )
'''.replace("{{aggregate_name}}", aggregate_name).replace("{{aggregate_name.lower()}}", aggregate_name.lower())

    return examples


def generate_specifications(aggregate_name: str, spec_names: list) -> dict:
    """
    Generate Specification pattern implementations.

    Args:
        aggregate_name: Aggregate name (e.g., Order)
        spec_names: Specification names (e.g., [IsPaid, IsOverdue, CanBeCancelled])

    Returns:
        dict with specification classes
    """

    imports = '''from abc import ABC, abstractmethod
from typing import Any, Optional


class Specification(ABC):
    """Base Specification abstract class"""

    @abstractmethod
    def is_satisfied_by(self, obj: Any) -> bool:
        """Check if object satisfies this specification"""
        raise NotImplementedError()

    def and_spec(self, other: "Specification") -> "CompositeSpecification":
        return CompositeSpecification(self, other, "AND")

    def or_spec(self, other: "Specification") -> "CompositeSpecification":
        return CompositeSpecification(self, other, "OR")

    def not_spec(self) -> "NotSpecification":
        return NotSpecification(self)

    def __and__(self, other):
        return self.and_spec(other)

    def __or__(self, other):
        return self.or_spec(other)

    def __invert__(self):
        return self.not_spec()


'''

    module_doc = f'''"""
Specification Pattern for {{aggregate_name}}

Specifications are reusable, composable business rules.

Benefits:
- Encapsulate domain logic
- Reusable across Repository, Services, Aggregates
- Composable: AND, OR, NOT combinations
- Testable in isolation
- Self-documenting

Specifications:
{{specs_list}}
""".replace("{{aggregate_name}}", aggregate_name).replace("{{specs_list}}", "\n".join([f"- {name}" for name in spec_names]))

    spec_classes = "\n".join([
        generate_specification(name, aggregate_name)
        for name in spec_names
    ])

    composite = generate_composite_specs()
    examples = generate_example_implementations(aggregate_name)

    complete_code = imports + module_doc + "\n" + spec_classes + "\n" + composite + "\n" + examples

    return {
        "code": complete_code,
        "aggregate": aggregate_name,
        "specifications": spec_names,
        "spec_count": len(spec_names),
        "module": f"{aggregate_name.lower()}_specifications.py",
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate Specification pattern"
    )
    parser.add_argument(
        "--aggregate", required=True,
        help="Aggregate name (e.g., Order)"
    )
    parser.add_argument(
        "--specs", nargs="+", required=True,
        help="Specification names (e.g., IsPaid IsOverdue CanBeCancelled)"
    )
    parser.add_argument(
        "--output", choices=["json", "code"], default="code",
        help="Output format"
    )

    args = parser.parse_args()

    result = generate_specifications(args.aggregate, args.specs)

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
