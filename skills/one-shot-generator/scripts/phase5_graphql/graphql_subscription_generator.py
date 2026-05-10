#!/usr/bin/env python3
"""GraphQL Subscription Generator"""
from typing import Dict

class GraphQLSubscriptionGenerator:
    def __init__(self, framework: str):
        self.framework = framework.lower()

    def generate(self) -> Dict[str, str]:
        return {'subscriptions.graphql': 'type Subscription { orderCreated: Order! }'}
