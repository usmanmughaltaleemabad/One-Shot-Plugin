#!/usr/bin/env python3
"""
Phase 5 Microservices: Resilience Patterns

Resilience: System continues working even when parts fail.

Failure scenarios:
- Service B is down → Service A continues (fails gracefully)
- Service B is slow → Service A times out, retries
- Service B is overwhelmed → Service A backs off (exponential backoff)
- Service B fails partially → Service A uses fallback response

Patterns:
- Circuit Breaker: Stop calling broken service
- Timeout: Don't wait forever
- Retry: Try again with backoff
- Fallback: Return default if service fails
- Bulkhead: Isolate failure (don't bring down whole system)
"""

from typing import Dict, Optional, Callable
from datetime import datetime, timedelta


def generate_circuit_breaker_advanced() -> str:
    """Generate advanced circuit breaker."""

    cb = '''
class CircuitBreaker:
    """
    Stop calling service that's failing.

    States:
    - CLOSED: Normal operation, requests flow
    - OPEN: Service failing, stop requests
    - HALF_OPEN: Service recovering? Try one request

    Transitions:
    CLOSED →(failures > threshold)→ OPEN
    OPEN →(timeout)→ HALF_OPEN
    HALF_OPEN →(success)→ CLOSED
    HALF_OPEN →(failure)→ OPEN
    """

    def __init__(self, name: str, failure_threshold: int = 5, timeout_seconds: int = 30):
        self.name = name
        self._state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self._failure_count = 0
        self._failure_threshold = failure_threshold
        self._timeout = timedelta(seconds=timeout_seconds)
        self._opened_at = None
        self._last_request = None

    def call(self, func: Callable, *args, **kwargs):
        """Execute function through circuit breaker"""
        if self._state == "OPEN":
            if self._should_attempt_reset():
                self._state = "HALF_OPEN"
            else:
                raise Exception(f"Circuit {self.name} is OPEN")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if timeout expired"""
        if not self._opened_at:
            return False
        return datetime.utcnow() - self._opened_at > self._timeout

    def _on_success(self):
        """Handle successful request"""
        self._failure_count = 0
        if self._state == "HALF_OPEN":
            self._state = "CLOSED"

    def _on_failure(self):
        """Handle failed request"""
        self._failure_count += 1
        if self._failure_count >= self._failure_threshold:
            self._state = "OPEN"
            self._opened_at = datetime.utcnow()

    def get_state(self) -> str:
        """Get current state"""
        return self._state
'''

    return cb


def generate_resilience_utils() -> str:
    """Generate resilience utilities."""

    utils = '''
class Timeout:
    """Timeout: Don't wait forever for response"""

    def __init__(self, seconds: float):
        self.seconds = seconds

    def __call__(self, func: Callable) -> any:
        """Decorator: timeout function execution"""
        import signal

        def handler(signum, frame):
            raise TimeoutError(f"Timed out after {self.seconds}s")

        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, handler)
            signal.alarm(int(self.seconds))
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result

        return wrapper


class ExponentialBackoff:
    """Retry with exponential backoff: 100ms, 200ms, 400ms, 800ms"""

    def __init__(self, initial_delay_ms: float = 100, max_delay_ms: float = 30000):
        self.initial_delay = initial_delay_ms / 1000
        self.max_delay = max_delay_ms / 1000

    def retry(self, func: Callable, max_attempts: int = 5) -> any:
        """Retry function with exponential backoff"""
        import time
        delay = self.initial_delay

        for attempt in range(max_attempts):
            try:
                return func()
            except Exception as e:
                if attempt == max_attempts - 1:
                    raise
                time.sleep(delay)
                delay = min(delay * 2, self.max_delay)


class Bulkhead:
    """Isolate resource pools (thread pools, connection pools)"""

    def __init__(self, name: str, max_concurrent: int = 10):
        self.name = name
        self._max_concurrent = max_concurrent
        self._active_count = 0

    def execute(self, func: Callable, *args, **kwargs) -> any:
        """Execute in isolated resource pool"""
        if self._active_count >= self._max_concurrent:
            raise Exception(f"Bulkhead {self.name} at capacity")

        self._active_count += 1
        try:
            return func(*args, **kwargs)
        finally:
            self._active_count -= 1
'''

    return utils


def generate_resilience_system() -> dict:
    """Generate complete resilience system."""

    imports = '''from typing import Dict, Optional, Callable
from datetime import datetime, timedelta


'''

    module_doc = '''"""
Phase 5 Resilience Patterns: Fault Tolerance

Build systems that work even when things fail.

PATTERN: CIRCUIT BREAKER

Problem:
- UserService calls PaymentService
- PaymentService is down
- UserService waits 30s, times out
- User sees error
- After recovery: UserService still tries calling PaymentService
- More timeouts, more failures

Solution: Circuit breaker

CLOSED (normal):
- Requests flow: UserService → PaymentService
- Working fine

OPEN (failure detected):
- 5 requests fail
- Circuit opens
- UserService doesn't call PaymentService anymore
- Returns error immediately (fail fast)

HALF_OPEN (testing recovery):
- After 30s: circuit goes to HALF_OPEN
- Try one request to PaymentService
- If succeeds: circuit closes, resume normal
- If fails: circuit opens again

PATTERN: RETRY WITH EXPONENTIAL BACKOFF

Problem:
- PaymentService has temporary glitch
- First request fails
- Retry immediately
- 1000 clients retry immediately
- "Thundering herd" overwhelms service

Solution: Exponential backoff with jitter

Retry delays:
- Attempt 1: wait 100ms
- Attempt 2: wait 200ms
- Attempt 3: wait 400ms
- Attempt 4: wait 800ms
- Attempt 5: wait 1600ms

Spreads retries over time, prevents thundering herd

PATTERN: BULKHEAD (Isolation)

Problem:
- One service in trouble
- Consumes all thread pool
- Other services can't run
- Cascading failure

Solution: Isolate resource pools

- UserService: 10 threads
- PaymentService: 10 threads
- ShippingService: 10 threads
- PaymentService fails, consumes 10 threads
- UserService still has 10 threads, keeps running
"""
'''

    cb = generate_circuit_breaker_advanced()
    utils = generate_resilience_utils()

    complete_code = imports + module_doc + "\n" + cb + "\n" + utils

    return {
        "code": complete_code,
        "pattern": "Resilience Patterns",
        "module": "phase5_resilience_patterns.py"
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate resilience patterns")
    args = parser.parse_args()
    result = generate_resilience_system()
    print(result["code"])


if __name__ == "__main__":
    main()
