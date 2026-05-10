# Implementation Priority: Legacy Strangler First

**Decision Date:** 2026-05-09  
**Status:** Strategic pivot approved  
**Next Action:** Build /strangler-analyze MVP  

---

## Strategic Decision: NOT Building CRUD

### What We're Abandoning
- ❌ `/add-standard-crud` endpoint generation
- ❌ Generic "create CRUD endpoints" skill
- ❌ Competition with Superpowers/gstack on CRUD

### Why
1. **Superpowers already won** CRUD market (native, proven, $50/month)
2. **gstack already won** scaffolding (pre-fab, easy, $99/month)
3. **You can't beat them** at commoditized features (you'd be me-too)
4. **Users don't need automation** for CRUD (manual is 10 min, not 2 hours)
5. **Strangler is uncontested** ($2.5B TAM, zero competitors)

### The Math
- CRUD market: $100-200M (dominated by 5+ competitors)
- Strangler market: $2.5-10B (zero competitors, high barriers to entry)
- Your positioning: "Third-place CRUD tool" vs "Only Strangler Tool"

**Decision:** Own the $2.5B niche instead of fighting for $100M commodity.

---

## What We're Building Instead: STRANGLER-FIRST ROADMAP

### Tier 1: Must-Build (Next 2-3 Weeks)

#### [CRITICAL] `/strangler-analyze` Skill
**Objective:** Given a monolith, identify which features can be extracted.

**Deliverables:**
- ✅ Extend `analyze_codebase.py` with feature detection
  - Identify functions/models/views by feature
  - Measure coupling (internal vs external dependencies)
  - Detect database boundaries
  - Calculate extraction difficulty scores

- ✅ Create SKILL.md section: "Strangler Analysis"
  - Input: codebase path
  - Output: Extraction candidates ranked by ease
  - Markup: Clear risk assessment (RED/YELLOW/GREEN)

- ✅ Test on 3 real monoliths
  - Django monolith (Python)
  - Spring monolith (Java)
  - Go monolith (Go)

**Success Criteria:**
- Can identify 5+ extractable features in a 400k+ LOC monolith
- Ranking matches human architect assessment (ask real architect)
- Output is actionable (clear next steps)
- Runs in < 30 seconds

**LOC Estimate:** 500-800 (both analyzer + SKILL.md)

---

#### [CRITICAL] `/strangler-extract` Skill (Payment Service First)
**Objective:** Generate a complete microservice to replace one feature from monolith.

**Deliverables:**
- ✅ Microservice code (Go first, FastAPI second)
  - REST API (GET /payments/:id, POST /payments)
  - Database schema + ORM
  - Error handling + validation
  - Integration with external API (Stripe, etc.)

- ✅ Legacy adapter code
  - Python/Node/Java wrapper that old code calls
  - Maintains old interface, calls new service
  - Fallback to old code if new service fails

- ✅ Database migration script
  - Safe extraction (no data loss, no downtime)
  - Backfill logic (cross-database lookups)
  - Verification queries

- ✅ Event schema + async handlers
  - Define events published by service
  - Kafka/RabbitMQ producer code
  - Example event consumers

- ✅ Docker + Kubernetes manifests
  - Dockerfile (production-ready)
  - K8s deployment (with health checks, scaling)
  - ConfigMaps for env variables

- ✅ Integration tests
  - Test new service directly
  - Test old code calling new service
  - Test fallback if new service fails
  - Test data consistency

- ✅ Rollback procedure
  - Step-by-step how to rollback if extraction fails
  - Safety gates (canary, circuit breaker)
  - Validation before full cutover

**Test with Payment Feature:**
1. Analyze a real Django/Spring/Go monolith
2. Identify payment service
3. Generate extraction
4. Build, deploy, test
5. Create before/after comparison

**Success Criteria:**
- Generated code compiles/runs without errors
- Payment service talks to old code via adapter
- Tests pass (new service, fallback, data consistency)
- Deployment to staging K8s works
- Integration tests verify no data loss

**LOC Estimate:** 1,000-1,500 (service code + wiring + tests)

---

### Tier 2: Build-Out (Weeks 3-6)

#### `/strangler-validate` Skill
**Objective:** Pre-flight safety checks before extraction.

**Validates:**
- ✅ Can we extract this without breaking other services?
- ✅ Are there any data consistency risks?
- ✅ How many sync transactions span this boundary?
- ✅ Is it possible to fail gracefully?

**Output:**
- RED/YELLOW/GREEN assessment
- Specific risks + mitigations
- "Ready to extract?" recommendation

**LOC Estimate:** 300-500

---

#### `/strangler-roadmap` Skill
**Objective:** Generate full 12-24 month modernization plan.

**Generates:**
- Phased extraction plan (which features in what order)
- Timeline + resource requirements
- Investment needed
- Expected payoff (productivity, uptime, scaling)

**Outputs:**
- Excel/PDF roadmap
- Weekly/monthly milestones
- Risk assessment per phase
- Consulting recommendations

**LOC Estimate:** 400-600

---

#### Support for 3+ Services
**Instead of just payment, also handle:**
- Notifications
- Inventory  
- User profiles
- Reporting

**Effort:** Reuse payment patterns, ~20% additional LOC per service

---

### Tier 3: Market (Weeks 6-8)

#### Create Case Study: Real Monolith Extraction
**Objective:** Prove the tool works end-to-end.

**Choose one:**
- Django-based e-commerce (open source: Saleor, Oscar, etc.)
- Spring Boot SaaS (open source: Jira clone, etc.)
- Go microservices that started as monolith

**Document:**
- Before: Monolith size, features, structure
- Extraction: What we extracted, how long
- After: Independent service, metrics, ROI

**Publish:**
- Blog post: "How We Extracted Payment from Django Monolith in 2 Days"
- Code repo: GitHub (full working example)
- Video: 10-min walkthrough of extraction

**Impact:**
- Proves tool works
- Shows real ROI (2 days → normally takes 2 weeks)
- Marketing asset (case study, blog, video)

---

### What We're NOT Building (In Priority Order)

#### ❌ CRUD Endpoint Generation
**Why:** Superpowers, gstack, ChatGPT all do this. You'd be third-place.  
**Opportunity Cost:** 1 week of engineering that could be spent on Strangler.  
**ROI:** Low (commoditized, $0 premium pricing).  
**Decision:** SKIP.

#### ❌ React/Vue/Angular Component Generation
**Why:** 15 competitors, visual/interactive hard for LLMs, 50% rework rate.  
**Opportunity Cost:** 2-3 weeks (Phases 5 had 50+ components).  
**ROI:** None (features Phase 5 does not differentiate One-Shot).  
**Decision:** SKIP. (Keep existing code for reference, don't market it.)

#### ❌ Generic Scaffolding
**Why:** Every framework has built-in scaffolding (startproject, generate, etc.).  
**Opportunity Cost:** 1 week.  
**ROI:** Zero (nobody pays for scaffolding).  
**Decision:** SKIP.

---

## Why This Order Works

### Why Build /strangler-analyze First
- Foundational (all other strangler skills depend on it)
- Proves "we understand the monolith" (key claim)
- Can run independently (users get value immediately)
- Fast feedback (can test against real codebases)
- De-risks the entire strangler approach

### Why Build /strangler-extract Second
- Proves we can do the hard part (code generation)
- Provides working example (case study)
- Builds on analyze output (natural progression)
- Shows ROI (2 days vs 2 weeks)

### Why Validate & Roadmap Third
- Users want to know "is it safe?" before extracting
- Need full plan before committing to modernization
- Lower urgency than analyze + extract

---

## Implementation Timeline

| Phase | Weeks | Deliverables | Status |
|-------|-------|--------------|--------|
| **1: MVP** | 2-3 | `/strangler-analyze`, `/strangler-extract` (payment) | Next |
| **2: Build-Out** | 3-6 | `/strangler-validate`, `/strangler-roadmap`, 3+ services | Planned |
| **3: Case Study** | 6-8 | Full working example + blog/video/code | Planned |
| **4: Market** | 8-12 | Partner with consulting firms, pitch to enterprises | Planned |
| **5: Scale** | 12+ | Additional services, support more frameworks, premium SaaS | Planned |

**Total Time to Market:** 8-12 weeks (2-3 months)

---

## Success Metrics

### Tier 1: Technical (MVP)
- ✅ /strangler-analyze identifies 5+ extractable features
- ✅ /strangler-extract generates working payment service
- ✅ Generated code compiles/runs
- ✅ Integration tests pass
- ✅ Data migration is safe + verified

### Tier 2: Market (Case Study)
- ✅ End-to-end extraction works (analyze → extract → deploy)
- ✅ Case study shows clear ROI
- ✅ Code + blog + video published
- ✅ First enterprise inquiry (proof of interest)

### Tier 3: Revenue (SaaS)
- ✅ $50k-500k/year pricing model
- ✅ First 2-3 enterprise customers
- ✅ $1M ARR target (top quartile for most SaaS)

---

## What We're Committing To

### Build
- ✅ Strangler-first skills (analyze, extract, validate, roadmap)
- ✅ Support 5+ extractable services (payment, notification, inventory, etc.)
- ✅ Support 3 frameworks (Django, Spring, Go initially; Node, FastAPI later)
- ✅ Enterprise-grade tooling (safety checks, rollback, monitoring)

### Market
- ✅ Position as "legacy modernization specialist" (not generic app builder)
- ✅ Focus on enterprises (not startups)
- ✅ Premium pricing ($50k-500k/year, not $50/month)
- ✅ Consulting partnerships (Deloitte, Accenture, etc.)

### Don't Build
- ❌ CRUD endpoint generation (Superpowers owns it)
- ❌ UI component generation (15 competitors own it)
- ❌ Generic scaffolding (every framework does it)
- ❌ "One-shot CRUD tool that competes with Superpowers"

---

## Next Action

**START HERE:** Build `/strangler-analyze`

1. Extend `analyze_codebase.py` with feature detection
2. Create SKILL.md section for strangler analysis
3. Test against real Django/Spring/Go monoliths
4. Get feedback from real architects

**Timeline:** Start this week, MVP in 2-3 weeks.

---

**Decision Owner:** Strategic Leadership  
**Decision Date:** 2026-05-09  
**Approval:** ✅ Approved for implementation  
**Next Review:** After /strangler-analyze MVP
