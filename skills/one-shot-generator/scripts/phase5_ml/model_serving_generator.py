#!/usr/bin/env python3
"""ML Model Serving Generator"""
from typing import Dict

class ModelServingGenerator:
    def __init__(self, framework: str):
        self.framework = framework.lower()

    def generate(self) -> Dict[str, str]:
        return {'serving.py': 'from fastapi import FastAPI\napp = FastAPI()'}
