#!/usr/bin/env python3
"""SOC 2 Type II Controls Generation"""
from typing import Dict

class SOC2Generator:
    def __init__(self, framework: str):
        self.framework = framework.lower()

    def generate(self) -> Dict[str, str]:
        files = {}
        files['soc2_controls.py'] = self._soc2_controls()
        return files

    def _soc2_controls(self) -> str:
        return '''class SOC2Controls:
    AUDIT_LOGGING_ENABLED = True
    ENCRYPTION_ENABLED = True
    MFA_REQUIRED = True
'''
