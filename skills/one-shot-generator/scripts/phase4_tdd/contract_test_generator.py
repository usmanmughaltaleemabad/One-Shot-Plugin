#!/usr/bin/env python3
"""Consumer-Driven Contract Tests"""
from typing import Dict

class ContractTestGenerator:
    def __init__(self, framework: str):
        self.framework = framework.lower()

    def generate(self) -> Dict[str, str]:
        files = {}
        files['pact/order_consumer.json'] = self._contract()
        return files

    def _contract(self) -> str:
        return '''{"interactions": [{"request": {"method": "POST", "path": "/orders"}}]}'''
