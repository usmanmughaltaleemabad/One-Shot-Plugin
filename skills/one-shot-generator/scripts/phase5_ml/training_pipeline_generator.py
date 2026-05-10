#!/usr/bin/env python3
"""ML Training Pipeline Generator"""
from typing import Dict

class TrainingPipelineGenerator:
    def __init__(self, framework: str):
        self.framework = framework.lower()

    def generate(self) -> Dict[str, str]:
        return {'train.py': 'import pandas as pd\nfrom sklearn.ensemble import RandomForest'}
