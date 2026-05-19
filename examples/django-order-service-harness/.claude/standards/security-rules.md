---
type: standards
last_verified: 2026-05-19
owner: claude
---

# Django Security Rules

- Use DRF serializer validation — never access `request.data` raw
- Permissions on every ViewSet: `permission_classes = [IsAuthenticated]` minimum
- No raw SQL: use ORM or `django.db.connection` with parameterized queries only
- CSRF: DRF handles via SessionAuthentication — do not disable
- Secrets: `django-environ` or `python-decouple` from environment, never `settings.py` hardcoded
