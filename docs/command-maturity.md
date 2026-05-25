---
type: reference
last_verified: 2026-05-25
owner: claude
---

# Command Maturity Tiers

This document is the authoritative source for the `status:` field in command
front matter. It exists because the README v1.0.0 "Known gaps" entry that
flagged "9 experimental commands" was treating *experimental* as a single
catch-all, which over-promised in some places and under-promised in others.

## Tiers

- **stable** — the command is the recommended way to perform its task.
  Has integration tests + replay evals + at least one shipped feature
  generated through it. Behaviour is contract-frozen for the current major
  version.

- **beta** — feature-complete and exercised in development. Documented
  argument contract is stable. Lacks the replay-eval and external-usage
  evidence required for *stable*. Safe to use; minor argument tweaks
  possible in a minor version bump.

- **experimental** — design or interface may change without notice. Use at
  your own risk; flagged so users know not to depend on it in scripts.

A command is bumped from *experimental* → *beta* when its argument-hint and
README example stop changing across releases. *beta* → *stable* when at
least one replay eval is recorded against it and there is non-author
evidence of use.

## Roster (as of 2026-05-25)

### Stable
- **one-shot** — primary agentic pipeline. 26 replay scenarios across 7 agent
  types; the only command with a published cost/latency budget.

### Beta (promoted from experimental on 2026-05-25)
- **architecture** — pre-code blueprint. Deterministic generator; stable CLI
  surface. Lacks an eval covering the blueprint→spec→code roundtrip.
- **execute-plan** — markdown plan execution. Used by superpowers
  `subagent-driven-development`; resumable across sessions.
- **sys-debug** — 4-phase root cause investigation. Documented methodology;
  no replay eval yet.
- **tdd** — Red-Green-Refactor cycle enforcement. Phase gates work; no
  cross-language eval.
- **strangler** — strangler pattern migration scaffold. Generator works on
  Python; other languages untested.
- **templates** — curated prompt library (25+ entries). Read-only browse UX;
  promoted to beta because the library content is curated and the browser
  surface is stable.

### Experimental (kept as such, with reasons)
- **browser-test** — requires chrome-devtools MCP server. Useful but the
  dependency surface is large and the failure modes when the MCP server is
  unhealthy are not yet well-handled.
- **tour** — interactive onboarding walkthrough. Lightly tested; primarily
  exists for first-time users and the script may change as we learn what
  trips people up.
- **generate** — predates `/one-shot`. Kept experimental because `/one-shot`
  supersedes it for new work; retained for users on legacy scripts.

## How this differs from the v1.0.0 README

The v1.0.0 README claimed "9 commands marked status: experimental". That
count was correct as of release but conflated three meaningfully different
maturity levels. After this reclassification:

- 1 stable: one-shot
- 6 beta:  architecture, execute-plan, sys-debug, tdd, strangler, templates
- 3 experimental (down from 9): browser-test, tour, generate

Nothing was archived or removed. Every command in the v1.0.0 roster is
still present and callable; the change is in how their reliability is
advertised.
