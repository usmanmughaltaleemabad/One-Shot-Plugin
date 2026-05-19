---
type: reference
last_verified: 2026-05-17
owner: claude
---

# Plugin Validation Report — May 17, 2026

End-to-end real-use validation of the `one-shot-prompting` plugin against a greenfield FastAPI test project. Goal: catch bugs that the integration test suite misses by actually running the generator pipelines.

**Result: 8 real bugs found, 8 fixed; 4 quality issues documented for future work.**

---

## Test Setup

- **Test project**: `c:/Projects/plugin-validation/fastapi-shop/`
  - FastAPI 0.104.1 + SQLAlchemy 2.0 + Pydantic 2.5 + pytest + structlog
  - `requirements.txt`, `main.py`, `models.py`, `tests/test_health.py`
- **Generated output**: `c:/Projects/plugin-validation/fastapi-shop-generated/`
- **Python**: 3.14.3 on Windows 11 (cp1252 default codec)

---

## Bugs Found and Fixed

### 🔴 BUG 1 — Windows Unicode crash (BLOCKER on Windows)

**File**: `skills/one-shot-generator/scripts/phase2_runner.py:136` (and ~30 other scripts)
**Symptom**:
```
UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f680'
  in position 0: character maps to <undefined>
```
**Cause**: `print("🚀 Phase 2: ...")` uses emoji; Python on Windows defaults stdout to cp1252.
**Scope**: 31 scripts across the plugin print emojis.
**Fix**: Added stdout/stderr UTF-8 reconfigure at the top of entry-point runners (`phase2_runner.py`, `phase3_runner.py`).

```python
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass
```

Verified: phase2 + phase3 now run cleanly on Windows without `PYTHONIOENCODING=utf-8` workaround.

---

### 🔴 BUG 2 — Phase 2 subpackages missing `__init__.py` (BLOCKER)

**Files**: `skills/one-shot-generator/scripts/phase2_rest_api/{core,generators,handlers,validators}/`
**Symptom**: `ModuleNotFoundError: No module named 'core'`
**Cause**: Subdirectories had no `__init__.py`, so relative imports from `orchestrator_phase2.py` failed.
**Fix**: Created `__init__.py` in all 4 subpackages.

---

### 🔴 BUG 3 — Phase 2 orchestrator uses absolute imports inside package (BLOCKER)

**File**: `skills/one-shot-generator/scripts/phase2_rest_api/orchestrator_phase2.py:18-26, 143`
**Symptom**: `ModuleNotFoundError: No module named 'core'` even after BUG 2 fix.
**Cause**: `from core.crud_generator import ...` is an absolute import that requires `phase2_rest_api/` itself on `sys.path`. The package was imported as `phase2_rest_api`, so absolute imports resolve from `scripts/` parent, not from the package.
**Fix**: Changed to relative imports (`from .core.crud_generator import ...`). Same fix applied to the lazy import on line 143.

---

### 🔴 BUG 4 — Phase 2 pagination passes `dict` where `PaginationConfig` expected

**File**: `skills/one-shot-generator/scripts/phase2_rest_api/orchestrator_phase2.py:120-125`
**Symptom**: `'dict' object has no attribute 'default_limit'`
**Cause**: Constructor `PaginationGenerator(framework, config)` expects a `PaginationConfig` dataclass; orchestrator passed a plain `dict`.
**Fix**: Wrap dict in `PaginationConfig(...)` call. Imported `PaginationConfig` from handlers.

---

### 🔴 BUG 5 — Phase 4 DDD generator NameError on `self`

**File**: `skills/one-shot-generator/scripts/phase4_ddd_aggregate_design.py:61, 214`
**Symptom**: `NameError: name 'self' is not defined`
**Cause**: Generator uses outer f-string to compose Python code. Inside the template, `f"{vo}({self._value!r})"` evaluates `{self._value!r}` at code-generation time instead of leaving it as a literal in the output.
**Fix**: Double-brace the inner expression: `f"{vo}({{self._value!r}})"`. Two occurrences corrected.

---

### 🟡 BUG 6 — Phase 2 CRUD docstrings escape template placeholders

**File**: `skills/one-shot-generator/scripts/phase2_rest_api/core/crud_generator.py` (17 lines)
**Symptom**: Generated code contained literal `"""List all {plural} ..."""` and `"""Create new {resource}"""`.
**Cause**: Docstrings used `{{plural}}` / `{{resource}}` (escaped to literal braces) when they meant `{plural}` / `{resource}` (substituted).
**Fix**: Replaced all `{{plural}}` → `{plural}` and `{{resource}}` → `{resource}` in docstrings/test strings.

Verified: docstring in generated router.py is now `"""List all products with pagination and filtering"""`.

---

### 🟡 BUG 7 — Phase 3 SyntaxWarnings from JS template literals

**Files**: 5 files in `skills/one-shot-generator/scripts/phase3_batch_jobs/core/`
- `retry_handler.py`, `dlq_handler.py`, `job_router.py`, `worker_generator.py`, `batch_logging.py`

**Symptom**:
```
SyntaxWarning: "\`" is an invalid escape sequence. Such sequences will not work in the future.
```
**Cause**: JS template literals (`` `${var}` ``) inside Python triple-quoted strings were over-escaped (`` \` `` and ``\$``). Since the surrounding Python string isn't a raw or escaped context, the backslashes are invalid.
**Fix**: Removed unnecessary backslashes (20 occurrences across 5 files).

---

### 🟡 BUG 8 — Phase 3 SKILL.md / runner CLI mismatch

**File**: `skills/one-shot-generator/SKILL.md:195` vs `phase3_batch_jobs/phase3_runner.py`
**Symptom**: SKILL.md calls `phase3_runner.py "$ARGUMENTS"` (single string), but `phase3_runner.py` uses argparse with required `--framework`/`--language`/`--job-name` flags → crashes with "unrecognized arguments".
**Fix**: Added `_normalize_freeform_args()` to `phase3_runner.py` that converts `"$ARGUMENTS"`-style input ("add email batch processor @/project") into explicit argparse flags by:
- extracting `@path` argument to detect framework (django/fastapi/go/spring),
- using first non-keyword word as `--job-name`,
- defaulting `--format json`.

Both invocation styles now work: free-form (`"add email job @/project"`) and explicit (`--framework fastapi ...`).

---

### 🟡 BUG 9 — Documentation contradiction on Phase 4-5 status

**File**: `skills/CLAUDE.md` (3 places)
**Symptom**: This file said "Phase 4-5 have stub scripts only", contradicting `docs/phase-status.md` and `IMPLEMENTATION_STATUS.md` which say all 177 modules shipped in v2.0.0.
**Fix**: Updated three sections of `skills/CLAUDE.md` to reflect actual state: 49 phase 4 modules (DDD/CQRS/compliance), 59 phase 5 modules (microservices/GraphQL/ML).

---

## Quality Issues NOT Fixed (Documented for Future)

### ⚠️ ISSUE A — Generated tests have logic bugs

`test_product_api.py` is generated alongside the router but contains assertions that don't match the generated router:

- `test_pagination` asserts `"next" in response.json()`, but the generated list endpoint returns a plain `List[ProductSchema]` (no pagination envelope).
- `test_unauthorized` asserts status 401, but the generated router has no auth middleware so requests succeed.

**Why not fixed now**: requires aligning the test generator with the router generator's actual output shape; this is a larger refactor in `phase2_rest_api/generators/test_generator.py` and beyond the validation scope.

### ⚠️ ISSUE B — `preview_mode.py` ignores task input

**File**: `skills/one-shot-generator/scripts/preview_mode.py`
Invoking with `"add product CRUD @/project"` produces hardcoded output describing a "Rate limiter" (180 LOC, sliding window log). The script doesn't read its argument.

### ⚠️ ISSUE C — `analyze_codebase.py` won't detect language without manifest

Plugin's own root directory has 344 `.py` files but no `requirements.txt` / `pyproject.toml`, so the analyzer reports `Language: Unknown`. The detection logic is manifest-only. Adding a `.py` count fallback would catch source-only repos.

### ⚠️ ISSUE D — Pre-existing integration test failures (2)

`tests/test_integration_fixtures.py`:
- `test_analyze_django_codebase`: asserts `orm == 'django_orm'` but code returns `'Django ORM'` (capitalization mismatch — test bug).
- `test_django_autodiscovery`: expects `structure.get('app_root')` to be non-None, but the Django fixture lacks `src`/`app`/`apps`/`lib` directories.

Not introduced by this validation; left for a dedicated test-cleanup pass.

### ⚠️ ISSUE E — Inconsistent CLI conventions across modules

Phase-2 and (now) phase-3 runners accept `"$ARGUMENTS"` free-form. The 100+ standalone phase-4/phase-5 scripts each use their own argparse interface (e.g. `phase4_ddd_aggregate_design.py --aggregate Order --entities ... --values ...`). The SKILL.md only documents free-form invocation, so a user calling phase-4 modules through the skill harness will hit unrecognized-args errors unless they invoke the scripts directly. A future task: either unify CLIs or generate per-module wrappers.

---

## What Worked (Positive Findings)

- ✅ `analyze_codebase.py` — correctly detects FastAPI 0.104.1, SQLAlchemy, Pydantic, pytest, structlog from `requirements.txt` + source.
- ✅ `analyze_and_plan.py` — generates the 6-decision plan with 8.6/10 confidence; all decisions match the project (async, SQLAlchemy, pytest, exceptions, structlog, Pydantic v2).
- ✅ `phase2_runner.py` — after fixes, generates 6 files (router, pagination, tests, openapi.json, swagger-ui.html, README). Generated router.py passes `python -m py_compile`.
- ✅ `phase3_runner.py` — generates 35 files for a Celery email job (jobs, scheduler, monitoring, retry, DLQ, worker, logging, metrics, etc.).
- ✅ `phase4_circuit_breaker.py` — produces complete circuit-breaker code with state machine.
- ✅ `phase4_ddd_aggregate_design.py` (after fix) — generates value-object, entity, aggregate-root, and repository classes for any aggregate.
- ✅ `phase5_api_gateway.py` — generates microservices gateway pattern.
- ✅ Supporting skills (`plan_writer`, `tdd_cycle_enforcer`, `completion_gate`, `systematic_debug`) — all run successfully when called with their explicit CLI flags.
- ✅ Smoke test (`bash .claude/scripts/smoke-test.sh`) — 8/8 pass.
- ✅ Integration test suite — 9/11 categories pass (2 pre-existing failures, see Issue D).
- ✅ Performance budgets — all 7 modules within budget; slowest is `detect_message_bus` at 1.7s (budget 2s).

---

## Files Modified by This Validation

| File | Change |
|------|--------|
| `skills/one-shot-generator/scripts/phase2_runner.py` | Added Windows UTF-8 stdout/stderr reconfigure |
| `skills/one-shot-generator/scripts/phase2_rest_api/core/__init__.py` | Created (subpackage marker) |
| `skills/one-shot-generator/scripts/phase2_rest_api/generators/__init__.py` | Created |
| `skills/one-shot-generator/scripts/phase2_rest_api/handlers/__init__.py` | Created |
| `skills/one-shot-generator/scripts/phase2_rest_api/validators/__init__.py` | Created |
| `skills/one-shot-generator/scripts/phase2_rest_api/orchestrator_phase2.py` | Relative imports; `PaginationConfig` wrapper |
| `skills/one-shot-generator/scripts/phase2_rest_api/core/crud_generator.py` | 17 docstring/test template substitutions |
| `skills/one-shot-generator/scripts/phase3_batch_jobs/phase3_runner.py` | Windows UTF-8 + free-form arg normalizer |
| `skills/one-shot-generator/scripts/phase3_batch_jobs/core/retry_handler.py` | Removed invalid backtick escapes |
| `skills/one-shot-generator/scripts/phase3_batch_jobs/core/dlq_handler.py` | Removed invalid backtick escapes |
| `skills/one-shot-generator/scripts/phase3_batch_jobs/core/job_router.py` | Removed invalid backtick escapes |
| `skills/one-shot-generator/scripts/phase3_batch_jobs/core/worker_generator.py` | Removed invalid backtick escapes |
| `skills/one-shot-generator/scripts/phase3_batch_jobs/core/batch_logging.py` | Removed invalid backtick escapes |
| `skills/one-shot-generator/scripts/phase4_ddd_aggregate_design.py` | Fixed two f-string template `self` references |
| `skills/CLAUDE.md` | Corrected Phase 4-5 status from "stub" to shipped |

15 source files modified, 4 new `__init__.py` created. No documentation files reorganized.

---

## Recommended Next Steps

1. **Cross-platform CI** — add Windows runner to GitHub Actions; the 31 emoji prints elsewhere in the code will continue to be a hazard until the UTF-8 reconfigure is centralised (a single `lib/base_script.py` helper).
2. **Test generator alignment** — fix the generated `test_*.py` to match the actual router shape (Issue A); this is the single biggest quality gap discovered.
3. **`preview_mode.py` rewrite** — actually use its argument; right now it's a hardcoded demo (Issue B).
4. **`analyze_codebase.py` source fallback** — detect Python via `.py` count when no manifest exists (Issue C).
5. **Phase 4-5 CLI unification** — wrap the 100+ standalone scripts behind a single runner with `$ARGUMENTS` parsing (Issue E).
6. **Fix `test_integration_fixtures.py`** — the two failing tests are trivial (capitalization + missing fixture dir) (Issue D).

---

**Validation methodology**: build a real FastAPI project → run each runner end-to-end → inspect generated output → re-run after each fix → confirm regression-free.
