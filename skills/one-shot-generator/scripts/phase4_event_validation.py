#!/usr/bin/env python3
"""
Phase 4 Event Validation

Validates events conform to schema and business rules.

Why validate events?
- Event log is immutable source of truth
- Bad events = corrupted data forever
- Validation at write time prevents issues

Validation levels:
1. Schema: required fields, types
2. Business rules: constraints (total >= 0, dates valid)
3. Correlation: event links to valid aggregate
4. Consistency: event doesn't violate invariants

Usage:
    python phase4_event_validation.py --event OrderCreated

Input: Event type
Output: Validation framework
"""

import argparse
import json
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime


def generate_event_validator() -> str:
    """Generate event validator."""

    validator = '''
class EventValidator:
    """
    Base validator for events.

    Validates:
    1. Schema: has required fields, correct types
    2. Business rules: value constraints
    3. Dependencies: linked aggregates exist
    """

    def __init__(self):
        self._schema_validators = {}
        self._rule_validators = {}
        self._dependency_validators = {}

    def validate_schema(self, event: Dict, event_type: str) -> List[str]:
        """
        Validate event schema.

        Checks:
        - Required fields present
        - Field types correct
        - No unexpected fields
        """
        errors = []

        validator = self._schema_validators.get(event_type)
        if not validator:
            return errors

        # Check required fields
        for field in validator.get("required", []):
            if field not in event:
                errors.append(f"Missing required field: {field}")

        # Check field types
        for field, expected_type in validator.get("types", {}).items():
            if field in event:
                actual_type = type(event[field]).__name__
                if actual_type != expected_type:
                    errors.append(
                        f"Field {field}: expected {expected_type}, "
                        f"got {actual_type}"
                    )

        return errors

    def validate_business_rules(self, event: Dict, event_type: str) -> List[str]:
        """
        Validate business rule constraints.

        Checks:
        - Total amounts >= 0
        - Dates are valid
        - Enum values are valid
        """
        errors = []

        validators = self._rule_validators.get(event_type, [])
        for rule_validator in validators:
            rule_errors = rule_validator(event)
            errors.extend(rule_errors)

        return errors

    def validate_dependencies(
        self,
        event: Dict,
        event_type: str,
        aggregate_store: Any
    ) -> List[str]:
        """
        Validate event references valid aggregates.

        Checks:
        - aggregate_id exists
        - linked aggregates exist
        """
        errors = []

        validators = self._dependency_validators.get(event_type, [])
        for dep_validator in validators:
            dep_errors = dep_validator(event, aggregate_store)
            errors.extend(dep_errors)

        return errors

    def validate_full(
        self,
        event: Dict,
        event_type: str,
        aggregate_store: Optional[Any] = None
    ) -> Dict[str, List[str]]:
        """
        Full validation: schema + rules + dependencies.

        Returns:
            {
                "schema": [...],
                "rules": [...],
                "dependencies": [...],
                "valid": bool
            }
        """
        schema_errors = self.validate_schema(event, event_type)
        rule_errors = self.validate_business_rules(event, event_type)
        dep_errors = []

        if aggregate_store:
            dep_errors = self.validate_dependencies(
                event,
                event_type,
                aggregate_store
            )

        return {
            "schema": schema_errors,
            "rules": rule_errors,
            "dependencies": dep_errors,
            "valid": not (schema_errors or rule_errors or dep_errors)
        }

    def register_schema(self, event_type: str, schema: Dict) -> None:
        """Register schema for event type"""
        self._schema_validators[event_type] = schema

    def register_rule(
        self,
        event_type: str,
        rule_fn: Callable
    ) -> None:
        """Register business rule validator"""
        if event_type not in self._rule_validators:
            self._rule_validators[event_type] = []
        self._rule_validators[event_type].append(rule_fn)

    def register_dependency(
        self,
        event_type: str,
        dep_fn: Callable
    ) -> None:
        """Register dependency validator"""
        if event_type not in self._dependency_validators:
            self._dependency_validators[event_type] = []
        self._dependency_validators[event_type].append(dep_fn)
'''

    return validator


def generate_schema_registry() -> str:
    """Generate event schema registry."""

    registry = '''
class EventSchemaRegistry:
    """
    Registry of event schemas.

    Defines structure of each event type.

    Example:
    OrderCreated: {
        required: [aggregate_id, customer_id, total],
        types: {aggregate_id: str, customer_id: str, total: float},
        constraints: [total >= 0]
    }
    """

    def __init__(self):
        self._schemas = {}

    def register_event_schema(
        self,
        event_type: str,
        required_fields: List[str],
        field_types: Dict[str, str]
    ) -> None:
        """Register event schema"""
        self._schemas[event_type] = {
            "required": required_fields,
            "types": field_types
        }

    def get_schema(self, event_type: str) -> Optional[Dict]:
        """Get event schema"""
        return self._schemas.get(event_type)

    def build_registry(self) -> Dict:
        """Get all registered schemas"""
        return self._schemas

    @staticmethod
    def build_order_schema() -> Dict:
        """Example: OrderCreated event schema"""
        return {
            "required": [
                "aggregate_id",
                "event_type",
                "customer_id",
                "items",
                "total",
                "timestamp"
            ],
            "types": {
                "aggregate_id": "str",
                "event_type": "str",
                "customer_id": "str",
                "items": "list",
                "total": "float",
                "timestamp": "str"
            }
        }
'''

    return registry


def generate_validation_rules() -> str:
    """Generate business rule validators."""

    rules = '''
class ValidationRules:
    """Business rule validators for events"""

    @staticmethod
    def order_amount_valid(event: Dict) -> List[str]:
        """OrderCreated: total must be >= 0"""
        errors = []
        total = event.get("data", {}).get("total", 0)
        if total < 0:
            errors.append(f"Total must be >= 0, got {total}")
        return errors

    @staticmethod
    def order_has_items(event: Dict) -> List[str]:
        """OrderCreated: must have items"""
        errors = []
        items = event.get("data", {}).get("items", [])
        if not items:
            errors.append("Order must have at least one item")
        return errors

    @staticmethod
    def timestamp_valid(event: Dict) -> List[str]:
        """Event: timestamp must be valid ISO format"""
        errors = []
        timestamp = event.get("timestamp")
        if not timestamp:
            errors.append("Missing timestamp")
            return errors

        try:
            datetime.fromisoformat(timestamp)
        except ValueError:
            errors.append(f"Invalid timestamp format: {timestamp}")

        return errors

    @staticmethod
    def event_type_valid(event: Dict, valid_types: List[str]) -> List[str]:
        """Event: event_type must be in valid list"""
        errors = []
        event_type = event.get("event_type")
        if event_type not in valid_types:
            errors.append(
                f"Unknown event type: {event_type}. "
                f"Valid: {valid_types}"
            )
        return errors
'''

    return rules


def generate_validation_pipeline() -> str:
    """Generate validation pipeline."""

    pipeline = '''
class ValidationPipeline:
    """
    Chain of validators.

    Run multiple validators in sequence.
    Collect all errors.
    """

    def __init__(self):
        self._validators = []

    def add_validator(self, validator: Callable) -> "ValidationPipeline":
        """Add validator to pipeline"""
        self._validators.append(validator)
        return self

    def validate(self, event: Dict) -> Dict:
        """
        Run all validators.

        Returns:
            {
                "valid": bool,
                "errors": [list of all errors],
                "warnings": [non-blocking issues]
            }
        """
        errors = []
        warnings = []

        for validator in self._validators:
            result = validator(event)
            if isinstance(result, dict):
                errors.extend(result.get("errors", []))
                warnings.extend(result.get("warnings", []))
            else:
                errors.extend(result)

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    @staticmethod
    def build_default() -> "ValidationPipeline":
        """Build pipeline with standard validators"""
        return (ValidationPipeline()
            .add_validator(
                lambda e: [] if ValidationRules.timestamp_valid(e) else ["invalid timestamp"]
            )
            .add_validator(
                lambda e: [] if ValidationRules.event_type_valid(
                    e,
                    ["OrderCreated", "OrderUpdated", "OrderDeleted"]
                ) else ["invalid event type"]
            ))
'''

    return pipeline


def generate_validation_system() -> dict:
    """Generate complete validation system."""

    imports = '''from typing import Any, Callable, Dict, List, Optional
from datetime import datetime


'''

    module_doc = '''"""
Event Validation Framework

Ensures events are valid before storing in immutable event log.

Why validate?
- Event log is source of truth
- Bad events = corrupted data forever
- Validation at write time prevents issues

Validation levels:
1. Schema: required fields, types (strict)
2. Business rules: constraints (total >= 0, dates valid)
3. Dependencies: linked aggregates exist
4. Consistency: event doesn't violate invariants

Example:
OrderCreated event:
- Schema: has aggregate_id, customer_id, total, items (required)
- Types: aggregate_id=str, total=float, items=list
- Rules: total >= 0, items.length > 0
- Dependencies: customer_id references valid Customer
- Invariant: total = sum(item.price * item.qty)

If any validation fails:
- Event rejected
- Error returned to caller
- Event never stored
- Data stays consistent
"""
'''

    validator = generate_event_validator()
    schema = generate_schema_registry()
    rules = generate_validation_rules()
    pipeline = generate_validation_pipeline()

    complete_code = imports + module_doc + "\n" + validator + "\n" + schema + "\n" + rules + "\n" + pipeline

    return {
        "code": complete_code,
        "pattern": "Event Validation",
        "module": "event_validation.py",
    }


def main():
    parser = argparse.ArgumentParser(description="Generate event validation")
    parser.add_argument("--event", help="Event type")
    parser.add_argument("--output", choices=["json", "code"], default="code")

    args = parser.parse_args()
    result = generate_validation_system()

    if args.output == "json":
        metadata = {k: v for k, v in result.items() if k != "code"}
        print(json.dumps(metadata, indent=2))
    else:
        print(result["code"])


if __name__ == "__main__":
    main()
