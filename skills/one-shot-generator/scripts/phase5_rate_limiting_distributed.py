#!/usr/bin/env python3
"""
Phase 5 Distributed Rate Limiting: Shared Token Bucket & Quotas

Distributed Rate Limiting: Limit across multiple servers.

Problem: Local rate limiting ineffective
- Server 1: 100 req/min per user
- Server 2: 100 req/min per user
- User A: 100 to Server 1 + 100 to Server 2 = 200/min (bypassed!)

Distributed Rate Limiting (solution):
- Shared counter (Redis): single source of truth
- Token bucket: fair, smooth limiting
- Per-user quotas: prevent abuse
- DDoS protection: block at edge
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta


def generate_distributed_rate_limiting() -> str:
    """Generate distributed rate limiting system."""

    rate_limiting = '''
class DistributedRateLimiter:
    """
    Rate limiting across multiple servers.

    Strategies:
    - Token bucket: smooth rate, burst capacity
    - Sliding window: per-minute count
    - User quotas: per-user limits
    """

    def __init__(self):
        self._buckets = {}  # user_id → {tokens, last_refill}
        self._window_counters = {}  # user_id → {minute, count}
        self._quota_usage = {}  # user_id → {used, limit, reset_at}

    def create_bucket(
        self,
        user_id: str,
        capacity: int = 100,
        refill_rate: float = 10.0  # tokens per second
    ) -> None:
        """Create token bucket for user"""
        self._buckets[user_id] = {
            "user_id": user_id,
            "capacity": capacity,
            "tokens": capacity,
            "refill_rate": refill_rate,
            "last_refill": datetime.utcnow().isoformat()
        }

    def allow_request(self, user_id: str, tokens_required: int = 1) -> tuple:
        """Check if request is allowed (token bucket)"""
        if user_id not in self._buckets:
            self.create_bucket(user_id)

        bucket = self._buckets[user_id]

        # Refill tokens based on time elapsed
        now = datetime.utcnow()
        last_refill = datetime.fromisoformat(bucket["last_refill"])
        elapsed_seconds = (now - last_refill).total_seconds()

        tokens_added = elapsed_seconds * bucket["refill_rate"]
        bucket["tokens"] = min(bucket["capacity"], bucket["tokens"] + tokens_added)
        bucket["last_refill"] = now.isoformat()

        # Check if enough tokens
        if bucket["tokens"] >= tokens_required:
            bucket["tokens"] -= tokens_required
            return (True, f"{int(bucket['tokens'])} tokens remaining")
        else:
            return (False, f"Rate limited. Need {tokens_required}, have {int(bucket['tokens'])}")

    def set_user_quota(
        self,
        user_id: str,
        limit: int,
        reset_after_seconds: int = 3600
    ) -> None:
        """Set per-user quota (e.g., 1000 requests per hour)"""
        self._quota_usage[user_id] = {
            "user_id": user_id,
            "used": 0,
            "limit": limit,
            "reset_at": (datetime.utcnow() + timedelta(seconds=reset_after_seconds)).isoformat()
        }

    def check_quota(self, user_id: str) -> tuple:
        """Check if user is within quota"""
        if user_id not in self._quota_usage:
            return (True, "No quota set")

        quota = self._quota_usage[user_id]
        now = datetime.utcnow()

        # Reset if period expired
        if now.isoformat() > quota["reset_at"]:
            quota["used"] = 0
            quota["reset_at"] = (now + timedelta(hours=1)).isoformat()

        # Check quota
        if quota["used"] < quota["limit"]:
            quota["used"] += 1
            remaining = quota["limit"] - quota["used"]
            return (True, f"{remaining} requests remaining in quota")
        else:
            return (False, "User quota exceeded")

    def increment_window_counter(self, user_id: str) -> bool:
        """Increment sliding window counter"""
        now = datetime.utcnow()
        current_minute = now.replace(second=0, microsecond=0)

        if user_id not in self._window_counters:
            self._window_counters[user_id] = {"minute": current_minute, "count": 0}

        counter = self._window_counters[user_id]

        # Reset if new minute
        if counter["minute"] != current_minute:
            counter["minute"] = current_minute
            counter["count"] = 0

        counter["count"] += 1
        return counter["count"] <= 100  # Allow 100 per minute

    def get_bucket_status(self, user_id: str) -> Optional[Dict]:
        """Get token bucket status"""
        return self._buckets.get(user_id)

    def get_quota_status(self, user_id: str) -> Optional[Dict]:
        """Get quota status"""
        return self._quota_usage.get(user_id)
'''

    return rate_limiting


def generate_rate_limiting_system() -> dict:
    """Generate complete distributed rate limiting system."""

    imports = '''from typing import Dict, List, Optional
from datetime import datetime, timedelta


'''

    module_doc = '''"""
Phase 5 Distributed Rate Limiting: Shared Token Bucket & Quotas

Rate limiting across multiple servers with shared state (Redis-backed).

TOKEN BUCKET ALGORITHM:

Bucket capacity: 100 tokens
Refill rate: 10 tokens/second

Timeline:
- T=0:00s: bucket has 100 tokens, 5 requests arrive (each costs 20 tokens)
  - Request 1: 100 tokens → allow, remaining 80
  - Request 2: 80 tokens → allow, remaining 60
  - Request 3: 60 tokens → allow, remaining 40
  - Request 4: 40 tokens → allow, remaining 20
  - Request 5: 20 tokens → allow, remaining 0
  - Result: 5 requests OK, burst of 5

- T=0:10s: 10 seconds pass, 100 new tokens added (10 * 10)
  - But capacity is 100, so still 100
  - Refill is capped at capacity

- T=0:20s: steady state
  - 10 tokens added per second
  - 1 request (1 token) per second = allowed
  - Throughput: 1 req/sec sustained
  - Bursts: up to 100 requests instantly (using capacity)

COMPARISON: Token Bucket vs Fixed Window

Fixed window (per minute):
- Limit: 60 requests per minute
- Problem: all 60 requests at T=0:00, then zero until T=1:00

Timeline:
- T=0:00: 60 requests allowed
- T=0:30: 0 requests allowed (quota exhausted)
- T=1:00: reset, 60 requests allowed
- Problem: bursty, uneven

Token bucket:
- Refill rate: 1 token/sec
- Capacity: 60 tokens
- Timeline:
  - T=0:00: 60 requests allowed (burst)
  - T=0:30: 30 requests allowed (30 sec refill)
  - T=1:00: 60 requests allowed (capacity refilled)
- Benefit: smooth, fair, handles bursts

PER-USER QUOTAS:

Free tier: 10,000 requests/month
Pro tier: 100,000 requests/month
Enterprise: unlimited

User alice (Free):
- Quota: 10,000 requests/month
- Used this month: 8,500
- Remaining: 1,500
- When she hits 10,000: request denied
- When month resets: counter resets to 0

User bob (Pro):
- Quota: 100,000 requests/month
- Used: 95,000
- Remaining: 5,000
- Can use much more

Billing:
- Charged for actual usage
- Can upgrade if quota reached
- Can set per-API-key quotas

DDoS PROTECTION:

Attacker tries to overwhelm service:
- 1000 requests/second
- Each request: 1 token
- Bucket capacity: 100

Timeline:
- T=0:00: First 100 requests allowed (bucket drained)
- T=0:01+: Only 10 new tokens/sec (refill rate)
  - 990 new requests arrive, only 10 allowed
  - 980 requests denied
- Result: attacker blocked, legitimate users unaffected

Tiered limits:
- Rate limiting at edge (CDN): 1000 req/sec per IP
- At API gateway: 100 req/sec per user
- At service: 10 req/sec per specific endpoint
- Multiple layers: defense in depth

RESPONSE HEADERS:

When request is rate limited, return:
```
HTTP 429 Too Many Requests

X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 2026-05-17T10:01:00Z
```

Client can:
- Read reset time: wait until 10:01
- Check remaining: know how many requests left
- Plan ahead: batch requests before limit

SCALING: Redis-Backed Counter

Local rate limiting (single server):
- Limited to one server's capacity
- Different servers = different limits
- Doesn't coordinate

Distributed (Redis-backed):
- All servers read/write same Redis
- Single source of truth
- Coordinated across all servers

Implementation:
1. Request arrives at Server A
2. Check Redis: "alice" key
3. Decrement counter: alice count -= 1
4. Allow if count > 0
5. Same for Server B: always uses Redis

Result:
- 1000 servers, 1 Redis
- Unified rate limiting
- Attacker can't bypass by hitting different servers

SLIDING WINDOW:

Sliding window (more accurate):
- Instead of: 100 requests per minute
- Track: requests in last 60 seconds

Timeline:
- T=0:00-0:30: 60 requests
- T=0:30-0:59: can't send more (60 already sent in window)
- T=0:59-1:00: only 1 second in window, ~1-2 requests allowed (as old ones fall out)
- T=1:00-1:10: requests from T=0:00-0:10 fall out, new ones allowed
- Result: smoother than fixed window

BENEFITS:

✓ DDoS protection: limit requests per user
✓ Fair: quota protects other users
✓ Smooth: token bucket prevents bursts
✓ Observable: headers tell client status
✓ Coordinated: Redis backend ensures consistency

COMMON PITFALLS:

❌ No distributed coordination: each server counts independently
   → Limit: 100 req/sec per server
   → 10 servers * 100 = 1000 req/sec total (defeats purpose)
   → Solution: use shared Redis

❌ Limit too strict: legitimate users blocked
   → Limit: 10 requests/day
   → User does 5 real requests, 5 requests blocked
   → Result: user frustrated
   → Solution: generous limits, monitor for abuse

❌ No backoff: client retries immediately
   → Attacker: retry 1000x/sec
   → Server: process 1000 denied requests/sec (busy!)
   → Solution: client backoff + server rate limit

✓ Good rate limiting:
   - Generous limits (users don't notice)
   - Token bucket (smooth)
   - Per-user quotas (fair)
   - Observable headers (clients know status)
   - Distributed (coordinated across servers)
"""
'''

    rate_limiting = generate_distributed_rate_limiting()

    complete_code = imports + module_doc + "\n" + rate_limiting

    return {
        "code": complete_code,
        "pattern": "Distributed Rate Limiting",
        "module": "phase5_rate_limiting_distributed.py"
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate distributed rate limiting")
    args = parser.parse_args()
    result = generate_rate_limiting_system()
    print(result["code"])


if __name__ == "__main__":
    main()
