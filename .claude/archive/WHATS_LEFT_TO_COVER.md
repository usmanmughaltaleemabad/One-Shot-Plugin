# What's Left to Cover — Complete Roadmap

**Status:** v0.7.0 infrastructure complete. v1.0 blockers identified. Strangler features pending.  
**Current Date:** May 9, 2026  
**Days to v1.0:** 22 days  
**Resource Requirement:** 2.2 FTE × 4 weeks

---

## THE BIG PICTURE

### ✅ WHAT'S DONE (57 modules built, 13,133 LOC Python)

**Phase 0:** Silent planning engine + verification harness ✅  
**Phase 2:** REST API specialist (44 modules) ✅  
**Phase 3:** Batch job specialist (13 core modules) ✅  
**v0.7.0:** Logging, versioning, testing infrastructure ✅  
**Harness:** 40+ helper modules (preview, TDD, review, health check, templates, etc.) ✅

**Status:** Production-ready MVP except for strangler integration.

---

### ❌ WHAT'S MISSING (The Strangler Gap)

The plugin can generate CRUD APIs and batch jobs, but **cannot extract monoliths into microservices** — the $2.5B uncontested market.

**What you're missing:**
1. `/strangler-analyze` — Identify extractable features from monoliths
2. `/strangler-extract` — Generate complete microservice + legacy adapter
3. `/strangler-validate` — Pre-flight safety checks
4. `/strangler-roadmap` — 12-24 month modernization plans

**Impact:** Can't serve enterprise market (legacy modernization) worth $2.5B.

---

## WHAT'S LEFT TO COVER (4-Week Sprint)

### PRIORITY 1: Strangler Commands (Weeks 1-3)

#### Week 1: `/strangler-analyze` — Identify Extraction Candidates

**Goal:** Given a monolith, identify which features can be extracted  
**Success:** Can identify 5+ extractable features in test monolith with difficulty scores

**What to build:**
```
INPUT:  Monolith codebase (@/path/to/django-app)
ANALYZER OUTPUT:
  - Feature 1: User Management (tight coupling: 3/10, extractability: 9/10, difficulty: YELLOW)
  - Feature 2: Payment Service (tight coupling: 8/10, extractability: 5/10, difficulty: RED)
  - Feature 3: Notification Service (tight coupling: 2/10, extractability: 9/10, difficulty: GREEN)
```

**Files to modify:**
- `analyze_codebase.py` — Add feature extraction + coupling detection
- `SKILL.md` — Add `/strangler-analyze` section with 5+ examples
- `orchestrate_harness_modules.py` — Wire up `--strangler` flag
- Tests — Add feature detection validation

**Acceptance Criteria:**
- ✅ Detects 5+ features in test monolith
- ✅ Scores match human architect assessment
- ✅ Performance: <30 seconds on 100K+ LOC
- ✅ 8+ integration tests passing
- ✅ Works on real Django/Spring/Go monoliths

**Effort:** ~120 hours (1 week, 1 senior engineer + 1 QA)

---

#### Week 2: `/strangler-extract` — Generate Microservice + Adapter

**Goal:** Generate complete microservice to replace one feature from monolith  
**Success:** Generated code compiles, tests pass, deploys to staging K8s

**What to build:**
```
INPUT:  Monolith + feature to extract ("payment_service")
GENERATOR OUTPUT:
  - Microservice code (Go/FastAPI)
  - Database schema + ORM
  - Error handling + validation
  - Event producers
  - Legacy adapter (maintains old interface)
  - Docker + K8s manifests
  - Integration tests
  - Rollback procedure
```

**Files to create/modify:**
- `phase3_runner.py` → `strangler_extract_runner.py` (leverage batch job generation patterns)
- `SKILL.md` — Add `/strangler-extract` section with payment/notification/inventory examples
- Integration tests — Full E2E (analyze → extract → build → test → deploy)

**Acceptance Criteria:**
- ✅ Generated code compiles/runs
- ✅ Legacy adapter maintains old interface
- ✅ Integration tests pass (new + old code + fallback)
- ✅ Data consistency verified
- ✅ Deploys to staging K8s
- ✅ Canary deployment works

**Effort:** ~160 hours (1.5 weeks, 1 lead engineer + 1 QA)

---

#### Week 3: `/strangler-validate` + `/strangler-roadmap` + Documentation

**Goal:** Safety checks + full modernization plan generation  
**Success:** Users can validate extraction safety before committing

**What to build:**

**`/strangler-validate`:**
```
INPUT:  Monolith + feature to extract
OUTPUT:
  - RED/YELLOW/GREEN risk assessment
  - Identify circular dependencies
  - Validate transaction boundaries
  - Suggest mitigations
```

**`/strangler-roadmap`:**
```
INPUT:  Monolith + extraction priorities
OUTPUT:
  - Phased extraction plan (12-24 months)
  - Timeline + resource requirements
  - Investment vs. payoff
  - Risk per phase
  - Excel/PDF roadmap
```

**Files to modify:**
- `SKILL.md` — Add validate + roadmap sections
- Documentation — TESTING.md, QUICKSTART.md, troubleshooting guide
- plugin.json — Add command metadata

**Acceptance Criteria:**
- ✅ `/strangler-validate` validates 3+ scenarios
- ✅ `/strangler-roadmap` generates 12-month plans
- ✅ Documentation complete (no "coming soon")
- ✅ Anthropic compliance approved
- ✅ Examples working

**Effort:** ~80 hours (1 week, 1 engineer + 1 writer)

---

### PRIORITY 2: Testing & Validation (Throughout Weeks 1-4)

| Task | Owner | Effort | Criteria |
|------|-------|--------|----------|
| Real monolith testing | QA | 40h | Test on 3 real projects (Django, Spring, Go) |
| Performance benchmarks | QA | 20h | <30s analyze, <2m extract |
| Security review | Security | 16h | SAST scan + approval |
| E2E workflow tests | QA | 30h | analyze → extract → deploy passing |

**Total:** 106 hours (spread across 4 weeks)

---

### PRIORITY 3: Documentation Updates (Throughout Weeks 1-4)

| Document | Owner | Effort | Scope |
|----------|-------|--------|-------|
| README.md | Writer | 8h | Strangler positioning, examples |
| SKILL.md strangler sections | Writer | 24h | analyze, extract, validate, roadmap with examples |
| QUICKSTART.md | Writer | 8h | Strangler-focused getting started |
| TESTING.md | Writer | 6h | Strangler test coverage |
| Troubleshooting guide | Writer | 10h | Common issues + fixes |
| Migration guide | Writer | 8h | Step-by-step strangler adoption |
| Examples | Engineer | 16h | 3+ working case studies (payment, notification, inventory extraction) |
| FAQ | Writer | 8h | 15+ common Q&A |

**Total:** 88 hours (1 technical writer + 1 engineer)

---

### PRIORITY 4: Compliance & Marketplace (Week 4)

| Task | Owner | Effort | Criteria |
|------|-------|--------|----------|
| plugin.json update | Engineer | 2h | Command metadata, categories, tags |
| Error message audit | Engineer | 2h | Anthropic style guide compliance |
| Help text | Writer | 4h | Strangler command discoverability |
| Marketplace submission | PM | 4h | Complete checklist, review requirements |

**Total:** 12 hours (end of Week 4)

---

## THE COMPLETE CHECKLIST

### ✅ Already Done (Don't Redo)
- Codebase analysis engine (analyze_codebase.py)
- Multi-framework support (Django, FastAPI, Spring, Go, Node)
- Logging + versioning infrastructure
- Test fixtures + CI/CD pipeline
- 40+ helper modules (preview, TDD, review, etc.)
- Phase 2 REST API generation
- Phase 3 batch job generation

### ❌ Must Do Before v1.0 (Critical Path)

**WEEK 1 (Days 1-7):**
- [ ] Implement `/strangler-analyze` core logic
- [ ] Add feature detection to analyzer
- [ ] Add coupling analysis (tight/loose detection)
- [ ] Add difficulty scoring (RED/YELLOW/GREEN)
- [ ] Update SKILL.md with analyze section + 5 examples
- [ ] Write 8+ integration tests
- [ ] Test on real monolith (Django or Spring project)

**WEEK 2 (Days 8-14):**
- [ ] Implement `/strangler-extract` code generation
- [ ] Generate microservice code (Go first)
- [ ] Generate legacy adapter + database migration
- [ ] Generate Docker + K8s configs
- [ ] Generate integration tests + rollback procedures
- [ ] Update SKILL.md with extract section + 3 full examples
- [ ] E2E tests (analyze → extract → build → deploy)
- [ ] Test on real monolith

**WEEK 3 (Days 15-21):**
- [ ] Implement `/strangler-validate` + `/strangler-roadmap`
- [ ] Update all documentation (README, SKILL, QUICKSTART, troubleshooting)
- [ ] Create strangler examples (payment, notification, inventory)
- [ ] Anthropic compliance (plugin.json, help text, error messages)
- [ ] Security review + approval

**WEEK 4 (Days 22-28):**
- [ ] Final testing (all tests green)
- [ ] Performance validation (<30s, <2m)
- [ ] Marketplace submission
- [ ] Launch (v1.0.0 release)

### 🟡 Should Do (Can Defer to v1.1 with Documentation)
- SDLC processes (release management, code review, incident response)
- Enterprise security (audit logging, secrets management, RBAC)
- Production observability (metrics, tracing, health checks)
- Advanced deployment patterns (canary, blue-green, A/B testing)

---

## SUCCESS = THESE 4 THINGS WORKING

1. **`/strangler-analyze` Working** ✅ Can identify extractable features in real monoliths
2. **`/strangler-extract` Working** ✅ Can generate complete microservice that compiles and deploys
3. **E2E Workflow Proven** ✅ analyze → extract → build → test → deploy succeeds on real monolith
4. **Documentation Complete** ✅ No "coming soon" placeholders, all examples working

---

## RESOURCE MATH

```
Total Effort: 528 engineer-hours (2.2 FTE × 4 weeks)

Breakdown:
- Lead Engineer (strangler-analyze + strangler-extract): 160h
- Senior Engineer (code generation + E2E tests): 128h
- QA/Test (testing matrix + real project validation): 96h
- Technical Writer (documentation + examples): 80h
- Product Manager (roadmap + messaging): 48h
- Security (review + approval): 16h

Timeline: 4 weeks (aggressive but doable)
Start: Today (May 9)
Target Launch: May 31, 2026
```

---

## IF SOMETHING BREAKS (Contingency)

| Scenario | Mitigation | Timeline Impact |
|----------|-----------|-----------------|
| Strangler-extract too slow | Optimize analyzer, use caching | +2-3 days |
| Real monolith fails | Root cause analysis, adapt algorithm | +3-4 days |
| Marketplace approval delayed | Submit earlier (Week 3 instead of Week 4) | No impact |
| Security issues found | Fix immediately, re-review | +2-3 days |
| Performance fails | Profile, optimize hot paths | +3-4 days |

**Contingency Buffer:** 5 days built into 4-week timeline = 23-day runway

---

## ONE-PAGE SUMMARY FOR DECISION-MAKERS

### What You Have
✅ Solid code generation foundation (57 modules, 13K LOC)  
✅ Multi-framework support proven (Django, FastAPI, Spring, Go, Node)  
✅ Production infrastructure ready (logging, testing, CI/CD)  

### What You're Missing
❌ Strangler features (analyze, extract, validate, roadmap)  
❌ This is the $2.5B market opportunity (enterprise legacy modernization)  

### What It Takes to Launch
📋 4 weeks, 2.2 FTE, $50k-75k (loaded cost)  
📈 Result: Enterprise-focused product worth $50k-500k/year per customer  

### Bottom Line
**You have 95% of the technical foundation. The last 5% (strangler integration) is what unlocks the $2.5B market and differentiates you from Superpowers (which loses here).**

---

## NEXT ACTIONS (Today)

1. **Assign owners** — Lead engineer for analyze + extract, QA for testing, writer for docs
2. **Create sprint tasks** — Break checklist into daily deliverables
3. **Start strangler-analyze** — First task on critical path
4. **Identify 3 real monoliths** — For Week 1 testing
5. **Daily standups** — 15min sync, track blockers, adjust plan

---

**Owner:** Engineering Leadership  
**Last Updated:** 2026-05-09  
**Status:** Ready to execute  
**Confidence:** HIGH (path clear, resources identified, timeline aggressive but achievable)
