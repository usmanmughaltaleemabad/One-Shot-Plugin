#!/usr/bin/env python3
"""
Robustness Tests

Negative tests, edge cases, and end-to-end project simulations across
*every* module shipped in v1.4.1. Designed to catch regressions where a
module silently degrades on bad input.

Run: python test_robustness.py
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


# ----------------------------------------------------------------------------
# Negative tests - modules must not crash on empty / malformed input
# ----------------------------------------------------------------------------

def test_bus_detector_empty_dir() -> bool:
    from detect_message_bus import MessageBusDetector
    with tempfile.TemporaryDirectory() as tmp:
        result = MessageBusDetector(tmp).detect()
        assert result['primary_bus'] == 'none'
        assert result['runtime'] == 'sync'
        assert result['confidence'] == 0.0
    return True


def test_bus_detector_unreadable_files() -> bool:
    from detect_message_bus import MessageBusDetector
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / 'binary.py').write_bytes(b'\x80\x81\x82\x83\x84')
        result = MessageBusDetector(tmp).detect()
        # Should not raise; should still produce a result
        assert isinstance(result, dict)
        assert 'primary_bus' in result
    return True


def test_catalog_unknown_format() -> bool:
    from event_catalog import EventCatalog
    with tempfile.NamedTemporaryFile(suffix='.txt', mode='w', delete=False) as f:
        f.write('not a catalog')
        path = f.name
    try:
        try:
            EventCatalog.from_file(path)
        except ValueError:
            return True
        return False  # Should have raised
    finally:
        os.unlink(path)


def test_catalog_invalid_payload_types() -> bool:
    from event_catalog import EventCatalog
    catalog = EventCatalog.from_dict({'events': [
        {'name': 'order.placed', 'fields': {'amount': 'float'}, 'required': ['amount']},
    ]})
    bad = catalog.validate('order.placed', {'amount': 'not-a-number'})
    assert not bad['valid']
    assert any('expected float' in e for e in bad['errors']), bad
    return True


def test_review_handles_empty_code() -> bool:
    from code_review_automation import CodeReviewer
    report = CodeReviewer().review('', filepath='empty.py')
    assert report['overall'] in ('PASS', 'WARN'), report
    return True


def test_review_warns_on_blocking_async() -> bool:
    from code_review_automation import CodeReviewer
    code = (
        "import time\n"
        "async def handler():\n"
        "    time.sleep(1)\n"
        "    return 'ok'\n"
    )
    report = CodeReviewer().review(code, filepath='handler.py')
    perf = report['sections']['performance']
    assert perf['status'] in ('WARN', 'BLOCK'), perf
    return True


def test_debugger_unknown_pattern() -> bool:
    from debugging_helpers import DebuggingHelper
    diag = DebuggingHelper().diagnose(error_text='wibblefish failed')
    assert diag['pattern'] == 'unknown'
    assert diag['fixes'], diag
    return True


def test_cost_no_budget() -> bool:
    from cost_management import CostManager
    with tempfile.TemporaryDirectory() as tmp:
        cm = CostManager(state_dir=tmp)
        decision = cm.preflight(estimated_tokens=1_000_000, label='huge')
        assert decision['allow'], 'no budget set should always allow'
    return True


def test_cost_corrupt_log() -> bool:
    from cost_management import CostManager
    with tempfile.TemporaryDirectory() as tmp:
        cm = CostManager(state_dir=tmp)
        # corrupt log
        (Path(tmp) / 'usage-log.jsonl').write_text('not json\n{"timestamp": "bad", broken\n')
        used = cm.tokens_used_this_month()
        assert used == 0, used
    return True


def test_strangler_files_exist_and_runnable_python() -> bool:
    """Generated router/adapter/dual_run modules must parse as valid Python."""
    import ast
    from strangler_pattern import StranglerGenerator
    files = StranglerGenerator(framework='django').generate(
        legacy_module='legacy_auth.py', new_module='auth_v2.py', feature_flag='AUTH_V2',
    )
    for path, content in files.items():
        if path.endswith('.py'):
            ast.parse(content)  # raises SyntaxError if bad
    return True


def test_consistency_checker_handles_unicode() -> bool:
    from consistency_checker import ConsistencyChecker
    with tempfile.TemporaryDirectory() as tmp:
        # Write UTF-8 content with emoji etc.
        Path(tmp, 'a.py').write_text('# coding: utf-8\n# 你好 - pydantic\nfrom pydantic import BaseModel\n', encoding='utf-8')
        Path(tmp, 'b.py').write_text('# 🚀 dataclass\nfrom dataclasses import dataclass\n', encoding='utf-8')
        report = ConsistencyChecker(tmp).check()
        assert report['files_scanned'] >= 2
    return True


def test_arch_design_no_keywords_falls_back() -> bool:
    from architecture_design import ArchitectureDesigner
    bp = ArchitectureDesigner().design(problem='do something useful', constraints=[])
    assert any(s['name'] == 'core' for s in bp['services']), bp
    return True


def test_pr_integration_long_title_truncated() -> bool:
    from pr_integration import PRIntegration
    long_feature = 'A very very long feature description that definitely exceeds 70 chars and keeps going'
    bundle = PRIntegration(provider='github').build(feature=long_feature, files=[], review_findings=[])
    assert len(bundle['title']) <= 68, bundle['title']
    return True


def test_observability_unknown_domain_falls_back() -> bool:
    from domain_observability import ObservabilityBuilder
    block = ObservabilityBuilder(domain='quantum-computing').build(feature_name='x')
    assert block['domain'] == 'generic', block
    assert block['metric_names'], block
    return True


def test_preview_handles_missing_fields() -> bool:
    from preview_mode import PreviewBuilder
    text = PreviewBuilder().build(
        feature='X',
        files=[{}],  # missing name + loc
        decisions=[],
        estimated_minutes=0,
    )
    assert 'PREVIEW' in text
    return True


def test_tdd_handles_empty_tests() -> bool:
    from tdd_mode import TDDGenerator
    out = TDDGenerator().compose(feature_name='X', tests=[], implementation='pass\n')
    assert 'Test-First Generation' in out
    return True


def test_production_debugger_low_traffic() -> bool:
    from production_debugger import ProductionDebugger
    out = ProductionDebugger().respond(error_log='warning: small thing', request_volume=2)
    assert out['severity'] in ('P2', 'P3')
    return True


# ----------------------------------------------------------------------------
# End-to-end project simulations
# ----------------------------------------------------------------------------

def test_e2e_django_kafka_project() -> bool:
    """Simulate a Django+Kafka project; bus detector + catalog + review pipeline."""
    from detect_message_bus import MessageBusDetector
    from event_catalog import EventCatalog
    from code_review_automation import CodeReviewer

    with tempfile.TemporaryDirectory() as tmp:
        # synthetic project
        (Path(tmp) / 'requirements.txt').write_text(
            'django==4.2\nkafka-python==2.0.2\nstructlog==23.1\n'
        )
        (Path(tmp) / 'app').mkdir()
        (Path(tmp) / 'app' / 'consumer.py').write_text(
            'from kafka import KafkaConsumer\n'
            'import structlog\n'
            'log = structlog.get_logger()\n'
            'def consume():\n'
            '    consumer = KafkaConsumer("orders")\n'
            '    for msg in consumer:\n'
            '        log.info("received", msg=msg)\n'
        )
        (Path(tmp) / 'events.json').write_text(json.dumps({'events': [
            {'name': 'order.placed', 'fields': {'order_id': 'str'}, 'required': ['order_id']},
        ]}))

        bus = MessageBusDetector(tmp).detect()
        assert bus['primary_bus'] == 'kafka', bus

        catalog = EventCatalog.from_file(str(Path(tmp) / 'events.json'))
        assert catalog.has('order.placed')

        reviewer = CodeReviewer(framework='django', language='python')
        report = reviewer.review((Path(tmp) / 'app' / 'consumer.py').read_text(encoding='utf-8'),
                                 filepath='app/consumer.py')
        assert report['overall'] in ('PASS', 'WARN'), report
    return True


def test_e2e_strangler_with_consistency_check() -> bool:
    """Generate strangler files, place them in a project, verify consistency checker runs cleanly."""
    from strangler_pattern import StranglerGenerator
    from consistency_checker import ConsistencyChecker

    with tempfile.TemporaryDirectory() as tmp:
        files = StranglerGenerator(framework='django').generate(
            legacy_module='legacy', new_module='new_module', feature_flag='FF',
        )
        for path, content in files.items():
            full = Path(tmp) / path
            full.parent.mkdir(parents=True, exist_ok=True)
            full.write_text(content, encoding='utf-8')

        report = ConsistencyChecker(tmp).check()
        # No inconsistencies because all files come from the same generator.
        # But the checker should run successfully.
        assert report['files_scanned'] >= 1, report
    return True


def test_e2e_arch_to_generation_to_pr() -> bool:
    """Architecture blueprint --> simulated generation --> PR bundle."""
    from architecture_design import ArchitectureDesigner
    from pr_integration import PRIntegration
    from preview_mode import PreviewBuilder

    bp = ArchitectureDesigner(framework='fastapi').design(
        problem='Order pipeline with payment + notification',
        constraints=['async', 'kafka'],
    )
    assert any(s['name'] == 'orders' for s in bp['services'])

    files = [{'path': f'{s["name"]}/handlers.py', 'kind': 'feature', 'loc': 120}
             for s in bp['services']]

    preview = PreviewBuilder(framework='fastapi').build(
        feature='Order pipeline',
        files=[{'name': f['path'], 'loc': f['loc']} for f in files],
        decisions=[('Bus', 'kafka'), ('Concurrency', 'async')],
        estimated_minutes=20,
    )
    assert 'PREVIEW' in preview

    bundle = PRIntegration(provider='github').build(
        feature='Order pipeline',
        files=files,
        review_findings=[],
    )
    assert 'order pipeline' in bundle['title'].lower() or 'order' in bundle['title'].lower()
    return True


# ----------------------------------------------------------------------------
# Cross-module: verify_generated should reject blocking-secret code
# ----------------------------------------------------------------------------

def test_verify_generated_blocks_on_syntax_error() -> bool:
    from verify_generated import CodeValidator
    bad = "def broken(:\n    pass\n"
    result = CodeValidator(framework='fastapi', language='python').validate_code(bad, 'python', 'fastapi')
    assert result['status'] in ('REPAIRED', 'FAILED'), result
    return True


def test_verify_generated_passes_clean_python() -> bool:
    from verify_generated import CodeValidator
    good = "from fastapi import FastAPI\napp = FastAPI()\n"
    result = CodeValidator(framework='fastapi', language='python').validate_code(good, 'python', 'fastapi')
    assert result['status'] == 'PASSED', result
    return True


# ----------------------------------------------------------------------------

ROBUSTNESS_TESTS = [
    ('bus detector - empty dir',                 test_bus_detector_empty_dir),
    ('bus detector - unreadable files',          test_bus_detector_unreadable_files),
    ('catalog - unknown format raises',          test_catalog_unknown_format),
    ('catalog - type validation',                test_catalog_invalid_payload_types),
    ('review - empty code',                      test_review_handles_empty_code),
    ('review - blocking call in async',          test_review_warns_on_blocking_async),
    ('debugger - unknown pattern fallback',      test_debugger_unknown_pattern),
    ('cost - no budget allows everything',       test_cost_no_budget),
    ('cost - corrupt log handled',               test_cost_corrupt_log),
    ('strangler - generated python parses',      test_strangler_files_exist_and_runnable_python),
    ('consistency - unicode files',              test_consistency_checker_handles_unicode),
    ('arch - no-keyword fallback',               test_arch_design_no_keywords_falls_back),
    ('pr - long title truncated',                test_pr_integration_long_title_truncated),
    ('observability - unknown domain fallback',  test_observability_unknown_domain_falls_back),
    ('preview - missing fields',                 test_preview_handles_missing_fields),
    ('tdd - empty tests',                        test_tdd_handles_empty_tests),
    ('prod debugger - low-severity classification', test_production_debugger_low_traffic),
    ('e2e - django + kafka pipeline',            test_e2e_django_kafka_project),
    ('e2e - strangler + consistency',            test_e2e_strangler_with_consistency_check),
    ('e2e - arch --> preview --> PR',                test_e2e_arch_to_generation_to_pr),
    ('verify - blocks bad syntax',               test_verify_generated_blocks_on_syntax_error),
    ('verify - passes clean python',             test_verify_generated_passes_clean_python),
]


def main():
    banner("ROBUSTNESS + E2E TESTS")
    results = []
    for name, fn in ROBUSTNESS_TESTS:
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

    with open('robustness_test_results.json', 'w', encoding='utf-8') as f:
        json.dump([
            {'name': n, 'passed': ok, 'error': err}
            for n, ok, err in results
        ], f, indent=2)

    sys.exit(0 if passed == len(results) else 1)


if __name__ == '__main__':
    main()
