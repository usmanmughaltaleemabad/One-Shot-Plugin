---
type: reference
last_verified: 2026-05-21
owner: usman
---

# Testing Standards

Rules for test coverage and quality in generated code.

## Test Coverage Requirement

**Rule:** Generated code must have ≥80% test coverage.

**How Measured:**
```bash
pytest --cov=src tests/ --cov-report=term-missing
```

**Coverage by Module Type:**
- Models/schemas: ≥90% (simple logic, easy to test)
- Service/business logic: ≥85% (core logic, all paths covered)
- API endpoints: ≥80% (happy path + error cases)
- Utilities: ≥75% (optional, dependencies can vary)

**Enforcement:** Critic agent measures coverage post-generation. Fails if <80%.

## Test Isolation

**Rule:** Tests must not depend on each other or external services.

**Requirements:**
- Each test is independent (no shared state)
- Use fixtures for setup/teardown
- Mock external APIs (don't call real APIs)
- Use in-memory database for unit tests

**Valid Example:**
```python
@pytest.fixture
def cart():
    return Cart(id=1, user_id=1)

def test_add_item_to_cart(cart):
    cart.add_item(item_id=1, quantity=1)
    assert len(cart.items) == 1
```

**Invalid Example:**
```python
# ❌ Depends on external API
def test_process_payment():
    response = stripe.charge(amount=100)
    assert response.status == "success"
```

## Test Naming

**Rule:** Test names must clearly describe what's being tested.

**Pattern:** `test_<function>_<scenario>_<expected_result>`

**Valid Examples:**
- `test_calculate_discount_with_bulk_order_returns_lower_price()`
- `test_add_item_to_empty_cart_increments_count()`
- `test_invalid_email_raises_validation_error()`

**Invalid Examples:**
- `test_it_works()` — unclear
- `test_1()` — no meaning
