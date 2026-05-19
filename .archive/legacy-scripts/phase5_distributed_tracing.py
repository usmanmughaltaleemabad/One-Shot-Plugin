#!/usr/bin/env python3
"""
Phase 5 Microservices: Distributed Tracing (Jaeger-like)

Problem: Request spans 10+ microservices
- User clicks button
- API Gateway calls UserService
- UserService calls OrderService
- OrderService calls PaymentService
- PaymentService calls BankingService
- Total latency: 500ms

Where did the time go?
- UserService: 50ms
- OrderService: 100ms
- PaymentService: 300ms
- BankingService: 50ms

Distributed Tracing: Follow request across services.
"""

from typing import Dict, List, Optional
from datetime import datetime
import uuid


def generate_distributed_tracing() -> str:
    """Generate distributed tracing system."""

    tracing = '''
class DistributedTracer:
    """
    Distributed Tracing: Track request across services.

    Trace ID: Unique identifier (e.g., abc123)
    Span: Unit of work in one service (db query, API call)
    Span ID: Unique identifier for span
    Parent Span ID: Which span called this one

    Example trace:
    - Trace: abc123
      - Span: APIGateway (0-100ms)
        - Span: UserService (10-30ms)
          - Span: Database query (15-25ms)
        - Span: OrderService (35-90ms)
          - Span: Cache lookup (36-40ms)
          - Span: Database query (50-88ms)
    """

    def __init__(self):
        self._spans = []
        self._traces = {}  # trace_id → spans

    def start_trace(self) -> str:
        """Start new trace (usually at entry point)"""
        trace_id = str(uuid.uuid4())
        self._traces[trace_id] = []
        return trace_id

    def start_span(
        self,
        trace_id: str,
        span_name: str,
        parent_span_id: Optional[str] = None
    ) -> str:
        """Start span within trace"""
        span_id = str(uuid.uuid4())

        span = {
            "trace_id": trace_id,
            "span_id": span_id,
            "parent_span_id": parent_span_id,
            "name": span_name,
            "start_time": datetime.utcnow().isoformat(),
            "tags": {},  # service, method, status
            "logs": []  # events within span
        }

        self._spans.append(span)
        if trace_id in self._traces:
            self._traces[trace_id].append(span)

        return span_id

    def add_tag(self, trace_id: str, span_id: str, key: str, value: str) -> None:
        """Add tag to span (service, method, etc.)"""
        for span in self._spans:
            if span["span_id"] == span_id:
                span["tags"][key] = value
                break

    def add_log(self, trace_id: str, span_id: str, message: str) -> None:
        """Add log entry to span"""
        for span in self._spans:
            if span["span_id"] == span_id:
                span["logs"].append({
                    "message": message,
                    "timestamp": datetime.utcnow().isoformat()
                })
                break

    def end_span(self, trace_id: str, span_id: str) -> None:
        """End span (record end time)"""
        for span in self._spans:
            if span["span_id"] == span_id:
                span["end_time"] = datetime.utcnow().isoformat()
                break

    def get_trace(self, trace_id: str) -> Optional[Dict]:
        """Get full trace (all spans)"""
        if trace_id not in self._traces:
            return None

        spans = self._traces[trace_id]
        return {
            "trace_id": trace_id,
            "spans": spans,
            "total_duration_ms": self._calculate_duration(spans)
        }

    def _calculate_duration(self, spans: List[Dict]) -> float:
        """Calculate total trace duration"""
        if not spans:
            return 0

        start = datetime.fromisoformat(spans[0]["start_time"])
        end = datetime.fromisoformat(spans[-1].get("end_time", datetime.utcnow().isoformat()))

        return (end - start).total_seconds() * 1000
'''

    return tracing


def generate_trace_visualization() -> str:
    """Generate trace visualization & analysis."""

    viz = '''
class TraceAnalyzer:
    """
    Analyze traces to find performance issues.

    Examples:
    - "Why is this request slow?"
      - 90% time in PaymentService
      - PaymentService is calling BankAPI (external, slow)
      - Fix: cache PaymentService responses

    - "Which services are slowest?"
      - PaymentService: p99 = 500ms
      - DatabaseService: p99 = 200ms
      - Fix: optimize PaymentService or add caching

    - "Which services are failing?"
      - UserService: 0.1% error rate
      - OrderService: 1.5% error rate (Problem!)
      - Fix: investigate OrderService
    """

    def __init__(self):
        self._latency_stats = {}  # service → [latencies]
        self._error_counts = {}  # service → error_count

    def analyze_trace(self, trace: Dict) -> Dict:
        """Analyze single trace"""
        spans = trace.get("spans", [])

        analysis = {
            "trace_id": trace["trace_id"],
            "total_duration_ms": trace.get("total_duration_ms", 0),
            "services_involved": [],
            "slowest_span": None,
            "errors": []
        }

        # Find slowest span
        max_duration = 0
        for span in spans:
            service = span["tags"].get("service", "unknown")
            analysis["services_involved"].append(service)

            start = datetime.fromisoformat(span["start_time"])
            end = datetime.fromisoformat(span.get("end_time", span["start_time"]))
            duration = (end - start).total_seconds() * 1000

            if duration > max_duration:
                max_duration = duration
                analysis["slowest_span"] = {
                    "service": service,
                    "name": span["name"],
                    "duration_ms": duration
                }

            # Check for errors in logs
            for log in span.get("logs", []):
                if "error" in log["message"].lower():
                    analysis["errors"].append({
                        "service": service,
                        "message": log["message"]
                    })

        return analysis
'''

    return viz


def generate_tracing_system() -> dict:
    """Generate complete distributed tracing system."""

    imports = '''from typing import Dict, List, Optional
from datetime import datetime
import uuid


'''

    module_doc = '''"""
Phase 5 Distributed Tracing: Request Flow Visualization

Follow requests across 10+ microservices (Jaeger/Zipkin).

PROBLEM:
User submits order → takes 800ms (too slow!)
- Where did time go?
- Which service is bottleneck?
- Did any service fail?

SOLUTION: Distributed tracing

REQUEST FLOW WITH TRACING:
1. Client requests /api/orders
2. API Gateway generates Trace ID (abc123)
3. Calls OrderService, passes Trace ID
4. OrderService starts Span, calls PaymentService
5. PaymentService starts Span, calls BankingAPI
6. Responses bubble up, spans end
7. Trace complete: all spans collected

SPAN DATA:
- trace_id: abc123 (identifies request)
- span_id: xyz789 (identifies this service's work)
- parent_span_id: def456 (which span called this)
- service: order-service
- operation: create_order
- start_time: 2026-05-17T10:00:00.000Z
- end_time: 2026-05-17T10:00:00.250Z
- tags: {user_id: 123, status: success}
- logs: ["Started processing", "Saved to database", "Sent response"]

ANALYSIS:
- Slowest: PaymentService (500ms)
- Root cause: Calling external BankAPI (latency)
- Fix: cache results, add circuit breaker, retry

VISUALIZATION:
Timeline showing all spans:
APIGateway (0-800ms)
  OrderService (10-500ms)
    Database (20-100ms)
    PaymentService (110-490ms)
      BankAPI (120-480ms)
"""
'''

    tracing = generate_distributed_tracing()
    viz = generate_trace_visualization()

    complete_code = imports + module_doc + "\n" + tracing + "\n" + viz

    return {
        "code": complete_code,
        "pattern": "Distributed Tracing",
        "module": "phase5_distributed_tracing.py"
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate distributed tracing")
    args = parser.parse_args()
    result = generate_tracing_system()
    print(result["code"])


if __name__ == "__main__":
    main()
