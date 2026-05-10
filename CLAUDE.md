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

## Implementation Status — v0.6.0-Foundation (10 Pieces)

| # | Piece | Implementation | Status |
|---|-------|----------------|--------|
| 1 | Codebase Analyzer | `scripts/analyze_codebase.py` | ✅ DONE |
| 2 | Context Extraction | `scripts/analyze_codebase.py` output format | ✅ DONE |
| 3 | Integration Adapter | SKILL.md "Framework-Specific Generation Patterns" | ✅ DONE |
| 4 | Dependency Resolver | SKILL.md "Dependency Awareness" | ✅ DONE |
| 5 | Convention Matcher | SKILL.md "Convention Matching" | ✅ DONE |
| 6 | Test Integration | SKILL.md "Test Integration" | ✅ DONE |
| 7 | Migration Generator | SKILL.md "Migration Generation" | ✅ DONE |
| 8 | API Consistency | SKILL.md "API Consistency" | ✅ DONE |
| 9 | Documentation | SKILL.md "Documentation" | ✅ DONE |
| 10 | Deployment Context | SKILL.md "Deployment Context" | ✅ DONE |

All 10 pieces complete as of v0.6.0.

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

## Next Phase: v0.7.0+ (after v0.6.0 marketplace approval)

See `FUTURE_PLAN.md` for full roadmap. Key next items:
- Bus auto-detection (asyncio vs Tokio vs NestJS event bus)
- Event catalog enforcement (SKILL.md naming constraints)
- Integration test scaffold generation
- Domain-specific observability patterns

---

## Current Status (May 10, 2026)

- **Phase 0**: ✅ Complete (4 modules, 475 LOC) — v0.6.1 shipped
- **Phase 1**: 🟡 In Progress (3/7 modules, 43% complete) — Blocking v0.7.0 (May 20 target)
  - ✅ Gap 1: format_multifile_output.py (90 LOC)
  - ✅ Gap 2: autowire_into_project.py (250 LOC)
  - 🟡 Gap 3: generate_migrations.py (300 LOC) — Integration testing in progress
  - 📋 Gap 4+: Framework config, DI, env vars, Docker Compose (pending)
- **Phase 2-3**: ✅ Complete (57 modules, 12,486 LOC) — v2.0.0 shipped
  - REST API generation (44 modules)
  - Batch job systems (13 modules)
- **Phase 4-5**: 📋 Planned (110 modules, 33,000 LOC) — Q3-Q4 2026

**Market**: 5-8% dev penetration | **Target**: 15-20% post-Phase 4+5

---

**Maintained by:** Claude Code Agent  
**Last updated: 2026-05-11


