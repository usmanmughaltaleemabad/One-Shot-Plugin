#!/usr/bin/env python3
"""
Phase 5 Data Validation: Schema Enforcement & Quality Checks

Data Validation: Ensure incoming data meets requirements.

Problem: Garbage in, garbage out
- Field "age" = -5 (invalid)
- Field "email" = "not-an-email" (invalid)
- Required field "name" is missing
- Data quality: 70% missing values

Validation (solution):
- Schema: define expected structure
- Type checking: age must be int
- Range checking: age must be 0-150
- Format checking: email must match pattern
- Constraint checking: no duplicates
"""

from typing import Dict, List, Optional, Any, Callable
import re


def generate_data_validation() -> str:
    """Generate data validation system."""

    validation = '''
class DataValidator:
    """
    Validate data against schema.

    Schema: {field → {type, required, constraints}}
    """

    def __init__(self):
        self._schemas = {}  # schema_name → schema_def
        self._validators = {}  # field_type → validation_fn
        self._errors = []  # Validation errors

    def define_schema(self, name: str, schema: Dict) -> None:
        """Define validation schema"""
        self._schemas[name] = {
            "name": name,
            "fields": schema,
            "created_at": __import__("datetime").datetime.utcnow().isoformat()
        }

    def register_validator(
        self,
        field_type: str,
        validator: Callable
    ) -> None:
        """Register custom validator"""
        self._validators[field_type] = validator

    def validate(self, data: Dict, schema_name: str) -> tuple:
        """Validate data against schema"""
        schema = self._schemas.get(schema_name)
        if not schema:
            return (False, ["Schema not found"])

        self._errors = []

        for field_name, field_def in schema["fields"].items():
            value = data.get(field_name)

            # Check required
            if field_def.get("required") and value is None:
                self._errors.append(f"Field '{field_name}' is required")
                continue

            if value is None:
                continue

            # Check type
            expected_type = field_def.get("type")
            if expected_type and not self._check_type(value, expected_type):
                self._errors.append(
                    f"Field '{field_name}': expected {expected_type}, got {type(value).__name__}"
                )
                continue

            # Check constraints
            for constraint_name, constraint_value in field_def.items():
                if constraint_name in ["type", "required"]:
                    continue

                if constraint_name == "min" and value < constraint_value:
                    self._errors.append(f"Field '{field_name}': must be >= {constraint_value}")

                elif constraint_name == "max" and value > constraint_value:
                    self._errors.append(f"Field '{field_name}': must be <= {constraint_value}")

                elif constraint_name == "pattern":
                    if not __import__("re").match(constraint_value, str(value)):
                        self._errors.append(f"Field '{field_name}': invalid format")

                elif constraint_name == "enum":
                    if value not in constraint_value:
                        self._errors.append(f"Field '{field_name}': must be one of {constraint_value}")

                elif constraint_name == "length":
                    if len(value) != constraint_value:
                        self._errors.append(f"Field '{field_name}': must be length {constraint_value}")

        return (len(self._errors) == 0, self._errors)

    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected type"""
        type_map = {
            "string": str,
            "int": int,
            "float": float,
            "bool": bool,
            "list": list,
            "dict": dict
        }

        expected = type_map.get(expected_type)
        return isinstance(value, expected) if expected else False

    def get_errors(self) -> List[str]:
        """Get validation errors"""
        return self._errors


class DataQualityChecker:
    """Check overall data quality."""

    def __init__(self):
        self._rules = []

    def add_rule(
        self,
        name: str,
        field: str,
        check: str  # "not_null", "unique", "positive"
    ) -> None:
        """Add data quality rule"""
        self._rules.append({
            "name": name,
            "field": field,
            "check": check
        })

    def check_quality(self, dataset: List[Dict]) -> Dict:
        """Check data quality across dataset"""
        results = {}

        for rule in self._rules:
            field = rule["field"]
            check = rule["check"]

            if check == "not_null":
                nulls = len([d for d in dataset if d.get(field) is None])
                results[rule["name"]] = {
                    "passed": nulls == 0,
                    "null_count": nulls,
                    "null_percentage": (nulls / len(dataset) * 100) if dataset else 0
                }

            elif check == "unique":
                values = [d.get(field) for d in dataset]
                unique_count = len(set(values))
                results[rule["name"]] = {
                    "passed": unique_count == len(values),
                    "duplicates": len(values) - unique_count
                }

            elif check == "positive":
                negatives = len([d for d in dataset if d.get(field, 0) < 0])
                results[rule["name"]] = {
                    "passed": negatives == 0,
                    "negative_count": negatives
                }

        return results
'''

    return validation


def generate_validation_system() -> dict:
    """Generate complete data validation system."""

    imports = '''from typing import Dict, List, Optional, Any, Callable
import re
from datetime import datetime


'''

    module_doc = '''"""
Phase 5 Data Validation: Schema Enforcement & Quality Checks

Validate data structure and quality (JSON schema pattern).

SCHEMA EXAMPLE:

{
  "name": {
    "type": "string",
    "required": true,
    "length": 50
  },
  "age": {
    "type": "int",
    "required": true,
    "min": 0,
    "max": 150
  },
  "email": {
    "type": "string",
    "required": true,
    "pattern": "^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$"
  },
  "role": {
    "type": "string",
    "required": false,
    "enum": ["admin", "user", "guest"]
  }
}

VALIDATION CHECKS:

Type checking:
- string: "alice"
- int: 25
- float: 3.14
- bool: true
- list: [1, 2, 3]
- dict: {key: value}

Range checking:
- min: age >= 0
- max: age <= 150

Format checking:
- pattern: email matches regex
- length: name length <= 50

Enum checking:
- role in [admin, user, guest]

Required checking:
- name must be present (not null)

EXAMPLE: User Registration

Input JSON:
{
  "name": "Alice",
  "age": 25,
  "email": "alice@example.com",
  "role": "user"
}

Validation:
- name "Alice": string ✓, length 5 ✓, required ✓
- age 25: int ✓, min 0 ✓, max 150 ✓, required ✓
- email valid: pattern ✓, required ✓
- role "user": enum [admin, user, guest] ✓, required ✗ (optional)

Result: PASS

Invalid input:
{
  "name": "Alice",
  "age": -5,
  "email": "invalid-email",
  "role": "superadmin"
}

Validation:
- age -5: min 0 ✗
- email invalid: pattern ✗
- role "superadmin": enum [admin, user, guest] ✗

Result: FAIL
Errors: [
  "age: must be >= 0",
  "email: invalid format",
  "role: must be one of [admin, user, guest]"
]

DATA QUALITY METRICS:

Completeness: % of non-null fields
- Dataset: 1000 rows
- nulls in "email": 50
- Completeness: 95%

Uniqueness: % of unique values (for ID fields)
- Dataset: 1000 rows
- Duplicates in "user_id": 0
- Uniqueness: 100%

Validity: % passing format checks
- Dataset: 1000 rows
- Invalid emails: 20
- Validity: 98%

Consistency: values match pattern
- Dataset: 1000 rows
- USD amounts with '$': 990/1000
- Consistency: 99%

EXAMPLE: Data Quality Report

Rule: "Emails must not be null"
- Result: 95% complete (950/1000 not null)
- Alert: if < 95%, block import

Rule: "User IDs must be unique"
- Result: 100% unique (0 duplicates)
- Alert: if duplicates found, investigate

Rule: "Age must be positive"
- Result: 99% valid (10 negative values)
- Alert: if > 1% invalid, review

COMMON PITFALLS:

❌ No validation: accept any input
   → User_id = -999999 (invalid)
   → email = "" (empty)
   → age = "twenty-five" (not a number)
   → Downstream systems crash
   → Solution: validate at boundary

❌ Validation too strict: reject valid data
   → Phone number format: only US?
   → Name length: only 50 chars max?
   → Solution: allow flexibility for edge cases

❌ Silent failure: validation fails, no error
   → User doesn't know why submission rejected
   → Solution: return clear error messages

✓ Good validation:
   - Clear error messages
   - Reusable schemas
   - Fast (fail early)
   - Logged for auditing
"""
'''

    validation = generate_data_validation()

    complete_code = imports + module_doc + "\n" + validation

    return {
        "code": complete_code,
        "pattern": "Data Validation",
        "module": "phase5_data_validation.py"
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate data validation")
    args = parser.parse_args()
    result = generate_validation_system()
    print(result["code"])


if __name__ == "__main__":
    main()
