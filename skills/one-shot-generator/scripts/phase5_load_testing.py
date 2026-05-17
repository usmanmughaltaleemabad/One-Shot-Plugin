#!/usr/bin/env python3
"""
Phase 5 Reliability: Load Testing & Chaos Engineering

Load Testing: Test system under stress.

Questions:
- How many requests/second can system handle?
- When does it start failing?
- What breaks first (database, cache, network)?
- How fast does it recover?

Chaos Engineering:
- Intentionally break things in production
- Kill a server: does system still work?
- Slow down database: does system degrade gracefully?
- Network partition: do we handle it?

Build confidence that system works.
"""

from typing import Dict, List, Optional, Callable
from datetime import datetime


def generate_load_tester() -> str:
    """Generate load testing framework."""

    tester = '''
class LoadTester:
    """
    Test system under load.

    Scenarios:
    - Steady load: 100 requests/sec for 1 hour
    - Ramp up: 0 → 1000 requests/sec over 5 minutes
    - Spike: sudden jump to 5000 requests/sec
    - Wave: oscillate 100-500-100 requests/sec
    """

    def __init__(self):
        self._results = {
            "total_requests": 0,
            "successful": 0,
            "failed": 0,
            "latencies": [],
            "errors": []
        }

    def run_load_test(
        self,
        endpoint: str,
        duration_seconds: int,
        requests_per_second: int,
        request_func: Callable
    ) -> Dict:
        """Run load test"""
        start = datetime.utcnow()

        while (datetime.utcnow() - start).total_seconds() < duration_seconds:
            try:
                response = request_func(endpoint)
                self._results["total_requests"] += 1

                if response.status == 200:
                    self._results["successful"] += 1
                    self._results["latencies"].append(response.latency_ms)
                else:
                    self._results["failed"] += 1

            except Exception as e:
                self._results["failed"] += 1
                self._results["errors"].append(str(e))

        return self.get_results()

    def get_results(self) -> Dict:
        """Get test results"""
        latencies = self._results["latencies"]

        return {
            "total_requests": self._results["total_requests"],
            "successful": self._results["successful"],
            "failed": self._results["failed"],
            "error_rate": self._results["failed"] / max(1, self._results["total_requests"]),
            "latency_p50": sorted(latencies)[len(latencies)//2] if latencies else 0,
            "latency_p95": sorted(latencies)[int(len(latencies)*0.95)] if latencies else 0,
            "latency_p99": sorted(latencies)[int(len(latencies)*0.99)] if latencies else 0
        }
'''

    return tester


def generate_chaos_engineering() -> str:
    """Generate chaos engineering framework."""

    chaos = '''
class ChaosExperiment:
    """
    Run chaos experiments: intentionally break things.

    Experiments:
    1. Kill instance: remove 1 server, system still works
    2. Slow service: add 5 second latency, system degrades gracefully
    3. Network partition: isolate region, detect and failover
    4. Disk full: disk runs out of space, circuit breaker kicks in
    5. Memory leak: OOM kill process, system recovers
    """

    def __init__(self):
        self._experiments = []
        self._results = []

    def kill_instance(self, instance_id: str, duration_seconds: int = 60) -> Dict:
        """Kill instance, watch system"""
        experiment = {
            "type": "kill_instance",
            "target": instance_id,
            "start": datetime.utcnow().isoformat(),
            "duration": duration_seconds,
            "observations": []
        }

        # Monitor during outage
        # - Error rate increases?
        # - Request latency increases?
        # - Traffic reroutes to other instances?
        # - Auto-scaling kicks in?

        return experiment

    def slow_down_service(
        self,
        service_name: str,
        latency_ms: int,
        percentage: float = 1.0
    ) -> Dict:
        """Add latency to service (X% of requests)"""
        experiment = {
            "type": "slow_service",
            "target": service_name,
            "added_latency_ms": latency_ms,
            "percentage": percentage,
            "observations": []
        }

        # Monitor:
        # - Does timeout trigger?
        # - Does circuit breaker open?
        # - Does user-facing latency spike?
        # - Does retry storm occur?

        return experiment

    def run_experiment(self, experiment: Dict) -> None:
        """Run chaos experiment"""
        self._experiments.append(experiment)

        # Log observations during experiment
        # Report findings
'''

    return chaos


def generate_chaos_system() -> dict:
    """Generate complete chaos testing system."""

    imports = '''from typing import Dict, List, Optional, Callable
from datetime import datetime


'''

    module_doc = '''"""
Phase 5 Load Testing & Chaos Engineering: Reliability Validation

Test system breaks gracefully (Gremlin, Chaos Monkey).

LOAD TESTING:

Purpose: Find breaking point

Scenarios:
1. Steady load: 100 req/sec × 1 hour
   - Monitor: CPU, memory, latency
   - Check: no memory leaks, CPU stays stable

2. Ramp up: 0 → 1000 req/sec over 5 min
   - Monitor: auto-scaling triggers
   - Check: scales within 30 seconds

3. Spike: sudden 5000 req/sec
   - Monitor: queue depth, latency
   - Check: stays online, doesn't crash

4. Soak: 500 req/sec × 24 hours
   - Monitor: memory usage
   - Check: no gradual degradation

METRICS TO TRACK:
- Throughput: requests/sec (can it handle load?)
- Latency: p50/p95/p99 (is it fast enough?)
- Error rate: % failures (is it stable?)
- Resource: CPU/memory/disk (is it efficient?)

CHAOS ENGINEERING:

Purpose: Find failure modes

Experiments:
1. KILL INSTANCE
   - Stop 1 server
   - Does traffic reroute?
   - Does circuit breaker kick in?
   - Do users see errors?

2. SLOW SERVICE
   - Add 5s latency to one service
   - Does timeout trigger?
   - Do requests pile up?
   - Does circuit breaker trip?

3. NETWORK PARTITION
   - Block traffic between data centers
   - Does system detect?
   - Does failover happen?
   - Do users see impact?

4. DISK FULL
   - Fill 1 server's disk
   - Does alerting trigger?
   - Does system stay up?
   - Does graceful degradation work?

5. MEMORY LEAK
   - OOM kill a process
   - Does auto-scaling restart?
   - How fast does it recover?
   - Do other instances compensate?

EXPECTED FINDINGS:
- Good: System stays up, traffic reroutes, users see no impact
- OK: System detects issue, fails partially, recovers in < 5 min
- Bad: System crashes, cascading failure, manual intervention needed

CONTINUOUS CHAOS:
- Netflix Chaos Monkey: kill random instances daily
- Gremlin: scheduled chaos experiments
- PagerDuty GameDays: practice incident response
- Run in production (automated, rollback enabled)
"""
'''

    tester = generate_load_tester()
    chaos = generate_chaos_engineering()

    complete_code = imports + module_doc + "\n" + tester + "\n" + chaos

    return {
        "code": complete_code,
        "pattern": "Load Testing & Chaos Engineering",
        "module": "phase5_load_testing.py"
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate load testing & chaos engineering")
    args = parser.parse_args()
    result = generate_chaos_system()
    print(result["code"])


if __name__ == "__main__":
    main()
