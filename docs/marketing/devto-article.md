# dev.to Article

**Title**: I built a Claude Code plugin that generates production-ready FastAPI features in 3 minutes

**Tags**: claudecode, python, fastapi, ai

**Cover image**: Screenshot of terminal showing the command + output

---

## Article body (paste into dev.to editor)

---

I've been building REST APIs long enough to know that the tedious part isn't 
the hard problems — it's the scaffolding. Every new entity needs the same 
thing: model, schema, service, router, tests, migration. Same structure, 
different names.

So I built a Claude Code plugin that does all of it from one command.

## What it does

```bash
/one-shot "Add shopping cart with line items and discounts" @./my-project
```

In about 2-3 minutes, you get back:

```
✅ Analyzed codebase (detected User, Product, Order entities)
✅ Generated Cart, CartItem, Discount — models + schemas + services  
✅ Generated 6 REST endpoints with FastAPI routers
✅ Generated 12 tests — 12/12 passing
✅ Generated reversible Alembic migration
✅ Wired into main.py
Ready to commit. Cost: $0.45.
```

17 files. All passing tests. All wired up. All following your existing code 
patterns — not generic boilerplate.

## Why "one-shot"?

The name refers to the user experience: you describe the feature once, 
and the plugin handles the entire implementation loop without asking you 
follow-up questions (unless the feature description is too vague — then 
it asks before spending your tokens).

## How it actually works

Under the hood it's a 14-stage pipeline:

**PLAN** (free)
1. Scan your codebase, extract existing entities and relationships
2. Run a cost estimate — halt if over your `--budget` limit  
3. Architect agent (Claude Sonnet) designs a spec.json with FK columns derived from relationships

**BUILD** (~$0.20)
4. Implementer agents (Claude Haiku, one per entity) generate files in parallel
5. Test-author agent (Claude Sonnet) writes tests independently of the implementers

**VERIFY** (~$0.10)
6. Auto-patch: 4 deterministic rules fix common bug classes
7. Reviewer agent checks security, performance, style
8. Doubter agent takes a fresh context and adversarially reviews the reviewer's output

**SHIP** (~$0.05)
9. Wirer generates main.py changes (dry-run by default, `--apply` to mutate)
10. Critic runs pytest — if tests fail, it loops up to 3 times with auto-fixes
11. Alembic migration generated with proper `upgrade()` and `downgrade()`

The key insight: code quality tasks go to Claude (reasoning), but deterministic 
tasks (patching, wiring, running tests) stay in Python scripts.

## The codebase-aware part

Before any code is generated, the plugin scans your project:

- Extracts existing SQLAlchemy/Django models to derive FK relationships
- Reads your naming conventions (snake_case? PascalCase?)
- Detects your ORM patterns (does your base model have `created_at`?)
- Identifies your existing router structure

The architect agent uses this context to design code that fits *your* project, 
not a template.

## Supported frameworks

FastAPI, Django + DRF, Spring Boot 3, NestJS, Go (stdlib + Chi), Node.js/Express

## Try it yourself

```bash
# Install from Claude Code community marketplace
claude plugin add one-shot-prompting

# Or use directly in Claude Code
/one-shot "Add user authentication with JWT" @./my-fastapi-project
```

The `--templated` flag runs a zero-token Python fallback if you don't want 
to use API credits for a quick test.

Source: https://github.com/usmanmughaltaleemabad/One-Shot-Plugin

---

Would love to hear what breaks on your codebase. Negative reports are more 
useful than positive ones at this stage.
