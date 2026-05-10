#!/usr/bin/env python3
"""CDN Configuration Generator"""
from typing import Dict

class CDNConfigGenerator:
    def __init__(self, framework: str):
        self.framework = framework.lower()

    def generate(self) -> Dict[str, str]:
        files = {}
        files['cloudfront_config.json'] = self._cloudfront()
        return files

    def _cloudfront(self) -> str:
        return '''{"Distribution": {"DistributionConfig": {"Enabled": true}}}'''
