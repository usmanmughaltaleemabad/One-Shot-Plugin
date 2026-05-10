"""
Rate Limiter Generator - Request rate limiting

Generates rate limiting logic for:
- Per-IP rate limiting
- Per-user rate limiting
- Per-endpoint rate limiting
- Token bucket algorithm
- Sliding window algorithm
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    by_ip: bool = True
    by_user: bool = True
    endpoint_specific: bool = False


class RateLimiterGenerator:
    """Generate rate limiting code"""

    def __init__(self, framework: str, config: RateLimitConfig):
        self.framework = framework
        self.config = config

    def generate_django(self) -> str:
        """Generate Django rate limiting with django-ratelimit"""
        return f"""
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from rest_framework.exceptions import Throttled
import time

class CustomUserThrottle(UserRateThrottle):
    scope = 'user'
    THROTTLE_RATES = {{
        'user': '{self.config.requests_per_minute}/min',
        'anon': '{self.config.requests_per_minute}/min'
    }}

class CustomAnonThrottle(AnonRateThrottle):
    scope = 'anon'
    THROTTLE_RATES = {{
        'anon': '{self.config.requests_per_minute}/min'
    }}

class EndpointThrottle(UserRateThrottle):
    scope = 'endpoint'
    THROTTLE_RATES = {{
        'endpoint': '{self.config.requests_per_minute}/min'
    }}

class RateLimiter:
    def __init__(self, requests_per_minute: int = {self.config.requests_per_minute}):
        self.requests_per_minute = requests_per_minute
        self.window_size = 60  # seconds

    def is_allowed(self, identifier: str) -> bool:
        key = f'rate_limit:{{identifier}}'
        current = cache.get(key, 0)

        if current >= self.requests_per_minute:
            return False

        cache.set(key, current + 1, self.window_size)
        return True

    def get_remaining(self, identifier: str) -> int:
        key = f'rate_limit:{{identifier}}'
        current = cache.get(key, 0)
        return max(0, self.requests_per_minute - current)

def rate_limit_by_ip(requests_per_minute: int = {self.config.requests_per_minute}):
    def decorator(view_func):
        limiter = RateLimiter(requests_per_minute)
        def wrapper(request, *args, **kwargs):
            client_ip = get_client_ip(request)
            if not limiter.is_allowed(client_ip):
                return Response({{'error': 'Rate limit exceeded'}}, status=429)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def rate_limit_by_user(requests_per_minute: int = {self.config.requests_per_minute}):
    def decorator(view_func):
        limiter = RateLimiter(requests_per_minute)
        def wrapper(request, *args, **kwargs):
            identifier = f'user:{{request.user.id}}' if request.user else 'anon'
            if not limiter.is_allowed(identifier):
                return Response({{'error': 'Rate limit exceeded'}}, status=429)
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
"""

    def generate_fastapi(self) -> str:
        """Generate FastAPI rate limiting"""
        return f"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from functools import wraps
import time
from typing import Dict

class RateLimiter:
    def __init__(self, requests_per_minute: int = {self.config.requests_per_minute}):
        self.requests_per_minute = requests_per_minute
        self.window_size = 60  # seconds
        self.requests: Dict[str, list] = {{}}

    def is_allowed(self, identifier: str) -> bool:
        current_time = time.time()
        window_start = current_time - self.window_size

        if identifier not in self.requests:
            self.requests[identifier] = []

        # Remove old requests outside the window
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > window_start
        ]

        if len(self.requests[identifier]) >= self.requests_per_minute:
            return False

        self.requests[identifier].append(current_time)
        return True

    def get_remaining(self, identifier: str) -> int:
        if identifier not in self.requests:
            return self.requests_per_minute

        current_time = time.time()
        window_start = current_time - self.window_size

        active_requests = [
            req_time for req_time in self.requests[identifier]
            if req_time > window_start
        ]

        return max(0, self.requests_per_minute - len(active_requests))

limiter = RateLimiter({self.config.requests_per_minute})

def get_client_ip(request: Request) -> str:
    if request.headers.get('x-forwarded-for'):
        return request.headers['x-forwarded-for'].split(',')[0]
    return request.client.host

async def rate_limit_middleware(request: Request, call_next):
    identifier = f"user:{{request.user}}" if hasattr(request, 'user') else f"ip:{{get_client_ip(request)}}"

    if not limiter.is_allowed(identifier):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={{'error': 'Rate limit exceeded'}}
        )

    response = await call_next(request)
    remaining = limiter.get_remaining(identifier)
    response.headers['X-RateLimit-Remaining'] = str(remaining)
    response.headers['X-RateLimit-Limit'] = str(limiter.requests_per_minute)

    return response

def limit_by_ip(requests_per_minute: int = {self.config.requests_per_minute}):
    async def middleware(request: Request, call_next):
        ip = get_client_ip(request)
        limiter_ip = RateLimiter(requests_per_minute)

        if not limiter_ip.is_allowed(ip):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={{'error': 'Rate limit exceeded'}}
            )

        return await call_next(request)
    return middleware

def limit_by_user(requests_per_minute: int = {self.config.requests_per_minute}):
    async def middleware(request: Request, call_next):
        user_id = getattr(request.state, 'user_id', None) or 'anonymous'
        limiter_user = RateLimiter(requests_per_minute)

        if not limiter_user.is_allowed(f'user:{{user_id}}'):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={{'error': 'Rate limit exceeded'}}
            )

        return await call_next(request)
    return middleware
"""


def generate_rate_limiter(
    framework: str,
    requests_per_minute: int = 60
) -> Dict[str, str]:
    """
    Generate rate limiting code.

    Args:
        framework: django or fastapi
        requests_per_minute: number of requests allowed per minute

    Returns: dict of {filename: code_content}
    """
    config = RateLimitConfig(requests_per_minute=requests_per_minute)
    generator = RateLimiterGenerator(framework, config)
    output = {}

    if framework == "django":
        output["rate_limiter.py"] = generator.generate_django()
    elif framework == "fastapi":
        output["rate_limiter.py"] = generator.generate_fastapi()

    return output
