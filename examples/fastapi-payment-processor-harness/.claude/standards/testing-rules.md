---
type: standards
last_verified: 2026-05-19
owner: claude
---

# FastAPI Testing Rules

## Minimum coverage: 80%

Run: `pytest --cov=app --cov-report=term-missing`

## Every endpoint gets a test
- Happy path
- Validation failure (422)
- Not found (404)
- Auth failure (401) where applicable

## Use httpx AsyncClient, not requests

```python
@pytest.mark.asyncio
async def test_create_payment(client: AsyncClient):
    resp = await client.post("/payments/", json={"amount": 100, "currency": "USD"})
    assert resp.status_code == 201
    assert resp.json()["status"] == "pending"
```

## Never mock the database in integration tests
Use a real test DB (SQLite async is fine for tests).
