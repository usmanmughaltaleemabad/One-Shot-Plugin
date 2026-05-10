---
name: one-shot-prompting-commands
description: Override slash commands for one-shot-generator skill (Phase 0.3)
---

# One-Shot Prompting — Slash Command Overrides

## Overview

After the plugin generates code with PLAN DECISIONS, users can override any decision using slash commands. All commands are friction-free (no confirmation prompts).

---

## /osp:regenerate — Regenerate with different options

Re-run code generation with specific decision overrides.

### Syntax
```
/osp:regenerate [--async | --sync]
                 [--orm | --raw-sql]
                 [--pytest | --unittest | --jest | --junit5 | --go-test]
                 [--exceptions | --error-returns | --result-types]
                 [--structlog | --loguru | --winston | --zap | --log4j]
                 [--pydantic | --marshmallow | --zod | --joi]
                 [--minimal | --exhaustive]
```

### Flags

**Async/Sync:**
- `--async` — Force async def, async patterns
- `--sync` — Force synchronous, no async/await

**Persistence:**
- `--orm` — Use ORM (SQLAlchemy, Django ORM, JPA, etc.)
- `--raw-sql` — Use raw SQL queries

**Testing Framework:**
- `--pytest` — Python: pytest
- `--unittest` — Python: unittest
- `--jest` — JavaScript: Jest
- `--junit5` — Java: JUnit 5
- `--go-test` — Go: stdlib testing + testify

**Error Handling:**
- `--exceptions` — Use try/except or try/catch
- `--error-returns` — Use error return values (Go style)
- `--result-types` — Use Result<T, E> types (Rust style)

**Logging:**
- `--structlog` — Python: structlog
- `--loguru` — Python: loguru
- `--winston` — JavaScript: winston
- `--zap` — Go: zap
- `--log4j` — Java: Log4j 2

**Validation:**
- `--pydantic` — Python: Pydantic v2
- `--marshmallow` — Python: Marshmallow
- `--zod` — JavaScript: Zod
- `--joi` — JavaScript: Joi

**Code Style:**
- `--minimal` — Minimal code, no comments/docstrings
- `--exhaustive` — Complete code with full documentation

### Examples

```bash
# Switch from async to sync
/osp:regenerate --sync

# Use raw SQL instead of ORM
/osp:regenerate --raw-sql

# Switch to unittest instead of pytest
/osp:regenerate --unittest

# Multiple overrides
/osp:regenerate --sync --raw-sql --unittest

# Minimal code without comments
/osp:regenerate --minimal

# Full documentation
/osp:regenerate --exhaustive
```

---

## /osp:validate — Run verification without regenerating

Validates the generated code without re-running generation. Useful after making manual edits.

### Syntax
```
/osp:validate [filepath]
```

### Examples

```bash
# Validate the main generated file
/osp:validate models.py

# Validate all generated files
/osp:validate
```

### Output
```
✅ VERIFICATION PASSED — All validation checks passed
⚠️ AUTO-REPAIR APPLIED — Fixed N issues:
   - Issue 1: [description]
   - Issue 2: [description]
❌ FAILED — Manual fixes needed:
   - Issue 1: [description] → Fix: [recommendation]
```

---

## /osp:test — Generate + run tests

Generate code and immediately run the test suite.

### Syntax
```
/osp:test [test-framework]
```

### Examples

```bash
# Run tests using detected testing framework
/osp:test

# Force specific test framework
/osp:test --pytest
/osp:test --jest
/osp:test --junit5
```

### Output
Generates code, then outputs test results:
```
Generated: models.py, views.py, tests/test_feature.py

Running tests...
✅ 12 passed in 0.45s
```

---

## /osp:integrate — Copy files to project

Copy generated files to the project. Useful after testing/review.

### Syntax
```
/osp:integrate [--dry-run]
```

### Examples

```bash
# Show what would be copied (dry run)
/osp:integrate --dry-run

# Actually copy files to project
/osp:integrate
```

### Output
```
Copying generated files to project...
✅ models.py → src/models.py
✅ views.py → src/views.py
✅ tests/test_feature.py → tests/test_feature.py
✅ README.md → docs/FEATURE_README.md

Run:  python manage.py makemigrations && python manage.py migrate
```

---

## /osp:explain — Show all decisions and override options

Display the PLAN DECISIONS table again, plus all available override options for each decision.

### Syntax
```
/osp:explain [decision]
```

### Examples

```bash
# Show all decisions and all override options
/osp:explain

# Show details for a specific decision
/osp:explain async-sync
/osp:explain testing
/osp:explain logging
```

### Output
```
## PLAN DECISIONS

| Decision | Choice | Score | Reasoning |
|----------|--------|-------|-----------|
| Async/Sync | async | 8.5/10 | FastAPI + async patterns |
| ... |

## Override Options

**Async/Sync:**
  Current: async
  Override: /osp:regenerate --sync

**Persistence:**
  Current: SQLAlchemy ORM
  Override: /osp:regenerate --raw-sql

...

## Full Command Reference

/osp:regenerate [--async|--sync] [--orm|--raw-sql] [--pytest|--unittest|...]
/osp:validate [filepath]
/osp:test [test-framework]
/osp:integrate [--dry-run]
/osp:explain [decision]
/osp:status
/osp:reset
```

---

## /osp:status — Show progress/status

Display current generation state and next steps.

### Syntax
```
/osp:status
```

### Output
```
Generation Status:
  Phase: Planning ✅
  Phase: Generation ✅
  Phase: Verification ⏳ (running validation...)
  Phase: Integration ⏹ (pending)

Latest Generation:
  Time: 2026-05-06 10:35:20
  Framework: Django 4.2
  Files: 4 (models.py, views.py, serializers.py, tests.py)
  Status: ✅ VERIFICATION PASSED

Next Steps:
  1. Review generated code (see output above)
  2. /osp:test to run tests
  3. /osp:integrate to copy to project
```

---

## /osp:reset — Reset to defaults

Clear all overrides and regenerate with original planning decisions.

### Syntax
```
/osp:reset
```

### Output
```
Resetting to original decisions...
Regenerating with:
  Async/Sync: async (8.5/10)
  Persistence: SQLAlchemy ORM (8.3/10)
  Testing: pytest-asyncio (9.0/10)
  Error Handling: exceptions (8.3/10)
  Logging: structlog (9.0/10)
  Validation: Pydantic v2 (9.0/10)

Generated: models.py, router.py, tests.py
```

---

## Implementation Notes

### No Confirmation Prompts
All slash commands execute immediately. No "Are you sure?" dialogs.

### Stateless
Each command stands alone. `/osp:regenerate --async` doesn't require prior context.

### Composable
Commands can be chained:
```
/osp:regenerate --sync --raw-sql && /osp:validate && /osp:test
```

### Error Handling
- Invalid flags → show usage with available options
- File not found → show available files
- Validation errors → show all issues + remediation steps

---

## Design Philosophy

**One-shot with friction-free overrides:** Users should never ask "how do I change X?" The answer is always:
1. `See PLAN DECISIONS above`
2. `Use /osp:regenerate --flag to override`
3. No friction, no confirmation, no explanation needed

---

**Status:** Phase 0.3 Specification (v0.1)  
**Created:** May 6, 2026  
**Implementation:** In SKILL.md / .claude/commands/
