---
type: plan
last_verified: 2026-05-16
owner: claude
status: active
related_beads: ["bd-002", "bd-003", "bd-004", "bd-005", "bd-006"]
---

# Phase 4 Implementation Plan — Production Hardening

**Goal:** Implement 60 modules for enterprise production systems.  
**Release Target:** v3.0.0  
**Total Effort:** ~220-280 hours (4-5 weeks full-time)  
**Modules:** 60  

---

## Overview: 4 Implementation Chunks

Phase 4 is structured in dependency order. Each chunk unlocks the next.

| Chunk | Name | Modules | Hours | Release |
|-------|------|---------|-------|---------|
| 1 | Domain-Driven Design | 15 | 50-60 | v3.0.0-alpha |
| 2 | CQRS + Event Sourcing | 18 | 70-80 | v3.0.0-beta |
| 3 | Testing + Cost + Reliability | 20 | 60-70 | v3.0.0-rc |
| 4 | Compliance + Hardening | 7 | 40-50 | v3.0.0 (release) |

---

## Chunk 1: Domain-Driven Design (DDD)

**Modules:** 15  
**Effort:** 50-60 hours  
**Release:** v3.0.0-alpha  
**Status:** Ready to start (no dependencies)  
**Bead:** bd-003

### What It Delivers

Foundation for all Phase 4 work. Enables domain-first architecture and bounded contexts.

### Modules (15)

| # | Module | Purpose | Effort |
|---|--------|---------|--------|
| 1 | ddd_aggregate_design.py | Design aggregates + value objects | 6h |
| 2 | ddd_repository_pattern.py | Repository abstraction (ORM-agnostic) | 5h |
| 3 | ddd_domain_events.py | Domain event emission + handlers | 6h |
| 4 | ddd_bounded_contexts.py | Detect + split service boundaries | 4h |
| 5 | ddd_entity_design.py | Entity identity + lifecycle | 3h |
| 6 | ddd_ubiquitous_language.py | Extract domain terminology + glossary | 4h |
| 7 | ddd_application_service.py | Application service patterns | 5h |
| 8 | ddd_specification_pattern.py | Specification objects for queries | 4h |
| 9 | ddd_value_object_library.py | Common value object builders | 4h |
| 10 | ddd_aggregate_roots.py | Aggregate root identification | 3h |
| 11 | ddd_snapshot_pattern.py | Event sourcing snapshots | 5h |
| 12 | ddd_saga_pattern.py | Long-running transactions | 6h |
| 13 | ddd_module_scaffolder.py | Scaffold DDD-structure modules | 3h |
| 14 | ddd_validation_rules.py | Business rule validation | 4h |
| 15 | ddd_context_mapper.py | Map multiple bounded contexts | 5h |

### Implementation Path

1. **Days 1-2:** Aggregate design + repository pattern (modules 1-2)
2. **Days 3-4:** Domain events + bounded contexts (modules 3-4)
3. **Days 5-6:** Entity + ubiquitous language (modules 5-6)
4. **Days 7-8:** Application service + specification (modules 7-8)
5. **Days 9:** Value objects + roots (modules 9-10)
6. **Days 10-11:** Snapshot + saga + scaffolder (modules 11-13)
7. **Days 12:** Validation + context mapping (modules 14-15)

### Dependencies

- None (foundational chunk)

### Unblocks

- Chunk 2 (CQRS) depends on DDD entities and repositories
- Chunk 3 (TDD) can run in parallel after day 2
- Chunk 4 (Compliance) can run in parallel after day 4

### Testing

- Test on `test_contexts/django_minimal.txt` with models
- Verify generated aggregates have proper boundaries
- Verify repositories work with existing ORMs

### Success Criteria

- All 15 modules working (❌ Stub → ✅ Real in docs/scripts-index.md)
- DDD walkthroughs in `docs/examples/phase4-ddd.md`
- v3.0.0-alpha released

---

## Chunk 2: CQRS + Event Sourcing

**Modules:** 18  
**Effort:** 70-80 hours  
**Release:** v3.0.0-beta  
**Status:** Blocked by Chunk 1  
**Bead:** bd-004

### What It Delivers

Event-driven architecture with Command-Query responsibility separation. Enables temporal consistency + audit trails.

### Modules (18)

| # | Module | Purpose | Effort |
|---|--------|---------|--------|
| 1 | cqrs_command_handler.py | Command dispatch + validation | 6h |
| 2 | cqrs_query_handler.py | Query optimization (read models) | 5h |
| 3 | cqrs_event_bus.py | Event pub/sub (Kafka, RabbitMQ, Redis) | 8h |
| 4 | cqrs_event_store.py | Event log (PostgreSQL, DynamoDB, custom) | 8h |
| 5 | cqrs_snapshot_store.py | Snapshots for performance | 5h |
| 6 | cqrs_projections.py | Read model projections | 6h |
| 7 | cqrs_saga_orchestrator.py | Distributed saga (long-running transactions) | 8h |
| 8 | cqrs_idempotency.py | Deduplication + replay safety | 5h |
| 9 | event_sourcing_aggregate.py | Aggregate + event sourcing integration | 7h |
| 10 | event_sourcing_upcaster.py | Event versioning + migration | 6h |
| 11 | event_sourcing_snapshot.py | Snapshot + restore mechanics | 5h |
| 12 | event_sourcing_playback.py | Full rebuild from event log | 4h |
| 13 | event_sourcing_time_travel.py | Query at specific point-in-time | 4h |
| 14 | cqrs_read_model_sync.py | Keep read models in sync | 6h |
| 15 | cqrs_dead_letter_handler.py | Poison pill handling + replay | 5h |
| 16 | cqrs_performance_tuning.py | Cache strategies + projection optimization | 6h |
| 17 | cqrs_testing_utilities.py | Test fixtures for CQRS tests | 5h |
| 18 | cqrs_framework_adapters.py | Django ORM, SQLAlchemy, Spring Data adapters | 7h |

### Implementation Path

1. **Days 1-2:** Command + query handlers (modules 1-2)
2. **Days 3-4:** Event bus + event store (modules 3-4)
3. **Days 5:** Snapshots + projections (modules 5-6)
4. **Days 6-7:** Saga + idempotency (modules 7-8)
5. **Days 8-9:** Event sourcing aggregate + upcaster (modules 9-10)
6. **Days 10:** Snapshot + playback (modules 11-12)
7. **Days 11-12:** Time travel + read model sync (modules 13-14)
8. **Days 13-14:** DLH + tuning + testing + adapters (modules 15-18)

### Dependencies

- **Depends on:** Chunk 1 (DDD entities + repositories)
- **Unblocks:** Chunk 3 (TDD) and Chunk 4 (Compliance)

### Testing

- Test projections with `test_contexts/fastapi_minimal.txt` (async)
- Verify event replay produces same state as direct operations
- Test snapshot + replay consistency
- Verify saga orchestration across multiple aggregates

### Success Criteria

- All 18 modules working
- CQRS + Event Sourcing walkthrough in `docs/examples/phase4-cqrs.md`
- v3.0.0-beta released

---

## Chunk 3: Testing + Cost + Reliability

**Modules:** 20  
**Effort:** 60-70 hours  
**Release:** v3.0.0-rc  
**Status:** Can start after Chunk 1 Day 2  
**Bead:** bd-005

### What It Delivers

Test-driven development harness, infrastructure cost analysis, and resilience patterns.

### Modules (20)

| # | Module | Purpose | Effort |
|---|--------|---------|--------|
| **Testing (8 modules)** |
| 1 | tdd_cycle_enforcer.py | Test → red → green → refactor | 6h |
| 2 | tdd_fixtures_library.py | DDD + CQRS test fixtures | 5h |
| 3 | tdd_mutation_testing.py | Verify test quality (mutation score) | 4h |
| 4 | tdd_property_testing.py | Hypothesis + QuickCheck-style generators | 5h |
| 5 | tdd_test_data_builders.py | Fluent API for test object construction | 3h |
| 6 | tdd_contract_testing.py | Consumer-driven contracts (Pact) | 5h |
| 7 | tdd_chaos_testing.py | Resilience testing (failures, latency) | 6h |
| 8 | tdd_benchmark_suite.py | Performance regression detection | 4h |
| **Cost Management (5 modules)** |
| 9 | cost_infrastructure_analyzer.py | Estimate cloud costs (AWS, GCP, Azure) | 6h |
| 10 | cost_db_optimization.py | Query + index cost analysis | 5h |
| 11 | cost_api_budgeting.py | Token budgets + rate limit warnings | 4h |
| 12 | cost_resource_profiler.py | Memory + CPU usage patterns | 4h |
| 13 | cost_optimization_recommender.py | Suggest cost savings | 5h |
| **Reliability (7 modules)** |
| 14 | chaos_network_faults.py | Inject network delays + failures | 6h |
| 15 | chaos_resource_exhaustion.py | CPU + memory stress testing | 5h |
| 16 | chaos_dependency_failures.py | Simulate downstream service failures | 5h |
| 17 | chaos_data_corruption.py | Test data integrity checks | 4h |
| 18 | circuit_breaker_pattern.py | Fail-fast with auto-recovery | 5h |
| 19 | bulkhead_pattern.py | Isolate critical paths | 4h |
| 20 | observability_metrics.py | Prometheus + custom metrics | 6h |

### Implementation Path

1. **Days 1-2:** TDD cycle + fixtures (modules 1-2)
2. **Days 3-4:** Mutation + property testing (modules 3-4)
3. **Days 5:** Test data builders + contracts (modules 5-6)
4. **Days 6-7:** Chaos + benchmarks (modules 7-8)
5. **Days 8-9:** Cost infrastructure + DB (modules 9-10)
6. **Days 10:** Cost API + profiler (modules 11-12)
7. **Days 11:** Cost recommender (module 13)
8. **Days 12-13:** Chaos (network, resources, deps, data) (modules 14-17)
9. **Days 14:** Circuit breaker + bulkhead + observability (modules 18-20)

### Dependencies

- **Depends on:** Chunk 1 (optional, but DDD testing easier with proper boundaries)
- **Parallel with:** Chunk 2 (CQRS, can run in parallel)
- **Unblocks:** Chunk 4 (Compliance)

### Testing

- TDD: Generate code, verify failing tests first
- Cost: Analyze Phase 2 (REST APIs) code for cost
- Chaos: Test Phase 3 (batch jobs) resilience

### Success Criteria

- All 20 modules working
- TDD + cost + chaos walkthroughs in `docs/examples/phase4-testing.md`
- v3.0.0-rc released

---

## Chunk 4: Compliance + Hardening

**Modules:** 7  
**Effort:** 40-50 hours  
**Release:** v3.0.0 (final)  
**Status:** Blocked by Chunks 1-3  
**Bead:** bd-006

### What It Delivers

Enterprise compliance (SOC2, HIPAA, GDPR) and security hardening.

### Modules (7)

| # | Module | Purpose | Effort |
|---|--------|---------|--------|
| 1 | compliance_framework_selector.py | Choose SOC2, HIPAA, GDPR based on project | 5h |
| 2 | compliance_soc2_checklist.py | SOC2 trust service criteria (CC, CA, CT, CP) | 8h |
| 3 | compliance_hipaa_checklist.py | HIPAA security + privacy rules + audit log | 8h |
| 4 | compliance_gdpr_checklist.py | GDPR data rights + consent + DPA | 8h |
| 5 | security_secrets_scanning.py | Detect + remediate hardcoded secrets | 6h |
| 6 | security_dependency_audit.py | Vulnerability scanning (npm audit, pip-audit, OWASP DependencyCheck) | 6h |
| 7 | security_encryption_standards.py | AES-256, TLS 1.3, key rotation enforcement | 6h |

### Implementation Path

1. **Days 1-2:** Compliance framework selector (module 1)
2. **Days 3-4:** SOC2 checklist (module 2)
3. **Days 5-6:** HIPAA checklist (module 3)
4. **Days 7-8:** GDPR checklist (module 4)
5. **Days 9-10:** Secrets scanning (module 5)
6. **Days 11:** Dependency audit (module 6)
7. **Days 12-13:** Encryption standards (module 7)

### Dependencies

- **Depends on:** All Chunks 1-3 (these enable compliance across all systems)

### Testing

- Test each compliance module on a sample project
- Verify checklist output is actionable
- Test secrets scanning on code with intentional secrets

### Success Criteria

- All 7 modules working
- Compliance + security walkthrough in `docs/examples/phase4-compliance.md`
- v3.0.0 released to marketplace

---

## Beads & Work Tracking

Open one bead per chunk:

```jsonl
{"id": "bd-003", "title": "Implement Phase 4 Chunk 1: DDD (15 modules)", "status": "pending", "priority": "high", "created": "2026-05-16", "category": "feature", "blocked_by": null, "owner": "claude"}
{"id": "bd-004", "title": "Implement Phase 4 Chunk 2: CQRS + Event Sourcing (18 modules)", "status": "pending", "priority": "high", "created": "2026-05-16", "category": "feature", "blocked_by": "bd-003", "owner": "claude"}
{"id": "bd-005", "title": "Implement Phase 4 Chunk 3: Testing + Cost + Reliability (20 modules)", "status": "pending", "priority": "high", "created": "2026-05-16", "category": "feature", "blocked_by": "bd-003", "owner": "claude"}
{"id": "bd-006", "title": "Implement Phase 4 Chunk 4: Compliance + Hardening (7 modules)", "status": "pending", "priority": "high", "created": "2026-05-16", "category": "feature", "blocked_by": "bd-005", "owner": "claude"}
```

---

## Effort Summary

| Chunk | Modules | Hours | Person-Weeks | Start | End |
|-------|---------|-------|--------|-------|-----|
| 1 (DDD) | 15 | 50-60 | 1.2-1.5 | Week 1 | Week 2 |
| 2 (CQRS/ES) | 18 | 70-80 | 1.8-2.0 | Week 2 | Week 4 |
| 3 (Testing/Cost) | 20 | 60-70 | 1.5-1.8 | Week 1 (parallel) | Week 3 |
| 4 (Compliance) | 7 | 40-50 | 1.0-1.2 | Week 4 | Week 5 |
| **TOTAL** | **60** | **220-260** | **5-6** | **Week 1** | **Week 5** |

---

## Parallel Execution

For faster delivery, run Chunks 1 + 3 in parallel (both ~11-12 days):

```
Week 1:
  Mon-Fri: Chunk 1 Days 1-5 (DDD aggregates, repos, events, contexts, entities)
  Mon-Fri: Chunk 3 Days 1-5 (TDD, fixtures, mutation, property, builders) [in parallel]

Week 2:
  Mon-Fri: Chunk 1 Days 6-12 (ubiq lang, app service, spec, values, saga, scaffold)
  Mon-Fri: Chunk 2 Days 1-5 (CQRS handlers, event bus, store) [start Chunk 2]
  Mon-Fri: Chunk 3 Days 6-11 (contracts, chaos, cost, profiler) [finish Chunk 3]

Week 3:
  Mon-Fri: Chunk 2 Days 6-14 (projections, sagas, event sourcing, upcasting)

Week 4:
  Mon-Fri: Chunk 4 Days 1-10 (compliance frameworks, checklists)

Week 5:
  Mon-Fri: Chunk 4 Days 11-13 (security, encryption)
```

With parallel execution: **5 weeks full-time** to complete all of Phase 4.

---

## Next: Phase 5

After Phase 4 is released (v3.0.0), Phase 5 begins:

- **Phase 5 (50+ modules):** Microservices, real-time (WebSocket/SSE), GraphQL, ML pipelines, legacy modernization
- **Target:** v4.0.0 (Q3 2026)
- **Effort:** ~300+ hours

See `ROADMAP.md` for Phase 5 details.

---

**Status:** ✅ Plan complete. Ready to implement bd-003 (Chunk 1 - DDD).
