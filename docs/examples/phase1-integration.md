---
type: reference
last_verified: 2026-05-16
owner: claude
---

# Phase 1: Integration & Auto-Wiring — Walkthrough

How the plugin integrates generated code into existing projects automatically, handling migrations, DI, and framework-specific configuration.

---

## What Phase 1 Does

**Phase 1 (8 modules):** Critical integration gaps - multi-file output formatting, auto-wiring into projects, migration generation, config setup, dependency injection, framework-specific command scaffolding, OpenAPI documentation, multi-handler orchestration.

When you ask the plugin: `"add user authentication with database to my project"`

1. **Analyzer** detects your framework, ORM, existing models
2. **Planner** (Phase 0) scores integration decisions
3. **Generator** (Phase 0) creates code
4. **Multi-File Formatter** (Phase 1) organizes output with dependency ordering
5. **Auto-Wirer** (Phase 1) modifies existing files (urls.py, settings.py, main.py, go.mod, etc.) to wire in the new code
6. **Migration Generator** (Phase 1) creates database migrations per framework
7. **Config Generator** (Phase 1) creates .env.example with new settings
8. **DI Injector** (Phase 1) adds Spring @Autowired, FastAPI Depends(), Go wire.go, NestJS providers
9. **Verifier** (Phase 0) confirms all changes are syntactically correct
10. **User sees:** Code ready to integrate, migrations already generated, no missing wiring

---

## Walkthrough: Authentication + Database Integration

### Command
```bash
/one-shot-prompting:one-shot-generator "add JWT auth with refresh tokens and user database" @examples/fastapi-async-api
```

### What Happens (Behind the Scenes)

#### Step 1: Analysis + Planning (Phase 0)
```
Framework: FastAPI 0.104.0
ORM: SQLAlchemy 2.0.23 (async)
Database: SQLite (with async support)
Auth: None (new implementation)
Async: Yes (async def)
Testing: pytest
```

**Phase 0 Decisions:**
- Async views ✓ (FastAPI is async)
- SQLAlchemy ORM ✓ (already detected)
- JWT + Bearer tokens ✓ (FastAPI standard)
- Pydantic validators ✓ (request/response validation)
- structlog ✓ (structured logging)
- pytest fixtures ✓ (FastAPI convention)

#### Step 2: Generation (Phase 0)
Generator creates 8 files:
```
models.py        — User model with hashed password, refresh_token table
schemas.py       — Pydantic UserCreate, UserLogin, TokenResponse
auth.py          — JWT encode/decode, hash_password, verify_password
routes.py        — /auth/register, /auth/login, /auth/refresh endpoints
security.py      — Depends() for current_user extraction
database.py      — Database session dependency (async SQLAlchemy)
migrations.py    — Alembic migration with User table
tests/
  test_auth.py   — Registration, login, refresh, invalid creds tests
```

#### Step 3: Multi-File Formatting (Phase 1)
**Task**: Order files for safe integration (dependencies first)

**Dependency Graph**:
```
models.py → schemas.py
          → security.py
          → auth.py
          → routes.py → main.py (existing)
          → tests/test_auth.py

database.py → models.py → ...
migrations.py → run after models.py synced
```

**Output Order**:
1. models.py (User, RefreshToken models)
2. database.py (SessionLocal, get_db)
3. auth.py (JWT logic)
4. schemas.py (Pydantic models)
5. security.py (current_user dependency)
6. routes.py (endpoints)
7. tests/test_auth.py (test suite)
8. migrations/versions/xxx_add_user_auth.py (Alembic migration)
9. .env.example (new config vars)
10. main.py.MERGE.patch (how to integrate into existing)

#### Step 4: Auto-Wiring (Phase 1)
**Task**: Modify existing files to register new endpoints

For FastAPI, this means:
1. Import auth routes into main.py
2. Register router with app
3. Add database session as dependency
4. Add JWT secret to settings

**Changes to main.py**:
```python
# BEFORE
from fastapi import FastAPI
app = FastAPI()

# AFTER (with auto-wiring)
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from routes import auth_router
from database import get_db

app = FastAPI()

# Register auth routes
app.include_router(auth_router, prefix="/auth", tags=["auth"])

# Add database dependency context
@app.on_event("startup")
async def startup():
    app.state.db = create_async_engine("sqlite+aiosqlite://./test.db")

@app.on_event("shutdown")
async def shutdown():
    await app.state.db.dispose()
```

#### Step 5: Migration Generation (Phase 1)
**Task**: Create database migration without manual SQL

Phase 1 detects:
- ORM: SQLAlchemy
- Framework: FastAPI
- Migration tool: Alembic (detected from requirements.txt)

Generates:
```python
# alembic/versions/001_add_user_auth.py
def upgrade():
    op.create_table(
        'user',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('email', sa.String, unique=True),
        sa.Column('hashed_password', sa.String),
        sa.Column('created_at', sa.DateTime, default=datetime.utcnow),
    )
    op.create_table(
        'refresh_token',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('user.id')),
        sa.Column('token', sa.String, unique=True),
        sa.Column('expires_at', sa.DateTime),
    )

def downgrade():
    op.drop_table('refresh_token')
    op.drop_table('user')
```

User runs:
```bash
alembic upgrade head
```

#### Step 6: Config Generation (Phase 1)
**Task**: Extract new config variables into .env.example

Generated .env.example:
```bash
# Database
DATABASE_URL=sqlite+aiosqlite:///./test.db
# (was not in original requirements)

# Auth
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_SECONDS=3600
JWT_REFRESH_EXPIRATION_DAYS=7
# (new, required by generated auth)
```

#### Step 7: DI Injection (Phase 1)
**Task**: Inject dependency injection code for framework

For FastAPI, this means Depends() is used:

```python
# In routes.py
from fastapi import APIRouter, Depends
from security import get_current_user
from models import User

auth_router = APIRouter()

@auth_router.post("/login")
async def login(
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db)  # ← FastAPI DI
):
    # ...

@auth_router.get("/me")
async def get_profile(
    current_user: User = Depends(get_current_user)  # ← DI: current user
):
    return current_user
```

For Spring Boot (different framework), Phase 1 would instead inject:
```java
@RestController
@RequestMapping("/auth")
public class AuthController {
    @Autowired  // ← Spring DI
    private UserService userService;
    
    @PostMapping("/login")
    public ResponseEntity<TokenResponse> login(@RequestBody LoginRequest req) {
        // userService injected by Spring
    }
}
```

#### Step 8: OpenAPI Documentation (Phase 1)
**Task**: Auto-generate Swagger/OpenAPI docs

Phase 1 injects OpenAPI metadata into FastAPI:

```python
# In routes.py
@auth_router.post(
    "/login",
    response_model=TokenResponse,
    summary="User Login",
    description="Authenticate user with email and password, returns JWT token",
    responses={
        200: {"description": "Login successful, JWT token returned"},
        401: {"description": "Invalid credentials"},
    }
)
async def login(
    email: str = Form(..., description="User email"),
    password: str = Form(..., description="User password"),
    db: AsyncSession = Depends(get_db)
):
    # ...
```

FastAPI auto-generates: `GET /docs` (Swagger UI) with all endpoints documented

#### Step 9: Multi-Handler Orchestration (Phase 1)
**Task**: If multiple services need same auth, coordinate wiring

Example: If project has both FastAPI `/api/v1` and WebSocket `/ws`:

```python
# database.py — shared across all handlers
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

engine = create_async_engine(DATABASE_URL, echo=True)

async def get_db():
    async with AsyncSession(engine) as session:
        yield session

# In main.py — orchestrate registration
app = FastAPI()

# Register REST API handler
app.include_router(rest_router, prefix="/api")

# Register WebSocket handler (reuses get_db)
@app.websocket("/ws/notifications")
async def websocket_endpoint(websocket: WebSocket, db: AsyncSession = Depends(get_db)):
    # Can use same database session as REST endpoints
```

#### Step 10: Verification + Merge Checklist
```
Verifier confirms:
✓ Imports resolve (SQLAlchemy, FastAPI, etc.)
✓ Pydantic models valid
✓ Database models use SQLAlchemy ORM correctly
✓ Async/await syntax correct
✓ Dependency injections use FastAPI Depends()
✓ Routes inherit from APIRouter
✓ Tests use pytest async fixtures
✓ Migration SQL valid
✓ No hardcoded secrets (uses env vars)
✓ Code follows FastAPI conventions
```

**Integration Checklist** (printed for user):
```
Phase 1 Integration Checklist:

□ Update .env from .env.example
□ Run: pip install -r requirements.txt
□ Run: alembic upgrade head (to create tables)
□ Run: pytest tests/test_auth.py (verify tests pass)
□ Review: main.py for router registration
□ Test: curl http://localhost:8000/auth/register (POST with email, password)
□ Test: curl http://localhost:8000/docs (Swagger UI)
```

---

## Phase 1 Prevents Common Mistakes

### Without Phase 1

Developer asks for "add user auth" in FastAPI project:
1. Plugin generates models.py, routes.py, tests
2. User manually wires into main.py (forgets to import)
3. User manually creates migration (or forgets)
4. User forgets to add JWT_SECRET_KEY to .env
5. Code doesn't run → debugging takes hours

### With Phase 1

1. **Multi-File Formatter** ensures models.py created before routes.py
2. **Auto-Wirer** modifies main.py: adds import, registers router
3. **Migration Generator** creates Alembic migration automatically
4. **Config Generator** creates .env.example with all required keys
5. **DI Injector** adds Depends() to all endpoint functions
6. **Verifier** confirms all syntax correct
7. Developer runs 3 commands: `pip install`, `alembic upgrade head`, `pytest`
8. Code works immediately ✅

---

## Walkthrough: Go Project (Different Framework)

### Command
```bash
/one-shot-prompting:one-shot-generator "add user auth to trading bot" @examples/go-trading-bot
```

### What Phase 1 Does Differently for Go

#### Analysis
```
Framework: Go 1.21
Database: No ORM detected (plain http.Handler)
HTTP: net/http
Auth: None (new)
Concurrency: sync.RWMutex for in-memory store
```

#### Generation creates:
```
models.go           — User struct, RefreshToken struct
auth.go            — JWT sign/verify, password hash
handlers.go        — RegisterHandler, LoginHandler, RefreshHandler
middleware.go      — AuthMiddleware for protected routes
migrations.go      — In-memory seed function (or SQL migration)
main.go.MERGE.patch — How to wire into existing server
wire.go            — Google Wire DI setup (if detected)
```

#### Phase 1 Auto-Wiring for Go
Instead of app.include_router(), Phase 1 modifies main.go:

```go
// BEFORE
func main() {
    http.HandleFunc("/health", healthHandler)
    http.HandleFunc("/orders/create", createOrderHandler)
    // ...
}

// AFTER (auto-wired by Phase 1)
func main() {
    // Existing routes
    http.HandleFunc("/health", healthHandler)
    http.HandleFunc("/orders/create", createOrderHandler)
    
    // NEW: Auth routes (added by Phase 1)
    http.HandleFunc("/auth/register", registerHandler)
    http.HandleFunc("/auth/login", loginHandler)
    http.HandleFunc("/auth/refresh", refreshHandler)
    
    // Existing routes that need auth protection
    http.HandleFunc("/orders/list", authMiddleware(listOrdersHandler))
    
    fmt.Println("Server starting on :8080")
    if err := http.ListenAndServe(":8080", nil); err != nil {
        log.Fatal(err)
    }
}

// NEW: Auth middleware (created by Phase 1)
func authMiddleware(next http.HandlerFunc) http.HandlerFunc {
    return func(w http.ResponseWriter, r *http.Request) {
        token := r.Header.Get("Authorization")
        if token == "" {
            http.Error(w, "Missing token", http.StatusUnauthorized)
            return
        }
        // Validate JWT...
        next(w, r)
    }
}
```

#### DI for Go
If project uses Google Wire:

Phase 1 generates wire.go:
```go
//go:build wireinject
// +build wireinject

package main

import "github.com/google/wire"

func InitializeApp() *App {
    wire.Build(
        NewUserRepository,
        NewAuthService,
        NewAuthHandler,
    )
    return &App{}
}
```

---

## Key Phase 1 Modules

| Module | Purpose | Handles |
|--------|---------|---------|
| format_multifile_output.py | Dependency-ordered output | File ordering, safe merging |
| autowire_into_project.py | Modify existing files | main.py, settings.py, urls.py, go.mod |
| generate_migrations.py | Database migrations | Django, Alembic, Flyway, golang-migrate |
| config_generator.py | .env.example creation | Extract new config vars from code |
| di_aware_generator.py | DI injection per framework | Spring @Autowired, FastAPI Depends(), Go wire |
| multi_handler_orchestrator.py | Coordinate multiple services | REST + WebSocket, REST + gRPC |
| slash_command_scaffolder.py | CLI platform wrappers | Discord, Slack, Telegram, CLI |
| openapi_generator.py | Swagger/OpenAPI docs | Auto-document endpoints, models |

---

## Test This Yourself

### 1. Analysis Only
```bash
python skills/one-shot-generator/scripts/analyze_codebase.py "add auth" @examples/fastapi-async-api
# Output: FastAPI framework, SQLAlchemy ORM, pytest
```

### 2. Full Generation with Auto-Wiring
```bash
/one-shot-prompting:one-shot-generator "add JWT auth" @examples/fastapi-async-api
# Output: models.py, routes.py, tests/, migrations/
# Also: main.py modified (router registered)
# Also: .env.example with JWT_SECRET_KEY
```

### 3. Check Integration
```bash
cd examples/fastapi-async-api
pip install -r requirements.txt
alembic upgrade head  # Run migration
pytest tests/test_auth.py  # Verify tests pass
python -m uvicorn main:app --reload  # Start server
curl http://localhost:8000/docs  # Check Swagger UI
```

---

## Next: Phase 2

Phase 1 generates single features in integration. Phase 2 handles **specialized domains**:
- Full REST API CRUD with validation, auth, pagination
- Webhook handlers with retries
- Database relationship generation
- Comprehensive test suite (50+ tests per API)
- Framework-specific best practices per domain

See [phase2-crud.md](phase2-crud.md)

---

**The Magic:** Phase 1 makes integration effortless. No manual wiring, no missing migrations, no forgotten config. Just code that works in your project immediately.
