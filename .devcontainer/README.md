---
type: runbook
last_verified: 2026-05-18
owner: claude
---

# Codespaces Sandbox — Try `/one-shot` Risk-Free

This devcontainer lets prospective users **try the plugin without
installing anything locally**. One click in the GitHub UI → a working
VS Code with the plugin loaded, a broken FastAPI demo project ready to
be fixed by `/one-shot`, and full Python + Node + git tooling.

## Free tier

GitHub Codespaces gives every personal account **60 hours/month** of free
compute on the 2-core / 4GB instance — enough to try the plugin many times.

## One-click launch

```
https://codespaces.new/usmanmughaltaleemabad/One-Shot-Plugin
```

Or via the GitHub repo: **Code → Codespaces → Create codespace on master**.

## What you get

1. **Python 3.11** + Node 20 + GitHub CLI pre-installed
2. **The plugin itself**, registered with Claude Code
3. **A deliberately broken FastAPI demo** at `./demo/`:
   - Half-baked `Cart` model with only a `status` field
   - One passing test for `/healthz`
   - No `LineItem`, no `Discount`, no API routes for cart contents
   - This is the gap `/one-shot` fills in real-time
4. **Pre-forwarded port 8000** so the demo's FastAPI server is browser-reachable
5. **The Claude Code extension** pre-installed in VS Code

## Walkthrough (5 minutes)

```bash
# 1. Verify the baseline works (1 test passes)
cd demo
pip install -r requirements.txt
pytest tests/ -v

# 2. Open Claude Code (Cmd/Ctrl+Shift+P → "Claude: Open")

# 3. In the Claude Code panel:
/one-shot "Add line items and discounts to the cart" @./demo

# 4. Review the explain output, then apply:
/one-shot "Add line items and discounts to the cart" @./demo --apply

# 5. Verify the new code works (now ~12 tests pass)
pytest tests/ -v

# 6. Try the API:
uvicorn main:app --reload
# Open the forwarded port 8000 in your browser → /docs
```

## What to look for

The demo is calibrated to show the plugin's strengths:

- **Cross-entity FK resolution**: the architect auto-derives
  `line_items.cart_id` from the spec's `has_many` relationship.
- **Idiomatic patterns**: SQLAlchemy 2.0 `mapped_column` (not legacy
  `Column`), Pydantic v2 `ConfigDict` (not the deprecated `Config`),
  FastAPI Annotated dependencies.
- **Real migration**: Alembic revision file with `create_table`, FK
  constraints, indexes, and a working `downgrade()` in reverse.
- **Service-layer enforcement**: business invariants like
  `cart.total = sum(line_items.price * quantity) - sum(discounts)`
  are honestly enforced in `cart/service.py`, not just declared.

## Cost

Typical cost for this end-to-end demo: **$0.30–0.50** at the default
sonnet pricing. If you'd rather try the templated (free) path:

```bash
/one-shot "Add line items and discounts to the cart" @./demo --templated
```

## Resetting the demo

After `--apply` mutates the demo project, you can `git reset --hard HEAD`
to start fresh. The Codespace persists for ~30 days of inactivity, so
you can return and iterate without re-launching.

## When you're ready to install locally

```bash
git clone https://github.com/usmanmughaltaleemabad/One-Shot-Plugin
claude --plugin-dir ./One-Shot-Plugin
```

Or pin a specific release: `git checkout v1.0.0` before the `claude` step.
