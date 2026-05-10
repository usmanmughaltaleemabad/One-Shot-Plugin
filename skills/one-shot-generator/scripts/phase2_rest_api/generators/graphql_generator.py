"""
GraphQL Generator - GraphQL schema from REST API

Generates:
- GraphQL schema from REST models
- GraphQL resolvers
- Query and mutation types
- Subscription support
"""

from typing import Dict, Any


class GraphQLGenerator:
    """Generate GraphQL schema"""

    def __init__(self, framework: str, model_name: str):
        self.framework = framework
        self.model_name = model_name

    def generate_graphql_schema(self) -> str:
        """Generate GraphQL schema"""
        return f"""
import graphene
from graphene_django import DjangoObjectType
from .models import {self.model_name}

class {self.model_name}Type(DjangoObjectType):
    class Meta:
        model = {self.model_name}
        fields = ('id', 'name', 'description', 'created_at', 'updated_at')

class Query(graphene.ObjectType):
    all_{self.model_name.lower()}s = graphene.List({self.model_name}Type)
    {self.model_name.lower()} = graphene.Field({self.model_name}Type, id=graphene.Int(required=True))

    def resolve_all_{self.model_name.lower()}s(self, info):
        return {self.model_name}.objects.all()

    def resolve_{self.model_name.lower()}(self, info, id):
        try:
            return {self.model_name}.objects.get(pk=id)
        except {self.model_name}.DoesNotExist:
            return None

class Create{self.model_name}(graphene.Mutation):
    {self.model_name.lower()} = graphene.Field({self.model_name}Type)

    class Arguments:
        name = graphene.String(required=True)
        description = graphene.String()

    def mutate(self, info, name, description=''):
        {self.model_name.lower()} = {self.model_name}.objects.create(
            name=name,
            description=description
        )
        return Create{self.model_name}({self.model_name.lower()}={self.model_name.lower()})

class Update{self.model_name}(graphene.Mutation):
    {self.model_name.lower()} = graphene.Field({self.model_name}Type)

    class Arguments:
        id = graphene.Int(required=True)
        name = graphene.String()
        description = graphene.String()

    def mutate(self, info, id, name=None, description=None):
        {self.model_name.lower()} = {self.model_name}.objects.get(pk=id)
        if name:
            {self.model_name.lower()}.name = name
        if description:
            {self.model_name.lower()}.description = description
        {self.model_name.lower()}.save()
        return Update{self.model_name}({self.model_name.lower()}={self.model_name.lower()})

class Mutation(graphene.ObjectType):
    create_{self.model_name.lower()} = Create{self.model_name}.Field()
    update_{self.model_name.lower()} = Update{self.model_name}.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)
"""

    def generate_fastapi_graphql(self) -> str:
        """Generate FastAPI GraphQL (Strawberry)"""
        return f"""
import strawberry
from typing import List, Optional
from datetime import datetime

@strawberry.type
class {self.model_name}:
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

@strawberry.type
class Query:
    @strawberry.field
    def all_{self.model_name.lower()}s(self) -> List[{self.model_name}]:
        # Fetch all {self.model_name.lower()}s
        return []

    @strawberry.field
    def {self.model_name.lower()}(self, id: int) -> Optional[{self.model_name}]:
        # Fetch single {self.model_name.lower()}
        return None

@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_{self.model_name.lower()}(
        self,
        name: str,
        description: Optional[str] = None
    ) -> {self.model_name}:
        # Create {self.model_name.lower()}
        return {self.model_name}(
            id=1,
            name=name,
            description=description,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

    @strawberry.mutation
    def update_{self.model_name.lower()}(
        self,
        id: int,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Optional[{self.model_name}]:
        # Update {self.model_name.lower()}
        return None

schema = strawberry.Schema(query=Query, mutation=Mutation)
"""


def generate_graphql(framework: str, model_name: str) -> Dict[str, str]:
    """
    Generate GraphQL schema.

    Args:
        framework: django or fastapi
        model_name: e.g., "User"

    Returns: dict of {filename: code_content}
    """
    generator = GraphQLGenerator(framework, model_name)
    output = {}

    if framework == "django":
        output["graphql_schema.py"] = generator.generate_graphql_schema()
    elif framework == "fastapi":
        output["graphql_schema.py"] = generator.generate_fastapi_graphql()

    return output
