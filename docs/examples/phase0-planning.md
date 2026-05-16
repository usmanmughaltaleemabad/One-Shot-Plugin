---
type: reference
last_verified: 2026-05-16
owner: claude
---

# Phase 0: Silent Planning & Verification — Walkthrough

How the plugin silently evaluates options and verifies code quality without asking the user.

---

## What Phase 0 Does

**Phase 0 (4 modules):** Foundation - planning engine, verification harness, slash commands, zero-question UX.

When you ask the plugin: `"add user authentication"`

1. **Analyzer** detects your framework (Django/FastAPI/Spring/Go)
2. **Planner** silently evaluates 6 critical decisions (async, ORM, testing, errors, logging, validation)
3. **Generator** creates code matching those decisions
4. **Verifier** confirms code quality before showing you the result
5. **User sees:** Working code, no questions asked

---

## Walkthrough: Authentication Feature

### Command
```bash
/one-shot-prompting:one-shot-generator "add JWT authentication" @examples/django-rest-api
```

### What Happens (Behind the Scenes)

#### Step 1: Codebase Analysis
```
Analyzer runs: python analyze_codebase.py "add JWT authentication @examples/django-rest-api"

Output (CODEBASE CONTEXT):
  Framework: Django 4.2
  ORM: Django ORM
  Testing: pytest
  Auth: django.contrib.auth
  API: Django REST Framework
  Async: No (synchronous)
```

#### Step 2: Silent Planning
```
Planner runs: python plan_decisions.py < codebase_context

Decision: "JWT Tokens" (confidence 9/10)
  Rationale: DRF has built-in token support, JWT is industry standard, codebase uses Django

Decision: "Synchronous Views" (confidence 9/10)
  Rationale: No async/await in codebase, synchronous is the default

Decision: "pytest Fixtures" (confidence 10/10)
  Rationale: Modern Django testing standard

Decision: "Django Exceptions" (confidence 9/10)
  Rationale: DRF returns DRF exceptions, not custom types

Decision: "Structlog" (confidence 6/10)
  Rationale: No logging config detected, structlog is modern choice

Decision: "Pydantic Validators" (confidence 7/10)
  Rationale: Using DRF serializers, could use Pydantic for extra validation
```

#### Step 3: Code Generation
```
Generator sees all decisions and creates:

models.py:
  - CustomUser model (extends Django User)
  - UserProfile with JWT metadata

serializers.py:
  - UserSerializer with JWT fields
  - LoginSerializer with email + password

views.py:
  - LoginView (POST returns JWT)
  - RefreshTokenView (POST with refresh token returns new access)
  - ValidateTokenView (GET returns token status)

urls.py:
  - /api/auth/login/ → LoginView
  - /api/auth/refresh/ → RefreshTokenView
  - /api/auth/validate/ → ValidateTokenView

tests/test_auth.py:
  - Test successful login
  - Test invalid credentials
  - Test token refresh
  - Test expired token
  - Test token validation

README.md:
  - Setup: pip install djangorestframework-simplejwt
  - Configuration snippets
  - Example API calls
```

#### Step 4: Verification
```
Verifier runs: python verify_generated.py "models.py, serializers.py, views.py, tests/test_auth.py"

Checks:
  ✓ Python syntax valid
  ✓ Imports resolve (JWT library available)
  ✓ DRF serializer patterns correct
  ✓ Views inherit from correct DRF classes
  ✓ Tests use pytest fixtures correctly
  ✓ No hardcoded secrets
  ✓ Code matches Django conventions
```

#### Step 5: User Gets Result
```
✅ All checks passed. Generated code:

models.py (89 lines) — CustomUser + UserProfile
serializers.py (156 lines) — Login + serialization
views.py (234 lines) — Auth endpoints with token logic
tests/test_auth.py (167 lines) — 8 test cases
GENERATED_README.md — Setup instructions
```

---

## Phase 0 Prevents Common Mistakes

### Without Phase 0
- Dev asks for "auth" in async FastAPI project
- Plugin defaults to Django patterns
- Generated code uses sync views (❌ doesn't work in FastAPI)

### With Phase 0
- **Analyzer** detects: FastAPI, async/await, Pydantic
- **Planner** picks: Async views, JWT + Bearer tokens, Pydantic validators
- **Generator** creates: async def, Bearer schema, Pydantic model validation
- **Verifier** confirms: Code syntax, async patterns, Pydantic model structure
- Dev gets: Working async auth ✅

---

## Key Phase 0 Modules

| Module | Purpose | Used When |
|--------|---------|-----------|
| plan_decisions.py | Score 6 critical decisions without asking user | Every generation |
| verify_generated.py | Confirm syntax, patterns, no secrets | Before showing code |
| command_overrides.py | Register slash command variants | Plugin loads |
| zero_questions_ux.py | Intelligent fallbacks for missing context | Analysis incomplete |

---

## When Phase 0 Asks Questions (Never)

**Phase 0 philosophy:** Zero questions, intelligent defaults.

If framework detection is ambiguous:
- Default: Python + Django (most common)
- Document assumption in README
- Provide slash command override: `--framework fastapi`

If ORM choice unclear:
- Default: SQLAlchemy (most portable)
- Fall back to plain SQL if no ORM detected
- User can override: `--orm django`

---

## Test This Yourself

### 1. Analyzer Only
```bash
python skills/one-shot-generator/scripts/analyze_codebase.py "test" @examples/django-rest-api
# Output: Detected framework, ORM, testing library, patterns
```

### 2. Planner Only
```bash
python skills/one-shot-generator/scripts/analyze_codebase.py "test" @examples/django-rest-api | \
  python skills/one-shot-generator/scripts/plan_decisions.py
# Output: CODEBASE CONTEXT + PLAN DECISIONS (6 decisions with scores)
```

### 3. Full Generation
```bash
/one-shot-prompting:one-shot-generator "add JWT auth" @examples/django-rest-api
# Output: Complete code + tests + README (all files)
```

---

## Next: Phase 1

Phase 0 generates single features in isolation. Phase 1 handles **integration**:
- Multi-file organization
- Auto-wiring into existing project
- Generating migrations
- Framework-specific DI setup

See [phase1-integration.md](phase1-integration.md)

---

**The Magic:** Phase 0 makes code generation look effortless. No prompting, no back-and-forth, no "did you mean?" — just working code.
