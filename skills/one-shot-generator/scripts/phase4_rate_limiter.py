#!/usr/bin/env python3
"""
Phase 4 Rate Limiter

Prevents abuse and protects system capacity.

Why rate limit?
- API abuse: 1000 requests/second from attacker
- Runaway jobs: code looping, hammering database
- Fair allocation: each user gets fair share

Strategies:
1. Token bucket: smooth rate, allows bursts
2. Sliding window: precise per-second/per-minute
3. Fixed window: simple, efficient

Usage:
    python phase4_rate_limiter.py --strategy token-bucket

Input: Rate limiting strategy
Output: Rate limiter implementation
"""

import argparse
import json
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime, timedelta


def generate_token_bucket() -> str:
    """Generate token bucket rate limiter."""

    bucket = '''
class TokenBucket:
    """
    Token bucket rate limiter.

    Concept:
    - Bucket holds tokens
    - Each request costs 1 token
    - Tokens refill at rate (e.g., 100 tokens/minute)
    - Allows bursts (full bucket)
    - Smooth rate over time

    Configuration:
    - capacity: max tokens in bucket
    - refill_rate: tokens per second
    """

    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = datetime.utcnow()

    def allow_request(self, tokens: int = 1) -> bool:
        """Check if request is allowed"""
        self._refill()

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True

        return False

    def _refill(self) -> None:
        """Refill tokens"""
        now = datetime.utcnow()
        elapsed = (now - self.last_refill).total_seconds()

        new_tokens = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_refill = now

    def get_remaining(self) -> int:
        """Get remaining tokens"""
        self._refill()
        return int(self.tokens)
'''

    return bucket


def generate_rate_limiter() -> str:
    """Generate rate limiter registry."""

    limiter = '''
class RateLimiter:
    """Rate limiter with per-user limits"""

    def __init__(self):
        self._limiters = {}  # user_id → TokenBucket

    def check_limit(
        self,
        user_id: str,
        capacity: int,
        refill_rate: float
    ) -> bool:
        """Check if user is within rate limit"""
        if user_id not in self._limiters:
            self._limiters[user_id] = TokenBucket(capacity, refill_rate)

        bucket = self._limiters[user_id]
        return bucket.allow_request()

    def get_limit_status(self, user_id: str) -> Optional[Dict]:
        """Get rate limit status"""
        if user_id not in self._limiters:
            return None

        bucket = self._limiters[user_id]
        return {
            "user": user_id,
            "remaining": bucket.get_remaining(),
            "capacity": bucket.capacity
        }
'''

    return limiter


def generate_audit_logger() -> str:
    """Generate audit logger."""

    audit = '''
class AuditLogger:
    """
    Audit log: compliance and debugging.

    Logs:
    - Who did what
    - When it happened
    - Result (success/failure)
    - Context (IP, user agent, etc)
    - Changes made

    Why?
    - Compliance: prove who changed what
    - Debugging: understand what happened
    - Security: detect suspicious activity
    - Accountability: track user actions
    """

    def __init__(self, log_store):
        self.store = log_store

    def log_action(
        self,
        user_id: str,
        action: str,
        resource: str,
        result: str = "success",
        details: Optional[Dict] = None
    ) -> None:
        """Log action"""
        entry = {
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "result": result,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details or {}
        }

        self.store.append(entry)

    def get_user_actions(self, user_id: str) -> List[Dict]:
        """Get all actions by user"""
        return self.store.query_by_user(user_id)

    def get_resource_history(self, resource: str) -> List[Dict]:
        """Get all actions on resource"""
        return self.store.query_by_resource(resource)

    def get_actions_in_range(self, start: datetime, end: datetime) -> List[Dict]:
        """Get actions in time range"""
        return self.store.query_by_date_range(start, end)
'''

    return audit


def generate_rate_limit_system() -> dict:
    """Generate complete rate limiter system."""

    imports = '''from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta


'''

    module_doc = '''"""
Rate Limiting and Audit Logging

Control request rates and maintain compliance logs.

RATE LIMITING:

Why?
- Prevent abuse (1000 req/s attack)
- Protect capacity (fair sharing)
- Cost control (limit API usage)

Token Bucket Strategy:
- Bucket has N tokens
- Each request costs 1 token
- Tokens refill at rate R per second
- Allows bursts (full bucket = many requests)
- Smooth over time (prevents hammering)

Example: 100 requests per minute
- Capacity: 100 tokens
- Refill rate: 100/60 = 1.67 tokens/second

User makes 100 requests instantly:
- Allowed (bucket full)
- Tokens → 0
- Then: must wait 60 seconds for refill

User makes 2 requests/second steadily:
- Allowed (bucket refills 1.67/sec, using 2/sec)
- Smooth operation, no waiting

AUDIT LOGGING:

Why?
- Compliance: prove what changed
- Security: detect anomalies
- Debugging: understand what happened
- Accountability: track user actions

What to log:
- User: who did it
- Action: what they did (create, update, delete)
- Resource: what they modified
- Timestamp: when
- Result: success/failure
- Context: IP, user agent, etc

Example log:
{
    "user_id": "alice@example.com",
    "action": "DELETE",
    "resource": "Order #123",
    "timestamp": "2026-05-16T14:30:00",
    "result": "success",
    "details": {
        "ip": "192.168.1.1",
        "reason": "Customer requested cancellation"
    }
}
"""
'''

    bucket = generate_token_bucket()
    limiter = generate_rate_limiter()
    audit = generate_audit_logger()

    complete_code = imports + module_doc + "\n" + bucket + "\n" + limiter + "\n" + audit

    return {
        "code": complete_code,
        "pattern": "Rate Limiter + Audit Logger",
        "module": "rate_limiter.py",
    }


def main():
    parser = argparse.ArgumentParser(description="Generate rate limiter")
    parser.add_argument("--strategy", help="Rate limiting strategy")
    parser.add_argument("--output", choices=["json", "code"], default="code")

    args = parser.parse_args()
    result = generate_rate_limit_system()

    if args.output == "json":
        metadata = {k: v for k, v in result.items() if k != "code"}
        print(json.dumps(metadata, indent=2))
    else:
        print(result["code"])


if __name__ == "__main__":
    main()
