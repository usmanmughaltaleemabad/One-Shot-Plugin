#!/usr/bin/env python3
"""Phase 5 GraphQL Caching: Persisted Queries & Cache Invalidation"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta


def generate_graphql_caching() -> str:
    caching = '''
class PersistedQueryCache:
    """Cache GraphQL queries and invalidate on mutations."""

    def __init__(self):
        self._queries = {}  # query_hash → query_text
        self._cache = {}  # cache_key → {data, expires_at}
        self._dependencies = {}  # resource_type → [cache_keys]
        self._ttl = 3600  # 1 hour default

    def register_query(self, query_id: str, query_text: str) -> str:
        """Persist query (client sends ID instead of full query)"""
        self._queries[query_id] = query_text
        return query_id

    def cache_result(self, query_id: str, variables: Dict, result: Dict) -> None:
        """Cache query result"""
        cache_key = f"{query_id}:{str(variables)}"
        self._cache[cache_key] = {
            "data": result,
            "expires_at": (datetime.utcnow() + timedelta(seconds=self._ttl)).isoformat()
        }

    def get_cached(self, query_id: str, variables: Dict) -> Optional[Dict]:
        """Get cached result"""
        cache_key = f"{query_id}:{str(variables)}"
        cached = self._cache.get(cache_key)
        if cached and datetime.fromisoformat(cached["expires_at"]) > datetime.utcnow():
            return cached["data"]
        return None

    def invalidate_by_type(self, resource_type: str) -> None:
        """Invalidate all caches for resource type"""
        if resource_type in self._dependencies:
            for cache_key in self._dependencies[resource_type]:
                self._cache.pop(cache_key, None)
'''
    return caching


def generate_caching_system() -> dict:
    imports = 'from typing import Dict, List, Optional\\nfrom datetime import datetime, timedelta\\n\\n\\n'
    module_doc = '''"""GraphQL query caching with automatic invalidation (Apollo/Relay pattern)."""'''
    caching = generate_graphql_caching()
    return {"code": imports + module_doc + "\\n" + caching, "pattern": "GraphQL Caching", "module": "phase5_graphql_caching.py"}


if __name__ == "__main__":
    print(generate_caching_system()["code"])
