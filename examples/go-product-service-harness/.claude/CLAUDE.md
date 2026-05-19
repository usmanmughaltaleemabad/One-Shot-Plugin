---
type: router
last_verified: 2026-05-19
owner: claude
---

# Go Product Service — Harness

## Default agent behaviour — READ THIS FIRST

When working in this project, **always use agents before scripts**:

| Situation | Use this agent — NOT scripts directly |
|---|---|
| After generating or editing code | Invoke **`go-reviewer`** automatically |
| Debugging an error | Invoke **`go-debugger`** with the error message |
| Unsure about handler/service pattern | Read `.claude/standards/code-style-go.md` first |
| Security question | Read `.claude/standards/security-rules.md` first |

**Automatic review rule:** Any time you write or edit a `.go` file in this
project, immediately after writing invoke `go-reviewer` on it. Do not wait
to be asked. The reviewer is the primary quality gate.

## Project standards (agents enforce these)

1. All errors checked — no `_ =` on error returns
2. Business logic in `internal/service/` — handlers only parse + delegate
3. Context passed through the full call chain
4. No `fmt.Sprintf` in SQL queries — parameterized only
5. Secrets from `os.Getenv` only — never in source
6. Table-driven tests for all service functions

## Available agents

- **`go-reviewer`** — checks error handling, service-layer separation,
  SQL safety, context propagation, idiomatic style. Run after every write.
- **`go-debugger`** — diagnoses nil dereferences, context cancellation,
  DB pool exhaustion, goroutine leaks.

## Standards reference

- `.claude/standards/code-style-go.md` — handler + service + error patterns
- `.claude/standards/testing-rules.md` — table-driven tests, 80% coverage
- `.claude/standards/security-rules.md` — bcrypt, no exec with user input, parameterized SQL

## Scripts are the fallback

Use scripts only for deterministic checks (`gofmt`, syntax). Agents handle
all reasoning.
