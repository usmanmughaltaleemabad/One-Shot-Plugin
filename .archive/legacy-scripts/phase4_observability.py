#!/usr/bin/env python3
"""
Phase 4 Observability and Monitoring

Observe system behavior in production.

The three pillars:
1. Metrics: numbers (latency, throughput, errors)
2. Logs: events (what happened)
3. Traces: causality (request path through system)

Why?
- Unknown unknowns: system behaves unexpectedly
- Debugging: understand what happened post-incident
- Alerting: detect problems before users notice
- Capacity planning: predict when to scale

Metrics to track:
- Latency: request duration (p50, p95, p99)
- Throughput: requests per second
- Error rate: % failed
- Queue depth: waiting requests
- Cache hit rate: % cached vs fresh

Usage:
    python phase4_observability.py --metric-type latency

Input: Metric type
Output: Observability framework with metrics and alerts
"""

import argparse
import json
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime


def generate_metrics_collector() -> str:
    """Generate metrics collector."""

    collector = '''
class MetricsCollector:
    """
    Collect system metrics.

    Metric types:
    - Counter: cumulative (total requests)
    - Gauge: current value (queue depth)
    - Histogram: distribution (latencies)
    """

    def __init__(self):
        self._counters = {}  # name → count
        self._gauges = {}  # name → current_value
        self._histograms = {}  # name → [values]

    def counter(self, name: str, increment: float = 1.0) -> None:
        """Record counter"""
        self._counters[name] = self._counters.get(name, 0) + increment

    def gauge(self, name: str, value: float) -> None:
        """Record gauge (current value)"""
        self._gauges[name] = value

    def histogram(self, name: str, value: float) -> None:
        """Record histogram (distribution)"""
        if name not in self._histograms:
            self._histograms[name] = []
        self._histograms[name].append(value)

    def get_metrics(self) -> Dict:
        """Get all metrics"""
        return {
            "counters": self._counters,
            "gauges": self._gauges,
            "histograms": self._compute_histogram_stats()
        }

    def _compute_histogram_stats(self) -> Dict:
        """Compute percentiles from histograms"""
        stats = {}

        for name, values in self._histograms.items():
            if not values:
                continue

            sorted_values = sorted(values)
            n = len(sorted_values)

            stats[name] = {
                "count": n,
                "min": sorted_values[0],
                "max": sorted_values[-1],
                "avg": sum(values) / n,
                "p50": sorted_values[n // 2],
                "p95": sorted_values[int(n * 0.95)],
                "p99": sorted_values[int(n * 0.99)]
            }

        return stats
'''

    return collector


def generate_alerting() -> str:
    """Generate alerting rules."""

    alerting = '''
class AlertingRules:
    """
    Alert on metric thresholds.

    Alerting rule:
    - Condition: error_rate > 5%
    - Duration: for 5 minutes
    - Severity: critical
    - Action: page on-call engineer
    """

    def __init__(self, metrics: MetricsCollector):
        self.metrics = metrics
        self.rules = []
        self.active_alerts = []

    def add_rule(
        self,
        name: str,
        metric: str,
        condition: str,  # >, <, ==
        threshold: float,
        duration_seconds: int,
        severity: str  # warning, critical
    ) -> None:
        """Add alerting rule"""
        self.rules.append({
            "name": name,
            "metric": metric,
            "condition": condition,
            "threshold": threshold,
            "duration": duration_seconds,
            "severity": severity
        })

    def check_rules(self) -> List[Dict]:
        """Check all rules against current metrics"""
        alerts = []

        for rule in self.rules:
            metric_name = rule["metric"]
            current_value = self.metrics._gauges.get(metric_name, 0)

            # Check condition
            triggered = False
            if rule["condition"] == ">" and current_value > rule["threshold"]:
                triggered = True
            elif rule["condition"] == "<" and current_value < rule["threshold"]:
                triggered = True

            if triggered:
                alerts.append({
                    "rule": rule["name"],
                    "metric": metric_name,
                    "current_value": current_value,
                    "threshold": rule["threshold"],
                    "severity": rule["severity"],
                    "timestamp": datetime.utcnow().isoformat()
                })

        self.active_alerts = alerts
        return alerts

    def get_alerts(self) -> List[Dict]:
        """Get current active alerts"""
        return self.active_alerts
'''

    return alerting


def generate_observability_system() -> dict:
    """Generate complete observability system."""

    imports = '''from typing import Any, Dict, List, Optional
from datetime import datetime


'''

    module_doc = '''"""
Observability and Monitoring

Observe system behavior in production.

Three pillars of observability:

1. METRICS: Numbers
   - Latency: How long does operation take?
   - Throughput: How many operations per second?
   - Error rate: What % of operations fail?
   - Queue depth: How many waiting?

2. LOGS: Events
   - What happened?
   - When?
   - Who did it?
   - Result?

3. TRACES: Causality
   - How does request flow through system?
   - Where does it slow down?
   - Which service fails?

Key metrics to track:

Request Latency (p50, p95, p99):
- p50 (median): typical user experience
- p95: 95% of users see this or better
- p99: worst 1% (identify slow requests)

Error Rate:
- % of failed requests
- Alert if > 1% (something broken)

Cache Hit Rate:
- % of requests served from cache
- Indicates performance bottleneck if < 80%

Queue Depth:
- How many requests waiting?
- Alert if > 100 (system overloaded)

Alerting examples:

Rule 1: High error rate
- Metric: error_rate
- Condition: > 5%
- Severity: critical
- Action: page on-call

Rule 2: High latency
- Metric: p99_latency
- Condition: > 1000ms
- Severity: warning
- Action: notify team

Rule 3: Low cache hit rate
- Metric: cache_hit_rate
- Condition: < 80%
- Severity: warning
- Action: investigate
"""
'''

    collector = generate_metrics_collector()
    alerting = generate_alerting()

    complete_code = imports + module_doc + "\n" + collector + "\n" + alerting

    return {
        "code": complete_code,
        "pattern": "Observability and Monitoring",
        "module": "observability.py",
    }


def main():
    parser = argparse.ArgumentParser(description="Generate observability module")
    parser.add_argument("--metric-type", help="Metric type")
    parser.add_argument("--output", choices=["json", "code"], default="code")

    args = parser.parse_args()
    result = generate_observability_system()

    if args.output == "json":
        metadata = {k: v for k, v in result.items() if k != "code"}
        print(json.dumps(metadata, indent=2))
    else:
        print(result["code"])


if __name__ == "__main__":
    main()
