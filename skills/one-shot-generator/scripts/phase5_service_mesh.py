#!/usr/bin/env python3
"""
Phase 5 Microservices: Service Mesh (Istio-like)

Service Mesh: Observability + reliability for microservices.

Problem: 10+ microservices communicating = complex network
- Which services call which?
- What's the latency between services?
- How do we retry when service fails?
- How do we do traffic splitting (canary deployments)?
- How do we enforce security (mTLS)?

Service Mesh (solution):
- Sidecar proxy on each service
- Intercept all service-to-service traffic
- Centralized control (manage retries, timeouts, routing)
- Observability (trace requests, collect metrics)
- Security (mTLS between services)
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime


def generate_service_mesh_proxy() -> str:
    """Generate service mesh sidecar proxy."""

    proxy = '''
class ServiceMeshProxy:
    """
    Sidecar Proxy: Intercepts and manages service traffic.

    Responsibilities:
    - Intercept outgoing requests (to other services)
    - Apply routing policies
    - Enforce retries & timeouts
    - Collect metrics (latency, errors)
    - Enforce mTLS (encrypted service-to-service)
    """

    def __init__(self, service_name: str):
        self.service_name = service_name
        self._routing_policies = {}  # dest_service → policy
        self._metrics = []

    def add_routing_policy(
        self,
        destination: str,
        rule: str,  # match condition
        target: str  # where to route
    ) -> None:
        """Add routing policy"""
        if destination not in self._routing_policies:
            self._routing_policies[destination] = []

        self._routing_policies[destination].append({
            "rule": rule,
            "target": target
        })

    def intercept_request(
        self,
        destination: str,
        request: Dict
    ) -> Tuple[str, Dict]:
        """Intercept outgoing request"""
        # 1. Find routing policy
        policies = self._routing_policies.get(destination, [])

        # 2. Match against rules and apply policy
        target = destination
        for policy in policies:
            if self._matches_rule(request, policy["rule"]):
                target = policy["target"]
                break

        # 3. Retry logic
        retries = 3
        for attempt in range(retries):
            try:
                # Forward request (simplified)
                response = self._forward_request(target, request)

                # Log metrics
                self._record_metric(destination, target, "success")

                return target, response
            except Exception as e:
                if attempt == retries - 1:
                    self._record_metric(destination, target, "failure")
                    raise

        return target, {}

    def _matches_rule(self, request: Dict, rule: str) -> bool:
        """Check if request matches routing rule"""
        # In production: parse rule (e.g., "path=/api/v2/*")
        return True

    def _forward_request(self, target: str, request: Dict) -> Dict:
        """Forward request to target service"""
        # In production: make actual HTTP call
        return {"status": 200}

    def _record_metric(
        self,
        source: str,
        destination: str,
        result: str
    ) -> None:
        """Record metric for observability"""
        self._metrics.append({
            "source": self.service_name,
            "destination": destination,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        })

    def get_metrics(self) -> List[Dict]:
        """Get collected metrics"""
        return self._metrics.copy()
'''

    return proxy


def generate_control_plane() -> str:
    """Generate service mesh control plane."""

    cp = '''
class ServiceMeshControlPlane:
    """
    Control Plane: Centralized management of service mesh.

    Manages:
    - Service discovery (know all services + versions)
    - Routing policies (how traffic flows)
    - Traffic management (canary, blue-green)
    - Security (mTLS certificates, policies)
    - Observability (metrics collection rules)
    """

    def __init__(self):
        self._services = {}  # service_name → instances
        self._policies = {}  # policy_name → policy_config
        self._certificates = {}  # service_name → mTLS cert

    def register_service(
        self,
        service_name: str,
        version: str,
        instances: List[str]
    ) -> None:
        """Register service with instances"""
        self._services[service_name] = {
            "version": version,
            "instances": instances,
            "registered_at": datetime.utcnow().isoformat()
        }

    def create_routing_policy(
        self,
        policy_name: str,
        source: str,
        destination: str,
        rules: List[Dict]
    ) -> None:
        """Create traffic routing policy"""
        self._policies[policy_name] = {
            "source": source,
            "destination": destination,
            "rules": rules
        }

    def create_canary_deployment(
        self,
        service_name: str,
        stable_version: str,
        canary_version: str,
        canary_percentage: int
    ) -> None:
        """Deploy new version to small % of traffic"""
        policy = {
            "type": "canary",
            "service": service_name,
            "stable": stable_version,
            "canary": canary_version,
            "canary_percentage": canary_percentage
        }

        self._policies[f"canary-{service_name}"] = policy

    def issue_mtls_certificate(self, service_name: str) -> str:
        """Issue mTLS certificate for service"""
        cert = {
            "service": service_name,
            "issued_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + datetime.timedelta(days=365)).isoformat()
        }

        self._certificates[service_name] = cert
        return f"cert-{service_name}"

    def get_service_info(self, service_name: str) -> Optional[Dict]:
        """Get service info (discovery)"""
        return self._services.get(service_name)
'''

    return cp


def generate_service_mesh_system() -> dict:
    """Generate complete service mesh system."""

    imports = '''from typing import Dict, List, Optional, Tuple
from datetime import datetime


'''

    module_doc = '''"""
Phase 5 Service Mesh: Microservices Reliability & Observability

Istio-like architecture: Proxy + Control Plane.

ARCHITECTURE:
- Control Plane: Central config (policies, routing, certs)
- Data Plane: Sidecar proxies on each service
- Observability: Metrics, traces, logs collected by proxies

SIDECAR PROXY:
- Runs on each pod/container with service
- Intercepts ALL traffic (inbound + outbound)
- Applies policies (retries, timeouts, rate limiting)
- Collects metrics (latency, errors, throughput)
- Enforces mTLS (encrypted service-to-service)
- Can be transparent (no code changes needed)

CONTROL PLANE:
- Manages configuration
- Pushes policies to proxies
- Service discovery
- Traffic management
- Security policies
- Certificate management

USE CASES:

1. CANARY DEPLOYMENT
   - 90% traffic → v1.0 (stable)
   - 10% traffic → v1.1 (canary)
   - Monitor metrics (latency, errors)
   - If v1.1 good: increase to 25%, 50%, 100%
   - If v1.1 bad: rollback to v1.0

2. CIRCUIT BREAKER
   - Service B is failing
   - Proxy stops sending requests
   - Returns error immediately (fail fast)
   - After 30s, tries again
   - Once healthy, resume normal

3. RETRIES
   - Request to Service B fails
   - Proxy retries up to 3 times
   - Exponential backoff (wait 100ms, 200ms, 400ms)
   - Limits: only retry on 5xx errors, not 4xx

4. METRICS
   - Latency: p50=10ms, p95=50ms, p99=100ms
   - Error rate: 0.1% of requests fail
   - Throughput: 1000 requests/sec
   - Which services call which (dependency graph)

5. mTLS
   - Service A → Service B: encrypted
   - Mutual authentication (A verifies B, B verifies A)
   - Automatic certificate rotation
   - No changes to application code
"""
'''

    proxy = generate_service_mesh_proxy()
    cp = generate_control_plane()

    complete_code = imports + module_doc + "\n" + proxy + "\n" + cp

    return {
        "code": complete_code,
        "pattern": "Service Mesh",
        "module": "phase5_service_mesh.py"
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate service mesh")
    args = parser.parse_args()
    result = generate_service_mesh_system()
    print(result["code"])


if __name__ == "__main__":
    main()
