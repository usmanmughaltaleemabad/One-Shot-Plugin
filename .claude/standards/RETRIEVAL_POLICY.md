---
type: reference
last_verified: 2026-05-16
owner: claude
---

# Retrieval Policy

What gets loaded when. Defines the L1→L2→L3 cascade to minimize context waste.

---

## The L1/L2/L3 Contract

| Level | What lives here | Load behavior |
|-------|---|---|
| **L1** | CLAUDE.md at repo root | Always loaded, every session. < 100 lines, routing only. |
| **L2** | CLAUDE.md in sub-folders (skills/, commands/, tests/) | On-demand — loaded when Claude reads a file in that directory. < 100 lines, routing only. |
| **L3** | Actual docs, runbooks, references (docs/*.md) | Load only when blocked without it. Specific doc only, not whole directory. < 300 lines per doc. |

---

## L1: Root CLAUDE.md

Loaded: Always, every session (it's small — < 100 lines).

Contains:
- ✅ Navigation table → where to find L2/L3 docs
- ✅ Folder structure diagram
- ✅ Quick skill index
- ✅ Critical rules (3-5 only)
- ✅ Common commands (copy-paste runnable)

Does NOT contain:
- ❌ Detailed skill descriptions (link to skills/CLAUDE.md instead)
- ❌ Full phase status (link to docs/phase-status.md instead)
- ❌ Testing procedure (link to docs/testing.md instead)
- ❌ Roadmap (link to ROADMAP.md or .claude/PHASE_X_IMPLEMENTATION_PLAN.md)

---

## L2: Sub-folder CLAUDE.md files

**When loaded:** On-demand. When Claude reads a file in that folder (e.g., edits `skills/one-shot-generator/SKILL.md` → loads `skills/CLAUDE.md`).

**What lives here:**
- ✅ Navigation to all docs in that domain (skills, commands, tests)
- ✅ Domain-specific quick reference
- ✅ Links to L3 docs

**Current L2 files:**
```
skills/CLAUDE.md          ← loaded when editing a skill
commands/CLAUDE.md        ← loaded when working with commands
tests/CLAUDE.md           ← loaded when writing tests
```

**Line limit:** < 100 lines (same as L1)

**Why .claude/rules/ NOT used here:** Plugin is small (6 skills). Sub-folder CLAUDE.md is simpler and more discoverable than `.claude/rules/` with path patterns.

---

## L3: Specific Documentation

**When loaded:** Only when you're blocked without it. Specific doc only.

**Structure:**
```
docs/
├── skill-authoring.md     ← how to write a SKILL.md
├── phase-status.md        ← real vs stub modules (CRITICAL)
├── testing.md             ← how to test locally
├── publish.md             ← marketplace publish workflow
├── scripts-index.md       ← all 170 scripts listed
└── active/                ← time-bound docs (investigations, active plans)
    └── (not yet created)
```

**Line limit:** < 300 lines per doc (split if needed)

**Load rules:**
- Load only the one doc that unblocks you, not the whole directory
- Never load `docs/` as a folder — load specific files only
- If a doc references another (e.g., "see phase-status.md"), load that one doc, not all of `docs/`

---

## L1 → L2 → L3 Navigation Examples

### Example 1: "How do I test locally?"

Session starts:
1. **L1 loaded:** CLAUDE.md
2. Claude sees "Testing" → looks in quick commands section
3. Command: `bash .claude/scripts/smoke-test.sh` or `python RUN_INTEGRATION_TESTS.py`
4. User says: "More details on testing"
5. **L3 loaded:** `docs/testing.md` ← only this one, on-demand

---

### Example 2: "I want to edit the one-shot-generator skill"

Session:
1. **L1 loaded:** CLAUDE.md (always)
2. Claude opens `skills/one-shot-generator/SKILL.md`
3. **L2 auto-loads:** `skills/CLAUDE.md` (on-demand, when reading files in skills/)
4. Claude sees: "For skill authoring guide, see docs/skill-authoring.md"
5. If Claude needs authoring details: **L3 loads:** `docs/skill-authoring.md`

---

### Example 3: "Which modules are implemented in Phase 4?"

Session:
1. **L1 loaded:** CLAUDE.md
2. Claude needs phase status → session-start injected a summary
3. For full details: **L3 loads:** `docs/phase-status.md`
4. Claude finds: ❌ Phase 4 all marked as STUB

---

## Special: Beads (Meta-Context)

Beads are injected by session-start.sh (not loaded as docs):

```
.beads/status.jsonl       ← injected: last 5 open beads
.beads/decisions.jsonl    ← not auto-injected, load if needed
.beads/failures.jsonl     ← not auto-injected, load if needed
```

Open beads are shown at session start as metadata, not loaded as context.
If you need to read decisions or failures, use Read tool explicitly.

---

## Never Auto-Load

- ❌ `CHANGELOG.md` (append-only, can be huge — load by version section only)
- ❌ `ROADMAP.md` (aspirational planning, load if planning Phase 4-5)
- ❌ `.claude/PHASE_4_IMPLEMENTATION_PLAN.md` (load only when actively implementing)
- ❌ All of `docs/` directory (load specific docs only)
- ❌ Archived investigations
- ❌ Full `.beads/decisions.jsonl` or `failures.jsonl`

---

## Context Budget

Typical L1→L2→L3 load for a session:

| Scenario | L1 | L2 | L3 | Total tokens |
|----------|---|---|---|---|
| Session start (no work yet) | 50 | 0 | 0 | ~50 |
| Editing a skill | 50 | 100 | 300 (skill-authoring) | ~450 |
| Publishing new version | 50 | 0 | 300 (publish.md) | ~350 |
| Planning Phase 4 | 50 | 0 | 500+ (ROADMAP + phase-status) | ~550+ |
| Debugging failure | 50 | 0 | 300 (failures.jsonl + investigation) | ~350 |

Goal: Keep total < 1000 tokens for standard tasks (under 5% of context window).

---

## Feedback Loop

If you find yourself re-loading the same L3 doc every session:
→ Consider promoting it to L2 (include in sub-folder CLAUDE.md)

If a doc exceeds its line limit:
→ Split it and update navigation (see DOC_TYPE_SYSTEM.md)

If a doc is never loaded:
→ Archive it (move to history/) or integrate into another doc
