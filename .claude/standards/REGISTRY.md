---
type: reference
last_verified: 2026-05-21
owner: usman
---

# Standards Registry

Master index of all domain rules enforced in code generation.

## How Standards Work

1. **Define** — each standard in its own file (generated-code.md, testing.md, etc.)
2. **Enforce** — via hooks (PreToolUse blocks, PostToolUse validation) or agent checks
3. **Extend** — add new standards by creating a file + updating REGISTRY

## Active Standards (8 total)

| ID | Category | Rule | Enforcement | Exempt? |
|---|---|---|---|---|
| GEN-001 | Generated Code | All generated code must include tests | Hook: PostToolUse scans for test file | marked @skip-test |
| GEN-002 | Generated Code | Foreign key relationships auto-validated | Hook: PostToolUse validates FK syntax | N/A |
| GEN-003 | Security | Security scan (OWASP top 10) before ship | Agent: reviewer runs bandit/semgrep | marked @unsafe |
| GEN-004 | API Documentation | API endpoints documented in OpenAPI | Hook: PostToolUse checks openapi.json | marked @undocumented |
| GEN-005 | Code Quality | All models include type hints | Hook: PostToolUse scans types | marked @untyped |
| GEN-006 | Security | No hardcoded secrets (scan with truffleHog) | Hook: PostToolUse runs truffleHog | none |
| GEN-007 | Migrations | Migrations reversible (Alembic UP/DOWN) | Agent: migration-verifier runs migrations | none |
| GEN-008 | Performance | N+1 query detection on ORMs | Agent: performance-auditor scans ORM | marked @slow-ok |

## Standard Files

- [generated-code.md](generated-code.md) — GEN-001, GEN-002, GEN-005
- [testing.md](testing.md) — Test coverage, isolation requirements
- [security.md](security.md) — GEN-003, GEN-006
- [api-documentation.md](api-documentation.md) — GEN-004
- [performance.md](performance.md) — GEN-008
- [fk-validation.md](fk-validation.md) — GEN-002 detailed rules

## How to Add a New Standard

1. Create a new file (e.g., `.claude/standards/logging.md`)
2. Include YAML frontmatter + rule definition (see any file for template)
3. Add row to REGISTRY table
4. (Optional) Wire into hook if enforcement is automated

See [README.md](README.md) for details.
