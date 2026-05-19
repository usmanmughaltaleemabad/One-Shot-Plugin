---
type: standards
last_verified: 2026-05-19
owner: claude
---

# Go Security Rules

- Secrets from environment via `os.Getenv` — never in source
- SQL: `database/sql` with parameterized queries only — never `fmt.Sprintf` into queries
- Input validation: validate struct fields before business logic
- Passwords: `golang.org/x/crypto/bcrypt` with cost ≥ 12
- No `os/exec` with user-controlled input
