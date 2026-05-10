# Phase 1: Critical Integration Gaps — Implementation Spec

**Status**: 🟡 In Progress | **Modules**: 7 | **Est. LOC**: 1,400 | **Deadline**: May 20, 2026 (v0.7.0)

---

## Overview

Phase 1 closes critical gaps between code generation (Phase 0-3) and production deployment. These 7 modules enable multi-file output, automatic project integration, database migrations, and local dev environment setup.

**Blocking Issue**: Without Phase 1, generated code is fragmented across multiple files with unclear dependencies. Phase 1 unifies output into deployment-ready packages.

---

## Module Breakdown

### Gap 1: Multi-File Output Formatting (2 modules)

#### 1.1: `format_multifile_output.py` (90 LOC)
**Purpose**: Organize generated code files with dependency ordering and clear structure.

**Input**:
- Dict of file paths → code snippets (e.g., `{"models.py": "class User...", "views.py": "def get_user()..."}`)
- Framework context (Django, FastAPI, NestJS, Express, Spring)
- Project root path

**Output**:
- Ordered list of (path, code) tuples respecting dependencies
- Dependency graph visualization (optional)

**Algorithm**:
1. Parse file imports/requires to build dependency graph
2. Topological sort (models before views before tests)
3. Organize by layer (models, handlers, middleware, tests)
4. Return sorted list with insertion order

**Example**:
```python
input = {
    "tests/test_users.py": "import views; ...",
    "models.py": "class User: ...",
    "views.py": "from models import User; ...",
}
output = [
    ("models.py", "class User: ..."),
    ("views.py", "from models import User; ..."),
    ("tests/test_users.py", "import views; ..."),
]
```

**Test cases**:
- [ ] Circular dependency detection → error with advice
- [ ] Models before handlers (layer ordering)
- [ ] Tests always last
- [ ] Multi-framework (Django, FastAPI, NestJS, Express)

---

#### 1.2: `autowire_into_project.py` (250 LOC)
**Purpose**: Auto-inject generated code into existing projects at correct locations.

**Input**:
- Generated files (from 1.1)
- Project root path
- Framework detection (auto or explicit)

**Output**:
- Updated project with generated code integrated
- Backup of original files (`.backup/`)
- Merge conflicts (if any) flagged

**Algorithm**:
1. Detect framework (look for `manage.py`, `main.py`, `package.json`, `pom.xml`)
2. Find correct insertion points:
   - Django: `myapp/models.py`, `myapp/views.py`, `myapp/migrations/`
   - FastAPI: `app/models.py`, `app/routes/`, `app/tests/`
   - NestJS: `src/`, `src/controllers/`, `src/modules/`
   - Express: `src/routes/`, `src/models/`, `src/middleware/`
3. Merge with existing files (append functions, merge imports)
4. Create `.backup/` directory with pre-merge versions
5. Return merge report

**Edge cases**:
- [ ] File already exists → ask merge strategy (overwrite/append/skip)
- [ ] Import conflicts → rename imports
- [ ] Missing directories → create them
- [ ] Permission denied → skip with warning

**Test cases**:
- [ ] Django project with existing models
- [ ] FastAPI with existing routes
- [ ] NestJS with existing modules
- [ ] Express with existing middleware

---

### Gap 2: Database Migration Generation (1 module)

#### 2.1: `generate_migrations.py` (300 LOC)
**Purpose**: Auto-generate database migrations for newly created models.

**Input**:
- Model definitions (from Phase 2 REST API generation)
- Database type (PostgreSQL, MySQL, SQLite, etc.)
- Framework (Django, FastAPI, Spring, Go)
- Project root

**Output**:
- Migration file(s) ready to apply
- SQL preview (for review)
- Rollback script

**Algorithm**:
1. **Django**: Use `makemigrations` + `sqlmigrate` to inspect changes
   - Parse models from generated code
   - Create migration files in `migrations/`
   - Return SQL for user approval
   
2. **FastAPI**: Generate Alembic migrations
   - Parse SQLAlchemy models
   - Create `alembic/versions/*.py`
   - Return SQL for user approval
   
3. **Spring**: Generate Flyway migrations
   - Parse JPA entities
   - Create `resources/db/migration/V*.sql`
   
4. **Go**: Generate sql-migrate migrations
   - Parse models
   - Create migrations in `migrations/` with timestamp

**Edge cases**:
- [ ] Column name collisions → rename with suffix
- [ ] Missing primary keys → add auto-increment ID
- [ ] Foreign key constraints → create in correct order
- [ ] Existing schema → detect and update

**Test cases**:
- [ ] Simple model (User with email, password)
- [ ] Relationships (Order → User, Product)
- [ ] Indexes and constraints
- [ ] Enum fields
- [ ] JSON/JSONB fields

---

### Gap 3: Framework Configuration Generation (4 modules)

#### 3.1: `framework_config_generator.py` (200 LOC)
**Purpose**: Generate framework-specific configuration files based on generated features.

**Input**:
- Generated features (auth, webhooks, batch jobs, etc.)
- Framework & version
- Project root

**Output**:
- Framework config files (updated or created)

**Configs by framework**:

**Django**:
- `settings.py` — Add apps, middleware, installed packages
- `urls.py` — Add routes for generated endpoints
- `wsgi.py` — (rarely modified)

**FastAPI**:
- `main.py` — Add routers, middleware, dependencies
- `settings.py` — Environment config
- `.env` — Example environment variables

**NestJS**:
- `app.module.ts` — Add modules, controllers
- `.env` — Example environment

**Express**:
- `app.js` or `index.js` — Add routes, middleware
- `.env` — Environment config

**Spring**:
- `application.properties` or `.yml` — Add database, security config
- `pom.xml` — Add dependencies

**Algorithm**:
1. Detect existing config files
2. Parse framework-specific syntax
3. Merge new configs without breaking existing ones
4. Preserve formatting & comments
5. Return updated config + diff

**Test cases**:
- [ ] Adding auth to Django project
- [ ] Adding middleware to FastAPI
- [ ] Adding modules to NestJS

---

#### 3.2: `dependency_injector.py` (250 LOC)
**Purpose**: Generate DI container setup for generated components.

**Input**:
- Generated classes/services
- Framework (Django, FastAPI, NestJS, Express, Spring)
- Existing DI container (if any)

**Output**:
- DI container code
- Service registration
- Dependency graph visualization

**DI patterns by framework**:

**Django**: 
- Use Django's built-in dependency injection (model/view/middleware)
- Generate service classes in `services/` with `@dataclass` or `@inject`

**FastAPI**:
- Use `Depends()` for dependency injection
- Generate factory functions for services

**NestJS**:
- Use `@Injectable()` decorators
- Generate provider registration in modules

**Express**:
- Manual DI via closure/middleware
- Generate factory functions

**Spring**:
- Use `@Component`, `@Service`, `@Autowired`
- Generate XML or annotation-based config

**Test cases**:
- [ ] Simple service with 1 dependency
- [ ] Complex graph (A → B → C → D)
- [ ] Circular dependency detection + error

---

#### 3.3: `environment_variables_generator.py` (100 LOC)
**Purpose**: Generate `.env.example` template with all required variables.

**Input**:
- Generated code (extract from env references)
- Framework config
- Project root

**Output**:
- `.env.example` file with all variables
- `.env` file (if doesn't exist)
- Validation schema

**Variables extracted from**:
- Database config (DB_URL, DB_USER, DB_PASS, etc.)
- API keys (STRIPE_KEY, OPENAI_KEY, etc.)
- Queue config (CELERY_BROKER_URL, etc.)
- Logging config (LOG_LEVEL, etc.)
- Feature flags (ENABLE_WEBHOOKS, etc.)

**Format**:
```env
# Database
DATABASE_URL=postgresql://user:pass@localhost/dbname
DATABASE_ECHO=false

# Authentication
JWT_SECRET=your_secret_here
JWT_ALGORITHM=HS256
JWT_EXPIRY_HOURS=24

# External APIs
STRIPE_API_KEY=sk_test_...
```

**Test cases**:
- [ ] Generate for Django project (DATABASE_URL, SECRET_KEY, etc.)
- [ ] Generate for FastAPI project
- [ ] Preserve existing .env

---

#### 3.4: `docker_compose_generator.py` (150 LOC)
**Purpose**: Generate `docker-compose.yml` for local development environment.

**Input**:
- Framework & version
- Database type (PostgreSQL, MySQL, SQLite, Redis, MongoDB)
- Queue system (Celery, Bull, RQ)
- External services (Stripe, AWS, etc.)
- Project root

**Output**:
- `docker-compose.yml` (development)
- `.dockerignore`
- Dockerfile (if doesn't exist)

**Services**:
- App service (Django, FastAPI, NestJS, Express, Spring)
- Database (PostgreSQL 14+, MySQL 8+, MongoDB 5+)
- Cache (Redis 7+)
- Queue broker (RabbitMQ, Redis)
- Optional: Adminer, pgAdmin, MongoDB Compass

**Example**:
```yaml
version: '3.8'
services:
  app:
    build: .
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/myapp
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:14
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=myapp
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7
```

**Test cases**:
- [ ] Django + PostgreSQL + Redis
- [ ] FastAPI + MySQL
- [ ] NestJS + MongoDB + RabbitMQ

---

## Implementation Timeline

| Week | Gap | Modules | LOC | Tasks |
|------|-----|---------|-----|-------|
| 1 (May 13-17) | 1 | 1.1, 1.2 | 340 | Implement, test on 3 frameworks |
| 2 (May 18-20) | 2-3 | 2.1, 3.1-3.4 | 1,060 | Implement, integration test, bug fix |
| **May 20** | **All** | **All 7** | **1,400** | **v0.7.0 Release** |

---

## Testing Strategy

### Unit Tests (per module)
- Mock file systems, framework detection, config parsing
- Test each module in isolation

### Integration Tests
- Real Django, FastAPI, NestJS, Express projects
- Generate → Autowire → Migrate → Run → Verify it works

### Edge Case Tests
- Empty projects
- Large projects (1000+ files)
- Projects with existing generated code

---

## Success Criteria (v0.7.0)

- ✅ All 7 modules implemented & tested
- ✅ Works on 4+ frameworks (Django, FastAPI, NestJS, Express)
- ✅ Handles circular dependencies & conflicts gracefully
- ✅ Integration tests pass (real project scenarios)
- ✅ Backup/rollback mechanisms work
- ✅ Edge cases documented & handled

---

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|------|------------|-----------|
| Import merging breaks code | High | Careful AST parsing + test imports |
| Migration conflicts | Medium | Preview migrations before apply |
| Framework detection fails | Low | Fallback to user input, add hints |
| File permissions issues | Low | Graceful fallback + warnings |

---

**Created**: 2026-05-09  
**Deadline**: 2026-05-20  
**Contact**: musman.mughal@taleemabad.com
