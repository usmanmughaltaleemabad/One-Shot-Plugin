---
type: reference
last_verified: 2026-05-16
owner: claude
---

# Scripts Index — All 170+ Scripts

Reference for all Python scripts in `skills/one-shot-generator/scripts/`.

---

## Overview

```
skills/one-shot-generator/scripts/
├── analyze_codebase.py              ✅ Real (Phase 1)
├── phase0_*.py (4 scripts)           ✅ Real (Phase 0)
├── phase1_*.py (8 scripts)           ✅ Real (Phase 1)
├── phase2_rest_api/ (44 scripts)    ✅ Real (Phase 2)
│   ├── crud_generators.py
│   ├── auth_generators.py
│   ├── pagination_generators.py
│   ├── webhook_generators.py
│   ├── validation_generators.py
│   ├── error_handling_generators.py
│   └── ... (38 more)
├── phase3_batch_jobs/ (13 scripts)  ✅ Real (Phase 3)
│   ├── queue_generators.py
│   ├── retry_generators.py
│   ├── monitoring_generators.py
│   └── ... (10 more)
├── phase4_*.py (60 scripts)          ❌ STUBS (not implemented)
└── phase5_*.py (50+ scripts)         ❌ STUBS (not implemented)
```

---

## Phase 0: Silent Planning ✅

All real. Foundational harness.

| Script | Purpose | Status |
|--------|---------|--------|
| plan_decisions.py | Generate plan options before code | ✅ Real |
| verify_generated.py | 4-step verification harness | ✅ Real |
| command_overrides.py | Slash command framework | ✅ Real |
| zero_questions_ux.py | Prompt fallbacks (no UX questions) | ✅ Real |

---

## Phase 1: Multi-File & Integration ✅

All real. Framework detection and output organization.

| Script | Purpose | Status |
|--------|---------|--------|
| analyze_codebase.py | Detect frameworks, models, views, tests | ✅ Real |
| format_multifile_output.py | Organize code across files (models, views, tests, etc.) | ✅ Real |
| autowire_into_project.py | Auto-patch Django/FastAPI/Spring/Go projects | ✅ Real |
| generate_migrations.py | Django/Alembic/Flyway/Go migrations | ✅ Real |
| framework_config.py | DI, config loading per framework | ✅ Real |
| multi_handler_orchestration.py | Coordinate multiple endpoints | ✅ Real |
| openapi_generation.py | Auto-generate OpenAPI spec | ✅ Real |
| handler_detection.py | Language/framework specific detection | ✅ Real |

---

## Phase 2: REST API Generation ✅

All real. 44 modules in `phase2_rest_api/`.

### CRUD Generators (4 scripts)

| Script | Purpose | Status |
|--------|---------|--------|
| crud_generators.py | Create, read, update, delete, list | ✅ Real |
| create_generators.py | CREATE (POST) endpoint | ✅ Real |
| read_generators.py | READ (GET) endpoint | ✅ Real |
| update_generators.py | UPDATE (PUT/PATCH) endpoints | ✅ Real |
| delete_generators.py | DELETE endpoint | ✅ Real |
| list_generators.py | LIST (GET /all) with filters | ✅ Real |

### Authentication & Authorization (6 scripts)

| Script | Purpose | Status |
|--------|---------|--------|
| auth_generators.py | Auth strategy orchestrator | ✅ Real |
| jwt_generators.py | JWT (access + refresh tokens) | ✅ Real |
| oauth_generators.py | OAuth 2.0 flows | ✅ Real |
| basic_auth_generators.py | Basic auth (user:pass) | ✅ Real |
| session_generators.py | Session-based auth | ✅ Real |
| permission_generators.py | Role-based access control (RBAC) | ✅ Real |
| api_key_generators.py | API key authentication | ✅ Real |

### Pagination (3 scripts)

| Script | Purpose | Status |
|--------|---------|--------|
| pagination_generators.py | Pagination strategy picker | ✅ Real |
| offset_pagination_generators.py | Offset/limit pagination | ✅ Real |
| cursor_pagination_generators.py | Cursor-based pagination | ✅ Real |
| keyset_pagination_generators.py | Keyset pagination | ✅ Real |

### Versioning (2 scripts)

| Script | Purpose | Status |
|--------|---------|--------|
| versioning_generators.py | API versioning orchestrator | ✅ Real |
| url_versioning_generators.py | /v1/, /v2/ URL paths | ✅ Real |
| header_versioning_generators.py | X-API-Version header | ✅ Real |

### Webhooks (4 scripts)

| Script | Purpose | Status |
|--------|---------|--------|
| webhook_generators.py | Webhook orchestrator | ✅ Real |
| webhook_delivery_generators.py | HTTP delivery logic | ✅ Real |
| webhook_signature_generators.py | HMAC signing | ✅ Real |
| webhook_retry_generators.py | Exponential backoff + DLQ | ✅ Real |

### Request Validation (4 scripts)

| Script | Purpose | Status |
|--------|---------|--------|
| validation_generators.py | Validation orchestrator | ✅ Real |
| field_validators.py | Type, length, pattern checks | ✅ Real |
| custom_validators.py | Business logic validators | ✅ Real |
| constraint_validators.py | Unique, foreign key constraints | ✅ Real |

### Error Handling (5 scripts)

| Script | Purpose | Status |
|--------|---------|--------|
| error_handling_generators.py | Error orchestrator | ✅ Real |
| http_error_generators.py | 4xx, 5xx handlers | ✅ Real |
| validation_error_generators.py | 422 Unprocessable Entity | ✅ Real |
| auth_error_generators.py | 401, 403 errors | ✅ Real |
| retry_logic_generators.py | Idempotency + retry headers | ✅ Real |

### Testing (6 scripts)

| Script | Purpose | Status |
|--------|---------|--------|
| test_generators.py | Test orchestrator (unit + integration) | ✅ Real |
| unit_test_generators.py | Single-function unit tests | ✅ Real |
| integration_test_generators.py | API endpoint tests | ✅ Real |
| fixture_generators.py | Test data + factories | ✅ Real |
| mock_generators.py | Mock external services | ✅ Real |
| e2e_test_generators.py | End-to-end API workflow tests | ✅ Real |

### Other Phase 2 (5 scripts)

| Script | Purpose | Status |
|--------|---------|--------|
| request_response_generators.py | Request/response models | ✅ Real |
| serialization_generators.py | JSON/XML serialization | ✅ Real |
| caching_generators.py | HTTP caching headers | ✅ Real |
| rate_limiting_generators.py | Rate limit headers + logic | ✅ Real |
| documentation_generators.py | API docs (Swagger, ReDoc) | ✅ Real |

---

## Phase 3: Batch Job Systems ✅

All real. 13 modules in `phase3_batch_jobs/`.

| Script | Purpose | Status |
|--------|---------|--------|
| queue_generators.py | Queue orchestrator | ✅ Real |
| redis_queue_generators.py | Redis queue setup | ✅ Real |
| rabbitmq_queue_generators.py | RabbitMQ setup | ✅ Real |
| sqs_queue_generators.py | AWS SQS setup | ✅ Real |
| retry_generators.py | Retry strategy orchestrator | ✅ Real |
| exponential_backoff_generators.py | Exponential backoff + jitter | ✅ Real |
| circuit_breaker_generators.py | Circuit breaker pattern | ✅ Real |
| dlq_generators.py | Dead-letter queue handling | ✅ Real |
| monitoring_generators.py | Job monitoring setup | ✅ Real |
| prometheus_generators.py | Prometheus metrics | ✅ Real |
| observability_generators.py | Structured logging + tracing | ✅ Real |
| health_check_generators.py | Health check endpoints | ✅ Real |
| job_status_generators.py | Job status tracking | ✅ Real |

---

## Phase 4: Production Hardening ❌ STUBS

NOT IMPLEMENTED. 60 script placeholders exist but have no working code.

| Script | Purpose | Status |
|--------|---------|--------|
| ddd_aggregate_design.py | Domain-driven design aggregates | ❌ Stub |
| ddd_value_objects.py | Value object patterns | ❌ Stub |
| ddd_repositories.py | Repository pattern | ❌ Stub |
| cqrs_pattern.py | CQRS command/query separation | ❌ Stub |
| cqrs_event_bus.py | CQRS event bus | ❌ Stub |
| event_sourcing.py | Event-driven persistence | ❌ Stub |
| event_store.py | Event store implementation | ❌ Stub |
| tdd_cycle.py | Test-driven development | ❌ Stub |
| tdd_test_first.py | Test-first workflow | ❌ Stub |
| tdd_coverage.py | Coverage requirements | ❌ Stub |
| cost_optimization.py | Infrastructure cost analysis | ❌ Stub |
| cost_database.py | Database cost optimization | ❌ Stub |
| cost_compute.py | Compute cost analysis | ❌ Stub |
| cost_storage.py | Storage cost analysis | ❌ Stub |
| chaos_engineering.py | Chaos testing framework | ❌ Stub |
| chaos_network.py | Network fault injection | ❌ Stub |
| chaos_resource.py | Resource exhaustion tests | ❌ Stub |
| chaos_dependency.py | Dependency failure tests | ❌ Stub |
| ... (42 more Phase 4 stubs) | | ❌ Stub |

---

## Phase 5: Advanced Patterns ❌ STUBS

NOT IMPLEMENTED. 50+ script placeholders exist but have no working code.

| Script | Purpose | Status |
|--------|---------|--------|
| microservices_decompose.py | Service boundary analysis | ❌ Stub |
| microservices_communication.py | Service-to-service patterns | ❌ Stub |
| microservices_deployment.py | Multi-service deployment | ❌ Stub |
| real_time_websocket.py | WebSocket patterns | ❌ Stub |
| real_time_sse.py | Server-sent events | ❌ Stub |
| real_time_sync.py | Data synchronization | ❌ Stub |
| graphql_schema.py | GraphQL from REST | ❌ Stub |
| graphql_resolvers.py | GraphQL resolvers | ❌ Stub |
| graphql_federation.py | Apollo federation | ❌ Stub |
| ml_pipeline.py | ML model serving | ❌ Stub |
| ml_training.py | Model training pipeline | ❌ Stub |
| ml_deployment.py | Model deployment | ❌ Stub |
| legacy_strangler.py | Strangler fig pattern | ❌ Stub |
| legacy_adapter.py | Legacy system adapters | ❌ Stub |
| ... (36+ more Phase 5 stubs) | | ❌ Stub |

---

## Test Files (co-located with source)

All Phase 0-3 scripts have corresponding test files:

| Test | Covers |
|------|--------|
| test_analyze_codebase.py | Framework detection |
| test_phase2_*.py (44 tests) | CRUD, auth, webhooks, validation |
| test_phase3_*.py (13 tests) | Queues, retries, monitoring |

Run all tests:
```bash
python RUN_INTEGRATION_TESTS.py
```

---

## How to Find a Script

**By purpose:**
1. Check `docs/phase-status.md` for what you need (e.g., "JWT auth")
2. Find the script name from the Phase X table above
3. Check status (✅ Real or ❌ Stub)

**By phase:**
```bash
# List all Phase 2 REST API scripts
ls skills/one-shot-generator/scripts/phase2_rest_api/

# List all Phase 4-5 stubs
ls skills/one-shot-generator/scripts/phase4_*.py
ls skills/one-shot-generator/scripts/phase5_*.py
```

**By searching:**
```bash
# Find JWT-related scripts
grep -r "JWT\|jwt\|token" skills/one-shot-generator/scripts/ --include="*.py" | cut -d: -f1 | sort -u

# Count scripts per phase
ls -1 skills/one-shot-generator/scripts/phase*.py | cut -d_ -f1 | sort | uniq -c
```

---

## Adding a New Script

When you implement a Phase 4-5 module:

1. Create the script: `skills/one-shot-generator/scripts/phase4_myfeature.py`
2. Add it to this index (change ❌ Stub → ✅ Real)
3. Create test file: `test_phase4_myfeature.py`
4. Update `docs/phase-status.md`
5. Bump version in plugin.json + CHANGELOG.md

See `docs/skill-authoring.md` for script guidelines.
