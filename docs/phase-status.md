---
type: reference
last_verified: 2026-05-16
owner: claude
---

# Implementation Status — Real vs Stub Modules

**Last audit: 2026-05-16 — confirmed with CLAUDE.md section**

---

## Executive Summary

| Phase | Status | Modules | LOC | Release | Runnable? |
|-------|--------|---------|-----|---------|-----------|
| **0** | ✅ Shipped | 4 | ~475 | v0.6.1 | YES |
| **1** | ✅ Shipped | 8 | ~2,050 | v0.7.0 | YES |
| **2** | ✅ Shipped | 44 | ~8,900 | v2.0.0 | YES |
| **3** | ✅ Shipped | 13 | ~3,586 | v2.0.0 | YES |
| **4** | ❌ Stub | 60 | 0 | v3.0.0 (planned) | NO |
| **5** | ❌ Stub | 50+ | 0 | v4.0.0 (planned) | NO |
| **TOTAL** | **39% done** | **69/177** | **~15k** | **v2.0.0** | — |

---

## What "Stub" Means

Script files exist in `skills/one-shot-generator/scripts/phase4_*.py` and `phase5_*.py`,
but:
- ❌ No actual implementation logic (empty or placeholder)
- ❌ Not called by any SKILL.md
- ❌ Not tested in RUN_INTEGRATION_TESTS.py
- ❌ Will error if invoked directly

**Rule for Claude:** Do not invoke Phase 4-5 generators. These files are aspirational
planning artifacts, not working code. If you need to work on Phase 4-5, open a bead
first (see `.beads/status.jsonl`).

---

## Phase 0: Silent Planning Engine ✅ (v0.6.1)

Foundation: silent planning, verification harness, slash commands.

| Module | Purpose | Status |
|--------|---------|--------|
| plan_decisions.py | Generate options before code | ✅ Working |
| verify_generated.py | 4-step verification harness | ✅ Working |
| Slash command overrides | 7 commands, 25+ flags | ✅ Working |
| Zero questions UX | All prompts have fallbacks | ✅ Working |

**How to test:**
```bash
/one-shot-prompting:write-plan "add user auth" @/tmp/test
/one-shot-prompting:verify-before-complete "run tests" @/tmp/test
```

---

## Phase 1: Multi-File & Integration ✅ (v0.7.0)

Output formatting, framework detection, auto-wiring.

| Module | Purpose | Status |
|--------|---------|--------|
| format_multifile_output.py | Organize code across files | ✅ Working |
| autowire_into_project.py | Auto-patch Django/FastAPI/Spring/Go | ✅ Working |
| generate_migrations.py | Django/Alembic/Flyway/Go migrations | ✅ Working |
| framework_config.py | DI, config loading | ✅ Working |
| multi_handler_orchestration.py | Coordinate multiple endpoints | ✅ Working |
| openapi_generation.py | Auto-generate OpenAPI spec | ✅ Working |
| Handler detection | Language/framework specific | ✅ Working |

**How to test:**
```bash
/one-shot-prompting:one-shot-generator "add user auth endpoint" @/tmp/django-project
# Output: models.py, views.py, migrations, tests, README
```

---

## Phase 2: REST API Generation ✅ (v2.0.0)

CRUD, auth, webhooks, validation, tests.

**44 modules.** Covers:
- CRUD operations (create, read, update, delete, list)
- Authentication (JWT, OAuth, basic)
- Pagination (offset, cursor, keyset)
- Versioning (URL, header)
- Webhooks (delivery, retry, signature)
- Request validation (fields, types, constraints)
- Error handling (400s, 500s, retry logic)
- Testing (unit, integration, fixtures)

**How to test:**
```bash
python RUN_INTEGRATION_TESTS.py
# Runs test_contexts/django_minimal, fastapi_minimal, go_trading_bot, etc.
```

---

## Phase 3: Batch Job Systems ✅ (v2.0.0)

Queues, retries, monitoring, observability.

**13 modules.** Covers:
- Job queues (Redis, RabbitMQ, SQS)
- Retry strategies (exponential, jitter, circuit breaker)
- Dead-letter queues (DLQ handling)
- Monitoring (Prometheus metrics)
- Observability (structured logging, tracing)
- Health checks

**How to test:**
```bash
/one-shot-prompting:one-shot-generator "add batch processor for email notifications" @/tmp/fastapi-project
```

---

## Phase 4: Production Hardening ❌ STUB (v3.0.0 planned)

NOT IMPLEMENTED. Files exist but no logic.

| Module | Purpose | Status |
|--------|---------|--------|
| ddd_aggregate_design.py | Domain-driven design | ❌ Stub |
| cqrs_pattern.py | CQRS architecture | ❌ Stub |
| event_sourcing.py | Event-driven persistence | ❌ Stub |
| tdd_cycle.py | Test-driven development | ❌ Stub |
| cost_optimization.py | Infrastructure cost analysis | ❌ Stub |
| chaos_engineering.py | Resilience testing | ❌ Stub |
| compliance_soc2.py | SOC2 compliance checklist | ❌ Stub |
| compliance_hipaa.py | HIPAA compliance checklist | ❌ Stub |
| compliance_gdpr.py | GDPR compliance checklist | ❌ Stub |
| ... (60 modules total) | | ❌ Stub |

**Status:** PHASE_4_IMPLEMENTATION_PLAN.md does not exist. No code written.

**If you need Phase 4:** See `.beads/` → open a bead for Phase 4 planning.

---

## Phase 5: Advanced Patterns ❌ STUB (v4.0.0 planned)

NOT IMPLEMENTED. Files exist but no logic.

| Module | Purpose | Status |
|--------|---------|--------|
| microservices_decompose.py | Service boundary analysis | ❌ Stub |
| real_time_sync.py | WebSocket/SSE patterns | ❌ Stub |
| graphql_schema.py | GraphQL from REST | ❌ Stub |
| ml_pipeline.py | ML serving patterns | ❌ Stub |
| legacy_strangler.py | Strangler fig pattern | ❌ Stub |
| ... (50+ modules total) | | ❌ Stub |

**Status:** PHASE_5_IMPLEMENTATION_PLAN.md does not exist. No code written.

---

## How the Phases Relate

```
Phase 0 (Planning, Verification)
  ↓
Phase 1 (Multi-file, Auto-wire, Migrations)
  ↓
Phase 2 (REST APIs: CRUD, auth, webhooks, tests)
  ↓
Phase 3 (Batch jobs: Queues, retry, monitoring)
  ↓
Phase 4 (Production hardening: DDD, CQRS, compliance) ← NOT STARTED
  ↓
Phase 5 (Advanced patterns: Microservices, real-time) ← NOT STARTED
```

---

## Repository of Real Scripts

All Phase 0-3 scripts are in `skills/one-shot-generator/scripts/`:

| Phase | Directory | File count | Status |
|-------|-----------|-----------|--------|
| 0 | `phase0_*` | ~4 | ✅ Real |
| 1 | `phase1_*` | ~8 | ✅ Real |
| 2 | `phase2_rest_api/` | ~44 | ✅ Real |
| 3 | `phase3_batch_jobs/` | ~13 | ✅ Real |
| 4 | `phase4_*.py` | ~60 | ❌ Stubs (empty or placeholder) |
| 5 | `phase5_*.py` | ~50+ | ❌ Stubs (empty or placeholder) |

Total in skills/: ~170+ files

---

## Reality Check Rule

**Before invoking any Phase 4-5 script:**

1. Check this doc's status table
2. If ❌ Stub, do NOT call it
3. If you need Phase 4-5 features:
   - Open a bead in `.beads/status.jsonl`
   - Update `.claude/agents/phase-planner.md`
   - Plan out the implementation
   - Implement it, then mark bead as closed
