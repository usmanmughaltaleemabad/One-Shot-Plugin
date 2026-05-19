---
type: router
last_verified: 2026-05-19
owner: claude
---

# Django Order Service — Harness

## Default agent behaviour — READ THIS FIRST

When working in this project, **always use agents before scripts**:

| Situation | Use this agent — NOT scripts directly |
|---|---|
| After generating or editing code | Invoke **`django-reviewer`** automatically |
| Debugging an error | Invoke **`django-debugger`** with the error message |
| Unsure about ViewSet/serializer pattern | Read `.claude/standards/code-style-django.md` first |
| Security question | Read `.claude/standards/security-rules.md` first |

**Automatic review rule:** Any time you write or edit a `.py` file in this
project, immediately after writing invoke `django-reviewer` on it. Do not
wait to be asked. The reviewer is the primary quality gate.

## Project standards (agents enforce these)

1. ViewSets for CRUD — `APIView` only for custom logic
2. Business logic in `services.py` — views only delegate
3. Serializers validate all input — never trust `request.data` directly
4. `select_related` / `prefetch_related` on all list views — no N+1
5. Explicit `permission_classes` on every ViewSet
6. Migrations present for every model change

## Available agents

- **`django-reviewer`** — checks serializer validation, N+1 queries,
  permission gaps, service-layer separation. Run after every code write.
- **`django-debugger`** — diagnoses migration conflicts, N+1 queries,
  serializer validation failures, Celery task issues.

## Standards reference

- `.claude/standards/code-style-django.md` — ViewSet + serializer + service patterns
- `.claude/standards/testing-rules.md` — APITestCase, pytest-django, 80% floor
- `.claude/standards/security-rules.md` — permissions, no raw SQL, secrets

## Scripts are the fallback

Use scripts only for deterministic checks: syntax validation, migration
generation. Agents handle all reasoning tasks.
