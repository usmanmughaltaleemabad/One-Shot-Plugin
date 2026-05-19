#!/usr/bin/env python3
"""
Phase 5 Microservices: Health Checks & Readiness Probes

Health Check: Is service alive?
Readiness Probe: Is service ready to handle traffic?

Liveness: "Is container running?"
- If no: kill + restart

Readiness: "Can service handle requests?"
- If no: remove from load balancer, but don't kill

Startup: "Did service start successfully?"
- If no: fail container start

Types:
- HTTP: GET /health → 200 OK
- TCP: Can connect to port?
- Exec: Run command, check exit code
"""

from typing import Dict, Optional
from datetime import datetime


def generate_health_checks() -> str:
    """Generate health check system."""

    health = '''
class HealthChecker:
    """
    Monitor service health.

    Checks:
    - Liveness: service alive?
    - Readiness: service ready?
    - Startup: service started?
    """

    def __init__(self):
        self._checks = {
            "liveness": [],
            "readiness": [],
            "startup": []
        }
        self._results = {}

    def add_liveness_check(self, name: str, check_func) -> None:
        """Add liveness check"""
        self._checks["liveness"].append({
            "name": name,
            "func": check_func
        })

    def add_readiness_check(self, name: str, check_func) -> None:
        """Add readiness check"""
        self._checks["readiness"].append({
            "name": name,
            "func": check_func
        })

    def run_liveness_check(self) -> Dict:
        """Run liveness probes"""
        results = {
            "type": "liveness",
            "passed": [],
            "failed": [],
            "timestamp": datetime.utcnow().isoformat()
        }

        for check in self._checks["liveness"]:
            try:
                if check["func"]():
                    results["passed"].append(check["name"])
                else:
                    results["failed"].append(check["name"])
            except Exception as e:
                results["failed"].append(f"{check['name']}: {str(e)}")

        self._results["liveness"] = results
        return results

    def run_readiness_check(self) -> Dict:
        """Run readiness probes"""
        results = {
            "type": "readiness",
            "passed": [],
            "failed": [],
            "timestamp": datetime.utcnow().isoformat()
        }

        for check in self._checks["readiness"]:
            try:
                if check["func"]():
                    results["passed"].append(check["name"])
                else:
                    results["failed"].append(check["name"])
            except Exception as e:
                results["failed"].append(f"{check['name']}: {str(e)}")

        self._results["readiness"] = results
        return results

    def is_healthy(self) -> bool:
        """Overall health status"""
        liveness = self.run_liveness_check()
        return len(liveness["failed"]) == 0

    def is_ready(self) -> bool:
        """Overall readiness status"""
        readiness = self.run_readiness_check()
        return len(readiness["failed"]) == 0
'''

    return health


def generate_health_system() -> dict:
    """Generate complete health check system."""

    imports = '''from typing import Dict, Optional
from datetime import datetime


'''

    module_doc = '''"""
Phase 5 Health Checks: Liveness & Readiness Probes

Kubernetes/orchestrator monitoring (HTTP endpoints).

LIVENESS PROBE: "Is service alive?"

Example checks:
- Process running?
- No deadlocks?
- No fatal errors?

Response:
- 200: alive (don't restart)
- 500: dead (kill + restart)

Typical interval: every 10 seconds
Failure threshold: 3 failures = kill

READINESS PROBE: "Is service ready?"

Example checks:
- Database connected?
- Dependencies reachable?
- Cache warming done?
- Migrations completed?

Response:
- 200: ready (add to load balancer)
- 503: not ready (remove from load balancer)

Typical interval: every 5 seconds
Failure threshold: 3 failures = remove from LB

STARTUP PROBE: "Did service start?"

Only runs during startup
- 200: started (begin liveness/readiness)
- 500: startup failed (kill + restart)

Used for slow-starting apps

TYPICAL HEALTH ENDPOINT:

GET /health
Response (liveness + readiness):
{
  "status": "healthy",
  "liveness": "ok",
  "readiness": "ok",
  "checks": {
    "database": "ok",
    "cache": "ok",
    "external_api": "ok"
  },
  "uptime_seconds": 123456
}

KUBERNETES EXAMPLE:

apiVersion: v1
kind: Pod
metadata:
  name: api-service
spec:
  containers:
  - name: api
    image: api:latest
    livenessProbe:
      httpGet:
        path: /health
        port: 8000
      initialDelaySeconds: 10
      periodSeconds: 10
      failureThreshold: 3
    readinessProbe:
      httpGet:
        path: /ready
        port: 8000
      initialDelaySeconds: 5
      periodSeconds: 5
      failureThreshold: 3
"""
'''

    health = generate_health_checks()

    complete_code = imports + module_doc + "\n" + health

    return {
        "code": complete_code,
        "pattern": "Health Checks",
        "module": "phase5_health_checks.py"
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate health checks")
    args = parser.parse_args()
    result = generate_health_system()
    print(result["code"])


if __name__ == "__main__":
    main()
