---
type: reference
last_verified: 2026-05-21
owner: usman
---

# Generated Code Standards

Rules for code produced by the one-shot pipeline.

## GEN-001: All Generated Code Must Include Tests

**Rule:** Every generated file with business logic must have a corresponding test file.

**Scope:**
- Models, services, API endpoints, background jobs: REQUIRED
- Config files, migrations, type stubs: EXEMPT
- Mark files with `@skip-test` comment to exempt

**Enforcement:** Hook: PostToolUse scans for test files
```python
# Example: if generated file is services/cart.py, must have tests/test_cart.py
```

**Exemption Pattern:**
```python
# @skip-test
# config: migrations config, no logic to test
class MigrationConfig:
    pass
```

**How to Test:** After generation, `pytest tests/ -v` must pass all tests.

---

## GEN-002: Foreign Key Relationships Auto-Validated

**Rule:** All foreign key declarations must be syntactically valid and point to existing models.

**Scope:**
- All ORM models (SQLAlchemy, Django ORM, etc.)
- Relationships defined via ForeignKey or relationship()
- Must match schema in spec.json

**Enforcement:** Hook: PostToolUse runs validation script
```python
# Validates:
# - FK column type matches referenced PK type
# - Referenced model exists
# - No circular references without explicit backref
```

**Valid Example (SQLAlchemy):**
```python
class Cart(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    user: Mapped["User"] = relationship("User", back_populates="carts")
```

**Invalid Example (caught by GEN-002):**
```python
class Cart(Base):
    user_id: Mapped[int] = mapped_column(ForeignKey("NonExistentModel.id"))
    # ❌ NonExistentModel doesn't exist
```

---

## GEN-005: All Models Include Type Hints

**Rule:** All model definitions must use type hints for all attributes.

**Scope:**
- Pydantic models (FastAPI)
- SQLAlchemy mapped classes
- TypedDict definitions
- Django models

**Enforcement:** Hook: PostToolUse scans for untyped attributes

**Valid Example (Pydantic):**
```python
class CartItem(BaseModel):
    id: int
    quantity: int
    price: Decimal
    cart_id: int
```

**Invalid Example (caught by GEN-005):**
```python
class CartItem(BaseModel):
    id = 1  # ❌ Missing type hint
    quantity: int
```

**Exemption:** Mark with `@untyped` if absolutely necessary (rare).
```python
class LegacyModel:  # @untyped — maintains compatibility with old code
    data = None
```
