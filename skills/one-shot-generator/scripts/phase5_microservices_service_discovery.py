#!/usr/bin/env python3
"""
Phase 5 Microservices: Service Discovery

Microservices communicate across network.
Need to discover where services are running.

Problems:
- Services move (scaling, failures, updates)
- Service instances: 10 payment servers, which one?
- Dynamic: can't hardcode IP addresses

Solution: Service Discovery

Registry:
- Service registers: "payment-api at 10.0.1.5:8080"
- Service unregisters: shutdown or failure
- Client queries: "where is payment-api?"
- Gets: [10.0.1.5:8080, 10.0.1.6:8080, ...]
- Picks one (load balancing)

Strategies:
1. Client-side: client queries registry
2. Server-side: request router queries registry

Implementation:
- In-memory registry (local)
- Consul (distributed)
- Kubernetes (container orchestration)

Usage:
    python phase5_microservices_service_discovery.py --strategy client-side

Input: Discovery strategy
Output: Service discovery with registry and load balancing
"""

import argparse
import json
from typing import Any, Callable, Dict, List, Optional, Tuple
from datetime import datetime, timedelta


def generate_service_registry() -> str:
    """Generate service registry."""

    registry = '''
class ServiceRegistry:
    """
    Central registry of services.

    Services register location:
    - Service name: "payment-api"
    - Instance: "payment-01"
    - Host: "10.0.1.5"
    - Port: 8080
    - Metadata: {environment: "prod", version: "1.2.3"}

    Heartbeat:
    - Service sends heartbeat every 30 seconds
    - If no heartbeat for 60s, assume dead
    - Remove from registry
    """

    def __init__(self):
        self._services = {}  # service_name → [instances]
        self._heartbeats = {}  # (service, instance) → last_heartbeat

    def register(
        self,
        service_name: str,
        instance_id: str,
        host: str,
        port: int,
        metadata: Optional[Dict] = None
    ) -> None:
        """Register service instance"""
        if service_name not in self._services:
            self._services[service_name] = []

        instance = {
            "id": instance_id,
            "host": host,
            "port": port,
            "metadata": metadata or {},
            "url": f"http://{host}:{port}"
        }

        # Remove if already exists (update)
        self._services[service_name] = [
            s for s in self._services[service_name]
            if s["id"] != instance_id
        ]

        self._services[service_name].append(instance)
        self._heartbeats[(service_name, instance_id)] = datetime.utcnow()

    def deregister(self, service_name: str, instance_id: str) -> None:
        """Deregister service instance"""
        if service_name in self._services:
            self._services[service_name] = [
                s for s in self._services[service_name]
                if s["id"] != instance_id
            ]

    def heartbeat(self, service_name: str, instance_id: str) -> None:
        """Heartbeat from instance (still alive)"""
        self._heartbeats[(service_name, instance_id)] = datetime.utcnow()

    def discover(self, service_name: str) -> List[Dict]:
        """Discover instances of service"""
        self._cleanup_stale()

        if service_name not in self._services:
            return []

        return self._services[service_name]

    def _cleanup_stale(self, timeout_seconds: int = 60) -> None:
        """Remove stale instances (no heartbeat)"""
        now = datetime.utcnow()
        timeout = timedelta(seconds=timeout_seconds)

        for (service_name, instance_id), last_heartbeat in list(
            self._heartbeats.items()
        ):
            if now - last_heartbeat > timeout:
                self.deregister(service_name, instance_id)
                del self._heartbeats[(service_name, instance_id)]
'''

    return registry


def generate_load_balancer() -> str:
    """Generate client-side load balancer."""

    balancer = '''
class ClientSideLoadBalancer:
    """
    Client-side load balancing.

    Client queries registry and picks an instance.

    Strategies:
    1. Round-robin: cycle through instances
    2. Least connections: pick least busy
    3. Random: random instance
    """

    def __init__(self, registry: ServiceRegistry, strategy: str = "round-robin"):
        self.registry = registry
        self.strategy = strategy
        self._counters = {}  # service → index for round-robin

    def resolve(self, service_name: str) -> Tuple[str, int]:
        """
        Resolve service to host:port.

        Returns:
            (host, port) tuple
        """
        instances = self.registry.discover(service_name)

        if not instances:
            raise ServiceNotFound(f"Service {service_name} not found")

        if self.strategy == "round-robin":
            instance = self._round_robin(service_name, instances)
        elif self.strategy == "random":
            instance = self._random(instances)
        else:
            instance = instances[0]  # Default

        return (instance["host"], instance["port"])

    def _round_robin(self, service_name: str, instances: List[Dict]) -> Dict:
        """Round-robin: cycle through instances"""
        if service_name not in self._counters:
            self._counters[service_name] = 0

        index = self._counters[service_name] % len(instances)
        self._counters[service_name] = (index + 1) % len(instances)

        return instances[index]

    def _random(self, instances: List[Dict]) -> Dict:
        """Random instance"""
        import random
        return random.choice(instances)

    def get_url(self, service_name: str) -> str:
        """Get service URL"""
        instance = self.registry.discover(service_name)[0]
        return instance["url"]


class ServiceNotFound(Exception):
    """Service not found in registry"""
    pass
'''

    return balancer


def generate_heartbeat_manager() -> str:
    """Generate heartbeat manager for instance health."""

    heartbeat = '''
class HeartbeatManager:
    """
    Heartbeat health checking.

    Instance regularly sends heartbeat:
    - "I'm alive"
    - "My status: healthy"
    - "Metrics: 50% CPU, 4GB memory"
    """

    def __init__(self, registry: ServiceRegistry, interval_seconds: int = 30):
        self.registry = registry
        self.interval = interval_seconds
        self.is_healthy = True

    def start_heartbeat(
        self,
        service_name: str,
        instance_id: str
    ) -> None:
        """Start sending heartbeats"""
        # In production: use threading or asyncio
        # Run every 30 seconds:
        # self.registry.heartbeat(service_name, instance_id)

    def report_health(self, healthy: bool) -> None:
        """Report health status"""
        self.is_healthy = healthy

    def is_alive(self) -> bool:
        """Check if instance is alive"""
        return self.is_healthy
'''

    return heartbeat


def generate_service_discovery_system() -> dict:
    """Generate complete service discovery system."""

    imports = '''from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import random


'''

    module_doc = '''"""
Phase 5 Microservices: Service Discovery

Dynamic service location for microservices.

Microservices Architecture:
- Many small services (auth, payment, inventory)
- Each service deployed on multiple machines
- Services move (scaling, failures, updates)
- Network topology dynamic

Challenge: How do services find each other?

Option 1: Hardcode IPs
- auth-service: 10.0.1.5:8080
- Problem: breaks when service moves
- Not dynamic

Option 2: Service Discovery Registry
- Central registry: "payment-api at 10.0.1.5, 10.0.1.6"
- Service registers on startup
- Service sends heartbeat (I'm alive)
- If no heartbeat for 60s, assume dead
- Clients query registry to find services

Client-Side Discovery (this module):
- Client queries registry
- Gets list of instances
- Picks one (load balancing)
- Makes request

Example flow:
1. Payment service starts
   - Registers: "payment-api at 10.0.1.5:8080"
   - Sends heartbeat every 30s

2. Order service needs to call payment
   - Queries registry: "where is payment-api?"
   - Gets: [10.0.1.5:8080, 10.0.1.6:8080]
   - Picks: 10.0.1.6:8080 (round-robin)
   - Calls: http://10.0.1.6:8080/charge

3. Heartbeat stops (service crashed)
   - Registry waits 60s
   - Removes: 10.0.1.5:8080
   - Next request uses: 10.0.1.6:8080 (still alive)

Load balancing strategies:
- Round-robin: 1→2→3→1→2→3
- Random: random instance
- Least connections: pick least busy

Health checking:
- Service sends heartbeat every 30s
- Registry assumes dead if no heartbeat for 60s
- Removes from discovery
- Clients never see dead instances
"""
'''

    registry = generate_service_registry()
    balancer = generate_load_balancer()
    heartbeat = generate_heartbeat_manager()

    complete_code = imports + module_doc + "\n" + registry + "\n" + balancer + "\n" + heartbeat

    return {
        "code": complete_code,
        "pattern": "Microservices Service Discovery",
        "module": "phase5_microservices_service_discovery.py",
    }


def main():
    parser = argparse.ArgumentParser(description="Generate microservices service discovery")
    parser.add_argument("--strategy", help="Discovery strategy")
    parser.add_argument("--output", choices=["json", "code"], default="code")

    args = parser.parse_args()
    result = generate_service_discovery_system()

    if args.output == "json":
        metadata = {k: v for k, v in result.items() if k != "code"}
        print(json.dumps(metadata, indent=2))
    else:
        print(result["code"])


if __name__ == "__main__":
    main()
