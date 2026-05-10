# Example: django-order-service

Django microservice that processes orders end-to-end: HTTP intake → Celery
task → email notification → Kafka audit log. Generated in one shot.

## Original prompt

```
/one-shot-prompting:one-shot-generator
Add an order intake endpoint to my Django app: POST /orders accepts an order,
validates payload, queues a Celery task that charges the customer and sends
an email, then audits the result on Kafka. Include tests and Docker.
@./
```

## Generated assumptions block (excerpt)

```
- Framework: Django 4.2 (detected manage.py + DRF in requirements)
- Database: Postgres (detected DATABASES + psycopg2)
- Task queue: Celery + Redis broker (detected celery in requirements)
- Tests: pytest-django + factory_boy (detected conftest.py)
- Logging: structlog (detected)
- Bus: Kafka (detected kafka-python in requirements)
- Convention: snake_case + Google-style docstrings + 100% type hints
```

## Files generated (8)

| File | Purpose | LOC |
|------|---------|-----|
| `orders/models.py` | Order, OrderItem | 60 |
| `orders/views.py` | POST /orders DRF view | 45 |
| `orders/serializers.py` | OrderSerializer (writable nested) | 40 |
| `orders/tasks.py` | charge_and_notify Celery task | 70 |
| `orders/audit.py` | Kafka emitter | 30 |
| `orders/tests/test_views.py` | endpoint tests | 80 |
| `orders/tests/test_tasks.py` | task tests w/ Celery eager | 50 |
| `Dockerfile` | multi-stage Python 3.11 image | 25 |

## Diff vs. generated

After generation, only 7 lines were edited (renamed env var, plugged
in real Stripe key). 0% structural changes.

## Run locally

```bash
docker compose up -d
python manage.py migrate
python manage.py runserver &
celery -A orders worker -l info &
curl -X POST http://localhost:8000/orders -H 'Content-Type: application/json' \
     -d '{"customer_id": "c1", "items": [{"sku": "ABC", "qty": 1}]}'
```
