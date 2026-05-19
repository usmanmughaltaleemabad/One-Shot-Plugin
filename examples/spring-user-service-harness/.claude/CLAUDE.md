---
type: router
last_verified: 2026-05-19
owner: claude
---

# Spring Boot User Service — Harness

## Default agent behaviour — READ THIS FIRST

When working in this project, **always use agents before scripts**:

| Situation | Use this agent — NOT scripts directly |
|---|---|
| After generating or editing code | Invoke **`spring-reviewer`** automatically |
| Debugging an error | Invoke **`spring-debugger`** with the error message |
| Unsure about controller/service pattern | Read `.claude/standards/code-style-spring.md` first |
| Security question | Read `.claude/standards/security-rules.md` first |

**Automatic review rule:** Any time you write or edit a `.java` file in this
project, immediately after writing invoke `spring-reviewer` on it. Do not
wait to be asked. The reviewer is the primary quality gate.

## Project standards (agents enforce these)

1. Controllers only delegate — zero business logic in `@RestController`
2. Business logic in `@Service` classes only
3. `@Valid` + Bean Validation on all request DTOs
4. `@Transactional` on service methods that mutate state
5. No hardcoded secrets — `${ENV_VAR}` in `application.properties` only
6. Flyway migration for every schema change

## Available agents

- **`spring-reviewer`** — checks layering violations, missing validation,
  N+1 queries, missing `@Transactional`. Run after every code write.
- **`spring-debugger`** — diagnoses `LazyInitializationException`, circular
  dependencies, Flyway conflicts, `MethodArgumentNotValidException`.

## Standards reference

- `.claude/standards/code-style-spring.md` — controller + service + repo patterns
- `.claude/standards/testing-rules.md` — SpringBootTest, MockMvc, JaCoCo 80%
- `.claude/standards/security-rules.md` — BCrypt, JWT, no native SQL

## Scripts are the fallback

Use scripts only for deterministic checks. Agents handle all reasoning.
