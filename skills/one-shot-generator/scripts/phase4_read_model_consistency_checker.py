#!/usr/bin/env python3
"""
Phase 4 Read Model Consistency Checker

Monitors eventual consistency between write and read models.

Problem: Read models lag behind write model.
- User creates order (write model updated)
- Read model updater processes event (milliseconds to seconds lag)
- During lag, read model is stale

Acceptable? Yes (eventual consistency).
But need to: monitor lag, detect drift, alert on inconsistency.

Checks:
1. Lag: how far behind is read model?
2. Completeness: all write model changes in read model?
3. Accuracy: read model matches write model?
4. Integrity: no extra/missing data?

Usage:
    python phase4_read_model_consistency_checker.py --aggregate Order

Input: Aggregate type
Output: Consistency checker with health monitoring
"""

import argparse
import json
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime


def generate_consistency_checker() -> str:
    """Generate consistency checker."""

    checker = '''
class ReadModelConsistencyChecker:
    """
    Monitors consistency between write and read models.

    Performs:
    1. Lag detection: measure delay
    2. Completeness check: all events projected?
    3. Accuracy check: values match?
    4. Integrity check: data consistent?
    """

    def __init__(self, event_store, read_model_store, projection_engine):
        self.event_store = event_store
        self.read_model_store = read_model_store
        self.projection_engine = projection_engine
        self.health_metrics = {
            "lag_ms": [],
            "completeness_errors": [],
            "accuracy_errors": [],
            "integrity_errors": []
        }

    def measure_lag(self, aggregate_id: str) -> float:
        """
        Measure lag: how far behind is read model?

        Returns:
            Milliseconds behind write model
        """
        # Get latest event in write model
        events = self.event_store.get_events(aggregate_id)
        if not events:
            return 0

        latest_event = events[-1]
        event_timestamp = datetime.fromisoformat(latest_event["timestamp"])

        # Get latest update in read model
        read_model = self.read_model_store.get_projection(aggregate_id)
        if not read_model:
            # Read model not created yet
            return -1  # Not yet projected

        read_timestamp = datetime.fromisoformat(
            read_model.get("updated_at", datetime.utcnow().isoformat())
        )

        # Calculate lag
        lag = (datetime.utcnow() - event_timestamp).total_seconds() * 1000
        self.health_metrics["lag_ms"].append(lag)

        return lag

    def check_completeness(self, aggregate_id: str) -> Dict:
        """
        Check: are all events projected?

        Returns:
            {
                "complete": bool,
                "event_count": int,
                "projected_count": int,
                "missing_events": []
            }
        """
        events = self.event_store.get_events(aggregate_id)
        read_model = self.read_model_store.get_projection(aggregate_id)

        if not read_model:
            return {
                "complete": False,
                "event_count": len(events),
                "projected_count": 0,
                "missing_events": [e["event_id"] for e in events]
            }

        # Count projected events in read model
        projected_count = read_model.get("event_count", 0)
        event_count = len(events)

        missing = []
        if projected_count < event_count:
            # Find missing events
            projected_ids = read_model.get("event_ids", [])
            for event in events:
                if event["event_id"] not in projected_ids:
                    missing.append(event["event_id"])

        result = {
            "complete": projected_count == event_count,
            "event_count": event_count,
            "projected_count": projected_count,
            "missing_events": missing
        }

        if not result["complete"]:
            self.health_metrics["completeness_errors"].append(result)

        return result

    def check_accuracy(
        self,
        aggregate_id: str,
        comparison_fn: Callable
    ) -> Dict:
        """
        Check: does read model match write model?

        Requires custom comparison function that knows how to
        compare write and read model formats.

        Args:
            aggregate_id: Aggregate to check
            comparison_fn: function(write_state, read_state) → errors[]

        Returns:
            {
                "accurate": bool,
                "errors": [mismatches]
            }
        """
        # Load aggregate from write model
        events = self.event_store.get_events(aggregate_id)
        write_aggregate = self.event_store.reconstruct_aggregate(
            aggregate_id,
            events
        )

        # Get read model
        read_model = self.read_model_store.get_projection(aggregate_id)

        # Compare
        errors = comparison_fn(write_aggregate, read_model)

        result = {
            "accurate": len(errors) == 0,
            "errors": errors
        }

        if not result["accurate"]:
            self.health_metrics["accuracy_errors"].append(result)

        return result

    def check_integrity(
        self,
        aggregate_id: str,
        integrity_rules: List[Callable]
    ) -> Dict:
        """
        Check: is data internally consistent?

        Runs integrity rules (e.g., total = sum of items).

        Args:
            aggregate_id: Aggregate to check
            integrity_rules: list of rule functions

        Returns:
            {
                "integrity_ok": bool,
                "violations": [rule_name, error_msg]
            }
        """
        read_model = self.read_model_store.get_projection(aggregate_id)
        violations = []

        for rule_fn in integrity_rules:
            try:
                rule_name, is_valid = rule_fn(read_model)
                if not is_valid:
                    violations.append(rule_name)
            except Exception as e:
                violations.append(f"{rule_fn.__name__}: {str(e)}")

        result = {
            "integrity_ok": len(violations) == 0,
            "violations": violations
        }

        if not result["integrity_ok"]:
            self.health_metrics["integrity_errors"].append(result)

        return result

    def run_full_check(
        self,
        aggregate_id: str,
        comparison_fn: Optional[Callable] = None,
        integrity_rules: Optional[List[Callable]] = None
    ) -> Dict:
        """
        Run complete consistency check.

        Returns:
            {
                "consistent": bool,
                "lag_ms": float,
                "completeness": {...},
                "accuracy": {...},
                "integrity": {...},
                "overall_health": str  # "green", "yellow", "red"
            }
        """
        lag = self.measure_lag(aggregate_id)
        completeness = self.check_completeness(aggregate_id)

        accuracy = {}
        if comparison_fn:
            accuracy = self.check_accuracy(aggregate_id, comparison_fn)

        integrity = {}
        if integrity_rules:
            integrity = self.check_integrity(aggregate_id, integrity_rules)

        # Determine health
        health = "green"
        if lag > 5000:  # > 5 seconds lag
            health = "yellow"
        if not completeness["complete"]:
            health = "red"
        if accuracy and not accuracy["accurate"]:
            health = "red"
        if integrity and not integrity["integrity_ok"]:
            health = "red"

        return {
            "aggregate_id": aggregate_id,
            "consistent": all([
                completeness["complete"],
                accuracy.get("accurate", True),
                integrity.get("integrity_ok", True)
            ]),
            "lag_ms": lag,
            "completeness": completeness,
            "accuracy": accuracy,
            "integrity": integrity,
            "overall_health": health,
            "timestamp": datetime.utcnow().isoformat()
        }

    def get_health_report(self) -> Dict:
        """Get overall health metrics"""
        lag_values = self.health_metrics["lag_ms"]
        avg_lag = sum(lag_values) / len(lag_values) if lag_values else 0

        return {
            "checks_performed": len(lag_values),
            "average_lag_ms": avg_lag,
            "max_lag_ms": max(lag_values) if lag_values else 0,
            "completeness_errors": len(self.health_metrics["completeness_errors"]),
            "accuracy_errors": len(self.health_metrics["accuracy_errors"]),
            "integrity_errors": len(self.health_metrics["integrity_errors"]),
            "total_errors": sum([
                len(self.health_metrics[k])
                for k in self.health_metrics
                if k != "lag_ms"
            ])
        }
'''

    return checker


def generate_consistency_rules() -> str:
    """Generate integrity rules."""

    rules = '''
class ConsistencyRules:
    """Common consistency checks"""

    @staticmethod
    def order_total_matches_items(read_model: Dict) -> tuple:
        """
        Integrity: total = sum(items * qty * price)

        Returns: (rule_name, is_valid)
        """
        if "items" not in read_model or "total" not in read_model:
            return ("order_total_matches", True)  # Can't check

        calculated_total = sum(
            item.get("price", 0) * item.get("qty", 0)
            for item in read_model.get("items", [])
        )

        actual_total = read_model.get("total", 0)

        return (
            "order_total_matches",
            abs(calculated_total - actual_total) < 0.01  # Allow rounding
        )

    @staticmethod
    def no_negative_amounts(read_model: Dict) -> tuple:
        """Integrity: no negative amounts"""
        total = read_model.get("total", 0)
        return ("no_negative_amounts", total >= 0)

    @staticmethod
    def has_required_fields(read_model: Dict, required_fields: List[str]) -> tuple:
        """Integrity: has all required fields"""
        missing = [f for f in required_fields if f not in read_model]
        return ("has_required_fields", len(missing) == 0)

    @staticmethod
    def timestamps_chronological(read_model: Dict) -> tuple:
        """Integrity: timestamps in chronological order"""
        if "events" not in read_model:
            return ("timestamps_chronological", True)

        timestamps = [e.get("timestamp") for e in read_model.get("events", [])]
        for i in range(len(timestamps) - 1):
            if timestamps[i] > timestamps[i + 1]:
                return ("timestamps_chronological", False)

        return ("timestamps_chronological", True)
'''

    return rules


def generate_monitoring_dashboard() -> str:
    """Generate monitoring dashboard."""

    dashboard = '''
class ConsistencyMonitoringDashboard:
    """Monitor consistency continuously"""

    def __init__(self, checker: ReadModelConsistencyChecker):
        self.checker = checker
        self.checks = []
        self.alerts = []

    def schedule_check(
        self,
        aggregate_id: str,
        interval_seconds: int = 60
    ) -> None:
        """Schedule periodic consistency check"""
        self.checks.append({
            "aggregate_id": aggregate_id,
            "interval": interval_seconds,
            "last_check": None,
            "next_check": datetime.utcnow()
        })

    def run_scheduled_checks(self) -> List[Dict]:
        """Run all due checks"""
        results = []
        now = datetime.utcnow()

        for check in self.checks:
            if now >= check["next_check"]:
                result = self.checker.run_full_check(check["aggregate_id"])
                results.append(result)

                # Alert if unhealthy
                if result["overall_health"] != "green":
                    self.alerts.append({
                        "aggregate_id": check["aggregate_id"],
                        "health": result["overall_health"],
                        "timestamp": now.isoformat(),
                        "reason": result
                    })

                check["last_check"] = now
                check["next_check"] = now + \
                    datetime.timedelta(seconds=check["interval"])

        return results

    def get_alerts(self) -> List[Dict]:
        """Get recent alerts"""
        return self.alerts[-10:]  # Last 10 alerts

    def clear_alerts(self) -> None:
        """Clear alert history"""
        self.alerts = []
'''

    return dashboard


def generate_consistency_system() -> dict:
    """Generate complete consistency system."""

    imports = '''from typing import Any, Callable, Dict, List, Optional
from datetime import datetime, timedelta


'''

    module_doc = '''"""
Read Model Consistency Checker

Monitors eventual consistency between write and read models.

CQRS systems are eventually consistent:
- Write model (events): immediately consistent
- Read models (projections): lag behind by milliseconds to seconds

Acceptable? Yes. But need to monitor and detect issues.

Checks performed:
1. Lag: milliseconds behind write model
   - < 100ms: excellent
   - < 1s: good
   - > 5s: alert

2. Completeness: all events projected?
   - Count events in write model
   - Count projections in read model
   - Should match

3. Accuracy: read model matches write model?
   - Load aggregate from events (write model)
   - Load from read model
   - Compare state
   - Should match

4. Integrity: data internally consistent?
   - Run invariant checks
   - Example: total = sum(items)
   - Should pass

Health levels:
- Green: all checks pass, lag < 100ms
- Yellow: lag > 5s but improving
- Red: missing events, mismatches, integrity violated

Alert on Red conditions.
"""
'''

    checker = generate_consistency_checker()
    rules = generate_consistency_rules()
    dashboard = generate_monitoring_dashboard()

    complete_code = imports + module_doc + "\n" + checker + "\n" + rules + "\n" + dashboard

    return {
        "code": complete_code,
        "pattern": "Read Model Consistency Checker",
        "module": "read_model_consistency_checker.py",
    }


def main():
    parser = argparse.ArgumentParser(description="Generate read model consistency checker")
    parser.add_argument("--aggregate", help="Aggregate type")
    parser.add_argument("--output", choices=["json", "code"], default="code")

    args = parser.parse_args()
    result = generate_consistency_system()

    if args.output == "json":
        metadata = {k: v for k, v in result.items() if k != "code"}
        print(json.dumps(metadata, indent=2))
    else:
        print(result["code"])


if __name__ == "__main__":
    main()
