---
type: reference
last_verified: 2026-05-25
owner: claude
version: v1.2.0
---

# CI Setup — Enabling the live E2E job

The repo ships with two CI workflows that test the agentic pipeline:

- **`cross-os.yml`** — runs the full test suite (492+ tests) on
  Ubuntu × macOS × Windows × Py 3.10/3.11/3.12. Always runs, no setup
  needed.
- **`e2e.yml`** — runs replay evals + skill-wiring tests + (optionally)
  a real Anthropic-API run against a fixture project.

The `e2e.yml` workflow has two jobs:

## Job 1: `e2e-dry` — free, no setup required

Runs on every push to master. Validates:
- Replay evals pass for all 14 scenarios across 7 agent types
- `live_api_runner.py` refuses gracefully without an API key
- Skill-wiring tests confirm mattpocock skills are wired into stages
- Curriculum seed file is well-formed
- Compliance audit is 15/15 green

**No setup needed.** Already runs.

## Job 2: `e2e-live` — needs your API key

Runs a real architect-agent scenario against the Anthropic API and asserts
the output scores ≥ 0.85 against the contract. Also dry-runs the live API
runner against a fastapi fixture project.

**Cost:** ~$0.30 per run. Triggered on push to `skills/one-shot-generate/**`,
`.claude/agents/**`, or manually from the Actions tab. Skipped on forks.

### To enable

1. **Get an Anthropic API key** at https://console.anthropic.com/
2. **Add it as a GitHub secret**:
   - Go to repo → Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `ANTHROPIC_API_KEY`
   - Value: your `sk-ant-...` key
   - Click "Add secret"
3. **Trigger a run** to verify:
   - Push any commit touching the watched paths, OR
   - Go to Actions → "E2E Pipeline Test" → "Run workflow" → master

The job will execute one live architect run, save the result as a
workflow artifact (`e2e-live-result`), and pass if score ≥ 0.85.

### What the live job protects

| Without `e2e-live` | With `e2e-live` |
|---|---|
| Replay evals only — frozen architect outputs scored against a contract. | Live agent invocation — the actual model's behavior today against the contract. |
| Won't catch model regressions (Anthropic ships a new Sonnet, scores drop). | Catches model regressions on the next scheduled run. |
| Won't catch SKILL.md drift that breaks live execution. | Catches when SKILL.md gets restructured in a way Claude can't follow. |

### Budget guard

Each scheduled run costs ~$0.30. With the Monday cron + a push trigger,
expect ~$5–10/month. Configure your Anthropic billing alerts accordingly.

To make the job stricter (cost ~$1.50/run, but covers more), edit
`.github/workflows/e2e.yml` and add more scenarios to the architect eval
step (e.g. `--scenario architect-subscription-billing`).

### What happens without the secret

If `ANTHROPIC_API_KEY` is not set in repo secrets:
- The `e2e-live` job is skipped (the `if:` guard sees an empty secret).
- The `e2e-dry` job still runs and validates everything except live
  inference.
- The README's "agentic eval coverage: architect replay scenarios only"
  remains accurate — no live verification yet.

### Forks

Forks never see secrets. The `e2e-live` job skips automatically on PRs
from forks. Only the original repo runs live evals.
