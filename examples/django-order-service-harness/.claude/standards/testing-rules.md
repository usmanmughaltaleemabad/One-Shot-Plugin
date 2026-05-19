---
type: standards
last_verified: 2026-05-19
owner: claude
---

# Django Testing Rules

## Use APITestCase or pytest-django

```python
from rest_framework.test import APITestCase

class OrderAPITests(APITestCase):
    def test_create_order(self):
        resp = self.client.post("/api/orders/", {"customer_id": 1, "items": []}, format="json")
        self.assertEqual(resp.status_code, 201)
```

## Coverage minimum: 80%

```bash
pytest --cov=orders --cov-report=term-missing
```

## Factory pattern for fixtures

Use `factory_boy` or plain `Model.objects.create()` — never rely on fixture JSON files.
