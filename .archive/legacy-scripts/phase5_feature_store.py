#!/usr/bin/env python3
"""
Phase 5 ML Pipelines: Feature Store

Feature Store: Centralized ML feature management.

Problem: ML models need features (inputs)
- Example: Predict customer churn
- Features: account_age, total_spent, support_tickets, last_login_days_ago
- Where do features come from?
  - Some from database
  - Some from analytics
  - Some from real-time calculations
  - Some from external APIs
- Recompute for training vs serving (skew)

Feature Store (solution):
- Centralized: single source of truth
- Computed once, used everywhere
- Training + Serving: consistent features
- Versioned: track feature changes
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta


def generate_feature_store() -> str:
    """Generate feature store system."""

    store = '''
class FeatureStore:
    """
    Store and serve ML features.

    Features:
    - account_age: days since signup
    - total_spent: total revenue
    - support_tickets: count
    - last_login_days_ago: recency

    Schema:
    - entity_id: customer_123
    - features: {account_age: 365, total_spent: 5000, ...}
    - timestamp: when computed
    - version: feature set version
    """

    def __init__(self):
        self._features = {}  # entity_id → {features}
        self._feature_definitions = {}  # feature_name → {description, version}
        self._compute_log = []

    def define_feature(
        self,
        name: str,
        description: str,
        version: int = 1
    ) -> None:
        """Define feature"""
        self._feature_definitions[name] = {
            "description": description,
            "version": version,
            "created_at": datetime.utcnow().isoformat()
        }

    def write_features(
        self,
        entity_id: str,
        features: Dict,
        timestamp: Optional[datetime] = None
    ) -> None:
        """Write features for entity"""
        if entity_id not in self._features:
            self._features[entity_id] = []

        self._features[entity_id].append({
            "features": features,
            "timestamp": timestamp or datetime.utcnow(),
            "version": len(self._features.get(entity_id, []))
        })

    def get_features(
        self,
        entity_id: str,
        as_of_date: Optional[datetime] = None
    ) -> Optional[Dict]:
        """Get features for entity"""
        if entity_id not in self._features:
            return None

        # Get latest version
        features_history = self._features[entity_id]

        if as_of_date:
            # Get features as they were on that date
            for entry in reversed(features_history):
                if entry["timestamp"] <= as_of_date:
                    return entry["features"]

        # Get latest
        return features_history[-1]["features"] if features_history else None

    def compute_features_batch(
        self,
        entities: List[str],
        compute_func
    ) -> int:
        """Batch compute features"""
        count = 0
        for entity_id in entities:
            try:
                features = compute_func(entity_id)
                self.write_features(entity_id, features)
                count += 1
            except Exception as e:
                self._compute_log.append({
                    "entity": entity_id,
                    "error": str(e)
                })

        return count
'''

    return store


def generate_feature_pipelines() -> str:
    """Generate feature computation pipelines."""

    pipelines = '''
class FeatureComputationPipeline:
    """
    Compute features from raw data.

    Sources:
    - Database: customer table, orders table
    - Events: customer_created, order_placed, support_ticket_opened
    - External: fraud scores, credit reports
    - Derived: features computed from other features
    """

    def __init__(self):
        self._pipeline_jobs = []

    def compute_customer_features(self, customer_id: str) -> Dict:
        """Compute all features for customer"""
        # Compute from database queries, events, etc.
        return {
            "account_age_days": 365,
            "total_spent": 5000,
            "order_count": 50,
            "avg_order_value": 100,
            "support_tickets": 2,
            "last_login_days_ago": 3,
            "is_premium": True
        }

    def schedule_daily_recompute(self, feature_names: List[str]) -> None:
        """Schedule nightly recompute"""
        job = {
            "features": feature_names,
            "schedule": "daily 2am UTC",
            "created_at": datetime.utcnow().isoformat()
        }

        self._pipeline_jobs.append(job)

    def get_feature_lineage(self, feature_name: str) -> Dict:
        """Show how feature computed (debugging)"""
        # Feature: total_spent
        # Source: orders table
        # Query: SELECT SUM(amount) FROM orders WHERE customer_id = ?
        # Updated: daily
        return {
            "name": feature_name,
            "source": "orders table",
            "computation": "SUM(amount)",
            "update_frequency": "daily"
        }
'''

    return pipelines


def generate_feature_store_system() -> dict:
    """Generate complete feature store system."""

    imports = '''from typing import Dict, List, Optional
from datetime import datetime, timedelta


'''

    module_doc = '''"""
Phase 5 Feature Store: ML Feature Management

Centralized feature storage for training & serving models.

PROBLEM: Feature skew
- Training: feature computed Monday
- Serving: feature computed Tuesday
- Values different → model makes bad predictions

SOLUTION: Feature store

Single source of truth:
- Compute features once
- Store with timestamp
- Serve to training (historical)
- Serve to inference (current)
- Always consistent

ARCHITECTURE:

FeatureStore:
- Offline store: full history (training)
- Online store: current values (serving)

Process:
1. Compute: raw data → features (daily)
2. Store offline: save history
3. Materialize online: copy latest to online store
4. Serve: training reads from offline, inference from online

EXAMPLE: Customer churn prediction

Features:
- account_age_days: 365
- total_spent: $5,000
- support_tickets: 2
- last_login_days_ago: 3
- monthly_active: 1 (user logged in this month)

Training:
- Date: 2026-05-01
- Features: get as_of_date("2026-04-01")
- Get historical values
- Train model: predict churn for May

Serving:
- Date: 2026-05-20
- Features: get latest
- Predict: is customer at risk?
- If risk > 0.8: alert support team

BENEFITS:
✓ No feature skew (same features train & serve)
✓ Fast inference (pre-computed, cached)
✓ Reproducibility (can rebuild model)
✓ Debugging (see which features caused prediction)
✓ Reuse (multiple models share features)

IMPLEMENTATION:
- Database: PostgreSQL for history
- Cache: Redis for online store
- Scheduler: daily feature recompute
- API: query features by entity_id
"""
'''

    store = generate_feature_store()
    pipelines = generate_feature_pipelines()

    complete_code = imports + module_doc + "\n" + store + "\n" + pipelines

    return {
        "code": complete_code,
        "pattern": "Feature Store",
        "module": "phase5_feature_store.py"
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate feature store")
    args = parser.parse_args()
    result = generate_feature_store_system()
    print(result["code"])


if __name__ == "__main__":
    main()
