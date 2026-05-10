#!/usr/bin/env python3
"""Helm Chart Generator"""
from typing import Dict

class HelmGenerator:
    def __init__(self, framework: str):
        self.framework = framework.lower()

    def generate(self) -> Dict[str, str]:
        return {'helm/Chart.yaml': 'apiVersion: v2\nname: api-service'}
