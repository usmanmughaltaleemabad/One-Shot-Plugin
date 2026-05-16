---
type: reference
last_verified: 2026-05-16
owner: claude
---

# Document Type System

Every markdown file in this repo belongs to one type. Type determines line limits and load behavior.

---

## The 6 Types

| Type | Purpose | Line Limit | When Loaded |
|------|---------|-----------|------------|
| **router** | Navigation only — links, no content | 100 | Always safe to load |
| **runbook** | Step-by-step procedures | 200 | Load when executing that procedure |
| **reference** | Stable lookup information | 300 | Load when that domain is active |
| **investigation** | Active analysis, time-bound | 300 | Load when debugging |
| **plan** | Proposed approach, decisions | Unlimited | Load when planning implementation |
| **changelog** | Version history, append-only | Unlimited | Load by section only |

---

## Type Details

### router

Navigation only. Contains links, one-line descriptions, nothing else. Metadata for humans and Claude.

**Purpose:** Help Claude find the right document quickly.

**Examples:** `CLAUDE.md`, `docs/`, `skills/CLAUDE.md`

**What NOT to include:**
- Procedures (that's runbook)
- Explanations > 1 sentence
- Code snippets (except links to them)
- Credentials or env vars

**Example:**
```markdown
---
type: router
last_verified: 2026-05-16
owner: claude
---

# Documentation

| Document | Purpose |
|----------|---------|
| [Testing](testing.md) | How to run tests locally |
| [Publishing](publish.md) | Marketplace release workflow |
```

---

### runbook

Step-by-step procedures. Each step is an action. Someone should execute this without reading anything else.

**Purpose:** Actionable instructions for a specific task.

**Examples:** `docs/testing.md`, `docs/publish.md`, `docs/skill-authoring.md`

**What NOT to include:**
- Background context (that's reference)
- Architecture explanations (that's reference)
- Design rationale (that's plan)

**Example:**
```markdown
---
type: runbook
last_verified: 2026-05-16
owner: claude
---

# Testing

## Prerequisites
- [ ] Python 3.10+ installed
- [ ] Git repository cloned

## Steps

1. Run smoke test:
   ```bash
   bash .claude/scripts/smoke-test.sh
   ```

2. If passing, run integration tests:
   ```bash
   python RUN_INTEGRATION_TESTS.py
   ```
```

---

### reference

Stable lookup information. Doesn't change often. Loaded when Claude needs to know something factual.

**Purpose:** Answer "what is X?", "where is Y?", "how much is Z?"

**Examples:** `docs/phase-status.md`, `docs/scripts-index.md`, schema docs, environment variables

**What NOT to include:**
- Procedures (that's runbook)
- History (that's changelog)
- Current work in progress (that's investigation)

**Example:**
```markdown
---
type: reference
last_verified: 2026-05-16
owner: claude
---

# Phase Status

| Phase | Modules | Status |
|-------|---------|--------|
| 0 | 4 | ✅ Real |
| 1 | 8 | ✅ Real |
| 2 | 44 | ✅ Real |
| 3 | 13 | ✅ Real |
| 4 | 60 | ❌ Stub |
| 5 | 50+ | ❌ Stub |
```

---

### investigation

Active analysis with findings. Created when debugging or researching. Has a start, findings, conclusion. Time-bound.

**Purpose:** Document findings from a deep dive.

**Examples:** `docs/active/investigation-phase4-stubs.md`

**Status field is mandatory:** `active` while open, `archived` when resolved.

**What NOT to include:**
- Planning (that's plan)
- Procedures (that's runbook)

**Example:**
```markdown
---
type: investigation
last_verified: 2026-05-16
owner: claude
status: active
---

# Investigation: Phase 4-5 Stub Status

## Problem
Phase 4-5 script files exist but claimed as implemented.

## Findings
- Checked all phase4_*.py files: empty or placeholder only
- No working implementations
- Script files were created for planning, never filled in

## Resolution
Created docs/phase-status.md with ✅ Real vs ❌ Stub labels. Added session-start hook to warn.
```

---

### plan

Proposed approach. Contains design, trade-offs, open questions. Forward-looking.

**Purpose:** Discuss "how should we build X?"

**Examples:** `.claude/PHASE_4_IMPLEMENTATION_PLAN.md`

**Status field:** `active` while executing, `archived` when done.

**What NOT to include:**
- History (that's changelog)
- Finalized knowledge (that's reference)

**Example:**
```markdown
---
type: plan
last_verified: 2026-05-16
owner: claude
status: active
---

# Phase 4 Implementation Plan

## Goal
Implement production hardening: DDD, CQRS, compliance.

## Phases
1. DDD (15 modules, 40h)
2. CQRS (10 modules, 30h)
3. Compliance (19 modules, 80h)

## Open Questions
- Should DDD and CQRS share models, or separate?
```

---

### changelog

Version history. Append-only. Load by version section only.

**Purpose:** Record what changed in each version.

**Examples:** `CHANGELOG.md`

**Format:** Keep a Changelog standard

**Example:**
```markdown
---
type: changelog
last_verified: 2026-05-16
owner: claude
---

# Changelog

## v2.0.0 – 2026-05-11
- Added Phase 3: Batch job systems
- Fixed webhook retry backoff

## v1.0.0 – 2026-04-01
- Initial release
```

---

## Enforcement

**Hooks validate:**
- All .md files (except CLAUDE.md) must have YAML frontmatter with `type:`
- Line counts must not exceed type's limit (router ≤ 100, runbook ≤ 200, reference ≤ 300, etc.)

**Pre-commit:**
```bash
bash .claude/scripts/smoke-test.sh
# Will fail if any doc violates type limits
```

---

## Why These Limits?

Stanford research ("Lost in the Middle") shows: longer context degrades token quality.

- **100 lines (router):** Loaded every session; must be lightweight
- **200 lines (runbook):** Loaded once per task; readable in 5 min
- **300 lines (reference):** Loaded when domain is active; ~10-15 min read
- **Unlimited (plan, changelog):** Loaded by section only; never as a whole

Violating limits = polluting context = slower, more expensive, lower quality.

---

## Splitting Documents

When a doc hits its line limit, split it.

**Pattern:**
```
docs/schema.md              → router (links to:)
  docs/schema-tables.md     → reference (300 lines)
  docs/schema-indexes.md    → reference (100 lines)
```

The router becomes:
```markdown
---
type: router
---

# Schema

| Document | Contents |
|----------|----------|
| [schema-tables.md](schema-tables.md) | Tables, columns, types |
| [schema-indexes.md](schema-indexes.md) | Indexes, constraints |
```

Never have a 600-line reference doc.
