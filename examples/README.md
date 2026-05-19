---
type: reference
last_verified: 2026-05-16
owner: claude
---

# Examples for one-shot-prompting Plugin

This directory mixes two kinds of examples:

1. **Runnable starter projects** — directories with actual source files
   (`django-rest-api/`, `fastapi-async-api/`, `go-trading-bot/`, plus the
   `*-harness/` directories that include `app/`, `models/`, `src/`).
   Useful as targets to run `/one-shot` against.
2. **Prompt examples (README-only)** — directories that contain ONLY a
   README describing a prompt and the files it would generate. These are
   NOT runnable as-is. They include: `django-order-service/`,
   `django-order-service-harness/`, `fastapi-rate-limiter/`,
   `nestjs-realtime-api/`, `spring-payment-service/`. Each README is
   marked with a note at the top.

---

## Django REST API (`django-rest-api/`)

**Framework:** Django 4.2 + Django REST Framework  
**Database:** SQLite  
**Models:** Post, Comment

### Setup
```bash
cd examples/django-rest-api
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Test Generation
```bash
/one-shot-prompting:one-shot-generator "add JWT authentication endpoints" @examples/django-rest-api
```

### Tests
- ✅ CRUD API generation
- ✅ Authentication integration
- ✅ Serializer detection
- ✅ Pagination + filtering
- ✅ Endpoint routing

---

## FastAPI Async API (`fastapi-async-api/`)

**Framework:** FastAPI 0.104 + SQLAlchemy  
**Database:** SQLite  
**Models:** Post (async endpoints)

### Setup
```bash
cd examples/fastapi-async-api
pip install -r requirements.txt
python main.py
# API at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### Test Generation
```bash
/one-shot-prompting:one-shot-generator "add user profiles with relationships" @examples/fastapi-async-api
```

### Tests
- ✅ Async/await detection
- ✅ Pydantic model generation
- ✅ SQLAlchemy async support
- ✅ OpenAPI docs generation
- ✅ Dependency injection

---

## Go Trading Bot (`go-trading-bot/`)

**Language:** Go 1.21  
**Framework:** stdlib (http)  
**Storage:** In-memory (sync.RWMutex)

### Setup
```bash
cd examples/go-trading-bot
go run main.go
# API at http://localhost:8080
```

### Test Generation
```bash
/one-shot-prompting:one-shot-generator "add database persistence with PostgreSQL" @examples/go-trading-bot
```

### Tests
- ✅ Go concurrency patterns
- ✅ HTTP handler detection
- ✅ Struct generation
- ✅ JSON marshaling
- ✅ Error handling

---

## How to Use

### Test Code Generation
```bash
# Each example can be used as a test context
/one-shot-prompting:one-shot-generator "[feature description]" @examples/django-rest-api
```

### Test Framework Detection
```bash
python skills/one-shot-generator/scripts/analyze_codebase.py "test" @examples/django-rest-api
```

---

**Last Updated:** 2026-05-16
