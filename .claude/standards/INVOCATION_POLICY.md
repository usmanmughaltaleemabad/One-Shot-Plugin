---
type: reference
last_verified: 2026-05-16
owner: claude
---

# Invocation Policy

When and how each agent and skill is loaded and used.

---

## Agents

Autonomous multi-step orchestrators. Run via manual invocation or session hooks.

| Agent | File | Trigger | When to use |
|-------|------|---------|------------|
| skill-validator | `.claude/agents/skill-validator.md` | manual | After editing a SKILL.md or script — before commit |
| phase-planner | `.claude/agents/phase-planner.md` | manual | When starting Phase 4-5 work — plan the implementation |

### skill-validator

**Invocation:**
```bash
/skill-validator "skills/my-skill/SKILL.md"
```

**Cost:** Low (haiku model) — quick syntax + smoke tests

**Output:** Pass/fail validation report

**What it does:**
- Checks SKILL.md frontmatter
- Verifies scripts exist and have valid syntax
- Runs script against test_contexts/
- Confirms output < 500 tokens

---

### phase-planner

**Invocation:**
```bash
/phase-planner "plan Phase 4 DDD/CQRS implementation"
```

**Cost:** Medium (sonnet) — reads roadmap, plans modules, creates beads

**Output:** Phase implementation plan with module chunks and effort estimates

**What it does:**
- Reads ROADMAP.md + docs/phase-status.md
- Creates .claude/PHASE_X_IMPLEMENTATION_PLAN.md
- Opens beads for each module chunk
- Recommends implementation order

---

## Skills

Static knowledge libraries. Loaded on demand when domain is active.

| Skill | Trigger | Invocation | Cost |
|-------|---------|-----------|------|
| one-shot-generator | manual | `/one-shot-prompting:one-shot-generator "request" @/project` | Medium-High |
| write-plan | manual | `/one-shot-prompting:write-plan "request" @/project` | Medium |
| execute-plan | manual | `/one-shot-prompting:execute-plan "step" @/project` | Low |
| tdd-cycle | manual | `/one-shot-prompting:tdd-cycle "feature" @/project` | Medium |
| systematic-debug | manual | `/one-shot-prompting:systematic-debug /log.txt @/project` | Medium |
| verify-before-complete | manual | `/one-shot-prompting:verify-before-complete @/project` | Medium |

All skills are **manual trigger** — user must explicitly invoke them. None auto-load in session-start.

---

## Cost Tiers

| Tier | Model | Typical Cost | When Used |
|------|-------|---|---|
| **Low** | haiku | ~$0.001/invocation | smoke tests, quick analysis |
| **Medium** | sonnet | ~$0.01/invocation | skills, standard generation |
| **High** | opus | ~$0.1/invocation | complex planning, deep analysis |

**Default for one-shot-prompting:** Sonnet (balances quality + cost)

---

## Workflow

Typical session:

```
1. SESSION STARTS
   → session-start.sh injects: open beads, phase status, CLAUDE.md size warning

2. USER INVOKES A SKILL
   → /one-shot-prompting:one-shot-generator "add auth" @/project
   → Skill runs, generates code, returns output

3. USER INVOKES VERIFY SKILL (optional)
   → /one-shot-prompting:verify-before-complete @/project
   → Confirmation gate before applying generated code

4. SESSION ENDS
   → session-end.sh checks: unclosed beads, unstaged changes
   → Reminds user to update beads if work is incomplete
```

---

## Auto-loading Rules

Nothing auto-loads in this harness except:

1. **CLAUDE.md** (L1 router) — always loaded, every session
2. **Open beads** (from `.beads/status.jsonl`) — injected at session-start
3. **Phase status** (from `docs/phase-status.md` summary) — shown at session-start

Everything else requires explicit invocation.

**Why:** Context is depletable. Auto-loading everything burns tokens on things you don't need this session.

---

## Recommended Workflows

### Generating Code

```
1. /write-plan "add auth endpoint" @/project           ← understand approach
2. /one-shot-prompting:one-shot-generator ... @/project ← generate
3. /verify-before-complete @/project                   ← gate before applying
```

### Debugging Generated Code

```
1. Review error log
2. /systematic-debug /error.log @/project              ← pinpoint issue
3. Edit SKILL.md or script based on findings
4. Re-run generation
```

### Implementing Phase 4-5

```
1. /phase-planner "plan Phase 4"                       ← create plan
2. Open beads per module chunk (phaseplan opens them)
3. Iterate: /skill-validator → edit SKILL.md → test    ← per chunk
4. When all chunks done, bump version + publish
```

---

## Permission Allowlist

Settings in `.claude/settings.json` — what tools are pre-approved:

- Bash: read-only commands (git status, cat, grep)
- Read: any file
- Write/Edit: .md and .py files (hooks validate syntax)
- Skill invocation: all /one-shot-prompting:* skills

Commands that prompt for approval:
- Bash write/execute commands (git commit, bash scripts)
- PowerShell (platform-specific)
- External APIs (none used by design)
