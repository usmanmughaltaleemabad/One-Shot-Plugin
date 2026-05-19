---
type: standards
last_verified: 2026-05-19
owner: claude
---

# Node.js Security Rules

- Secrets from `process.env` only — never hardcoded, never in source
- Use `helmet` middleware for HTTP security headers
- Input validation: Zod or class-validator on all request bodies
- No `eval()`, no `Function()`, no `child_process.exec` with user input
- SQL: use parameterized queries (Prisma/TypeORM) — no string interpolation
- Passwords: `bcrypt` with saltRounds ≥ 12
