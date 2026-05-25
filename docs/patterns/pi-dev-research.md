---
type: research
last_verified: 2026-05-25
owner: claude
sources:
  - https://pi.dev/docs/latest
  - https://pi.dev/packages
---

# pi.dev Research Findings

The user asked us to look at pi.dev — what it is, what we can grab, and which
packages might be relevant for the one-shot-prompting plugin. This is the
honest write-up.

## What pi.dev Is

**pi.dev** is a minimal terminal coding harness for LLM agents, with a
TypeScript extension model and a package ecosystem under `pi-*`. It is
structurally analogous to Claude Code itself, not to our plugin — i.e.,
it is a *peer* of the harness we are running inside, not a peer of the
one-shot-prompting plugin.

Core primitives:
- Extensions (tools, commands, events, custom UI)
- Skills (reusable on-demand agent capabilities)
- Prompt templates expanded from slash commands
- JSONL-based persistent session storage
- Programmatic APIs (SDK, RPC, JSON event streaming)
- Session branching / tree navigation
- Context compaction for long sessions
- Multi-provider support (Anthropic, OpenAI, …)

Anyone familiar with Claude Code's skill / command / agent triad will
recognise every one of these.

## The Mapping (pi.dev ↔ one-shot-prompting)

| pi.dev concept | one-shot-prompting equivalent | Notes |
|---|---|---|
| **pi-subagents** (delegation, chains, parallel) | Task-tool dispatch inside `/one-shot` pipeline (architect → implementer × N + test-author → reviewer → critic) | Same idea, different harness |
| **pi-crew** (coordinated AI teams) | The 18-agent orchestration documented in CLAUDE.md | Same idea |
| **taskplane** (parallel exec + checkpoints) | The `superpowers:subagent-driven-development` workflow we already invoke | Same idea |
| **pi-hermes-memory** (SQLite FTS5) | `.beads/*.jsonl` + curriculum_seed.jsonl + grep | Different impl; FTS5 is interesting at scale |
| **context-mode** (sandbox, save context) | Subagent isolation by default | Same idea |
| **pi-lens** (LSP + linter feedback) | Our reviewer agent | Same idea |
| **gentle-pi** (SDD + TDD evidence) | Our TDD enforcement + replay evals | Same idea |
| **pi-lean-ctx** (token-efficient routing) | Our cost_budget gating + haiku-vs-sonnet routing | Same idea |

The honest finding: **pi.dev is a parallel ecosystem solving the same
problems with the same patterns.** There is no missing primitive we lack;
there are well-named idioms we already implement.

## What's Worth Borrowing

After studying the package catalogue, three concrete ideas surfaced as
worth adapting — and several that are not. We are being honest about both
to avoid the "audit said we did 32 patterns" hallucination problem the
plugin has burned itself on before.

### Worth adapting (small, concrete)

1. **JSONL session entry types** (from pi.dev's session format).
   Our `.beads/*.jsonl` files are loosely structured. pi.dev uses
   typed entries (user_msg, agent_msg, tool_call, tool_result, …).
   Adopting a similar enum-style `type:` field in beads would make the
   curriculum / cost / failure logs cleaner to filter without grep
   pattern-matching. *Status: tracked as BD-followup, low priority.*

2. **Confidence labels on derived stats** (inspired by `gentle-pi`'s
   evidence/guardrail framing). Already shipped — `scripts/cost_stats.py`
   now emits confidence: none / low / low-medium / medium / high based on
   sample count, so the README claim about cost calibration becomes
   observable instead of asserted.

3. **Tree-style replay exploration** (from pi.dev's session branching).
   Our replay evals are a flat list of scenarios. Branching the replay
   tree (one scenario → ten variants, all scored) is a path forward when
   we want to push from 26 scenarios to ~200 without hand-writing every
   one. *Status: deferred — not a v1.0.1 gap; revisit when we run out of
   manual coverage to add.*

### Considered and rejected

- **pi.dev's SQLite FTS5 for curriculum search.** Our combined curriculum
  is 14 entries today. Grep is fine. FTS5 becomes worth the dependency at
  ~1000 entries. We will not add a SQLite dependency to "look modern" —
  we'd be paying complexity for no measurable benefit.

- **Multi-provider abstraction (OpenAI in addition to Anthropic).** The
  plugin runs inside Claude Code, which is single-provider by design.
  Adding an abstraction would be dead code.

- **TypeScript extension model.** Our plugin is Python + Markdown, which
  is what Claude Code's skill/command/agent model expects. Rewriting in
  TypeScript would be churn for no user-visible benefit.

- **A pi-dev/* "vector store" package as a curriculum embedding backend.**
  We already have `scripts/embedding_cache.py` (WS4) which uses
  sentence-transformers as an optional dependency. Switching it to a
  pi-dev package would not change behaviour for users; it would add a
  dependency and a vendor coupling.

## What This Closes in the README

The user's request was to "check what we can grab from here for our
plugin and what best practices we can get." The honest answer is in this
file:

- The conceptual mapping in the table above is the "best practices" — we
  already implement them; we now have a cross-reference for users who
  arrive from pi.dev.
- Two small ideas are tracked as follow-ups (typed JSONL, branched
  replay tree).
- One idea (confidence labels) shipped as `scripts/cost_stats.py` in the
  same v1.0.1 / v1.2.1 release as this document.
- Several ideas were considered and rejected with reasons, to avoid the
  prior pattern of claiming integrations that don't actually exist.

## Source verification

This document is the human-readable distillation of two `WebFetch`
queries against `pi.dev/docs/latest` and `pi.dev/packages` on
2026-05-25. The raw findings are in the git history of this file. If
pi.dev's surface changes meaningfully, regenerate.
