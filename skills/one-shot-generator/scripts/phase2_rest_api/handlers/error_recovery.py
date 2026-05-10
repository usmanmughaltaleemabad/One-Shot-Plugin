"""
Error Recovery - Recovery strategies and retry logic

Provides:
- Exponential backoff for retries
- Circuit breaker pattern
- Fallback strategies
- Graceful degradation
- Error logging and monitoring
"""

from typing import Dict, Any, Callable, Optional
from dataclasses import dataclass
from enum import Enum
import time
import logging


logger = logging.getLogger(__name__)


class RetryStrategy(Enum):
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    FIBONACCI = "fibonacci"


@dataclass
class RetryConfig:
    """Retry configuration"""
    max_retries: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    backoff_multiplier: float = 2.0


class ErrorRecovery:
    """Error recovery and retry logic"""

    def __init__(self, config: RetryConfig):
        self.config = config

    def generate_django(self) -> str:
        """Generate Django error recovery code"""
        return f"""
import time
import logging
from functools import wraps
from enum import Enum

logger = logging.getLogger(__name__)

class RetryStrategy(Enum):
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    FIBONACCI = "fibonacci"

class RetryConfig:
    def __init__(self, max_retries: int = {self.config.max_retries},
                 initial_delay: float = {self.config.initial_delay},
                 max_delay: float = {self.config.max_delay}):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.strategy = RetryStrategy.EXPONENTIAL

class ExponentialBackoff:
    def __init__(self, initial_delay: float = {self.config.initial_delay}, multiplier: float = {self.config.backoff_multiplier}):
        self.initial_delay = initial_delay
        self.multiplier = multiplier

    def calculate_delay(self, attempt: int) -> float:
        delay = self.initial_delay * (self.multiplier ** attempt)
        return min(delay, {self.config.max_delay})

def retry_with_backoff(max_retries: int = {self.config.max_retries}, initial_delay: float = {self.config.initial_delay}):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            backoff = ExponentialBackoff(initial_delay)
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = backoff.calculate_delay(attempt)
                        logger.warning(f"Attempt {{attempt + 1}} failed. Retrying in {{delay}}s: {{str(e)}}")
                        time.sleep(delay)
                    else:
                        logger.error(f"All {{max_retries + 1}} attempts failed: {{str(e)}}")

            raise last_exception
        return wrapper
    return decorator

class CircuitBreaker:
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = self.CLOSED

    def call(self, func: callable, *args, **kwargs):
        if self.state == self.OPEN:
            if time.time() - self.last_failure_time > self.timeout:
                self.state = self.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise e

    def on_success(self):
        self.failure_count = 0
        self.state = self.CLOSED

    def on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = self.OPEN

class Fallback:
    @staticmethod
    def get_cached_value(cache_key: str, default_value=None):
        from django.core.cache import cache
        return cache.get(cache_key, default_value)

    @staticmethod
    def set_cached_value(cache_key: str, value: Any, timeout: int = 300):
        from django.core.cache import cache
        cache.set(cache_key, value, timeout)

    @staticmethod
    def use_stale_data(cache_key: str):
        from django.core.cache import cache
        return cache.get(cache_key)
"""

    def generate_fastapi(self) -> str:
        """Generate FastAPI error recovery code"""
        return f"""
import time
import logging
import asyncio
from functools import wraps
from enum import Enum

logger = logging.getLogger(__name__)

class RetryStrategy(Enum):
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    FIBONACCI = "fibonacci"

class ExponentialBackoff:
    def __init__(self, initial_delay: float = {self.config.initial_delay}, multiplier: float = {self.config.backoff_multiplier}):
        self.initial_delay = initial_delay
        self.multiplier = multiplier

    def calculate_delay(self, attempt: int) -> float:
        delay = self.initial_delay * (self.multiplier ** attempt)
        return min(delay, {self.config.max_delay})

def retry_with_backoff(max_retries: int = {self.config.max_retries}, initial_delay: float = {self.config.initial_delay}):
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            backoff = ExponentialBackoff(initial_delay)
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = backoff.calculate_delay(attempt)
                        logger.warning(f"Attempt {{attempt + 1}} failed. Retrying in {{delay}}s: {{str(e)}}")
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"All {{max_retries + 1}} attempts failed: {{str(e)}}")

            raise last_exception

        return async_wrapper
    return decorator

class CircuitBreaker:
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

    def __init__(self, failure_threshold: int = 5, timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = self.CLOSED

    async def call(self, func: callable, *args, **kwargs):
        if self.state == self.OPEN:
            if time.time() - self.last_failure_time > self.timeout:
                self.state = self.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise e

    def on_success(self):
        self.failure_count = 0
        self.state = self.CLOSED

    def on_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = self.OPEN

class Fallback:
    def __init__(self):
        self.cache = {{}}

    def get_cached_value(self, key: str, default_value=None):
        return self.cache.get(key, default_value)

    def set_cached_value(self, key: str, value, timeout: int = 300):
        self.cache[key] = {{
            'value': value,
            'expires_at': time.time() + timeout
        }}

    def is_expired(self, key: str) -> bool:
        if key not in self.cache:
            return True
        expires_at = self.cache[key].get('expires_at', 0)
        return time.time() > expires_at

    def use_stale_data(self, key: str):
        if key in self.cache and not self.is_expired(key):
            return self.cache[key]['value']
        return None
"""


def generate_error_recovery(framework: str) -> Dict[str, str]:
    """
    Generate error recovery code.

    Args:
        framework: django or fastapi

    Returns: dict of {filename: code_content}
    """
    config = RetryConfig()
    recovery = ErrorRecovery(config)
    output = {}

    if framework == "django":
        output["error_recovery.py"] = recovery.generate_django()
    elif framework == "fastapi":
        output["error_recovery.py"] = recovery.generate_fastapi()

    return output
