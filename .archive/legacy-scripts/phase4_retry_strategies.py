#!/usr/bin/env python3
"""
Phase 4 Retry Strategies

Reliable operations with smart retries.

Problems:
- Network glitch: request fails once, succeeds on retry
- Temporary outage: service down for 5 minutes, then recovers
- Rate limit: API rate-limited, but OK after waiting

Bad retry:
def call_api(url):
    for i in range(3):
        try:
            return requests.get(url)
        except:
            pass  # Retry immediately
Result: hammers API when down, no backoff

Good retry:
- Exponential backoff: 1s, 2s, 4s, 8s...
- Jitter: randomize to avoid thundering herd
- Max retries: don't retry forever
- Circuit breaker: stop if persistently failing
- Idempotency: safe to retry

Strategies:
1. Fixed delay (2s, 2s, 2s)
2. Linear backoff (1s, 2s, 3s)
3. Exponential backoff (1s, 2s, 4s, 8s)
4. With jitter (randomize)

Usage:
    python phase4_retry_strategies.py --strategy exponential

Input: Retry strategy type
Output: Retry implementation with backoff and idempotency
"""

import argparse
import json
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime, timedelta
import random
import time


def generate_retry_policy() -> str:
    """Generate retry policy."""

    policy = '''
class RetryPolicy:
    """
    Retry policy configuration.

    Parameters:
    - max_retries: Maximum retry attempts
    - backoff_strategy: how to delay between retries
    - jitter: randomize delay to avoid thundering herd
    - timeout: overall timeout for all retries
    - retryable_exceptions: which exceptions to retry on
    """

    def __init__(
        self,
        max_retries: int = 3,
        backoff_strategy: str = "exponential",
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        jitter: bool = True,
        timeout: Optional[float] = None,
        retryable_exceptions: Optional[list] = None
    ):
        self.max_retries = max_retries
        self.backoff_strategy = backoff_strategy
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.jitter = jitter
        self.timeout = timeout
        self.retryable_exceptions = retryable_exceptions or [Exception]
        self.start_time = None

    def should_retry(self, attempt: int, exception: Exception) -> bool:
        """Check if should retry"""
        # Check max retries
        if attempt >= self.max_retries:
            return False

        # Check if retryable exception
        if not any(isinstance(exception, exc) for exc in self.retryable_exceptions):
            return False

        # Check overall timeout
        if self.timeout and self.start_time:
            elapsed = (datetime.utcnow() - self.start_time).total_seconds()
            if elapsed > self.timeout:
                return False

        return True

    def get_delay(self, attempt: int) -> float:
        """Get delay before next retry"""
        if self.backoff_strategy == "fixed":
            delay = self.initial_delay
        elif self.backoff_strategy == "linear":
            delay = self.initial_delay * (attempt + 1)
        elif self.backoff_strategy == "exponential":
            delay = self.initial_delay * (2 ** attempt)
        else:
            delay = self.initial_delay

        # Cap delay
        delay = min(delay, self.max_delay)

        # Add jitter
        if self.jitter:
            jitter_amount = random.uniform(0, delay * 0.1)
            delay += jitter_amount

        return delay
'''

    return policy


def generate_retry_executor() -> str:
    """Generate retry executor."""

    executor = '''
class RetryExecutor:
    """
    Executes operations with retries.

    Handles:
    - Retry logic
    - Delay calculation
    - Exception handling
    - Metrics tracking
    """

    def __init__(self, policy: RetryPolicy):
        self.policy = policy
        self.metrics = {
            "total_attempts": 0,
            "successful_retries": 0,  # Succeeded after failure
            "failed_after_retries": 0
        }

    def execute(self, fn: Callable, *args, **kwargs) -> Any:
        """
        Execute function with retries.

        Returns result on success.
        Raises exception on all retries exhausted.
        """
        self.policy.start_time = datetime.utcnow()
        last_exception = None

        for attempt in range(self.policy.max_retries + 1):
            self.metrics["total_attempts"] += 1

            try:
                result = fn(*args, **kwargs)

                # Success!
                if attempt > 0:
                    self.metrics["successful_retries"] += 1

                return result

            except Exception as e:
                last_exception = e

                if self.policy.should_retry(attempt, e):
                    delay = self.policy.get_delay(attempt)
                    time.sleep(delay)
                else:
                    self.metrics["failed_after_retries"] += 1
                    raise

        # Should not reach here
        raise last_exception

    def execute_async(
        self,
        fn: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Async-friendly version (use with asyncio)"""
        # Implementation for async/await
        return self.execute(fn, *args, **kwargs)

    def get_metrics(self) -> Dict:
        """Get retry metrics"""
        return self.metrics.copy()
'''

    return executor


def generate_idempotent_retry() -> str:
    """Generate idempotent retry."""

    idempotent = '''
class IdempotentRetry:
    """
    Retry with idempotency guarantee.

    Idempotency: calling twice = calling once
    Example: Refund($100) twice = refund once (not $200)

    How:
    1. Generate idempotency key (unique per operation)
    2. Store: idempotency_key → result
    3. On retry: check if already processed
    4. If yes: return cached result
    5. If no: execute and cache

    Solves:
    - Duplicate operations (payment charged twice)
    - Retries are always safe
    """

    def __init__(self, idempotency_store):
        self.store = idempotency_store

    def execute(
        self,
        idempotency_key: str,
        fn: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute with idempotency.

        Args:
            idempotency_key: Unique key for this operation
            fn: Function to execute
            args, kwargs: Arguments to function

        Returns:
            Result (either fresh or cached)
        """
        # Check if already processed
        cached = self.store.get(idempotency_key)
        if cached:
            return cached

        # Not processed, execute
        result = fn(*args, **kwargs)

        # Cache result
        self.store.set(idempotency_key, result)

        return result

    def is_processed(self, idempotency_key: str) -> bool:
        """Check if operation already processed"""
        return self.store.get(idempotency_key) is not None
'''

    return idempotent


def generate_retry_backoff_examples() -> str:
    """Generate backoff examples."""

    examples = '''
# Retry Strategy Examples

# 1. Fixed Delay (simple but ineffective)
policy = RetryPolicy(
    max_retries=3,
    backoff_strategy="fixed",
    initial_delay=2.0  # Always wait 2s
)
# Delays: 2s, 2s, 2s
# Use: for fast operations where API might be briefly down

# 2. Linear Backoff (growing)
policy = RetryPolicy(
    max_retries=5,
    backoff_strategy="linear",
    initial_delay=1.0  # Start with 1s
)
# Delays: 1s, 2s, 3s, 4s, 5s
# Use: moderate growth, good for API rate limits

# 3. Exponential Backoff with Jitter (recommended)
policy = RetryPolicy(
    max_retries=5,
    backoff_strategy="exponential",
    initial_delay=1.0,
    max_delay=60.0,
    jitter=True  # Add randomness
)
# Delays: 1.0s ±10%, 2.0s ±10%, 4.0s ±10%, 8.0s ±10%, 16.0s ±10%
# Use: production, especially for distributed systems

# 4. With timeout
policy = RetryPolicy(
    max_retries=10,
    backoff_strategy="exponential",
    initial_delay=1.0,
    timeout=120.0  # Give up after 2 minutes total
)

# 5. Only retry specific exceptions
from requests.exceptions import ConnectionError, Timeout

policy = RetryPolicy(
    max_retries=3,
    retryable_exceptions=[ConnectionError, Timeout],
    backoff_strategy="exponential"
)
# Don't retry on HTTP 400 (bad request)
# Do retry on ConnectionError, Timeout

# Usage:
executor = RetryExecutor(policy)

try:
    result = executor.execute(api.call_payment, amount=100)
    print(f"Success: {result}")
except Exception as e:
    print(f"Failed after retries: {e}")

print(executor.get_metrics())
# {
#     "total_attempts": 3,
#     "successful_retries": 1,  # Succeeded on 2nd try
#     "failed_after_retries": 0
# }
'''

    return examples


def generate_retry_system() -> dict:
    """Generate complete retry system."""

    imports = '''import random
import time
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime, timedelta


'''

    module_doc = '''"""
Retry Strategies with Backoff

Reliable operations with smart retries.

Problem: Unreliable networks

When API fails:
- Network glitch
- Temporary outage
- Rate limited

Solution: Retry with backoff

Bad approach:
- Retry immediately (hammers API when down)
- Retry forever (user waits forever)
- Same request twice (duplicate charge!)

Good approach:
- Wait before retry (exponential backoff)
- Limit retries (give up eventually)
- Idempotency key (safe to retry)

Backoff strategies:

1. FIXED DELAY: 2s, 2s, 2s
   When: never (too predictable)

2. LINEAR: 1s, 2s, 3s, 4s, 5s
   When: moderate growth

3. EXPONENTIAL: 1s, 2s, 4s, 8s, 16s, 32s (recommended)
   When: production (good balance)

4. WITH JITTER: 1s ±10%, 2s ±10%, 4s ±10%
   When: distributed systems (prevents thundering herd)

Thundering Herd:
- All clients retry at same time
- Retry timing: 1s, 2s, 3s, 4s (synchronized!)
- All hit server at once → overload
- Solution: Add jitter (randomize)
- Retry timing: 0.9s, 1.8s, 3.7s, 4.2s (randomized)
- Spread load over time

Idempotency:
- Charge($100)
- Network fails
- Retry: Charge($100)
- Without idempotency: $200 charged!
- With idempotency key: $100 charged once

Implementation:
1. Generate unique key for operation
2. Store: key → result
3. On retry: check if already done
4. If yes: return cached result
5. If no: execute and cache

Idempotency key format:
- Customer + operation type + timestamp
- Example: customer-123_charge_2026-05-16T12:00:00Z
"""
'''

    policy = generate_retry_policy()
    executor = generate_retry_executor()
    idempotent = generate_idempotent_retry()
    examples = generate_retry_backoff_examples()

    complete_code = imports + module_doc + "\n" + policy + "\n" + executor + "\n" + idempotent + "\n" + examples

    return {
        "code": complete_code,
        "pattern": "Retry Strategies",
        "module": "retry_strategies.py",
    }


def main():
    parser = argparse.ArgumentParser(description="Generate retry strategies")
    parser.add_argument("--strategy", help="Retry strategy")
    parser.add_argument("--output", choices=["json", "code"], default="code")

    args = parser.parse_args()
    result = generate_retry_system()

    if args.output == "json":
        metadata = {k: v for k, v in result.items() if k != "code"}
        print(json.dumps(metadata, indent=2))
    else:
        print(result["code"])


if __name__ == "__main__":
    main()
