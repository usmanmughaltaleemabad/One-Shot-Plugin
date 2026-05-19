#!/usr/bin/env python3
"""
Phase 1-3 Integration Tests

Validates all post-Phase-0 modules:
  - v0.7.0  detect_message_bus
  - v0.8.0  event_catalog
  - v0.9.0  domain_observability
  - v0.9.5  preview_mode
  - v0.10.0 code_review_automation
  - v1.1.0  tdd_mode
  - v1.2.0  debugging_helpers
  - v1.3.0  architecture_design
  - v1.3.1  pr_integration
  - v1.3.3  production_debugger
  - v1.3.4  cost_management
  - v1.4.0  strangler_pattern
  - v1.4.1  consistency_checker

Run: python test_phase_1_3_features.py
"""

import json
import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def banner(name: str):
    print("\n" + "=" * 80)
    print(name)
    print("=" * 80)


def test_bus_detection() -> bool:
    from detect_message_bus import MessageBusDetector
    with tempfile.TemporaryDirectory() as tmp:
        # synthetic kafka project
        Path(tmp, 'requirements.txt').write_text('aiokafka==0.10.0\nfastapi==0.95\n')
        Path(tmp, 'main.py').write_text(
            'from aiokafka import AIOKafkaConsumer\n'
            'import asyncio\n'
            'async def main():\n'
            '    consumer = AIOKafkaConsumer("orders")\n'
            '    await asyncio.gather(consumer.start())\n'
        )
        result = MessageBusDetector(tmp).detect()
        assert result['primary_bus'] == 'kafka', f"expected kafka, got {result['primary_bus']}"
        assert result['runtime'] == 'asyncio', f"expected asyncio, got {result['runtime']}"
        assert 'aiokafka' in result['libraries']
    return True


def test_event_catalog() -> bool:
    from event_catalog import EventCatalog
    catalog = EventCatalog.from_dict({'events': [
        {'name': 'order.placed', 'fields': {'order_id': 'str', 'amount': 'float'}, 'required': ['order_id', 'amount']},
    ]})
    ok = catalog.validate('order.placed', {'order_id': 'A', 'amount': 1.5})
    assert ok['valid'], ok
    bad = catalog.validate('order.placed', {'order_id': 'A'})
    assert not bad['valid']
    unknown = catalog.validate('order.shipped', {})
    assert not unknown['valid']
    return True


def test_observability() -> bool:
    from domain_observability import ObservabilityBuilder
    for domain in ('games', 'bots', 'ml', 'trading', 'generic'):
        block = ObservabilityBuilder(domain=domain).build(feature_name='demo')
        assert block['metrics']
        assert block['metric_names']
        assert block['span_names']
    return True


def test_preview() -> bool:
    from preview_mode import PreviewBuilder
    text = PreviewBuilder().build(
        feature='Rate limiter',
        files=[{'name': 'rate_limiter.py', 'loc': 100}],
        decisions=[('Algorithm', 'token bucket')],
        estimated_minutes=10,
    )
    assert 'PREVIEW' in text
    assert 'token bucket' in text
    assert 'rate_limiter.py' in text
    return True


def test_code_review() -> bool:
    from code_review_automation import CodeReviewer
    reviewer = CodeReviewer(framework='django', language='python')

    # Clean code
    clean = ('def add(a: int, b: int) -> int:\n'
             '    return a + b\n')
    report = reviewer.review(clean, filepath='math_utils.py')
    assert report['overall'] in ('PASS', 'WARN'), report

    # Block on hardcoded secret
    bad = 'API_KEY = "abcdef1234567890qwerty"\n'
    report = reviewer.review(bad, filepath='config.py')
    assert report['overall'] == 'BLOCK', report

    # Block on shell=True
    bad2 = 'import subprocess\nsubprocess.run("ls", shell=True)\n'
    report = reviewer.review(bad2, filepath='runner.py')
    assert report['overall'] == 'BLOCK', report
    return True


def test_tdd_mode() -> bool:
    from tdd_mode import TDDGenerator
    out = TDDGenerator(language='python', explain=True).compose(
        feature_name='Counter',
        tests=[{'name': 'test_increment', 'body': 'c = Counter(); c.inc(); assert c.value == 1',
                'intent': 'inc raises value', 'edge_case': 'starting value', 'failure_mode': 'silent no-op'}],
        implementation='class Counter:\n    def __init__(self): self.value = 0\n    def inc(self): self.value += 1\n',
    )
    assert 'Test-First Generation' in out
    assert 'test_increment' in out
    assert 'class Counter' in out
    assert 'Why each test exists' in out
    return True


def test_debugger() -> bool:
    from debugging_helpers import DebuggingHelper
    helper = DebuggingHelper()
    diag = helper.diagnose(error_text='asyncio.TimeoutError: handler exceeded')
    assert diag['pattern'] == 'handler-timeout', diag
    assert diag['fixes'][0]['rank'] >= 0.5

    diag2 = helper.diagnose(error_text='NoneType has no attribute foo')
    assert diag2['pattern'] == 'dependency-injection-missing', diag2
    return True


def test_architecture() -> bool:
    from architecture_design import ArchitectureDesigner
    bp = ArchitectureDesigner().design(
        problem='Order processing pipeline with payments and notifications',
        constraints=['async', 'kafka'],
    )
    assert any(s['name'] == 'orders' for s in bp['services']), bp['services']
    assert any(s['name'] == 'payments' for s in bp['services'])
    assert 'Architecture Blueprint' in bp['markdown']
    assert 'order.placed' in bp['events']
    return True


def test_pr_integration() -> bool:
    from pr_integration import PRIntegration
    bundle = PRIntegration(provider='github', repo='org/repo').build(
        feature='Rate limiter',
        files=[{'path': 'rate_limiter.py', 'kind': 'feature', 'loc': 100}],
        review_findings=[{'severity': 'warn', 'message': 'consider Redis'}],
    )
    assert 'Rate limiter' in bundle['title'].lower() or 'rate' in bundle['title'].lower()
    assert 'rate_limiter.py' in bundle['body']
    assert any('gh pr create' in c for c in bundle['commands'])
    return True


def test_production_debugger() -> bool:
    from production_debugger import ProductionDebugger
    out = ProductionDebugger().respond(
        error_log='asyncio.TimeoutError: handler timed out',
        affected_service='payments',
        request_volume=2000,
    )
    assert out['severity'] == 'P0', out
    assert 'Hypothesis' in out['response']
    assert out['structured']['hotfix']
    return True


def test_cost_management() -> bool:
    from cost_management import CostManager
    with tempfile.TemporaryDirectory() as tmp:
        cm = CostManager(state_dir=tmp)
        cm.set_budget(monthly_tokens=1_000)
        # within budget
        decision = cm.preflight(estimated_tokens=500, label='auth')
        assert decision['allow'], decision
        cm.record(actual_tokens=500, label='auth')
        # exceeds budget
        decision2 = cm.preflight(estimated_tokens=600, label='payments')
        assert not decision2['allow'], decision2
        # report
        report = cm.usage_report()
        assert report['tokens_used_this_month'] == 500
        assert report['monthly_budget'] == 1_000
    return True


def test_strangler() -> bool:
    from strangler_pattern import StranglerGenerator
    files = StranglerGenerator(framework='django').generate(
        legacy_module='legacy_auth.py', new_module='auth_v2.py', feature_flag='AUTH_V2',
    )
    assert 'strangler/router.py' in files
    assert 'strangler/dual_run.py' in files
    assert 'tests/test_strangler_parity.py' in files
    assert 'AUTH_V2' in files['strangler/router.py']
    return True


def test_consistency_checker() -> bool:
    from consistency_checker import ConsistencyChecker
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, 'a.py').write_text('from pydantic import BaseModel\nimport structlog\n')
        Path(tmp, 'b.py').write_text('from dataclasses import dataclass\nimport logging\n')
        Path(tmp, 'c.py').write_text('from pydantic import BaseModel\nimport structlog\n')
        rep = ConsistencyChecker(tmp).check()
        # We expect inconsistencies on serializer + logging axes
        axes = {i['axis'] for i in rep['inconsistencies']}
        assert 'serializers' in axes, rep
        assert 'logging' in axes, rep

        plan = ConsistencyChecker(tmp).standardize(target_library='shared_handlers')
        assert 'shared_handlers/dto.py' in plan
        assert 'shared_handlers/errors.py' in plan
    return True


TESTS = [
    ('v0.7.0  bus detection',         test_bus_detection),
    ('v0.8.0  event catalog',         test_event_catalog),
    ('v0.9.0  domain observability',  test_observability),
    ('v0.9.5  preview mode',          test_preview),
    ('v0.10.0 code review',           test_code_review),
    ('v1.1.0  tdd mode',              test_tdd_mode),
    ('v1.2.0  debugging helpers',     test_debugger),
    ('v1.3.0  architecture design',   test_architecture),
    ('v1.3.1  pr integration',        test_pr_integration),
    ('v1.3.3  production debugger',   test_production_debugger),
    ('v1.3.4  cost management',       test_cost_management),
    ('v1.4.0  strangler pattern',     test_strangler),
    ('v1.4.1  consistency checker',   test_consistency_checker),
]


def main():
    banner("PHASE 1-3 INTEGRATION TESTS")
    results = []
    for name, fn in TESTS:
        try:
            ok = fn()
            results.append((name, ok, None))
            print(f"  [{'PASS' if ok else 'FAIL'}]  {name}")
        except AssertionError as e:
            results.append((name, False, f'AssertionError: {e}'))
            print(f"  [FAIL] {name}: {e}")
        except Exception as e:
            results.append((name, False, f'{type(e).__name__}: {e}'))
            print(f"  [FAIL] {name}: {type(e).__name__}: {e}")

    banner("SUMMARY")
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"  {passed}/{len(results)} passed")
    if passed < len(results):
        print("\nFailures:")
        for name, ok, err in results:
            if not ok:
                print(f"  - {name}: {err}")

    # Persist for orchestrator
    with open('phase_1_3_test_results.json', 'w', encoding='utf-8') as f:
        json.dump([
            {'name': n, 'passed': ok, 'error': err}
            for n, ok, err in results
        ], f, indent=2)

    sys.exit(0 if passed == len(results) else 1)


if __name__ == '__main__':
    main()
