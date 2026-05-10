# Example Projects

Five hand-curated projects that demonstrate one-shot-prompting end-to-end.
Each example shows the *generation journey* (the exact prompt that produced
the code, the assumptions block, what was changed afterwards) — not just
the final output.

| Example | Stack | What it shows |
|---------|-------|---------------|
| `django-order-service/` | Django 4.2 + Celery + Postgres | Order lifecycle, Celery tasks, structlog, GitHub Actions, k8s. |
| `fastapi-rate-limiter/` | FastAPI + Redis + Kafka | Sliding-window rate limiter, async handlers, OTel + Prometheus. |
| `spring-payment-service/` | Spring Boot 3 + Kafka + Postgres | Saga pattern, JPA, Flyway, Bean Validation. |
| `go-trading-bot/` | Go 1.20 + NATS | Low-latency trade executor, channels, structured logging. |
| `nestjs-realtime-api/` | NestJS 10 + WebSocket + Redis | GraphQL subscriptions, RxJS, Jest, dependency injection. |

Each example has its own `README.md` with:
- Original prompt
- Generated assumptions block
- File list and approximate LOC
- Diff vs. the generated output (typically <5%)
- How to run locally
