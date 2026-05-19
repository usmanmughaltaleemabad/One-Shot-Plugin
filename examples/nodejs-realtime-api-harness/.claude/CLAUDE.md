---
type: router
last_verified: 2026-05-19
owner: claude
---

# Node.js Realtime API — Harness

## Default agent behaviour — READ THIS FIRST

When working in this project, **always use agents before scripts**:

| Situation | Use this agent — NOT scripts directly |
|---|---|
| After generating or editing code | Invoke **`node-reviewer`** automatically |
| Debugging an error | Invoke **`node-debugger`** with the error message |
| Unsure about route/service pattern | Read `.claude/standards/code-style-node.md` first |
| Security question | Read `.claude/standards/security-rules.md` first |

**Automatic review rule:** Any time you write or edit a `.ts` or `.js` file
in this project, immediately after writing invoke `node-reviewer` on it.
Do not wait to be asked. The reviewer is the primary quality gate.

## Project standards (agents enforce these)

1. No `any` types — use interfaces or `z.infer<>` everywhere
2. Business logic in `*.service.ts` — routes only call services
3. All request bodies validated with Zod or class-validator
4. `async/await` throughout — no bare `.then()/.catch()` chains
5. Errors passed to `next(err)` — never swallowed silently
6. `helmet` + `cors` configured at app entry point

## Available agents

- **`node-reviewer`** — checks type safety, error handling, service-layer
  separation, security headers. Run after every code write.
- **`node-debugger`** — diagnoses unhandled rejections, TypeORM issues,
  WebSocket disconnects, JWT expiry.

## Standards reference

- `.claude/standards/code-style-node.md` — Express + TypeScript patterns
- `.claude/standards/testing-rules.md` — Jest + supertest, 80% coverage floor
- `.claude/standards/security-rules.md` — helmet, bcrypt, no eval, parameterized SQL

## Scripts are the fallback

Use scripts only for deterministic checks. Agents handle all reasoning.
