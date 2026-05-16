---
type: runbook
last_verified: 2026-05-16
owner: claude
---

# Testing Guide

How to test the plugin locally before publishing.

---

## Quick Start

```bash
# 1. Install plugin locally
claude --plugin-dir /path/to/one-shot-prompting

# 2. Run smoke tests (syntax, frontmatter, versions)
bash .claude/scripts/smoke-test.sh

# 3. Run full integration tests
python RUN_INTEGRATION_TESTS.py

# 4. Test a skill manually
/one-shot-prompting:one-shot-generator "add user auth" @/tmp/test-project
```

---

## Test Contexts

Test contexts are minimal codebases used to test the analyzer and generators.
They live in `test_contexts/` and are `.txt` files (not actual repos).

| Context | Language | Framework | Size |
|---------|----------|-----------|------|
| `django_minimal.txt` | Python | Django | ~30 files |
| `fastapi_minimal.txt` | Python | FastAPI | ~20 files |
| `go_trading_bot.txt` | Go | stdlib | ~10 files |
| `nestjs_realtime_api.txt` | TypeScript | NestJS | ~15 files |
| `spring_payment_service.txt` | Java | Spring Boot | ~25 files |
| `sparse.txt` | Generic | None | ~5 files |

Each `.txt` file is a concatenated manifest: `filename:content` separated by `---`.

**Why .txt instead of real repos?**
- No git dependencies
- Fast to load in memory
- Deterministic output (no random project differences)
- No side effects (don't touch real filesystems)

---

## Smoke Test (bash)

Validates syntax, frontmatter, and version consistency.

```bash
bash .claude/scripts/smoke-test.sh
```

What it checks:
- ✅ All .py files in `skills/*/scripts/` have valid Python syntax
- ✅ All SKILL.md files have YAML frontmatter
- ✅ plugin.json version matches CHANGELOG.md latest version
- ✅ CLAUDE.md has < 100 lines
- ✅ All required .md docs have `type:`, `last_verified:`, `owner:`

Exit codes:
- 0 = all checks pass
- 1 = any check fails (details printed)

---

## Integration Tests (Python)

Tests the analyzer and generators against all test_contexts.

```bash
python RUN_INTEGRATION_TESTS.py
```

What it does:
1. For each test_context:
   - Load the context as a fake codebase
   - Run analyze_codebase.py
   - Parse analyzer output
   - Generate code using one-shot-generator SKILL
   - Verify output syntax (if Python/Go/Java)
   - Check for required files (models, views, tests, etc.)

Output: Pass/fail per context + summary.

**Example output:**
```
Testing django_minimal.txt...
  - Detected: Django 3.2, DRF, pytest
  - Generated: models.py (104L), views.py (267L), tests.py (89L), migrations/ (3)
  - Status: ✅ PASS

Testing fastapi_minimal.txt...
  - Detected: FastAPI 0.68, pydantic, pytest
  - Generated: main.py (201L), models.py (156L), tests/ (2 files)
  - Status: ✅ PASS

...

Summary: 6/6 passed. Duration: 2.3s.
```

---

## Skill Testing (Manual)

Test individual skills with the CLI.

### Test one-shot-generator

```bash
# Basic request
/one-shot-prompting:one-shot-generator "add user authentication with JWT" @/tmp/django-project

# With verbose output
/one-shot-prompting:one-shot-generator --verbose "add REST API for orders" @/tmp/fastapi-project

# Dry-run (plan without generating)
/one-shot-prompting:one-shot-generator --dry-run "add batch email processor" @/tmp/project

# Test with a test_context
/one-shot-prompting:one-shot-generator "add caching layer" @test_contexts/django_minimal.txt
```

### Test write-plan

```bash
/one-shot-prompting:write-plan "add user auth" @/tmp/project
# Outputs: step-by-step plan, no code generation
```

### Test tdd-cycle

```bash
/one-shot-prompting:tdd-cycle "add password reset endpoint" @/tmp/project
# Outputs: test template, then implementation, then verification
```

---

## Testing Checklist

Before committing:

- [ ] `bash .claude/scripts/smoke-test.sh` passes
- [ ] `python RUN_INTEGRATION_TESTS.py` passes all 6 contexts
- [ ] Manually test your changed skill with at least 1 test context
- [ ] If you changed SKILL.md, verify: syntax highlighting works, injected content is < 500 tokens
- [ ] If you added a script, verify: `python script.py "test @test_contexts/django_minimal.txt"` works
- [ ] If you changed Phase 2-3 logic, re-run full integration tests
- [ ] CHANGELOG.md updated with your changes
- [ ] plugin.json version bumped to match CHANGELOG

---

## Debugging Failed Tests

**If smoke-test.sh fails:**
```bash
# Run individual checks
python -m py_compile skills/one-shot-generator/scripts/analyze_codebase.py
# If this errors, fix the Python syntax

# Check SKILL.md frontmatter
head -5 skills/one-shot-generator/SKILL.md
# Should show: ---\nname: ...\ndescription: ...\ntrigger: ...

# Check versions match
grep "^## " CHANGELOG.md | head -1
cat .claude-plugin/plugin.json | grep version
# These should match
```

**If integration-test.py fails:**
```bash
# Run with verbose flag
python RUN_INTEGRATION_TESTS.py --verbose

# Test one context in isolation
python -c "from RUN_INTEGRATION_TESTS import test_context; test_context('test_contexts/django_minimal.txt')"

# Check if test context is readable
head -20 test_contexts/django_minimal.txt
```

**If a skill test fails:**
```bash
# Test the underlying script directly
python skills/one-shot-generator/scripts/analyze_codebase.py "test request @test_contexts/django_minimal.txt"

# If this errors, the script itself is broken
# Look at stderr and fix the Python code
```

---

## Performance Benchmarks

Expected timing on a modern laptop:

| Test | Expected time |
|------|---|
| smoke-test.sh | < 5s |
| analyze_codebase.py (one context) | < 2s |
| Full integration test (6 contexts) | < 30s |
| Manual skill invocation | 5-20s (depends on user request) |

If tests are significantly slower, check:
- Disk I/O (SSDs are 10x faster than HDDs)
- Python version (3.10+ recommended)
- Test context size (sparse.txt should be < 1s, django_minimal should be < 5s)

---

## CI/CD Integration (Future)

For marketplace CI:

```yaml
# .github/workflows/test.yml
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - run: bash .claude/scripts/smoke-test.sh
      - run: python RUN_INTEGRATION_TESTS.py
```

(Already in `.github/workflows/ci-cd.yml` — verify it's up-to-date.)
