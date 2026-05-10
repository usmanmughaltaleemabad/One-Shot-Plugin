# Strangler Pattern FAQ — v2.0.0

**Frequently asked questions and answers about the strangler migration pattern.**

---

## GENERAL QUESTIONS

### Q: What is the strangler pattern?

**A:** The strangler pattern is a safe way to migrate from a monolith to microservices **gradually**. Instead of replacing the entire system at once, you:

1. Extract one service at a time (smallest risk)
2. Route traffic gradually (5% → 25% → 50% → 100%)
3. Keep the old code as a fallback
4. Only remove legacy code when confident

This minimizes risk and allows incremental rollout.

---

### Q: Why not do a "big bang" rewrite?

**A:** Big bang rewrites are dangerous:
- ❌ High risk (entire system down if something breaks)
- ❌ Long timeline (months or years)
- ❌ Team distraction (can't ship features during rewrite)
- ❌ Bugs unknown until after cutover

The strangler pattern:
- ✅ Lower risk (one service at a time)
- ✅ Faster time-to-value (ship services weekly)
- ✅ Team productivity (ship features during migration)
- ✅ Parallel testing (old and new code side-by-side)

---

### Q: How long does it take to extract a service?

**A:** Depends on difficulty score:

| Difficulty | Time | Example |
|-----------|------|---------|
| GREEN | 3-7 days | Auth, email notification, logging |
| YELLOW | 2-3 weeks | Payment processing, order management |
| RED | 4-8 weeks | User management, core business logic |

**Typical monolith:** 8-12 weeks for complete migration.

---

### Q: What about data consistency during migration?

**A:** The generated code handles this with "dual-write" phase:

1. **Week 1-2:** Write to both old and new database
2. **Week 3:** Verify data parity (100% match)
3. **Week 4:** Cutover to new database only
4. **Week 5:** Retire old database

The generated migrations.sql script handles schema changes automatically.

---

### Q: Can we extract multiple services in parallel?

**A:** Yes, but:
- ✅ Extract GREEN services in parallel (low risk)
- ⚠️ Coordinate YELLOW services (shared dependencies)
- ❌ Don't extract RED services in parallel (too tightly coupled)

**Best practice:** Extract 1-2 services in parallel, not more.

---

## TECHNICAL QUESTIONS

### Q: Why is my analysis showing "no features found"?

**A:** The analyzer couldn't detect your monolith's framework.

**Solutions:**

1. Verify it's a supported framework:
   ```bash
   /one-shot-prompting:one-shot-generator health-check @/your/project
   ```

2. Force the framework explicitly:
   ```bash
   /one-shot-prompting:one-shot-generator analyze monolith @/app --framework django
   ```

3. Check directory structure (needs `manage.py` for Django, `pom.xml` for Spring, etc.)

---

### Q: What does "circular dependency" mean?

**A:** Two modules import each other:

```python
# payment.py
from users.auth import TokenManager  # imports users

# users.py  
from payment.models import Payment   # imports payment (circular!)
```

**What to do:**
- Extract both modules together as one service
- The generated code handles internal circular refs

```bash
/one-shot-prompting:one-shot-generator extract payment-auth \
  --modules payment,users \
  --language go
```

---

### Q: Analysis is slow. Why?

**Typical times:**
- 2.5K LOC: 0.34 seconds
- 10K LOC: 1-2 seconds
- 50K LOC: 6-8 seconds
- 100K LOC: 15-30 seconds

**If slower:**
1. Check CPU usage (might be IO-bound)
2. Try verbose mode to see where time is spent:
   ```bash
   /one-shot-prompting:one-shot-generator analyze @/app --verbose
   ```

3. For very large codebases, increase timeout:
   ```bash
   /one-shot-prompting:one-shot-generator analyze @/app --timeout=60
   ```

---

### Q: Generated code won't compile

**Solution steps:**

1. Check go.mod (missing dependencies):
   ```bash
   cd generated-payment
   go mod tidy
   ```

2. Verify database schema matches:
   ```bash
   cat migrations.sql  # Review what was extracted
   ```

3. Regenerate with verbose output:
   ```bash
   /one-shot-prompting:one-shot-generator extract payment --language go --verbose
   ```

4. Check error messages in stdout/stderr

If still broken, share the error with support.

---

### Q: Can I extract to languages other than Go/FastAPI?

**Currently:** Go and FastAPI only (v2.0.0)

**Coming soon (v2.0.1):** Spring Boot, NestJS, Node.js Express

**Workaround:** Extract as FastAPI first, then translate to your target language (usually straightforward).

---

### Q: How do I test the generated service?

**Generated code includes:**
- Integration tests (tests/integration_test.go or tests/test_service.py)
- Docker setup for local testing
- Example requests in README

**Run tests:**
```bash
cd generated-payment
go test ./...        # Go
pytest tests/        # FastAPI
```

**Local testing:**
```bash
docker-compose up
curl http://localhost:8080/health
```

---

### Q: What about database migrations?

**Generated `migrations.sql` includes:**

```sql
-- Extract payment tables from monolith
CREATE TABLE payment (
  id SERIAL PRIMARY KEY,
  amount DECIMAL(10, 2),
  status VARCHAR(50),
  ...
);

-- Dual-write setup (for testing phase)
CREATE TRIGGER sync_payment_on_update ...
```

**Apply migrations:**
```bash
psql -d your-db -f migrations.sql
```

---

## DEPLOYMENT QUESTIONS

### Q: How do we switch traffic from old to new service?

**The generated adapter handles this:**

**Django adapter (generated as adapter.py):**
```python
# In your Django app
from payment.adapters import PaymentRouter

# Gradual traffic shift
router = PaymentRouter(legacy_rate=95, new_rate=5)  # 95% old, 5% new

# API call
result = router.process_payment(amount, card)  # Routes based on percentage
```

**Week-by-week:**
- Week 1: 95% old, 5% new
- Week 2: 75% old, 25% new
- Week 3: 50% old, 50% new (fully dual-write)
- Week 4: 0% old, 100% new
- Week 5+: Remove legacy code

---

### Q: What's the rollback procedure?

**Each generated service includes rollback.sh:**

```bash
./rollback.sh  # Instant rollback to legacy service
```

**What it does:**
1. Removes new service from load balancer
2. Routes all traffic back to legacy code
3. Preserves database state (safe to retry)

**Time to rollback:** <1 minute

---

### Q: How do we handle database rollback?

**Dual-write phase protects you:**
1. New database has exact copy of old data
2. If issues found, just keep using old database
3. Both databases stay in sync during migration

**Manual rollback:**
```bash
# Stop writing to new database
UPDATE payment_sync SET enabled = false;

# Keep using old database
# Redeploy without the new service
```

---

### Q: Do we need downtime for cutover?

**No downtime required!**

The strangler pattern enables zero-downtime migration:
1. New service runs in parallel (weeks)
2. Traffic gradually shifts (5% → 100%)
3. Users don't notice anything (seamless)
4. Only risk is if new service is buggy (but we tested it first)

**Total downtime needed:** 0 minutes

---

## MONITORING & VALIDATION QUESTIONS

### Q: How do we validate the new service is correct?

**Three-stage validation:**

**Stage 1: Unit tests**
```bash
cd generated-service
go test ./...
```

**Stage 2: Integration tests** (generated code handles this)
```bash
./tests/integration_test.go  # Tests against both old and new
```

**Stage 3: Dual-write verification** (in production, during 50/50 traffic split)
```sql
SELECT COUNT(*) FROM payment_sync_log 
WHERE mismatch_detected = true;  -- Should be 0
```

---

### Q: What metrics should we monitor?

**Critical metrics to watch:**

| Metric | Target | Alert |
|--------|--------|-------|
| Error rate (5xx) | <0.1% | >1% |
| P95 latency | <200ms | >500ms |
| Database sync lag | <1s | >10s |
| Data parity % | 100% | <99.9% |

---

### Q: What if error rate spikes during migration?

**Automatic fallback:**

```
Error rate > 1% → Trigger rollback alert → On-call reviews → Automatic rollback if approved
```

**Process:**
1. Monitoring detects high error rate
2. Sends alert to on-call engineer
3. Engineer can approve instant rollback
4. Service reverts to legacy code automatically

**Time to fix:** <5 minutes

---

## COST & TIMELINE QUESTIONS

### Q: How much will this cost?

**Estimate using the roadmap command:**

```bash
/one-shot-prompting:one-shot-generator roadmap --from=analysis.json \
  --hourly-rate=150 \
  --team-size=3
```

**Typical costs:**

| Team Size | Duration | Cost |
|-----------|----------|------|
| 1 engineer | 6-12 months | $60-120K |
| 2 engineers | 4-6 months | $80-120K |
| 3 engineers | 3-4 months | $90-120K |

**ROI typically:** 18-24 months (ops savings, fewer bugs, faster shipping)

---

### Q: Can we do this part-time?

**Yes, but trade-offs:**

**Part-time (1 engineer 50%, others 0%):**
- Duration: 12-18 months
- Cost: Lower
- Risk: Higher (context switching)

**Full-time (2-3 engineers 100%):**
- Duration: 3-4 months
- Cost: Higher
- Risk: Lower (focused effort)

**Recommendation:** Start part-time for analysis, full-time for extractions.

---

### Q: Do we need to hire new engineers?

**No.** The generated code reduces complexity:
- ✅ Less to maintain during migration
- ✅ Services are smaller (easier to understand)
- ✅ Existing team can handle it

**But need:**
- ✅ DevOps support (Kubernetes, monitoring)
- ✅ QA support (testing generated code)
- ✅ Product owner (prioritization)

---

## BEST PRACTICES

### Q: What's the best extraction order?

**Answer:** By difficulty score

```
1. Extract all GREEN services first (weeks 1-4)
   - Builds team confidence
   - Establishes patterns
   - Low risk

2. Extract YELLOW services (weeks 5-12)
   - More complex
   - Team experienced
   - Medium risk

3. Extract RED services last (weeks 13+)
   - Most critical
   - Team expertise highest
   - Still manageable risk
```

---

### Q: Should we use the generated code as-is or customize it?

**Answer:** Customize it!

The generated code is a **starting point**, not final:
- ✅ Customize business logic
- ✅ Add error handlers
- ✅ Integrate with monitoring
- ✅ Add feature flags
- ❌ Don't change core architecture (that works)

**Time to customize:** 1-2 weeks per service (included in YELLOW/RED estimates)

---

### Q: How do we document the migration?

**Generated code includes:**
- README.md (how to build/run)
- API documentation (endpoints)
- Migration notes (what changed)

**You should add:**
- Timeline (when each service launches)
- Runbook (how to respond to incidents)
- Architecture diagram (updated with new services)
- Lessons learned (after each extraction)

---

## SUPPORT & GETTING HELP

### Q: Something went wrong. Who do I contact?

**Support channels:**

1. **Check FAQ** (this document)
2. **Check Reference** (STRANGLER_REFERENCE.md)
3. **Check User Guide** (STRANGLER_USER_GUIDE.md)
4. **Run health check:**
   ```bash
   /one-shot-prompting:one-shot-generator health-check @/project
   ```
5. **Contact support:** musman.mughal@taleemabad.com

---

### Q: Can you help us with a specific migration?

**Yes!** We offer consultation:
- Architecture review
- Timeline estimation
- Risk assessment
- Training for your team

Contact: musman.mughal@taleemabad.com

---

### Q: How do we report bugs or request features?

**Bug report:** Include:
- Your monolith framework
- Size (LOC)
- Error message
- Steps to reproduce

**Feature request:** Include:
- What feature
- Why you need it
- Your timeline

Contact: musman.mughal@taleemabad.com

---

## GLOSSARY

**Adapter:** Code that translates between old and new services during migration

**Coupling:** How tightly services depend on each other (score 0-10)

**Dual-write:** Writing to both old and new database during migration for verification

**Feature:** Extractable module or group of modules

**Monolith:** Single large application (opposite of microservices)

**Rollback:** Reverting to legacy code if something goes wrong

**Strangler:** Design pattern for incremental system replacement

**Traffic shift:** Gradually moving traffic from old to new service

---

**Last Updated:** May 10, 2026  
**Version:** 2.0.0
