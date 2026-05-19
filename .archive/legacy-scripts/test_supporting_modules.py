#!/usr/bin/env python3
"""
Supporting Module Tests (v2.0.0)

Validates the discovery / orchestration / harness modules added on top of
the v1.4.1 baseline:
  - health_check
  - template_library
  - interactive_tour
  - multi_sidecar_orchestration

Run: python test_supporting_modules.py
"""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))


def banner(name):
    print("\n" + "=" * 80)
    print(name)
    print("=" * 80)


# ---------------------------------------------------------------------------

def test_health_check_django() -> bool:
    from health_check import HealthChecker
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / 'manage.py').write_text('# django\n')
        (root / 'requirements.txt').write_text('django==4.2\nstructlog==23.1\npytest-django==4.5\n')
        (root / 'app').mkdir()
        (root / 'app' / 'views.py').write_text('import structlog\n')
        (root / 'pytest.ini').write_text('[pytest]\n')
        (root / 'Dockerfile').write_text('FROM python:3.11\n')
        report = HealthChecker(str(root)).scan()
        assert report['framework'] == 'django', report
        assert report['testing'] == 'pytest', report
        assert 'Dockerfile' in report['iac'], report
        text = HealthChecker(str(root)).format_report(report)
        assert 'Health Check Report' in text
    return True


def test_health_check_empty_project() -> bool:
    from health_check import HealthChecker
    with tempfile.TemporaryDirectory() as tmp:
        report = HealthChecker(tmp).scan()
        assert report['framework'] == ''
        assert report['recommendations'], report
    return True


def test_templates_list_and_search() -> bool:
    from template_library import TemplateLibrary
    lib = TemplateLibrary()
    all_t = lib.list()
    assert len(all_t) >= 25, f"only {len(all_t)} templates"
    msg = lib.list(tag='messaging')
    assert msg and all('messaging' in t['tags'] for t in msg)
    found = lib.search('rate-limited')
    assert any('rate' in t['title'].lower() or 'rate' in t['prompt'].lower() for t in found), found
    one = lib.get('msg-kafka-validate')
    assert one and one['id'] == 'msg-kafka-validate'
    assert lib.get('does-not-exist') is None
    tags = lib.tags()
    assert 'messaging' in tags and 'observability' in tags
    return True


def test_tour_initial_state() -> bool:
    from interactive_tour import InteractiveTour
    tour = InteractiveTour()
    state = tour.start()
    assert state['id'] == 'start'
    assert any(opt['key'] == 'b' for opt in state['options'])
    return True


def test_tour_to_recommendation() -> bool:
    from interactive_tour import InteractiveTour
    tour = InteractiveTour()
    state = tour.start()
    state = tour.choose(state, 'b')           # consumers
    assert state['id'] == 'consumers'
    state = tour.choose(state, 'a')           # kafka
    assert state['id'] == 'recommendation'
    assert state['recommended_templates']
    return True


def test_tour_browse_state() -> bool:
    from interactive_tour import InteractiveTour
    tour = InteractiveTour()
    state = tour.start()
    state = tour.choose(state, 'g')           # browse
    assert state['id'] == 'browse'
    assert state['options']
    return True


def test_tour_unknown_key_falls_back() -> bool:
    from interactive_tour import InteractiveTour
    tour = InteractiveTour()
    state = tour.start()
    state = tour.choose(state, 'zzz')
    assert state['id'] == 'error'
    return True


def test_multi_sidecar_pipeline() -> bool:
    import ast
    from multi_sidecar_orchestration import MultiSidecarOrchestrator
    files = MultiSidecarOrchestrator(framework='fastapi').generate([
        {'name': 'validator', 'consumes': 'order.created', 'produces_success': 'order.validated'},
        {'name': 'inventory', 'consumes': 'order.validated', 'produces_success': 'inventory.reserved',
         'produces_failure': 'inventory.unavailable'},
        {'name': 'payment',   'consumes': 'inventory.reserved', 'produces_success': 'payment.charged',
         'produces_failure': 'payment.failed'},
    ])
    # All Python files parse
    for path, content in files.items():
        if path.endswith('.py'):
            ast.parse(content)
    # Router wires every step
    router = files['orchestration/router.py']
    for step in ('validator', 'inventory', 'payment'):
        assert f'handle_{step}' in router
    # E2E test references the entry event
    e2e = files['tests/test_pipeline_e2e.py']
    assert 'order.created' in e2e
    return True


def test_multi_sidecar_dashboard_valid_json() -> bool:
    from multi_sidecar_orchestration import MultiSidecarOrchestrator
    files = MultiSidecarOrchestrator().generate([
        {'name': 'a', 'consumes': 'in', 'produces_success': 'a.done'},
    ])
    json.loads(files['observability/dashboard.json'])  # raises if bad
    return True


# ---------------------------------------------------------------------------

TESTS = [
    ('health-check django project',  test_health_check_django),
    ('health-check empty project',   test_health_check_empty_project),
    ('template library list+search', test_templates_list_and_search),
    ('tour initial state',           test_tour_initial_state),
    ('tour walks to recommendation', test_tour_to_recommendation),
    ('tour browse state populated',  test_tour_browse_state),
    ('tour unknown key fallback',    test_tour_unknown_key_falls_back),
    ('multi-sidecar pipeline',       test_multi_sidecar_pipeline),
    ('multi-sidecar dashboard json', test_multi_sidecar_dashboard_valid_json),
]


def main():
    banner("SUPPORTING MODULES TESTS")
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

    passed = sum(1 for _, ok, _ in results if ok)
    print("\n" + "=" * 80)
    print(f"  {passed}/{len(results)} passed")
    print("=" * 80)

    with open('supporting_modules_results.json', 'w', encoding='utf-8') as f:
        json.dump([{'name': n, 'passed': ok, 'error': err}
                   for n, ok, err in results], f, indent=2)

    sys.exit(0 if passed == len(results) else 1)


if __name__ == '__main__':
    main()
