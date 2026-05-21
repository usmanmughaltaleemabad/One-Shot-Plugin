#!/usr/bin/env python3
"""
Evaluation harness runner — orchestrates eval tasks and collects metrics.

Usage:
    python eval_runner.py --tasks .claude/evals/tasks.yaml --output baselines/2026-05-21-v1.0.0-baseline.jsonl
    python eval_runner.py --task fastapi-shopping-cart-v1  # Run single task
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import yaml


class EvalRunner:
    """Orchestrates evaluation tasks and collects metrics."""

    def __init__(self, tasks_file: str):
        with open(tasks_file) as f:
            self.config = yaml.safe_load(f)
        self.tasks = self.config['tasks']
        from datetime import timezone
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def run_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single evaluation task and collect metrics.

        Returns:
            {
                "task_id": "fastapi-shopping-cart-v1",
                "framework": "fastapi",
                "difficulty": "easy",
                "metrics": {
                    "routing_quality": 1.0,
                    "cost_usd": 0.45,
                    "test_pass_rate": 0.94,
                    "code_quality_score": 82.5,
                    "security_compliance": 1.0,
                    "activation_time_seconds": 180
                },
                "timestamp": "2026-05-21T...",
                "status": "pass" or "fail",
                "errors": []
            }
        """
        result = {
            "task_id": task['id'],
            "framework": task['framework'],
            "difficulty": task['difficulty'],
            "domain": task.get('domain', 'unknown'),
            "timestamp": self.timestamp,
            "metrics": {},
            "status": "unknown",
            "errors": [],
            "duration_seconds": 0
        }

        start_time = time.time()

        try:
            # STEP 1: Routing Quality — did we pick the right agent?
            # (Simulated; actual implementation calls /one-shot and observes routing trace)
            result['metrics']['routing_quality'] = self._measure_routing(task)

            # STEP 2: Cost — what did this generation cost?
            result['metrics']['cost_usd'] = self._measure_cost(task)

            # STEP 3: Test Pass Rate — do generated tests pass?
            result['metrics']['test_pass_rate'] = self._measure_test_pass_rate(task)

            # STEP 4: Code Quality Score — cyclomatic complexity, type coverage, style
            result['metrics']['code_quality_score'] = self._measure_code_quality(task)

            # STEP 5: Security Compliance — any critical vulns?
            result['metrics']['security_compliance'] = self._measure_security(task)

            # STEP 6: Activation Time — seconds from prompt to commit
            result['metrics']['activation_time_seconds'] = self._measure_activation_time(task)

            # Determine pass/fail based on SLOs
            result['status'] = self._evaluate_slos(result['metrics'])

        except Exception as e:
            result['status'] = 'error'
            result['errors'].append(str(e))

        result['duration_seconds'] = time.time() - start_time
        return result

    def _measure_routing(self, task: Dict) -> float:
        """Routing Quality: percentage of correct first-hop agent selection."""
        # Placeholder: actual implementation observes routing_trace from /one-shot
        # For now, return mock data (95% accuracy across all tasks)
        import random
        return random.uniform(0.92, 0.98)

    def _measure_cost(self, task: Dict) -> float:
        """Cost per generation in USD."""
        # Placeholder: actual implementation sums all API calls
        # Difficulty modulates cost estimate
        base_cost = 0.15
        multipliers = {'easy': 1.0, 'medium': 1.5, 'hard': 2.0}
        return base_cost * multipliers.get(task['difficulty'], 1.5)

    def _measure_test_pass_rate(self, task: Dict) -> float:
        """Test Pass Rate: percentage of generated tests that pass."""
        # Placeholder: actual implementation runs pytest on generated code
        import random
        return random.uniform(0.88, 0.96)

    def _measure_code_quality(self, task: Dict) -> float:
        """Code Quality Score: 0-100 based on complexity, types, style."""
        # Placeholder: actual implementation runs pylint, mypy, flake8
        import random
        return random.uniform(75, 88)

    def _measure_security(self, task: Dict) -> float:
        """Security Compliance: 0 (has vulns) or 1 (clean)."""
        # Placeholder: actual implementation runs bandit/semgrep
        # For now: 98% compliance (2% chance of finding an issue)
        import random
        return 1.0 if random.random() > 0.02 else 0.0

    def _measure_activation_time(self, task: Dict) -> float:
        """Activation Time: seconds from prompt to commit."""
        # Placeholder: actual implementation measures real elapsed time
        base_time = 120  # 2 minutes base
        multipliers = {'easy': 1.0, 'medium': 1.3, 'hard': 1.6}
        import random
        variance = random.uniform(0.9, 1.1)
        return base_time * multipliers.get(task['difficulty'], 1.3) * variance

    def _evaluate_slos(self, metrics: Dict[str, float]) -> str:
        """Determine pass/fail based on SLO thresholds."""
        thresholds = {
            'routing_quality': 0.92,
            'cost_usd': 0.60,  # Alert threshold
            'test_pass_rate': 0.85,  # Alert threshold
            'code_quality_score': 75,
            'security_compliance': 1.0,  # Must be 100%
            'activation_time_seconds': 480  # 8 minutes alert
        }

        for metric, threshold in thresholds.items():
            if metric == 'security_compliance':
                if metrics[metric] < 1.0:
                    return 'fail'
            elif metric == 'code_quality_score':
                if metrics[metric] < threshold:
                    return 'warn'
            else:
                if metrics[metric] < threshold:
                    return 'warn'

        return 'pass'

    def run_all_tasks(self, filter_by_task_id: str = None) -> List[Dict]:
        """Run all tasks (or filter by task_id) and return results."""
        tasks = self.tasks
        if filter_by_task_id:
            tasks = [t for t in tasks if t['id'] == filter_by_task_id]
            if not tasks:
                print(f"[ERROR] Task {filter_by_task_id} not found")
                return []

        results = []
        for i, task in enumerate(tasks, 1):
            print(f"[{i}/{len(tasks)}] Running {task['id']}...", end=' ', flush=True)
            result = self.run_task(task)
            results.append(result)
            print(f"[OK] {result['status']}")

        return results

    def print_summary(self, results: List[Dict]):
        """Print human-readable summary."""
        if not results:
            return

        print("\n" + "=" * 80)
        print("EVALUATION SUMMARY")
        print("=" * 80)

        # Overall stats
        total = len(results)
        passed = sum(1 for r in results if r['status'] == 'pass')
        warned = sum(1 for r in results if r['status'] == 'warn')
        failed = sum(1 for r in results if r['status'] == 'fail')

        print(f"\nResults: {passed}/{total} pass, {warned} warn, {failed} fail")

        # SLO metrics
        print("\nSLO Metrics:")
        metrics_avg = {
            'routing_quality': 'Routing Quality',
            'cost_usd': 'Cost per Gen',
            'test_pass_rate': 'Test Pass Rate',
            'code_quality_score': 'Code Quality',
            'security_compliance': 'Security',
            'activation_time_seconds': 'Activation Time'
        }

        for metric_key, metric_label in metrics_avg.items():
            values = [r['metrics'][metric_key] for r in results if metric_key in r['metrics']]
            if values:
                avg = sum(values) / len(values)
                if metric_key == 'cost_usd':
                    print(f"  {metric_label}: ${avg:.2f} avg")
                elif metric_key == 'activation_time_seconds':
                    print(f"  {metric_label}: {avg:.0f}s avg")
                elif metric_key in ['routing_quality', 'test_pass_rate', 'security_compliance']:
                    print(f"  {metric_label}: {avg*100:.1f}% avg")
                else:
                    print(f"  {metric_label}: {avg:.1f}/100 avg")

        # By framework
        print("\nResults by Framework:")
        frameworks = {}
        for r in results:
            fw = r['framework']
            frameworks.setdefault(fw, []).append(r['status'])

        for fw, statuses in sorted(frameworks.items()):
            pass_count = sum(1 for s in statuses if s == 'pass')
            print(f"  {fw}: {pass_count}/{len(statuses)} pass")

        print("\n" + "=" * 80)


def main():
    parser = argparse.ArgumentParser(description='Run evaluation harness')
    parser.add_argument('--tasks', default='.claude/evals/tasks.yaml', help='Path to tasks.yaml')
    parser.add_argument('--task', help='Run single task by ID')
    parser.add_argument('--output', help='Save results to JSONL file')
    args = parser.parse_args()

    runner = EvalRunner(args.tasks)
    results = runner.run_all_tasks(filter_by_task_id=args.task)

    runner.print_summary(results)

    # Save results to JSONL
    if args.output:
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, 'a') as f:
            for result in results:
                f.write(json.dumps(result) + '\n')
        print(f"\n[OK] Results saved to {args.output}")


if __name__ == '__main__':
    main()
