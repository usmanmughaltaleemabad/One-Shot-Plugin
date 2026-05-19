---
type: router
last_verified: 2026-05-19
owner: claude
---

# Node.js Real-Time API — Harness

Working harness for a Node.js + TypeScript + Express project.

| For... | See... |
|---|---|
| Code style | `.claude/standards/code-style-node.md` |
| Testing rules | `.claude/standards/testing-rules.md` |
| Security rules | `.claude/standards/security-rules.md` |
| Code review | `/call:node-reviewer` |
| Debugging | `/call:node-debugger` |

## Critical rules

1. No `any` types — use interfaces or `z.infer<>` from Zod
2. All async route handlers use try/catch and pass errors to `next(err)`
3. Business logic in service layer, not in route handlers
4. All request bodies validated with Zod or class-validator
5. `helmet` and `cors` configured in app entry point
