---
type: router
last_verified: 2026-05-19
owner: claude
---

# Go Product Service — Harness

Working harness for a Go + Chi/net/http project.

| For... | See... |
|---|---|
| Code style | `.claude/standards/code-style-go.md` |
| Testing rules | `.claude/standards/testing-rules.md` |
| Security rules | `.claude/standards/security-rules.md` |
| Code review | `/call:go-reviewer` |
| Debugging | `/call:go-debugger` |

## Critical rules

1. All errors checked — no `_ =` on error returns
2. Business logic in `internal/service/` — handlers only parse and delegate
3. No `fmt.Sprintf` into SQL queries — parameterized only
4. Context passed through the full call chain
5. No package-level globals for DB connections — inject via struct fields
