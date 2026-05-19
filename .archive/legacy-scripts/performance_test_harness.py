#!/usr/bin/env python3
"""
Performance Testing Harness

Tests plugin performance under load:
- Decision scoring latency
- Code verification latency
- Event orchestration throughput
- Multi-file formatting speed

Run: python performance_test_harness.py
"""

import sys
import time
import json
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, str(Path(__file__).parent))

from plan_decisions import PlanDecisionEngine
from verify_generated import CodeValidator
from format_multifile_output import MultiFileFormatter


class PerformanceTestHarness:
    """Performance testing for plugin components."""

    def __init__(self):
        self.results = {
            'decision_scoring': {},
            'code_verification': {},
            'multi_file_formatting': {},
            'concurrent_operations': {},
            'overall': {}
        }

    def test_decision_scoring_latency(self):
        """Test decision scoring performance."""
        print("\n" + "="*80)
        print("TEST 1: Decision Scoring Latency")
        print("="*80)

        context = {
            'framework': 'django',
            'language': 'python',
            'framework_version': '4.2',
            'package_manager': 'pip',
            'async_patterns': ['asyncio'],
            'orm_usage': True,
            'orm_type': 'django_orm',
            'testing_framework': 'pytest',
            'logging_style': 'structured',
            'error_handling': 'try_except_logging',
            'validation_style': 'model_validators',
            'codebase_size': 'large',
            'file_count': 150,
        }

        engine = PlanDecisionEngine(context)

        # Warmup
        _ = engine.score_all_decisions()

        # Time 10 runs
        times = []
        for i in range(10):
            start = time.time()
            decisions = engine.score_all_decisions()
            elapsed = time.time() - start
            times.append(elapsed)
            print(f"  Run {i+1}: {elapsed*1000:.2f}ms")

        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)

        self.results['decision_scoring'] = {
            'average_ms': avg_time * 1000,
            'min_ms': min_time * 1000,
            'max_ms': max_time * 1000,
            'target_ms': 100,
            'passed': avg_time * 1000 < 100
        }

        print(f"\n  Average: {avg_time*1000:.2f}ms (target: <100ms)")
        print(f"  Min: {min_time*1000:.2f}ms, Max: {max_time*1000:.2f}ms")
        print(f"  Status: {'✅ PASS' if avg_time * 1000 < 100 else '❌ FAIL'}")

        return avg_time * 1000 < 100

    def test_code_verification_latency(self):
        """Test code verification performance."""
        print("\n" + "="*80)
        print("TEST 2: Code Verification Latency")
        print("="*80)

        validator = CodeValidator(framework='fastapi', language='python')

        # Test code
        test_code = """
from fastapi import FastAPI
from pydantic import BaseModel
import json

app = FastAPI()

class Item(BaseModel):
    id: int
    name: str
    price: float

@app.get("/items")
async def get_items():
    return []

@app.post("/items")
async def create_item(item: Item):
    return item

@app.get("/items/{item_id}")
async def get_item(item_id: int):
    return {"id": item_id}
"""

        # Warmup
        _ = validator.validate_code(test_code, 'python', 'fastapi')

        # Time 10 validations
        times = []
        for i in range(10):
            start = time.time()
            result = validator.validate_code(test_code, 'python', 'fastapi')
            elapsed = time.time() - start
            times.append(elapsed)
            print(f"  Run {i+1}: {elapsed*1000:.2f}ms")

        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)

        self.results['code_verification'] = {
            'average_ms': avg_time * 1000,
            'min_ms': min_time * 1000,
            'max_ms': max_time * 1000,
            'target_ms': 200,
            'passed': avg_time * 1000 < 200
        }

        print(f"\n  Average: {avg_time*1000:.2f}ms (target: <200ms)")
        print(f"  Min: {min_time*1000:.2f}ms, Max: {max_time*1000:.2f}ms")
        print(f"  Status: {'✅ PASS' if avg_time * 1000 < 200 else '❌ FAIL'}")

        return avg_time * 1000 < 200

    def test_multi_file_formatting_speed(self):
        """Test multi-file formatting performance."""
        print("\n" + "="*80)
        print("TEST 3: Multi-File Formatting Speed")
        print("="*80)

        formatter = MultiFileFormatter(framework='django')

        # Generate sample files (simulate 10-file feature)
        files = [
            {'name': f'file{i}.py', 'content': f'# File {i}\n' * 100, 'type': 'module'}
            for i in range(10)
        ]

        # Warmup
        _ = formatter.format_multifile_response(files, 'Test Feature')

        # Time 10 formatting runs
        times = []
        for i in range(10):
            start = time.time()
            output = formatter.format_multifile_response(files, 'Test Feature')
            elapsed = time.time() - start
            times.append(elapsed)
            print(f"  Run {i+1}: {elapsed*1000:.2f}ms ({len(output)} chars)")

        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)

        self.results['multi_file_formatting'] = {
            'average_ms': avg_time * 1000,
            'min_ms': min_time * 1000,
            'max_ms': max_time * 1000,
            'target_ms': 500,
            'passed': avg_time * 1000 < 500
        }

        print(f"\n  Average: {avg_time*1000:.2f}ms (target: <500ms)")
        print(f"  Min: {min_time*1000:.2f}ms, Max: {max_time*1000:.2f}ms")
        print(f"  Status: {'✅ PASS' if avg_time * 1000 < 500 else '❌ FAIL'}")

        return avg_time * 1000 < 500

    def test_concurrent_operations(self):
        """Test concurrent decision scoring."""
        print("\n" + "="*80)
        print("TEST 4: Concurrent Operations (10 parallel)")
        print("="*80)

        context = {
            'framework': 'fastapi',
            'language': 'python',
            'async_patterns': ['async'],
            'orm_usage': True,
            'orm_type': 'sqlalchemy',
            'testing_framework': 'pytest',
            'codebase_size': 'medium',
            'file_count': 50,
        }

        def score_decision():
            engine = PlanDecisionEngine(context)
            return engine.score_all_decisions()

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(score_decision) for _ in range(10)]
            results = []
            for i, future in enumerate(as_completed(futures)):
                result = future.result()
                results.append(result)
                print(f"  Task {i+1}/10 completed")

        elapsed = time.time() - start_time
        avg_time_per_task = elapsed / 10

        self.results['concurrent_operations'] = {
            'total_time_seconds': elapsed,
            'avg_per_task_ms': avg_time_per_task * 1000,
            'tasks': 10,
            'target_seconds': 5,
            'passed': elapsed < 5
        }

        print(f"\n  Total: {elapsed:.2f}s (10 parallel operations)")
        print(f"  Avg per task: {avg_time_per_task*1000:.2f}ms")
        print(f"  Status: {'✅ PASS' if elapsed < 5 else '❌ FAIL'}")

        return elapsed < 5

    def test_concurrent_verifications(self):
        """Test concurrent code verifications."""
        print("\n" + "="*80)
        print("TEST 5: Concurrent Verifications (10 parallel)")
        print("="*80)

        validator = CodeValidator(framework='django', language='python')

        test_code = """
from django.db import models

class User(models.Model):
    email = models.EmailField()
    name = models.CharField(max_length=100)
"""

        def verify_code():
            return validator.validate_code(test_code, 'python', 'django')

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(verify_code) for _ in range(10)]
            results = []
            for i, future in enumerate(as_completed(futures)):
                result = future.result()
                results.append(result)
                print(f"  Task {i+1}/10 completed")

        elapsed = time.time() - start_time

        self.results['concurrent_verifications'] = {
            'total_time_seconds': elapsed,
            'tasks': 10,
            'target_seconds': 5,
            'passed': elapsed < 5
        }

        print(f"\n  Total: {elapsed:.2f}s (10 parallel verifications)")
        print(f"  Status: {'✅ PASS' if elapsed < 5 else '❌ FAIL'}")

        return elapsed < 5

    def run_all_tests(self):
        """Run all performance tests."""
        print("\n" + "="*80)
        print("PERFORMANCE TESTING HARNESS")
        print("="*80)

        tests = [
            ("Decision Scoring Latency", self.test_decision_scoring_latency),
            ("Code Verification Latency", self.test_code_verification_latency),
            ("Multi-File Formatting Speed", self.test_multi_file_formatting_speed),
            ("Concurrent Operations", self.test_concurrent_operations),
            ("Concurrent Verifications", self.test_concurrent_verifications),
        ]

        results = []
        for test_name, test_func in tests:
            try:
                passed = test_func()
                results.append((test_name, passed))
            except Exception as e:
                print(f"❌ Error in {test_name}: {str(e)}")
                results.append((test_name, False))

        # Summary
        print("\n" + "="*80)
        print("PERFORMANCE SUMMARY")
        print("="*80)

        for test_name, passed in results:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status}: {test_name}")

        all_passed = all(r[1] for r in results)
        self.results['overall'] = {
            'status': 'PASSED' if all_passed else 'FAILED',
            'tests_passed': sum(1 for r in results if r[1]),
            'tests_total': len(results),
            'timestamp': time.time()
        }

        print(f"\n{'='*80}")
        print(f"Overall: {'✅ ALL PERFORMANCE TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
        print(f"{'='*80}\n")

        # Save results
        with open('performance_test_results.json', 'w') as f:
            json.dump(self.results, f, indent=2)

        return all_passed


if __name__ == '__main__':
    harness = PerformanceTestHarness()
    success = harness.run_all_tests()
    sys.exit(0 if success else 1)
