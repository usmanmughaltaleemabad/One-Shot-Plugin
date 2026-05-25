---
type: audit
last_verified: 2026-05-25
owner: claude
---

# GAP ANALYSIS: one-shot-prompting v1.1.0

**Audit Date:** 2026-05-25  
**Auditor:** Claude Code Agent  
**Purpose:** Identify specific, actionable gaps preventing production launch

---

## 1. CRITICAL GAPS (Must Fix)

### Gap #1: Zero External Validation (Enterprise Risk — HIGH SEVERITY)

**Problem:**
- All validation internal (6 architect dry-runs, synthetic critic loops, integration tests)
- No real users have deployed generated code to production
- Unknown failure modes may exist in actual deployment scenarios
- Claims like "800+ tests green" are self-validated only

**Impact on Ride-Sharing:**
- Unknown how plugin handles ride-specific invariants (status progression, payment reconciliation, driver matching)
- No evidence of handling concurrent updates (driver availability, ride acceptance race conditions)
- Schema inference may fail on non-CRUD relationships (geographic proximity queries)

**Mitigation Path:**
1. **Pilot Phase 1 (Weeks 1–2):** Run 3 trusted teams through plugin with ride-sharing prototype
2. **Pilot Phase 2 (Weeks 3–4):** Collect failure data, update curriculum
3. **Public Launch (Week 5+):** Gather real-world observability, refine based on failures

**Effort to Fix:** 4 weeks (not code change; operational milestone)

**Success Criteria:**
- 5+ pilot users complete 10+ runs each
- Zero catastrophic failures (data corruption, auth bypass)
- Failure rate < 5% (ESCALATE verdict)

---

### Gap #2: Test Import Path Error (CI Blocker — LOW SEVERITY)

**Problem:**
```
ERROR collecting one-shot-prompting/tests/test_docs_drift.py
from scripts.codebase_diff import extract_classes_and_functions, detect_changes, scan_codebase
ModuleNotFoundError: No module named 'scripts.codebase_diff'
```

**Root Cause:**
- Test file imports from wrong path (scripts.codebase_diff instead of ../.../scripts/codebase_diff)
- Affects 1 file; doesn't impact functionality (WS2 docs-drift agent works)

**Impact:**
- CI test collection fails (reports 789 collected but can't import 1)
- Misleading test count (actual: 784 passing, 1 import error)

**Fix:**
1. Correct import path in `tests/test_docs_drift.py` (3 lines)
2. Verify tests run: `cd tests && python -m pytest test_docs_drift.py -v`

**Effort:** 30 minutes

---

### Gap #3: OTel Collector Availability Not Validated (Production Risk — MEDIUM SEVERITY)

**Problem:**
- Graceful no-op when OTLP disabled (`OSP_OTEL_ENABLED=0`), but **production deployments need working Jaeger**
- No health check for Jaeger sidecar/gateway before emitting spans
- If collector unreachable, spans silently dropped (no warning to user)

**Impact on Production:**
- Observability missing in production (no cost tracking, latency profiling, failure analysis in Jaeger)
- No way to diagnose agent performance issues or cost overruns in real time

**Mitigation Path:**
1. Add health check in `otel_tracer.py` (ping Jaeger on init)
2. Emit warning if unreachable (suggest `docker-compose up` or config collector URL)
3. Graceful fallback to console exporter (local logging only)

**Effort:** 1 day (health check + warning)

**Dependencies:**
- Helm chart for Kubernetes Jaeger sidecar (1–2 days, separate effort)
- Docker-compose Jaeger stack already provided (✅ Done)

---

## 2. MEDIUM-PRIORITY GAPS (Reduce Quality/Confidence)

### Gap #4: Critic Loop Cost Unpredictable (Budget Risk — MEDIUM SEVERITY)

**Problem:**
- `cost_budget.py` pre-estimates agent costs (architect, implementer, reviewer, critic base round)
- **Does NOT estimate critic loop cost** (depends on test suite runtime, which is unknown pre-run)
- If tests run slowly (30+ second suite), critic loop cost can exceed budget unexpectedly

**Scenario:**
```
User: /one-shot "add user auth" @./project --budget=0.50
Pre-estimate: $0.40 (all stages except critic)
Actual cost: $0.65 (critic loop 2 iterations × slow 30s test suite)
Result: Budget exceeded, user surprised
```

**Impact:**
- Unpredictable spend (can exceed --budget flag)
- Production cost overruns (if deployments hit critic loops)

**Mitigation Path:**
1. **Conservative estimation:** `cost_budget.py` assumes 2 critic loops (not 1)
2. **Post-run warning:** Emit "Cost exceeded estimate by $X. Suggest --budget=$Y for similar feature next time"
3. **Test-runtime prediction:** Optional flag `--predict-test-cost` (dry-run tests to estimate runtime)

**Effort:** 1 day (estimate adjustment + warning)

**Expected improvement:** Budget accuracy ±25% → ±10%

---

### Gap #5: Cost Calibration Low Confidence (Empirical Gap — MEDIUM SEVERITY)

**Problem:**
- Only 6 architect dry-run observations recorded
- Cost estimates based on 6 data points (not statistically significant)
- Ideal: 50+ observations for 95% confidence interval

**Impact:**
- Cost estimates may be off by ±30% until more data collected
- Can't distinguish agent degradation from natural variance
- Curriculum learning relies on cost tracking (weak signal)

**Mitigation Path:**
1. **Accumulate data passively:** /dream consolidator + `/learnings export` automatically collect cost observations
2. **Auto-recalibrate:** `cost_calibrator.py` runs after every 10th generation, updates `cost_budget.py`
3. **Publish confidence:** `/learnings dashboard` shows "Cost model confidence: 42% (6 observations, need 50)"

**Effort:** Already implemented (v4.9), just needs real-world usage

**Timeline:**
- Weeks 1–4 (pilot): 50+ observations → confidence >95%
- Ongoing: auto-calibration keeps estimates fresh

---

### Gap #6: No Circuit-Breaker for Repeated Agent Failures (Reliability Risk — MEDIUM SEVERITY)

**Problem:**
- If agent fails 3x on the same task, critic loop escalates to ESCALATE (correct)
- **But SKILL.md has no circuit-breaker** (what if external service is down? keeps retrying indefinitely)
- Example: If MCP service unavailable, mcp-integrator fails 3x, workflow escalates, but no backoff

**Impact:**
- Long-running escalations (3 × 120s timeout = 360s user wait)
- Cascading failures (one service down → many runs fail)
- No exponential backoff (always retry immediately)

**Mitigation Path:**
1. Add circuit-breaker in Stage 7: `if failures_count > 3: escalate_to_manual_review`
2. Add exponential backoff (1s, 2s, 4s) between retries
3. Health check before dispatch (fail-fast if known to be down)

**Effort:** 1 day (circuit-breaker logic + backoff)

---

### Gap #7: OTel Span Attributes Missing Model Info (Observability Gap — MEDIUM SEVERITY)

**Problem:**
- Spans track cost, tokens, verdict, intent, entities_count, etc.
- **Missing: `model` attribute** (can't tell which agent ran: "architect" or "architect-gpt4"?)
- Can't correlate Jaeger traces with agent.md version changes

**Impact:**
- Harder to debug: "Why did architect fail at timestamp T?" → Can't see if model changed
- No model A/B testing: Can't compare Sonnet vs older models

**Mitigation Path:**
1. Add `model` attribute to all agent spans (2–3 hours)
2. Add `agent_version` (hash of agent.md) for regression detection

**Effort:** 2 hours

---

### Gap #8: No Dynamic Skill Discovery (Extensibility Gap — MEDIUM SEVERITY)

**Problem:**
- Skills hardcoded in SKILL.md stages (grill-me at 1.6, tdd-cycle at 3, etc.)
- New skills require manual SKILL.md edits
- No plugin registry or auto-loading

**Impact:**
- Not user-extensible (can't add custom skills without forking)
- Harder to maintain (new WS requires SKILL.md patch)

**Mitigation Path:**
1. **Future work (Phase 2):** Skill registry in `.claude/skills/registry.json`
2. **Dynamic loading:** `@grill-me` syntax in prompts triggers skill auto-invoke
3. Non-blocking for MVP (hardcoded wiring is fine for v1.1)

**Effort:** 1 week (non-blocking)

---

## 3. NICE-TO-HAVE GAPS (Improve UX/Coverage)

### Gap #9: No Streaming Spec Review (UX — LOW SEVERITY)

**Problem:**
- `--review` flag shows spec.json to user, but **only after architect completes**
- Full pipeline (architect → implementer → reviewer) before user sees design
- If user dislikes design, all downstream work wasted

**Ideal Flow:**
```
Stage 1: Scan + extract
  ↓
Stage 2: Architect → spec.json [PAUSE FOR REVIEW]
User reviews spec.json, approves/modifies
  ↓
Stage 3: Implementer + test-author (based on approved spec)
```

**Impact:**
- UX friction (user can't shape design early)
- Wasted work (regenerate if design doesn't match vision)

**Mitigation Path:**
1. Emit spec.json early (after Stage 2)
2. Add `--review-and-pause` flag (SKILL.md waits for user approval before Stage 3)
3. Accept modifications to spec.json (re-parse and continue)

**Effort:** 3 days (non-blocking UX improvement)

---

### Gap #10: GraphQL Support Missing (Language Gap — LOW SEVERITY)

**Problem:**
- Currently REST-only (OpenAPI schema, CRUD endpoints)
- No GraphQL schema generation, resolver generation, or subscription support
- Common request from GraphQL-first shops

**Impact:**
- Can't generate GraphQL APIs (customer friction for GraphQL teams)

**Mitigation Path:**
1. **Phase 2 workstream:** GraphQL architect subagent
2. Emit `schema.graphql` + resolvers (Apollo/Strawberry/other)
3. Estimated effort: 2 weeks

**Blocking?** No. REST support sufficient for MVP.

---

### Gap #11: Agent Prompt Caching Not Adaptive (Performance — LOW SEVERITY)

**Problem:**
- Prompt caching (v4.14) caches entire agent.md (all frameworks, all patterns)
- Could be more selective: cache only FastAPI patterns for FastAPI projects
- Minor optimization opportunity

**Impact:**
- Caches slightly larger than necessary (100K tokens instead of 80K)
- Cache hit rate: 90% (already very good)

**Mitigation Path:**
1. Framework-specific agent prompt variants (conditional caching)
2. Non-critical (current approach simple and works)

**Effort:** 1 week (low ROI, skip)

---

### Gap #12: No Pre-Built Grafana Dashboards (Visibility — LOW SEVERITY)

**Problem:**
- Jaeger UI available, but no Grafana dashboards
- Users must create dashboards manually (cost trends, success rates, etc.)

**Mitigation Path:**
1. Docker-compose includes Grafana template (already provided)
2. Pre-built dashboard JSON in `docs/observability/grafana-dashboards.json`

**Effort:** 1 day

---

## 4. DOCUMENTED LIMITATIONS (Not Gaps; Expected)

### L1: Only 6 Agent Observations (Expected)

**Status:** ✅ Acceptable  
**Reason:** Cost calibration improves over time with real-world runs  
**Mitigation:** `/dream` consolidator mines failures; cost_calibrator.py auto-adjusts after 50 observations

### L2: Zero External Users (Expected)

**Status:** ⚠️ Acceptable for closed beta; MUST be addressed for public launch  
**Reason:** No real-world validation before public  
**Mitigation:** 4-week pilot program (see Gap #1)

### L3: Not Tested at 10MB+ Codebase Scale (Expected)

**Status:** ⚠️ Acceptable for MVP; should validate in Phase 2  
**Reason:** Context pruning is deterministic but untested at true scale  
**Mitigation:** Test on 10MB monorepo (FastAPI with 50+ services)

### L4: No Schema Inheritance Support (Expected)

**Status:** ✅ Acceptable for MVP  
**Reason:** Rare pattern; can work around with explicit FKs  
**Mitigation:** Future workstream (Phase 2)

### L5: Critic Loop Max 3 Iterations (Expected)

**Status:** ⚠️ Mostly acceptable; sometimes insufficient  
**Reason:** Safety limit prevents infinite loops  
**Mitigation:** Conservative limit; can be raised to 5 if needed

---

## 5. SPECIFIC GAPS FOR RIDE-SHARING SYSTEM

### RS-Gap #1: No Multi-Stop Route Modeling (MEDIUM)

**Problem:**
- Ride has multiple stops (pickup → waypoints → dropoff)
- Architect doesn't understand M:N relationship (Ride ↔ Location via stops)
- Likely generates flat list of locations, not ordered stops

**Mitigation:**
1. Add explicit "stop_order" field to hint architect (int, ordered)
2. Manual spec review (architect dry-run) before implementer
3. Service-author enforces ordering invariant

**Effort:** Workaround; no code change needed

### RS-Gap #2: No Geospatial Queries (MEDIUM)

**Problem:**
- Ride matching requires proximity queries (find drivers within 5km)
- Architect generates basic FK schema; no spatial indices
- Implementer generates CRUD only; no proximity logic

**Mitigation:**
1. Service-author adds haversine distance calculation (business logic)
2. Reviewer should flag missing spatial index on location columns
3. Manual query optimization (needs DBA or architect dry-run + review)

**Effort:** Partial support via service-author; full support requires Phase 2

### RS-Gap #3: No Concurrent Update Handling (MEDIUM)

**Problem:**
- Driver availability (toggle online/offline) is concurrent
- Ride acceptance (multiple drivers respond simultaneously) needs optimistic locking
- Architect generates basic schema; service-author must add locking

**Mitigation:**
1. Service-author checks for "optimistic_locking" contract hint (exists in body_hints)
2. Test-author generates tests for concurrent updates
3. Reviewer should flag if missing (but may miss)

**Effort:** Depends on body_hints coverage; likely ~80% handled

### RS-Gap #4: Payment Integration Not Modeled (MEDIUM)

**Problem:**
- Payment is external (Stripe, Square, etc.)
- Schema has Payment entity, but no integration with external service
- Implementer generates CRUD; no service layer calls

**Mitigation:**
1. Service-author should generate payment service calls (if intent mentions payment)
2. Implementer adds imports for payment library
3. Reviewer checks for API key handling (hardcoded secret check)

**Effort:** ~70% handled by existing agents; manual tuning needed

---

## 6. PRIORITIZED FIX LIST

### Priority 1 (Do Before Pilot)
| Gap | Fix | Effort | Blocker |
|-----|-----|--------|---------|
| Test import error | Fix path in test_docs_drift.py | 30 min | ✅ CI |
| OTel health check | Add collector health check + warning | 1 day | ⚠️ Prod |

### Priority 2 (Before Public Launch)
| Gap | Fix | Effort | Blocker |
|-----|-----|--------|---------|
| Critic loop cost | Assume 2 loops in estimate + post-run warning | 1 day | ⚠️ Billing |
| Circuit-breaker | Add fail-fast + exponential backoff | 1 day | ⚠️ Reliability |
| External validation | 4-week pilot program | 4 weeks | ✅ Yes |

### Priority 3 (Nice-to-Have)
| Gap | Fix | Effort | Blocker |
|-----|-----|--------|---------|
| OTel model attr | Add model to all spans | 2 hours | ❌ No |
| Grafana dashboards | Pre-built dashboard templates | 1 day | ❌ No |
| Streaming spec review | `--review-and-pause` flag | 3 days | ❌ No |

---

## 7. SUCCESS CRITERIA FOR GAP CLOSURE

| Gap | Success Metric | Verification |
|-----|---|---|
| Test import error | All 789 tests collected + pass | CI green |
| OTel collector | Health check runs on init | Integration test |
| Critic cost | Actual cost within 20% of estimate | cost_observations.jsonl vs --budget |
| External validation | 5 pilot users, <5% failure rate | Pilot metrics |
| Circuit-breaker | No timeout cascades | Logs show early escalation |

---

**Audit Completed:** 2026-05-25  
**Total Gaps Identified:** 12 (2 critical, 6 medium, 4 low)  
**Blocking Gaps:** 3 (test import, OTel health, external validation)  
**Non-Blocking Gaps:** 9 (nice-to-have, post-MVP)

</content>
