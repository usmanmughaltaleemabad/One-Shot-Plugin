---
type: runbook
last_verified: 2026-05-18
owner: claude
---

# Cookbook — Three Worked `/one-shot` Examples

Three realistic feature requests, walked through end-to-end with the
agentic pipeline. Each example shows what you type, what the plugin
does at each stage, and what files land where.

---

## Example 1 — Shopping cart with line items and discounts

The canonical multi-entity demo.

### What you type

```bash
/one-shot "Build a shopping cart with line items and discounts" @./my-fastapi-shop
```

### Pipeline trace

**Stage 0 — Curriculum (~50ms)**
```
CURRICULUM (47 past failures on file)
  • [0.42] bd-fail-20260518-001
      verification_warning: test asserts HTTP 401 but matching router has no auth
      advice: test/router contract drift — set test_contract.auth='none'
```

**Stage 1 — Scan + extract (~80ms)**
```
DOMAIN MODEL
  Intent: feature   (confidence 0.80)
  Primary: shopping_cart
  Entities (3):
    • ShoppingCart   • LineItem   • Discount
  Relationships:
    • shopping_cart ── has_many ──▶ line_item
    • shopping_cart ── has_many ──▶ discount

CODEBASE GRAPH (./my-fastapi-shop)
  python/fastapi   2 existing entities (HealthResponse, Product)
  IMPORTS: model_base → Base from models
```

**Stage 0.5 — External discovery (~30ms)**
```
DISCOVERY — no strong external match; proceeding with local pipeline
```

**Stage 2 — Architect agent (~$0.11, 55s)**

Spawned via Task. Produces `spec.json`:
```json
{
  "feature": "shopping cart with line items and discounts",
  "entities": [
    {"name": "ShoppingCart", "action": "create",
     "fk_columns": [], "attributes": ["status", "total", "user_id"]},
    {"name": "LineItem", "action": "create",
     "fk_columns": ["shopping_cart_id"],
     "attributes": ["product_id", "quantity", "unit_price"]},
    {"name": "Discount", "action": "create",
     "fk_columns": ["shopping_cart_id"],
     "attributes": ["code", "percent_off", "valid_until"]}
  ],
  "test_contract": {"auth": "none", "pagination": "list"}
}
```

**Stage 3 — Implementer + test-author (parallel, ~$0.27, 90s)**

3× implementer agents (one per entity) + 1× test-author agent fire in
parallel via Task. Each writes 4 files:

```
/tmp/osp-iter-1/
  shopping_cart/__init__.py
  shopping_cart/models.py        ← SQLAlchemy model (no FKs)
  shopping_cart/schemas.py       ← Pydantic Base/Create/Read/Update
  shopping_cart/router.py        ← FastAPI CRUD router
  line_item/__init__.py
  line_item/models.py            ← shopping_cart_id FK
  line_item/schemas.py
  line_item/router.py
  discount/__init__.py
  discount/models.py             ← shopping_cart_id FK
  discount/schemas.py
  discount/router.py
  tests/test_shopping_cart_api.py
  tests/test_line_item_api.py
  tests/test_discount_api.py
  database.py                    ← stub (project has no get_db)
```

**Stage 4 — Verify + auto-patch**
```
✓ syntax: all files compile
✓ template_placeholders: none
ℹ auto_patched: P2 rewrote pagination assertion to list-shape (test_line_item_api.py)
```

**Stage 5 — Reviewer (~$0.06, 25s)**
```
REVIEW: PASS  (3 files reviewed; no critical findings)
```

**Stage 6 — Wire (dry-run by default)**
```
WIRE PLAN
  + main.py: include shopping_cart_router
  + main.py: include line_item_router
  + main.py: include discount_router
  Migrations: alembic_revision
```

**Stage 7 — Critic (after `--apply`)**
```
VERDICT: SHIPPED  (12 tests passed; 0 failed)
```

**Total**: ~$0.45, ~3.5 minutes wall-time, 17 files generated.

---

## Example 2 — User auth flow with email verification

The auth-intent flow that catches contract drift automatically.

### What you type

```bash
/one-shot "Add user signup with email verification and password reset tokens" @./my-fastapi-app
```

### Key differences from Example 1

**Stage 1 detects auth intent** → spec.json sets `auth: jwt` by default.

**Stage 2 architect** emits:
- `User` (with `email`, `password_hash`, `email_verified` field)
- `EmailVerification` (with `user_id` FK, `token`, `expires_at`)
- `PasswordResetToken` (with `user_id` FK, `token`, `used`)

**Stage 3 implementer** generates auth-aware routers (`Depends(get_current_user)`).
**Test-author** correctly emits 401 assertions (because `auth: jwt`, not `none`).

**No contract drift this time** — the test contract is honest about auth,
so the critic doesn't loop.

**Cost**: ~$0.55, ~4 minutes, 19 files (auth utilities + 3 entity dirs).

---

## Example 3 — Batch job for email notifications

The phase-3 batch-job intent route.

### What you type

```bash
/one-shot "Add a Celery batch job that sends marketing emails to opted-in users daily at 9am" @./my-app --templated
```

Note the `--templated` flag — for batch jobs, the deterministic phase3
pipeline is often the better choice (rich queue / DLQ / monitoring
generators that don't benefit from Claude reasoning).

### Pipeline trace

Routes directly to `one_shot_orchestrator.py --headless`, which invokes
`phase3_runner.py --framework fastapi --language python --job-name
send_marketing_emails --queue-type celery`.

Output: 35 files covering:
- `jobs.py`           — Celery task definition with retry + DLQ
- `scheduler.py`      — Celery Beat schedule
- `job_monitor.py`    — Per-job status monitoring
- `result_handler.py` — Result persistence
- `retry_handler.py`  — Exponential backoff
- `dlq_handler.py`    — Dead-letter queue processing
- … and 29 more

**Cost**: $0.00 (no Claude tokens; pure template generation).
**Quality**: lower than the agentic path (templates can't reason about
your specific user model), but works as a starting scaffold.

---

## When to pick which mode

| Scenario | Recommended |
|---|---|
| Multi-entity feature with relationships | Agentic (`/one-shot ...`) |
| Single entity CRUD | Either; templated is fine |
| Auth flow with email verification | Agentic (gets contract right) |
| Batch jobs / queue workers | Templated (`--templated`) |
| CI/CD / sandboxed environment | Templated |
| Quick prototype scaffold | Templated |
| Production feature for a real app | Agentic + `--review` + `--budget=0.50` |

---

## Common gotchas

1. **The extractor is rule-based** — phrases like "Tag with name, plus
   TagAssignment connecting tags to products" produce noisy output.
   The architect agent cleans it up. If you skip the agentic path
   (with `--templated`), you'll get a messy `TagassignmentConnectingTagsToProducts`
   entity. Don't.

2. **Cost can surprise you** — a 5-iteration critic loop on a complex
   feature can run $1.50+. Always use `--budget` for unfamiliar tasks.

3. **`--apply` is a real mutation** — it edits `main.py`. The `.osp.bak`
   backup is there but only one level deep. Commit before `--apply` on
   important projects.

4. **Existing entities are reused, not regenerated** — if your project
   already has `Product`, the architect marks it `action: reuse` and
   no `product/` files are generated. Add `--force` if you want a
   parallel `Product2`.

5. **The critic uses your project's pytest** — if your venv is missing
   `httpx` or other test deps, the critic verdict will be ERROR. Run
   `pip install -r requirements.txt` in your project before `--apply`.

---

## Where to go next

- Curate external agents: `/curate <task-keyword>` to find better fits
- Inspect cost retroactively: `cat .beads/cost_observations.jsonl`
- Trace a generation: `OSP_OTEL_ENABLED=1 /one-shot ...` (requires
  `opentelemetry-sdk` installed)
- Promote a recurring fix into an auto_patch rule:
  `python skills/one-shot-generator/scripts/promote_rule.py --rule-id ...`
