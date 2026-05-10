#!/usr/bin/env python3
"""GDPR Data Handling"""
from typing import Dict

class GDPRGenerator:
    def __init__(self, framework: str):
        self.framework = framework.lower()

    def generate(self) -> Dict[str, str]:
        files = {}
        files['gdpr_handler.py'] = self._gdpr()
        return files

    def _gdpr(self) -> str:
        return '''class GDPRHandler:
    def right_to_erasure(self, user_id):
        return {"status": "deleted", "user_id": user_id}
'''
