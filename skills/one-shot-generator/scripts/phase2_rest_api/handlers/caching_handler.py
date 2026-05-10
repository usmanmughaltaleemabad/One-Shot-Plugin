"""
Caching Handler - Response caching and cache management

Generates:
- HTTP cache headers
- Redis caching
- In-memory caching
- Cache invalidation
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class CacheConfig:
    """Cache configuration"""
    ttl_seconds: int = 300
    cache_backend: str = "redis"  # redis, memcached, locmem
    enable_etag: bool = True
    enable_last_modified: bool = True


class CachingHandler:
    """Generate caching code"""

    def __init__(self, framework: str):
        self.framework = framework

    def generate_django_caching(self) -> str:
        """Generate Django caching"""
        return """
from django.views.decorators.cache import cache_page, cache_control
from django.utils.decorators import method_decorator
from django.core.cache import cache
from rest_framework.response import Response
from rest_framework.decorators import api_view
from functools import wraps
import hashlib

CACHE_TIMEOUT = 300  # 5 minutes

def cache_response(timeout=CACHE_TIMEOUT):
    '''Decorator to cache API responses'''
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Generate cache key from request
            cache_key = generate_cache_key(request)

            # Check cache
            cached_response = cache.get(cache_key)
            if cached_response:
                return cached_response

            # Execute view
            response = view_func(request, *args, **kwargs)

            # Cache successful responses
            if response.status_code == 200:
                cache.set(cache_key, response, timeout)

            return response
        return wrapper
    return decorator

def generate_cache_key(request, prefix='api'):
    '''Generate cache key from request'''
    key_data = f'{{prefix}}:{{request.path}}:{{request.query_string.decode()}}'
    return hashlib.md5(key_data.encode()).hexdigest()

@cache_page(60 * 5)  # Cache for 5 minutes
@api_view(['GET'])
def cached_list_view(request):
    '''View with Django cache_page decorator'''
    return Response({'data': []})

class CacheControlMixin:
    '''Mixin for cache control headers'''

    cache_timeout = 300

    @method_decorator(cache_control(max_age=300, must_revalidate=True))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @method_decorator(cache_control(max_age=60, must_revalidate=True))
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @method_decorator(cache_control(no_cache=True))
    def create(self, request, *args, **kwargs):
        # Clear related caches
        self.clear_cache()
        return super().create(request, *args, **kwargs)

    def clear_cache(self):
        '''Clear cache entries'''
        pattern = 'api:*'
        cache.delete_pattern(pattern)

class CacheManager:
    '''Manage cache operations'''

    @staticmethod
    def invalidate(key_pattern):
        '''Invalidate cache by pattern'''
        from django.core.cache import cache
        cache.delete_pattern(key_pattern)

    @staticmethod
    def get(key):
        '''Get value from cache'''
        return cache.get(key)

    @staticmethod
    def set(key, value, timeout=300):
        '''Set value in cache'''
        cache.set(key, value, timeout)

    @staticmethod
    def delete(key):
        '''Delete from cache'''
        cache.delete(key)

    @staticmethod
    def clear_all():
        '''Clear all cache'''
        cache.clear()
"""

    def generate_fastapi_caching(self) -> str:
        """Generate FastAPI caching"""
        return """
from fastapi import Response
from functools import wraps
import hashlib
from datetime import datetime, timedelta
import aioredis

# In-memory cache
in_memory_cache = {}

class CacheConfig:
    TTL_SECONDS = 300
    MAX_CACHE_SIZE = 1000

class CacheManager:
    def __init__(self):
        self.cache = {}
        self.ttl = CacheConfig.TTL_SECONDS

    async def get(self, key: str):
        '''Get value from cache'''
        if key in self.cache:
            value, expiry = self.cache[key]
            if datetime.now() < expiry:
                return value
            else:
                del self.cache[key]
        return None

    async def set(self, key: str, value, ttl: int = None):
        '''Set value in cache'''
        if ttl is None:
            ttl = self.ttl

        expiry = datetime.now() + timedelta(seconds=ttl)
        self.cache[key] = (value, expiry)

        # Enforce max cache size
        if len(self.cache) > CacheConfig.MAX_CACHE_SIZE:
            self.clear_old()

    async def delete(self, key: str):
        '''Delete from cache'''
        if key in self.cache:
            del self.cache[key]

    async def clear(self):
        '''Clear all cache'''
        self.cache.clear()

    def clear_old(self):
        '''Remove expired entries'''
        now = datetime.now()
        expired_keys = [
            k for k, (v, expiry) in self.cache.items()
            if expiry < now
        ]
        for key in expired_keys:
            del self.cache[key]

cache_manager = CacheManager()

def generate_cache_key(path: str, query_params: dict, prefix: str = 'api'):
    '''Generate cache key'''
    params_str = '&'.join(f'{{k}}={{v}}' for k, v in sorted(query_params.items()))
    key_data = f'{{prefix}}:{{path}}:{{params_str}}'
    return hashlib.md5(key_data.encode()).hexdigest()

async def cached_response(
    path: str,
    query_params: dict,
    ttl: int = 300
):
    '''Decorator for caching responses'''
    async def decorator(call_next):
        cache_key = generate_cache_key(path, query_params)

        # Check cache
        cached = await cache_manager.get(cache_key)
        if cached:
            return Response(
                content=cached,
                media_type='application/json',
                headers={'X-Cache': 'HIT'}
            )

        # Execute endpoint
        response = await call_next()

        # Cache response
        if response.status_code == 200:
            await cache_manager.set(cache_key, response.body, ttl)

        response.headers['X-Cache'] = 'MISS'
        return response

    return decorator

# Cache control headers
def add_cache_headers(response: Response, max_age: int = 300):
    '''Add cache control headers'''
    response.headers['Cache-Control'] = f'public, max-age={{max_age}}'
    response.headers['Expires'] = (datetime.now() + timedelta(seconds=max_age)).isoformat()
    return response

def add_no_cache_headers(response: Response):
    '''Add no-cache headers'''
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

class CacheMiddleware:
    async def __call__(self, request, call_next):
        response = await call_next(request)

        if request.method == 'GET':
            response = add_cache_headers(response, max_age=300)
        else:
            response = add_no_cache_headers(response)

        return response
"""


def generate_caching(framework: str) -> Dict[str, str]:
    """
    Generate caching code.

    Args:
        framework: django or fastapi

    Returns: dict of {filename: code_content}
    """
    handler = CachingHandler(framework)
    output = {}

    if framework == "django":
        output["caching.py"] = handler.generate_django_caching()
    elif framework == "fastapi":
        output["caching.py"] = handler.generate_fastapi_caching()

    return output
