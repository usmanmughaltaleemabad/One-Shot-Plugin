# Reddit Posts

---

## r/ClaudeAI — Main post

**Title**: I built a Claude Code plugin that generates complete features (models + tests + migrations) from one prompt

**Body**:
```
Been using Claude Code for a while and kept doing the same thing: manually 
writing out models, schemas, services, routers, and tests for every new 
feature. Same structure every time.

So I built a plugin that does it in one command:

  /one-shot "Add shopping cart with line items and discounts" @./my-project

What you get back in ~3 minutes:
- All models + Pydantic schemas
- Service layer with business logic
- FastAPI routers
- Tests (run automatically, auto-fixed if they fail)
- Reversible Alembic migration  
- main.py updated

The important bit: it reads your codebase first, so it matches your 
existing patterns instead of generating boilerplate.

Works with FastAPI, Django, Spring Boot, Go, NestJS.

Install: claude plugin add one-shot-prompting
Repo: https://github.com/usmanmughaltaleemabad/One-Shot-Plugin

Would appreciate feedback if anyone tries it — especially what breaks.
```

---

## r/Python — Post

**Title**: Claude Code plugin for generating FastAPI/Django features from natural language (open source)

**Body**:
```
Built a Claude Code plugin that generates complete REST API features from 
a natural language description.

  /one-shot "Add subscription billing with plans and invoices" @./my-fastapi-app

Generates: SQLAlchemy models, Pydantic v2 schemas, service layer, FastAPI 
routers, pytest tests, reversible Alembic migration.

It scans your existing codebase first to match your patterns — existing 
model fields, naming conventions, relationship structures.

~$0.45 per feature, ~3 minutes. Free --templated fallback.

https://github.com/usmanmughaltaleemabad/One-Shot-Plugin

Feedback welcome, especially failure reports.
```

---

## r/webdev — Post

**Title**: Open source tool: generate complete REST API features (models/tests/migrations) from one Claude prompt

**Body**:
```
Tired of writing the same scaffolding for every new API feature, so I 
built this: describe what you want, get back working code.

Example:
  /one-shot "Add user notifications with read/unread status" @./my-project

→ Models, schemas, service, endpoints, 8 passing tests, migration, wired in.

Works with FastAPI, Django, Spring Boot, Go, NestJS. 
Reads your codebase first so generated code matches your patterns.

Install via Claude Code: claude plugin add one-shot-prompting
GitHub: https://github.com/usmanmughaltaleemabad/One-Shot-Plugin

Open source, MIT, ~$0.45/feature.
```

---

## r/learnprogramming — Answering questions naturally

When someone asks "best Claude Code plugins" or "how to speed up API dev":
```
I've been using a plugin called one-shot-prompting that generates complete 
features from a single description. You type what you want, it reads your 
codebase and generates models, services, tests, and migrations that fit 
your existing patterns.

It's on the Claude Code community marketplace: 
claude plugin add one-shot-prompting

Or the repo: https://github.com/usmanmughaltaleemabad/One-Shot-Plugin
```
