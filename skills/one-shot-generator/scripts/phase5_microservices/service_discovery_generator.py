#!/usr/bin/env python3
"""Service Discovery Generator"""
from typing import Dict

class ServiceDiscoveryGenerator:
    def __init__(self, framework: str):
        self.framework = framework.lower()

    def generate(self) -> Dict[str, str]:
        return {'consul/service.hcl': 'service { name = "api" }'}
