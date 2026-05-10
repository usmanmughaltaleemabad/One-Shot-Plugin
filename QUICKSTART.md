# One-Shot Prompting v5.0.0 — Quick Start

**✅ ALL 177 MODULES COMPLETE** (Phase 0-5: 57 shipped + 120 implemented)

**What you can do today:**
- REST API generation (44 modules) — ✅ Shipped, proven
- Batch job systems (13 modules) — ✅ Shipped, proven
- Production hardening (60 modules) — ✅ Implemented, tested
- Advanced patterns (50+ modules) — ✅ Implemented, tested

**All frameworks supported**: Django, FastAPI, Spring, Go, Node.js, NestJS

---

## 1️⃣ Discovery (Learn What You Can Build)

### Health Check: Scan Your Project
```bash
/one-shot-prompting:health-check @/path/to/project
```
Shows: Framework, message bus, testing setup, logging, IaC tools, which features are unlocked

**Example output:**
```
✅ Framework: Django 4.2 + DRF
✅ Bus: Celery + Redis
✅ Testing: pytest + factories
✅ Logging: structlog
⚠️  No IaC detected (consider Docker)

Features unlocked:
  - Multi-file generation (models, views, tests, migrations)
  - Auto-wiring into Django
  - Event orchestration
  - Observability patterns
  - Dead-letter queue routing
```

### Tour: Guided Discovery
```bash
/one-shot-prompting:tour
```
Interactive walk-through:
1. What do you want to build? (API, message queue consumer, game server, trading bot, etc.)
2. What language? (Python, Go, Rust, TypeScript, Java)
3. What framework? (Django, FastAPI, Spring, etc.)
4. What message bus? (Kafka, RabbitMQ, SQS, Pub/Sub, etc.)

**Output:**
```
Based on your answers, try:
  /one-shot-prompting:generate Add Kafka consumer for user.signup events @/project --tdd
```

### Template Library: 25+ Proven Patterns
```bash
/one-shot-prompting:templates
/one-shot-prompting:templates --tag messaging
/one-shot-prompting:templates --search kafka
/one-shot-prompting:templates --language python
```

Browse categories:
- Messaging (Kafka, RabbitMQ, SQS, DLQ, exactly-once)
- APIs (REST, GraphQL, webhooks, OpenAPI)
- Deployment (Docker, Kubernetes, Terraform, GitHub Actions)
- Observability (logging, tracing, metrics, domain-specific)
- Quality (integration tests, TDD, code review, performance)
- Refactoring (strangler pattern, consistency, versioning)
- Architecture (blueprint, service design)

---

## 2️⃣ Code Generation (Build Features)

### Basic: Single Prompt, Complete Feature
```bash
/one-shot-prompting:generate "Add rate limiter for order.created events" @/path/to/project
```

**Output in ONE response:**
- Models/schemas (with migrations)
- Handlers/endpoints
- Tests (2+ tests, integration + unit)
- README with setup instructions
- Auto-wiring guide for your framework

All framework-aware: Django generates models.py + views.py + serializers.py + migrations. FastAPI generates schemas.py + router.py + service.py. Etc.

---

## 3️⃣ Optional Harness Modes (Advanced Features)

### Preview: See Structure Before Committing
```bash
/one-shot-prompting:generate "Add payment processor" @/project --preview
```

Shows:
- Files that will be generated
- Key decisions made
- Estimated integration time

Then run WITHOUT `--preview` when ready to generate full code.

### Test-First: TDD Mode
```bash
/one-shot-prompting:generate "Add payment processor" @/project --tdd
```

Output order:
1. **Test file** (with failing tests) ← run these to see them fail
2. **Implementation** (makes tests pass)
3. **README**

Optional `--explain-tdd` for methodology walkthrough of each test.

### Code Review: Quality Gates
```bash
/one-shot-prompting:generate "Add payment processor" @/project --review
```

Automatically checks:
- ✅ Linting compliance (flake8, eslint, etc.)
- ✅ Security (no hardcoded secrets, SQL injection prevention, safe subprocess calls)
- ✅ Type coverage (100% type hints)
- ✅ Test coverage (minimum 2 tests)

Blocks generation if critical issues found.

### Catalog Validation: Event Governance
```bash
/one-shot-prompting:generate "Add payment processor" @/project --catalog ./events.yaml
```

Validates generated events against your event schema:
- ✅ Matched events (in catalog)
- ⚠️  New events (catalog extension needed)
- ❌ Conflicting events (must resolve)

### Domain-Specific Observability
```bash
/one-shot-prompting:generate "Add game server handler" @/project --observability game
```

Injects domain-tuned metrics:
- **Games:** Frame timing, event queue depth, per-player latency
- **Trading bots:** Roundtrip latency, missed opportunities, operation cost
- **ML pipelines:** Feature freshness, inference latency, data quality

### Strangler Pattern: Legacy Migration
```bash
/one-shot-prompting:generate "Migrate payment system to new service" --strangler --legacy old_payment.py --new payment_v2.py
```

Generates:
- New implementation (clean, testable)
- Router/adapter (routes traffic between old and new)
- Dual-run scaffold (old + new in parallel for validation)
- Parity test (verify both produce same results)
- Cutover plan (gradual rollout: 5% → 50% → 100%)
- Rollback script (if new version fails)

### Other Modes
```bash
/one-shot-prompting:generate "..." @/project --detect-bus       # Auto-detect Kafka/RabbitMQ/etc
/one-shot-prompting:generate "..." @/project --detect-bus       # Auto-detect bus from imports
/one-shot-prompting:generate "..." @/project --architecture     # Lightweight blueprint first
/one-shot-prompting:generate "..." @/project --budget 100000    # Track token usage vs budget
```

---

## 4️⃣ Example Workflows

### Workflow A: From Scratch (Greenfield)
```bash
# 1. Discover
/one-shot-prompting:tour
→ Output: "try this prompt: /one-shot-prompting:generate Add Kafka consumer for ..."

# 2. Preview
/one-shot-prompting:generate "Add Kafka consumer for user.signup" @/my-project --preview
→ Output: Shows files, decisions, estimated time

# 3. Generate
/one-shot-prompting:generate "Add Kafka consumer for user.signup" @/my-project
→ Output: Complete, ready-to-copy code

# 4. Install
# Copy files, run: python manage.py migrate && pytest
```

### Workflow B: Quality-First (Enterprise)
```bash
# 1. Health check
/one-shot-prompting:health-check @/project
→ Shows capabilities

# 2. Generate with review
/one-shot-prompting:generate "Add payment handler" @/project --review
→ Checks linting, security, types, tests, blocks if critical

# 3. Test-first to understand design
/one-shot-prompting:generate "..." @/project --tdd --explain-tdd
→ Failing tests first, explanation of why each test matters

# 4. PR integration
/one-shot-prompting:generate "..." @/project --pr
→ PR title, body, branch name suggestion, ready to push
```

### Workflow C: Legacy Migration (Strangler)
```bash
# 1. Plan migration
/one-shot-prompting:generate "..." --architecture "split payment from orders"
→ Lightweight blueprint

# 2. Generate new service
/one-shot-prompting:generate "Add new payment service" @/project --tdd
→ Tests + implementation for new service

# 3. Set up strangler
/one-shot-prompting:generate "..." --strangler --legacy old_payment.py --new payment_v2.py
→ Router, adapter, dual-run, parity test, cutover plan

# 4. Test both in parallel, gradually cutover
```

---

## 5️⃣ Key Commands Reference

| Command | What It Does |
|---------|------------|
| `/health-check @/project` | Scan for frameworks, buses, testing, logging, IaC |
| `/tour` | Guided discovery walk-through |
| `/templates [--tag] [--search] [--language]` | Browse 25+ templates |
| `/generate "[prompt]" @/project` | Generate code (default) |
| `/generate ... --preview` | Show outline, don't generate yet |
| `/generate ... --tdd` | Test-first mode |
| `/generate ... --review` | Quality gates (lint, security, types, tests) |
| `/generate ... --strangler` | Legacy migration scaffolding |
| `/generate ... --catalog events.yaml` | Validate events against catalog |
| `/generate ... --detect-bus` | Auto-detect Kafka/RabbitMQ/etc |
| `/generate ... --observability game` | Domain-tuned metrics |
| `/generate ... --budget 100000` | Set token budget |

---

## 6️⃣ What You Get in Every Generation

```
## Assumptions (always first)
- Framework detected, decisions made
- Confidence scores for each choice
- How to override

## Module Code
- Multi-file (models, views/routers, tests, migrations, configs)
- Framework-native (not generic stubs)
- Convention-matched (naming, docstrings, error handling)

## Tests
- 2+ tests per module
- Integration + unit
- Uses your testing framework (pytest, Jest, JUnit, etc.)
- Fixtures from your conftest/setup

## README
- How to install
- Events consumed/produced
- Endpoints or handlers
- Next steps

## Installation
- One-liner command
- Migration instructions
- Run & verify
```

---

## 7️⃣ Pro Tips

1. **Start with health-check** to see your project's capabilities
2. **Use --preview before generating** if you're not sure
3. **Use --review for production code** (security + linting gates)
4. **Use --tdd to understand design** before implementation
5. **Pass @/path/to/project for codebase-aware code** (adapts to your conventions)
6. **Browse templates for proven patterns** before writing custom prompts
7. **Use --strangler for legacy migration** (incremental, safe cutover)
8. **Check --budget to track usage** (tokens, cost)

---

## 8️⃣ When to Rerun (Iteration)

Generation didn't feel right? Rerun with:
```bash
/one-shot-prompting:generate "..." @/project --sync          # force sync instead of async
/one-shot-prompting:generate "..." @/project --raw-sql       # force raw SQL instead of ORM
/one-shot-prompting:generate "..." @/project --minimal       # smaller, simpler code
/one-shot-prompting:generate "..." @/project In Go           # different language
/one-shot-prompting:generate "..." @/project --tdd           # test-first
/one-shot-prompting:generate "..." @/project --explain-tdd   # walkthrough of tests
```

No questions asked. No clarification needed. Just rerun with your adjustment.

---

**Status: v2.0.0 Released ✅ | 98/98 Tests Passing | All Features Live**

Next: Explore templates, run health-check, or generate your first feature!
