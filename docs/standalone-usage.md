---
type: runbook
last_verified: 2026-05-18
owner: claude
---

# Standalone Usage — Without Claude Code

The plugin is deeply integrated with Claude Code, but **most of its
machinery is plain Python** and runs anywhere — Cursor, Gemini CLI,
plain shell, GitHub Actions, scheduled cron jobs, custom automation.

Only the **Task-spawning orchestration** in `SKILL.md` requires a live
Claude Code session. Everything else is callable as a normal CLI tool.

This document maps which pieces work standalone and how to chain them.

## What works without Claude Code

### ✅ All deterministic scripts (~30 of them)

Run from any Python 3.10+ environment:

```bash
# Scan a project, extract the domain model
python skills/one-shot-generator/scripts/extract_domain_model.py --json \
    "shopping cart with line items and discounts"

# Plan a feature slice (which files to create, in which order)
python skills/one-shot-generator/scripts/scaffold_planner.py \
    --spec my-spec.json

# Topo-sort entities by FK dependency for incremental shipping
python skills/one-shot-generator/scripts/incremental_planner.py \
    --spec my-spec.json --out-dir /tmp/slices

# Detect framework + emit doc-lookup plan
python skills/one-shot-generator/scripts/source_docs_fetcher.py \
    --project ./my-fastapi-project

# Get production-grade body hints for any (framework, file_kind) pair
python skills/one-shot-generator/scripts/body_hints.py \
    --framework fastapi --kind service_layer

# 10-gate production-readiness check
python skills/one-shot-generator/scripts/ship_gates.py \
    --project . --strict

# Emit + index Architecture Decision Records
python skills/one-shot-generator/scripts/adr_writer.py emit \
    --project . --title "Use SQLAlchemy 2.0 mapped_column" \
    --decision "Adopt mapped_column over legacy Column"

# Self-recalibrate cost model from .beads/cost_observations.jsonl
python skills/one-shot-generator/scripts/cost_calibrator.py --apply
```

### ✅ 101 body hints catalogue

The `body_hints.py` script is **fully standalone**. Pipe its JSON
output into Cursor / Gemini / your own automation:

```bash
# Get all FastAPI hints
python skills/one-shot-generator/scripts/body_hints.py \
    --framework fastapi --list --json

# Use a hint as the system prompt for any LLM
python skills/one-shot-generator/scripts/body_hints.py \
    --framework fastapi --kind service_layer \
    | jq -r '.guidance' \
    | your-llm-cli --system-prompt-stdin
```

### ✅ Critic loop driver

Stateful per-iteration tracker for ANY multi-iteration agent loop:

```bash
SANDBOX=/tmp/my-loop
python skills/one-shot-generator/scripts/critic_loop_driver.py init \
    --sandbox $SANDBOX

# After each iteration of YOUR loop, record the verdict
echo '{"verdict": "LOOP", "routes": [...]}' > /tmp/verdict.json
python skills/one-shot-generator/scripts/critic_loop_driver.py record \
    --sandbox $SANDBOX --verdict /tmp/verdict.json
```

### ✅ Live API runner (v4.9)

Direct Anthropic SDK access — no Claude Code needed:

```bash
pip install anthropic
export ANTHROPIC_API_KEY=sk-ant-...

python skills/one-shot-generator/scripts/agentic_session_driver.py \
    --mode live-api --spec my-spec.json --out /tmp/run-001
```

This calls the Anthropic API directly, persists per-agent JSON
records, computes cost. Use it in:
- GitHub Actions (`runs-on: ubuntu-latest`)
- Scheduled cron jobs / Airflow tasks
- CI/CD pipelines
- Cursor / Gemini scripts that shell out to it

### ✅ Cross-agent learning hub

`learnings_hub.py` is a normal append-only log + analytics CLI:

```bash
# Record an outcome from any agent system
python skills/one-shot-generator/scripts/learnings_hub.py record \
    --agent "my-system/code-reviewer" --outcome succeeded \
    --task-keywords security authentication

# Rate it / show top performers / dashboard
python skills/one-shot-generator/scripts/learnings_hub.py top-agents --limit 10
python skills/one-shot-generator/scripts/learnings_hub.py dashboard \
    --window-days 30
```

## What requires Claude Code (~10% of the plugin)

The `SKILL.md` orchestration uses `Task` agent spawns, which is a
Claude Code-specific feature. Specifically:

- **Stage 2 architect spawn**, **Stage 2.7 service-author**, **Stage 3
  implementer × N + test-author parallel**, **Stage 5 reviewer**,
  **Stage 5.5 doubter**, **Stage 7 critic** — these all use `Task` in
  the `/one-shot` flow.
- **The 12-stage orchestration itself** — runs inside a Claude Code
  session that follows `skills/one-shot-generate/SKILL.md`.

The `live-api` mode (v4.9) is the **bridge**: it replays the same
agents through the Anthropic SDK directly, so the agentic flow runs
*without* a Claude Code session. Use it for CI / scheduled runs.

## Integration patterns

### Cursor — use as a CLI from inside Cursor's terminal

Cursor's built-in terminal can run any of the standalone scripts.
Common pattern: write a Cursor rule (`.cursor/rules/body-hints.md`)
that says "for FastAPI files, before generating code, shell out to
`body_hints.py --framework fastapi --kind <kind>` and use that as the
contract."

### Gemini CLI — pipe body hints as system prompt

```bash
HINT=$(python skills/one-shot-generator/scripts/body_hints.py \
    --framework fastapi --kind service_layer | jq -r '.guidance')

gemini --model gemini-2.0-pro --system "$HINT" "Write the cart service"
```

### GitHub Actions — automate the full pipeline

```yaml
# .github/workflows/regenerate-on-spec-change.yml
name: Regenerate on spec change

on:
  push:
    paths: ['specs/*.json']

jobs:
  regenerate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install anthropic
      - run: |
          python skills/one-shot-generator/scripts/agentic_session_driver.py \
            --mode live-api \
            --spec specs/${{ github.event.head_commit.modified[0] }} \
            --out runs/${{ github.sha }}
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      - run: |
          python skills/one-shot-generator/scripts/ship_gates.py \
            --project . --strict
```

### Plain Python — embed the pieces

```python
import json
import subprocess
import sys

# Use scaffold_planner directly
result = subprocess.run([
    sys.executable, 'skills/one-shot-generator/scripts/scaffold_planner.py',
    '--spec', 'my-spec.json'
], capture_output=True, text=True, check=True)

plan = json.loads(result.stdout)
for file_spec in plan['files_to_create']:
    print(f"  {file_spec['path']} ({file_spec['kind']})")
```

## Summary table — what runs where

| Component | Claude Code | Cursor / Gemini / shell | CI / scheduled |
|---|---|---|---|
| `/one-shot` slash command | ✅ | ❌ | ❌ |
| 30+ deterministic scripts | ✅ | ✅ | ✅ |
| `live_api_runner.py` (Anthropic SDK direct) | ✅ | ✅ (with `pip install anthropic`) | ✅ |
| 101 body hints catalogue | ✅ | ✅ | ✅ |
| ADR writer, ship-gates, cost-calibrator, learnings-hub | ✅ | ✅ | ✅ |
| Multi-iteration critic loop driver | ✅ | ✅ | ✅ |
| Doubt-driver | ✅ | ✅ | ✅ |
| Incremental planner | ✅ | ✅ | ✅ |

**Bottom line**: about 90% of the plugin's value (the 101 hints, all
the deterministic helpers, and the headless live-api path) works
outside Claude Code. The native `/one-shot` flow is the cleanest
experience, but it's not a hard requirement.

## Related

- [tests/integration/README.md](../tests/integration/README.md) —
  validation harnesses that exercise the full pipeline programmatically
- [docs/scripts-index.md](scripts-index.md) — full catalog of
  deterministic scripts
- [docs/observability/production-collector.md](observability/production-collector.md) —
  production OTel collector deployment guide
