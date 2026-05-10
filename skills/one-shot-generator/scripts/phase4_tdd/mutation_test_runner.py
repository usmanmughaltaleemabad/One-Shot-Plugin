#!/usr/bin/env python3
"""Mutation Testing Configuration"""
from typing import Dict

class MutationTestRunner:
    def __init__(self, framework: str):
        self.framework = framework.lower()

    def generate(self) -> Dict[str, str]:
        files = {}
        files['mutmut_config.ini'] = self._mutmut_config()
        return files

    def _mutmut_config(self) -> str:
        return '''[mutmut]
tests_dir = tests
backup = False
'''
