# CLAUDE.md — Developer Guide for one-shot-prompting Plugin

This file is for developers contributing to or maintaining this plugin.
For user documentation, see [README.md](README.md).
For version history, see [CHANGELOG.md](CHANGELOG.md).
For strategic roadmap, see `FUTURE_PLAN.md` (local only, gitignored).

---

## Plugin Architecture

This is a **Claude Code plugin** — a SKILL.md-based prompt skill. No Python code
runs at plugin invocation time. The correct mental model:

```
User invokes skill
  → ! injection block runs analyze_codebase.py (shell subprocess)
  → Script output injected into SKILL.md prompt
  → Claude reads context + instructions, generates code
```

**Key files:**
```
one-shot-prompting/
├── .claude-plugin/plugin.json              ← marketplace metadata
├── CLAUDE.md                               ← this file (developer context)
├── README.md                               ← user-facing documentation
├── CHANGELOG.md                            ← version history
├── FUTURE_PLAN.md                          ← strategic roadmap (LOCAL, gitignored)
└── skills/
    └── one-shot-generator/
        ├── SKILL.md                        ← all generation logic (Claude instructions)
        └── scripts/
            └── analyze_codebase.py         ← codebase analyzer (runs via ! injection)
```

The `src/` directory and Python library approach were removed in v0.6.0.
All logic lives in SKILL.md sections or `scripts/analyze_codebase.py`.

---

## How to Test Locally

```bash
# Install plugin from local directory
claude --plugin-dir /path/to/one-shot-prompting

# Test skill invocation (generic)
/one-shot-prompting:one-shot-generator add a kafka consumer for order.placed events in Go

# Test with codebase analysis
/one-shot-prompting:one-shot-generator add user auth endpoint @/path/to/django-project

# Test the analyzer script directly
python skills/one-shot-generator/scripts/analyze_codebase.py "add auth @/tmp/test_django"
```

---

## Implementation Status (Current Reality — May 11, 2026)

| Phase | Status | Modules | LOC | Release | Notes |
|-------|--------|---------|-----|---------|-------|
| 0 | ✅ Shipped | 4 | 475 | v0.6.1 | Silent planning, verification, slash commands |
| 1 | ✅ Shipped | 8 | 2,050 | v0.7.0 | Multi-file formatting, migrations, DI, config |
| 2 | ✅ Shipped | 44 | 8,900 | v2.0.0 | REST API generation (CRUD, auth, webhooks, tests) |
| 3 | ✅ Shipped | 13 | 3,586 | v2.0.0 | Batch job systems (queues, monitoring, observability) |
| 4 | ⏸️ Planned | 60 | 0 | v3.0.0 | NOT IMPLEMENTED — PHASE_4_IMPLEMENTATION_PLAN.md missing |
| 5 | ⏸️ Planned | 50+ | 0 | v4.0.0 | NOT IMPLEMENTED — PHASE_5_IMPLEMENTATION_PLAN.md missing |
| **Total** | **39% COMPLETE** | **69/177** | **~16.5k** | **v2.0.0** | Phases 0-3 shipped; Phases 4-5 not started |

**Reality**: 69 modules actually implemented (~16,500 LOC). ROADMAP.md contains aspirational plans for Phases 4-5 but code doesn't exist.

---

## How the ! Injection Works

In `SKILL.md`:
```
```!
python "./scripts/analyze_codebase.py" "$ARGUMENTS"
```
```

- `./scripts/analyze_codebase.py` — relative path to script (runs from skill directory)
- `$ARGUMENTS` — full user argument string (e.g., "add user auth @/path/to/project")
- Script output is injected into the prompt before Claude processes it
- Script must be fast (<2s) and output <500 tokens

---

## Contribution Guidelines

1. **SKILL.md is the source of truth** for generation logic. Keep sections clearly labeled.
2. **analyze_codebase.py must have zero external dependencies** — only Python stdlib.
3. **Never add Python library code** in `src/` — this is not how plugins work.
4. **Update CHANGELOG.md** for every version bump.
5. **Keep FUTURE_PLAN.md updated** (local only) for roadmap decisions.
6. **Bump plugin.json version** before any marketplace submission.

---

## Version Bump Workflow

```bash
# 1. Update version in .claude-plugin/plugin.json
# 2. Add entry to CHANGELOG.md
# 3. Add "What's New" section to README.md if major feature
# 4. Update this CLAUDE.md implementation status table
# 5. Commit and push
git add .
git commit -m "feat: v0.6.0 — large codebase support (10 pieces)"
git push origin main
```

---

## Post-v2.0.0 Roadmap

**Phase 4-5 (Critical Features NOT YET IMPLEMENTED)** — Q3-Q4 2026:
- Production hardening (DDD, CQRS, Event Sourcing, TDD, cost optimization, chaos engineering, compliance)
- Advanced patterns (microservices, real-time, GraphQL, ML pipelines, legacy modernization)
- See [ROADMAP.md](ROADMAP.md) for detailed Phase 4-5 specifications

**Phase 6.0.0+ (Future Market Enhancements)** — v6.0.0+:
- Advanced bus auto-detection (asyncio vs Tokio vs NestJS event bus optimization)
- Event catalog enforcement (catalog-first generation with validation)
- Multi-language SDK generation (TypeScript, Python, Go SDKs from schemas)
- Domain-specific marketplace templates (fintech, gaming, healthcare, logistics)
- Custom framework support (custom backends, proprietary patterns)

See `FUTURE_PLAN.md` (local, gitignored) for strategic planning details.

---

## Current Status (May 11, 2026 — CORRECTED)

⚠️ **69 MODULES SHIPPED (39% of roadmap goal) — Phase 4-5 NOT IMPLEMENTED**

- **Phase 0-3 (69 modules)**: Shipped and proven ✅
  - ✅ Phase 0: Silent planning engine, verification harness, slash commands (v0.6.1)
  - ✅ Phase 1: Multi-file formatting, migrations, DI, framework config (v0.7.0)
  - ✅ Phase 2: REST API generation (44 modules, v2.0.0)
  - ✅ Phase 3: Batch job systems (13 modules, v2.0.0)

- **Phase 4-5 (110 modules)**: NOT IMPLEMENTED ❌
  - ✗ Phase 4: Planned (60 modules) — PHASE_4_IMPLEMENTATION_PLAN.md does NOT exist
    - No code for Architecture Design, TDD, Cost Optimization, Chaos Engineering, Compliance
  - ✗ Phase 5: Planned (50+ modules) — PHASE_5_IMPLEMENTATION_PLAN.md does NOT exist
    - No code for Microservices, Real-time, GraphQL, ML Pipelines, Legacy modernization

**Reality**: ROADMAP.md contains the aspirational plan, but Phases 4-5 were never implemented. Previous claims of "81 Django files tested" refer to theoretical examples, not actual working code.

---

**Maintained by:** Claude Code Agent  
**Last updated: 2026-05-11


