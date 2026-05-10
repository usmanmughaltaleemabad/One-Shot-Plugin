"""
Relationship Handler - Database relationship generation

Generates:
- One-to-many relationships
- Many-to-many relationships
- Foreign key handling
- Nested serialization
- Reverse relationships
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class RelationType(Enum):
    ONE_TO_MANY = "one_to_many"
    MANY_TO_ONE = "many_to_one"
    MANY_TO_MANY = "many_to_many"
    ONE_TO_ONE = "one_to_one"


@dataclass
class Relationship:
    """Relationship definition"""
    name: str
    relation_type: RelationType
    related_model: str
    back_populates: Optional[str] = None
    cascade_delete: bool = False
    nullable: bool = True


class RelationshipGenerator:
    """Generate relationship code"""

    def __init__(self, framework: str, resource_name: str):
        self.framework = framework
        self.resource_name = resource_name

    def generate_django(self, relationships: List[Relationship]) -> str:
        """Generate Django model relationships"""
        relationships_code = []

        for rel in relationships:
            if rel.relation_type == RelationType.ONE_TO_MANY:
                code = f"""    {rel.name} = models.OneToOneField(
        '{rel.related_model}',
        on_delete=models.CASCADE if {rel.cascade_delete} else models.SET_NULL,
        null={rel.nullable},
        blank=True
    )"""
                relationships_code.append(code)

            elif rel.relation_type == RelationType.MANY_TO_ONE:
                code = f"""    {rel.name} = models.ForeignKey(
        '{rel.related_model}',
        on_delete=models.CASCADE if {rel.cascade_delete} else models.SET_NULL,
        null={rel.nullable},
        related_name='{rel.back_populates or (self.resource_name + "_" + rel.name)}'
    )"""
                relationships_code.append(code)

            elif rel.relation_type == RelationType.MANY_TO_MANY:
                code = f"""    {rel.name} = models.ManyToManyField(
        '{rel.related_model}',
        related_name='{rel.back_populates or (self.resource_name + "_" + rel.name)}',
        blank=True
    )"""
                relationships_code.append(code)

        return f"""
from django.db import models

class {self.resource_name.capitalize()}(models.Model):
    # Relationships
{''.join(relationships_code) if relationships_code else '    pass'}

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return str(self.id)
"""

    def generate_django_serializers(self, relationships: List[Relationship]) -> str:
        """Generate Django nested serializers for relationships"""
        nested_serializers = []

        for rel in relationships:
            serializer_name = f"{rel.related_model.capitalize()}Serializer"
            if rel.relation_type == RelationType.MANY_TO_MANY:
                nested_serializers.append(f"""    {rel.name} = {serializer_name}(many=True, read_only=True)""")
            elif rel.relation_type in [RelationType.ONE_TO_MANY, RelationType.ONE_TO_ONE]:
                nested_serializers.append(f"""    {rel.name} = {serializer_name}(read_only=True)""")

        return f"""
from rest_framework import serializers

class {self.resource_name.capitalize()}Serializer(serializers.ModelSerializer):
{''.join(nested_serializers) if nested_serializers else '    pass'}

    class Meta:
        model = {self.resource_name.capitalize()}
        fields = '__all__'
"""

    def generate_fastapi(self, relationships: List[Relationship]) -> str:
        """Generate FastAPI relationship schemas"""
        pydantic_fields = []

        for rel in relationships:
            schema_name = f"{rel.related_model.capitalize()}Schema"
            if rel.relation_type == RelationType.MANY_TO_MANY:
                pydantic_fields.append(f"    {rel.name}: List[{schema_name}] = []")
            elif rel.relation_type in [RelationType.ONE_TO_MANY, RelationType.ONE_TO_ONE]:
                nullable = f"Optional[{schema_name}]" if rel.nullable else schema_name
                pydantic_fields.append(f"    {rel.name}: {nullable} = None")

        return f"""
from pydantic import BaseModel
from typing import Optional, List

class {self.resource_name.capitalize()}Schema(BaseModel):
{''.join(pydantic_fields) if pydantic_fields else '    pass'}

    class Config:
        from_attributes = True
"""

    def generate_fastapi_nested_routes(self, relationships: List[Relationship]) -> str:
        """Generate FastAPI nested routes for relationships"""
        routes = []

        for rel in relationships:
            if rel.relation_type == RelationType.MANY_TO_MANY:
                routes.append(f"""
@router.get("/{{{self.resource_name}_id}}/{rel.name}")
async def get_{self.resource_name}_{rel.name}({self.resource_name}_id: int):
    # Retrieve all {rel.name} for {self.resource_name}
    pass

@router.post("/{{{self.resource_name}_id}}/{rel.name}")
async def add_{self.resource_name}_{rel.name}({self.resource_name}_id: int, item_id: int):
    # Add {rel.name} to {self.resource_name}
    pass

@router.delete("/{{{self.resource_name}_id}}/{rel.name}/{{{rel.name}_id}}")
async def remove_{self.resource_name}_{rel.name}({self.resource_name}_id: int, {rel.name}_id: int):
    # Remove {rel.name} from {self.resource_name}
    pass""")

        return "\n".join(routes) if routes else "# No nested routes"


def generate_relationships(
    framework: str,
    resource_name: str,
    relationships: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, str]:
    """
    Generate relationship code.

    Args:
        framework: django or fastapi
        resource_name: e.g., "user"
        relationships: list of relationship dicts

    Returns: dict of {filename: code_content}
    """
    generator = RelationshipGenerator(framework, resource_name)
    output = {}

    rel_objs = [
        Relationship(
            name=r.get("name"),
            relation_type=RelationType(r.get("type", "many_to_one")),
            related_model=r.get("related_model"),
            back_populates=r.get("back_populates"),
            cascade_delete=r.get("cascade_delete", False),
            nullable=r.get("nullable", True)
        )
        for r in (relationships or [])
    ]

    if framework == "django":
        output["relationships.py"] = generator.generate_django(rel_objs)
        output["relationship_serializers.py"] = generator.generate_django_serializers(rel_objs)
    elif framework == "fastapi":
        output["relationships.py"] = generator.generate_fastapi(rel_objs)
        output["nested_routes.py"] = generator.generate_fastapi_nested_routes(rel_objs)

    return output
