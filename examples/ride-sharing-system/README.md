---
type: example
title: Ride-Sharing System
framework: FastAPI
complexity: Advanced
last_verified: 2026-05-25
---

# Ride-Sharing System — Example FastAPI Application

A runnable FastAPI app that demonstrates the patterns the
one-shot-prompting plugin is designed to generate for an Uber-like
domain. Use it as a reference implementation or as a target for
`/one-shot` to extend.

This README is the **honest accounting** of what's actually in this
directory. A prior version overstated the contents; that copy is what
the original audit flagged and is the reason for this rewrite.

## What's actually here

```
examples/ride-sharing-system/
├── README.md            (this file)
├── requirements.txt     (FastAPI, SQLAlchemy 2 async, Pydantic v2, PyJWT, pytest)
├── app/
│   ├── main.py          (FastAPI factory, router wiring, /health)
│   ├── db.py            (async engine, get_db dependency)
│   ├── deps.py          (get_current_user, require_role gate)
│   ├── security.py      (PBKDF2 password hash + JWT helpers)
│   ├── schemas.py       (Pydantic request/response models)
│   ├── models/          (11 SQLAlchemy ORM models)
│   ├── services/
│   │   ├── pricing.py   (deterministic fare calculator + haversine)
│   │   └── matching.py  (nearest-driver search over GPS pings)
│   └── routers/
│       ├── auth.py      (register, login, refresh)
│       ├── users.py     (me, update, get)
│       ├── drivers.py   (profile, status, location, vehicle)
│       ├── rides.py     (request, list, get, status transitions)
│       ├── payments.py  (history, get, add-tip)
│       ├── ratings.py   (create, list-for-user)
│       ├── support.py   (tickets create/get/update-status)
│       └── admin.py     (promo codes, suspend/ban, dashboard counters)
└── tests/
    ├── conftest.py      (in-memory SQLite + ASGI test client)
    ├── test_auth.py     (5 tests)
    ├── test_pricing.py  (8 tests — pure functions, no DB)
    ├── test_rides.py    (6 tests — full e2e flows)
    └── test_misc.py     (5 tests — ratings, support, admin, health)
```

## Honest coverage matrix

| Item | Spec target | Implemented here |
|---|---|---|
| Database tables | 11 | **11** (users, drivers, passengers, vehicles, rides, ride_requests, driver_locations, ratings, payments, support_tickets, promo_codes) |
| HTTP endpoints | 87 listed in spec | **29 implemented** (around one-third — the core happy-path of every domain). The remaining endpoints follow the same patterns and are left as `/one-shot` extension targets. |
| Authentication | OAuth + phone OTP + JWT | **JWT only** (register/login/refresh). OAuth and OTP are wiring points the spec describes; they are not implemented here. |
| Real-time | WebSockets for ride updates + chat | **Not implemented.** Driver locations are stored as REST `PUT` pings instead of a WebSocket stream. |
| External integrations | Stripe, Google Maps, Twilio, SendGrid | **Not wired.** Pricing uses a deterministic local formula; matching uses an in-memory linear scan; no SMS, no card processing, no map calls. |
| Background jobs | Celery for matching, payouts, notifications | **Not implemented.** Matching runs synchronously on ride request. |
| Tests | implied | **24 tests, all passing** (`pytest tests/ -v`) — auth flow, pricing pure functions, full ride flow (request → match → cancel), promo codes, support tickets, admin gates. |

## What this *is* and *isn't*

This is an **example**, not a production ride-sharing platform. It
shows:

- How to lay out a multi-domain FastAPI app the way `/one-shot`
  generates code (`models/` + `schemas.py` + `services/` + `routers/`).
- How to enforce role gates (`require_role(UserRole.driver)`) the way
  the plugin's `architect` agent specifies them.
- How to wire deterministic business logic (pricing, matching) into
  HTTP handlers so it is testable without spinning up infrastructure.
- How to test the whole thing with an in-memory SQLite database and the
  FastAPI ASGI test client.

It is **not**:

- A production system. There is no Stripe integration, no real
  geospatial index, no WebSocket layer, no Celery worker, no rate
  limiter, no observability wiring beyond what the plugin's own OTel
  layer would add.
- A complete realisation of the spec. The spec lists 87 endpoints
  across passenger / driver / admin / payments / support / real-time /
  analytics; this implementation covers 29 of them. The omitted
  endpoints are clearly bounded — they follow the same patterns as the
  ones that exist.

## Run it

```bash
cd examples/ride-sharing-system
pip install -r requirements.txt
pytest tests/ -v          # all 24 should pass
uvicorn app.main:app --reload
```

OpenAPI docs at `http://localhost:8000/docs`.

## Where to take it next with `/one-shot`

Each of these is a one-shot prompt that would extend the example along
the patterns above:

```bash
/one-shot "Add a /api/v1/rides/{ride_id}/messages endpoint for in-ride passenger-driver chat persistence" @examples/ride-sharing-system
/one-shot "Add Stripe payment intent creation when a ride is requested and confirmation on completion" @examples/ride-sharing-system
/one-shot "Add WebSocket /ws/ride/{ride_id}/updates broadcasting driver location changes" @examples/ride-sharing-system
/one-shot "Add admin /api/v1/admin/analytics/revenue with day/week/month breakdown" @examples/ride-sharing-system
```

Pick one and run it; the resulting code should slot into this example
without disturbing the existing 29 endpoints or 24 tests. This is the
plugin's actual job — extending a real codebase, not generating
greenfield architecture diagrams.

## What changed from the prior README

Previous version of this file claimed "PRODUCTION READY", "99.79% Test
Pass Rate", "8.3/10 Audit Score" and described 87 endpoints as
implemented. Those numbers belonged to the plugin's *own* test suite
and were copy-pasted into this example. **There was no code in this
directory** — only the marketing README.

This rewrite ships actual code (app/, tests/, requirements.txt) with
honest coverage stats. The numbers in this file refer to *this
example*, not to the plugin overall.
