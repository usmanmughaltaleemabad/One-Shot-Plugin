"""
Serializer Generator - Custom serializer generation

Generates:
- Field serializers for complex types
- Custom serializer methods
- Nested serializers
- Dynamic field inclusion
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class SerializerField:
    """Serializer field definition"""
    name: str
    field_type: str
    read_only: bool = False
    write_only: bool = False
    required: bool = True


class SerializerGenerator:
    """Generate custom serializers"""

    def __init__(self, framework: str, model_name: str):
        self.framework = framework
        self.model_name = model_name

    def generate_django_serializer(self, fields: List[SerializerField]) -> str:
        """Generate Django REST Framework serializer"""
        field_definitions = []

        for field in fields:
            field_class = self._get_field_class(field.field_type)
            params = []

            if field.read_only:
                params.append("read_only=True")
            if field.write_only:
                params.append("write_only=True")
            if not field.required:
                params.append("required=False")

            params_str = ", ".join(params) if params else ""
            if params_str:
                params_str = ", " + params_str

            field_definitions.append(f"    {field.name} = {field_class}({params_str})")

        return f"""
from rest_framework import serializers
from .models import {self.model_name}

class {self.model_name}Serializer(serializers.ModelSerializer):
    '''Serializer for {self.model_name}'''

{''.join(field_definitions)}

    class Meta:
        model = {self.model_name}
        fields = '__all__'

    def create(self, validated_data):
        '''Create instance'''
        return {self.model_name}.objects.create(**validated_data)

    def update(self, instance, validated_data):
        '''Update instance'''
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

    def to_representation(self, instance):
        '''Customize representation'''
        data = super().to_representation(instance)
        # Add computed fields
        data['display_name'] = str(instance)
        return data

class {self.model_name}ListSerializer(serializers.ListSerializer):
    '''List serializer for bulk operations'''

    def create(self, validated_data):
        return [{self.model_name}.objects.create(**item) for item in validated_data]

    def update(self, instances, validated_data):
        # Update multiple instances
        return instances
"""

    def generate_fastapi_serializer(self, fields: List[SerializerField]) -> str:
        """Generate Pydantic schema serializer"""
        field_definitions = []

        for field in fields:
            python_type = self._get_python_type(field.field_type)
            if not field.required:
                python_type = f"Optional[{python_type}]"

            field_definitions.append(f"    {field.name}: {python_type}")

        return f"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

class {self.model_name}Base(BaseModel):
    '''Base schema for {self.model_name}'''
{''.join(field_definitions)}

class {self.model_name}Create(BaseModel):
    '''Create schema for {self.model_name}'''
{''.join(field_definitions)}

class {self.model_name}Update(BaseModel):
    '''Update schema for {self.model_name}'''
{''.join([f.replace(':', f'Optional[', 1).replace('\n', '] = None\n', 1) for f in field_definitions if not f.strip().startswith('id')])}

class {self.model_name}Response(BaseModel):
    '''Response schema for {self.model_name}'''
    id: int
{''.join(field_definitions)}
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @validator('created_at', 'updated_at', pre=True)
    def parse_datetime(cls, v):
        if isinstance(v, datetime):
            return v
        return datetime.fromisoformat(v)

class {self.model_name}ListResponse(BaseModel):
    '''List response schema'''
    total: int
    items: List[{self.model_name}Response]
"""

    @staticmethod
    def _get_field_class(field_type: str) -> str:
        type_map = {
            "string": "serializers.CharField",
            "integer": "serializers.IntegerField",
            "boolean": "serializers.BooleanField",
            "datetime": "serializers.DateTimeField",
            "date": "serializers.DateField",
            "decimal": "serializers.DecimalField",
            "email": "serializers.EmailField",
            "url": "serializers.URLField",
            "json": "serializers.JSONField"
        }
        return type_map.get(field_type, "serializers.CharField")

    @staticmethod
    def _get_python_type(field_type: str) -> str:
        type_map = {
            "string": "str",
            "integer": "int",
            "boolean": "bool",
            "datetime": "datetime",
            "date": "date",
            "decimal": "Decimal",
            "email": "str",
            "url": "str",
            "json": "dict"
        }
        return type_map.get(field_type, "str")


def generate_serializers(
    framework: str,
    model_name: str,
    fields: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, str]:
    """
    Generate serializers.

    Args:
        framework: django or fastapi
        model_name: e.g., "User"
        fields: list of field definitions

    Returns: dict of {filename: serializer_code}
    """
    generator = SerializerGenerator(framework, model_name)

    field_objs = [
        SerializerField(
            name=f.get("name"),
            field_type=f.get("type", "string"),
            read_only=f.get("read_only", False),
            write_only=f.get("write_only", False),
            required=f.get("required", True)
        )
        for f in (fields or [])
    ]

    output = {}

    if framework == "django":
        output["serializers.py"] = generator.generate_django_serializer(field_objs)
    elif framework == "fastapi":
        output["schemas.py"] = generator.generate_fastapi_serializer(field_objs)

    return output
