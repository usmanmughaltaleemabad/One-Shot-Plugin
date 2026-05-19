#!/usr/bin/env python3
"""
Phase 4 DDD: Validation Rules Generator

Generates domain-level validation rules (not UI/API validation).
Validation encapsulates business rules: invariants, constraints, domain logic.

Usage:
    python phase4_ddd_validation_rules.py --aggregate Order --rules "total > 0" "status in [pending, completed]"

Input: Aggregate and validation rules
Output: Domain validation rule classes
"""

import argparse
import json
from typing import Any, Callable


def generate_validation_rule(rule_name: str, condition: str) -> str:
    """Generate a single validation rule."""

    rule_code = f'''
class {rule_name}ValidationRule:
    """Validation Rule: {rule_name}"""

    def __init__(self):
        self.name = "{rule_name}"
        self.description = "{condition}"

    def validate(self, obj: Any) -> bool:
        """
        Check if object satisfies this rule.

        Returns:
            True if valid, False otherwise
        """
        try:
            # TODO: Implement domain logic
            # Example: return obj.total > 0
            return True
        except Exception:
            return False

    def validate_or_raise(self, obj: Any) -> None:
        """
        Validate and raise exception on failure.

        Raises:
            ValidationException: If validation fails
        """
        if not self.validate(obj):
            raise ValidationException(f"{{self.name}} violation: {{self.description}}")

    def __repr__(self):
        return f"{rule_name}({{self.description}})"
'''

    return rule_code


def generate_validation_context() -> str:
    """Generate validation context/aggregator."""

    context_code = '''
class ValidationContext:
    """
    Aggregates all domain validation rules.

    Usage:
        context = ValidationContext()
        context.register(rule1)
        context.register(rule2)
        context.validate_all(aggregate)  # Raises on first failure
        context.validate_all_and_report(aggregate)  # Returns all failures
    """

    def __init__(self):
        self._rules = []

    def register(self, rule: "ValidationRule") -> None:
        """Register a validation rule"""
        self._rules.append(rule)

    def validate(self, obj: Any) -> bool:
        """Check all rules (short-circuit on first failure)"""
        for rule in self._rules:
            if not rule.validate(obj):
                return False
        return True

    def validate_all(self, obj: Any) -> None:
        """Validate all rules, raise on first failure"""
        for rule in self._rules:
            rule.validate_or_raise(obj)

    def validate_all_and_report(self, obj: Any) -> "ValidationReport":
        """Validate all rules, return detailed report"""
        report = ValidationReport()
        for rule in self._rules:
            try:
                rule.validate_or_raise(obj)
            except ValidationException as e:
                report.add_error(rule.name, str(e))
        return report

    def __repr__(self):
        return f"ValidationContext({len(self._rules)} rules)"


class ValidationReport:
    """Report of validation failures"""

    def __init__(self):
        self.errors = {}  # rule_name -> error_message

    def add_error(self, rule_name: str, message: str) -> None:
        """Record validation failure"""
        self.errors[rule_name] = message

    def is_valid(self) -> bool:
        """Check if validation passed"""
        return len(self.errors) == 0

    def to_dict(self) -> dict:
        """Serialize for API response"""
        return {
            "valid": self.is_valid(),
            "errors": self.errors,
            "error_count": len(self.errors)
        }

    def __repr__(self):
        if self.is_valid():
            return "ValidationReport(✓ valid)"
        return f"ValidationReport({len(self.errors)} errors)"
'''

    return context_code


def generate_validation_exceptions() -> str:
    """Generate validation exception classes."""

    exceptions = '''
class ValidationException(Exception):
    """Base class for validation exceptions"""
    pass


class InvariantViolation(ValidationException):
    """Aggregate invariant violated"""
    pass


class ConstraintViolation(ValidationException):
    """Domain constraint violated"""
    pass


class BusinessRuleViolation(ValidationException):
    """Business rule violated"""
    pass
'''

    return exceptions


def generate_validation_rules(aggregate_name: str, rules: list) -> dict:
    """
    Generate validation rule system for aggregate.

    Args:
        aggregate_name: Aggregate name (e.g., Order)
        rules: List of rule names/descriptions

    Returns:
        dict with validation rules and context
    """

    imports = '''from typing import Any, Dict, List
from abc import ABC, abstractmethod


'''

    module_doc = f'''"""
Domain Validation Rules for {{aggregate_name}}

Validation encapsulates domain knowledge about {{aggregate_name}} invariants.

Validation vs. Constraints:
- Invariants: must always be true ({{aggregate_name}} cannot exist without)
- Constraints: domain rules ({{aggregate_name}} cannot transition to state X from Y)
- External validation: API/UI input validation (separate from domain)

Rules enforce domain logic at aggregate boundary.
""".replace("{{aggregate_name}}", aggregate_name)

    exceptions = generate_validation_exceptions()

    rule_classes = "\n".join([
        generate_validation_rule(name.replace(" ", ""), name)
        for name in rules
    ])

    context = generate_validation_context()

    # Example usage
    example_usage = f'''
# Example Usage

# Create validation context for {{aggregate_name}}
validator = ValidationContext()
validator.register(TotalGreaterThanZeroValidationRule())
validator.register(StatusValidTransitionValidationRule())

# Validate aggregate
try:
    validator.validate_all(order)
    print("Order is valid")
except ValidationException as e:
    print(f"Order invalid: {{e}}")

# Get detailed report
report = validator.validate_all_and_report(order)
if not report.is_valid():
    for rule_name, error in report.errors.items():
        print(f"Rule {{rule_name}}: {{error}}")
'''.replace("{{aggregate_name}}", aggregate_name).replace("{{aggregate_name.lower()}}", aggregate_name.lower())

    complete_code = imports + module_doc + "\n" + exceptions + "\n" + rule_classes + "\n" + context + "\n" + example_usage

    return {
        "code": complete_code,
        "aggregate": aggregate_name,
        "rules": rules,
        "rule_count": len(rules),
        "module": f"{aggregate_name.lower()}_validation.py",
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate domain validation rules"
    )
    parser.add_argument(
        "--aggregate", required=True,
        help="Aggregate name (e.g., Order)"
    )
    parser.add_argument(
        "--rules", nargs="+", required=True,
        help='Validation rules (e.g., "total > 0" "status in [PENDING, COMPLETED]")'
    )
    parser.add_argument(
        "--output", choices=["json", "code"], default="code",
        help="Output format"
    )

    args = parser.parse_args()

    result = generate_validation_rules(args.aggregate, args.rules)

    if args.output == "json":
        metadata = {k: v for k, v in result.items() if k != "code"}
        print(json.dumps(metadata, indent=2))
    else:
        print(result["code"])


if __name__ == "__main__":
    main()
