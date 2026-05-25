---
type: reference
last_verified: 2026-05-25
owner: claude
---

# Validation Pathway

This document replaces the "zero external users" line in the v1.0.0
README. That line was honest, but it framed the gap as a wall instead of
a door: you, the reader of this document, are the path to closing it.
Here is exactly what "validating the plugin" looks like and what evidence
makes it count.

## The three validation tiers

| Tier | What it proves | How to do it |
|---|---|---|
| **Tier 1 — dry-run** | The plugin's deterministic plumbing works on your codebase | `/one-shot "<feature>" @./your-project` (without `--apply`) |
| **Tier 2 — apply-and-revert** | The generated code compiles, tests pass, and `--apply` actually wires it in | `/one-shot "<feature>" @./your-project --apply`, run your tests, then `git revert HEAD` |
| **Tier 3 — ship-it** | The generated code went to production and survived a real user | Anything that earns a `git log` entry on a deployed branch |

Tier 1 takes about three minutes and costs zero API tokens beyond your
existing Claude Code session. Tier 3 is the bar that closes the
external-users gap permanently.

## What counts as evidence

A validation report is one of:

1. **A merged PR** in any repository other than this one, whose commits
   reference `one-shot-prompting` as the generator (e.g.
   `Generated with /one-shot - reviewed and adjusted by <name>`).

2. **A public gist or write-up** describing the feature you generated,
   the framework, the cost in tokens (use `scripts/cost_stats.py` to
   read your own observations log), and what you had to adjust by hand
   afterwards.

3. **A failure report**. Negative evidence is also evidence. If the
   plugin generated nonsense for your codebase, a one-paragraph
   description of where it broke is more useful than ten more
   self-validated replays.

Send any of the above as a GitHub issue on this repository tagged
`validation`. We will link the validations from this file.

## Reading the plugin's own honesty signals

Before you spend tokens, check what the plugin itself reports about its
own confidence:

```bash
python scripts/cost_stats.py          # how many real cost samples exist
python scripts/curriculum_status.py   # how much real failure data has been learned
python tests/evals/agentic_evals.py --mode replay --json | jq '. | length'
                                       # how many replay scenarios are graded
```

If `cost_stats` says "low confidence, directional" — which it does
today — that is the plugin telling you to treat its $0.45/feature
estimate as a rough number, not a contract. The whole point of this
release is to surface those signals so external users can make
informed decisions instead of trusting marketing.

## Recorded validations

This section is populated as external validations arrive. As of
2026-05-25 it is empty by construction: this is the document that
opens the channel.

| Date | Repository | Feature | Tier | Notes |
|---|---|---|---|---|
| _none yet_ | — | — | — | — |
