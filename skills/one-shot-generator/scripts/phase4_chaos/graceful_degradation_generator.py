#!/usr/bin/env python3
"""Graceful Degradation Generator - Degradation Patterns

Generates:
- Load shedding (reject low-priority requests)
- Feature flags (disable non-critical features)
- Cache fallback (serve stale data)
- Feature downgrade (reduced functionality)
"""

import sys
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.base_script import setup_logging, timed_run, check_budget

__version__ = "0.7.0"
logger = setup_logging(__name__)


class GracefulDegradationGenerator:
    """Generates graceful degradation patterns."""

    def __init__(self, framework: str):
        self.framework = framework.lower()

    def generate(self) -> Dict[str, str]:
        files = {}
        files['resilience/degradation.py'] = self._degradation()
        files['resilience/load_shedding.py'] = self._load_shedding()
        files['resilience/feature_flags.py'] = self._feature_flags()
        files['resilience/cache_fallback.py'] = self._cache_fallback()
        files['resilience/README.md'] = self._readme()
        return files

    def _degradation(self) -> str:
        return '''"""Graceful Degradation - Reduce Functionality Under Load"""

import logging
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class DegradationLevel(Enum):
    NORMAL = 0
    REDUCED_FEATURES = 1
    CRITICAL_ONLY = 2


class GracefulDegradation:
    """Manage graceful degradation under load"""

    def __init__(self):
        self.degradation_level = DegradationLevel.NORMAL
        self.disabled_features = set()

    def set_degradation_level(self, level: DegradationLevel):
        """Set degradation level"""
        self.degradation_level = level
        logger.warning(f"Degradation level set to: {level.name}")

    def disable_feature(self, feature_name: str):
        """Disable a feature"""
        self.disabled_features.add(feature_name)
        logger.warning(f"Feature disabled: {feature_name}")

    def enable_feature(self, feature_name: str):
        """Re-enable a feature"""
        self.disabled_features.discard(feature_name)
        logger.info(f"Feature enabled: {feature_name}")

    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if feature is enabled"""
        if self.degradation_level == DegradationLevel.CRITICAL_ONLY:
            return feature_name in ['auth', 'payment', 'core_api']

        if self.degradation_level == DegradationLevel.REDUCED_FEATURES:
            return feature_name not in self.disabled_features and feature_name not in ['recommendations', 'analytics']

        return feature_name not in self.disabled_features

    def guard_feature(self, feature_name: str, func: Callable, *args, **kwargs) -> Any:
        """Execute function only if feature is enabled"""
        if not self.is_feature_enabled(feature_name):
            logger.debug(f"Feature {feature_name} is disabled")
            return None

        return func(*args, **kwargs)

    def get_status(self) -> dict:
        """Get degradation status"""
        return {
            "degradation_level": self.degradation_level.name,
            "disabled_features": list(self.disabled_features),
        }
'''

    def _load_shedding(self) -> str:
        return '''"""Load Shedding - Reject Low-Priority Requests Under Load"""

import logging
import threading
from enum import Enum
from typing import Callable, Any

logger = logging.getLogger(__name__)


class Priority(Enum):
    CRITICAL = 0      # Must complete
    HIGH = 1          # Should complete
    NORMAL = 2        # Nice to have
    LOW = 3           # Can defer


class LoadShedder:
    """Shed low-priority load when system overloaded"""

    def __init__(self, cpu_threshold: float = 0.8, memory_threshold: float = 0.85):
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        self.current_load = 0.0
        self.shedding_enabled = False

    def set_load(self, load: float):
        """Set current system load (0-1)"""
        self.current_load = load
        self.shedding_enabled = load > self.cpu_threshold

        if self.shedding_enabled:
            logger.warning(f"Load shedding enabled (load: {load:.2%})")

    def can_accept_request(self, priority: Priority) -> bool:
        """Check if request should be accepted"""
        if not self.shedding_enabled:
            return True

        # Under load, reject LOW and NORMAL priority
        if priority == Priority.LOW:
            logger.warning("Rejecting LOW priority request (shedding)")
            return False
        if priority == Priority.NORMAL and self.current_load > 0.9:
            logger.warning("Rejecting NORMAL priority request (high load)")
            return False

        return True

    def call(self, func: Callable, priority: Priority, *args, **kwargs) -> Any:
        """Execute function if load allows"""
        if not self.can_accept_request(priority):
            raise LoadShed(f"Request rejected due to load shedding")
        return func(*args, **kwargs)

    def decorator(self, priority: Priority = Priority.NORMAL):
        """Decorator for load shedding"""
        def decorator_wrapper(func: Callable) -> Callable:
            def wrapper(*args, **kwargs):
                return self.call(func, priority, *args, **kwargs)
            return wrapper
        return decorator_wrapper


class LoadShed(Exception):
    """Request was shed due to load"""
    pass
'''

    def _feature_flags(self) -> str:
        return '''"""Feature Flags - Control Feature Availability"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class FeatureFlag:
    """Feature flag with metadata"""

    def __init__(self, name: str, enabled: bool = False, description: str = "", critical: bool = False):
        self.name = name
        self.enabled = enabled
        self.description = description
        self.critical = critical  # Cannot be disabled under any circumstances


class FeatureFlags:
    """Manage feature flags"""

    def __init__(self):
        self.flags: Dict[str, FeatureFlag] = {}

    def register_flag(self, name: str, enabled: bool = False, description: str = "", critical: bool = False):
        """Register a feature flag"""
        self.flags[name] = FeatureFlag(name, enabled, description, critical)
        logger.info(f"Registered flag: {name} (enabled={enabled})")

    def enable(self, flag_name: str):
        """Enable a flag"""
        if flag_name not in self.flags:
            logger.warning(f"Flag not found: {flag_name}")
            return
        self.flags[flag_name].enabled = True
        logger.info(f"Flag enabled: {flag_name}")

    def disable(self, flag_name: str):
        """Disable a flag"""
        if flag_name not in self.flags:
            logger.warning(f"Flag not found: {flag_name}")
            return

        flag = self.flags[flag_name]
        if flag.critical:
            logger.error(f"Cannot disable critical flag: {flag_name}")
            return

        flag.enabled = False
        logger.info(f"Flag disabled: {flag_name}")

    def is_enabled(self, flag_name: str) -> bool:
        """Check if flag is enabled"""
        if flag_name not in self.flags:
            return False
        return self.flags[flag_name].enabled

    def get_all_flags(self) -> Dict[str, bool]:
        """Get all flags and their status"""
        return {name: flag.enabled for name, flag in self.flags.items()}


def feature_flag(flag_name: str, flags: FeatureFlags):
    """Decorator to guard feature with flag"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not flags.is_enabled(flag_name):
                logger.debug(f"Feature {flag_name} is disabled")
                return None
            return func(*args, **kwargs)
        return wrapper
    return decorator
'''

    def _cache_fallback(self) -> str:
        return '''"""Cache Fallback - Serve Stale Data When Primary Fails"""

import logging
from typing import Any, Callable, Optional, Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CacheFallback:
    """Fallback to cached data when primary fails"""

    def __init__(self, ttl_seconds: int = 3600):
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, tuple] = {}  # key -> (value, timestamp)

    def get_cached(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        if key not in self.cache:
            return None

        value, timestamp = self.cache[key]
        age = (datetime.now() - timestamp).total_seconds()

        if age > self.ttl_seconds:
            del self.cache[key]
            logger.debug(f"Cache expired: {key}")
            return None

        logger.debug(f"Cache hit (age: {age:.0f}s): {key}")
        return value

    def set_cached(self, key: str, value: Any):
        """Store value in cache"""
        self.cache[key] = (value, datetime.now())
        logger.debug(f"Cached: {key}")

    def call(self, func: Callable, key: str, *args, **kwargs) -> Any:
        """Try to call function, fall back to cache on error"""
        try:
            result = func(*args, **kwargs)
            self.set_cached(key, result)
            return result
        except Exception as e:
            logger.warning(f"Function failed: {e}, checking cache")
            cached = self.get_cached(key)
            if cached is not None:
                logger.warning(f"Returning cached data for {key} (stale)")
                return cached
            raise

    def decorator(self, cache_key: str):
        """Decorator with cache fallback"""
        def decorator_wrapper(func: Callable):
            def wrapper(*args, **kwargs):
                return self.call(func, cache_key, *args, **kwargs)
            return wrapper
        return decorator_wrapper

    def get_stats(self) -> dict:
        """Get cache statistics"""
        return {
            "cached_keys": len(self.cache),
            "keys": list(self.cache.keys()),
        }
'''

    def _readme(self) -> str:
        return '''# Graceful Degradation

## Feature Degradation

Reduce functionality under load:

```python
from resilience.degradation import GracefulDegradation, DegradationLevel

degradation = GracefulDegradation()

# Set degradation level
degradation.set_degradation_level(DegradationLevel.REDUCED_FEATURES)

# Check if feature enabled
if degradation.is_feature_enabled("recommendations"):
    show_recommendations()
else:
    logger.warning("Recommendations disabled due to degradation")
```

## Load Shedding

Reject low-priority requests:

```python
from resilience.load_shedding import LoadShedder, Priority

shedder = LoadShedder(cpu_threshold=0.8)
shedder.set_load(0.85)  # CPU at 85%

@shedder.decorator(Priority.NORMAL)
def analytics_call():
    return perform_analytics()

try:
    analytics_call()
except LoadShed:
    logger.warning("Request shed due to load")
```

## Feature Flags

Control feature availability:

```python
from resilience.feature_flags import FeatureFlags, feature_flag

flags = FeatureFlags()
flags.register_flag("new_ui", enabled=False)

@feature_flag("new_ui", flags)
def render_new_ui():
    return new_ui_html()
```

Disable under degradation:
```python
if degradation.degradation_level == DegradationLevel.CRITICAL_ONLY:
    flags.disable("new_ui")
    flags.disable("recommendations")
```

## Cache Fallback

Serve stale data when primary fails:

```python
from resilience.cache_fallback import CacheFallback

cache = CacheFallback(ttl_seconds=3600)

@cache.decorator(cache_key="user_profile:123")
def get_user_profile(user_id):
    return db.get_user(user_id)

# Returns stale data if database is down
profile = get_user_profile(123)
```

## Combining Patterns

```python
# Under high load:
degradation.set_degradation_level(DegradationLevel.REDUCED_FEATURES)
shedder.set_load(0.9)
flags.disable("new_ui")

# Now:
# - Low-priority requests are rejected
# - Non-critical features disabled
# - New UI unavailable
# - Serve stale cached data
```

Result: System stays responsive with reduced functionality instead of crashing.
'''


def main():
    with timed_run("graceful_degradation_generator") as timer:
        logger.debug("Testing Graceful Degradation generation")
        gen = GracefulDegradationGenerator("python")
        files = gen.generate()
        logger.debug(f"Generated {len(files)} files")
        for filepath in files:
            print(f"  ✓ {filepath}")
        check_budget("graceful_degradation_generator", timer.elapsed_ms, logger)


if __name__ == '__main__':
    main()
