# ONE SHOT PLUGIN (Claude Code Studio)

**Agentic one-shot code generation for existing codebases.** Claude conducts a 7-stage pipeline of deterministic scanners + specialist agents (architect, implementer, test-author, reviewer, wirer, critic) to take a natural-language feature request and ship verified, FK-aware, cost-gated code into your project. Multi-entity, relationship-aware, with a free templated fallback for CI use.

## ⭐ v3.5.0 — Agentic Restructure (Tier 3.5)

**Status**: Architecture pivoted from Python regex templates → Claude (the model) for code generation. Deterministic muscles stay in Python; reasoning moves to the agentic layer.

```bash
# Primary entry point (agentic) — Claude reasons, scripts execute
/one-shot "shopping cart with line items and discounts" @./my-project

# With cost gate
/one-shot "..." @./my-project --budget=0.30

# Actually mutate the project (default is dry-run)
/one-shot "..." @./my-project --apply

# Free fallback (zero Claude tokens, deterministic templates)
/one-shot "..." @./my-project --templated
```

### What you get for `/one-shot "shopping cart with line items and discounts"`

- Multi-entity extraction: 3 entities + relationships (`has_many`)
- Codebase scan: detects FastAPI, existing models, import contracts
- Architect agent: produces `spec.json` (entities, FKs, API surface, test contract)
- Implementer agents (parallel, one per file, **Haiku** for cost): write models / schemas / routers
- Test-author agent (independent, reads only spec): writes tests that match the contract
- Reviewer agent: security / perf / style gate
- Static verifier + auto-patch: catches and fixes 4 deterministic bug classes (401-drift, pagination-drift, placeholder-leak, broken-imports)
- Wirer: adds `app.include_router(...)` to your `main.py` (dry-run by default)
- Critic agent: runs `pytest` against generated code; verdicts ship-or-loop
- All recorded as a bead in `.beads/failures.jsonl` so future sessions learn

**Cost: ~$0.30–0.80 per generation on the Sonnet-for-reasoners + Haiku-for-file-writers mix.** Free if you pass `--templated`.

### Framework support

Agentic path: **FastAPI** (full). **Django, Spring, Go, Node, NestJS** route through the spec but use the templated fallback for code emission (cross-language scaffold variants queued).

Templated fallback path: all 6 frameworks, 99 phase generators.

---

## 🏗️ Architecture

The plugin is a **Claude Code plugin proper** — skills, commands, and agents as first-class units; scripts as deterministic helpers the agents call.

```
commands/                            ← User entry points
  one-shot.md                          ⭐ /one-shot — primary agentic
  (14 legacy commands)                  generate, plan, tdd, debug, ...

skills/                              ← Claude reads SKILL.md and acts
  one-shot-generate/SKILL.md           ⭐ Tier 3.5 agentic playbook
  one-shot-generator/SKILL.md          legacy templated fallback
  write-plan, execute-plan, tdd-cycle, systematic-debug, verify-before-complete

.claude/agents/                      ← Specialists invoked via Task
  architect.md       (sonnet) — designs spec.json
  implementer.md     (haiku)  — writes ONE file per spawn
  test-author.md     (sonnet) — independent of implementer
  reviewer.md        (sonnet) — security/perf/style gate
  wirer.md           (haiku)  — integrates into main.py
  critic.md          (sonnet) — runs pytest, verdicts

skills/one-shot-generator/scripts/   ← Deterministic tools
  scan, graph, diff, verify, auto-patch, auto-wire,
  critic-runner, live-critic, beads, curriculum,
  cross-feature-consistency, self-improvement, scaffold_planner, cost_budget
```

See [docs/tier35-agentic.md](docs/tier35-agentic.md) for the full architectural narrative; the other tier docs (`tier1`, `tier2`, `tier25`, `tier3`) cover the foundations.

---

## 🚀 Get Started in 30 Seconds

```bash
# 1. Install
git clone https://github.com/usmanmughaltaleemabad/One-Shot-Plugin
claude --plugin-dir ./One-Shot-Plugin/one-shot-prompting

# 2. Generate your first feature
/one-shot "add a shopping cart with line items and discounts" @./your-project

# 3. Review the dry-run wire plan, then ship
/one-shot "..." @./your-project --apply
```

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

### Shipped Features (Code Complete)

✅ REST API generation (CRUD, auth, pagination, webhooks)  
✅ Batch job generation (queues, retries, DLQ handling, monitoring)  
✅ Multi-file output with dependency ordering  
✅ Auto-wiring into existing projects  
✅ Database migration generation (Django, Alembic, Flyway, Go)  
✅ Configuration management (.env, Django settings, FastAPI BaseSettings, Spring YAML)  
✅ Dependency injection awareness (Spring @Autowired, FastAPI Depends, Go wire)  
✅ OpenAPI/Swagger documentation generation  
✅ Test generation (unit + integration tests)  
✅ Framework-correct code structure (no generic stubs)  

### Verified & Production-Ready (Phases 0-3)

✅ Code generation across Django, FastAPI, Spring Boot, Go, Node.js, NestJS  
✅ Framework detection & analysis  
✅ Multi-file output with proper structure  
✅ Test generation (unit + integration)  
✅ Migration generation  
✅ Async/await patterns  

### Code Complete, Deployment Pending (Phases 4-5)

✅ **Phase 4 Code**: 49 modules, 18.7k LOC (DDD, CQRS, event sourcing, compliance)  
✅ **Phase 5 Code**: 16 modules, 8.4k LOC (microservices, real-time, GraphQL, ML)  

🚧 **Pending**: Enterprise sales motion, real-world validation, compliance certification

**Recommendation**: 
- **Immediate** (Phase 0-3): REST APIs, batch jobs, migrations, webhooks
- **Near-term** (Phase 4): Enterprise patterns (after sales team & customer validation)
- **Future** (Phase 5): Advanced microservices & integrations (after enterprise market proves demand)

### Phase 4-5 Features (Now Implemented)

✅ Architecture pattern generation (DDD, CQRS, Event Sourcing, Sagas)  
✅ TDD cycle enforcement (test-first code generation)  
✅ Cost optimization patterns (token tracking, budget enforcement)  
✅ Compliance automation (GDPR, HIPAA, SOC2 audit trails)  
✅ Microservices patterns (service mesh, API gateways, service discovery)  
✅ Real-time feature generation (WebSockets, GraphQL subscriptions, SSE)  
✅ GraphQL schema generation (with resolvers and subscriptions)  
✅ Legacy modernization (strangler pattern, blue-green deployments)  
✅ Distributed tracing (Jaeger, Zipkin, X-Ray)  
✅ Feature flags & configuration management

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

**Known Constraints (v2.0.0)**:
- **Requires Claude Code** — VS Code + Claude Code server (plugin runs inside Claude, not standalone)
- **Modern frameworks only** — Django 3+, FastAPI 0.100+, Spring 5+, Go 1.16+, Node 16+
- **Manual review required** — Generated code is for review, not auto-deployment
- **One-shot generation** — Regenerate with constraints instead of iterative back-and-forth
- **Phase 4-5 complexity** — Enterprise patterns (DDD, CQRS) are available but designed for larger teams

**Not Limitations (Addressed)**:
- ✅ Multi-file output (implemented in Phase 1)
- ✅ Framework-aware generation (implemented in Phase 0)
- ✅ Test generation (implemented in Phase 2)
- ✅ Async/await patterns (implemented throughout)
- ✅ Privacy-first (local processing only, zero telemetry)

## Tier 2 Execution Status

### ✅ COMPLETE
- Phase 0-3 code (73 modules, 13.5k LOC) — Proven, tested, production-ready
- Phase 4-5 code (65 modules, 27k LOC) — Implemented, awaiting enterprise deployment
- Marketplace backend (Phase 3a) — FastAPI + PostgreSQL + Stripe integration
- GitHub Actions workflows — Security, lint, testing automated
- Documentation & guides — 15 essential docs + archival system

### 🚧 PENDING
- **Phase 3b**: Marketplace frontend (Next.js web UI for agent discovery)
- **Phase 3c**: CLI commands (search, install, publish, analytics)
- **Phase 3d**: Marketplace launch & monetization (June-July 2026)
- **Phase 4**: Enterprise sales motion (SAML/OAuth, compliance, support team)
- **Phase 5**: Advanced integrations & optimization (real-world validation)

## Phase 3 Roadmap (Months 6-12)

**Phase 3a: Backend** ✅ COMPLETE
- Agent discovery & publishing API (FastAPI)
- Creator dashboard backend
- Stripe billing integration (70/30 split)
- Rating & analytics system

**Phase 3b-3d: Frontend, CLI, Launch** 🚧 IN PROGRESS (6-12 weeks)
- Next.js marketplace UI (agent list, search, detail, creator dashboard)
- CLI commands (search, install, publish, analytics)
- Marketplace soft launch with 50-100 beta agents
- 500+ agents target by end of Phase 3
- 50-100k paying teams target
- $2-5M ARR target

## Phase 4-5 Roadmap (Months 12-24)

**Enterprise Motion** (M12-18):
- SAML/OAuth SSO
- SOC2/GDPR/HIPAA compliance
- Premium enterprise agents
- Sales-driven growth

**Scale & Optimize** (M18-24):
- Performance analytics
- A/B testing framework
- Strategic integrations
- Exit preparation ($300-600M acquisition target)

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

**What's Been Tested**:
- ✅ Phase 0-3 code generation across 6+ frameworks
- ✅ Framework detection (Django, FastAPI, Spring, Go, Node.js, NestJS)
- ✅ Test result files exist for Phase 0-3 (phase_0_test_results.json, phase_1_3_test_results.json, etc.)
- ✅ Example projects included as reference

**What You Should Test Before Production**:
- Test on a non-critical feature in your project
- Verify generated code compiles and passes your test suite
- Confirm generated code follows your team's style and conventions

**Note**: We haven't verified it works on *every* project type yet. Real-world feedback will help us improve.

---

## Documentation

**Strategic Docs**:
- **[Execution Status](EXECUTION_STATUS_MAY_2026.md)** — Phase 3a complete, Phases 3b-5 roadmap, $300-600M acquisition strategy
- **[Tier 2 Master Roadmap](TIER2_MASTER_ROADMAP.md)** — 24-month vision, market analysis, defensibility moat
- **[Tier 2 Execution Plan](TIER2_EXECUTION_PLAN.md)** — How to execute from launch to acquisition

**Technical Docs**:
- **[Implementation Status](IMPLEMENTATION_STATUS.md)** — Complete breakdown of 177 modules across all phases
- **[Phase 3a Backend Complete](PHASE3A_BACKEND_COMPLETE.md)** — Marketplace platform launch status
- **[Architecture & Design](CLAUDE.md)** — How the plugin works internally

**Getting Started**:
- **[Quickstart](QUICKSTART.md)** — 30-second setup
- **[START_HERE.md](START_HERE.md)** — New user guide

**Reference**:
- **[Roadmap](ROADMAP.md)** — Long-term vision
- **[Privacy](PRIVACY.md)** — Data handling & security
- **[Security](SECURITY.md)** — Vulnerability reporting
- **[Support](SUPPORT.md)** — Getting help
- **[Changelog](CHANGELOG.md)** — Version history

---

## 🤝 Support & Contact

### Report Issues or Ask Questions
- **GitHub Issues**: [usmanmughaltaleemabad/One-Shot-Plugin/issues](https://github.com/usmanmughaltaleemabad/One-Shot-Plugin/issues)
- **Email**: musman.mughal@taleemabad.com
- **Response Time**: Best-effort, typically within 24-48 hours

### Feature Requests
Please open a GitHub issue with the label `feature-request` describing your use case.

### Community
Join discussions on GitHub or email the maintainer directly.

---

## 🔒 Security

### Reporting Vulnerabilities
If you discover a security vulnerability, **please do not open a public GitHub issue**. Instead:

1. Email musman.mughal@taleemabad.com with:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact

2. We will investigate and provide a fix within 7 days

3. Once fixed, we'll credit you in the security advisory (if desired)

### Security Best Practices
- Plugin processes all code locally — no external APIs called
- No telemetry or data collection
- Open source — audit the code yourself: [github.com/usmanmughaltaleemabad/One-Shot-Plugin](https://github.com/usmanmughaltaleemabad/One-Shot-Plugin)
- Dependencies: Python stdlib only (zero external packages)

### Data Retention
- Plugin generates code in your local Claude Code instance
- Generated code is **not stored** on any remote server
- Claude Code itself may store chat history per Anthropic's policies
- See [PRIVACY.md](PRIVACY.md) for details

---

---

## License

MIT. See LICENSE file.

---

**Last updated**: May 17, 2026  
**Current version**: v2.0.0 (Tier 2 - Harness + One-Shot)  
**Status**: Phase 3a complete (backend), Phases 3b-3d in progress, 177 modules, 75k+ LOC  
**Next Milestone**: Phase 3 marketplace launch (June 2026), $2-5M ARR target
