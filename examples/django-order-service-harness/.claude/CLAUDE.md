---
type: router
last_verified: 2026-05-19
owner: claude
---

# Django Order Service — Harness

Working harness for a Django 4.2 + DRF project.

| For... | See... |
|---|---|
| Code style | `.claude/standards/code-style-django.md` |
| Testing rules | `.claude/standards/testing-rules.md` |
| Security rules | `.claude/standards/security-rules.md` |
| Full template | `one-shot-prompting/.claude/examples/DJANGO_HARNESS_TEMPLATE.md` |

## Critical rules

1. ViewSets for CRUD, APIView only for custom logic
2. Serializers validate all input — never trust request.data directly
3. Business logic in service functions, not in views
4. Use `select_related` / `prefetch_related` — no N+1 queries
5. All tests use `APITestCase` or `pytest-django`
