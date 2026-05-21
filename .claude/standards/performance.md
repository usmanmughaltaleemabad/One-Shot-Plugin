---
type: reference
last_verified: 2026-05-21
owner: usman
---

# Performance Standards

## GEN-008: N+1 Query Detection

**Rule:** Generated ORM code must not have N+1 query patterns.

**Pattern to Avoid:**
```python
# ❌ N+1: Loop queries the database repeatedly
carts = db.query(Cart).all()
for cart in carts:
    items = cart.items  # Queries 1x per cart (N queries)
    print(items)
```

**Correct Pattern:**
```python
# ✅ Single query with eager loading
carts = db.query(Cart).options(joinedload(Cart.items)).all()
for cart in carts:
    items = cart.items  # Already loaded (1 query total)
    print(items)
```

**Enforcement:** Performance auditor scans generated code for missing joinedload/prefetch_related.

**Exemption:** Mark with `@slow-ok` if intentional (rare)
```python
def get_cart_with_details(cart_id):  # @slow-ok — intentional for batch processing
    # ...
```
