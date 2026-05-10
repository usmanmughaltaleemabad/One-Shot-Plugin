#!/usr/bin/env python3
"""SLO/SLI Generator - Service Level Objectives & Indicators

Generates:
- SLO definitions (availability, latency targets)
- SLI tracking (success rate, latency percentiles)
- Error budget calculations (how much failure allowed)
- Burn rate alerts (when burning budget too fast)
"""

import sys
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.base_script import setup_logging, timed_run, check_budget

__version__ = "0.7.0"
logger = setup_logging(__name__)


class SLOSLIGenerator:
    """Generates SLO/SLI tracking framework."""

    def __init__(self, framework: str):
        self.framework = framework.lower()

    def generate(self) -> Dict[str, str]:
        files = {}
        files['slo_sli/definitions.py'] = self._definitions()
        files['slo_sli/indicators.py'] = self._indicators()
        files['slo_sli/error_budget.py'] = self._error_budget()
        files['slo_sli/burn_rate.py'] = self._burn_rate()
        files['slo_sli/README.md'] = self._readme()
        return files

    def _definitions(self) -> str:
        return '''"""SLO Definitions - Service Level Objectives"""

from dataclasses import dataclass
from typing import Dict, List
from enum import Enum


class SLIType(Enum):
    AVAILABILITY = "availability"      # % uptime
    LATENCY = "latency"                # Response time
    ERROR_RATE = "error_rate"          # % of failed requests
    THROUGHPUT = "throughput"          # Requests per second


@dataclass
class SLO:
    """Service Level Objective"""
    service_name: str
    metric: SLIType
    target: float              # e.g., 0.999 for 99.9%
    window_days: int          # Evaluation window (30, 90, etc)
    description: str = ""


class SLODefinitions:
    """Standard SLO definitions"""

    COMMON_SLOS = {
        'availability_99_9': SLO(
            service_name="api",
            metric=SLIType.AVAILABILITY,
            target=0.999,  # 99.9%
            window_days=30,
            description="99.9% availability (8.64 minutes downtime allowed per month)"
        ),
        'availability_99_99': SLO(
            service_name="payment",
            metric=SLIType.AVAILABILITY,
            target=0.9999,  # 99.99%
            window_days=30,
            description="99.99% availability (4.32 seconds downtime allowed per month)"
        ),
        'latency_p99_200ms': SLO(
            service_name="api",
            metric=SLIType.LATENCY,
            target=0.99,  # 99% of requests < 200ms
            window_days=30,
            description="99% of requests complete in < 200ms"
        ),
        'error_rate_0_1': SLO(
            service_name="api",
            metric=SLIType.ERROR_RATE,
            target=0.001,  # 0.1% error rate
            window_days=30,
            description="Error rate < 0.1% (99.9% success)"
        ),
    }

    @classmethod
    def get_slo(cls, name: str) -> SLO:
        """Get SLO definition"""
        if name not in cls.COMMON_SLOS:
            raise ValueError(f"Unknown SLO: {name}")
        return cls.COMMON_SLOS[name]

    @classmethod
    def list_slos(cls) -> List[str]:
        """List all available SLOs"""
        return list(cls.COMMON_SLOS.keys())

    @classmethod
    def create_custom(
        cls,
        service_name: str,
        metric: SLIType,
        target: float,
        window_days: int = 30,
        description: str = ""
    ) -> SLO:
        """Create custom SLO"""
        return SLO(service_name, metric, target, window_days, description)


class SLOTarget:
    """SLO target with calculated allowed failures"""

    def __init__(self, slo: SLO):
        self.slo = slo
        self.allowed_failures = self._calculate_allowed_failures()

    def _calculate_allowed_failures(self) -> float:
        """Calculate allowed failures based on SLO target"""
        # For availability SLO: allowed_downtime = (1 - target) * window_duration
        # For error rate SLO: allowed_errors = (1 - target) * total_requests
        return 1.0 - self.slo.target

    def get_allowed_downtime_seconds(self) -> float:
        """Get allowed downtime in seconds"""
        seconds_per_day = 86400
        window_seconds = self.slo.window_days * seconds_per_day
        return self.allowed_failures * window_seconds

    def get_allowed_errors_percent(self) -> float:
        """Get allowed error rate as percentage"""
        return self.allowed_failures * 100
'''

    def _indicators(self) -> str:
        return '''"""SLI Tracking - Service Level Indicators"""

import logging
from typing import Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class SLIReading:
    """Single SLI measurement"""
    timestamp: datetime
    value: float  # 0-1
    metric_type: str


class SLITracker:
    """Track Service Level Indicators"""

    def __init__(self, window_days: int = 30):
        self.window_days = window_days
        self.readings: Dict[str, list] = {}

    def record_success(self, metric_name: str):
        """Record successful operation"""
        self._record_reading(metric_name, 1.0)

    def record_failure(self, metric_name: str):
        """Record failed operation"""
        self._record_reading(metric_name, 0.0)

    def record_latency(self, metric_name: str, latency_ms: float, target_ms: float):
        """Record latency (success if under target)"""
        value = 1.0 if latency_ms <= target_ms else 0.0
        self._record_reading(metric_name, value)

    def _record_reading(self, metric_name: str, value: float):
        """Record a reading"""
        if metric_name not in self.readings:
            self.readings[metric_name] = []

        reading = SLIReading(
            timestamp=datetime.now(),
            value=value,
            metric_type=metric_name
        )
        self.readings[metric_name].append(reading)
        self._cleanup_old_readings(metric_name)

    def _cleanup_old_readings(self, metric_name: str):
        """Remove readings older than window"""
        cutoff = datetime.now() - timedelta(days=self.window_days)
        self.readings[metric_name] = [
            r for r in self.readings[metric_name]
            if r.timestamp > cutoff
        ]

    def get_success_rate(self, metric_name: str) -> float:
        """Get success rate for metric (0-1)"""
        if metric_name not in self.readings or not self.readings[metric_name]:
            return 0.0

        readings = self.readings[metric_name]
        success = sum(r.value for r in readings)
        return success / len(readings)

    def get_all_metrics(self) -> Dict[str, float]:
        """Get all tracked metrics"""
        return {
            name: self.get_success_rate(name)
            for name in self.readings
        }
'''

    def _error_budget(self) -> str:
        return '''"""Error Budget - How Much Failure is Allowed"""

import logging
from typing import Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ErrorBudget:
    """Track error budget spending"""

    def __init__(self, slo_target: float, window_days: int = 30):
        self.slo_target = slo_target
        self.window_days = window_days
        self.start_date = datetime.now()
        self.total_requests = 0
        self.failed_requests = 0

    def record_request(self, success: bool):
        """Record request outcome"""
        self.total_requests += 1
        if not success:
            self.failed_requests += 1

    def get_current_error_rate(self) -> float:
        """Get current error rate"""
        if self.total_requests == 0:
            return 0.0
        return self.failed_requests / self.total_requests

    def get_allowed_error_rate(self) -> float:
        """Get allowed error rate based on SLO"""
        return 1.0 - self.slo_target

    def get_budget_remaining(self) -> float:
        """Get fraction of budget remaining (0-1)"""
        allowed_errors = self.get_allowed_error_rate() * self.total_requests
        remaining = max(0, allowed_errors - self.failed_requests)
        return remaining / (allowed_errors or 1)

    def get_budget_percent(self) -> float:
        """Get budget remaining as percentage"""
        return self.get_budget_remaining() * 100

    def is_budget_exhausted(self) -> bool:
        """Check if error budget exhausted"""
        return self.get_budget_remaining() <= 0

    def get_status(self) -> Dict[str, Any]:
        """Get error budget status"""
        return {
            "slo_target": self.slo_target,
            "current_error_rate": self.get_current_error_rate(),
            "allowed_error_rate": self.get_allowed_error_rate(),
            "budget_remaining": self.get_budget_remaining(),
            "budget_percent": self.get_budget_percent(),
            "exhausted": self.is_budget_exhausted(),
            "total_requests": self.total_requests,
            "failed_requests": self.failed_requests,
        }
'''

    def _burn_rate(self) -> str:
        return '''"""Burn Rate - How Fast Error Budget is Being Consumed"""

import logging
from typing import Dict, Any
from datetime import datetime, timedelta
from collections import deque

logger = logging.getLogger(__name__)


class BurnRate:
    """Calculate burn rate (budget consumption speed)"""

    def __init__(self, window_minutes: int = 5):
        self.window_minutes = window_minutes
        self.events: deque = deque()  # (timestamp, success)

    def record_event(self, success: bool):
        """Record event (request success/failure)"""
        self.events.append((datetime.now(), success))
        self._cleanup_old_events()

    def _cleanup_old_events(self):
        """Remove events outside window"""
        cutoff = datetime.now() - timedelta(minutes=self.window_minutes)
        while self.events and self.events[0][0] < cutoff:
            self.events.popleft()

    def get_burn_rate(self) -> float:
        """Get burn rate (0-1, where 1 = burning budget at SLO rate)"""
        if not self.events:
            return 0.0

        failures = sum(1 for _, success in self.events if not success)
        return failures / len(self.events) if self.events else 0.0

    def is_burn_rate_high(self, threshold: float = 0.1) -> bool:
        """Check if burn rate exceeds threshold"""
        return self.get_burn_rate() > threshold

    def get_time_to_exhaustion(
        self, budget_percent: float, slo_target: float = 0.999
    ) -> timedelta:
        """Estimate time until budget exhausted"""
        allowed_error_rate = 1.0 - slo_target
        current_burn = self.get_burn_rate()

        if current_burn == 0:
            return timedelta(days=999)  # Never

        if current_burn >= allowed_error_rate:
            return timedelta(hours=0)  # Now

        # budget_percent * allowed_error_rate / current_burn
        days_remaining = (budget_percent / 100) * allowed_error_rate / current_burn
        return timedelta(days=days_remaining)


class BurnRateAlert:
    """Alert when burn rate is critical"""

    def __init__(self, slo_target: float, alert_threshold: float = 10.0):
        self.slo_target = slo_target
        self.alert_threshold = alert_threshold  # 10 = 10x normal burn rate
        self.burn_rate_tracker = BurnRate()
        self.alerts = []

    def record_event(self, success: bool):
        """Record event and check for alerts"""
        self.burn_rate_tracker.record_event(success)
        self._check_alerts()

    def _check_alerts(self):
        """Check if burn rate triggers alerts"""
        burn_rate = self.burn_rate_tracker.get_burn_rate()
        allowed_error_rate = 1.0 - self.slo_target

        if allowed_error_rate > 0:
            burn_rate_multiple = burn_rate / allowed_error_rate
            if burn_rate_multiple > self.alert_threshold:
                message = f"CRITICAL: Burn rate {burn_rate_multiple:.0f}x normal"
                logger.error(message)
                self.alerts.append(message)
'''

    def _readme(self) -> str:
        return '''# SLO/SLI - Service Level Objectives & Indicators

## SLO Definitions

Define targets for your services:

```python
from slo_sli.definitions import SLODefinitions, SLOTarget

# Use predefined SLO
slo = SLODefinitions.get_slo('availability_99_9')
target = SLOTarget(slo)

# Allowed downtime: 8.64 minutes per month
print(target.get_allowed_downtime_seconds() / 60)  # 8.64 minutes
```

Common SLOs:
- `availability_99_9`: 99.9% uptime (8.64 min/month downtime)
- `availability_99_99`: 99.99% uptime (4.32 sec/month downtime)
- `latency_p99_200ms`: 99% of requests < 200ms
- `error_rate_0_1`: Error rate < 0.1%

## SLI Tracking

Track actual metrics:

```python
from slo_sli.indicators import SLITracker

tracker = SLITracker(window_days=30)

# Record successes/failures
tracker.record_success("api_requests")
tracker.record_failure("api_requests")

# Or track latency
tracker.record_latency("database_calls", latency_ms=45, target_ms=100)

# Get success rate
success_rate = tracker.get_success_rate("api_requests")
```

## Error Budget

How much failure is allowed:

```python
from slo_sli.error_budget import ErrorBudget

budget = ErrorBudget(slo_target=0.999, window_days=30)

for _ in range(1000000):
    success = check_request()
    budget.record_request(success)

# Check if budget exhausted
if budget.is_budget_exhausted():
    logger.error("Error budget exhausted!")

print(f"Budget remaining: {budget.get_budget_percent():.1f}%")
```

For 99.9% SLO:
- Allowed: 0.1% error rate
- If 1M requests/month: can fail 1,000 requests
- Once you've had 1,000 failures: STOP deployments/changes

## Burn Rate

Monitor how fast budget is being consumed:

```python
from slo_sli.burn_rate import BurnRate, BurnRateAlert

tracker = BurnRate(window_minutes=5)
alerter = BurnRateAlert(slo_target=0.999, alert_threshold=10.0)

for request in incoming_requests:
    success = process(request)
    tracker.record_event(success)
    alerter.record_event(success)

# Get current burn rate
burn = tracker.get_burn_rate()
# If burn > 1x normal rate: spending budget faster than SLO allows
```

## Alerting Rules

Typical alert rules:
- **CRITICAL**: Burn rate > 10x normal (budget exhausted in hours)
- **HIGH**: Burn rate > 5x normal (budget exhausted in days)
- **MEDIUM**: Burn rate > 1x normal (on pace to exhaust budget)

## Example: Page on High Burn Rate

```python
# Alert immediately if burn rate is critical
if alerter.burn_rate_tracker.get_burn_rate() > threshold:
    notify_oncall()
    disable_non_critical_features()
    pause_deployments()
```

Result: Error budget protected, SLO maintained.
'''


def main():
    with timed_run("slo_sli_generator") as timer:
        logger.debug("Testing SLO/SLI generation")
        gen = SLOSLIGenerator("python")
        files = gen.generate()
        logger.debug(f"Generated {len(files)} files")
        for filepath in files:
            print(f"  ✓ {filepath}")
        check_budget("slo_sli_generator", timer.elapsed_ms, logger)


if __name__ == '__main__':
    main()
