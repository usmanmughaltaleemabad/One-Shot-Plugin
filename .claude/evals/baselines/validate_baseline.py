#!/usr/bin/env python3
"""Validate baseline results and print summary."""

import json
import sys

def validate_baseline(filename):
    """Validate baseline file and print summary."""
    with open(filename) as f:
        results = [json.loads(line) for line in f]

    print(f"\n[OK] Baseline established: {len(results)} tasks")
    print("\nSLO Performance:")

    # Routing Quality
    routing = [r['metrics']['routing_quality'] for r in results]
    routing_pct = sum(routing)/len(routing)*100
    target = 95
    status = "PASS" if routing_pct >= target else "WARN"
    print(f"  Routing Quality: {routing_pct:.1f}% (target: >={target}%) [{status}]")

    # Cost
    costs = [r['metrics']['cost_usd'] for r in results]
    cost_avg = sum(costs)/len(costs)
    target = 0.50
    status = "PASS" if cost_avg <= target else "WARN"
    print(f"  Cost per Gen: ${cost_avg:.2f} (target: <=${target:.2f}) [{status}]")

    # Test Pass Rate
    test_rates = [r['metrics']['test_pass_rate'] for r in results]
    test_pct = sum(test_rates)/len(test_rates)*100
    target = 90
    status = "PASS" if test_pct >= target else "WARN"
    print(f"  Test Pass Rate: {test_pct:.1f}% (target: >={target}%) [{status}]")

    # Code Quality
    qualities = [r['metrics']['code_quality_score'] for r in results]
    quality_avg = sum(qualities)/len(qualities)
    target = 80
    status = "PASS" if quality_avg >= target else "WARN"
    print(f"  Code Quality: {quality_avg:.1f}/100 (target: >={target}) [{status}]")

    # Security
    security = [r['metrics']['security_compliance'] for r in results]
    security_pct = sum(security)/len(security)*100
    target = 100
    status = "PASS" if security_pct >= target else "FAIL"
    print(f"  Security: {security_pct:.1f}% (target: {target}%) [{status}]")

    # Activation Time
    times = [r['metrics']['activation_time_seconds'] for r in results]
    time_avg = sum(times)/len(times)
    target = 300  # 5 minutes
    status = "PASS" if time_avg <= target else "WARN"
    print(f"  Activation Time: {time_avg:.0f}s (target: <={target}s) [{status}]")

    # Overall status
    statuses = [r['status'] for r in results]
    pass_count = len([s for s in statuses if s == 'pass'])
    warn_count = len([s for s in statuses if s == 'warn'])
    fail_count = len([s for s in statuses if s == 'fail'])

    print(f"\nOverall Results: {pass_count}/{len(results)} pass, {warn_count} warn, {fail_count} fail")

    # By framework
    print("\nResults by Framework:")
    frameworks = {}
    for r in results:
        fw = r['framework']
        frameworks.setdefault(fw, []).append(r['status'])

    for fw in sorted(frameworks.keys()):
        statuses = frameworks[fw]
        pass_count = sum(1 for s in statuses if s == 'pass')
        print(f"  {fw}: {pass_count}/{len(statuses)} pass")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python validate_baseline.py <baseline.jsonl>")
        sys.exit(1)
    validate_baseline(sys.argv[1])
