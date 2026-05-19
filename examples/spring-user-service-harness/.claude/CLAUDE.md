---
type: router
last_verified: 2026-05-19
owner: claude
---

# Spring Boot User Service — Harness

Working harness for a Spring Boot 3.x + Spring Data JPA + DRF project.

| For... | See... |
|---|---|
| Code style | `.claude/standards/code-style-spring.md` |
| Testing rules | `.claude/standards/testing-rules.md` |
| Security rules | `.claude/standards/security-rules.md` |
| Code review | `/call:spring-reviewer` |
| Debugging | `/call:spring-debugger` |

## Critical rules

1. Controller only delegates — no business logic in controllers
2. All request DTOs annotated with `@Valid` + Bean Validation
3. Business logic in `@Service` classes only
4. `@Transactional` on all service methods that mutate state
5. No hardcoded secrets — environment substitution in properties
