#!/usr/bin/env python3
"""
Phase 5 Microservices: Advanced Rate Limiting

Rate Limiting: Control request flow.

Problem: Too many requests
- DDoS attack: 1M requests/second
- Internal client bug: sending 100 requests/second instead of 1
- User clicks button 10 times quickly
- System overloaded

Solution: Rate limiting
- Allow: 100 requests/second
- Block: requests beyond limit
- Return: 429 Too Many Requests

Strategies:
- Token bucket: smooth traffic
- Leaky bucket: strict limit
- Sliding window: accurate
- Fixed window: simple
"""

from typing import Dict, Optional
from datetime import datetime, timedelta


def generate_token_bucket() -> str:
    """Generate token bucket algorithm."""

    tb = '''
class TokenBucket:
    """
    Token Bucket: Smooth rate limiting.

    Bucket holds tokens:
    - Start: 100 tokens
    - Request: costs 1 token
    - Refill: 10 tokens/second
    - Burst: can use up to 100 tokens (smooth spike)
    """

    def __init__(self, capacity: int = 100, refill_rate: float = 10.0):
        self._capacity = capacity
        self._refill_rate = refill_rate
        self._tokens = capacity
        self._last_refill = datetime.utcnow()

    def allow_request(self, tokens: int = 1) -> bool:
        """Check if request allowed"""
        self._refill_tokens()

        if self._tokens >= tokens:
            self._tokens -= tokens
            return True

        return False

    def _refill_tokens(self) -> None:
        """Add tokens based on time elapsed"""
        now = datetime.utcnow()
        elapsed = (now - self._last_refill).total_seconds()
        tokens_to_add = elapsed * self._refill_rate

        self._tokens = min(self._capacity, self._tokens + tokens_to_add)
        self._last_refill = now

    def get_available_tokens(self) -> int:
        """Get current token count"""
        self._refill_tokens()
        return int(self._tokens)
'''

    return tb


def generate_rate_limit_strategies() -> str:
    """Generate rate limiting strategies."""

    strategies = '''
class RateLimitStrategies:
    """
    Different rate limiting strategies.

    1. GLOBAL
       - All users share limit
       - Total: 10k requests/sec

    2. PER-USER
       - Each user: 100 requests/sec
       - User A maxes out doesn't affect User B

    3. PER-IP
       - Each IP: 1000 requests/sec
       - Protects against single client attack

    4. TIERED
       - Free tier: 100 requests/hour
       - Pro tier: 1M requests/day
       - Enterprise tier: unlimited

    5. DYNAMIC
       - Normal: 100 requests/sec
       - High load: 50 requests/sec (reduce)
       - Low load: 200 requests/sec (allow burst)
    """

    def __init__(self):
        self._buckets = {}  # user_id → TokenBucket
        self._tier_limits = {
            "free": 100,  # requests/hour
            "pro": 10000,
            "enterprise": float('inf')
        }

    def get_bucket_for_user(self, user_id: str, tier: str = "free") -> TokenBucket:
        """Get rate limit bucket for user"""
        if user_id not in self._buckets:
            limit = self._tier_limits.get(tier, 100)
            self._buckets[user_id] = TokenBucket(capacity=limit, refill_rate=limit/3600)

        return self._buckets[user_id]

    def allow_request(self, user_id: str, tier: str = "free") -> bool:
        """Check if user can make request"""
        bucket = self.get_bucket_for_user(user_id, tier)
        return bucket.allow_request()

    def get_remaining(self, user_id: str, tier: str = "free") -> int:
        """Get remaining requests for user"""
        bucket = self.get_bucket_for_user(user_id, tier)
        return bucket.get_available_tokens()
'''

    return strategies


def generate_rate_limit_system() -> dict:
    """Generate complete rate limiting system."""

    imports = '''from typing import Dict, Optional
from datetime import datetime, timedelta


'''

    module_doc = '''"""
Phase 5 Rate Limiting: Request Control

Protect APIs from abuse (DDoS, bugs, spikes).

SCENARIOS:

1. DDOS ATTACK
   - Attacker sends 1M requests/sec
   - Rate limiter: allow 10k requests/sec
   - Drop: 990k requests/sec
   - Service: stays up

2. CLIENT BUG
   - User clicks button
   - Client bug: sends 100 requests instead of 1
   - Rate limiter: allow 10/sec
   - Drop: 90 requests
   - Server: protected

3. TRAFFIC SPIKE
   - Normal: 1000 requests/sec
   - Promotion: 5000 requests/sec
   - Capacity: 2000 requests/sec
   - Rate limiter: queue excess, return 429
   - Allow: slow gradual increase

ALGORITHM: TOKEN BUCKET

- Bucket: 100 tokens
- Refill: 10 tokens/second
- Request: costs 1 token

Time 0s: 100 tokens, request → 99 tokens
Time 0.1s: request → 98 tokens
Time 0.5s: refill 5 tokens → 103 (capped at 100)

Benefits:
- Smooth traffic
- Allows small bursts
- Simple to implement

RESPONSE: 429 Too Many Requests

GET /api/products
→ Rate limiter: check tokens
→ No tokens available
→ 429 Too Many Requests
→ Retry-After: 60 (wait 60 seconds)

CLIENT SHOULD:
- Respect 429 status
- Respect Retry-After header
- Implement exponential backoff
- Don't retry immediately

TIERED LIMITS:

Free tier:
- 100 requests/hour
- Suitable for development

Pro tier:
- 1M requests/day
- Suitable for small apps

Enterprise tier:
- Unlimited
- Custom SLAs
"""
'''

    tb = generate_token_bucket()
    strategies = generate_rate_limit_strategies()

    complete_code = imports + module_doc + "\n" + tb + "\n" + strategies

    return {
        "code": complete_code,
        "pattern": "Advanced Rate Limiting",
        "module": "phase5_rate_limiting_advanced.py"
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate rate limiting system")
    args = parser.parse_args()
    result = generate_rate_limit_system()
    print(result["code"])


if __name__ == "__main__":
    main()
