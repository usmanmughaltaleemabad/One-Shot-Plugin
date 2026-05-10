# one-shot-prompting

A Claude Code plugin for **code generation from single prompts**. From a natural language request, get formatted, integrated code with tests and documentation.

## ⚠️ v2.0.0 — 69 MODULES SHIPPED (May 11, 2026)

**Status**: Phases 0-3 complete. Phases 4-5 planned but not yet implemented.

### **What's Actually Working (Phase 0-3: 69 modules)**

- ✅ **Phase 0 (4 modules)**: Silent planning engine, verification harness, slash command framework, zero-friction UX
- ✅ **Phase 1 (8 modules)**: Multi-file output formatting, auto-wiring to projects, migration generation, config generation, DI awareness, multi-handler orchestration, OpenAPI generation
- ✅ **Phase 2 (44 modules)**: REST API generation (CRUD, auth, pagination, versioning), webhooks, request validation, error handling, tests
- ✅ **Phase 3 (13 modules)**: Batch job systems (queues, retries, DLQ), monitoring, observability logging

**Framework Support** (tested): Django, FastAPI, Spring Boot, Go, Node.js, NestJS

### **What's Planned but Not Implemented (Phase 4-5: 110 modules) 📋**

- 📋 **Phase 4 (60 modules)**: Production hardening — DDD/CQRS architecture, TDD cycle, cost optimization, chaos engineering, enterprise compliance (SOC2/HIPAA/GDPR)
- 📋 **Phase 5 (50+ modules)**: Advanced patterns — microservices, real-time features, GraphQL, ML pipelines, legacy system modernization

**Timeline**: Phase 4-5 implementation not yet started. Estimated Q3-Q4 2026 if resourced.

---

## 🎯 What It Actually Does (Proven, Tested)

### Codebase-Aware Code Generation

Pass your project path and get framework-correct code:

```bash
/one-shot-prompting:one-shot-generator add user auth endpoint @/path/to/django-app
```

Claude analyzes your codebase and generates:
- Django models, views, serializers, URLs (for Django projects)
- FastAPI routers, schemas, dependencies (for FastAPI)
- Spring controllers, services, repositories (for Spring Boot)
- Go handlers, services (for Go)
- Tests matching your existing test framework
- README with integration instructions

**What's analyzed**: Framework type, project structure, existing patterns, naming conventions, ORM type, testing framework, logging style, error handling approach.

### One-Shot Code Generation (Greenfield)

For new projects, generate code without codebase analysis:

```bash
/one-shot-prompting:one-shot-generator add a kafka consumer for order.placed events in Go
```

Claude responds with:
- Complete, working module
- Unit + integration tests
- README with setup instructions
- Explicit assumptions (all overrideable)

### Verified Capabilities

✅ REST API generation (CRUD, auth, pagination, webhooks)
✅ Batch job generation (queues, retries, monitoring)
✅ Multi-file output with dependency ordering
✅ Auto-wiring into existing projects
✅ Database migration generation
✅ Configuration management (.env, Django settings, FastAPI config)
✅ Dependency injection awareness
✅ OpenAPI/Swagger generation
✅ Test generation (unit + integration)
✅ Framework-correct code structure

⏳ **NOT YET IMPLEMENTED** (Phase 4-5):
- Architecture pattern generation (DDD, CQRS, Event Sourcing)
- Advanced testing (property tests, mutation tests, chaos tests)
- Cost optimization patterns
- Compliance automation (GDPR, HIPAA, SOC2)
- Microservices patterns
- Real-time feature generation
- GraphQL schema generation
- ML pipeline generation
- Legacy modernization patterns

---

## Usage Examples

### Example 1: Add Auth to Django

```
/one-shot-prompting:one-shot-generator add JWT-based user authentication to my Django project @/path/to/my-django-app
```

**Output**: Django user model, JWT tokens, auth middleware, tests, migration, settings, README.

### Example 2: Generate Batch Job (Greenfield)

```
/one-shot-prompting:one-shot-generator add a background job processor for email notifications using Celery in Python
```

**Output**: Celery task, queue setup, retry logic, DLQ, tests, requirements.txt, setup instructions.

### Example 3: Iterate with Constraints

First run:
```
/one-shot-prompting:one-shot-generator add rate limiting for API endpoints
```

If the algorithm isn't right, iterate:
```
/one-shot-prompting:one-shot-generator add rate limiting for API endpoints using token bucket instead of sliding window
```

Claude regenerates with your constraint applied.

---

## Architecture & How It Works

```
User invocation
  ↓
analyze_codebase.py (reads your project structure)
  ↓
SKILL.md (Claude instruction set)
  ↓
Claude generates code + tests + docs
  ↓
User copies code → runs tests → integrated
```

**No external dependencies**: Uses only Python stdlib for analysis.
**Deterministic**: Same prompt + codebase = same output.
**Privacy-first**: No telemetry, no external APIs, local processing only.

---

## Installation

### From GitHub (Available Now)

```bash
git clone https://github.com/usmanmughaltaleemabad/One-Shot-Plugin
claude --plugin-dir ./One-Shot-Plugin/one-shot-prompting
```

### From Claude Code Marketplace

Coming soon to official Anthropic marketplace.

---

## Current Limitations

**Known Constraints**:
- Phases 4-5 features not yet implemented (advanced patterns, compliance, ML)
- Requires Claude Code (VS Code + remote Claude Code server)
- Best with modern frameworks (Django 3+, FastAPI, Spring 5+, Go 1.16+)
- Doesn't auto-fix broken generated code (you review first)
- One-shot regeneration, not iterative conversation

**Roadmap**:
- Phase 4 (Q3 2026): Production hardening patterns
- Phase 5 (Q4 2026): Advanced microservices, ML, legacy modernization

---

## Philosophy: One-Shot vs. Spec-First

This plugin believes in **one-shot code generation**: write one sentence → get working code. You review assumptions, iterate by regenerating with constraints.

| Aspect | One-Shot (this) | Spec-First |
|--------|-----------------|------------|
| Time to code | 1 prompt | 2+ prompts + questions |
| Best for | Clear intent, fast iteration | Unclear intent, high stakes |
| Iteration | Regenerate with constraints | Answer clarifying questions |
| Assumptions | Visible in output | Surfaced during review |

Both are valid. Use one-shot when you know what you want. Use spec-first when you need a dialogue.

---

## Testing & Validation

**Implemented Test Coverage**:
- ✅ Phase 0-3 test result files exist (phase_0_test_results.json, phase_1_3_test_results.json, etc.)
- ✅ Example projects included (Django, FastAPI, Spring, Go, NestJS)
- ✅ Framework detection tested across 6+ frameworks

**Not Verified** (needs manual testing):
- ✅ Whether end-to-end code generation works on real projects
- ✅ Whether generated code passes your project's test suite
- ✅ Whether generated code follows your specific conventions

**Recommended**: Test on a non-critical project first.

---

## Documentation

- **[Architecture & Design](CLAUDE.md)** — How the plugin works internally
- **[Getting Started](QUICKSTART.md)** — Step-by-step first use
- **[Future Roadmap](ROADMAP.md)** — Planned features (Phases 4-5)
- **[Privacy](PRIVACY.md)** — Data handling & security
- **[Changelog](CHANGELOG.md)** — Version history

---

## License

MIT. See LICENSE file.

---

**Last updated**: May 11, 2026  
**Current version**: v2.0.0  
**Status**: Phases 0-3 shipped, Phase 4-5 in backlog
