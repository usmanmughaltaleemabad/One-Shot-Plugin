#!/usr/bin/env python3
"""Chaos Monkey Generator - Random Service Failure Injection

Generates chaos testing framework for:
- Random service failures (kill pods, force restarts)
- Resource exhaustion (memory, CPU, disk)
- Latency injection (random delays)
- Request failures (error rates)
"""

import sys
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.base_script import setup_logging, timed_run, check_budget

__version__ = "0.7.0"
logger = setup_logging(__name__)


class ChaosMonkeyGenerator:
    """Generates chaos monkey framework for resilience testing."""

    def __init__(self, framework: str):
        self.framework = framework.lower()

    def generate(self) -> Dict[str, str]:
        files = {}
        files['chaos/monkey/chaos_monkey.py'] = self._chaos_monkey()
        files['chaos/monkey/failure_injector.py'] = self._failure_injector()
        files['chaos/monkey/scenarios.py'] = self._scenarios()
        files['chaos/monkey/config.py'] = self._config()
        files['chaos/monkey/README.md'] = self._readme()
        return files

    def _chaos_monkey(self) -> str:
        return '''"""Chaos Monkey - Random Failure Injection Engine"""

import random
import logging
from typing import Callable, List, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ChaosMonkey:
    """Orchestrates chaos scenarios across services"""

    def __init__(self, enabled: bool = False, failure_rate: float = 0.1):
        self.enabled = enabled
        self.failure_rate = failure_rate  # 0-1: probability of failure
        self.active_scenarios: List[str] = []
        self.stats = {
            'total_injections': 0,
            'total_failures': 0,
            'scenarios_executed': {},
        }

    def inject_random_failure(self, context: str = "unknown") -> bool:
        """Randomly inject failure based on configured rate"""
        if not self.enabled or random.random() > self.failure_rate:
            return False

        self.stats['total_injections'] += 1
        logger.warning(f"Chaos Monkey: Injecting failure in {context}")
        return True

    def kill_service(self, service_name: str):
        """Force kill a service instance"""
        logger.warning(f"Chaos Monkey: Killing service {service_name}")
        self.active_scenarios.append(f"kill:{service_name}")
        # Actual implementation depends on orchestrator (K8s, Docker, etc)
        return True

    def exhaust_memory(self, service_name: str, percent: int = 90):
        """Exhaust memory on a service"""
        logger.warning(f"Chaos Monkey: Exhausting {percent}% memory on {service_name}")
        self.active_scenarios.append(f"memory_exhaust:{service_name}")
        return True

    def exhaust_cpu(self, service_name: str, percent: int = 95):
        """Max out CPU on a service"""
        logger.warning(f"Chaos Monkey: Exhausting {percent}% CPU on {service_name}")
        self.active_scenarios.append(f"cpu_exhaust:{service_name}")
        return True

    def exhaust_disk(self, service_name: str, percent: int = 95):
        """Fill up disk on a service"""
        logger.warning(f"Chaos Monkey: Exhausting {percent}% disk on {service_name}")
        self.active_scenarios.append(f"disk_exhaust:{service_name}")
        return True

    def inject_latency(self, service_name: str, latency_ms: int = 1000):
        """Add artificial latency to service calls"""
        logger.warning(f"Chaos Monkey: Injecting {latency_ms}ms latency to {service_name}")
        self.active_scenarios.append(f"latency:{service_name}:{latency_ms}")
        return True

    def get_stats(self) -> Dict[str, Any]:
        """Get chaos execution statistics"""
        return self.stats

    def reset_stats(self):
        """Reset statistics"""
        self.stats = {
            'total_injections': 0,
            'total_failures': 0,
            'scenarios_executed': {},
        }
'''

    def _failure_injector(self) -> str:
        return '''"""Failure Injection Middleware/Decorator"""

import random
import time
import logging
from functools import wraps
from typing import Callable, Any

logger = logging.getLogger(__name__)


class FailureInjector:
    """Inject failures into function calls"""

    def __init__(self, failure_rate: float = 0.1):
        self.failure_rate = failure_rate

    def inject_on_call(self, func: Callable) -> Callable:
        """Decorator to inject failures on function calls"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            if random.random() < self.failure_rate:
                logger.warning(f"Chaos: Injecting failure in {func.__name__}")
                raise Exception(f"Chaos-injected failure in {func.__name__}")
            return func(*args, **kwargs)
        return wrapper

    def inject_latency(self, latency_ms: int) -> Callable:
        """Decorator to inject random latency"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                jitter = random.randint(-int(latency_ms * 0.1), int(latency_ms * 0.1))
                actual_latency = (latency_ms + jitter) / 1000.0
                logger.debug(f"Injecting {actual_latency:.2f}s latency to {func.__name__}")
                time.sleep(actual_latency)
                return func(*args, **kwargs)
            return wrapper
        return decorator

    def inject_timeout(self, timeout_seconds: float) -> Callable:
        """Decorator to inject random timeouts"""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                if random.random() < 0.1:  # 10% timeout rate
                    logger.warning(f"Chaos: Timeout in {func.__name__}")
                    raise TimeoutError(f"Chaos-injected timeout in {func.__name__}")
                return func(*args, **kwargs)
            return wrapper
        return decorator
'''

    def _scenarios(self) -> str:
        return '''"""Predefined Chaos Scenarios"""

from dataclasses import dataclass
from typing import List, Callable
import random


@dataclass
class ChaosScenario:
    """Definition of a chaos scenario"""
    name: str
    description: str
    affected_services: List[str]
    duration_seconds: int
    failure_mode: str  # kill, latency, memory_exhaust, cpu_exhaust
    severity: str  # low, medium, high, critical


class ChaosScenarios:
    """Predefined scenarios for chaos testing"""

    SCENARIOS = {
        'pod_kill': ChaosScenario(
            name='Pod Kill',
            description='Randomly kill pods every 30 seconds',
            affected_services=['api', 'worker'],
            duration_seconds=300,
            failure_mode='kill',
            severity='high'
        ),
        'latency_spike': ChaosScenario(
            name='Latency Spike',
            description='Add 500-2000ms latency to database calls',
            affected_services=['database'],
            duration_seconds=120,
            failure_mode='latency',
            severity='medium'
        ),
        'memory_leak': ChaosScenario(
            name='Memory Leak',
            description='Slowly exhaust memory on worker services',
            affected_services=['worker'],
            duration_seconds=600,
            failure_mode='memory_exhaust',
            severity='critical'
        ),
        'cpu_spike': ChaosScenario(
            name='CPU Spike',
            description='Spike CPU to 95% on API servers',
            affected_services=['api'],
            duration_seconds=180,
            failure_mode='cpu_exhaust',
            severity='high'
        ),
        'cascading_failure': ChaosScenario(
            name='Cascading Failure',
            description='Kill database, then API servers in sequence',
            affected_services=['database', 'api', 'cache'],
            duration_seconds=300,
            failure_mode='kill',
            severity='critical'
        ),
        'network_partition': ChaosScenario(
            name='Network Partition',
            description='Drop 30% of packets between services',
            affected_services=['api', 'database'],
            duration_seconds=120,
            failure_mode='latency',
            severity='high'
        ),
    }

    @classmethod
    def get_scenario(cls, name: str) -> ChaosScenario:
        """Get scenario by name"""
        if name not in cls.SCENARIOS:
            raise ValueError(f"Unknown scenario: {name}")
        return cls.SCENARIOS[name]

    @classmethod
    def list_scenarios(cls) -> List[str]:
        """List all available scenarios"""
        return list(cls.SCENARIOS.keys())

    @classmethod
    def random_scenario(cls) -> ChaosScenario:
        """Get a random scenario"""
        name = random.choice(list(cls.SCENARIOS.keys()))
        return cls.SCENARIOS[name]
'''

    def _config(self) -> str:
        return '''"""Chaos Monkey Configuration"""

CHAOS_CONFIG = {
    "enabled": False,  # Enable/disable chaos testing
    "global_failure_rate": 0.05,  # 5% of requests fail
    "scenarios": [
        {
            "name": "pod_kill",
            "enabled": False,
            "interval_seconds": 30,
            "duration_seconds": 300,
        },
        {
            "name": "latency_spike",
            "enabled": False,
            "latency_ms_min": 500,
            "latency_ms_max": 2000,
            "duration_seconds": 120,
        },
        {
            "name": "cpu_spike",
            "enabled": False,
            "target_percent": 95,
            "duration_seconds": 180,
        },
    ],
    "exclude_services": [],  # Services to never chaos-test
    "alert_threshold": 0.5,  # Alert if failure rate exceeds this
}


def get_chaos_config():
    """Get chaos configuration"""
    return CHAOS_CONFIG


def is_chaos_enabled():
    """Check if chaos testing is enabled"""
    return CHAOS_CONFIG.get("enabled", False)


def set_chaos_enabled(enabled: bool):
    """Enable/disable chaos testing"""
    CHAOS_CONFIG["enabled"] = enabled
'''

    def _readme(self) -> str:
        return '''# Chaos Monkey - Failure Injection Framework

## Overview

Chaos Monkey randomly injects failures to test system resilience:
- Service kills (pod termination)
- Resource exhaustion (memory, CPU, disk)
- Latency injection
- Network failures

## Usage

### Enable Chaos Testing

```python
from chaos.monkey import ChaosMonkey

monkey = ChaosMonkey(enabled=True, failure_rate=0.1)

# Inject random failures
if monkey.inject_random_failure(context="api_request"):
    handle_failure()
```

### Run Predefined Scenarios

```python
from chaos.monkey.scenarios import ChaosScenarios

# Get a specific scenario
scenario = ChaosScenarios.get_scenario('pod_kill')

# Run random scenario
scenario = ChaosScenarios.random_scenario()
```

### Use Failure Injector Decorator

```python
from chaos.monkey.failure_injector import FailureInjector

injector = FailureInjector(failure_rate=0.1)

@injector.inject_on_call
def risky_operation():
    pass

@injector.inject_latency(latency_ms=500)
def database_call():
    pass
```

## Best Practices

1. **Start small**: Begin with 1-5% failure rate
2. **Non-production first**: Test in staging/QA
3. **Monitor closely**: Watch metrics during chaos
4. **Define alerting**: Alert when failures exceed threshold
5. **Document impact**: Record what fails and how system recovers

## Configuration

Edit `chaos/monkey/config.py` to enable/disable scenarios:
- `pod_kill`: Random pod termination
- `latency_spike`: Add latency to requests
- `cpu_spike`: Exhaust CPU
- `memory_leak`: Gradually fill memory
- `cascading_failure`: Sequential service failure

## Integration with K8s

For Kubernetes, use LitmusChaos to execute scenarios:
```bash
kubectl apply -f chaos-experiments.yaml
```

See [LitmusChaos docs](https://litmuschaos.io/) for details.
'''


def main():
    with timed_run("chaos_monkey_generator") as timer:
        logger.debug("Testing Chaos Monkey generation")
        gen = ChaosMonkeyGenerator("python")
        files = gen.generate()
        logger.debug(f"Generated {len(files)} files")
        for filepath in files:
            print(f"  ✓ {filepath}")
        check_budget("chaos_monkey_generator", timer.elapsed_ms, logger)


if __name__ == '__main__':
    main()
