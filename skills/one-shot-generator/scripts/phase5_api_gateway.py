#!/usr/bin/env python3
"""
Phase 5 Microservices: API Gateway

API Gateway: Single entry point for all client requests.

Problems without API Gateway:
- Clients call 10+ microservices directly → tight coupling
- Each client handles service discovery, retries, timeouts
- No centralized auth, rate limiting, logging
- Hard to change service locations
- Hard to do version management

API Gateway (solution):
- Single entry point (api.example.com)
- Route requests to correct microservice
- Centralized auth (JWT validation)
- Centralized rate limiting
- Centralized logging & monitoring
- Service discovery (knows where services are)
- Load balancing (distribute traffic)
"""

from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
import json


def generate_api_gateway_router() -> str:
    """Generate API Gateway routing."""

    router = '''
class APIGateway:
    """
    API Gateway: Route requests to microservices.

    Responsibilities:
    - Route by path: /users/* → UserService, /orders/* → OrderService
    - Auth: Validate JWT token
    - Rate limit: Block if too many requests
    - Log: Record all requests
    - Metrics: Track latency, errors, throughput
    - Transform: Adapt response format for client
    """

    def __init__(self):
        self._routes = {}  # path_pattern → service_url
        self._auth_validators = {}  # method_name → validator
        self._request_log = []

    def register_route(self, path_pattern: str, service_url: str) -> None:
        """Register microservice route"""
        self._routes[path_pattern] = service_url

    def handle_request(
        self,
        method: str,
        path: str,
        headers: Dict,
        body: Optional[Dict] = None
    ) -> Dict:
        """Handle incoming request"""
        request_id = f"req-{datetime.utcnow().timestamp()}"

        # 1. Authenticate
        auth_token = headers.get("Authorization", "").replace("Bearer ", "")
        if not self._validate_auth(auth_token):
            return {
                "request_id": request_id,
                "status": 401,
                "error": "Unauthorized"
            }

        # 2. Find target service
        service_url = self._find_service(path)
        if not service_url:
            return {
                "request_id": request_id,
                "status": 404,
                "error": "Service not found"
            }

        # 3. Log request
        self._log_request(request_id, method, path, auth_token)

        # 4. Forward to service (simplified)
        return {
            "request_id": request_id,
            "status": 200,
            "forwarded_to": service_url,
            "path": path,
            "method": method
        }

    def _find_service(self, path: str) -> Optional[str]:
        """Find service for path"""
        for pattern, url in self._routes.items():
            if path.startswith(pattern):
                return url
        return None

    def _validate_auth(self, token: str) -> bool:
        """Validate JWT token"""
        # In production: validate JWT signature, expiration
        return bool(token)

    def _log_request(
        self,
        request_id: str,
        method: str,
        path: str,
        auth_token: str
    ) -> None:
        """Log request for audit trail"""
        self._request_log.append({
            "request_id": request_id,
            "method": method,
            "path": path,
            "timestamp": datetime.utcnow().isoformat()
        })
'''

    return router


def generate_load_balancer() -> str:
    """Generate load balancer."""

    lb = '''
class LoadBalancer:
    """
    Load Balancer: Distribute requests across service instances.

    Strategies:
    - Round-robin: service1, service2, service1, service2
    - Least connections: route to service with fewest active
    - Random: randomly pick service
    - Weighted: 70% to service1, 30% to service2
    - IP hash: same client always goes to same service
    """

    def __init__(self, strategy: str = "round_robin"):
        self._instances = []  # List of service instances
        self._strategy = strategy
        self._current_index = 0

    def add_instance(self, instance_url: str) -> None:
        """Register service instance"""
        self._instances.append({
            "url": instance_url,
            "active_connections": 0,
            "health": "healthy"
        })

    def select_instance(self) -> Optional[str]:
        """Select instance using load balancing strategy"""
        if not self._instances:
            return None

        if self._strategy == "round_robin":
            instance = self._instances[self._current_index]
            self._current_index = (self._current_index + 1) % len(self._instances)
            return instance["url"]

        elif self._strategy == "least_connections":
            return min(self._instances, key=lambda i: i["active_connections"])["url"]

        return self._instances[0]["url"]

    def mark_healthy(self, instance_url: str) -> None:
        """Mark instance as healthy"""
        for inst in self._instances:
            if inst["url"] == instance_url:
                inst["health"] = "healthy"

    def mark_unhealthy(self, instance_url: str) -> None:
        """Mark instance as unhealthy (stop routing to it)"""
        for inst in self._instances:
            if inst["url"] == instance_url:
                inst["health"] = "unhealthy"
'''

    return lb


def generate_api_gateway_system() -> dict:
    """Generate complete API Gateway system."""

    imports = '''from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
import json


'''

    module_doc = '''"""
Phase 5 API Gateway: Microservices Entry Point

Single entry point for all client requests.

Architecture:
- Client → API Gateway → Microservices (Users, Orders, Payments, etc.)
- Client knows only API Gateway URL
- Gateway knows where all microservices are

Gateway Responsibilities:

1. ROUTING
   - URL pattern matching: /users/* → UserService
   - Version handling: /v1/orders vs /v2/orders
   - Path rewriting: /api/users → /users (strip prefix)

2. AUTHENTICATION
   - Validate JWT token on every request
   - Extract user ID from token
   - Pass to backend as header
   - Reject if invalid/expired

3. RATE LIMITING
   - Per-user: max 1000 requests/hour
   - Per-IP: max 10000 requests/hour
   - Per-service: max capacity (circuit breaker)
   - Return 429 Too Many Requests if exceeded

4. LOAD BALANCING
   - Multiple instances of each service
   - Distribute traffic (round-robin, least connections)
   - Health checks (remove unhealthy instances)
   - Automatic failover

5. MONITORING
   - Log all requests
   - Track latency per service
   - Count errors per service
   - Alert if service slow/down

6. TRANSFORMATION
   - Adapt response format for client
   - Add metadata (request ID, timestamp)
   - Compress response
   - Handle errors gracefully
"""
'''

    router = generate_api_gateway_router()
    lb = generate_load_balancer()

    complete_code = imports + module_doc + "\n" + router + "\n" + lb

    return {
        "code": complete_code,
        "pattern": "API Gateway",
        "module": "phase5_api_gateway.py"
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate API Gateway")
    args = parser.parse_args()
    result = generate_api_gateway_system()
    print(result["code"])


if __name__ == "__main__":
    main()
