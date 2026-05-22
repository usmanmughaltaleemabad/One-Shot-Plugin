---
type: reference
last_verified: 2026-05-21
owner: usman
---

# One-Shot Positioning Brief

Developer-focused positioning adapted from Jugnu framework (Mashhood, April 2026).

---

## Problem Statement

**Current Reality:**
Manual feature scaffolding is slow, error-prone, and doesn't fit existing code.

- **Speed:** 30+ minutes of boilerplate + integration work per feature
- **Reliability:** Mistakes in FK setup, missing migrations, untested edge cases
- **Context Loss:** Generic templates ignore your codebase's patterns, naming conventions, architecture

**Developer Frustration:**
"I know what I want to build. Why do I need to spend 30 minutes wiring it into my codebase?"

**Market Insight:**
Developers care about **velocity + confidence**. They'll accept automation if it:
1. Saves real time (not 5 minutes, but 20+)
2. Produces code they trust (tested, documented, idiomatic)
3. Understands their codebase (not generic)

---

## Solution: One-Shot Prompting

**Elevator Pitch:**
Generate production-ready features that fit seamlessly into your existing codebase. Claude reads your code, understands your patterns, and writes code that belongs there.

**How It Works (User Perspective):**
```
/one-shot "Add shopping cart with line items" @./my-project

↓

✅ Claude analyzes your codebase
✅ Generates idiomatic code (understands your ORM, API style, testing patterns)
✅ Auto-runs tests (and fixes them if needed)
✅ Creates migrations
✅ Wires into main.py
↓

Ready to commit in 2-3 minutes
```

**Core Value Props:**

### 1. Codebase-Aware
- Understands your existing schema, models, relationships
- Generates code in your style (not generic boilerplate)
- Respects your naming conventions, import patterns, folder structure

### 2. Self-Verifying
- Auto-generates tests alongside code
- Runs tests immediately
- Auto-fixes issues (bugs, type errors, missing dependencies)
- Shows you the results before committing

### 3. Framework-Native
- FastAPI, Django, Spring Boot, Go, Node, NestJS
- Idiomatic patterns per framework (not lowest-common-denominator)
- Knows ORM best practices (eager loading, migrations, indexes)

### 4. Cost-Transparent
- Average $0.45 per feature (shown upfront)
- No hidden API calls
- Free templated fallback (`--templated` flag)

### 5. Enterprise-Safe
- Full reversibility (migrations have UP/DOWN)
- Audit trail (what changed, why, when)
- Zero hardcoded secrets
- Security scanning (OWASP top 10)
- Optional approval workflow

---

## Differentiation

| Aspect | One-Shot | Templates | Copilot |
|---|---|---|---|
| **Context** | Reads entire codebase | N/A | File-only |
| **Testing** | Auto-generates + runs | You write tests | Completion-only |
| **Migrations** | Automatic (reversible) | Manual | Manual |
| **Speed** | 2-3 min | 30+ min | 10-15 min (still manual) |
| **Cost** | $0.45 | $0 (but your time) | Per-usage/subscription |
| **Integration** | Auto-wires to main.py | You integrate | You integrate |

**Why we win:**
- Developers don't want to write scaffolding. They want to write *business logic*.
- One-shot is the only tool that understands existing codebases + auto-generates tests + auto-wires integration.

---

## Proof Points (from Eval Harness)

**Routing Quality:** 99% — correct agent chosen first time
**Cost:** $0.45 average per generation
**Test Pass Rate:** 94% — generated code passes tests immediately
**Code Quality:** 82/100 — cyclomatic complexity, type hints, style
**Security:** 100% — zero critical vulnerabilities
**Speed:** 2.5 min average (vs 30 min manual)

---

## Key Hooks (Messaging Angles)

### Hook 1: "Feels Like a Teammate"
> "One-Shot understands your codebase like a senior engineer. It knows your schema, your patterns, your style. It writes code that *belongs* in your project."

**Why it works:** Developers want AI that understands context, not a dumb autocomplete.

### Hook 2: "Meets You Where Your Workflow Is"
> "No need to adapt your stack. FastAPI, Django, Spring, Go, Node — One-Shot speaks your language."

**Why it works:** Developers hate tool lock-in. Meeting them in their existing workflow removes friction.

### Hook 3: "Self-Verifying"
> "Generated code includes tests. We run them immediately. If they fail, we fix them. You see working code, ready to commit."

**Why it works:** Trust is the blocker for code generation adoption. Seeing tests pass builds confidence instantly.

### Hook 4: "Reversible Changes"
> "Every change includes a reversible migration. Every commit includes an audit trail. Enterprise-safe by design."

**Why it works:** Enterprises care about compliance, reversibility, auditability. One-Shot speaks their language.

### Hook 5: "Global, Not Gatekept"
> "No vendor lock-in. No API key requirements. Use locally or in Claude Code. Open source. MIT license."

**Why it works:** Developers are suspicious of closed tools. Openness + local control = adoption.

---

## Launch Positioning: From Day 1

**Day 1 Message:**
"One-Shot generates production-ready features that fit your codebase. Claude reads your code, understands your patterns, and writes code that belongs there. Try it with `/one-shot "<feature>" @./project`."

**Month 1 Goal:**
100 developers trying it, 20% activation (20 teams using it regularly)

**Month 3 Goal:**
1,000 weekly active developers, 50% test pass rate adoption, platform partnerships (IDE extensions)

---

## Tone & Voice

Adapted from Jugnu Mashhood guide:

- **Confident, not arrogant** — We know this works, but we're not claiming perfection
- **Developer-first** — Speak their language (you understand velocity, tech debt, migrations)
- **Transparent about tradeoffs** — "Costs $0.45 per feature, not free" (but it's cheaper than your time)
- **Focused on outcomes, not features** — Don't say "14-stage pipeline"; say "2-3 min from idea to commit"
- **Human voice** — Written for humans, not marketing copy templates
