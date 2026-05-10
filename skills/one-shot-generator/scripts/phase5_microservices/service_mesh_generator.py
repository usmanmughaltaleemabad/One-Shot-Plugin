#!/usr/bin/env python3
"""Service Mesh (Istio) Generator"""
from typing import Dict

class ServiceMeshGenerator:
    def __init__(self, framework: str):
        self.framework = framework.lower()

    def generate(self) -> Dict[str, str]:
        return {'istio/vs.yaml': 'apiVersion: networking.istio.io/v1beta1'}
