---
type: reference
last_verified: 2026-05-18
owner: claude
---

# Registry — Tier 4 Self-Extending Plugin

This directory holds curated catalogues of external resources the plugin
can discover, recommend, or route work to during the agentic pipeline.
Three resource types, three files:

| File | What it lists |
|---|---|
| `agents.json` | External Claude Code agents (pr-review-toolkit, Plan, Explore, …) |
| `skills.json` | External skills the plugin recognises and may suggest |
| `mcp_servers.json` | MCP servers the plugin knows can extend a pipeline stage (Chrome DevTools for UI critic, Supabase for schema lookup, …) |

## How entries get added

**Manually** — edit the JSON file directly.

**Via the curator skill** — `skills/curator/SKILL.md` (Tier 4.3). When the
main pipeline encounters a task it doesn't have a strong local match for,
the curator can:

1. Use `WebSearch` to find published agents/skills/MCPs that fit
2. `WebFetch` their definition (README + frontmatter)
3. Present candidates to the user
4. On approval, append the entry to the relevant registry file

**Curator never executes code from outside the plugin.** It only
catalogues pointers. Execution still happens through Claude Code's normal
agent/skill/MCP invocation paths the user has consented to.

## How entries get used

`agent_discovery.py` reads all three files plus the local
`.claude/agents/` and `.claude/skills/` directories, scores every entry
against the current task's keywords, and returns the top N matches.

The main pipeline (in `one-shot-generate/SKILL.md` Stage 0.5) consults
this score. When an external agent scores >= our local agent for a given
specialty AND has `preferred_over_local: <local-name>` set, the pipeline
routes that stage to the external agent.

## Safety stance

- **The plugin never auto-installs MCP servers** — they must already be
  connected by the user in Claude Code.
- **The plugin never executes downloaded code** — agents and skills are
  invoked through Claude Code's `Task` tool, which respects the user's
  installed plugin set.
- **Every addition to the registry is logged** in `agents.json` /
  `skills.json` / `mcp_servers.json` with an `added_at` timestamp and
  source provenance, so users can audit the curator's work.
- **The user is always asked before the curator adds an entry** — the
  curator skill makes this explicit.
