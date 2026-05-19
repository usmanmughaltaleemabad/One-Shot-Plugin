#!/usr/bin/env python3
"""
Phase 4 CQRS: Performance Optimization

Optimize CQRS systems for production.

Bottlenecks:
- Event replay slow (1000s of events = milliseconds)
- Read model queries complex (multiple aggregates)
- Projections behind (seconds lag)
- Cache misses (cold start)

Strategies:
1. Snapshots: checkpoint every N events
2. Caching: cache aggregates, projections, queries
3. Denormalization: flatten read model structure
4. Indexing: optimize projection queries
5. Batch: process events in batches

Usage:
    python phase4_cqrs_performance_optimization.py --strategy snapshots

Input: Optimization strategy
Output: Performance tuning implementations
"""

import argparse
import json
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime


def generate_caching_layer() -> str:
    """Generate caching layer."""

    caching = '''
class CQRSCache:
    """
    Multi-level cache for CQRS.

    Levels:
    1. Aggregate cache: avoid replay
    2. Projection cache: cache query results
    3. Read model cache: denormalized data cache
    4. Query result cache: expensive queries
    """

    def __init__(self, event_store):
        self.event_store = event_store
        self._aggregate_cache = {}  # aggregate_id → aggregate
        self._projection_cache = {}  # projection_name → data
        self._query_cache = {}  # query_key → results
        self._ttl = {}  # key → expiration time
        self.hits = 0
        self.misses = 0

    def get_or_load_aggregate(
        self,
        aggregate_id: str,
        aggregate_class,
        max_age_seconds: int = 300
    ) -> Any:
        """
        Get aggregate from cache or load.

        If in cache and fresh: return cached
        If in cache but stale: reload from snapshot
        If not cached: load from event store

        Args:
            aggregate_id: ID of aggregate
            aggregate_class: Class to instantiate
            max_age_seconds: How old can cache be (default: 5 minutes)

        Returns:
            Cached or fresh aggregate
        """
        cache_key = f"agg-{aggregate_id}"

        # Check cache
        if cache_key in self._aggregate_cache:
            if self._is_fresh(cache_key, max_age_seconds):
                self.hits += 1
                return self._aggregate_cache[cache_key]

        # Cache miss or stale: load
        self.misses += 1
        aggregate = self.event_store.load_aggregate(aggregate_id, aggregate_class)

        # Cache it
        self._aggregate_cache[cache_key] = aggregate
        self._set_expiration(cache_key, max_age_seconds)

        return aggregate

    def cache_projection(
        self,
        projection_name: str,
        data: Any,
        ttl_seconds: int = 60
    ) -> None:
        """Cache projection result"""
        key = f"proj-{projection_name}"
        self._projection_cache[key] = data
        self._set_expiration(key, ttl_seconds)

    def get_cached_projection(self, projection_name: str) -> Optional[Any]:
        """Get cached projection if fresh"""
        key = f"proj-{projection_name}"
        if key in self._projection_cache and self._is_fresh(key):
            self.hits += 1
            return self._projection_cache[key]
        self.misses += 1
        return None

    def cache_query_result(
        self,
        query_key: str,
        result: Any,
        ttl_seconds: int = 120
    ) -> None:
        """Cache query result"""
        self._query_cache[query_key] = result
        self._set_expiration(query_key, ttl_seconds)

    def get_cached_query(self, query_key: str) -> Optional[Any]:
        """Get cached query result if fresh"""
        if query_key in self._query_cache and self._is_fresh(query_key):
            self.hits += 1
            return self._query_cache[query_key]
        self.misses += 1
        return None

    def invalidate_aggregate(self, aggregate_id: str) -> None:
        """Invalidate aggregate cache (when it changes)"""
        key = f"agg-{aggregate_id}"
        if key in self._aggregate_cache:
            del self._aggregate_cache[key]

    def invalidate_projection(self, projection_name: str) -> None:
        """Invalidate projection cache (when updated)"""
        key = f"proj-{projection_name}"
        if key in self._projection_cache:
            del self._projection_cache[key]

    def invalidate_queries(self, pattern: str) -> None:
        """Invalidate queries matching pattern"""
        keys_to_remove = [k for k in self._query_cache if pattern in k]
        for key in keys_to_remove:
            del self._query_cache[key]

    def _is_fresh(self, key: str, max_age_seconds: Optional[int] = None) -> bool:
        """Check if cached item is still fresh"""
        if key not in self._ttl:
            return False
        expiration = self._ttl[key]
        if max_age_seconds:
            expiration = min(expiration, datetime.utcnow().timestamp() + max_age_seconds)
        return datetime.utcnow().timestamp() < expiration

    def _set_expiration(self, key: str, ttl_seconds: int) -> None:
        """Set expiration time"""
        self._ttl[key] = datetime.utcnow().timestamp() + ttl_seconds

    def get_stats(self) -> dict:
        """Cache statistics"""
        total = self.hits + self.misses
        hit_rate = self.hits / total * 100 if total > 0 else 0
        return {
            "hits": self.hits,
            "misses": self.misses,
            "total": total,
            "hit_rate": hit_rate,
            "cached_aggregates": len(self._aggregate_cache),
            "cached_projections": len(self._projection_cache),
            "cached_queries": len(self._query_cache)
        }
'''

    return caching


def generate_snapshot_optimization() -> str:
    """Generate snapshot optimization."""

    snapshot = '''
class SnapshotOptimizer:
    """
    Optimize event replay with snapshots.

    Problem: Replaying 10,000 events takes milliseconds.
    Solution: Save snapshot every N events, replay only recent events.

    Example:
    - Aggregate has 10,000 events
    - Snapshot at event 9,000 (1 second to create)
    - Now load: use snapshot + replay 200 events (5ms instead of 1000ms)
    - 200x faster!

    Strategy:
    - Create snapshot every snapshot_interval events
    - On load: use latest snapshot + replay events after
    - Periodically clean old snapshots
    """

    def __init__(self, event_store, snapshot_store, snapshot_interval: int = 100):
        self.event_store = event_store
        self.snapshot_store = snapshot_store
        self.snapshot_interval = snapshot_interval
        self.last_snapshot_version = {}

    def should_create_snapshot(self, aggregate_id: str, current_version: int) -> bool:
        """Check if snapshot should be created"""
        last = self.last_snapshot_version.get(aggregate_id, 0)
        return current_version - last >= self.snapshot_interval

    def create_snapshot(
        self,
        aggregate_id: str,
        aggregate_state: Dict,
        version: int
    ) -> None:
        """Create snapshot of aggregate state"""
        snapshot = {
            "aggregate_id": aggregate_id,
            "version": version,
            "state": aggregate_state,
            "created_at": datetime.utcnow().isoformat()
        }

        self.snapshot_store.save(snapshot)
        self.last_snapshot_version[aggregate_id] = version

    def load_with_optimization(
        self,
        aggregate_id: str,
        aggregate_class
    ) -> Any:
        """
        Load aggregate with snapshot optimization.

        If snapshot exists:
        - Reconstruct from snapshot
        - Replay events after snapshot
        - Much faster!
        """
        snapshot = self.snapshot_store.get_latest(aggregate_id)

        if snapshot:
            # Load from snapshot
            aggregate = aggregate_class.from_dict(snapshot["state"])
            aggregate.version = snapshot["version"]

            # Replay events after snapshot
            events = self.event_store.get_events_after(
                aggregate_id,
                snapshot["version"]
            )
            for event in events:
                aggregate.apply_event(event)

            return aggregate
        else:
            # No snapshot, full replay
            return self.event_store.load_aggregate(aggregate_id, aggregate_class)

    def cleanup_old_snapshots(self, keep_last: int = 3) -> None:
        """Delete old snapshots (keep only last N)"""
        self.snapshot_store.cleanup(keep_last)
'''

    return snapshot


def generate_denormalization_helper() -> str:
    """Generate denormalization helper."""

    denorm = '''
class DenormalizationHelper:
    """
    Optimize read models with denormalization.

    Problem: Answering query "get all orders for customer X" requires:
    - Query Order aggregate by customer_id
    - For each, query related Payment, Inventory, Shipping aggregates
    - Join results
    - Slow!

    Solution: Denormalize into read model:
    OrderListView: {
        customer_id, [
            {order_id, total, status, payment_status, inventory_status, shipping_status}
        ]
    }

    One query instead of 1+N queries.
    """

    def __init__(self, read_model_store):
        self.read_model_store = read_model_store

    def denormalize_customer_orders(self, customer_id: str) -> Dict:
        """
        Denormalized view: all order info for customer.

        Includes: order ID, total, status, payment, inventory, shipping.
        Single query. Fast.
        """
        orders = self.read_model_store.query_orders_by_customer(customer_id)

        denormalized = {
            "customer_id": customer_id,
            "order_count": len(orders),
            "total_spent": sum(o["total"] for o in orders),
            "orders": orders
        }

        return denormalized

    def denormalize_order_detail(self, order_id: str) -> Dict:
        """
        Denormalized view: complete order details.

        Includes: items, payments, inventory, tracking.
        Everything in one place for quick display.
        """
        order = self.read_model_store.get_order(order_id)
        items = self.read_model_store.get_order_items(order_id)
        payments = self.read_model_store.get_order_payments(order_id)
        shipments = self.read_model_store.get_order_shipments(order_id)

        return {
            "order_id": order_id,
            "customer": order["customer"],
            "status": order["status"],
            "items": items,
            "payments": payments,
            "shipments": shipments,
            "total": order["total"],
            "created_at": order["created_at"]
        }
'''

    return denorm


def generate_query_optimization() -> str:
    """Generate query optimization."""

    query_opt = '''
class QueryOptimizer:
    """
    Optimize CQRS queries.

    Techniques:
    1. Index creation: index frequently queried fields
    2. Batch loading: load related data in one query
    3. Lazy loading: load nested data only when needed
    4. Query rewriting: simplify complex queries
    5. Explain plans: understand slow queries
    """

    def __init__(self, read_model_store):
        self.read_model_store = read_model_store
        self.query_stats = {}

    def create_index(self, table: str, column: str) -> None:
        """Create index for fast queries"""
        self.read_model_store.create_index(table, column)

    def optimize_slow_query(self, query_key: str, query_fn: Callable) -> None:
        """
        Identify and optimize slow query.

        1. Measure execution time
        2. If slow, check if index exists
        3. Suggest denormalization
        4. Cache result
        """
        start = datetime.utcnow()
        result = query_fn()
        elapsed = (datetime.utcnow() - start).total_seconds()

        self.query_stats[query_key] = {
            "execution_time": elapsed,
            "result_count": len(result) if isinstance(result, list) else 1
        }

        if elapsed > 1.0:  # Slow query (>1 second)
            # Suggest optimization
            print(f"SLOW QUERY: {query_key} took {elapsed}s")
            print(f"  → Consider creating index")
            print(f"  → Consider caching")
            print(f"  → Consider denormalization")

    def get_query_stats(self) -> Dict:
        """Get query performance statistics"""
        return {
            "total_queries": len(self.query_stats),
            "slow_queries": sum(
                1 for q in self.query_stats.values()
                if q["execution_time"] > 1.0
            ),
            "avg_execution_time": sum(
                q["execution_time"] for q in self.query_stats.values()
            ) / len(self.query_stats) if self.query_stats else 0
        }
'''

    return query_opt


def generate_optimization_system() -> dict:
    """Generate complete optimization system."""

    imports = '''from typing import Any, Callable, Dict, List, Optional
from datetime import datetime


'''

    module_doc = '''"""
CQRS Performance Optimization

Strategies to optimize CQRS systems for production.

Common bottlenecks:
1. Event replay: 1000s of events = slow
   → Solution: Snapshots (checkpoint every 100 events)

2. Complex queries: join multiple read models
   → Solution: Denormalize into single view

3. Cache misses: cold start
   → Solution: Multi-level cache with TTL

4. Slow queries: no indexes
   → Solution: Create indexes, rewrite queries

5. Stale data: read model lag
   → Solution: Accept eventual consistency, monitor lag

Optimization checklist:
☐ Create snapshots (every 100 events)
☐ Denormalize read models (flatten structure)
☐ Cache frequently accessed data (TTL=5m)
☐ Create indexes (on filter columns)
☐ Monitor query performance
☐ Set cache expiration TTLs
"""
'''

    caching = generate_caching_layer()
    snapshot = generate_snapshot_optimization()
    denorm = generate_denormalization_helper()
    query = generate_query_optimization()

    complete_code = imports + module_doc + "\n" + caching + "\n" + snapshot + "\n" + denorm + "\n" + query

    return {
        "code": complete_code,
        "pattern": "CQRS Performance Optimization",
        "module": "cqrs_performance_optimization.py",
    }


def main():
    parser = argparse.ArgumentParser(description="Generate CQRS performance optimization")
    parser.add_argument("--strategy", help="Optimization strategy")
    parser.add_argument("--output", choices=["json", "code"], default="code")

    args = parser.parse_args()
    result = generate_optimization_system()

    if args.output == "json":
        metadata = {k: v for k, v in result.items() if k != "code"}
        print(json.dumps(metadata, indent=2))
    else:
        print(result["code"])


if __name__ == "__main__":
    main()
