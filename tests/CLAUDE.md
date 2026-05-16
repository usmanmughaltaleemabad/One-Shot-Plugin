---
type: router
last_verified: 2026-05-16
owner: claude
---

# Tests Directory

Fixtures and integration test suite.

---

## Quick Reference

| File/Dir | Purpose | Status |
|----------|---------|--------|
| `test_integration_fixtures.py` | Load and parse test_contexts/ | ✅ Active |
| `test_superpowers_skills.py` | Test each skill with fixtures | ✅ Active |
| `fixtures/` | Minimal test projects | ✅ 6 projects |

---

## Test Contexts (Fixtures)

Minimal codebases used to test the analyzer and generators.

Live in `../test_contexts/*.txt` (shared, not in this dir).

| Context | Framework | Size | Use case |
|---------|-----------|------|----------|
| django_minimal.txt | Django + DRF | ~30 files | Web API with ORM |
| fastapi_minimal.txt | FastAPI + pydantic | ~20 files | Async API |
| go_trading_bot.txt | Go stdlib | ~10 files | Trading system |
| nestjs_realtime_api.txt | NestJS | ~15 files | Real-time subscriptions |
| spring_payment_service.txt | Spring Boot | ~25 files | Payment processing |
| sparse.txt | Generic | ~5 files | Minimal project |

Each is a `.txt` file with format: `filename:content` separated by `---`.

---

## Running Tests

**Quick test:**
```bash
cd /path/to/one-shot-prompting
bash .claude/scripts/smoke-test.sh
```

**Full integration test:**
```bash
python RUN_INTEGRATION_TESTS.py
```

**Test a specific context:**
```bash
python -c "from test_integration_fixtures import load_context; ctx = load_context('test_contexts/django_minimal.txt'); print(ctx['files'])"
```

**Test a skill manually:**
```bash
/one-shot-prompting:one-shot-generator "add auth" @test_contexts/django_minimal.txt
```

---

## Fixtures Folder

Local test projects (Django, FastAPI minimal setups).

```
fixtures/
├── django_minimal/
│   ├── manage.py
│   ├── settings.py
│   └── models.py
├── fastapi_minimal/
│   ├── main.py
│   └── models.py
└── ...
```

Used for end-to-end testing (if running tests against real filesystems, not just test_contexts).

---

## Development

Adding a new test:

1. Create `test_myfeature.py` with:
   ```python
   import unittest
   from test_integration_fixtures import load_context

   class TestMyFeature(unittest.TestCase):
       def test_phase2_rest_api(self):
           ctx = load_context("test_contexts/django_minimal.txt")
           # Test logic
   ```

2. Run: `python -m unittest test_myfeature`

3. Add to `RUN_INTEGRATION_TESTS.py` if general-purpose test

---

**See also:**
- `../docs/testing.md` — how to test locally
- `../docs/phase-status.md` — what's implemented vs stub
- `../RUN_INTEGRATION_TESTS.py` — main test runner
