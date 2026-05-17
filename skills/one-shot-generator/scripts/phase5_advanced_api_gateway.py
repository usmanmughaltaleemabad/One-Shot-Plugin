#!/usr/bin/env python3
"""
Phase 5 Advanced API Gateway: Traffic Splitting & Request Shadowing

API Gateway: Single entry point for all client requests.

Problem: Direct client-to-service calls
- Clients couple to service locations (IP/port)
- Service A depends on service B directly
- Can't add auth, rate limiting, monitoring without modifying all services
- No A/B testing or canary deployments possible

Advanced API Gateway (solution):
- Single endpoint clients call
- Routes to multiple services (path-based, host-based, header-based)
- Traffic splitting (canary: 90% stable, 10% new)
- Shadow routing (duplicate traffic to new service, discard response)
- Adaptive routing (route based on latency, error rate)
"""

from typing import Dict, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass


@dataclass
class Route:
    path: str
    service: str
    weight: int = 100


def generate_advanced_api_gateway() -> str:
    """Generate advanced API gateway with traffic splitting."""

    gateway = '''
class AdvancedAPIGateway:
    """
    Advanced routing: traffic splitting, shadow routing, adaptive routing.

    Capabilities:
    - Canary deployments: route 10% to new version, 90% to stable
    - Shadow routing: duplicate traffic to test service, discard response
    - Adaptive routing: route based on latency or error rate
    - Rate limiting: per-user, per-IP, per-service
    """

    def __init__(self):
        self._routes = {}  # path → list of Route(service, weight)
        self._traffic_stats = {}  # service → {latency, error_rate}
        self._active_experiments = []  # (start_time, service_a, service_b, split%)

    def add_route(
        self,
        path: str,
        services: List[Dict]  # [{service: "v1", weight: 90}, {service: "v2", weight: 10}]
    ) -> None:
        """Register route with traffic split"""
        if sum(s["weight"] for s in services) != 100:
            raise ValueError("Weights must sum to 100")

        self._routes[path] = services

    def route_request(self, path: str, request_id: str) -> str:
        """Route request based on weights (weighted round-robin)"""
        routes = self._routes.get(path, [])
        if not routes:
            return None

        # Deterministic routing: same request_id → same service
        hash_val = hash(request_id) % 100
        cumulative = 0

        for route in routes:
            cumulative += route["weight"]
            if hash_val < cumulative:
                return route["service"]

        return routes[-1]["service"]

    def shadow_route(
        self,
        path: str,
        request_id: str,
        shadow_service: str
    ) -> tuple:
        """Route to primary, shadow to test service"""
        primary = self.route_request(path, request_id)

        # Execute both (shadow response discarded)
        return {
            "primary_service": primary,
            "shadow_service": shadow_service,
            "primary_active": True,
            "shadow_active": True
        }

    def adaptive_route(self, path: str, request_id: str) -> str:
        """Route based on service latency/error rate"""
        routes = self._routes.get(path, [])
        if not routes:
            return None

        # Prefer services with low latency and error rate
        scored_routes = []
        for route in routes:
            stats = self._traffic_stats.get(route["service"], {})
            latency = stats.get("latency_ms", 100)
            error_rate = stats.get("error_rate", 0)

            # Score: lower is better
            score = latency * (1 + error_rate)
            scored_routes.append((score, route["service"]))

        scored_routes.sort()
        return scored_routes[0][1] if scored_routes else None

    def start_canary(
        self,
        path: str,
        stable_service: str,
        canary_service: str,
        canary_percentage: int
    ) -> str:
        """Start canary deployment"""
        if not 0 < canary_percentage < 100:
            raise ValueError("Canary % must be 1-99")

        self.add_route(
            path,
            [
                {"service": stable_service, "weight": 100 - canary_percentage},
                {"service": canary_service, "weight": canary_percentage}
            ]
        )

        experiment_id = f"canary-{datetime.utcnow().timestamp()}"
        self._active_experiments.append({
            "id": experiment_id,
            "path": path,
            "stable": stable_service,
            "canary": canary_service,
            "percentage": canary_percentage,
            "started_at": datetime.utcnow().isoformat()
        })

        return experiment_id

    def promote_canary(self, experiment_id: str) -> None:
        """Promote canary to stable (100% traffic)"""
        exp = next((e for e in self._active_experiments if e["id"] == experiment_id), None)
        if not exp:
            return

        self.add_route(exp["path"], [{"service": exp["canary"], "weight": 100}])
        self._active_experiments.remove(exp)

    def update_traffic_stats(self, service: str, latency_ms: int, error_rate: float) -> None:
        """Update service metrics for adaptive routing"""
        self._traffic_stats[service] = {
            "latency_ms": latency_ms,
            "error_rate": error_rate,
            "updated_at": datetime.utcnow().isoformat()
        }

    def get_active_routes(self, path: str) -> List[Dict]:
        """Get current route configuration"""
        return self._routes.get(path, [])
'''

    return gateway


def generate_gateway_system() -> dict:
    """Generate complete advanced API gateway system."""

    imports = '''from typing import Dict, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass


'''

    module_doc = '''"""
Phase 5 Advanced API Gateway: Traffic Splitting & Request Shadowing

Single entry point with sophisticated routing strategies (Envoy, Kong pattern).

TRAFFIC SPLITTING:

1. CANARY DEPLOYMENT (Gradual rollout)
   - Route 90% to stable version, 10% to new version
   - Monitor: error rate, latency
   - If good: increase to 20%, 50%, 100%
   - If bad: rollback to 0%, keep stable

2. SHADOW ROUTING (Test without impact)
   - Route request to primary (v1)
   - Duplicate to canary (v2)
   - Discard canary response
   - Use to test new service before traffic
   - Cost: 2x infrastructure temporarily

3. WEIGHTED ROUND-ROBIN (Blue-green)
   - Route 50% to blue, 50% to green
   - Switch instantly when ready
   - Same as canary but atomic switch

4. ADAPTIVE ROUTING (Performance-based)
   - Route to service with lowest latency
   - Avoid services with high error rate
   - Dynamic: re-evaluate on each request
   - Use: load balancing, failover

EXAMPLE: Canary Deployment

Goal: Roll out API v2 to 1% of users, then 5%, 10%, 50%, 100%

Week 1: 1% traffic (real users, small risk)
- 99 requests to v1 (stable)
- 1 request to v2 (canary)
- Monitor: errors, latency, business metrics

Week 2: 5% if good
- 95 to v1, 5 to v2

Week 3: 50% (blue-green)
- 50 to v1, 50 to v2

Week 4: 100% (complete)
- All traffic to v2, v1 decommissioned

MONITORING:

- Canary error rate > 1%? Rollback immediately
- Canary latency > 2x stable? Pause rollout
- User complaints? Investigate
- Business metrics (conversion, revenue)? No change = safe

REQUEST ROUTING DECISION TREE:

Client request → API Gateway
  ↓
Match path: /api/users → "user-service"
  ↓
Lookup route config:
  - v1 (user-service-v1): 90% (weight)
  - v2 (user-service-v2): 10% (weight)
  ↓
Hash(request_id) % 100 = 47
  ↓
47 < 90? YES → route to v1
  ↓
Call v1, return response
"""
'''

    gateway = generate_advanced_api_gateway()

    complete_code = imports + module_doc + "\n" + gateway

    return {
        "code": complete_code,
        "pattern": "Advanced API Gateway",
        "module": "phase5_advanced_api_gateway.py"
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate advanced API gateway")
    args = parser.parse_args()
    result = generate_gateway_system()
    print(result["code"])


if __name__ == "__main__":
    main()
