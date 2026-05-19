#!/usr/bin/env python3
"""
Phase 5 Microservices: Observability & Monitoring

Observability: See inside your system.

Three pillars:
1. Metrics: Numbers (latency, error rate, throughput)
2. Logs: Events (what happened)
3. Traces: Flow (which services called which)

Problem: System slow
- Which service is bottleneck?
- Which queries are slow?
- Are users affected?
- What's the root cause?

Without observability: blind guessing

With observability:
- Traces: show request path
- Metrics: show latency at each step
- Logs: show errors
- Root cause: clear
"""

from typing import Dict, List, Optional
from datetime import datetime


def generate_metrics_collector() -> str:
    """Generate metrics collection."""

    metrics = '''
class MetricsCollector:
    """
    Collect system metrics.

    Metrics types:
    - Counter: increases (requests, errors)
    - Gauge: current value (memory, CPU)
    - Histogram: distribution (latency)
    - Summary: percentiles (p50, p95, p99)
    """

    def __init__(self):
        self._counters = {}  # name → count
        self._gauges = {}  # name → value
        self._histograms = {}  # name → [values]

    def increment_counter(self, name: str, value: int = 1) -> None:
        """Increment counter"""
        if name not in self._counters:
            self._counters[name] = 0
        self._counters[name] += value

    def set_gauge(self, name: str, value: float) -> None:
        """Set gauge value"""
        self._gauges[name] = value

    def record_histogram(self, name: str, value: float) -> None:
        """Record histogram value"""
        if name not in self._histograms:
            self._histograms[name] = []
        self._histograms[name].append(value)

    def get_metrics(self) -> Dict:
        """Get all metrics"""
        return {
            "counters": self._counters.copy(),
            "gauges": self._gauges.copy(),
            "histograms": {
                name: self._percentiles(values)
                for name, values in self._histograms.items()
            }
        }

    def _percentiles(self, values: List[float]) -> Dict:
        """Calculate percentiles"""
        if not values:
            return {}

        sorted_vals = sorted(values)
        n = len(sorted_vals)

        return {
            "p50": sorted_vals[n // 2],
            "p95": sorted_vals[int(n * 0.95)],
            "p99": sorted_vals[int(n * 0.99)]
        }
'''

    return metrics


def generate_alerting() -> str:
    """Generate alerting system."""

    alerting = '''
class AlertingRules:
    """
    Alert when metrics exceed thresholds.

    Examples:
    - Error rate > 1%: page on-call
    - Latency p99 > 500ms: investigation
    - Disk full: warning
    - Service down: immediate alert
    """

    def __init__(self):
        self._rules = []
        self._active_alerts = []

    def add_rule(
        self,
        name: str,
        condition: str,  # "error_rate > 0.01"
        threshold: float,
        severity: str  # low, medium, high, critical
    ) -> None:
        """Define alert rule"""
        self._rules.append({
            "name": name,
            "condition": condition,
            "threshold": threshold,
            "severity": severity
        })

    def evaluate_metrics(self, metrics: Dict) -> None:
        """Check metrics against rules"""
        # Example: check error_rate > 0.01
        error_rate = metrics.get("error_rate", 0)

        for rule in self._rules:
            if "error_rate" in rule["condition"]:
                if error_rate > rule["threshold"]:
                    self._active_alerts.append({
                        "rule": rule["name"],
                        "metric": "error_rate",
                        "value": error_rate,
                        "triggered_at": datetime.utcnow().isoformat()
                    })

    def get_active_alerts(self) -> List[Dict]:
        """Get current alerts"""
        return self._active_alerts.copy()
'''

    return alerting


def generate_observability_system() -> dict:
    """Generate complete observability system."""

    imports = '''from typing import Dict, List, Optional
from datetime import datetime


'''

    module_doc = '''"""
Phase 5 Observability: Monitoring, Alerting, Debugging

See what's happening in your system (Prometheus, Datadog, New Relic).

METRICS (Numbers):
- Latency: p50=10ms, p95=50ms, p99=100ms
- Error rate: 0.1% of requests fail
- Throughput: 1000 requests/second
- Resource usage: CPU 40%, Memory 60%, Disk 70%
- Business: revenue/hour, active_users, conversion_rate

LOGS (Events):
- "Request started: GET /products"
- "Database query took 50ms"
- "Error: timeout after 30s"
- "User signed up"
- "Payment processed"

TRACES (Flow):
- Request ID: abc123
- API Gateway (0-10ms)
  → UserService (10-30ms)
    → Database (15-25ms)
  → OrderService (35-90ms)
- Total: 0-90ms

RED METHOD (monitoring):
- Rate: requests per second
- Errors: failed requests per second
- Duration: latency (p50, p95, p99)

USE METHOD (resources):
- Utilization: % CPU, memory, disk
- Saturation: queue depth, thread pool
- Errors: error count, error rate

ALERTING EXAMPLES:

1. Immediate (Critical):
   - Service down
   - Error rate > 5%
   - Disk full

2. Investigation (High):
   - Latency p99 > 500ms
   - Error rate > 1%
   - Memory > 90%

3. Information (Medium):
   - Latency p95 > 200ms
   - Error rate > 0.1%

DASHBOARD EXAMPLE:
- Top left: Requests/sec (time series)
- Top right: Error rate (gauge)
- Bottom left: Latency p99 (gauge)
- Bottom right: Top slow endpoints (table)
"""
'''

    metrics = generate_metrics_collector()
    alerting = generate_alerting()

    complete_code = imports + module_doc + "\n" + metrics + "\n" + alerting

    return {
        "code": complete_code,
        "pattern": "Observability",
        "module": "phase5_observability.py"
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate observability system")
    args = parser.parse_args()
    result = generate_observability_system()
    print(result["code"])


if __name__ == "__main__":
    main()
