---
type: router
last_verified: 2026-05-16
owner: claude
---

# one-shot-prompting Plugin

Plugin for generating REST APIs and batch jobs from natural language.

## Quick Navigation

| For... | See... |
|---|---|
| Writing a skill | `docs/skill-authoring.md` |
| Real vs stub modules | `docs/phase-status.md` |
| Testing locally | `docs/testing.md` |
| Publishing | `docs/publish.md` |
| All 170 scripts | `docs/scripts-index.md` |
| Active work | `.beads/status.jsonl` |

## Structure

```
├── .claude/           ← harness: hooks, agents, standards, beads
├── skills/            ← 6 skills + 170 scripts
├── docs/              ← L3 docs
├── tests/, examples/  ← fixtures, examples
├── CHANGELOG.md, plugin.json
```

## The 6 Skills

| Skill | Purpose |
|---|---|
| one-shot-generator | REST APIs + batch jobs (1677 L) |
| write-plan | Generate plan before code |
| execute-plan | Execute plan steps |
| tdd-cycle | Test → fail → implement → pass |
| systematic-debug | Analyze error logs |
| verify-before-complete | Gate: confirm before apply |

## Critical Rules

1. CLAUDE.md < 100 lines — route to L2/L3
2. All scripts: zero external dependencies (stdlib only)
3. All .md files: YAML frontmatter (type, last_verified, owner)
4. Phase 4-5 scripts are STUBS — see docs/phase-status.md
5. Publish: version bump protocol (see docs/publish.md)

## Workflow

PLAN → AUTHOR → TEST → VERIFY → PUBLISH → CLOSE

## Quick Commands

```bash
/one-shot-prompting:one-shot-generator "request" @/project
bash .claude/scripts/smoke-test.sh
python RUN_INTEGRATION_TESTS.py
cat docs/phase-status.md
```

---

Updated 2026-05-16
