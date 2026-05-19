#!/usr/bin/env python3
"""
Phase 5 Observability: Metrics & Dashboards

Metrics: Quantifiable measurement of system behavior.

Problem: Black box monitoring
- "Is the service slow?" Don't know until users complain
- "How many errors?" Manual log grepping
- "Which service is the bottleneck?" Guessing

Metrics (solution):
- Counters: total requests, errors, deployments
- Gauges: CPU%, memory, active connections
- Histograms: request latency distribution
- Dashboard: visualize in real-time (Grafana)
- Alert: if metric exceeds threshold
"""

from typing import Dict, List, Optional
from datetime import datetime
from collections import defaultdict


def generate_metrics_dashboards() -> str:
    """Generate metrics and dashboards system."""

    metrics = '''
class MetricsCollector:
    """
    Collect metrics: counters, gauges, histograms.

    Types:
    - Counter: monotonic increase (requests, errors)
    - Gauge: up/down value (CPU%, memory)
    - Histogram: distribution (latency)
    """

    def __init__(self):
        self._counters = defaultdict(int)  # name → count
        self._gauges = {}  # name → value
        self._histograms = defaultdict(list)  # name → [values]
        self._timeseries = {}  # metric → {timestamp → value}

    def counter_increment(self, name: str, labels: Dict = None, amount: int = 1) -> None:
        """Increment counter"""
        key = self._make_key(name, labels)
        self._counters[key] += amount

    def gauge_set(self, name: str, value: float, labels: Dict = None) -> None:
        """Set gauge to value"""
        key = self._make_key(name, labels)
        self._gauges[key] = value

        # Track timeseries
        if name not in self._timeseries:
            self._timeseries[name] = {}
        self._timeseries[name][datetime.utcnow().isoformat()] = value

    def histogram_observe(self, name: str, value: float, labels: Dict = None) -> None:
        """Record histogram observation"""
        key = self._make_key(name, labels)
        self._histograms[key].append(value)

    def _make_key(self, name: str, labels: Dict = None) -> str:
        """Create metric key with labels"""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def get_counter(self, name: str, labels: Dict = None) -> int:
        """Get counter value"""
        key = self._make_key(name, labels)
        return self._counters.get(key, 0)

    def get_gauge(self, name: str, labels: Dict = None) -> Optional[float]:
        """Get gauge value"""
        key = self._make_key(name, labels)
        return self._gauges.get(key)

    def get_histogram_stats(self, name: str, labels: Dict = None) -> Dict:
        """Get histogram statistics"""
        key = self._make_key(name, labels)
        values = self._histograms.get(key, [])

        if not values:
            return None

        sorted_vals = sorted(values)
        return {
            "name": name,
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": sum(values) / len(values),
            "p50": sorted_vals[len(values) // 2],
            "p95": sorted_vals[int(len(values) * 0.95)],
            "p99": sorted_vals[int(len(values) * 0.99)]
        }

    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format"""
        lines = []

        for name, value in self._counters.items():
            lines.append(f"# TYPE {name} counter")
            lines.append(f"{name} {value}")

        for name, value in self._gauges.items():
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {value}")

        for name, values in self._histograms.items():
            lines.append(f"# TYPE {name} histogram")
            stats = self.get_histogram_stats(name)
            if stats:
                lines.append(f"{name}_count {stats['count']}")
                lines.append(f"{name}_sum {sum(values)}")

        return "\\n".join(lines)


class DashboardBuilder:
    """Build Grafana-like dashboards."""

    def __init__(self, metrics: MetricsCollector):
        self._metrics = metrics
        self._panels = []

    def add_panel(
        self,
        title: str,
        metric: str,
        type_: str = "graph"  # graph, stat, gauge
    ) -> None:
        """Add dashboard panel"""
        self._panels.append({
            "title": title,
            "metric": metric,
            "type": type_,
            "created_at": datetime.utcnow().isoformat()
        })

    def render(self) -> Dict:
        """Render dashboard"""
        return {
            "title": "Service Dashboard",
            "panels": self._panels,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {
                panel["metric"]: self._metrics.get_gauge(panel["metric"])
                for panel in self._panels
            }
        }
'''

    return metrics


def generate_dashboard_system() -> dict:
    """Generate complete metrics and dashboard system."""

    imports = '''from typing import Dict, List, Optional
from datetime import datetime
from collections import defaultdict


'''

    module_doc = '''"""
Phase 5 Observability: Metrics & Dashboards

Collect quantifiable measurements, visualize in dashboards (Prometheus, Grafana).

METRIC TYPES:

1. COUNTER (only increases)
   - http_requests_total: 1000000
   - errors_total: 523
   - deployments_total: 42
   - Use: count events

2. GAUGE (up or down)
   - cpu_percent: 75
   - memory_bytes: 4294967296
   - active_connections: 523
   - Use: current value

3. HISTOGRAM (distribution)
   - request_latency_ms: [10, 12, 11, 50, 100, 15, ...]
   - p50: 11ms (median)
   - p95: 48ms (95th percentile)
   - p99: 98ms (99th percentile)
   - Use: understand distribution

DASHBOARD PANELS:

Line graph:
- X-axis: time
- Y-axis: metric value
- Example: request latency over 24 hours

Stat (single value):
- Large number displayed
- Color: green (good), red (bad)
- Example: "Error Rate: 0.5%" (green)

Gauge (dial):
- Needle pointing to value
- Red zone: too high
- Green zone: healthy
- Example: CPU% gauge (currently 75%)

EXAMPLE: API Service Dashboard

Panel 1: Request Rate
- Metric: http_requests_total
- Type: line graph
- Shows: requests per minute
- Alert: if < 100 req/min (service down)

Panel 2: Error Rate
- Metric: http_errors_total / http_requests_total
- Type: stat
- Shows: 0.5%
- Alert: if > 1% (bad deployment)

Panel 3: Latency (p95)
- Metric: request_latency_ms p95
- Type: line graph
- Shows: 50ms
- Alert: if > 100ms (slow)

Panel 4: Active Connections
- Metric: active_connections
- Type: gauge
- Shows: 523 connections
- Alert: if > 1000 (resource exhaustion)

MONITORING WORKFLOW:

1. SERVICE EMITS METRICS
   - Counter increment: request_count++
   - Gauge set: cpu_percent = 75
   - Histogram observe: request_latency_ms = 45

2. METRICS COLLECTED
   - Prometheus scrapes: http://service:8080/metrics
   - Stores: timeseries database
   - Retention: 15 days

3. DASHBOARD DISPLAYS
   - Grafana queries Prometheus
   - Renders panels
   - Auto-refreshes every 10 seconds

4. ALERTS
   - Rule: if error_rate > 1% for 5 min
   - Trigger: yes
   - Action: page oncall engineer

GOLDEN SIGNALS (Google SRE book):

1. Latency: How long did request take?
   - Measure: p50, p95, p99
   - Alert: if p99 > 500ms

2. Traffic: How many requests?
   - Measure: requests/sec
   - Alert: if < 10 req/sec (down?)

3. Errors: How many failed?
   - Measure: error rate %
   - Alert: if > 1%

4. Saturation: How full are resources?
   - Measure: CPU%, memory%, disk%
   - Alert: if > 85%

LABEL EXAMPLES (Prometheus):

http_requests_total{method="GET", endpoint="/api/users"}
http_requests_total{method="POST", endpoint="/api/users"}
http_requests_total{method="DELETE", endpoint="/api/users"}

This allows dashboards to:
- Filter by method: only GET requests
- Group by endpoint: which endpoint gets most traffic
- Drill down: see details
"""
'''

    metrics = generate_metrics_dashboards()

    complete_code = imports + module_doc + "\n" + metrics

    return {
        "code": complete_code,
        "pattern": "Metrics & Dashboards",
        "module": "phase5_metrics_dashboards.py"
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate metrics and dashboards")
    args = parser.parse_args()
    result = generate_dashboard_system()
    print(result["code"])


if __name__ == "__main__":
    main()
