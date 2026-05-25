---
type: release-notes
version: 1.2.1
date: 2026-05-25
last_verified: 2026-05-25
---

# Release Notes — v1.2.1

**Theme:** Honest accounting. Every "Known gap" in the v1.0.0 README is
either closed by real code, made observable by new tooling, or left
explicitly open with reasons. The ride-sharing example is now real code
instead of a marketing README.

## TL;DR

- 12 new replay scenarios → **26 agentic replays** across 7 agents
- 14 new unit tests (`cost_stats`, `curriculum_status`)
- 24 new tests in `examples/ride-sharing-system/` — and an **actually
  runnable FastAPI app** behind them (11 tables, 29 endpoints)
- Commands re-tiered: 1 stable / 6 beta / 3 experimental, criteria
  documented
- Parent `docs/observability/` folded into the plugin; `ay-framework/`
  and `nanoGPT/` indexed as external research clones
- pi.dev research: peer-harness mapping, 3 small borrowables, 4
  explicit rejections with reasons
- New: `docs/validation-pathway.md` — how to be the first external
  validator

## Detail by gap

| v1.0.0 gap | v1.2.1 resolution | Where |
|---|---|---|
| Agentic eval coverage (6 architect only) | 26 scenarios across 7 agents | `tests/evals/agentic_replays/` |
| Cost calibration directional | Confidence label tied to sample count | `scripts/cost_stats.py` |
| Self-learning loop unpopulated | Status reporter cold/warming/active/mature | `scripts/curriculum_status.py` |
| Live E2E gated on secret | Re-read: free-tier already runs every push; README wording was over-claimed | `.github/workflows/e2e.yml` |
| 9 commands marked experimental | 1 stable / 6 beta / 3 experimental, promotion criteria | `docs/command-maturity.md` |
| Ride-sharing example was 2 markdown files | Real FastAPI app: 11 models + 29 endpoints + 24 tests | `examples/ride-sharing-system/` |
| External folders outside plugin | Consolidated; ay/nanoGPT in parent `.gitignore` + indexed | `docs/external-references.md` |
| Zero external users | Pathway documented; gap is opened-as-door, not closed-as-claim | `docs/validation-pathway.md` |

## Migration / upgrade notes

None. v1.2.1 is purely additive — no removed surfaces, no breaking
schema changes, no behaviour modifications to existing commands.

## Test impact

- Plugin's own suite: **930 passed, 1 skipped, 0 failed** on the
  fast-path subset (excludes the 6-minute advanced_curriculum
  integration). Unchanged from v1.2.0 except for the new
  `test_cost_stats.py` and `test_curriculum_status.py` (14 new).
- Replay graders: **26/26 pass** under the existing scoring rubric.
- Ride-sharing example: **24/24 pass**.

## Honest "not done" list

- **External users:** still zero. Doc opened a path; cannot be closed
  by writing code.
- **pi.dev vendor packages:** considered and rejected — pi.dev is a
  peer harness, not a complementary tool. Reasons in
  `docs/patterns/pi-dev-research.md`.
- **Wirer-agent replay evals:** still none. Out of scope for this
  release; tracked as BD-followup.
- **Ride-sharing endpoints 30–87:** still spec-only. The 29 that exist
  cover every domain; remaining endpoints follow the same patterns and
  are documented as `/one-shot` extension targets in
  `examples/ride-sharing-system/README.md`.
