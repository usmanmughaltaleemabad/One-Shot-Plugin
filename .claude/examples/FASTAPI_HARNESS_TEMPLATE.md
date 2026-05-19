---
type: example
last_verified: 2026-05-17
owner: claude
---

# FastAPI Project Harness Template

**Framework**: FastAPI 0.104+  
**Features**: SQLAlchemy async, Pydantic, async/await  
**Use this**: If your project uses FastAPI + async

---

## File Structure

```
your-fastapi-project/
├── .claude/
│   ├── CLAUDE.md
│   ├── standards/
│   │   ├── code-style-fastapi.md
│   │   ├── testing-rules.md
│   │   └── security-rules.md
│   ├── agents/
│   │   ├── code-reviewer.md
│   │   ├── fastapi-expert.md
│   │   └── performance-analyzer.md
│   ├── hooks/
│   │   ├── pre_tool_use.sh
│   │   └── post_tool_use.sh
│   └── beads/
│       ├── status.jsonl
│       └── decisions.jsonl
├── app/
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── api/
│   │   ├── routes/
│   │   └── dependencies.py
│   └── db/
│       └── session.py
├── tests/
│   ├── conftest.py
│   ├── test_api.py
│   └── test_models.py
└── requirements.txt
```

---

## .claude/CLAUDE.md

```markdown
---
type: router
last_verified: 2026-05-19
owner: claude
---

# FastAPI Project

## Default agent behaviour — READ THIS FIRST

When working in this project, **always use agents before scripts**:

| Situation | Use this agent — NOT scripts directly |
|---|---|
| After generating or editing code | Invoke **`fastapi-reviewer`** automatically |
| Debugging an error | Invoke **`fastapi-debugger`** with the error message |
| Unsure about async/Pydantic pattern | Read `.claude/standards/code-style-fastapi.md` first |
| Security question | Read `.claude/standards/security-rules.md` first |

**Automatic review rule:** After every `.py` file write, invoke
`fastapi-reviewer` immediately. Do not wait to be asked.

## Critical rules (agents enforce these)

1. All endpoints `async def` — no blocking I/O
2. Business logic in service layer — routers only delegate
3. All request/response via Pydantic models
4. No hardcoded secrets — `os.environ` only
5. Coverage ≥ 80% before any `--apply`

## Framework

- **Version**: FastAPI 0.104 + SQLAlchemy async
- **Database**: PostgreSQL (asyncpg)
- **Testing**: pytest + httpx
```

---

## .claude/standards/code-style-fastapi.md

```markdown
---
type: standards
last_verified: 2026-05-17
owner: claude
---

# FastAPI Code Style

## Router Structure

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas import UserCreate, UserResponse

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/", response_model=list[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """List all users."""
    query = select(User).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create new user."""
    user = User(**user_in.dict())
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
```

## Pydantic Models

```python
from pydantic import BaseModel, EmailStr, Field

class UserBase(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserResponse(UserBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True
```

## Async Functions

```python
async def get_user_by_id(db: AsyncSession, user_id: int):
    """Get user by ID (async ORM query)."""
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()
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

# FastAPI Testing

## Minimum Coverage: 80%

```bash
pytest --cov=app --cov-report=term-missing
```

## Test Structure

```python
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine

@pytest.mark.asyncio
async def test_list_users(client: AsyncClient):
    """GET /users returns all users."""
    response = await client.get("/users/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_create_user(client: AsyncClient):
    """POST /users creates new user."""
    data = {
        "email": "test@example.com",
        "name": "Test User",
        "password": "securepassword123"
    }
    response = await client.post("/users/", json=data)
    assert response.status_code == 201
    assert response.json()["email"] == "test@example.com"
```

## conftest.py

```python
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

@pytest.fixture
async def client():
    """Test client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
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

# FastAPI Security

## Input Validation

- ✅ Always use Pydantic models for request bodies
- ✅ Validate all path/query parameters
- ❌ Never trust user input

```python
# ✅ CORRECT
@app.post("/users/")
async def create_user(user: UserCreate):  # Pydantic model
    # user is validated automatically
    pass
```

## Authentication

```python
from fastapi.security import HTTPBearer

security = HTTPBearer()

@app.get("/protected")
async def protected_route(token: str = Depends(security)):
    # Token is validated by dependency
    pass
```

## Database Security

- ✅ Use SQLAlchemy ORM exclusively
- ❌ No raw SQL
- ✅ Use parameterized queries

```python
# ❌ WRONG
query = f"SELECT * FROM users WHERE id = {user_id}"

# ✅ CORRECT
query = select(User).where(User.id == user_id)
```
```

---

## .claude/agents/fastapi-expert.md

```markdown
---
name: fastapi-expert
description: Reviews FastAPI code for async correctness, Pydantic validation, performance
owner: claude
---

# FastAPI Expert Agent

## Review Checklist

- [ ] All endpoints are async (no blocking I/O)
- [ ] All request/response use Pydantic models
- [ ] Database queries use SQLAlchemy async
- [ ] No blocking operations in async functions
- [ ] Proper dependency injection (Depends)
- [ ] Error handling with HTTPException
- [ ] Tests cover 80%+

## Common Issues

❌ Blocking I/O in async function:
```python
import requests  # BLOCKING!
@app.get("/")
async def get_data():
    response = requests.get("https://api.example.com")  # ❌ Blocks!
```

✅ Use async HTTP client:
```python
import httpx
@app.get("/")
async def get_data():
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com")  # ✅ Async
```
```

---

## .claude/hooks/post_tool_use.sh

```bash
#!/bin/bash

# Validate Python syntax
if [[ "$FILE" =~ \.py$ ]]; then
    python -m py_compile "$FILE"
    if [ $? -ne 0 ]; then
        echo "❌ Python syntax error"
        exit 1
    fi
fi

# Run ruff check
if [[ "$FILE" =~ "app/.*.py" ]]; then
    ruff check "$FILE" --fix
fi

# Validate Pydantic models
if [[ "$FILE" =~ "schemas.py" ]]; then
    python -c "from app.schemas import *; print('✅ Schemas valid')"
fi
```

---

## Getting Started

```bash
# 1. Copy template
cp .claude/examples/FASTAPI_HARNESS_TEMPLATE.md your-project/.claude/CLAUDE.md

# 2. Customize
nano your-project/.claude/CLAUDE.md

# 3. Generate endpoint
/one-shot-prompting:one-shot-generator "add user authentication with JWT" @.

# 4. Test
pytest --cov=app --cov-report=term-missing
```

