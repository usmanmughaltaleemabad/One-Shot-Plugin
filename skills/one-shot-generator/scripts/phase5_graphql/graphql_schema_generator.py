#!/usr/bin/env python3
"""GraphQL Schema Generator"""
from typing import Dict

class GraphQLSchemaGenerator:
    def __init__(self, framework: str):
        self.framework = framework.lower()

    def generate(self) -> Dict[str, str]:
        return {'schema.graphql': 'type Query { order(id: ID!): Order }'}
