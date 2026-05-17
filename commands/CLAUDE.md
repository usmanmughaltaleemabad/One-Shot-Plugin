---
type: router
last_verified: 2026-05-16
owner: claude
---

# Commands Directory

Metadata for 15 slash command overrides.

---

## Quick Reference

Command metadata files (no code, just descriptions).

| Command | File | Purpose |
|---------|------|---------|
| **one-shot** ⭐ | **one-shot.md** | **Primary agentic pipeline (Tier 3.5)** |
| one-shot-generator | one-shot-prompting.md | Legacy single-resource skill invocation |
| help | help.md | General help and getting started |
| health-check | health-check.md | Verify plugin installation |
| debug | debug.md | Diagnostic commands |
| plan | plan.md | Planning workflow |
| generate | generate.md | Code generation with constraints |
| test | test.md | Testing + verification |
| tdd | tdd.md | Test-driven development cycle |
| version | version.md | Plugin version info |
| status | status.md | Project status summary |
| roadmap | roadmap.md | Feature roadmap |
| examples | examples.md | Example projects |
| budget | budget.md | Cost & performance analysis |
| changelog | changelog.md | Version history access |

---

## How These Work

These files are slash command overrides that extend Claude Code's built-in `/help`, `/debug`, etc.

Each file documents:
- What the command does
- Syntax and examples
- Common use cases
- Flags and options

**No executable code** — these are documentation files for the CLI.

---

## Development

To add a new command:

1. Create a new `.md` file in this directory
2. Add YAML frontmatter: `name:`, `description:`
3. Document syntax, examples, flags
4. Reference in `CLAUDE.md` (this file)
5. Update plugin version + CHANGELOG

---

**See also:**
- `../docs/publish.md` — how to publish new commands
- `../CLAUDE.md` — main navigation
