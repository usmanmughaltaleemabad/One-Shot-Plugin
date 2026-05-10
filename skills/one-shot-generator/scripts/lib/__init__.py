"""
Shared library for one-shot-prompting scripts.

Provides:
- Version management
- Structured logging
- Performance timing
- Budget checking
"""

from .base_script import (
    __version__,
    PERFORMANCE_BUDGETS,
    setup_logging,
    timed_run,
    check_budget,
)

__all__ = [
    "__version__",
    "PERFORMANCE_BUDGETS",
    "setup_logging",
    "timed_run",
    "check_budget",
]
