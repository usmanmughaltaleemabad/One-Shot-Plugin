---
type: router
last_verified: 2026-05-19
owner: claude
---

# FastAPI Payment Processor — Harness

This is a working harness example. Copy the `.claude/` directory into your own FastAPI project and customise.

| For... | See... |
|---|---|
| Code style + patterns | `.claude/standards/code-style-fastapi.md` |
| Testing rules | `.claude/standards/testing-rules.md` |
| Security rules | `.claude/standards/security-rules.md` |
| Code review | `/call:fastapi-reviewer` |
| Debugging | `/call:fastapi-debugger` |
| Full harness template | `one-shot-prompting/.claude/examples/FASTAPI_HARNESS_TEMPLATE.md` |

## Critical rules

1. All endpoint functions must be `async def`
2. Business logic in service layer — routers only delegate
3. All request/response via Pydantic models
4. No hardcoded secrets — environment variables only
5. Coverage ≥ 80% before any `--apply`
