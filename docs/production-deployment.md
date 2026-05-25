---
type: runbook
last_verified: 2026-05-25
owner: claude
version: v1.2.0
---

# Production Deployment Guide

Taking generated code from `/one-shot --apply` to running production
in 5 stages. Each stage closes a specific risk category.

---

## Stage 1 — Pre-flight checks (local, free)

Before deploying anywhere, run these locally:

```bash
# Lint + syntax
python -m py_compile $(find . -name "*.py" -not -path "*/.osp.bak*")

# Security scan
python skills/one-shot-generator/scripts/sast_runner.py \
    --dir . --strict

# Type check (optional but recommended)
pip install mypy
mypy --strict $(git ls-files "*.py")

# Run all generated tests
pytest tests/ -v

# Check no .osp.bak files were committed
test -z "$(find . -name "*.osp.bak")" || \
    { echo "ERROR: .osp.bak files in tree"; exit 1; }
```

If any of these fail, fix or rollback (`/rollback`) before proceeding.

---

## Stage 2 — Migration check (database)

Generated features include an Alembic revision under
`alembic/versions/`. Before applying to production:

```bash
# 1. Inspect the revision
cat alembic/versions/<latest>.py

# 2. Run against a STAGING database first
DATABASE_URL=$STAGING_DB alembic upgrade head

# 3. Verify schema in staging
psql $STAGING_DB -c "\dt"   # or for sqlite: sqlite3 -cmd ".tables"

# 4. Test the smoke endpoints in staging
curl https://staging.example.com/api/v1/<entity>/

# 5. THEN apply to production with downtime budget known
DATABASE_URL=$PROD_DB alembic upgrade head
```

If the migration touches existing tables (column addition, type
change), use a **zero-downtime** pattern: deploy code that works on
both old AND new schema, run migration, then deploy code that uses
the new schema only.

---

## Stage 3 — Secrets + config

Generated code never contains secrets — but `--apply` may have
referenced them via env vars. Before deploying:

```bash
# Check what's expected
grep -rE "os\.environ\.(get|\[)" --include="*.py" .

# Required env vars to set in your deployment:
# - DATABASE_URL          (alembic + SQLAlchemy)
# - JWT_SECRET            (auth_endpoints hint emits this)
# - REDIS_URL             (if cache_layer or rate_limiter is in use)
# - SMTP_*                (if background_task emits emails)
# - OTEL_EXPORTER_OTLP_ENDPOINT  (if OTel enabled)
# - OSP_OTEL_ENABLED=1    (to actually emit spans)
```

Use your platform's secret manager (AWS Secrets Manager, GCP Secret
Manager, Vault, Doppler) — never commit secrets to git.

---

## Stage 4 — Observability + alerts

Generated services emit:

1. **Domain events** via `common/events.emit(name, **payload)`.
   In production, swap the stderr stub for Kafka / SNS / Redis Streams.

2. **OpenTelemetry spans** when `OSP_OTEL_ENABLED=1`. Point
   `OTEL_EXPORTER_OTLP_ENDPOINT` at your collector (Honeycomb, Tempo,
   Datadog, Jaeger).

3. **Structured logs** via `common/logging_setup.configure_logging()`
   if the implementer pulled in the logging_setup hint. JSON to stdout,
   then aggregator's choice.

Alert configuration:

| Signal | Threshold | Action |
|---|---|---|
| Critic verdict ≠ SHIPPED | any | page on-call before deploy |
| 5xx rate > 1% over 5min | sustained | rollback via `/rollback` |
| p95 latency > 500ms on `/api/v1/<entity>` | sustained | inspect via OTel trace |
| Migration runtime > 30s | any | investigate locks |

---

## Stage 5 — Rollback plan (always)

Before pushing to production, know the rollback path:

```bash
# Code rollback
git revert HEAD                # or git reset --hard <last-good-sha>
./deploy.sh                    # your CI redeploys

# Plugin-aware rollback (if --apply mutated files locally first)
/one-shot-prompting:rollback --keep-stash

# Database rollback
DATABASE_URL=$PROD_DB alembic downgrade -1
```

Test the rollback path in staging BEFORE you need it in prod.

---

## Pre-deployment checklist

Copy this checklist into your team's PR template:

- [ ] `pytest tests/` green
- [ ] `sast_runner.py --strict` clean
- [ ] Alembic revision applied + tested in staging
- [ ] Env vars set in production secrets manager
- [ ] Domain events stub swapped for real broker (or kept as logging if
      the feature doesn't need cross-service comms)
- [ ] OTel endpoint configured (or explicitly disabled)
- [ ] Rate-limiter / cache-layer backed by Redis if multi-worker
- [ ] On-call paged for any 5xx spike post-deploy
- [ ] Rollback path documented in the PR description

---

## Common gotchas

**1. `--apply` mutated `main.py` but the imports break.**
The wirer adds `from <entity>.router import router as <entity>_router`.
If your `main.py` has unusual structure (factory function, conditional
imports), inspect the diff before pushing.

**2. Generated tests assume the project's pytest config.**
If the project uses pytest-asyncio strict mode but the test contract
didn't account for it, tests fail. Check `pyproject.toml` /
`pytest.ini` matches what the test-author generated.

**3. Generated service-layer events are stubs.**
`common/events.py` logs to stderr by default. In production, wire it
to your message broker — but check the events the service emits are
the ones consumers expect.

**4. JWT secret rotation.**
Generated auth uses `JWT_SECRET` env var. If you rotate the secret,
all existing tokens invalidate. Plan a rotation window.

**5. Bcrypt cost factor.**
The auth_endpoints hint specifies `cost_factor >= 12`. On t3.micro
instances, that's ~200ms per hash. Profile your login endpoint
under load.
