#!/usr/bin/env python3
"""
Phase 4 Circuit Breaker Pattern

Prevents cascading failures when services are down.

Problem: API unreliable
- Call API
- API times out (30 seconds)
- Cascade: user request takes 30s, server timeout
- Cascades: 100s of waiting requests, queue explodes
- System overload

Solution: Circuit Breaker

States:
1. CLOSED: Normal. Pass requests through.
2. OPEN: Service down. Fail fast (don't call).
3. HALF_OPEN: Service recovering. Test with few requests.

Transitions:
- CLOSED → OPEN: too many failures
- OPEN → HALF_OPEN: timeout reached
- HALF_OPEN → CLOSED: test requests succeed
- HALF_OPEN → OPEN: test requests fail

Benefit: Fail fast, prevent cascades, allow recovery.

Usage:
    python phase4_circuit_breaker.py --service payment-api

Input: Service name
Output: Circuit breaker with monitoring
"""

import argparse
import json
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime, timedelta


def generate_circuit_breaker() -> str:
    """Generate circuit breaker."""

    breaker = '''
class CircuitBreaker:
    """
    Circuit breaker for resilient API calls.

    States: CLOSED → OPEN → HALF_OPEN → CLOSED

    Configuration:
    - failure_threshold: failures before OPEN (e.g., 5)
    - success_threshold: successes before CLOSED (e.g., 2)
    - timeout: duration in OPEN before trying HALF_OPEN (e.g., 60s)
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout_seconds: int = 60
    ):
        self.name = name
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.failure_count = 0
        self.success_count = 0
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timedelta(seconds=timeout_seconds)
        self.opened_at = None
        self.last_failure_at = None
        self.metrics = {
            "total_calls": 0,
            "total_failures": 0,
            "total_successes": 0
        }

    def call(self, fn: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker.

        If OPEN: fail fast (don't call)
        If CLOSED/HALF_OPEN: call function
        """
        self.metrics["total_calls"] += 1

        # Check if should transition to HALF_OPEN
        if self.state == "OPEN":
            if datetime.utcnow() > self.opened_at + self.timeout:
                self.state = "HALF_OPEN"
                self.success_count = 0
            else:
                # Still open, fail fast
                raise CircuitBreakerOpenException(
                    f"Circuit breaker '{self.name}' is OPEN"
                )

        # Call function
        try:
            result = fn(*args, **kwargs)
            self._record_success()
            return result
        except Exception as e:
            self._record_failure()
            raise

    def _record_success(self) -> None:
        """Record successful call"""
        self.metrics["total_successes"] += 1
        self.failure_count = 0

        if self.state == "HALF_OPEN":
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                # Recovered, close circuit
                self.state = "CLOSED"
                self.success_count = 0

    def _record_failure(self) -> None:
        """Record failed call"""
        self.metrics["total_failures"] += 1
        self.failure_count += 1
        self.last_failure_at = datetime.utcnow()

        if self.state == "CLOSED":
            if self.failure_count >= self.failure_threshold:
                # Too many failures, open circuit
                self.state = "OPEN"
                self.opened_at = datetime.utcnow()

        elif self.state == "HALF_OPEN":
            # Failure while testing, go back to OPEN
            self.state = "OPEN"
            self.opened_at = datetime.utcnow()

    def get_state(self) -> Dict:
        """Get current state"""
        return {
            "name": self.name,
            "state": self.state,
            "failures": self.failure_count,
            "successes": self.success_count if self.state == "HALF_OPEN" else "N/A",
            "metrics": self.metrics
        }


class CircuitBreakerOpenException(Exception):
    """Circuit breaker is open"""
    pass


class CircuitBreakerRegistry:
    """
    Registry of circuit breakers.

    Manage multiple circuit breakers for different services.
    """

    def __init__(self):
        self._breakers = {}

    def register(
        self,
        service_name: str,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout_seconds: int = 60
    ) -> CircuitBreaker:
        """Register circuit breaker"""
        breaker = CircuitBreaker(
            name=service_name,
            failure_threshold=failure_threshold,
            success_threshold=success_threshold,
            timeout_seconds=timeout_seconds
        )
        self._breakers[service_name] = breaker
        return breaker

    def get(self, service_name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker"""
        return self._breakers.get(service_name)

    def call(self, service_name: str, fn: Callable, *args, **kwargs) -> Any:
        """Call function through circuit breaker"""
        breaker = self.get(service_name)
        if not breaker:
            raise ValueError(f"Unknown service: {service_name}")
        return breaker.call(fn, *args, **kwargs)

    def get_all_states(self) -> List[Dict]:
        """Get all circuit breaker states"""
        return [breaker.get_state() for breaker in self._breakers.values()]

    def get_unhealthy(self) -> List[Dict]:
        """Get all open/half-open breakers"""
        return [
            breaker.get_state()
            for breaker in self._breakers.values()
            if breaker.state != "CLOSED"
        ]
'''

    return breaker


def generate_fallback_strategies() -> str:
    """Generate fallback strategies."""

    fallback = '''
class FallbackStrategy:
    """
    Fallback when circuit is open.

    Options:
    1. Fail: raise exception (default)
    2. Return default value
    3. Use cached value
    4. Use degraded mode
    """

    def __init__(self):
        self.fallback_fn = None
        self.default_value = None
        self.use_cache = False

    def with_fallback_fn(self, fn: Callable) -> "FallbackStrategy":
        """Use function for fallback"""
        self.fallback_fn = fn
        return self

    def with_default_value(self, value: Any) -> "FallbackStrategy":
        """Use default value"""
        self.default_value = value
        return self

    def with_cache_fallback(self) -> "FallbackStrategy":
        """Use cached value as fallback"""
        self.use_cache = True
        return self

    def get_fallback(self) -> Any:
        """Get fallback value"""
        if self.fallback_fn:
            return self.fallback_fn()
        return self.default_value

    def apply_fallback(self, circuit_breaker: CircuitBreaker, fn: Callable, *args, **kwargs) -> Any:
        """Apply fallback if circuit open"""
        try:
            return circuit_breaker.call(fn, *args, **kwargs)
        except CircuitBreakerOpenException:
            return self.get_fallback()
'''

    return fallback


def generate_metrics() -> str:
    """Generate metrics and monitoring."""

    metrics = '''
class CircuitBreakerMetrics:
    """Monitor circuit breaker health"""

    def __init__(self, registry: CircuitBreakerRegistry):
        self.registry = registry

    def health_check(self) -> Dict:
        """Overall health"""
        all_states = self.registry.get_all_states()
        open_count = sum(1 for s in all_states if s["state"] == "OPEN")
        half_open_count = sum(1 for s in all_states if s["state"] == "HALF_OPEN")

        return {
            "healthy": open_count == 0,
            "total_breakers": len(all_states),
            "open_breakers": open_count,
            "half_open_breakers": half_open_count,
            "breakers": all_states
        }

    def get_metrics_report(self) -> Dict:
        """Detailed metrics"""
        all_states = self.registry.get_all_states()

        total_calls = sum(s["metrics"]["total_calls"] for s in all_states)
        total_failures = sum(s["metrics"]["total_failures"] for s in all_states)
        failure_rate = (total_failures / total_calls * 100) if total_calls > 0 else 0

        return {
            "total_calls": total_calls,
            "total_failures": total_failures,
            "failure_rate": failure_rate,
            "breakers": all_states
        }
'''

    return metrics


def generate_breaker_system() -> dict:
    """Generate complete circuit breaker system."""

    imports = '''from typing import Any, Callable, Dict, List, Optional
from datetime import datetime, timedelta


'''

    module_doc = '''"""
Circuit Breaker Pattern

Prevents cascading failures.

Problem: Unreliable API

Normal flow:
1. User request
2. Call API (reliable)
3. Get response
4. Return to user

When API fails:
1. User request
2. Call API (times out after 30s)
3. System waits 30s, timeout
4. User waits 30s, frustrated
5. Cascade: 100s of requests waiting
6. Server overload
7. System down

Solution: Circuit Breaker

States:
CLOSED (normal):
- Requests pass through
- Failures accumulate
- If too many failures → OPEN

OPEN (service down):
- Requests fail immediately (fail fast!)
- No waiting
- No cascades
- After timeout → HALF_OPEN

HALF_OPEN (testing recovery):
- Allow few test requests
- If succeed → CLOSED
- If fail → OPEN

Benefits:
✓ Fail fast (no 30s wait)
✓ Prevent cascades
✓ Allow service recovery
✓ Fast user feedback

Configuration:
- Failure threshold: 5 failures before OPEN
- Success threshold: 2 successes before CLOSED
- Timeout: 60 seconds in OPEN before HALF_OPEN

Example:
breaker = CircuitBreaker("payment-api", failure_threshold=5)

try:
    response = breaker.call(api.charge_payment, amount=100)
except CircuitBreakerOpenException:
    # API down, fail fast
    show_error("Payment service unavailable")
"""
'''

    breaker = generate_circuit_breaker()
    fallback = generate_fallback_strategies()
    metrics = generate_metrics()

    complete_code = imports + module_doc + "\n" + breaker + "\n" + fallback + "\n" + metrics

    return {
        "code": complete_code,
        "pattern": "Circuit Breaker",
        "module": "circuit_breaker.py",
    }


def main():
    parser = argparse.ArgumentParser(description="Generate circuit breaker pattern")
    parser.add_argument("--service", help="Service name")
    parser.add_argument("--output", choices=["json", "code"], default="code")

    args = parser.parse_args()
    result = generate_breaker_system()

    if args.output == "json":
        metadata = {k: v for k, v in result.items() if k != "code"}
        print(json.dumps(metadata, indent=2))
    else:
        print(result["code"])


if __name__ == "__main__":
    main()
