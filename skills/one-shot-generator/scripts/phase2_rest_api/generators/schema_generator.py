"""
Schema Generator - Database schema generation

Generates:
- SQLAlchemy ORM models
- Pydantic schemas
- TypeScript interfaces
- JSON Schema definitions
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class SchemaField:
    """Schema field definition"""
    name: str
    field_type: str
    nullable: bool = False
    unique: bool = False
    description: Optional[str] = None
    example: Optional[Any] = None


class SchemaGenerator:
    """Generate database schemas"""

    def __init__(self, framework: str, language: str):
        self.framework = framework
        self.language = language

    def generate_sqlalchemy_model(self, model_name: str, fields: List[SchemaField]) -> str:
        """Generate SQLAlchemy ORM model"""
        column_definitions = []

        for field in fields:
            col_type = self._get_sqlalchemy_type(field.field_type)
            params = [col_type]
            if not field.nullable:
                params.append("nullable=False")
            if field.unique:
                params.append("unique=True")
            if field.description:
                params.append(f"comment='{field.description}'")

            column_definitions.append(f"    {field.name} = Column({', '.join(params)})")

        return f"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class {model_name.capitalize()}(Base):
    __tablename__ = '{model_name.lower()}s'

    id = Column(Integer, primary_key=True)
{''.join(column_definitions)}

    def __repr__(self):
        return f"<{model_name.capitalize()}(id={{self.id}})>"
"""

    def generate_pydantic_schema(self, schema_name: str, fields: List[SchemaField]) -> str:
        """Generate Pydantic schema"""
        field_definitions = []

        for field in fields:
            python_type = self._get_python_type(field.field_type)
            if field.nullable:
                python_type = f"Optional[{python_type}]"
            default = "None" if field.nullable else "..."
            field_definitions.append(f"    {field.name}: {python_type} = {default}")

        return f"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class {schema_name.capitalize()}Schema(BaseModel):
{''.join(field_definitions)}

    class Config:
        from_attributes = True
        json_schema_extra = {{
            "example": {{
{self._generate_example_fields(fields)}
            }}
        }}
"""

    def generate_typescript_interface(self, interface_name: str, fields: List[SchemaField]) -> str:
        """Generate TypeScript interface"""
        field_definitions = []

        for field in fields:
            ts_type = self._get_typescript_type(field.field_type)
            optional = "?" if field.nullable else ""
            field_definitions.append(f"  {field.name}{optional}: {ts_type};")

        return f"""
export interface {interface_name} {{
{''.join(field_definitions)}
}}

export type {interface_name}Input = Omit<{interface_name}, 'id' | 'createdAt' | 'updatedAt'>;
"""

    def generate_json_schema(self, schema_name: str, fields: List[SchemaField]) -> Dict[str, Any]:
        """Generate JSON Schema definition"""
        properties = {}
        required = []

        for field in fields:
            schema = {{
                "type": self._get_json_schema_type(field.field_type),
                "description": field.description or f"The {field.name} field"
            }}

            if field.example is not None:
                schema["example"] = field.example

            properties[field.name] = schema

            if not field.nullable:
                required.append(field.name)

        return {{
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "title": schema_name,
            "properties": properties,
            "required": required,
            "additionalProperties": False
        }}

    @staticmethod
    def _get_sqlalchemy_type(field_type: str) -> str:
        type_map = {
            "string": "String(255)",
            "text": "String",
            "integer": "Integer",
            "boolean": "Boolean",
            "datetime": "DateTime",
            "date": "Date",
            "decimal": "Numeric(10, 2)",
            "json": "JSON"
        }
        return type_map.get(field_type, "String(255)")

    @staticmethod
    def _get_python_type(field_type: str) -> str:
        type_map = {
            "string": "str",
            "text": "str",
            "integer": "int",
            "boolean": "bool",
            "datetime": "datetime",
            "date": "date",
            "decimal": "Decimal",
            "json": "dict"
        }
        return type_map.get(field_type, "str")

    @staticmethod
    def _get_typescript_type(field_type: str) -> str:
        type_map = {
            "string": "string",
            "text": "string",
            "integer": "number",
            "boolean": "boolean",
            "datetime": "Date",
            "date": "Date",
            "decimal": "number",
            "json": "object"
        }
        return type_map.get(field_type, "string")

    @staticmethod
    def _get_json_schema_type(field_type: str) -> str:
        type_map = {
            "string": "string",
            "text": "string",
            "integer": "integer",
            "boolean": "boolean",
            "datetime": "string",
            "date": "string",
            "decimal": "number",
            "json": "object"
        }
        return type_map.get(field_type, "string")

    @staticmethod
    def _generate_example_fields(fields: List[SchemaField]) -> str:
        examples = []
        for field in fields:
            if field.example is not None:
                examples.append(f"                {field.name}: {repr(field.example)},")
            else:
                if field.field_type == "string":
                    examples.append(f"                {field.name}: 'example',")
                elif field.field_type == "integer":
                    examples.append(f"                {field.name}: 1,")
                elif field.field_type == "boolean":
                    examples.append(f"                {field.name}: true,")
        return "\n".join(examples)


def generate_schemas(
    framework: str,
    language: str,
    model_name: str,
    fields: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, str]:
    """
    Generate database schemas.

    Args:
        framework: django, fastapi, spring, go
        language: python, java, go, typescript
        model_name: e.g., "user"
        fields: list of field definitions

    Returns: dict of {filename: schema_content}
    """
    generator = SchemaGenerator(framework, language)

    field_objs = [
        SchemaField(
            name=f.get("name"),
            field_type=f.get("type", "string"),
            nullable=f.get("nullable", False),
            unique=f.get("unique", False),
            description=f.get("description"),
            example=f.get("example")
        )
        for f in (fields or [])
    ]

    output = {}

    if language == "python" or framework in ["django", "fastapi"]:
        output["models.py"] = generator.generate_sqlalchemy_model(model_name, field_objs)
        output["schemas.py"] = generator.generate_pydantic_schema(model_name, field_objs)
    elif language == "typescript":
        output["types.ts"] = generator.generate_typescript_interface(model_name, field_objs)
    elif language in ["java", "go"]:
        output["schema.json"] = str(generator.generate_json_schema(model_name, field_objs))

    return output
