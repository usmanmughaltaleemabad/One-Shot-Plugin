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
| Tier 1 pipeline | `docs/tier1-pipeline.md` |
| Tier 2 (closed loop + agents) | `docs/tier2-pipeline.md` |
| Tier 2.5 (spec-driven, FKs, loop) | `docs/tier25-pipeline.md` |
| Tier 3 (curriculum, drift, gates) | `docs/tier3-pipeline.md` |
| Tier 3.5 (**agentic restructure**) | `docs/tier35-agentic.md` |
| Tier 4 (self-extending plugin) | `docs/tier4-self-extending.md` |
| Plugin scorecard | `docs/scorecard.md` |
| One-shot orchestrator | `skills/one-shot-generator/scripts/one_shot_orchestrator.py` |
| Multi-agent definitions | `.claude/agents/{architect,implementer,test-author,reviewer,wirer,critic}.md` |
| Validation findings | `VALIDATION_REPORT.md` |
| Writing a skill | `docs/skill-authoring.md` |
| Real vs stub modules | `docs/phase-status.md` |
| Testing locally | `docs/testing.md` |
| Publishing | `docs/publish.md` |
| All scripts | `docs/scripts-index.md` |
| Active work | `.beads/status.jsonl` |
| Failure beads | `.beads/failures.jsonl` |

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
# Primary path — agentic (Claude reasons, scripts execute)
/one-shot "shopping cart with line items, discounts" @./my-project
/one-shot "..." @./my-project --apply              # mutate main.py
/one-shot "..." @./my-project --budget=0.30        # halt if cost exceeds
/one-shot "..." @./my-project --templated          # free fallback (no Claude tokens)

# Headless / CI mode
python skills/one-shot-generator/scripts/one_shot_orchestrator.py \
    "shopping cart with line items" --project ./my-project

# Tests
bash .claude/scripts/smoke-test.sh
python -m pytest tests/
```

---

Updated 2026-05-16
