---
type: standards
last_verified: 2026-05-19
owner: claude
---

# Spring Boot Security Rules

- Secrets from `application.properties` via env substitution (`${JWT_SECRET}`) — never hardcoded
- Passwords: BCryptPasswordEncoder with strength ≥ 12
- JWT: signed with HS256 minimum, expiry required
- No `permitAll()` on sensitive endpoints — explicit `hasRole()` or `hasAuthority()`
- SQL: use JPA/JPQL only — no string concatenation in queries
