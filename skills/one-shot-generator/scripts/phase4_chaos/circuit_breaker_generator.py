#!/usr/bin/env python3
"""Circuit Breaker Generator - Resilience Patterns

Generates:
- Circuit breakers (fail-fast when service down)
- Bulkheads (isolate failures)
- Rate limiters (prevent cascading failures)
- Fallback patterns (graceful degradation)
"""

import sys
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.base_script import setup_logging, timed_run, check_budget

__version__ = "0.7.0"
logger = setup_logging(__name__)


class CircuitBreakerGenerator:
    """Generates circuit breaker and resilience patterns."""

    def __init__(self, framework: str):
        self.framework = framework.lower()

    def generate(self) -> Dict[str, str]:
        files = {}
        files['resilience/circuit_breaker.py'] = self._circuit_breaker()
        files['resilience/bulkhead.py'] = self._bulkhead()
        files['resilience/rate_limiter.py'] = self._rate_limiter()
        files['resilience/fallback.py'] = self._fallback()
        files['resilience/config.py'] = self._config()
        files['resilience/README.md'] = self._readme()
        return files

    def _circuit_breaker(self) -> str:
        return '''"""Circuit Breaker Pattern - Fail Fast When Service Down"""

import logging
import time
from enum import Enum
from typing import Callable, Any
from functools import wraps
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"      # Working normally
    OPEN = "open"          # Service down, reject calls
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """Circuit breaker for service calls"""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout_seconds: int = 60,
        success_threshold_half_open: int = 2,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self.success_threshold_half_open = success_threshold_half_open

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker: Attempting to recover")
            else:
                raise CircuitBreakerOpen(f"Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0

        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold_half_open:
                self.state = CircuitState.CLOSED
                self.success_count = 0
                logger.info("Circuit breaker: CLOSED (service recovered)")

    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.error(
                f"Circuit breaker: OPEN (failures: {self.failure_count})"
            )

        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            self.success_count = 0
            logger.warning("Circuit breaker: Reopened (half-open failed)")

    def _should_attempt_reset(self) -> bool:
        """Check if enough time passed to attempt recovery"""
        if not self.last_failure_time:
            return True
        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return elapsed >= self.recovery_timeout_seconds

    def decorator(self, func: Callable) -> Callable:
        """Decorator to protect function calls"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            return self.call(func, *args, **kwargs)
        return wrapper

    def get_state(self) -> str:
        """Get current circuit state"""
        return self.state.value


class CircuitBreakerOpen(Exception):
    """Circuit breaker is open"""
    pass
'''

    def _bulkhead(self) -> str:
        return '''"""Bulkhead Pattern - Isolate Failures to Prevent Cascading"""

import logging
from threading import Semaphore
from typing import Callable, Any
from functools import wraps

logger = logging.getLogger(__name__)


class Bulkhead:
    """Bulkhead isolation for resource pools"""

    def __init__(self, max_concurrent_calls: int = 10, pool_name: str = "default"):
        self.max_concurrent_calls = max_concurrent_calls
        self.pool_name = pool_name
        self.semaphore = Semaphore(max_concurrent_calls)
        self.active_count = 0

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with bulkhead isolation"""
        if not self.semaphore.acquire(blocking=False):
            raise BulkheadFull(
                f"Bulkhead {self.pool_name} full ({self.active_count}/{self.max_concurrent_calls})"
            )

        try:
            self.active_count += 1
            logger.debug(f"Bulkhead {self.pool_name}: {self.active_count} active")
            return func(*args, **kwargs)
        finally:
            self.active_count -= 1
            self.semaphore.release()

    def decorator(self, func: Callable) -> Callable:
        """Decorator to protect function calls"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            return self.call(func, *args, **kwargs)
        return wrapper

    def get_metrics(self) -> dict:
        """Get bulkhead metrics"""
        return {
            "pool_name": self.pool_name,
            "max_concurrent_calls": self.max_concurrent_calls,
            "active_count": self.active_count,
            "available_slots": self.max_concurrent_calls - self.active_count,
        }


class BulkheadFull(Exception):
    """Bulkhead is full"""
    pass
'''

    def _rate_limiter(self) -> str:
        return '''"""Rate Limiter - Control Request Rate"""

import logging
import time
from collections import deque
from typing import Callable, Any
from functools import wraps

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter"""

    def __init__(self, rate_per_second: float, name: str = "default"):
        self.rate_per_second = rate_per_second
        self.name = name
        self.tokens = rate_per_second
        self.last_update = time.time()
        self.rejected_count = 0

    def acquire(self, tokens: int = 1) -> bool:
        """Try to acquire tokens"""
        now = time.time()
        elapsed = now - self.last_update
        self.tokens = min(
            self.rate_per_second,
            self.tokens + elapsed * self.rate_per_second
        )
        self.last_update = now

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        else:
            self.rejected_count += 1
            return False

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with rate limiting"""
        if not self.acquire(tokens=1):
            raise RateLimitExceeded(f"Rate limit exceeded for {self.name}")
        return func(*args, **kwargs)

    def decorator(self, func: Callable) -> Callable:
        """Decorator to protect function calls"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            return self.call(func, *args, **kwargs)
        return wrapper

    def get_metrics(self) -> dict:
        """Get rate limiter metrics"""
        return {
            "name": self.name,
            "rate_per_second": self.rate_per_second,
            "available_tokens": self.tokens,
            "rejected_count": self.rejected_count,
        }


class RateLimitExceeded(Exception):
    """Rate limit exceeded"""
    pass
'''

    def _fallback(self) -> str:
        return '''"""Fallback Pattern - Graceful Degradation"""

import logging
from typing import Callable, Any, Optional
from functools import wraps

logger = logging.getLogger(__name__)


class Fallback:
    """Fallback execution when primary fails"""

    def __init__(self, primary: Callable, fallback: Callable):
        self.primary = primary
        self.fallback = fallback

    def execute(self, *args, **kwargs) -> Any:
        """Try primary, fall back to fallback on failure"""
        try:
            logger.debug("Executing primary function")
            return self.primary(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Primary failed: {e}, using fallback")
            try:
                return self.fallback(*args, **kwargs)
            except Exception as fe:
                logger.error(f"Fallback also failed: {fe}")
                raise

    def decorator(self) -> Callable:
        """Decorator for fallback execution"""
        def decorator_wrapper(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                return self.execute(*args, **kwargs)
            return wrapper
        return decorator_wrapper


class FallbackChain:
    """Chain multiple fallbacks"""

    def __init__(self, strategies: list):
        self.strategies = strategies  # List of callables

    def execute(self, *args, **kwargs) -> Any:
        """Try each strategy in order"""
        last_error = None
        for i, strategy in enumerate(self.strategies):
            try:
                logger.debug(f"Trying strategy {i+1}/{len(self.strategies)}")
                return strategy(*args, **kwargs)
            except Exception as e:
                last_error = e
                logger.warning(f"Strategy {i+1} failed: {e}")
                continue

        logger.error("All fallback strategies exhausted")
        raise last_error


def fallback_value(default_value: Any) -> Callable:
    """Return default value on error"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Function failed, returning default: {e}")
                return default_value
        return wrapper
    return decorator
'''

    def _config(self) -> str:
        return '''"""Resilience Configuration"""

RESILIENCE_CONFIG = {
    "circuit_breaker": {
        "failure_threshold": 5,
        "recovery_timeout_seconds": 60,
        "success_threshold_half_open": 2,
    },
    "bulkhead": {
        "max_concurrent_calls": 10,
        "pools": {
            "database": 5,
            "api": 20,
            "cache": 50,
        }
    },
    "rate_limiter": {
        "enabled": True,
        "default_rate_per_second": 100,
        "limits": {
            "external_api": 10,
            "database": 500,
            "cache": 1000,
        }
    },
    "fallback": {
        "enabled": True,
        "default_return_value": None,
    }
}
'''

    def _readme(self) -> str:
        return '''# Resilience Patterns - Circuit Breaker, Bulkhead, Rate Limiting

## Circuit Breaker

Fail fast when a service is down:

```python
from resilience.circuit_breaker import CircuitBreaker

breaker = CircuitBreaker(failure_threshold=5, recovery_timeout_seconds=60)

@breaker.decorator
def call_external_api():
    return requests.get('https://api.example.com/data')
```

States:
- **CLOSED**: Normal operation
- **OPEN**: Service down, reject calls
- **HALF_OPEN**: Testing if service recovered

## Bulkhead

Isolate failures to prevent cascading:

```python
from resilience.bulkhead import Bulkhead

bulkhead = Bulkhead(max_concurrent_calls=10, pool_name="database")

@bulkhead.decorator
def database_query(sql):
    return db.execute(sql)
```

Prevents one slow/failing service from exhausting all resources.

## Rate Limiter

Control request rate to prevent cascading failures:

```python
from resilience.rate_limiter import RateLimiter

limiter = RateLimiter(rate_per_second=100, name="api")

@limiter.decorator
def api_request():
    return requests.get('https://api.example.com')
```

Token bucket algorithm: earn tokens over time, spend 1 per request.

## Fallback

Graceful degradation when primary fails:

```python
from resilience.fallback import Fallback

primary = lambda: requests.get('https://api.example.com')
fallback = lambda: {"cached": True, "data": []}

fallback_call = Fallback(primary, fallback)
result = fallback_call.execute()
```

## Combined Example

```python
breaker = CircuitBreaker(failure_threshold=5)
bulkhead = Bulkhead(max_concurrent_calls=10)
limiter = RateLimiter(rate_per_second=100)

@limiter.decorator
@bulkhead.decorator
@breaker.decorator
def resilient_call():
    return requests.get('https://api.example.com')
```

All patterns working together = resilient system.

## Metrics

All patterns expose metrics:

```python
print(breaker.get_state())
print(bulkhead.get_metrics())
print(limiter.get_metrics())
```

Monitor these to detect degradation early.
'''


def main():
    with timed_run("circuit_breaker_generator") as timer:
        logger.debug("Testing Circuit Breaker generation")
        gen = CircuitBreakerGenerator("python")
        files = gen.generate()
        logger.debug(f"Generated {len(files)} files")
        for filepath in files:
            print(f"  ✓ {filepath}")
        check_budget("circuit_breaker_generator", timer.elapsed_ms, logger)


if __name__ == '__main__':
    main()
