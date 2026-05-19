---
type: router
last_verified: 2026-05-19
owner: claude
---

# FastAPI Payment Processor — Harness

## Default agent behaviour — READ THIS FIRST

When working in this project, **always use agents before scripts**:

| Situation | Use this agent — NOT scripts directly |
|---|---|
| After generating or editing code | Invoke **`fastapi-reviewer`** automatically |
| Debugging an error | Invoke **`fastapi-debugger`** with the error message |
| Unsure about async/Pydantic pattern | Read `.claude/standards/code-style-fastapi.md` first |
| Security question | Read `.claude/standards/security-rules.md` first |

**Automatic review rule:** Any time you write or edit a `.py` file in this
project, immediately after writing invoke `fastapi-reviewer` on it. Do not
wait to be asked. The reviewer is the primary quality gate — scripts are
only for deterministic checks the reviewer cannot do (syntax, imports).

## Project standards (agents enforce these)

1. All endpoint functions `async def` — no blocking I/O
2. Business logic in `service.py` — routers only delegate
3. All request/response via Pydantic models
4. No hardcoded secrets — `os.environ` only
5. Coverage ≥ 80% before any `--apply`
6. Alembic migration required for any schema change

## Available agents

- **`fastapi-reviewer`** — checks async correctness, service-layer separation,
  Pydantic use, security. Run after every code write.
- **`fastapi-debugger`** — diagnoses 422 errors, async/await mistakes,
  SQLAlchemy session issues, Alembic conflicts.

## Standards reference (agents use these)

- `.claude/standards/code-style-fastapi.md` — router + schema + service patterns
- `.claude/standards/testing-rules.md` — pytest + httpx, 80% coverage floor
- `.claude/standards/security-rules.md` — bcrypt, JWT, no raw SQL

## Scripts are the fallback

`scripts/` exist for deterministic checks agents cannot do: syntax validation,
import resolution, migration generation. Do NOT reach for scripts when an agent
can do the reasoning.
