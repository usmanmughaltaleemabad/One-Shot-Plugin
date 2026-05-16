#!/usr/bin/env python3
"""
Phase 5 Strangler Pattern: Legacy Modernization

Incrementally replace legacy system with new one.

Problem: Legacy system
- Old technology (Java 6, old frameworks)
- Hard to modify (spaghetti code)
- Difficult to test
- Can't do new features
- But: handles 99% of business logic, can't rewrite all at once

Options:
1. Big Bang Rewrite: rewrite everything
   - Risk: takes 2 years, bugs, lost features
   - Reality: often fails

2. Strangler Pattern: incrementally migrate
   - Run old + new in parallel
   - Gradually divert traffic to new
   - Features migrate one by one
   - Eventually: old system gone

Strangler process:
1. API Gateway: route requests to old/new
2. Feature flag: decides old vs new
3. Gradually increase: 10% → 50% → 100%
4. Monitor: metrics, logs, errors
5. Rollback: if new broken, switch back to old
6. Migrate: move feature to new, retire from old

Usage:
    python phase5_strangler_pattern.py --feature user-auth

Input: Feature to migrate
Output: Strangler pattern with dual routing
"""

import argparse
import json
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime


def generate_strangler_router() -> str:
    """Generate strangler router."""

    router = '''
class StranglerRouter:
    """
    Route requests to old or new system.

    Dual implementation:
    - Old system (legacy): proven, but old code
    - New system (modern): new code, needs validation

    Route based on:
    - Feature flag: 10% to new, 90% to old
    - User ID: new system for beta users
    - Feature area: auth on new, payments on old
    """

    def __init__(self, old_system, new_system):
        self.old = old_system
        self.new = new_system
        self._feature_flags = {}  # feature → percent_to_new

    def route_request(
        self,
        feature: str,
        request: Dict,
        user_id: Optional[str] = None
    ) -> Any:
        """Route request to old or new"""
        # Get routing percentage
        percent_new = self._feature_flags.get(feature, 0)

        # Decide: old or new?
        use_new = self._should_use_new(user_id, percent_new)

        try:
            if use_new:
                return self.new.handle_request(feature, request)
            else:
                return self.old.handle_request(feature, request)
        except Exception as e:
            # New system failed, fallback to old
            if use_new:
                return self.old.handle_request(feature, request)
            else:
                raise

    def _should_use_new(self, user_id: Optional[str], percent: int) -> bool:
        """Determine if should route to new system"""
        if percent == 0:
            return False  # 0% → always old
        if percent == 100:
            return True  # 100% → always new

        # Hash user ID for consistent routing
        if user_id:
            hash_value = hash(user_id) % 100
            return hash_value < percent

        return False

    def set_traffic_percentage(self, feature: str, percent: int) -> None:
        """Set what % of traffic goes to new system"""
        self._feature_flags[feature] = percent

    def migrate_feature(self, feature: str) -> None:
        """Complete migration: 100% to new"""
        self.set_traffic_percentage(feature, 100)
'''

    return router


def generate_dual_write() -> str:
    """Generate dual-write pattern."""

    dual_write = '''
class DualWriteOrchestrator:
    """
    Write to both old and new during migration.

    Use case: User creates order
    - Write to old system (for now)
    - Also write to new system (for validation)
    - Compare results
    - If new working: increase traffic %
    - If new broken: stay on old

    Validation:
    - Run both
    - Compare outputs
    - Log differences (dual-write divergence)
    """

    def __init__(self, old_system, new_system):
        self.old = old_system
        self.new = new_system
        self.divergences = []

    def dual_write(self, feature: str, data: Dict) -> Dict:
        """Write to both, compare"""
        # Write to old (source of truth)
        old_result = self.old.write(feature, data)

        # Write to new (for validation)
        try:
            new_result = self.new.write(feature, data)

            # Compare results
            if old_result != new_result:
                self.divergences.append({
                    "feature": feature,
                    "old": old_result,
                    "new": new_result,
                    "timestamp": datetime.utcnow().isoformat()
                })
        except Exception as e:
            # New system failed, log but continue with old
            pass

        # Return old result (source of truth for now)
        return old_result

    def get_divergences(self) -> List[Dict]:
        """Get differences between old and new"""
        return self.divergences
'''

    return dual_write


def generate_feature_verification() -> str:
    """Generate feature verification."""

    verification = '''
class FeatureVerification:
    """Verify new system ready for migration"""

    def __init__(self):
        self.test_results = {}  # feature → results

    def verify_feature(
        self,
        feature: str,
        test_cases: List[Callable],
        new_system
    ) -> Dict:
        """
        Run tests on new system.

        Verify new system handles all cases.
        """
        results = {
            "feature": feature,
            "passed": 0,
            "failed": 0,
            "errors": []
        }

        for test_fn in test_cases:
            try:
                # Run test on new system
                test_fn(new_system)
                results["passed"] += 1
            except Exception as e:
                results["failed"] += 1
                results["errors"].append(str(e))

        self.test_results[feature] = results
        return results

    def is_ready(self, feature: str) -> bool:
        """Check if feature ready to migrate"""
        results = self.test_results.get(feature)
        if not results:
            return False

        return results["failed"] == 0 and results["passed"] > 0
'''

    return verification


def generate_strangler_system() -> dict:
    """Generate complete strangler system."""

    imports = '''from typing import Any, Callable, Dict, List, Optional
from datetime import datetime


'''

    module_doc = '''"""
Phase 5 Strangler Pattern: Legacy Modernization

Incrementally replace legacy system.

The Problem:
Old monolithic system (10+ years old):
- Hard to change
- Difficult to test
- Technologies outdated
- But: working, handling all business logic
- Can't afford to rewrite (2-3 year project)

Solution: Strangler Pattern

Concept: Plant a strangler fig on an old tree.
Over time, the fig grows around the tree, eventually replacing it.
Similarly, new system grows alongside old, gradually replacing it.

Timeline:
Phase 1: API Gateway (1 month)
- Add router that directs traffic
- 100% to old system still
- Prepare for dual routing

Phase 2: Pilot (1-3 months)
- Implement first feature in new system
- 5-10% of users → new
- 90-95% of users → old
- Monitor: metrics, errors, logs

Phase 3: Expand (3-6 months)
- Implement more features
- Increase percentage: 25% → 50% → 75% → 90%
- Monitor continually

Phase 4: Cutover (1-2 months)
- Final features migrated
- 100% traffic to new
- Keep old as backup (off)

Phase 5: Retire (1 month)
- Decommission old system
- Archive code/data

Benefits:
✓ Low risk (can rollback anytime)
✓ Continuous delivery (features gradually)
✓ Team can learn (no big bang)
✓ Users see improvements incrementally
✓ Can integrate with old (hybrid period)

Example: User Authentication

Old system: /auth/login (Java servlet)
New system: /auth/login (Python FastAPI)

Week 1: Deploy new, 0% traffic
Week 2: 5% of users → new
Week 3: 25% of users → new
Week 4: 50% of users → new
Week 5: 100% of users → new
Week 6: Decommission old

Monitoring:
- Latency: new vs old
- Error rate: new vs old
- User satisfaction: new vs old
- If new slower/broken: rollback (switch %)
"""
'''

    router = generate_strangler_router()
    dual_write = generate_dual_write()
    verification = generate_feature_verification()

    complete_code = imports + module_doc + "\n" + router + "\n" + dual_write + "\n" + verification

    return {
        "code": complete_code,
        "pattern": "Strangler Pattern",
        "module": "phase5_strangler_pattern.py",
    }


def main():
    parser = argparse.ArgumentParser(description="Generate strangler pattern")
    parser.add_argument("--feature", help="Feature to migrate")
    parser.add_argument("--output", choices=["json", "code"], default="code")

    args = parser.parse_args()
    result = generate_strangler_system()

    if args.output == "json":
        metadata = {k: v for k, v in result.items() if k != "code"}
        print(json.dumps(metadata, indent=2))
    else:
        print(result["code"])


if __name__ == "__main__":
    main()
