#!/usr/bin/env python3
"""API Gateway Generator"""
from typing import Dict

class APIGatewayGenerator:
    def __init__(self, framework: str):
        self.framework = framework.lower()

    def generate(self) -> Dict[str, str]:
        return {'kong/kong.yaml': '_format_version: "1.1"'}
