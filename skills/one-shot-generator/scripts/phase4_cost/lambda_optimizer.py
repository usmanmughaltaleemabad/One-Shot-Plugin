#!/usr/bin/env python3
"""AWS Lambda Cost Optimization"""
from typing import Dict

class LambdaOptimizer:
    def __init__(self, framework: str):
        self.framework = framework.lower()

    def generate(self) -> Dict[str, str]:
        files = {}
        files['lambda_config.py'] = self._lambda_config()
        return files

    def _lambda_config(self) -> str:
        return '''class LambdaConfig:
    MEMORY_MB = 512
    TIMEOUT_SEC = 30
    EPHEMERAL_STORAGE = 512
'''
