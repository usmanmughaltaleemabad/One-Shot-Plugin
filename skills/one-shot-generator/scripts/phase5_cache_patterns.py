#!/usr/bin/env python3
"""
Phase 5 Microservices: Caching Patterns

Cache: Speed up responses by storing results.

Problem: Database query takes 100ms
- User requests /products
- Database: SELECT * FROM products (100ms)
- User waits 100ms

Solution: Cache
- First request: query database (100ms), store result
- Second request: return from cache (1ms)
- 100x faster!

Challenges:
- Cache invalidation: when to refresh
- Consistency: cache vs database (stale data)
- Size: can't cache everything
- Thundering herd: many requests, cache miss, everyone hits database
"""

from typing import Dict, Optional, Any, Callable
from datetime import datetime, timedelta


def generate_cache_strategy() -> str:
    """Generate cache strategies."""

    cache = '''
class CacheStrategy:
    """
    Cache management with invalidation strategies.

    Strategies:
    - TTL: expire after X seconds
    - LRU: remove least recently used when full
    - Write-through: update cache + DB
    - Write-behind: update cache, async DB
    - Cache-aside: app manages cache
    """

    def __init__(self, max_size: int = 10000, ttl_seconds: int = 3600):
        self._cache = {}  # key → {value, expires_at}
        self._max_size = max_size
        self._ttl = timedelta(seconds=ttl_seconds)
        self._hits = 0
        self._misses = 0

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key not in self._cache:
            self._misses += 1
            return None

        entry = self._cache[key]

        # Check expiration
        if datetime.utcnow() > entry["expires_at"]:
            del self._cache[key]
            self._misses += 1
            return None

        self._hits += 1
        return entry["value"]

    def set(self, key: str, value: Any, ttl: Optional[timedelta] = None) -> None:
        """Set value in cache"""
        if len(self._cache) >= self._max_size:
            self._evict_lru()

        self._cache[key] = {
            "value": value,
            "expires_at": datetime.utcnow() + (ttl or self._ttl),
            "last_access": datetime.utcnow()
        }

    def invalidate(self, key: str) -> None:
        """Remove from cache"""
        if key in self._cache:
            del self._cache[key]

    def _evict_lru(self) -> None:
        """Remove least recently used"""
        if not self._cache:
            return

        lru_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k]["last_access"]
        )
        del self._cache[lru_key]

    def hit_rate(self) -> float:
        """Cache hit rate (0-1)"""
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0
'''

    return cache


def generate_cache_patterns() -> str:
    """Generate caching patterns."""

    patterns = '''
class CachePatterns:
    """
    Common caching patterns.

    1. CACHE-ASIDE
       - Check cache
       - If miss: fetch from DB, store in cache
       - If hit: return from cache

    2. WRITE-THROUGH
       - Write to cache
       - Write to DB
       - Both must succeed

    3. WRITE-BEHIND
       - Write to cache immediately (return)
       - Async write to DB (eventual consistency)
       - Faster, but risk of loss
    """

    def __init__(self, cache: CacheStrategy, db: 'Database'):
        self.cache = cache
        self.db = db

    def cache_aside_read(self, key: str, loader: Callable) -> Any:
        """Cache-aside pattern: load if not cached"""
        # Try cache
        value = self.cache.get(key)
        if value is not None:
            return value

        # Cache miss: load from DB
        value = loader(key)
        self.cache.set(key, value)
        return value

    def write_through(self, key: str, value: Any) -> None:
        """Write to cache + DB"""
        self.cache.set(key, value)
        self.db.put(key, value)

    def write_behind(self, key: str, value: Any) -> None:
        """Write to cache, async to DB"""
        self.cache.set(key, value)
        # Schedule async write to DB
        import threading
        threading.Thread(target=self.db.put, args=(key, value)).start()
'''

    return patterns


def generate_cache_system() -> dict:
    """Generate complete caching system."""

    imports = '''from typing import Dict, Optional, Any, Callable
from datetime import datetime, timedelta


'''

    module_doc = '''"""
Phase 5 Caching Patterns: Performance Optimization

Speed up systems with strategic caching (Redis/Memcached).

CACHING LAYER:
Browser Cache (HTTP cache) → CDN Cache → App Cache → Database

EXAMPLE: Product listing

Without cache:
- Request: GET /products
- Database: SELECT * FROM products (100ms)
- Response: [1000 products] (50ms)
- Total: 150ms per request
- 1000 req/sec → database saturated (100,000ms = 100 seconds worth of queries)

With cache:
- Request 1: GET /products
- Cache miss: query database (100ms)
- Store in cache (10MB)
- Request 2-1000: GET /products
- Cache hit: return cached result (1ms)
- Total time: 100ms + 999ms = 1.1s (vs 150s without cache)

CACHE INVALIDATION STRATEGIES:

1. TTL (Time To Live)
   - Cache products for 1 hour
   - After 1 hour: refresh from database
   - Simple, but stale data for up to 1 hour

2. Event-based
   - Product updated
   - Invalidate cache: delete products/{id}
   - Next request: refetch from database
   - Accurate, but need to update all places that modify

3. Manual invalidation
   - Admin button: "Refresh cache"
   - Triggers refresh
   - For rarely-changing data

CACHE LEVELS:

Level 1: Browser cache
- HTTP caching headers (Cache-Control, ETag)
- Works: static assets (CSS, JS, images)
- Doesn't work: dynamic data

Level 2: CDN cache
- CloudFront, Cloudflare
- Cache HTML/JSON at edge
- Serve from nearest location
- ~50ms → ~5ms

Level 3: App cache
- Redis/Memcached
- Cache in application
- Very fast (1-2ms)
- Shared across server instances

Level 4: Database cache
- Internal query cache
- Fastest for repeated queries
- Limited size

THUNDERING HERD:
- Product #123 popular
- Cache expires
- 1000 requests hit at same time
- All hit database
- Database overloaded

Solution: Lock cache
- First request: acquire lock, query database
- Other requests: wait for lock, use result
- Release lock: all queries satisfied
- Prevents thundering herd
"""
'''

    cache = generate_cache_strategy()
    patterns = generate_cache_patterns()

    complete_code = imports + module_doc + "\n" + cache + "\n" + patterns

    return {
        "code": complete_code,
        "pattern": "Caching Patterns",
        "module": "phase5_cache_patterns.py"
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate caching patterns")
    args = parser.parse_args()
    result = generate_cache_system()
    print(result["code"])


if __name__ == "__main__":
    main()
