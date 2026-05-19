# 🚀 One-Shot Prompting v2.0.0 — Start Here

**Status:** ⚠️ **Phases 0-3 Complete (69 modules)** | Phases 4-5 Planned (110 modules)

Phases 0-3 are shipped and tested. Phases 4-5 are planned for Q3-Q4 2026 but not yet implemented.

---

## What You Can Do Now (Shipping Today)

### ✅ REST API Generation
Generate complete REST APIs with models, views, tests, and migrations.

```bash
/one-shot-prompting:one-shot-generator add user authentication endpoint @/path/to/project
```

**What's included**: Models, serializers, views, URL routing, tests, migrations, README.

**Frameworks supported**: Django, FastAPI, Spring Boot, Go, Node.js, NestJS

### ✅ Batch Job Generation
Generate background jobs, task queues, and event handlers.

```bash
/one-shot-prompting:one-shot-generator add background job for sending emails @/project
```

**What's included**: Job handler, queue config, retry logic, DLQ handling, tests.

### ✅ Multi-File Generation
Automatically splits complex features into organized files with proper imports.

### ✅ Auto-Wiring
Generated code automatically integrates into your existing project structure.

### ✅ Framework Detection
Analyzes your codebase and generates framework-specific code (not generic stubs).

---

## Quick Navigation

| If You Want | Go Here | Command |
|-------------|---------|---------|
| Fast start (5 min) | [QUICKSTART.md](QUICKSTART.md) | `/one-shot-prompting:one-shot-generator /health-check @/project` |
| Learn all features | [README.md](README.md) | Start with `/health-check` |
| See architecture | [CLAUDE.md](CLAUDE.md) | Read developer guide |
| Understand roadmap | [ROADMAP.md](ROADMAP.md) | See Phase 4-5 plans |
| Generate code | [QUICKSTART.md](QUICKSTART.md) | `/one-shot-prompting:one-shot-generator "add feature" @/project` |

---

## Three Workflows

### 🎯 Workflow 1: Explore Your Project

```bash
/one-shot-prompting:one-shot-generator /health-check @/path/to/project
```

Claude scans your project and shows:
- ✅ Framework detected
- ✅ Message bus (Kafka, RabbitMQ, etc.)
- ✅ Testing framework
- ✅ What code you can generate

### 🎯 Workflow 2: Generate a Feature

```bash
# Preview what will be generated
/one-shot-prompting:one-shot-generator "add user profile endpoint" @/project --preview

# Generate the code
/one-shot-prompting:one-shot-generator "add user profile endpoint" @/project

# Copy into your project, run tests
```

### 🎯 Workflow 3: Iterate Until Right

```bash
# First try
/one-shot-prompting:one-shot-generator add rate limiter

# Different algorithm?
/one-shot-prompting:one-shot-generator add rate limiter using token bucket

# Different language?
/one-shot-prompting:one-shot-generator add rate limiter in Go
```

Just rerun with your constraint. No questions, no conversation.

---

## What's Actually Implemented

### Phase 0 ✅
- Silent planning engine
- Verification harness
- Slash command framework
- Zero-friction UX

### Phase 1 ✅
- Multi-file output formatting
- Auto-wiring to projects
- Migration generation
- Config generation
- Dependency injection awareness
- OpenAPI generation

### Phase 2 ✅
- REST API generation (CRUD, auth, webhooks, pagination)
- Request validation
- Error handling
- Tests (unit + integration)

### Phase 3 ✅
- Batch job generation
- Queue handling
- Retries and DLQ
- Monitoring patterns
- Observability logging

### Phase 4 & 5 📋
- Architecture patterns (DDD, CQRS, Event Sourcing)
- Advanced testing (property tests, mutation tests, chaos tests)
- Production hardening (cost optimization, chaos engineering, compliance)
- Advanced patterns (microservices, real-time, GraphQL, ML, legacy modernization)

**Status**: Not yet started. Planned for Q3-Q4 2026.

---

## Examples

### Example 1: Add Auth to Django

```bash
/one-shot-prompting:one-shot-generator add JWT-based user authentication @/my-django-project
```

**Output**:
- User model with JWT
- Serializer
- Views/endpoints
- URL routing
- Tests
- Migration
- Settings updates
- README

### Example 2: Generate Celery Task

```bash
/one-shot-prompting:one-shot-generator add celery task for processing orders with retry logic @/project
```

**Output**:
- Task definition
- Queue configuration
- Retry logic
- DLQ routing
- Tests
- setup.py requirements
- README

### Example 3: Test-Driven Development

```bash
/one-shot-prompting:one-shot-generator add payment handler @/project --tdd
```

**Output**:
1. Test file (with failing tests)
2. Implementation (makes tests pass)
3. README

---

## Status Summary

**Shipped (v2.0.0)**:
- ✅ 69 modules across Phases 0-3
- ✅ 6 frameworks supported
- ✅ Multi-file generation
- ✅ Auto-wiring
- ✅ Framework detection
- ✅ Test generation

**In Backlog (Phase 4-5)**:
- 📋 110 additional modules
- 📋 Architecture patterns
- 📋 Advanced testing
- 📋 Production hardening
- 📋 Microservices & real-time
- 📋 ML pipelines
- 📋 Legacy modernization

**Timeline**: Phase 4-5 estimated Q3-Q4 2026 (not yet started).

---

## Installation

```bash
git clone https://github.com/usmanmughaltaleemabad/One-Shot-Plugin
claude --plugin-dir ./One-Shot-Plugin/one-shot-prompting
```

Then try:
```bash
/one-shot-prompting:one-shot-generator /health-check @/path/to/your/project
```

---

## Next Steps

1. **Install** the plugin (see above)
2. **Run health-check** on your project
3. **Try generating** a simple REST API or batch job
4. **Review** the generated code
5. **Read [QUICKSTART.md](QUICKSTART.md)** for detailed workflows

---

**Version**: v2.0.0 (May 11, 2026)  
**Status**: Phases 0-3 shipped. Phases 4-5 planned.  
**Frameworks**: Django, FastAPI, Spring, Go, Node.js, NestJS
