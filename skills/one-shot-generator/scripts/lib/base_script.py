#!/usr/bin/env python3
"""
Shared Base Library for one-shot-prompting Scripts

Provides standardized:
- Version management (__version__)
- Logging setup (structured, silent by default)
- Performance timing (context manager)
- Budget checking (validates execution time)

Usage:
    from lib.base_script import setup_logging, timed_run, __version__

    logger = setup_logging(__name__)
    with timed_run("my_operation") as timer:
        do_work()
    check_budget("my_operation", timer.elapsed_ms)
"""

import os
import sys
import logging
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Dict

__version__ = "0.8.0"


def bootstrap_runtime() -> None:
    """Standard runtime bootstrap every entry-point script should call first.

    - Reconfigures stdout/stderr to UTF-8 on Windows so emoji + non-ASCII
      output works under cp1252 default code page.
    - Adds scripts/ directory to sys.path so sibling top-level scripts
      can be imported without manual path manipulation.

    Safe to call multiple times.
    """
    if sys.platform == "win32":
        for stream in (sys.stdout, sys.stderr):
            try:
                stream.reconfigure(encoding="utf-8")
            except (AttributeError, OSError):
                pass

    scripts_dir = Path(__file__).resolve().parent.parent
    scripts_dir_str = str(scripts_dir)
    if scripts_dir_str not in sys.path:
        sys.path.insert(0, scripts_dir_str)


bootstrap_runtime()

# Performance budgets (milliseconds) — from benchmark_suite.py consolidated here
PERFORMANCE_BUDGETS: Dict[str, int] = {
    "analyze_codebase": 2000,
    "plan_decisions": 250,
    "format_multifile_output": 100,
    "code_review_automation": 500,
    "consistency_checker": 2500,
    "architecture_design": 100,
    "generate_migrations": 300,
    "verify_generated": 200,
    "autowire_into_project": 1000,
    "detect_message_bus": 500,
    "event_catalog": 400,
    "preview_mode": 100,
}


def setup_logging(name: str, level: Optional[str] = None) -> logging.Logger:
    """
    Set up structured logging for a script.

    Args:
        name: Logger name (typically __name__)
        level: Log level ("DEBUG", "INFO", "WARNING", "ERROR")
               If None, uses OSP_LOG_LEVEL env var, defaults to "WARNING"

    Returns:
        Configured logger instance

    Behavior:
        - WARNING level by default (silent in normal operation)
        - DEBUG level via OSP_LOG_LEVEL=DEBUG environment variable
        - Structured output to stderr with timestamps
    """
    if level is None:
        level = os.getenv("OSP_LOG_LEVEL", "WARNING").upper()

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Skip adding handler if already configured (avoid duplicates)
    if logger.handlers:
        return logger

    # Format: timestamp [LEVEL] logger_name: message
    formatter = logging.Formatter(
        fmt='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


class timed_run:
    """
    Context manager for timing code execution.

    Usage:
        with timed_run("operation_name") as timer:
            do_work()
        # timer.elapsed_ms contains duration in milliseconds

    Attributes:
        name: Operation name
        elapsed_ms: Duration in milliseconds after context exits
    """

    def __init__(self, name: str):
        self.name = name
        self.start_time: Optional[float] = None
        self.elapsed_ms: float = 0.0

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            self.elapsed_ms = (time.perf_counter() - self.start_time) * 1000
        return False  # Don't suppress exceptions


def check_budget(operation_name: str, elapsed_ms: float, logger: Optional[logging.Logger] = None) -> bool:
    """
    Check if operation execution time is within budget.

    Args:
        operation_name: Key in PERFORMANCE_BUDGETS
        elapsed_ms: Actual duration in milliseconds
        logger: Optional logger for warning output

    Returns:
        True if within budget, False otherwise

    Side effects:
        Logs WARNING if exceeded
    """
    budget_ms = PERFORMANCE_BUDGETS.get(operation_name)

    if budget_ms is None:
        # Operation not in budget list (new operation, not monitored)
        return True

    within_budget = elapsed_ms <= budget_ms

    if not within_budget and logger:
        logger.warning(
            f"{operation_name} exceeded budget: {elapsed_ms:.0f}ms > {budget_ms}ms"
        )

    return within_budget
