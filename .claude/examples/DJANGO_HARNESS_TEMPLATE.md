---
type: example
last_verified: 2026-05-17
owner: claude
---

# Django Project Harness Template

**Framework**: Django 4.2+  
**Features**: DRF, async views, testing  
**Use this**: If your project uses Django + DRF

---

## File Structure

Copy this structure to your Django project:

```
your-django-project/
├── .claude/
│   ├── CLAUDE.md                    ← Main entry point
│   ├── HARNESS.md                   ← Link to this
│   ├── hooks/
│   │   ├── pre_tool_use.sh
│   │   ├── post_tool_use.sh
│   │   └── stop.sh
│   ├── agents/
│   │   ├── code-reviewer.md
│   │   ├── architect.md
│   │   └── debugger.md
│   ├── standards/
│   │   ├── code-style-django.md
│   │   ├── testing-rules.md
│   │   └── security-rules.md
│   ├── skills/
│   │   └── (optional custom tools)
│   └── beads/
│       ├── status.jsonl
│       ├── decisions.jsonl
│       └── failures.jsonl
├── manage.py
├── requirements.txt
└── ...
```

---

## .claude/CLAUDE.md (Customize for your project)

```markdown
---
type: router
last_verified: 2026-05-17
owner: claude
---

# Your Django Project

## Quick Links

| For... | See... |
|--------|--------|
| Code style | `.claude/standards/code-style-django.md` |
| Adding API endpoints | `.claude/examples/api-endpoint-recipe.md` |
| Testing | `.claude/standards/testing-rules.md` |
| Security | `.claude/standards/security-rules.md` |
| Running generation | `/one-shot-prompting:one-shot-generator` |
| Code review | `.claude/agents/code-reviewer.md` |

## Critical Rules

1. All new endpoints must have 80%+ test coverage
2. All code must pass `python manage.py check` + `black --check`
3. Database queries must use ORM (no raw SQL)
4. All API responses use DRF serializers

## Framework Info

- **Version**: Django 4.2 + DRF 3.14
- **Database**: PostgreSQL (async)
- **Testing**: pytest + pytest-django
- **Linting**: black, flake8, isort
```

---

## .claude/standards/code-style-django.md

```markdown
---
type: standards
last_verified: 2026-05-17
owner: claude
---

# Django Code Style Standards

## File Organization

```
myapp/
├── models.py          ← Django models
├── views.py           ← Class-based views
├── serializers.py     ← DRF serializers
├── urls.py            ← URL routing
├── admin.py           ← Admin configuration
├── management/        ← Custom commands
├── migrations/        ← Database migrations
├── tests/
│   ├── test_models.py
│   ├── test_views.py
│   ├── test_serializers.py
│   └── conftest.py
```

## Code Style

- **Formatting**: Use `black` (line length: 100)
- **Import order**: `isort` (stdlib, third-party, local)
- **Linting**: `flake8` (no errors, warnings OK)
- **Type hints**: Required on function signatures

## Models

```python
class User(models.Model):
    """User account (auth)."""
    
    email = models.EmailField(unique=True, max_length=255)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['email'])]
    
    def __str__(self) -> str:
        return self.email
```

## Views

```python
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

class UserViewSet(viewsets.ModelViewSet):
    """User CRUD operations."""
    
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['post'])
    def set_password(self, request, pk=None):
        """Change user password."""
        user = self.get_object()
        serializer = SetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            user.set_password(serializer.data['new_password'])
            user.save()
            return Response({'status': 'password set'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
```

## Serializers

```python
from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    """User serializer."""
    
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'created_at']
        read_only_fields = ['id', 'created_at']
```
```

---

## .claude/standards/testing-rules.md

```markdown
---
type: standards
last_verified: 2026-05-17
owner: claude
---

# Testing Standards

## Minimum Coverage: 80%

Run coverage:
```bash
pytest --cov=. --cov-report=term-missing
```

## Test Structure

```
tests/
├── conftest.py          ← Fixtures
├── test_models.py       ← Model tests
├── test_views.py        ← View/API tests
├── test_serializers.py  ← Serializer tests
└── factories.py         ← Test data factories
```

## Writing Tests

```python
import pytest
from .factories import UserFactory

@pytest.mark.django_db
class TestUserAPI:
    """User API tests."""
    
    def test_list_users(self, client):
        """GET /users/ returns all users."""
        user1 = UserFactory()
        user2 = UserFactory()
        
        response = client.get('/api/users/')
        assert response.status_code == 200
        assert len(response.json()) == 2
    
    def test_create_user(self, client):
        """POST /users/ creates new user."""
        data = {'email': 'test@example.com', 'name': 'Test'}
        response = client.post('/api/users/', data)
        assert response.status_code == 201
        assert response.json()['email'] == 'test@example.com'
```
```

---

## .claude/standards/security-rules.md

```markdown
---
type: standards
last_verified: 2026-05-17
owner: claude
---

# Security Standards

## Database Security

- ❌ No raw SQL: Use ORM exclusively
- ❌ No SQL injection: Always use parameterized queries
- ✅ Use Django ORM for all queries

```python
# ❌ WRONG
users = User.objects.raw(f"SELECT * FROM users WHERE id = {user_id}")

# ✅ CORRECT
users = User.objects.filter(id=user_id)
```

## API Security

- ✅ All endpoints require authentication (except login/signup)
- ✅ Use DRF permissions (IsAuthenticated, IsAdminUser, etc.)
- ✅ Rate limiting on public endpoints
- ✅ CORS configured (whitelist domains)

```python
# ✅ CORRECT
class ProtectedView(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]
```

## Secrets Management

- ❌ No passwords/keys in code
- ✅ Use environment variables (python-decouple)
- ✅ .env file in .gitignore

```python
from decouple import config

SECRET_KEY = config('SECRET_KEY')
STRIPE_API_KEY = config('STRIPE_API_KEY')
```
```

---

## .claude/agents/code-reviewer.md

```markdown
---
name: code-reviewer
description: Reviews Django code for quality, security, and style
owner: claude
---

# Django Code Reviewer

## Review Checklist

- [ ] Code follows BLACK formatting (run: `black .`)
- [ ] Imports organized with ISORT (run: `isort .`)
- [ ] No flake8 errors (run: `flake8 .`)
- [ ] Models have docstrings
- [ ] Views have permission checks
- [ ] All new code has tests (80%+ coverage)
- [ ] No raw SQL queries
- [ ] No hardcoded secrets
- [ ] Serializers validate input

## Invoke

When you've written Django code:
```
/call:code-reviewer @/path/to/file.py
```

## Output

The reviewer will:
1. Check against standards
2. Flag issues
3. Suggest fixes
4. Approve or request changes
```

---

## .claude/hooks/pre_tool_use.sh

```bash
#!/bin/bash
# Enforce standards before Claude runs tools

# Block git push without approval
if [[ "$COMMAND" =~ git\ push ]]; then
    if ! grep -q "APPROVED: git push" .claude/beads/status.jsonl 2>/dev/null; then
        echo "❌ Code review required before git push"
        echo "   Invoke: /call:code-reviewer"
        exit 1
    fi
fi

# Block writing to models without migrations
if [[ "$COMMAND" =~ "Write" && "$FILE" =~ "models.py" ]]; then
    echo "⚠️  Remember to run: python manage.py makemigrations"
fi
```

---

## .claude/hooks/post_tool_use.sh

```bash
#!/bin/bash
# Validate Django code after writing

# Check Python syntax
if [[ "$FILE" =~ \.py$ ]]; then
    python -m py_compile "$FILE"
    if [ $? -ne 0 ]; then
        echo "❌ Python syntax error"
        exit 1
    fi
fi

# Check Django admin.py validity
if [[ "$FILE" =~ "admin.py" ]]; then
    python manage.py check
    if [ $? -ne 0 ]; then
        echo "❌ Django check failed"
        exit 1
    fi
fi
```

---

## Getting Started

### 1. Copy this template to your Django project

```bash
cp -r .claude/examples/DJANGO_HARNESS_TEMPLATE.md your-project/.claude/
```

### 2. Customize .claude/CLAUDE.md
- Update project name
- Update critical rules (specific to your app)
- Update framework version if needed

### 3. Test the harness

```bash
# Generate a simple endpoint
/one-shot-prompting:one-shot-generator "add a User list endpoint" @/your-project

# Check that:
# 1. Code follows your standards
# 2. Tests are included
# 3. Hooks validate it
```

### 4. Share with team

```bash
git add .claude/
git commit -m "feat: Add project harness configuration"
git push
```

---

## Reference Files

- Main harness spec: `.claude/HARNESS.md`
- Current status: `IMPLEMENTATION_STATUS.md`  (historical tier-2 plan archived in `.archive/v3-snapshots/`)
- ONE SHOT Plugin: `/one-shot-prompting:one-shot-generator`

