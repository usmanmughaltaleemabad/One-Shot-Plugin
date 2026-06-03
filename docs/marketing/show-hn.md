# Hacker News — Show HN Post

**Best time to post**: Tuesday–Thursday, 8–10am ET
**URL**: https://news.ycombinator.com/submit

---

## Title
```
Show HN: Claude Code plugin that generates complete FastAPI/Django features from one prompt
```

## Text body
```
I built a Claude Code plugin that takes a feature description and generates 
the full implementation: models, services, endpoints, tests, migrations, and 
wires into main.py — in about 2-3 minutes.

  /one-shot "Add shopping cart with line items and discounts" @./my-fastapi-project

What comes back:
- Cart, CartItem, Discount models (SQLAlchemy)
- Pydantic schemas, service layer with invariants
- FastAPI routers
- 12 tests (all passing)
- Reversible Alembic migration
- main.py updated with app.include_router(...)

The key thing it does differently: it reads your codebase first. Scans your 
existing models, naming conventions, ORM patterns. The generated code matches 
your project's style, not generic boilerplate.

Works with FastAPI, Django, Spring Boot, Go, NestJS, Node.js.

Under the hood it's a 14-stage pipeline with 8 specialist agents (architect, 
implementer, reviewer, doubter, critic, wirer, test-author, service-author). 
Cost is ~$0.30-0.45 per feature via the Anthropic API. There's also a free 
--templated fallback mode that uses zero tokens.

It's available in the Claude Code community plugin marketplace:
  claude plugin add one-shot-prompting

Or install directly:
  https://github.com/usmanmughaltaleemabad/One-Shot-Plugin

Happy to answer questions. Especially interested in hearing from people who 
try it on a real codebase — what breaks, what's missing.
```

## Tips
- Reply to every comment within the first 2 hours
- Don't upvote your own post (flagged)
- If it gets traction, post in r/ClaudeAI the same morning linking to the HN thread
