#!/usr/bin/env python3
"""gRPC Service Generator"""
from typing import Dict

class gRPCGenerator:
    def __init__(self, framework: str):
        self.framework = framework.lower()

    def generate(self) -> Dict[str, str]:
        return {'grpc/api.proto': 'syntax = "proto3";'}
