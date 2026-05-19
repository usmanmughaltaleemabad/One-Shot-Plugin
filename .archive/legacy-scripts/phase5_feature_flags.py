#!/usr/bin/env python3
"""
Phase 5 Microservices: Feature Flags

Feature Flag: Toggle features on/off without redeployment.

Problems solved:
- Deploy code with new feature
- Turn on for 10% users, test
- If bad: turn off immediately (no redeployment)
- If good: turn on for 100% users

Examples:
- A/B testing: Group A sees design v1, Group B sees v2
- Gradual rollout: 1% → 10% → 50% → 100%
- Dark launches: Code deployed but hidden from users
- Killswitches: Kill expensive feature if cost overruns
"""

from typing import Dict, Optional, Callable, List
from datetime import datetime


def generate_feature_flag_system() -> str:
    """Generate feature flag management."""

    flags = '''
class FeatureFlags:
    """
    Manage feature flags: enable/disable features dynamically.

    Types:
    - Boolean: on/off
    - Percentage: 0-100% of users
    - Targeted: specific users/groups
    - Time-based: enable at specific time
    """

    def __init__(self):
        self._flags = {}  # flag_name → config

    def define_flag(self, name: str, default: bool = False) -> None:
        """Define feature flag"""
        self._flags[name] = {
            "name": name,
            "enabled": default,
            "percentage": 0,
            "targeted_users": set(),
            "created_at": datetime.utcnow().isoformat()
        }

    def enable(self, flag_name: str) -> None:
        """Enable flag"""
        if flag_name in self._flags:
            self._flags[flag_name]["enabled"] = True

    def disable(self, flag_name: str) -> None:
        """Disable flag"""
        if flag_name in self._flags:
            self._flags[flag_name]["enabled"] = False

    def set_percentage(self, flag_name: str, percentage: int) -> None:
        """Enable for X% of users"""
        if flag_name in self._flags:
            self._flags[flag_name]["percentage"] = percentage

    def target_user(self, flag_name: str, user_id: str, enabled: bool = True) -> None:
        """Enable/disable for specific user"""
        if flag_name in self._flags:
            if enabled:
                self._flags[flag_name]["targeted_users"].add(user_id)
            else:
                self._flags[flag_name]["targeted_users"].discard(user_id)

    def is_enabled(self, flag_name: str, user_id: str = None) -> bool:
        """Check if flag is enabled for user"""
        if flag_name not in self._flags:
            return False

        flag = self._flags[flag_name]

        # Check if explicitly targeted
        if user_id and user_id in flag["targeted_users"]:
            return True

        # Check percentage (deterministic per user)
        if flag["percentage"] > 0 and user_id:
            user_hash = hash(user_id) % 100
            if user_hash < flag["percentage"]:
                return True

        return flag["enabled"]

    def get_flag(self, flag_name: str) -> Optional[Dict]:
        """Get flag configuration"""
        return self._flags.get(flag_name)
'''

    return flags


def generate_feature_flag_patterns() -> str:
    """Generate feature flag patterns."""

    patterns = '''
class FeatureFlagPatterns:
    """
    Common feature flag patterns.

    1. BASIC ROLLOUT
       - Flag: new-checkout
       - Week 1: 10% of users
       - Week 2: 50% of users
       - Week 3: 100% of users

    2. A/B TESTING
       - Flag: checkout-design-v2
       - Group A: 50%, see old design
       - Group B: 50%, see new design
       - Measure conversion rates

    3. KILLSWITCH
       - Flag: expensive-feature
       - Feature works but costs $$ per request
       - If cost overruns: disable flag
       - Saves money immediately
    """

    def __init__(self, flags: 'FeatureFlags'):
        self.flags = flags

    def gradual_rollout(
        self,
        flag_name: str,
        percentages: List[int],
        days_between: int = 7
    ) -> None:
        """Gradually roll out feature over weeks"""
        # Week 1: 10%, Week 2: 30%, Week 3: 70%, Week 4: 100%
        self.flags.set_percentage(flag_name, percentages[0])

    def ab_test(
        self,
        flag_name: str,
        control_users: List[str],
        treatment_users: List[str]
    ) -> None:
        """Run A/B test"""
        for user in treatment_users:
            self.flags.target_user(flag_name, user, True)

    def killswitch(self, flag_name: str, cost_exceeded: bool) -> None:
        """Disable feature if cost exceeds threshold"""
        if cost_exceeded:
            self.flags.disable(flag_name)
'''

    return patterns


def generate_feature_flag_system_full() -> dict:
    """Generate complete feature flag system."""

    imports = '''from typing import Dict, Optional, Callable, List
from datetime import datetime


'''

    module_doc = '''"""
Phase 5 Feature Flags: Dynamic Feature Control

Toggle features without redeployment (LaunchDarkly pattern).

BENEFITS:
✓ Deploy code at 10pm (off-hours)
✓ Test with 1% users before going live
✓ Disable instantly if something breaks
✓ No downtime (no redeployment needed)
✓ A/B test new features
✓ Cost killswitches (disable if expensive)

TYPICAL WORKFLOW:

1. DEVELOPMENT
   - Write new feature
   - Wrap in feature flag
   - Code: if flags.is_enabled("new-checkout"): ...

2. DEPLOYMENT
   - Deploy code (flag disabled)
   - All users: feature invisible
   - Zero impact

3. TESTING
   - Enable for 10% of users
   - Monitor metrics (latency, errors)
   - No external users affected

4. ROLLOUT
   - Day 1: 10% (10,000 users)
   - Day 2: 25% (25,000 users)
   - Day 3: 50% (50,000 users)
   - Day 4: 100% (100,000 users)

5. CLEANUP
   - Feature stable
   - Remove flag from code
   - All users now use feature

IMPLEMENTATION PATTERN:

if flags.is_enabled("new-checkout", user_id):
    return NewCheckout.process_order(order)
else:
    return OldCheckout.process_order(order)

ADVANCED: PERCENTAGE + TARGETING

User ABC:
- 50% → old-checkout
- 50% → new-checkout
- Deterministic (same user always sees same)

User XYZ:
- Explicitly targeted: new-checkout
- Override percentage

MONITORING:
- Track which flag enabled for which users
- Track impact (latency, errors, conversions)
- Automatic rollback if bad
"""
'''

    flags = generate_feature_flag_system()
    patterns = generate_feature_flag_patterns()

    complete_code = imports + module_doc + "\n" + flags + "\n" + patterns

    return {
        "code": complete_code,
        "pattern": "Feature Flags",
        "module": "phase5_feature_flags.py"
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate feature flags")
    args = parser.parse_args()
    result = generate_feature_flag_system_full()
    print(result["code"])


if __name__ == "__main__":
    main()
