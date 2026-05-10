#!/usr/bin/env python3
"""Network Partition Generator - Network Failure Simulation

Generates:
- Network delay injection (latency)
- Packet loss (drop requests)
- Network partition (split-brain)
- Connection timeout
"""

import sys
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.base_script import setup_logging, timed_run, check_budget

__version__ = "0.7.0"
logger = setup_logging(__name__)


class NetworkPartitionGenerator:
    """Generates network failure simulation framework."""

    def __init__(self, framework: str):
        self.framework = framework.lower()

    def generate(self) -> Dict[str, str]:
        files = {}
        files['chaos/network/partition_simulator.py'] = self._partition_simulator()
        files['chaos/network/latency_injector.py'] = self._latency_injector()
        files['chaos/network/packet_loss.py'] = self._packet_loss()
        files['chaos/network/scenarios.py'] = self._scenarios()
        files['chaos/network/README.md'] = self._readme()
        return files

    def _partition_simulator(self) -> str:
        return '''"""Network Partition Simulator - Split Brain Testing"""

import logging
from typing import Set, Dict, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class NetworkPartition:
    """Definition of network partition"""
    partition_id: str
    nodes_isolated: Set[str]  # Nodes in this partition
    timestamp: datetime
    duration_seconds: int


class NetworkPartitionSimulator:
    """Simulate network partitions (split-brain)"""

    def __init__(self):
        self.active_partitions: Dict[str, NetworkPartition] = {}
        self.blocked_connections: Set[tuple] = set()

    def create_partition(
        self,
        partition_id: str,
        nodes_isolated: list,
        duration_seconds: int = 60
    ) -> NetworkPartition:
        """Create a network partition"""
        partition = NetworkPartition(
            partition_id=partition_id,
            nodes_isolated=set(nodes_isolated),
            timestamp=datetime.now(),
            duration_seconds=duration_seconds,
        )
        self.active_partitions[partition_id] = partition
        logger.warning(
            f"Network partition created: {partition_id} "
            f"isolating {len(nodes_isolated)} nodes for {duration_seconds}s"
        )
        return partition

    def can_communicate(self, source_node: str, dest_node: str) -> bool:
        """Check if two nodes can communicate"""
        # Check all active partitions
        for partition in self.active_partitions.values():
            if source_node in partition.nodes_isolated and dest_node not in partition.nodes_isolated:
                logger.debug(f"Communication blocked: {source_node} -> {dest_node}")
                return False
            if dest_node in partition.nodes_isolated and source_node not in partition.nodes_isolated:
                logger.debug(f"Communication blocked: {source_node} -> {dest_node}")
                return False

        return True

    def block_connection(self, source: str, dest: str):
        """Block specific connection"""
        self.blocked_connections.add((source, dest))
        logger.warning(f"Blocked connection: {source} -> {dest}")

    def unblock_connection(self, source: str, dest: str):
        """Unblock specific connection"""
        self.blocked_connections.discard((source, dest))
        logger.info(f"Unblocked connection: {source} -> {dest}")

    def heal_partition(self, partition_id: str):
        """Heal network partition"""
        if partition_id in self.active_partitions:
            partition = self.active_partitions.pop(partition_id)
            logger.info(f"Network partition healed: {partition_id}")

    def get_partition_status(self) -> Dict[str, Any]:
        """Get status of all active partitions"""
        return {
            "active_partitions": len(self.active_partitions),
            "partitions": [
                {
                    "id": p.partition_id,
                    "isolated_nodes": list(p.nodes_isolated),
                    "duration_remaining": max(0, p.duration_seconds),
                }
                for p in self.active_partitions.values()
            ]
        }
'''

    def _latency_injector(self) -> str:
        return '''"""Latency Injector - Network Delay Simulation"""

import logging
import time
import random
from typing import Callable, Any
from functools import wraps

logger = logging.getLogger(__name__)


class LatencyInjector:
    """Inject network latency"""

    def __init__(self, base_latency_ms: int = 0, jitter_ms: int = 0):
        self.base_latency_ms = base_latency_ms
        self.jitter_ms = jitter_ms

    def inject(self):
        """Inject configured latency"""
        latency = self.base_latency_ms
        if self.jitter_ms > 0:
            jitter = random.randint(-self.jitter_ms, self.jitter_ms)
            latency = max(0, latency + jitter)

        if latency > 0:
            logger.debug(f"Injecting {latency}ms latency")
            time.sleep(latency / 1000.0)

    def decorator(self, func: Callable) -> Callable:
        """Decorator to inject latency"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            self.inject()
            return func(*args, **kwargs)
        return wrapper


class VariableLatencyInjector:
    """Inject variable latency (distribution)"""

    def __init__(self, min_ms: int, max_ms: int, mean_ms: int = None):
        self.min_ms = min_ms
        self.max_ms = max_ms
        self.mean_ms = mean_ms or (min_ms + max_ms) // 2

    def inject(self) -> int:
        """Inject random latency in range"""
        latency = random.randint(self.min_ms, self.max_ms)
        logger.debug(f"Injecting {latency}ms variable latency")
        time.sleep(latency / 1000.0)
        return latency

    def decorator(self, func: Callable) -> Callable:
        """Decorator to inject variable latency"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            self.inject()
            return func(*args, **kwargs)
        return wrapper
'''

    def _packet_loss(self) -> str:
        return '''"""Packet Loss Simulator"""

import logging
import random
from typing import Callable, Any
from functools import wraps

logger = logging.getLogger(__name__)


class PacketLossSimulator:
    """Simulate packet loss (request failures)"""

    def __init__(self, loss_rate: float = 0.1):
        self.loss_rate = loss_rate  # 0-1: probability of packet loss

    def should_drop(self) -> bool:
        """Determine if packet should be dropped"""
        return random.random() < self.loss_rate

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute with packet loss"""
        if self.should_drop():
            logger.warning(f"Packet loss: Dropping request to {func.__name__}")
            raise PacketDropped(f"Simulated packet loss in {func.__name__}")
        return func(*args, **kwargs)

    def decorator(self, func: Callable) -> Callable:
        """Decorator to simulate packet loss"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            return self.call(func, *args, **kwargs)
        return wrapper


class PacketDropped(Exception):
    """Packet was dropped"""
    pass


class BurstPacketLoss:
    """Burst packet loss (multiple drops in a row)"""

    def __init__(self, loss_rate: float = 0.1, burst_size: int = 3):
        self.loss_rate = loss_rate
        self.burst_size = burst_size
        self.in_burst = False
        self.burst_count = 0

    def should_drop(self) -> bool:
        """Determine if packet should be dropped"""
        if self.in_burst:
            self.burst_count += 1
            if self.burst_count >= self.burst_size:
                self.in_burst = False
                self.burst_count = 0
            return True

        if random.random() < self.loss_rate:
            self.in_burst = True
            self.burst_count = 1
            return True

        return False

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute with burst packet loss"""
        if self.should_drop():
            logger.warning(f"Burst packet loss: Dropping request")
            raise PacketDropped("Simulated burst packet loss")
        return func(*args, **kwargs)
'''

    def _scenarios(self) -> str:
        return '''"""Network Failure Scenarios"""

from dataclasses import dataclass
from typing import List, Dict


@dataclass
class NetworkScenario:
    """Network failure scenario"""
    name: str
    description: str
    latency_ms: int
    packet_loss_rate: float
    duration_seconds: int
    affected_services: List[str]
    severity: str


class NetworkScenarios:
    """Predefined network failure scenarios"""

    SCENARIOS = {
        'high_latency': NetworkScenario(
            name='High Latency',
            description='500ms latency on all network calls',
            latency_ms=500,
            packet_loss_rate=0.0,
            duration_seconds=120,
            affected_services=['api', 'database', 'cache'],
            severity='medium'
        ),
        'packet_loss': NetworkScenario(
            name='Packet Loss',
            description='10% packet loss rate',
            latency_ms=0,
            packet_loss_rate=0.1,
            duration_seconds=120,
            affected_services=['api', 'database'],
            severity='high'
        ),
        'network_partition': NetworkScenario(
            name='Network Partition',
            description='Complete split between services',
            latency_ms=5000,  # Timeout
            packet_loss_rate=1.0,  # 100% loss
            duration_seconds=180,
            affected_services=['api', 'database'],
            severity='critical'
        ),
        'degraded_network': NetworkScenario(
            name='Degraded Network',
            description='High latency + 5% packet loss',
            latency_ms=1000,
            packet_loss_rate=0.05,
            duration_seconds=300,
            affected_services=['api'],
            severity='high'
        ),
    }

    @classmethod
    def get_scenario(cls, name: str) -> NetworkScenario:
        """Get scenario by name"""
        if name not in cls.SCENARIOS:
            raise ValueError(f"Unknown scenario: {name}")
        return cls.SCENARIOS[name]

    @classmethod
    def list_scenarios(cls) -> List[str]:
        """List all scenarios"""
        return list(cls.SCENARIOS.keys())
'''

    def _readme(self) -> str:
        return '''# Network Failure Simulation

## Partition Simulator

Simulate network partitions (split-brain):

```python
from chaos.network import NetworkPartitionSimulator

simulator = NetworkPartitionSimulator()

# Create partition isolating database
simulator.create_partition(
    partition_id="db_isolated",
    nodes_isolated=["database"],
    duration_seconds=60
)

# Check if nodes can communicate
can_talk = simulator.can_communicate("api", "database")
```

## Latency Injector

Add network latency:

```python
from chaos.network import LatencyInjector

injector = LatencyInjector(base_latency_ms=500, jitter_ms=100)

@injector.decorator
def api_call():
    return requests.get('https://api.example.com')
```

## Packet Loss

Simulate packet loss (request failures):

```python
from chaos.network import PacketLossSimulator

loss = PacketLossSimulator(loss_rate=0.1)  # 10% loss

@loss.decorator
def database_query():
    return db.execute("SELECT * FROM users")
```

## Burst Packet Loss

Simulate burst packet loss (multiple failures):

```python
from chaos.network import BurstPacketLoss

burst_loss = BurstPacketLoss(loss_rate=0.1, burst_size=3)

@burst_loss.decorator
def call_external_api():
    pass
```

## Predefined Scenarios

```python
from chaos.network.scenarios import NetworkScenarios

# Get a scenario
scenario = NetworkScenarios.get_scenario('high_latency')

# Apply scenario
injector = LatencyInjector(base_latency_ms=scenario.latency_ms)
loss = PacketLossSimulator(loss_rate=scenario.packet_loss_rate)
```

Available scenarios:
- `high_latency`: 500ms latency
- `packet_loss`: 10% loss rate
- `network_partition`: Complete split
- `degraded_network`: 1000ms + 5% loss

## Tools

For Linux, use `tc` (traffic control):
```bash
# Add 500ms latency
sudo tc qdisc add dev eth0 root netem delay 500ms

# Add 10% packet loss
sudo tc qdisc add dev eth0 root netem loss 10%

# Clean up
sudo tc qdisc del dev eth0 root
```

For Kubernetes, use network policies or Istio.
'''


def main():
    with timed_run("network_partition_generator") as timer:
        logger.debug("Testing Network Partition generation")
        gen = NetworkPartitionGenerator("python")
        files = gen.generate()
        logger.debug(f"Generated {len(files)} files")
        for filepath in files:
            print(f"  ✓ {filepath}")
        check_budget("network_partition_generator", timer.elapsed_ms, logger)


if __name__ == '__main__':
    main()
