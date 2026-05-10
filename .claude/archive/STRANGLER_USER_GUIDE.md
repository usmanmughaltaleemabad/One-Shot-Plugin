# Strangler Pattern User Guide — v2.0.0

**Learn how to incrementally modernize your monolith using the strangler pattern.**

---

## OVERVIEW

The strangler pattern helps you migrate from a monolith to microservices **gradually and safely**. Instead of a risky "big bang" rewrite, you extract services one at a time, route traffic gradually, and only remove legacy code when you're confident.

**The OneShot strangler feature automates this process in 4 steps:**

1. **Analyze** — Identify what can be extracted (feature extraction)
2. **Extract** — Generate microservice boilerplate code
3. **Validate** — Pre-flight safety checks before deployment
4. **Plan** — 12-24 month extraction timeline with costs

---

## QUICK START: 5 MINUTES

### Step 1: Analyze Your Monolith

```bash
/one-shot-prompting:one-shot-generator analyze monolith @/path/to/django-project --strangler
```

**Output:**
- Markdown table showing extractable features
- Difficulty scores (GREEN = easy, YELLOW = medium, RED = hard)
- Recommended extraction order (easiest first)
- JSON data for programmatic use

**Example Output:**

```
[EXTRACTABLE FEATURES] (7 found)

| Feature | Modules | Coupling | Difficulty | Score |
|---------|---------|----------|------------|-------|
| payment |   3     |  5.2/10  |  YELLOW    | 6/10  |
| auth    |   2     |  2.1/10  |  GREEN     | 9/10  |
| notification | 4  |  7.1/10  |  RED       | 3/10  |
```

### Step 2: Extract a Service

```bash
/one-shot-prompting:one-shot-generator extract payment --language go @analysis-result
```

**Generated Files:**
- Go service code (main.go, service.go, handler.go, go.mod)
- Legacy adapter (Python middleware for gradual traffic routing)
- Database migrations (SQL extraction scripts)
- Docker configs (Dockerfile, docker-compose.yml)
- Kubernetes manifests (deployment, service, ingress)
- Integration tests + rollback procedures

### Step 3: Validate Safety

```bash
/one-shot-prompting:one-shot-generator validate payment --dry-run
```

**Checks:**
- Library compatibility (go.mod conflicts)
- Data consistency (migration risks)
- API compatibility (adapter coverage)
- Configuration (secrets, env vars)
- Performance (coupling analysis)

### Step 4: Plan Timeline

```bash
/one-shot-prompting:one-shot-generator roadmap --from=analysis
```

**Generates:**
- 12-24 month extraction plan
- Feature prioritization (GREEN → YELLOW → RED)
- Team allocation (engineers per phase)
- Financial analysis (investment, payoff, ROI)
- Traffic migration schedule (5% → 25% → 50% → 100%)

---

## FULL WORKFLOW EXAMPLE

### Scenario: Extract Payment Service from Django E-Commerce Monolith

**Initial State:**
- Django monolith: 50K LOC, 8 modules (payment, users, inventory, shipping, notifications, reviews, analytics, admin)
- Goal: Extract payment to standalone Go microservice
- Timeline: 8-week migration

**Week 1: Planning**

```bash
# Analyze the entire monolith
/one-shot-prompting:one-shot-generator analyze monolith @/app --strangler --json > monolith-analysis.json

# Review the analysis
cat monolith-analysis.json
```

**Output shows:**
- Payment module: GREEN (easy to extract, low coupling)
- Recommendation: Extract payment first

**Week 2-3: Code Generation**

```bash
# Extract payment service
/one-shot-prompting:one-shot-generator extract payment --language go --from=monolith-analysis.json

# Output: 11 files ready to build
ls generated-payment-service/
  ├── main.go                    # Entry point
  ├── service.go                 # Business logic
  ├── handler.go                 # HTTP handlers
  ├── go.mod                     # Dependencies
  ├── Dockerfile                 # Container build
  ├── docker-compose.yml         # Local dev
  ├── k8s-deployment.yaml        # Kubernetes
  ├── k8s-service.yaml
  ├── adapter.py                 # Django adapter
  ├── migrations.sql             # Data extraction
  └── tests/
      ├── integration_test.go
      └── rollback.sh
```

**Week 4: Safety Validation**

```bash
# Run pre-flight checks
/one-shot-prompting:one-shot-generator validate payment --service=generated-payment-service

# Output: All green (safe to deploy)
[VALIDATION COMPLETE] 5/5 categories PASS
- Library Compatibility: GREEN
- Data Consistency: GREEN
- Interface Breaking: GREEN
- Configuration: GREEN
- Performance: GREEN
```

**Week 5-6: Deployment & Testing**

```bash
# Build and test locally
cd generated-payment-service
go build
./payment-service --port=8080

# Test against synthetic data
go test ./...
# Result: 45 tests passing

# Deploy to staging
kubectl apply -f k8s-deployment.yaml -n staging

# Verify in staging
curl http://payment.staging:8080/health
# Response: {"status":"healthy"}
```

**Week 7: Gradual Traffic Migration**

```bash
# Week 7: Route 5% of production traffic to new service
# Django adapter: payment/adapters.py (generated)
# Traffic split: 95% legacy, 5% new

# Monitor metrics
# - New service error rate: 0.1% (acceptable)
# - Latency: 50ms (acceptable)

# Week 7.5: Expand to 25%
# Error rate: 0.05% (good)
# Latency: 48ms (better)

# Week 8: Full cutover to 100%
# Run parallel writes for 1 week to verify data parity
# All metrics green

# Remove legacy payment code from Django
# Deploy final cutover
```

**Week 8 Result:**
- Payment service now independent microservice
- Legacy code removed
- 8-week migration complete, zero incidents

---

## DIFFICULTY SCORES EXPLAINED

### GREEN (Easy to Extract)

**Characteristics:**
- <3.0 external coupling (loose dependencies)
- <5 functions (small scope)
- No circular dependencies
- Clear interfaces

**Examples:**
- Authentication service
- Email notification service
- Product catalog

**Recommendation:** Start here. Low risk, fast extraction.

### YELLOW (Medium Difficulty)

**Characteristics:**
- 3.0-6.0 external coupling (moderate dependencies)
- 5-15 functions (medium scope)
- Some shared data models
- Multiple entry points

**Examples:**
- Payment processing
- Order management
- Shipping calculation

**Recommendation:** Extract after GREEN features. Plan 2-3 weeks per service.

### RED (Complex Extraction)

**Characteristics:**
- >6.0 external coupling (tightly coupled)
- >15 functions (large scope)
- Circular dependencies
- Scattered across codebase

**Examples:**
- User management (often used by everything)
- Core business logic
- Admin features

**Recommendation:** Extract last. Plan 4-8 weeks per service. Consider phased approach.

---

## FRAMEWORK SUPPORT

### Supported Source Frameworks (Analyzers)

- **Django** (Python, most tested)
- **FastAPI** (Python)
- **Spring Boot** (Java)
- **Go** (standard library, Gin, Echo)
- **NestJS** (Node.js/TypeScript)

### Supported Target Languages (Extractors)

- **Go** (HTTP services, fastest)
- **FastAPI** (Python async services)
- Coming: Spring Boot, NestJS, Node.js Express

### Database Support

- **PostgreSQL**
- **MySQL**
- **MongoDB**
- **SQLite** (dev only)

---

## ADVANCED SCENARIOS

### Scenario 1: Extracting Circular Dependencies

**Problem:** Payment module imports Users, Users imports Payment (circular reference)

**Solution:** Extract together as a "payment-auth" service

```bash
/one-shot-prompting:one-shot-generator extract payment-auth \
  --modules payment,users \
  --language go
```

**Result:** Both modules extracted as unified service, circular dependency resolved internally.

---

### Scenario 2: Large Monolith (100K+ LOC)

**Problem:** Analyzer takes 15-30 seconds on very large codebase

**Solution:** Analyze in parts or use caching

```bash
# Option 1: Analyze just payment module
/one-shot-prompting:one-shot-generator analyze monolith @/app/payment --strangler

# Option 2: Use cache (v2.0.1+)
/one-shot-prompting:one-shot-generator analyze monolith @/app --cache=latest
```

---

### Scenario 3: Phased Extraction Timeline

**Large Monolith Roadmap (e.g., 50 modules):**

```
Phase 1 (Weeks 1-4):   Extract 3 GREEN services (auth, email, logging)
Phase 2 (Weeks 5-12):  Extract 4 YELLOW services (payment, inventory, shipping, analytics)
Phase 3 (Weeks 13-24): Extract 2 RED services (users, core-business-logic)
Result: 9 microservices, monolith retired
```

---

## TROUBLESHOOTING

### Q: "No features found"

**Cause:** Directory structure not recognized as Django/Spring/etc.

**Solution:**
```bash
# Verify framework detection
/one-shot-prompting:one-shot-generator health-check @/path

# If framework not detected, specify explicitly
/one-shot-prompting:one-shot-generator analyze monolith @/path --framework django
```

### Q: "Circular dependency detected"

**Cause:** Two or more modules import each other.

**Solution:** Extract together

```bash
/one-shot-prompting:one-shot-generator extract module-a,module-b --language go
```

### Q: "Analysis slow (>10 seconds)"

**Cause:** Very large codebase (>100K LOC)

**Solution:** Analyze subset or enable caching

```bash
# Analyze just one module
/one-shot-prompting:one-shot-generator analyze monolith @/app/payment

# Or increase timeout
/one-shot-prompting:one-shot-generator analyze monolith @/app --timeout=60
```

### Q: "Generated code won't compile"

**Cause:** Missing dependencies or syntax errors

**Solution:** Check go.mod and fix imports

```bash
cd generated-service
go mod tidy
go build
```

If issues persist, regenerate with verbose output:
```bash
/one-shot-prompting:one-shot-generator extract service --verbose --language go
```

---

## BEST PRACTICES

### 1. Start with GREEN (Easy) Services
- Lower risk, faster delivery
- Builds team confidence
- Establishes patterns for YELLOW/RED services

### 2. Use Dry-Run Before Real Deployment
```bash
/one-shot-prompting:one-shot-generator validate service --dry-run
```

### 3. Test Adapters Thoroughly
- Legacy adapter code routes traffic
- Bugs here cause production issues
- Write integration tests for adapter

### 4. Monitor Metrics Continuously
- Error rates
- Latency
- Data consistency (dual-write phase)

### 5. Keep Rollback Ready
```bash
# Each generated service includes rollback.sh
./rollback.sh  # Revert to legacy if needed
```

### 6. Document Extraction Process
- Keep record of what was extracted
- Document configuration changes
- Record timeline and costs

---

## FAQ

**Q: How long does a typical extraction take?**
A: GREEN services (3-7 days), YELLOW services (2-3 weeks), RED services (4-8 weeks)

**Q: Can we extract multiple services in parallel?**
A: Yes, but coordinate to avoid conflicts. Start with GREEN services that don't share dependencies.

**Q: What if extraction fails?**
A: Use generated rollback.sh script to revert to legacy behavior instantly.

**Q: How do we handle data consistency during migration?**
A: Generated code includes dual-write adapter. New service writes to both old and new databases for verification period.

**Q: What about testing?**
A: Generated code includes integration tests. Run them against both legacy and new service to verify parity.

---

## NEXT STEPS

1. **Analyze your monolith** — See what's extractable
2. **Plan extraction** — Use roadmap command to build timeline
3. **Extract first GREEN service** — Lowest risk, fast learning
4. **Deploy & monitor** — Use adapter for gradual traffic shift
5. **Repeat** — Move to next service in recommended order

---

**Need help?**
- FAQ: See section above
- Issues: Check troubleshooting
- Support: Contact musman.mughal@taleemabad.com

---

**Version:** 2.0.0  
**Last Updated:** May 10, 2026
