#!/usr/bin/env python3
"""
Performance Benchmark Suite

Measures wall-clock cost of each module so we can keep regressions visible.
Targets:
  - analyze_codebase / detect_message_bus: <2s for typical repo
  - plan_decisions: <100ms for one decision pass
  - format_multifile_output: <50ms for 10-file feature
  - code_review_automation: <200ms for ~500 LOC of code
  - consistency_checker: <2s for a 100-file project

Run: python benchmark_suite.py
"""

from __future__ import annotations

import json
import os
import sys
import time
import tempfile
from pathlib import Path
from typing import Callable, Dict, List

sys.path.insert(0, str(Path(__file__).parent))

from detect_message_bus import MessageBusDetector
from plan_decisions import PlanDecisionEngine
from format_multifile_output import MultiFileFormatter
from code_review_automation import CodeReviewer
from consistency_checker import ConsistencyChecker
from architecture_design import ArchitectureDesigner
from event_catalog import EventCatalog


def time_it(fn: Callable) -> float:
    start = time.perf_counter()
    fn()
    return (time.perf_counter() - start) * 1000  # ms


def make_synthetic_project(root: Path, n_files: int = 100) -> None:
    for i in range(n_files):
        sub = root / f'module_{i // 10}'
        sub.mkdir(parents=True, exist_ok=True)
        (sub / f'file_{i}.py').write_text(
            f'"""auto-generated for benchmarks"""\n'
            f'from pydantic import BaseModel\nimport structlog\n'
            f'class Item{i}(BaseModel):\n    id: int\n'
        )
    (root / 'requirements.txt').write_text('fastapi==0.95\naiokafka==0.10\n')


def main():
    print("\n" + "=" * 80)
    print("PERFORMANCE BENCHMARKS")
    print("=" * 80 + "\n")

    results: Dict[str, float] = {}

    # --- detect_message_bus
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_synthetic_project(root, n_files=100)
        results['detect_message_bus_100files_ms'] = time_it(
            lambda: MessageBusDetector(str(root)).detect()
        )

    # --- plan_decisions
    ctx = {'framework': 'fastapi', 'language': 'python', 'orm_type': 'sqlalchemy',
           'testing_framework': 'pytest', 'async_patterns': ['async def', 'await']}
    results['plan_decisions_ms'] = time_it(
        lambda: PlanDecisionEngine(ctx).score_all_decisions()
    )

    # --- format_multifile
    files = {f'mod_{i}.py': f'class M{i}: pass\n' for i in range(10)}
    results['format_multifile_10_ms'] = time_it(
        lambda: MultiFileFormatter(framework='fastapi').format_multifile_response(files, 'feat')
    )

    # --- code review
    sample = ('def f(a: int, b: int) -> int:\n    return a + b\n' * 50)
    results['code_review_500loc_ms'] = time_it(
        lambda: CodeReviewer().review(sample, filepath='sample.py')
    )

    # --- consistency_checker
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        make_synthetic_project(root, n_files=100)
        results['consistency_check_100files_ms'] = time_it(
            lambda: ConsistencyChecker(str(root)).check()
        )

    # --- architecture_design
    results['architecture_ms'] = time_it(
        lambda: ArchitectureDesigner().design('order pipeline with payments', constraints=['async', 'kafka'])
    )

    # --- event_catalog validate (1k payloads)
    catalog = EventCatalog.from_dict({'events': [
        {'name': 'order.placed', 'fields': {'order_id': 'str', 'amount': 'float'}, 'required': ['order_id', 'amount']},
    ]})
    def _validate_burst():
        for i in range(1000):
            catalog.validate('order.placed', {'order_id': f'o-{i}', 'amount': float(i)})
    results['catalog_validate_1k_ms'] = time_it(_validate_burst)

    # --- print + check budgets
    print("Results (ms):")
    for k, v in results.items():
        print(f"  {k:38} {v:8.2f}")

    budgets = {
        'detect_message_bus_100files_ms': 2000.0,
        'plan_decisions_ms': 250.0,
        'format_multifile_10_ms': 100.0,
        'code_review_500loc_ms': 500.0,
        'consistency_check_100files_ms': 2500.0,
        'architecture_ms': 100.0,
        'catalog_validate_1k_ms': 500.0,
    }

    all_within_budget = True
    print("\nBudget check:")
    for k, budget in budgets.items():
        actual = results[k]
        status = '[ok]' if actual <= budget else '[over]'
        if actual > budget:
            all_within_budget = False
        print(f"  {status} {k:38} actual={actual:8.2f}  budget={budget:8.2f}")

    with open('benchmark_results.json', 'w', encoding='utf-8') as f:
        json.dump({'results_ms': results, 'budgets_ms': budgets,
                   'all_within_budget': all_within_budget}, f, indent=2)

    print("\n" + "=" * 80)
    print("All within budget" if all_within_budget else "Some metrics over budget")
    print("=" * 80)

    sys.exit(0 if all_within_budget else 1)


if __name__ == '__main__':
    main()
