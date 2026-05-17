#!/usr/bin/env python3
"""
Phase 5 GraphQL Optimization: DataLoader & Batch Processing

DataLoader Pattern: Solve N+1 query problem in GraphQL.

Problem: N+1 queries
- Query: get orders with populated users
- Naive: 1 query for orders + 1000 queries for users (N+1)
- Cost: 1001 database queries!

DataLoader (solution):
- Batch collect all user IDs
- Single query: get all users
- Distribute results back
- Cost: 2 database queries (1 order + 1 user batch)
"""

from typing import Dict, List, Optional, Callable, Any
from datetime import datetime


def generate_graphql_batching() -> str:
    """Generate DataLoader pattern."""

    dataloader = '''
class DataLoader:
    """
    Batch operations to prevent N+1 queries.

    Pattern:
    1. Collect all IDs to load (user_1, user_2, user_3)
    2. Batch query: SELECT * FROM users WHERE id IN (1,2,3)
    3. Distribute results to callers
    """

    def __init__(self, batch_fn: Callable):
        self._batch_fn = batch_fn
        self._cache = {}
        self._queue = []  # Pending IDs
        self._results = {}

    def load(self, key: Any) -> Dict:
        """Queue a key to load"""
        if key in self._cache:
            return self._cache[key]

        if key not in self._queue:
            self._queue.append(key)

        return {"pending": True, "key": key}

    def load_many(self, keys: List[Any]) -> List[Dict]:
        """Queue multiple keys"""
        results = []
        for key in keys:
            results.append(self.load(key))
        return results

    def prime(self, key: Any, value: Any) -> None:
        """Pre-populate cache"""
        self._cache[key] = value

    def clear(self, key: Any = None) -> None:
        """Clear cache"""
        if key:
            self._cache.pop(key, None)
        else:
            self._cache.clear()

    def execute_batch(self) -> Dict[Any, Any]:
        """Execute batch query for all queued keys"""
        if not self._queue:
            return {}

        keys_to_load = self._queue
        self._queue = []

        # Call batch function
        results = self._batch_fn(keys_to_load)

        # Cache results
        for key, value in results.items():
            self._cache[key] = value

        return results

    def get(self, key: Any) -> Optional[Any]:
        """Get cached value"""
        return self._cache.get(key)


class GraphQLBatchingExample:
    """Example: Users for Orders"""

    def __init__(self):
        self._users = {1: {"id": 1, "name": "Alice"}, 2: {"id": 2, "name": "Bob"}}
        self._orders = [
            {"id": 1, "user_id": 1, "amount": 100},
            {"id": 2, "user_id": 2, "amount": 200}
        ]

    def batch_load_users(self, user_ids: List[int]) -> Dict[int, Dict]:
        """Load multiple users at once"""
        return {uid: self._users.get(uid) for uid in user_ids}

    def resolve_orders(self) -> List[Dict]:
        """Resolve orders with users (using DataLoader)"""
        user_loader = DataLoader(self.batch_load_users)

        orders_with_users = []
        for order in self._orders:
            user = user_loader.load(order["user_id"])
            orders_with_users.append({
                "order_id": order["id"],
                "amount": order["amount"],
                "user": user
            })

        # Execute batch
        user_loader.execute_batch()

        # Distribute results
        return [
            {
                "order_id": o["order_id"],
                "amount": o["amount"],
                "user": user_loader.get(o["user"]["key"]) if o["user"].get("pending") else o["user"]
            }
            for o in orders_with_users
        ]
'''

    return dataloader


def generate_batching_system() -> dict:
    """Generate complete GraphQL batching system."""

    imports = '''from typing import Dict, List, Optional, Callable, Any
from datetime import datetime


'''

    module_doc = '''"""
Phase 5 GraphQL Optimization: DataLoader & Batch Processing

Prevent N+1 query problems in GraphQL resolvers (DataLoader pattern).

THE N+1 PROBLEM:

Query:
query {
  orders {
    id
    amount
    user {
      name
    }
  }
}

Naive resolver execution:
1. Query orders (1 query)
   → orders: [order_1, order_2, order_3, ...]

2. For each order, resolve user (N queries):
   → Query user for order_1 (1 query)
   → Query user for order_2 (1 query)
   → Query user for order_3 (1 query)
   ...
   → Query user for order_1000 (1 query)

TOTAL: 1 + 1000 = 1001 queries
TIME: 1000 * 5ms (network latency) = 5 seconds

USER GETS: 5 second response time for simple query!

DATALOADER SOLUTION:

Resolver execution (with batching):
1. Query orders (1 query)
   → orders: [order_1, order_2, order_3]

2. Collect all user IDs: [1, 2, 3]

3. Batch load users (1 query instead of 1000)
   → Query: SELECT * FROM users WHERE id IN (1, 2, 3)
   → Result: {1: user_1, 2: user_2, 3: user_3}

4. Distribute results to resolvers

TOTAL: 1 + 1 = 2 queries
TIME: 2 * 5ms = 10ms

USER GETS: 10ms response time (500x faster!)

EXAMPLE CODE:

class UserLoader(DataLoader):
    def batch(self, user_ids):
        return db.query("SELECT * FROM users WHERE id IN ?", user_ids)

def resolve_order_user(order):
    loader = user_loader  # Global
    return loader.load(order.user_id)

Execution:
1. resolve_orders() calls resolve_order_user() 1000 times
2. Each call: loader.load(user_id) → queues ID, returns promise
3. Event loop: resolve() collects all queued IDs
4. Batch query: SELECT * FROM users WHERE id IN (1,2,3,...,1000)
5. Distribute results: promise.resolve(user_data)
6. Continue rendering

ADVANCED: Request Batching

Not just database queries, any "batches":
- API calls: batch 100 HTTP requests into 1 batch request
- Cache lookups: batch cache gets
- Microservice calls: batch RPC calls

Pattern applies to anything that benefits from batching.

TIMING:

Without DataLoader:
- Sequential: 1000 queries * 5ms = 5000ms

With DataLoader:
- Batched: 1 batch query of 1000 = 50ms (if backend supports bulk query)

Without DataLoader is 100x slower!

CACHING LAYER:

DataLoader also caches within request:
- order_1 references user_2
- order_2 also references user_2
- DataLoader caches user_2 result
- Second reference: returned from cache (no query)

Cache is per-request (cleared after response sent)

BENEFITS:

✓ N+1 query elimination (50-100x faster)
✓ Automatic batching (transparent to resolver)
✓ Cache efficiency (deduplication)
✓ Simple API (await loader.load(id))
✓ Database-agnostic (works with any query)

CAVEATS:

⚠️ Batch function must support bulk loads
   - If you call it with [1,2,3], it must return {1: ..., 2: ..., 3: ...}
   - Some APIs don't support bulk loads

⚠️ Order preservation
   - DataLoader preserves order: load([1,2,3]) → {1:..., 2:..., 3:...}
   - Important for deterministic results

⚠️ Error handling
   - If batch query fails, all loaders fail
   - May need granular error handling

COMMON MISTAKES:

❌ Creating new DataLoader per request
   - DataLoader is expensive to create
   - Solution: reuse same loader throughout request

❌ Not batching within same request
   - Different fields still call sequentially
   - Solution: ensure all resolvers use same DataLoader

❌ Batching across requests (cache pollution)
   - Request A loads user_1, caches it
   - Request B gets stale user_1 data
   - Solution: clear cache after request

✓ Good batching:
   - One DataLoader instance per resource type
   - Reused throughout request
   - Cleared after response sent
   - Backend supports bulk query
"""
'''

    dataloader = generate_graphql_batching()

    complete_code = imports + module_doc + "\n" + dataloader

    return {
        "code": complete_code,
        "pattern": "GraphQL Batching",
        "module": "phase5_graphql_batching.py"
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate GraphQL batching")
    args = parser.parse_args()
    result = generate_batching_system()
    print(result["code"])


if __name__ == "__main__":
    main()
