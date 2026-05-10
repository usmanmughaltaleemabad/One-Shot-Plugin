#!/usr/bin/env python3
"""Caching Strategy Generator"""
from typing import Dict

class CachingStrategyGenerator:
    def __init__(self, framework: str):
        self.framework = framework.lower()

    def generate(self) -> Dict[str, str]:
        files = {}
        files['cache_config.py'] = self._cache_config()
        return files

    def _cache_config(self) -> str:
        return '''class CacheConfig:
    REDIS_URL = "redis://localhost:6379"
    TTL_SECONDS = 3600
'''
