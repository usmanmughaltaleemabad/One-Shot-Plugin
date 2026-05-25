---
type: reference
last_verified: 2026-05-25
owner: claude
---

# External References

This file documents external repositories that have been studied as research
inputs to the plugin's design. They are deliberately **not** vendored or
submoduled — they are independent codebases with their own ownership and
licensing. When a colleague clones the plugin parent directory and sees these
folders untracked, this is the index that explains what they are.

## Layout

```
c:/Projects/plugin/
├── one-shot-prompting/       # this plugin (master branch is what ships)
├── ay-framework/             # external research clone (see below)
├── nanoGPT/                  # external research clone (see below)
└── docs/                     # superseded — content lives under
                              # one-shot-prompting/docs/ now
```

The `ay-framework/` and `nanoGPT/` directories are listed in the parent
`.gitignore` so they don't pollute git status on the parent repo.

## ay-framework

- Upstream: separate repository (clone present locally only)
- Purpose: reviewed for agent-orchestration patterns and template engine
  ideas
- Relevance to one-shot-prompting:
  - Their setup script's progressive-disclosure interview pattern informed
    the design of `/interview` and `/grill-me`
  - Their template-bin convention is analogous to our `commands/` directory
- Not vendored because the licensing and update cadence are independent
  of this plugin's release cycle.

## nanoGPT

- Upstream: separate repository (clone present locally only)
- Purpose: minimal training loop reference for any future "fine-tune the
  curriculum router" experiments
- Relevance to one-shot-prompting:
  - Currently no production code paths depend on it
  - Kept as a local reference so when we look at the curriculum predictor
    we have a concrete training loop to compare against
- Not vendored because the curriculum predictor we have today is similarity
  + heuristics, not a trained model — there's nothing to copy yet.

## Why these are not submodules

Submodules would pin a commit and force every clone of the parent repo to
also clone the external repos. Since these are research material only,
we keep them as opportunistic local clones, listed in `.gitignore`, with
this document as the index.

If a pattern from one of these eventually lands in the plugin, the relevant
file will live under `one-shot-prompting/` and reference the original via
docstring credit — not via submodule. That keeps the plugin's release
surface clean.

## docs/ at parent — historical note

`c:/Projects/plugin/docs/observability/` previously held two markdown files
(jaeger-setup, metrics-dashboard). They have been merged into
`one-shot-prompting/docs/observability/` so the plugin is self-contained
under its own folder. The parent `docs/` directory was removed in the same
commit as the rest of this consolidation.
