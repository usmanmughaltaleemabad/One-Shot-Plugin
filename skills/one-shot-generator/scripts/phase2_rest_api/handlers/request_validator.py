"""
Request Validator - Generate request validation logic

Validates:
- Required fields
- Field types
- Field constraints (min/max, regex patterns)
- Nested objects
- Arrays
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass


@dataclass
class ValidationRule:
    """Validation rule for a field"""
    field: str
    type: str  # string, integer, boolean, array, object
    required: bool = True
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    enum: Optional[List[str]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    items_type: Optional[str] = None  # for arrays


class RequestValidatorGenerator:
    """Generate request validation code"""

    def __init__(self, framework: str, resource_name: str):
        self.framework = framework
        self.resource_name = resource_name

    def generate_django(self, rules: List[ValidationRule]) -> str:
        """Generate Django DRF serializer validation"""
        resource = self.resource_name.capitalize()

        fields_code = []
        for rule in rules:
            field_code = self._generate_django_field(rule)
            fields_code.append(field_code)

        validators_code = []
        for rule in rules:
            if rule.pattern or rule.enum or rule.min_length or rule.max_length:
                validator_code = self._generate_django_validator(rule)
                validators_code.append(validator_code)

        return f"""
from rest_framework import serializers

class {resource}Serializer(serializers.Serializer):
    {''.join(fields_code)}

    def validate(self, data):
        {''.join(validators_code) or 'pass'}
        return data
"""

    def generate_fastapi(self, rules: List[ValidationRule]) -> str:
        """Generate Pydantic schema validation"""
        resource = self.resource_name.capitalize()

        fields_code = []
        for rule in rules:
            field_code = self._generate_fastapi_field(rule)
            fields_code.append(field_code)

        return f"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List

class {resource}Schema(BaseModel):
    {''.join(fields_code)}

    class Config:
        from_attributes = True

class {resource}CreateSchema(BaseModel):
    {''.join(fields_code)}
"""

    def _generate_django_field(self, rule: ValidationRule) -> str:
        """Generate Django field definition"""
        field_type_map = {
            "string": "serializers.CharField",
            "integer": "serializers.IntegerField",
            "boolean": "serializers.BooleanField",
            "array": "serializers.ListField",
            "object": "serializers.JSONField"
        }

        field_class = field_type_map.get(rule.type, "serializers.CharField")
        kwargs = [f"required={rule.required}"]

        if rule.min_length:
            kwargs.append(f"min_length={rule.min_length}")
        if rule.max_length:
            kwargs.append(f"max_length={rule.max_length}")

        return f"    {rule.field} = {field_class}({', '.join(kwargs)})\n"

    def _generate_fastapi_field(self, rule: ValidationRule) -> str:
        """Generate Pydantic field definition"""
        type_map = {
            "string": "str",
            "integer": "int",
            "boolean": "bool",
            "array": "List[str]",
            "object": "dict"
        }

        python_type = type_map.get(rule.type, "str")
        if not rule.required:
            python_type = f"Optional[{python_type}] = None"

        kwargs = []
        if rule.min_length:
            kwargs.append(f"min_length={rule.min_length}")
        if rule.max_length:
            kwargs.append(f"max_length={rule.max_length}")

        field_args = f", {', '.join(kwargs)}" if kwargs else ""
        return f"    {rule.field}: {python_type} = Field(...{field_args})\n"

    def _generate_django_validator(self, rule: ValidationRule) -> str:
        """Generate Django field validator"""
        if rule.enum:
            return f"""
    def validate_{rule.field}(self, value):
        valid_values = {rule.enum}
        if value not in valid_values:
            raise serializers.ValidationError(f"Must be one of {{valid_values}}")
        return value
"""
        elif rule.pattern:
            return f"""
    def validate_{rule.field}(self, value):
        import re
        if not re.match(r'{rule.pattern}', value):
            raise serializers.ValidationError("Invalid format")
        return value
"""
        return ""


class InputSanitizer:
    """Sanitize and clean input data"""

    @staticmethod
    def generate_django_sanitization() -> str:
        """Generate Django input sanitization"""
        return """
from django.utils.html import escape
from django.template.defaultfilters import slugify

def sanitize_input(data: dict) -> dict:
    '''Sanitize user input to prevent XSS and injection attacks'''
    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            # Escape HTML characters
            value = escape(value)
            # Strip whitespace
            value = value.strip()
        elif isinstance(value, dict):
            value = sanitize_input(value)
        elif isinstance(value, list):
            value = [sanitize_input({'v': v}).get('v') if isinstance(v, dict) else (
                escape(v) if isinstance(v, str) else v
            ) for v in value]
        sanitized[key] = value
    return sanitized
"""

    @staticmethod
    def generate_fastapi_sanitization() -> str:
        """Generate FastAPI input sanitization"""
        return """
from html import escape
import re

def sanitize_string(s: str) -> str:
    '''Sanitize string input'''
    s = escape(s)  # Escape HTML
    s = s.strip()  # Remove whitespace
    return s

def sanitize_input(data: dict) -> dict:
    '''Sanitize user input'''
    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            value = sanitize_string(value)
        elif isinstance(value, dict):
            value = sanitize_input(value)
        elif isinstance(value, list):
            value = [sanitize_input({'v': v}).get('v') if isinstance(v, dict) else (
                sanitize_string(v) if isinstance(v, str) else v
            ) for v in value]
        sanitized[key] = value
    return sanitized
"""


def generate_request_validation(
    framework: str,
    resource_name: str,
    validation_rules: List[Dict[str, Any]]
) -> Dict[str, str]:
    """
    Generate request validation code.

    Args:
        framework: django or fastapi
        resource_name: e.g., "user"
        validation_rules: list of validation rule dicts

    Returns: dict of {filename: code_content}
    """
    generator = RequestValidatorGenerator(framework, resource_name)

    rules = [
        ValidationRule(
            field=rule.get("field"),
            type=rule.get("type", "string"),
            required=rule.get("required", True),
            min_length=rule.get("min_length"),
            max_length=rule.get("max_length"),
            pattern=rule.get("pattern"),
            enum=rule.get("enum"),
            min_value=rule.get("min_value"),
            max_value=rule.get("max_value")
        )
        for rule in validation_rules
    ]

    output = {}

    if framework == "django":
        output["validation.py"] = generator.generate_django(rules)
        output["sanitizer.py"] = InputSanitizer.generate_django_sanitization()
    elif framework == "fastapi":
        output["schemas.py"] = generator.generate_fastapi(rules)
        output["sanitizer.py"] = InputSanitizer.generate_fastapi_sanitization()

    return output
