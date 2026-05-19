# Contributing to ONE SHOT PLUGIN

Thanks for considering a contribution. The plugin is solo-maintained
today but built to absorb contributions cleanly — every script is
testable, every agent is documented, every change goes through CI.

## Quick start

```bash
git clone https://github.com/usmanmughaltaleemabad/One-Shot-Plugin
cd One-Shot-Plugin
python -m pytest tests/           # all tests should be green
bash .claude/scripts/smoke-test.sh
```

## What we welcome

In rough priority order:

1. **Bug reports** — file via the issue template; include a `bead-id`
   from `.beads/failures.jsonl` if you have one.
2. **Real-world `/one-shot` recordings** — the agentic eval harness
   (`tests/evals/agentic_evals.py`) is built to ingest recorded runs.
   Run `/one-shot` on your project, capture the architect's spec.json,
   PR a new file under `tests/evals/agentic_replays/`.
3. **Cross-language body hints** — `body_hints.py` is FastAPI-mature
   but Django/Spring/Go/NestJS hints could be richer. See
   `docs/path-to-10.md` § Tier B.
4. **Eval fixtures** — add a fixture under `tests/evals/fixtures/`
   plus golden output. Regression-tracks the deterministic pipeline.
5. **External agent / MCP server proposals** — use the
   `agent_registry_proposal` issue template. Curator skill reviews +
   adds with provenance.
6. **Docs polish** — every `.md` in `docs/` should be self-contained
   and accurate.

## Code style

- **Stdlib only by default.** Optional dependencies are OK with a
  graceful no-op fallback (see `lib/telemetry.py` as the pattern).
- **Every entry-point script must call `bootstrap_runtime()`** from
  `lib/base_script.py` (handles Windows UTF-8 + sys.path).
- **Type hints required** on public function signatures.
- **One concise docstring per public function/class.** No multi-page
  PhD theses.
- **No `# TODO` comments without a bead reference**:
  `# TODO(bd-task-20260518-007): explain what + by when`.

## Test policy

- Every new module gets at least one invocation-based test in
  `tests/test_<module>.py`.
- Tests use `subprocess.run([sys.executable, str(SCRIPTS / script), ...])`
  so they validate the script's CLI surface, not just internal
  functions.
- New eval fixtures must score ≥ 0.85 on first golden capture.
- Pre-commit: run `python -m pytest tests/` and
  `bash .claude/scripts/smoke-test.sh`.

## Agent policy

- New `.claude/agents/*.md` must include `tools:` + `model:`
  frontmatter.
- Use `haiku` for file-writers (5× cheaper). Use `sonnet` for
  reasoners. Document the rationale in the agent body.
- "Propose, never apply" pattern — see `docs-author.md` /
  `prompt_versioner.py` for how to write an agent that suggests
  without auto-mutating.

## PR checklist

Copy this into your PR description:

- [ ] `pytest tests/` green
- [ ] `bash .claude/scripts/smoke-test.sh` green
- [ ] CLAUDE.md still < 100 lines (if you edited it)
- [ ] New scripts have at least one invocation-based test
- [ ] New agents have `tools:` + `model:` frontmatter
- [ ] CHANGELOG.md updated under "Unreleased" section
- [ ] Tier docs updated if you touched the pipeline structure

## Maintainer response time

- Bugs labeled `critical`: within 24 hours
- Bugs labeled `high`: within 72 hours
- Feature requests: triage within 1 week (may not be implemented soon)
- Registry proposals: within 1 week, reviewed via the curator skill

## Communication

- **Issues**: https://github.com/usmanmughaltaleemabad/One-Shot-Plugin/issues
- **Discussions**: https://github.com/usmanmughaltaleemabad/One-Shot-Plugin/discussions
- **Email**: musman.mughal@taleemabad.com (security disclosures only)

By contributing you agree your work is licensed under the same MIT
license as the project.
