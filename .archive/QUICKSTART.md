# One-Shot Prompting v2.0.0 — Quick Start

**Status**: Phases 0-3 shipped (69 modules). Phases 4-5 planned but not yet implemented.

**What works right now:**
- ✅ REST API generation (44 modules) — Proven, tested
- ✅ Batch job systems (13 modules) — Proven, tested
- ✅ Multi-file output formatting, auto-wiring, migrations
- ✅ Codebase analysis and framework detection

**Coming later (Q3-Q4 2026):**
- 📋 Production hardening patterns (DDD, CQRS, TDD, cost optimization, chaos, compliance)
- 📋 Advanced patterns (microservices, real-time, GraphQL, ML, legacy modernization)

**Frameworks supported**: Django, FastAPI, Spring Boot, Go, Node.js, NestJS

---

## Getting Started

### 1. Install the Plugin

```bash
git clone https://github.com/usmanmughaltaleemabad/One-Shot-Plugin
claude --plugin-dir ./One-Shot-Plugin/one-shot-prompting
```

### 2. Check Your Project's Capabilities

```bash
/one-shot-prompting:one-shot-generator /health-check @/path/to/project
```

This analyzes your codebase and shows:
- Framework & version detected
- Message bus (if any)
- Testing framework
- Logging setup
- What code you can generate

**Example output:**
```
✅ Framework: Django 4.2 + DRF
✅ Bus: Celery + Redis
✅ Testing: pytest + factories
✅ Logging: structlog
✅ Deployment: Docker + GitHub Actions

Capabilities unlocked:
  - REST API generation (models, views, serializers, tests, migrations)
  - Batch job generation (tasks, retries, DLQ routing)
  - Multi-file output with auto-wiring
  - OpenAPI documentation
```

### 3. Generate Your First Feature

**For your existing project** (codebase-aware):
```bash
/one-shot-prompting:one-shot-generator add user authentication with JWT @/path/to/project
```

Claude analyzes your project and generates:
- Models/schemas
- Views/endpoints
- Tests (unit + integration)
- Migrations
- Settings configuration
- README

**For a new feature** (greenfield):
```bash
/one-shot-prompting:one-shot-generator add a kafka consumer for order.placed events in Python
```

---

## Available Features (Phase 0-3)

### ✅ REST API Generation
```bash
/one-shot-prompting:one-shot-generator add a user endpoint with JWT auth and rate limiting @/project
```

Generates:
- Models/schemas
- Views/routers
- Serializers/schemas
- URL routing
- Tests (unit + integration)
- Migrations

All framework-native (no generic stubs).

### ✅ Batch Job Generation
```bash
/one-shot-prompting:one-shot-generator add a background job to send emails asynchronously @/project
```

Generates:
- Task/job handler
- Queue configuration
- Retry logic
- Dead-letter queue (DLQ) handling
- Tests
- Setup instructions

### ✅ Multi-File Generation
Automatically splits large features into multiple files:
- Models file
- Views/routers file
- Tests file
- Utilities file
- Configuration file
- Each file is generated with correct imports and structure

### ✅ Auto-Wiring into Projects
Generated code automatically:
- Imports your project's settings/config
- Uses your existing models/schemas
- Integrates with your testing framework
- Follows your naming conventions
- Uses your ORM/query patterns

### ✅ Migration Generation
For data models, Claude generates database migrations:
- Django migrations (makemigrations)
- Alembic migrations
- Flyway SQL migrations
- Go migrate SQL files

---

## Generation Modes

### Preview Mode
See what will be generated before committing:
```bash
/one-shot-prompting:one-shot-generator "add payment handler" @/project --preview
```

Shows:
- Files that will be created
- Key design decisions
- Estimated integration time

### Test-First (TDD) Mode
Generate tests first, then implementation:
```bash
/one-shot-prompting:one-shot-generator "add payment handler" @/project --tdd
```

Output order:
1. Test file (with failing tests)
2. Implementation (makes tests pass)
3. README

### Code Review Mode
Automatic quality checks before generation:
```bash
/one-shot-prompting:one-shot-generator "add payment handler" @/project --review
```

Checks:
- ✅ Linting (flake8, eslint, etc.)
- ✅ Security (no hardcoded secrets, SQL injection prevention)
- ✅ Type coverage (100% type hints)
- ✅ Test coverage (minimum 2 tests)

Blocks if critical issues found.

---

## Iteration Example

First attempt:
```bash
/one-shot-prompting:one-shot-generator add a rate limiter for API requests
```

If you want a different algorithm:
```bash
/one-shot-prompting:one-shot-generator add a rate limiter for API requests using token bucket instead of sliding window
```

If you want to change languages:
```bash
/one-shot-prompting:one-shot-generator add a rate limiter for API requests in Go
```

No conversation. Just rerun with your constraint. Claude regenerates from scratch.

---

## Example Workflows

### Workflow 1: Add Feature to Existing Project

```bash
# 1. Check what you can generate
/one-shot-prompting:one-shot-generator /health-check @/my-django-app

# 2. Preview the output
/one-shot-prompting:one-shot-generator add user profile endpoint @/my-django-app --preview

# 3. Generate
/one-shot-prompting:one-shot-generator add user profile endpoint @/my-django-app

# 4. Copy code into your project
# Copy output to your Django app directory

# 5. Run tests
pytest

# 6. Apply migrations (if generated)
python manage.py migrate
```

### Workflow 2: Generate from Scratch (Greenfield)

```bash
# Generate a complete Celery task handler
/one-shot-prompting:one-shot-generator add a celery task to send email notifications in Python

# Copy into your project
# Create requirements.txt entry (Claude includes it)
# Run tests and integrate
```

### Workflow 3: Test-Driven Development

```bash
# Generate tests first
/one-shot-prompting:one-shot-generator add payment processing API --tdd @/project

# See test output
# Understand the design through tests
# Implementation follows
```

---

## What You Get in Each Generation

### 1. Assumptions Section
- Framework detected
- Design choices explained
- Confidence scores
- How to override

### 2. Code
- Multiple files (organized by responsibility)
- Framework-native patterns
- Your project's conventions
- Well-formatted and documented

### 3. Tests
- 2+ tests per module
- Unit + integration tests
- Uses your testing framework
- Imports from your conftest/fixtures

### 4. README
- Installation instructions
- What was generated
- How to integrate
- Next steps

### 5. Auto-Integration Guide
- Where to copy files
- What to import
- Settings to update (if any)
- How to verify it works

---

## Common Patterns

### REST Endpoint with Auth
```bash
/one-shot-prompting:one-shot-generator add user profile endpoint with JWT authentication @/project
```

### Background Job with Retries
```bash
/one-shot-prompting:one-shot-generator add background job to process orders with retry logic @/project
```

### Event Consumer
```bash
/one-shot-prompting:one-shot-generator add kafka consumer for order.placed events with error handling @/project
```

### Batch Migration
```bash
/one-shot-prompting:one-shot-generator add database migration for denormalizing user data @/project
```

---

## Troubleshooting

**"I don't have a codebase to analyze"**
→ Just use the basic syntax without `@/path`. Claude generates generic, framework-specific code.

**"The generated code doesn't match my style"**
→ Rerun with a constraint: "use async/await", "use raw SQL instead of ORM", "add error logging", etc.

**"I want a different language"**
→ Rerun with "In Go" or "In Rust" or "In TypeScript".

**"The test doesn't cover my edge case"**
→ Rerun with "--tdd" to see the test first, then adjust.

---

## Important Limitations

**Phases 4-5 NOT YET AVAILABLE** (coming Q3-Q4 2026):
- ❌ Architecture pattern generation (DDD, CQRS, Event Sourcing)
- ❌ Advanced testing (property tests, mutation tests, chaos tests)
- ❌ Production hardening (cost optimization, compliance, chaos engineering)
- ❌ Advanced patterns (microservices, real-time, GraphQL, ML, legacy modernization)

**What's tested and verified**:
- ✅ Phases 0-3 code generation
- ✅ 6 frameworks (Django, FastAPI, Spring, Go, Node.js, NestJS)
- ✅ REST API + Batch job generation

**What you should test**:
- Your specific edge cases
- Your project's deployment process
- Your team's coding standards

**Recommendation**: Test on a non-critical feature first.

---

## Next Steps

1. **Install** the plugin (see above)
2. **Run health-check** on your project to see capabilities
3. **Generate** a simple feature (REST endpoint or batch job)
4. **Review** the generated code
5. **Iterate** if anything feels off
6. **Integrate** into your project

For more details, see:
- **[Full Documentation](README.md)** — Comprehensive guide
- **[Architecture](CLAUDE.md)** — How it works internally
- **[Roadmap](ROADMAP.md)** — What's coming in Phase 4-5

---

**Status**: v2.0.0 shipped | Phases 0-3 complete | Phases 4-5 planned
