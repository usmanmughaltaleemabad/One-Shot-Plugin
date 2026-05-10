# Plugin Directory Structure

This document explains the clean, organized structure of the one-shot-prompting plugin following Anthropic plugin development best practices.

## Structure Overview

```
one-shot-prompting/
├── .claude-plugin/
│   └── plugin.json                 ← Marketplace metadata (version, description, etc.)
├── commands/                       ← Command reference documentation
│   ├── architecture.md
│   ├── budget.md
│   ├── check-consistency.md
│   ├── debug.md
│   ├── generate.md
│   ├── health-check.md
│   ├── review.md
│   ├── strangler.md
│   ├── templates.md
│   └── tour.md
├── examples/                       ← Example projects for different frameworks
│   ├── README.md
│   ├── django-order-service/
│   ├── fastapi-rate-limiter/
│   ├── go-trading-bot/
│   ├── nestjs-realtime-api/
│   └── spring-payment-service/
├── skills/
│   └── one-shot-generator/         ← Main skill implementation
│       ├── SKILL.md                ← Core skill prompt with all generation logic
│       └── scripts/
│           └── analyze_codebase.py ← Python analyzer (subprocess invoked by skill)
├── .claude/
│   └── commands/
│       └── one-shot-prompting.md   ← Claude Code command reference
├── README.md                       ← User-facing documentation
├── CHANGELOG.md                    ← Version history
├── CLAUDE.md                       ← Developer guide
├── PRIVACY.md                      ← Privacy policy
├── QUICKSTART.md                   ← Quick start guide
├── START_HERE.md                   ← Entry point for new users
├── RELEASE_GUIDE.md                ← Release procedures
├── FUTURE_PLAN.md                  ← Strategic roadmap (gitignored, local only)
├── package.json                    ← NPM package metadata
├── tsconfig.json                   ← TypeScript configuration
├── .gitignore                      ← Git exclusions (includes FUTURE_PLAN.md)
└── .npmignore                      ← NPM publish exclusions

```

## File Categories

### 📦 Marketplace & Distribution
- `.claude-plugin/plugin.json` — Marketplace metadata
- `package.json` — NPM package definition
- `.npmignore` — Files excluded from npm publish
- `CHANGELOG.md` — Version history (user-facing)

### 📖 Documentation
- `README.md` — Main user guide
- `QUICKSTART.md` — Getting started in 5 minutes
- `START_HERE.md` — Entry point for new users
- `RELEASE_GUIDE.md` — Release process documentation
- `commands/` — Command reference (auto-discoverable)
- `PRIVACY.md` — Privacy policy

### 👨‍💻 Developer Resources
- `CLAUDE.md` — Developer guide and architecture
- `FUTURE_PLAN.md` — Strategic roadmap (local, gitignored)
- `.claude/commands/one-shot-prompting.md` — Claude Code command format

### 🛠️ Implementation
- `skills/one-shot-generator/SKILL.md` — Core skill logic and generation templates
- `skills/one-shot-generator/scripts/analyze_codebase.py` — Codebase analyzer

### 📚 Examples
- `examples/` — Real-world example projects
  - 5 frameworks with complete implementations
  - Each with independent README

## Key Principles

### ✅ What's In This Repository
- **Plugin metadata** (plugin.json, package.json)
- **User-facing documentation** (README, guides, examples)
- **Skill implementation** (SKILL.md with all generation logic)
- **Analyzer script** (Python with stdlib only, no external deps)
- **Developer guide** (CLAUDE.md for contributors)

### ❌ What's NOT In This Repository
- **Generated code** (users request it via skill, not stored here)
- **Session status documents** (progress tracking is local only)
- **Duplicate documentation** (consolidate into single source of truth)
- **Development artifacts** (test outputs, build logs, status files)
- **Strategic planning** (FUTURE_PLAN.md is gitignored and local-only)

## For Marketplace Release

When submitting to Claude marketplace:
1. Ensure `.claude-plugin/plugin.json` is updated with correct version
2. All `README`, `QUICKSTART`, `PRIVACY` are polished and complete
3. `CHANGELOG.md` documents all changes since last version
4. `examples/` are working and up-to-date
5. No session/progress/status files in repository (use .gitignore)

## For Package Distribution (npm)

When publishing to npm:
1. `.npmignore` excludes all development files
2. Only essential files packaged (metadata, scripts, minimal docs)
3. Large binary files compressed with semantic versioning
4. package.json maintains correct dependencies

## Migrating to This Structure

If coming from an older version:
1. ✅ Delete all `PHASE_*`, `IMPLEMENTATION_*`, `PROJECT_*` files
2. ✅ Delete all `.claude-plugin/*.md` files (keep plugin.json)
3. ✅ Delete duplicate `skills/*/commands/` directories
4. ✅ Consolidate nested generated markdown into FUTURE_PLAN.md
5. ✅ Create .npmignore if not present
6. ✅ Run `git status` to verify all artifacts are staged for cleanup

---

**Maintained by:** Claude Code Agent  
**Last updated:** 2026-05-09  
**Structure Version:** 1.0 (Anthropic standards-compliant)
