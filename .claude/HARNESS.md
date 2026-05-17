---
type: guide
last_verified: 2026-05-17
owner: claude
---

# The Harness Framework — Official Specification

## What is a Harness?

A **harness** is a `.claude/` directory in your project that contains governance, routing, and automation rules for Claude Code development.

**Think of it as**: An IDE configuration system for Claude, but instead of JSON settings, it's human-readable markdown + YAML + executable scripts.

**Why you need it**:
- **Context routing**: Tell Claude what docs to load (L1/L2/L3 context)
- **Quality gates**: Enforce code review, testing, security checks via hooks
- **State tracking**: Track decisions, blocked work, who did what (beads)
- **Standards**: Define your team's rules for code, docs, processes
- **Agent coordination**: Multiple agents working together without conflicts

---

## Directory Structure

Every harness has this structure:

```
.claude/
├── CLAUDE.md                 ← L1 router (main navigation)
├── HARNESS.md               ← This file (reference)
├── hooks/                   ← Execution enforcement
│   ├── pre_tool_use.sh      ← Before Claude runs any tool
│   ├── post_tool_use.sh     ← After Claude runs any tool
│   └── stop.sh              ← Before Claude stops/exits
├── agents/                  ← Custom agents for your team
│   ├── code-reviewer.md     ← Code review agent
│   ├── architect.md         ← Architecture design agent
│   └── debugger.md          ← Debugging agent
├── standards/               ← Team governance rules
│   ├── code-style.md        ← Linting, formatting, patterns
│   ├── doc-standards.md     ← Documentation requirements
│   ├── testing-rules.md     ← Test coverage, test patterns
│   └── security-rules.md    ← Security checklist
├── skills/                  ← Custom skills (reusable code)
│   ├── framework-detect.py
│   └── code-validator.py
└── beads/                   ← Operational state tracking
    ├── status.jsonl         ← Open/closed work items
    ├── decisions.jsonl      ← Decisions made + rationale
    └── failures.jsonl       ← Failures + lessons learned
```

---

## Core Concepts

### 1. CLAUDE.md — The L1 Router

**What it is**: Entry point for Claude. Tells Claude which docs to load and where to find help.

**How it works**:
- Claude reads CLAUDE.md first
- CLAUDE.md routes to L2 docs (in .claude/ subdirs)
- L2 docs route to L3 docs (in main repo)
- Result: Claude has right context for your project

**Rules**:
- Keep CLAUDE.md < 100 lines (discipline!)
- Link to detailed docs, don't write them in CLAUDE.md
- YAML frontmatter required (type, last_verified, owner)

**Example**:
```markdown
---
type: router
last_verified: 2026-05-17
owner: claude
---

# My Project

**Quick Links**

| For... | See... |
|--------|--------|
| Code style | `docs/CODE_STYLE.md` |
| Adding features | `docs/FEATURE_DEVELOPMENT.md` |
| Debugging | `.claude/agents/debugger.md` |
| Standards | `.claude/standards/` |

**Critical Rules**

1. All code must pass eslint (see .eslintrc.json)
2. All PRs need 2 reviews (see .github/CODEOWNERS)
3. Tests must have 80%+ coverage (see jest.config.js)
```

### 2. Hooks — Execution Enforcement

**What they are**: Scripts that run before/after Claude uses tools.

**When they run**:
- `pre_tool_use.sh`: Before Claude calls Bash, Edit, Write, etc.
- `post_tool_use.sh`: After the tool finishes
- `stop.sh`: Before Claude exits session

**Use cases**:
- Block dangerous commands (git push without review)
- Validate code before writing (Python syntax check)
- Enforce standards (YAML frontmatter on all .md files)
- Clean up (remove temp files before exit)

**Example hook** (block git push without review):
```bash
#!/bin/bash
# .claude/hooks/pre_tool_use.sh

if [[ "$TOOL" == "Bash" && "$COMMAND" =~ git\ push ]]; then
  if ! grep -q "APPROVED:" .claude/beads/status.jsonl; then
    echo "❌ BLOCKED: git push requires approval in beads"
    exit 1
  fi
fi
```

### 3. Agents — Custom AI Agents for Your Team

**What they are**: Markdown files describing specialized AI agents that help with specific tasks.

**Structure**:
```markdown
---
name: code-reviewer
description: Reviews code for quality, security, and style adherence
owner: team-lead
---

## Responsibilities

- Check code against CODE_STYLE.md
- Flag security issues (SQL injection, XSS, CSRF)
- Verify test coverage (80%+ required)
- Review error handling

## When to Invoke

When: you've just written code and want a review
Trigger: `/call:code-reviewer @/path/to/file.py`
```

**Types of agents**:
- Code reviewers (quality gates)
- Architects (design validation)
- Testers (test generation, coverage analysis)
- Debuggers (error analysis)
- Security reviewers (vulnerability scanning)
- Performance analyzers (optimization)

### 4. Standards — Team Governance Rules

**What they are**: Documents defining your team's rules for code, docs, processes.

**Core standards** (you can add more):

**code-style.md**: How code should look
- Linting rules (eslint, pylint, etc.)
- Naming conventions
- Formatting standards (2-space indent, etc.)
- Framework patterns (MVC, repository pattern, etc.)

**doc-standards.md**: How docs should be written
- All .md files must have YAML frontmatter
- Max line length: 100 characters
- One H1 per file
- Links must be relative (not absolute)

**testing-rules.md**: Test requirements
- Minimum 80% coverage
- Unit tests for all functions
- Integration tests for APIs
- E2E tests for critical flows

**security-rules.md**: Security checklist
- No credentials in code
- All inputs validated
- Output escaped
- SQL queries parameterized
- Dependencies audited weekly

### 5. Beads — Operational State Tracking

**What they are**: JSONL files (one JSON object per line) tracking decisions and work.

**Three types**:

**status.jsonl**: Open/closed work
```json
{"id":"bd-001","title":"Set up harness","status":"closed","owner":"you","created":"2026-05-17"}
{"id":"bd-002","title":"Implement code-reviewer agent","status":"open","owner":"you","blocked":"waiting for review API"}
```

**decisions.jsonl**: Decisions + rationale
```json
{"id":"dec-001","decision":"Use PostgreSQL not MongoDB","rationale":"Need ACID transactions for payments","date":"2026-05-17","owner":"architect"}
{"id":"dec-002","decision":"Skip Tier 3 SDLC work","rationale":"Focus on winning Tier 2 first","date":"2026-05-17","owner":"you"}
```

**failures.jsonl**: Failures + lessons
```json
{"id":"fail-001","error":"Generated code had SQL injection","module":"phase2_rest_api","lesson":"Always parameterize queries","date":"2026-05-17","fixed":"phase2_rest_api v2.3"}
```

---

## How to Use Your Harness

### Setting Up a New Harness

```bash
# 1. Initialize harness in your project
claude harness init

# 2. Choose your framework (Django, FastAPI, Spring, etc.)
# → Creates .claude/ with templates

# 3. Review and customize
# → Edit .claude/CLAUDE.md for your project
# → Add/remove standards as needed
# → Create custom agents for your team

# 4. Share with your team
# → Commit .claude/ to git
# → Teammates clone and use same harness
```

### Using Harness with One-Shot Plugin

```bash
# Generate code that respects your harness
/one-shot-prompting:one-shot-generator "add user authentication" @/project

# One-shot will:
# 1. Read .claude/CLAUDE.md (understand your project)
# 2. Check .claude/standards/ (follow your rules)
# 3. Call .claude/agents/code-reviewer (review generated code)
# 4. Update .claude/beads/status.jsonl (track what was generated)
```

### Working with Hooks

Hooks run automatically. You don't invoke them—Claude does.

```bash
# Example: This command triggers pre_tool_use hook
$ git push origin main

# Hook runs:
# 1. Check if push is approved in beads
# 2. If not approved → BLOCKED
# 3. If approved → Allow push

# To approve a push:
# Add to .claude/beads/status.jsonl:
# {"id":"bd-003","action":"APPROVED: git push to main","date":"2026-05-17"}
```

### Tracking Work with Beads

Record decisions as you make them:

```bash
# When you decide something important:
echo '{"id":"dec-003","decision":"Use Redis for caching","rationale":"10x faster than in-memory","date":"2026-05-17","owner":"you"}' >> .claude/beads/decisions.jsonl

# When something fails:
echo '{"id":"fail-002","error":"API timeout at 500 QPS","lesson":"Need better rate limiting","date":"2026-05-17","fixed":"rate-limiter v2.0"}' >> .claude/beads/failures.jsonl
```

---

## Best Practices

### 1. Keep CLAUDE.md Small
- Max 100 lines (hard limit)
- Link to detailed docs, don't write them there
- Update CLAUDE.md when you update the project

### 2. Use Frontmatter on All Docs
```yaml
---
type: guide/reference/runbook/router
last_verified: 2026-05-17
owner: claude/your-name/team
---
```

### 3. Standards Should Be Enforceable
- Can't write a hook for it? → Not a standard (make it a guideline instead)
- Example: "Must have 80% test coverage" ✅ (can check with pytest)
- Example: "Code should be elegant" ❌ (too vague)

### 4. Agents Should Have Clear Boundaries
- One agent = one responsibility
- Example: `code-reviewer` reviews code
- Example: `architect` designs systems
- Don't try to make one agent do everything

### 5. Hooks Should Be Fast
- Hook runs on every tool use
- Slow hooks = Claude gets annoyed
- Keep hooks < 1 second

### 6. Beads Are for Important Records
- Open/closed work: track progress
- Decisions: record WHY you made a choice
- Failures: learn from mistakes
- Delete old beads after 3 months (keep it fresh)

---

## Common Patterns

### Pattern 1: Code Review Gate
Require code review before committing.

**Hook** (pre_tool_use.sh):
```bash
if [[ "$COMMAND" =~ git\ commit ]]; then
  if ! grep -q "APPROVED" .claude/beads/status.jsonl; then
    echo "❌ Requires code review (see .claude/agents/code-reviewer.md)"
    exit 1
  fi
fi
```

**Agent** (code-reviewer.md):
```markdown
# Code Reviewer Agent

## Responsibilities
- Review code against CODE_STYLE.md
- Check security issues
- Verify tests exist and pass

## Approval Process
1. Review the code
2. If approved: `echo '{"action":"APPROVED by code-reviewer"}' >> .claude/beads/status.jsonl`
```

### Pattern 2: Framework Detection
Auto-detect your framework and provide context.

**Agent** (framework-detector.md):
```markdown
# Framework Detector

Detects: Django, FastAPI, Spring Boot, Go, Node/Express, NestJS

When invoked:
1. Check for framework config files (settings.py, main.py, etc.)
2. Load appropriate standards (see .claude/standards-{framework}/)
3. Suggest framework-specific agents
```

### Pattern 3: Continuous Integration
Run tests/linting on every code generation.

**Hook** (post_tool_use.sh):
```bash
if [[ "$TOOL" == "Write" && "$FILE" =~ \.py$ ]]; then
  python -m py_compile "$FILE"  # syntax check
  if [ $? -ne 0 ]; then
    echo "❌ Python syntax error in $FILE"
    exit 1
  fi
fi
```

### Pattern 4: Decision Tracking
Record important decisions automatically.

**Agent** (decision-tracker.md):
```markdown
# Decision Tracker

When user makes a significant decision (e.g., "use PostgreSQL"):
1. Record in .claude/beads/decisions.jsonl
2. Include rationale + date
3. Share with team via git
```

---

## Harness vs No Harness

| Scenario | Without Harness | With Harness |
|----------|---|---|
| **New team member joins** | "How do you code here?" (manual) | "See .claude/CLAUDE.md" (automated) |
| **Multiple agents working** | "Who changed what?" (confusion) | Beads track everything |
| **Code quality issues** | Caught in review (slow) | Caught by pre_tool_use hook (fast) |
| **Decision rationale** | "Why did we do this?" (unknown) | decisions.jsonl has record |
| **Failures** | "Did this happen before?" (unknown) | failures.jsonl tracks + prevents recurring |
| **Team standards** | Tribal knowledge | .claude/standards/ is explicit |

---

## Migration: From Chaos to Harness

If you have an existing project without harness:

**Month 1**: Set up harness structure
```bash
claude harness init
# Choose your framework
# Customize .claude/CLAUDE.md
```

**Month 2**: Add standards
- Move coding standards to .claude/standards/code-style.md
- Move test requirements to .claude/standards/testing-rules.md
- Move security rules to .claude/standards/security-rules.md

**Month 3**: Add hooks
- Create pre_tool_use.sh for quality gates
- Create post_tool_use.sh for validation
- Test that hooks work without breaking workflow

**Month 4**: Create agents
- Build code-reviewer agent
- Build architecture agent
- Build debugging agent

**Month 5**: Track decisions + failures
- Start recording decisions in beads
- Log failures and lessons learned
- Make beads a team habit

---

## FAQ

**Q: How much overhead does harness add?**  
A: Minutes (setup) + seconds per tool use (hooks). Hooks should be < 1 second.

**Q: Can I use harness without Claude Code Studio?**  
A: Yes! Harness works with any Claude Code development. One-Shot is optional.

**Q: Can I customize hooks for my framework?**  
A: Completely. Hooks are scripts — write whatever you want in bash/Python.

**Q: How do I share harness with my team?**  
A: Commit .claude/ to git. Team clones and uses same harness.

**Q: Can harness prevent Claude from making mistakes?**  
A: Hooks can block dangerous commands. Agents can review code. But you're still responsible.

**Q: Is harness open-source?**  
A: Yes! The harness specification is MIT licensed. Extend it as needed.

---

## Next Steps

1. **Initialize harness**: `claude harness init`
2. **Customize CLAUDE.md**: Edit for your project
3. **Add standards**: Define your team's rules
4. **Create agents**: Build custom agents for your workflow
5. **Track decisions**: Start using beads for important records
6. **Share with team**: Commit .claude/ to git

**Reference implementations**: See `.claude/examples/` for working harnesses in different frameworks.

---

**Status**: Official specification  
**Last updated**: 2026-05-17  
**Owner**: Claude Harness Community
