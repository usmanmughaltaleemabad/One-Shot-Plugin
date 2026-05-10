#!/usr/bin/env python3
"""GraphQL Resolver Generator"""
from typing import Dict

class GraphQLResolverGenerator:
    def __init__(self, framework: str):
        self.framework = framework.lower()

    def generate(self) -> Dict[str, str]:
        return {'resolvers.py': 'def resolve_order(obj, info, id): pass'}
