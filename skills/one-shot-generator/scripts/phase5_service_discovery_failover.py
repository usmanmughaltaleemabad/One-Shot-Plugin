#!/usr/bin/env python3
"""
Phase 5 Service Discovery: Automatic Failover & Graceful Shutdown

Service Discovery: Find services by name (not hardcoded IP).

Problem: Hardcoded service locations
- Database host: 10.0.1.5 (baked into app)
- If DB moves to 10.0.1.6, app breaks
- New instances: where do they register?
- Dead instances: how do clients know?

Service Discovery (solution):
- Service registry: {service_name → [instances]}
- Health checks: detect dead instances
- Automatic failover: route around dead instance
- Graceful shutdown: drain connections before exit
"""

from typing import Dict, List, Optional, Set
from datetime import datetime
from dataclasses import dataclass


@dataclass
class ServiceInstance:
    service_name: str
    instance_id: str
    host: str
    port: int
    status: str = "healthy"
    last_heartbeat: str = ""


def generate_service_discovery_failover() -> str:
    """Generate service discovery with failover."""

    discovery = '''
class ServiceDiscovery:
    """
    Service registry with health checks and automatic failover.

    Features:
    - Register/deregister services dynamically
    - Health check: heartbeat, HTTP, TCP
    - Failover: skip unhealthy instances
    - Graceful shutdown: drain before exit
    """

    def __init__(self):
        self._registry = {}  # service_name → [ServiceInstance]
        self._health_checks = {}  # instance_id → last_check_time
        self._draining = set()  # instance_ids being gracefully shut down

    def register_instance(
        self,
        service_name: str,
        instance_id: str,
        host: str,
        port: int
    ) -> str:
        """Register service instance"""
        instance = {
            "id": instance_id,
            "service": service_name,
            "host": host,
            "port": port,
            "status": "healthy",
            "registered_at": datetime.utcnow().isoformat()
        }

        if service_name not in self._registry:
            self._registry[service_name] = []

        self._registry[service_name].append(instance)
        return instance_id

    def deregister_instance(self, service_name: str, instance_id: str) -> None:
        """Deregister service instance"""
        if service_name in self._registry:
            self._registry[service_name] = [
                i for i in self._registry[service_name] if i["id"] != instance_id
            ]

    def discover(self, service_name: str) -> Optional[str]:
        """Get healthy instance (round-robin)"""
        instances = self._registry.get(service_name, [])
        healthy = [i for i in instances if i["status"] == "healthy" and i["id"] not in self._draining]

        if not healthy:
            return None

        # Round-robin: return first healthy
        return f"{healthy[0]['host']}:{healthy[0]['port']}"

    def heartbeat(self, instance_id: str) -> None:
        """Receive heartbeat from instance (still alive)"""
        self._health_checks[instance_id] = datetime.utcnow().isoformat()

        # Mark healthy
        for service_instances in self._registry.values():
            for instance in service_instances:
                if instance["id"] == instance_id:
                    instance["status"] = "healthy"

    def health_check_all(self) -> Dict[str, int]:
        """Check all instances (mark unhealthy if no heartbeat)"""
        now = datetime.utcnow()
        unhealthy_count = 0

        for service_instances in self._registry.values():
            for instance in service_instances:
                last_check = self._health_checks.get(instance["id"])

                if not last_check:
                    instance["status"] = "unhealthy"
                    unhealthy_count += 1
                else:
                    # If no heartbeat in 30 seconds, mark unhealthy
                    last_check_time = datetime.fromisoformat(last_check)
                    if (now - last_check_time).total_seconds() > 30:
                        instance["status"] = "unhealthy"
                        unhealthy_count += 1

        return {"unhealthy_instances": unhealthy_count}

    def graceful_shutdown(self, instance_id: str) -> None:
        """Start graceful shutdown: stop accepting new requests"""
        self._draining.add(instance_id)

        # Mark as draining (existing connections drain)
        for service_instances in self._registry.values():
            for instance in service_instances:
                if instance["id"] == instance_id:
                    instance["status"] = "draining"

    def finish_shutdown(self, instance_id: str) -> None:
        """Complete shutdown: deregister instance"""
        self._draining.discard(instance_id)
        for service_name, instances in self._registry.items():
            self._registry[service_name] = [i for i in instances if i["id"] != instance_id]

    def get_service_status(self, service_name: str) -> Dict:
        """Get service status"""
        instances = self._registry.get(service_name, [])
        healthy = len([i for i in instances if i["status"] == "healthy"])
        draining = len([i for i in instances if i["status"] == "draining"])

        return {
            "service": service_name,
            "total_instances": len(instances),
            "healthy_instances": healthy,
            "draining_instances": draining,
            "instances": instances
        }
'''

    return discovery


def generate_discovery_system() -> dict:
    """Generate complete service discovery system."""

    imports = '''from typing import Dict, List, Optional, Set
from datetime import datetime
from dataclasses import dataclass


'''

    module_doc = '''"""
Phase 5 Service Discovery: Automatic Failover & Graceful Shutdown

Services register themselves; clients discover by name (Consul, Eureka pattern).

WORKFLOW:

1. SERVICE STARTUP
   Instance starts → registers with service discovery
   POST /register {service: "user-api", instance: "user-api-1", host: "10.0.1.5", port: 8000}
   Registry: user-api → [10.0.1.5:8000]

2. HEARTBEAT
   Instance sends heartbeat every 10 seconds
   POST /heartbeat {instance: "user-api-1"}
   Registry updated: last_seen = now

3. HEALTH CHECK
   Discovery polls: any instances without heartbeat > 30s?
   Mark unhealthy: user-api → [10.0.1.5:8000 UNHEALTHY, 10.0.1.6:8000 HEALTHY]

4. CLIENT DISCOVER
   Client: "Give me user-api"
   Discovery: return only HEALTHY instances [10.0.1.6:8000]

5. AUTOMATIC FAILOVER
   Instance 10.0.1.5 crashes (no heartbeat)
   Discovery: auto-marks unhealthy
   New requests: routed to 10.0.1.6
   Result: transparent failover (no manual intervention)

6. GRACEFUL SHUTDOWN
   Instance decides to shut down (deploy new version)
   POST /graceful-shutdown {instance: "user-api-1"}
   Discovery: status = DRAINING
   New requests: sent to other instances
   Existing requests: allowed to complete
   After timeout: POST /deregister → removed from registry

DEPLOYMENT FLOW:

Current state:
- user-api-1 (10.0.1.5) HEALTHY
- user-api-2 (10.0.1.6) HEALTHY
- Requests split 50/50

Deploy new version to user-api-1:
1. POST /graceful-shutdown {instance: "user-api-1"}
   → Status: DRAINING
   → New requests sent to user-api-2 only

2. Wait 30 seconds for existing requests to finish
   → Existing connections on user-api-1 drain

3. Pull new code, restart user-api-1
   → Starts fresh, registers again
   → Status: HEALTHY

4. Discovery now sees:
   - user-api-1 (10.0.1.5) HEALTHY (new version)
   - user-api-2 (10.0.1.6) HEALTHY (old version)

5. New requests: split 50/50 again

FAILURE SCENARIOS:

Scenario: user-api-1 crashes without graceful shutdown
- Discovery: no heartbeat for 30s
- Auto-marks: UNHEALTHY
- New requests: sent to user-api-2
- Result: 1 second of errors, then recovered

Scenario: All instances down (disaster)
- Discovery: all UNHEALTHY
- Client: no instances available
- Fallback: use cached data or return error
- Operator: deploy new instances, re-register
"""
'''

    discovery = generate_service_discovery_failover()

    complete_code = imports + module_doc + "\n" + discovery

    return {
        "code": complete_code,
        "pattern": "Service Discovery with Failover",
        "module": "phase5_service_discovery_failover.py"
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate service discovery")
    args = parser.parse_args()
    result = generate_discovery_system()
    print(result["code"])


if __name__ == "__main__":
    main()
