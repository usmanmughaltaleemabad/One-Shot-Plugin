---
type: runbook
last_verified: 2026-05-18
owner: claude
---

# Troubleshooting

Common issues + fixes when running `/one-shot` and friends. If your
issue isn't here, open a [GitHub issue](https://github.com/usmanmughaltaleemabad/One-Shot-Plugin/issues)
with the error output + `python --version` + which slash command you ran.

## Installation

### `claude --plugin-dir ./One-Shot-Plugin/one-shot-prompting` says "no commands found"

The plugin directory must be **exactly** `one-shot-prompting` (the
subfolder containing `.claude-plugin/plugin.json`), not the parent
`One-Shot-Plugin` repo root.

```bash
# Correct:
claude --plugin-dir ./One-Shot-Plugin/one-shot-prompting

# Wrong (parent repo, no plugin.json there):
claude --plugin-dir ./One-Shot-Plugin
```

### `/one-shot` doesn't appear in Claude Code's command palette

Three causes, most common first:

1. **Plugin not reloaded.** Restart Claude Code after running the
   `--plugin-dir` flag.
2. **Stale `.claude/plugins.json` cache.** Delete it and relaunch:
   ```bash
   rm ~/.claude/plugins.json  # macOS / Linux
   del %USERPROFILE%\.claude\plugins.json  # Windows
   ```
3. **Frontmatter parsing failed.** Run the compliance audit:
   ```bash
   python skills/one-shot-generator/scripts/compliance_audit.py
   ```
   Any command file with malformed YAML frontmatter will be silently
   skipped by Claude Code.

## Running `/one-shot`

### "spec.json was malformed" after Stage 2 architect

The architect agent occasionally returns valid-looking JSON wrapped
in Markdown fences. The orchestrator retries on parse failure — wait
for the second attempt. If both fail:

- Pass `--review` to inspect what's being produced
- Pass `--templated` for the deterministic fallback path (zero token cost)

### Stage 7 critic returns LOOP three times → ESCALATE

This is the multi-iteration cap working as designed. Inspect the
escalation summary:

```bash
cat <sandbox>/.osp-loop-state.json
```

Common root causes:
- **Test infrastructure missing** — pytest can't import your project's
  modules because `conftest.py` doesn't set the sys.path correctly
- **Real bug in the spec** — invariants the architect declared can't
  actually be satisfied (e.g. `total = sum(items) - discounts` but
  `discounts > sum(items)` is legal per the spec)
- **External dependency** — generated code imports a library not in
  `requirements.txt`

Fix the root cause and run `/one-shot --resume` to skip already-completed
stages (v4.13+).

### Stage 5.5 doubter loops forever

The doubter has a hard cap of 2 rounds per artifact (configured in
`doubt_driver.py`). If a single artifact is hitting the cap, the
implementer is producing the same flagged code repeatedly — usually
a body_hints mismatch.

Fix:
1. Pass `--no-doubt` to skip doubter for this run
2. Inspect the generated artifact's actual content vs the body_hints
   for that file kind:
   ```bash
   python skills/one-shot-generator/scripts/body_hints.py \
       --framework fastapi --kind service_layer
   ```
3. If the hint genuinely conflicts with what the codebase expects,
   override via `--no-source-driven` (skip Stage 1.8)

### Stage 6 ship-check verdict is BLOCKED

Run the gates standalone to see which checks failed:

```bash
python skills/one-shot-generator/scripts/ship_gates.py --project . --json | jq '.gates[] | select(.status == "FAIL")'
```

Common fails:
- **`no_secrets_in_diff`** — `.env` or API key landed in the generated
  output. Move to env var, rotate the key.
- **`migration_reversible`** — Alembic migration's `downgrade()` is
  empty / `pass`. Re-spawn migration_generator with hints.
- **`tests_pass`** — pytest crashed. Fix the test infra (see above).

Pass `--no-ship-check` to bypass (NOT recommended for production).

## `--legacy-safe` mode

### "MAX_FILES_EXCEEDED: spec produces N files"

Legacy-safe mode caps generation at 3 files per run. Split the feature
into multiple smaller `/one-shot --legacy-safe` invocations (one
entity per run), OR fall back to `--incremental` if you can review
per-slice.

### "IMPACT_HEAT_DO_NOT_TOUCH: file X has heat score 75+"

The file you're trying to modify is imported by 100+ other files.
Legacy-safe mode refuses to auto-mutate it. Options:

- **Refactor first** — split the high-fanout file into smaller modules
- **Drop `--legacy-safe`** — accept the risk explicitly, with manual
  human review on the diff
- **Use `--no-apply`** — generate the new files into a separate
  directory; the user manually integrates

## `--mode live-api` (headless SDK)

### "missing_anthropic_api_key" skip

The script skipped intentionally because either:

1. `ANTHROPIC_API_KEY` env var is unset:
   ```bash
   export ANTHROPIC_API_KEY=sk-ant-...
   ```
2. The `anthropic` Python SDK isn't installed:
   ```bash
   pip install anthropic
   ```

### Live API run costs more than expected

Run `cost_calibrator.py --json` to see if your `PER_AGENT_TOKEN_ESTIMATES`
constants have drifted from reality. If they have, `--apply` rewrites
them from `.beads/cost_observations.jsonl`:

```bash
python skills/one-shot-generator/scripts/cost_calibrator.py --apply
```

## `/prune` (zombie code detector)

### False positive — a legit file is flagged as zombie

The scanner is conservative but `/prune scan` does emit false positives
for files reachable via dynamic import (`importlib.import_module(name)`,
Django's `INSTALLED_APPS`, Spring's `@ComponentScan`).

Fix:
- Add the file to the `KEEP_PATTERNS` regex list in `zombie_pruner.py`
- OR add a `# pragma: no-prune` comment to the file's first line

Note: `/prune` in default mode only REPORTS — it never deletes anything
unless you explicitly pass `delete --paths a.py --git-commit`.

## Tests

### `python -m pytest tests/` fails with "ModuleNotFoundError: No module named 'lib'"

The plugin's scripts use a `lib/` package next to them. Run pytest
from the plugin root, not from the `tests/` subdirectory:

```bash
# Correct:
cd one-shot-prompting && python -m pytest tests/

# Wrong:
cd one-shot-prompting/tests && python -m pytest .
```

### Tests pass locally but fail in CI

Probably encoding-related. Set:

```yaml
env:
  PYTHONIOENCODING: utf-8
```

In your GitHub Actions / CI config. The Windows console (cp1252)
doesn't accept the same character set as Linux (UTF-8); CI matrix
tests must declare encoding explicitly.

## Codespaces sandbox

### Codespace starts but `/one-shot` complains the plugin isn't loaded

Run the registration command manually:

```bash
claude --plugin-dir /workspaces/One-Shot-Plugin/one-shot-prompting
```

Then restart Claude Code from the VS Code command palette
(`Ctrl+Shift+P` → `Claude: Reload`).

### Codespace runs out of free hours

GitHub gives 60 hrs/month free. To extend:
- **Hibernate when idle**: VS Code → `Codespaces: Stop Current Codespace`
- **Delete unused codespaces**: `gh codespace delete --codespace NAME`
- **Upgrade to paid tier**: $0.18/hr for 2-core, much cheaper than
  re-running `/one-shot` against a real production codebase

## Filing an issue

If none of the above helps:

1. Run the compliance audit + capture output:
   ```bash
   python skills/one-shot-generator/scripts/compliance_audit.py --json > audit.json
   ```
2. Capture the failing command's output:
   ```bash
   <your command> 2>&1 | tee /tmp/osp-error.log
   ```
3. Open an issue at https://github.com/usmanmughaltaleemabad/One-Shot-Plugin/issues
   with both files attached + your `python --version` + which `/one-shot`
   flags you used.

Maintainer response time: < 48 hours during marketplace review window.
