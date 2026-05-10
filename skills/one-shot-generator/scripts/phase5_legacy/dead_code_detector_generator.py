#!/usr/bin/env python3
"""Dead Code Detector"""
from typing import Dict

class DeadCodeDetectorGenerator:
    def __init__(self, framework: str):
        self.framework = framework.lower()

    def generate(self) -> Dict[str, str]:
        return {'dead_code.py': 'class DeadCodeDetector: pass'}
