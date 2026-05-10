# Testing Guide — one-shot-prompting Plugin

This document explains how to run tests, understand the test structure, and add new tests.

---

## Quick Start

### Run All Tests (Recommended)

```bash
# Master orchestrator (Phase 0-3 + fixtures + benchmarks)
python RUN_INTEGRATION_TESTS.py
```

### Run Tests by Category

```bash
# Unit tests only
python -m pytest skills/one-shot-generator/scripts/test_*.py -v

# Fixture-based integration tests
python -m pytest tests/test_integration_fixtures.py -v

# Phase 0: Planning engine + verification
python skills/one-shot-generator/scripts/test_phase_0_integration.py

# Gap 1: Multi-file generation + auto-wiring
python skills/one-shot-generator/scripts/test_gap_1_multifile.py

# All gaps (2-8): migrations, config, CLI, events, etc.
python skills/one-shot-generator/scripts/test_all_gaps.py
```

### Run with Logging (Debug Mode)

```bash
# Enable DEBUG logging to see what each script is doing
OSP_LOG_LEVEL=DEBUG python skills/one-shot-generator/scripts/analyze_codebase.py "add auth @/some/path"

# All tests with logging
OSP_LOG_LEVEL=DEBUG python RUN_INTEGRATION_TESTS.py
```

---

## Test Structure

### Directory Layout

```
one-shot-prompting/
├── skills/one-shot-generator/
│   └── scripts/
│       ├── test_phase_0_integration.py    ← Phase 0 validation
│       ├── test_gap_1_multifile.py        ← Gap 1: multi-file + auto-wiring
│       ├── test_all_gaps.py               ← Gaps 2-8: migrations, config, etc.
│       ├── test_phase_1_3_features.py     ← Phase 1-3 features (bus, catalog, etc.)
│       ├── test_robustness.py             ← Negative tests, edge cases
│       ├── test_supporting_modules.py     ← Health-check, templates, tour
│       ├── performance_test_harness.py    ← Performance budgets + timing
│       └── benchmark_suite.py             ← Per-module budget validation
│
├── tests/
│   ├── fixtures/
│   │   ├── django_minimal/                ← Synthetic Django project
│   │   │   ├── manage.py
│   │   │   ├── settings.py
│   │   │   ├── urls.py
│   │   │   └── myapp/...
│   │   └── fastapi_minimal/               ← Synthetic FastAPI project
│   │       ├── main.py
│   │       └── app/...
│   │
│   └── test_integration_fixtures.py       ← Tests using fixtures (NEW)
│
├── RUN_INTEGRATION_TESTS.py               ← Master orchestrator
└── INTEGRATION_TEST_REPORT.md             ← Auto-generated report
```

### Test File Purposes

| File | Purpose | Scope | Framework |
|------|---------|-------|-----------|
| `test_phase_0_integration.py` | Validate harness foundation (planning + verification) | Planning engine scoring on Django/FastAPI/Spring/Go | Direct imports |
| `test_gap_1_multifile.py` | Validate multi-file generation + auto-wiring | File formatting, auto-wiring logic | Direct imports |
| `test_all_gaps.py` | Validate Gaps 2-8 (migrations, config, CLI, events, etc.) | Comprehensive feature coverage | Direct imports |
| `test_phase_1_3_features.py` | Validate Phase 1-3 features (bus detection, catalog, observability, preview, TDD, review, etc.) | Advanced features | Direct imports |
| `test_robustness.py` | Negative tests, edge cases, error handling | Robustness under stress | Direct imports |
| `test_supporting_modules.py` | Health-check, template library, interactive tour, multi-sidecar | Discovery + helper modules | Direct imports |
| `test_integration_fixtures.py` | End-to-end tests using synthetic Django/FastAPI projects | Real-world-like scenarios | pytest + fixtures |
| `performance_test_harness.py` | Timing validation, performance budgets | Wall-clock execution time per script | Direct imports + time measurement |
| `benchmark_suite.py` | Named budget validation against constants | Budget adherence checking | Direct imports |

---

## Performance Budgets

The plugin has strict performance budgets to ensure fast user experience. All scripts must complete within their allocated time window.

### Budget Definitions

Budgets are defined in `scripts/lib/base_script.py` and must be met on typical hardware:

| Script/Operation | Budget (ms) | Why |
|------------------|------------|-----|
| `analyze_codebase` | 2000 | Framework detection + file walking can be slow on large codebases |
| `plan_decisions` | 250 | Pure scoring algorithm, very fast |
| `format_multifile_output` | 100 | String formatting, nearly instant |
| `code_review_automation` | 500 | Linting + security checks, moderate |
| `consistency_checker` | 2500 | Full codebase scan for patterns |
| `architecture_design` | 100 | Template-based, instant |
| `generate_migrations` | 300 | SQL generation, fast |
| `verify_generated` | 200 | Syntax validation via parsing |
| `autowire_into_project` | 1000 | File I/O + regex, moderate |
| `detect_message_bus` | 500 | Pattern matching, fast |

### How Budgets Are Checked

```python
# In any script using the harness:
from lib.base_script import timed_run, check_budget

with timed_run("analyze_codebase") as timer:
    # ... do work ...
    pass

check_budget("analyze_codebase", timer.elapsed_ms, logger)
# Warns if exceeded budget
```

### Performance Regression Testing

Run the performance harness to catch regressions:

```bash
python skills/one-shot-generator/scripts/performance_test_harness.py
# Outputs: performance_test_results.json
#         test_results/performance.log

# Or via CI
python skills/one-shot-generator/scripts/benchmark_suite.py
```

---

## Running Tests Locally

### Prerequisites

```bash
# Python 3.10+
python --version

# pytest (for fixture-based tests)
pip install pytest pytest-django

# Django/FastAPI (for fixture projects)
pip install django fastapi
```

### Unit Tests (Fast, <5 seconds)

```bash
cd skills/one-shot-generator/scripts

# Run all unit tests
python -m pytest test_*.py -v

# Run a specific test
python -m pytest test_phase_0_integration.py::TestPhase0PlanningEngine::test_planning_engine_django -v

# Run with coverage
python -m pytest test_*.py --cov --cov-report=html
```

### Fixture-Based Integration Tests (Slower, ~10-20 seconds)

```bash
# From repo root
python -m pytest tests/test_integration_fixtures.py -v

# Run a specific test class
python -m pytest tests/test_integration_fixtures.py::TestIntegrationDjangoFixture -v

# Run a specific test
python -m pytest tests/test_integration_fixtures.py::TestAutoWireIntegration::test_autowire_django_dry_run -v
```

### Performance Tests (Slow, ~30-60 seconds)

```bash
cd skills/one-shot-generator/scripts

# Run performance validation
python performance_test_harness.py

# Run budget checks
python benchmark_suite.py

# Output includes:
# - test_results/performance.log
# - performance_test_results.json
```

### Full Integration Suite (Comprehensive, ~2-5 minutes)

```bash
# From repo root
python RUN_INTEGRATION_TESTS.py

# Generates:
# - INTEGRATION_TEST_REPORT.md
# - All individual test outputs
```

---

## CI/CD Pipeline

The plugin uses GitHub Actions for automated testing. See `.github/workflows/ci-cd.yml`.

### Jobs

| Job | Trigger | Key Steps | Timeout |
|-----|---------|-----------|---------|
| `quality-checks` | Every push | pylint, black, pytest unit tests, coverage | 15m |
| `performance-tests` | Every push | `performance_test_harness.py`, budget checks | 20m |
| `real-project-tests` | Nightly + release branches | Real-project validation | 30m |
| `security-scan` | Every push | bandit, secret scanning | 10m |
| `build` | Version tags (v*) | Package + verify metadata | 10m |
| `release` | Version tags | Create GitHub Release + assets | 10m |
| `marketplace-submit` | Manual trigger | Submit to VSCode marketplace | 20m |

### Running CI Jobs Locally

```bash
# Simulate the quality-checks job
python -m pytest skills/one-shot-generator/scripts/test_*.py -v --tb=short
python skills/one-shot-generator/scripts/performance_test_harness.py

# Simulate the real-project-tests job
python RUN_INTEGRATION_TESTS.py

# Simulate security scan
bandit -r skills/one-shot-generator/scripts --skip B101,B601
```

---

## Writing New Tests

### Adding a Unit Test

```python
# In tests/test_integration_fixtures.py or new test file

def test_my_feature():
    """Test description."""
    # Arrange
    test_input = {...}
    
    # Act
    result = my_function(test_input)
    
    # Assert
    assert result['success'] is True
    assert len(result['items']) > 0
```

### Adding a Fixture-Based Test

```python
# In tests/test_integration_fixtures.py

class TestMyFeature:
    """Test my feature on synthetic projects."""

    def setup_method(self):
        """Setup before each test."""
        self.project_root = FIXTURES_DIR / 'django_minimal'
        assert self.project_root.exists()

    def test_my_feature_on_django(self):
        """Test on Django fixture."""
        # Use self.project_root as test project
        analyzer = CodebaseAnalyzer(str(self.project_root))
        result = analyzer.analyze_full_context()
        
        assert result['framework'] == 'django'
```

### Performance Test Template

```python
# In benchmark_suite.py or performance_test_harness.py

from lib.base_script import timed_run, check_budget

def test_my_operation_performance():
    """Validate operation completes within budget."""
    with timed_run("my_operation") as timer:
        do_work()
    
    is_fast_enough = check_budget("my_operation", timer.elapsed_ms)
    assert is_fast_enough, f"Exceeded budget: {timer.elapsed_ms}ms"
```

### Running New Test

```bash
# Immediately
python -m pytest tests/test_integration_fixtures.py::TestMyFeature::test_my_feature_on_django -v

# Via orchestrator (next full run)
python RUN_INTEGRATION_TESTS.py
```

---

## Debugging Failed Tests

### Enable Logging

```bash
# Run test with DEBUG logging
OSP_LOG_LEVEL=DEBUG python -m pytest tests/test_integration_fixtures.py::TestIntegrationDjangoFixture -v -s

# The `-s` flag shows print statements and logging
```

### Inspect Fixture State

```python
# In a test, print fixture state
import json

def test_something(self):
    """Debug fixture state."""
    project_path = self.django_fixture
    
    # Print directory tree
    import os
    for root, dirs, files in os.walk(project_path):
        level = root.replace(str(project_path), '').count(os.sep)
        indent = ' ' * 2 * level
        print(f'{indent}{os.path.basename(root)}/')
        sub_indent = ' ' * 2 * (level + 1)
        for file in files:
            print(f'{sub_indent}{file}')
```

### Check Temp Directories After Test Failure

```python
# In test_autowire_integration.py, don't cleanup to inspect state:

def teardown_method(self):
    """Cleanup temporary directories."""
    # COMMENT OUT to inspect:
    # if self.temp_django.exists():
    #     shutil.rmtree(self.temp_django)
    print(f"Temp Django at: {self.temp_django}")
    print(f"Temp FastAPI at: {self.temp_fastapi}")
```

---

## Common Issues

### Issue: Tests fail with "Path not found" for fixtures

**Solution:** Ensure fixtures exist at correct paths:
```bash
ls -la tests/fixtures/django_minimal/
# Should show: manage.py, settings.py, urls.py, myapp/, requirements.txt
```

### Issue: Pytest not found

**Solution:** Install pytest:
```bash
pip install pytest pytest-django
```

### Issue: Performance test times out

**Solution:** Check system load, or increase timeout in CI config. Also check that `performance_test_harness.py` creates `test_results/` directory:
```python
os.makedirs('test_results', exist_ok=True)
```

### Issue: "No module named 'lib.base_script'"

**Solution:** Ensure you're running from correct directory and the lib module is in the scripts path:
```bash
cd skills/one-shot-generator/scripts
python -m pytest test_*.py -v
```

---

## Contributing Tests

When adding features, please add corresponding tests:

1. **Unit test** — Test your function directly
2. **Integration test** — Test interaction with other components
3. **Fixture test** — Test on synthetic projects (if applicable)
4. **Performance test** — Add budget to `base_script.py` and validate

Include tests in your PR. Tests must pass before merge:

```bash
# Before opening PR, run:
python RUN_INTEGRATION_TESTS.py
# Ensure all tests pass
```

---

## References

- [pytest documentation](https://docs.pytest.org/)
- [pytest-django](https://pytest-django.readthedocs.io/)
- [Performance Budgets](./scripts/lib/base_script.py)
- [CI/CD Configuration](.github/workflows/ci-cd.yml)
- [IMPLEMENTATION_STATUS_MAY_6_2026.md](IMPLEMENTATION_STATUS_MAY_6_2026.md)
