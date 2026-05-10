"""
Rate Limiting Handler - Job submission rate limiting

Generates:
- Per-user rate limiting
- Per-endpoint rate limiting
- Queue backpressure handling
- Leaky bucket algorithm
- Token bucket algorithm
"""

from typing import Dict, Any


class RateLimitingHandler:
    """Generate rate limiting code"""

    def __init__(self, framework: str, language: str):
        self.framework = framework
        self.language = language

    def generate_django_rate_limiting(self) -> str:
        """Generate Django rate limiting"""
        return """
from django.core.cache import cache
from django.http import JsonResponse
from functools import wraps
import logging
import time

logger = logging.getLogger(__name__)

class RateLimiter:
    '''Rate limiting for job submission'''

    def __init__(self, max_requests: int = 100, window: int = 60):
        self.max_requests = max_requests
        self.window = window  # seconds

    def is_allowed(self, identifier: str) -> bool:
        '''Check if request is allowed'''
        key = f'rate_limit:{identifier}'
        current = cache.get(key, 0)

        if current >= self.max_requests:
            logger.warning(f'Rate limit exceeded for {identifier}')
            return False

        cache.set(key, current + 1, self.window)
        return True

    def get_remaining(self, identifier: str) -> int:
        '''Get remaining requests'''
        key = f'rate_limit:{identifier}'
        current = cache.get(key, 0)
        return max(0, self.max_requests - current)

def rate_limit(max_requests: int = 100, window: int = 60):
    '''Decorator for rate limiting'''
    def decorator(view_func):
        limiter = RateLimiter(max_requests, window)

        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Use user ID or IP as identifier
            if request.user.is_authenticated:
                identifier = f'user:{request.user.id}'
            else:
                identifier = f'ip:{request.META.get("REMOTE_ADDR")}'

            if not limiter.is_allowed(identifier):
                return JsonResponse({
                    'error': 'Rate limit exceeded',
                    'retry_after': limiter.window
                }, status=429)

            response = view_func(request, *args, **kwargs)

            # Add rate limit headers
            remaining = limiter.get_remaining(identifier)
            response['X-RateLimit-Remaining'] = remaining
            response['X-RateLimit-Window'] = limiter.window

            return response

        return wrapper
    return decorator

class TokenBucket:
    '''Token bucket for rate limiting'''

    def __init__(self, capacity: float, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.tokens = capacity
        self.last_refill = time.time()

    def consume(self, tokens: float = 1) -> bool:
        '''Consume tokens if available'''
        self._refill()

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def _refill(self):
        '''Refill tokens based on elapsed time'''
        now = time.time()
        elapsed = now - self.last_refill
        refilled = elapsed * self.refill_rate

        self.tokens = min(self.capacity, self.tokens + refilled)
        self.last_refill = now

class LeakyBucket:
    '''Leaky bucket for smooth rate limiting'''

    def __init__(self, capacity: int, leak_rate: float):
        self.capacity = capacity
        self.leak_rate = leak_rate  # items per second
        self.queue = []
        self.last_leak = time.time()

    def add(self, item: any) -> bool:
        '''Add item to bucket'''
        self._leak()

        if len(self.queue) < self.capacity:
            self.queue.append(item)
            return True
        return False

    def _leak(self):
        '''Leak items based on leak rate'''
        now = time.time()
        elapsed = now - self.last_leak
        leaked = int(elapsed * self.leak_rate)

        for _ in range(min(leaked, len(self.queue))):
            self.queue.pop(0)

        self.last_leak = now

# Global rate limiters
default_limiter = RateLimiter(max_requests=1000, window=3600)
per_user_limiter = RateLimiter(max_requests=100, window=60)
"""

    def generate_fastapi_rate_limiting(self) -> str:
        """Generate FastAPI rate limiting"""
        return """
from fastapi import Request, HTTPException
from functools import wraps
import time
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    '''Rate limiting using sliding window'''

    def __init__(self, max_requests: int = 100, window: int = 60):
        self.max_requests = max_requests
        self.window = window
        self.requests = {}

    def is_allowed(self, identifier: str) -> tuple:
        '''Check if allowed, return (allowed, remaining, reset_time)'''
        now = time.time()

        if identifier not in self.requests:
            self.requests[identifier] = []

        # Clean old requests outside window
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if now - req_time < self.window
        ]

        if len(self.requests[identifier]) >= self.max_requests:
            reset_time = self.requests[identifier][0] + self.window
            return False, 0, reset_time

        self.requests[identifier].append(now)
        remaining = self.max_requests - len(self.requests[identifier])
        reset_time = now + self.window

        return True, remaining, reset_time

async def rate_limit_middleware(request: Request, call_next):
    '''Middleware for rate limiting'''
    # Identify user
    if request.user:
        identifier = f'user:{request.user.id}'
    else:
        identifier = f'ip:{request.client.host}'

    limiter = RateLimiter()
    allowed, remaining, reset = limiter.is_allowed(identifier)

    if not allowed:
        raise HTTPException(
            status_code=429,
            detail='Rate limit exceeded',
            headers={'Retry-After': str(int(reset))}
        )

    response = await call_next(request)
    response.headers['X-RateLimit-Remaining'] = str(remaining)
    response.headers['X-RateLimit-Reset'] = str(int(reset))

    return response

class TokenBucket:
    '''Token bucket implementation'''

    def __init__(self, capacity: float, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()

    def consume(self, tokens: float = 1) -> bool:
        '''Consume tokens'''
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(
            self.capacity,
            self.tokens + elapsed * self.refill_rate
        )
        self.last_refill = now

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

class QueueBackpressure:
    '''Handle backpressure when queue is full'''

    def __init__(self, max_queue_size: int = 10000):
        self.max_queue_size = max_queue_size

    async def check_capacity(self) -> bool:
        '''Check if queue has capacity'''
        from batch_job_integration import integration
        stats = await integration.get_stats()
        total_jobs = sum(q['current_jobs'] for q in stats.values())

        if total_jobs >= self.max_queue_size:
            logger.warning(f'Queue at capacity: {total_jobs}/{self.max_queue_size}')
            return False
        return True

    async def wait_for_capacity(self, timeout: int = 300):
        '''Wait until queue has capacity'''
        start = time.time()
        while time.time() - start < timeout:
            if await self.check_capacity():
                return True
            await __import__('asyncio').sleep(1)
        return False

backpressure = QueueBackpressure()
"""

    def generate_nestjs_rate_limiting(self) -> str:
        """Generate NestJS rate limiting"""
        return """
import { Injectable } from '@nestjs/common';
import { RateLimiterMemory } from 'rate-limiter-flexible';

@Injectable()
export class RateLimiterService {
    private limiter: RateLimiterMemory;
    private perUserLimiter: RateLimiterMemory;

    constructor() {
        // Global rate limiter: 1000 requests per hour
        this.limiter = new RateLimiterMemory({
            points: 1000,
            duration: 3600,
        });

        // Per-user rate limiter: 100 requests per minute
        this.perUserLimiter = new RateLimiterMemory({
            points: 100,
            duration: 60,
        });
    }

    async checkLimit(identifier: string): Promise<boolean> {
        try {
            await this.limiter.consume(identifier);
            return true;
        } catch (e) {
            return false;
        }
    }

    async checkUserLimit(userId: string): Promise<boolean> {
        try {
            await this.perUserLimiter.consume(`user:${userId}`);
            return true;
        } catch (e) {
            return false;
        }
    }

    async getRemainingRequests(identifier: string): Promise<number> {
        const res = await this.limiter.get(identifier);
        return res ? res.remainingPoints : 1000;
    }
}

export class TokenBucket {
    private tokens: number;
    private lastRefill: number;

    constructor(
        private capacity: number,
        private refillRate: number // tokens per second
    ) {
        this.tokens = capacity;
        this.lastRefill = Date.now();
    }

    consume(tokens: number = 1): boolean {
        this.refill();

        if (this.tokens >= tokens) {
            this.tokens -= tokens;
            return true;
        }
        return false;
    }

    private refill(): void {
        const now = Date.now();
        const elapsedSeconds = (now - this.lastRefill) / 1000;
        const refilled = elapsedSeconds * this.refillRate;

        this.tokens = Math.min(this.capacity, this.tokens + refilled);
        this.lastRefill = now;
    }
}

export class QueueBackpressure {
    constructor(private maxQueueSize: number = 10000) {}

    async checkCapacity(): Promise<boolean> {
        // Check current queue size
        // Return false if at capacity
        return true;
    }

    async waitForCapacity(timeout: number = 300000): Promise<boolean> {
        const start = Date.now();
        while (Date.now() - start < timeout) {
            if (await this.checkCapacity()) {
                return true;
            }
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
        return false;
    }
}
"""


def generate_rate_limiting_handler(framework: str, language: str) -> Dict[str, str]:
    """
    Generate rate limiting handler code.

    Args:
        framework: django, fastapi, spring
        language: python, javascript

    Returns: dict of {filename: code_content}
    """
    generator = RateLimitingHandler(framework, language)
    output = {}

    if language == "python":
        if framework == "django":
            output["rate_limiting.py"] = generator.generate_django_rate_limiting()
        elif framework == "fastapi":
            output["rate_limiting.py"] = generator.generate_fastapi_rate_limiting()
    elif language == "javascript":
        output["rate-limiter.service.ts"] = generator.generate_nestjs_rate_limiting()

    return output
