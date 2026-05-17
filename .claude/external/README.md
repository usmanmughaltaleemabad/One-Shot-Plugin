---
type: reference
last_verified: 2026-05-18
owner: claude
---

# `.claude/external/` — Optional Local Mirror of External Resources

This directory is **optional**. The Tier 4 self-extending plugin works
fine without it; entries in `.claude/registry/*.json` are pointers to
upstream resources that get invoked through Claude Code's normal Task /
skill / MCP plumbing.

If you want to mirror an external agent or skill locally (for offline
use, or to pin a specific version), the curator can write copies into:

| Subdirectory | Holds |
|---|---|
| `agents/` | Copies of external agent `.md` files |
| `skills/` | Copies of external skill folders (each with `SKILL.md` + scripts/) |
| `mcp/` | MCP server connection notes (NOT executable code — the user must connect MCP servers via Claude Code) |

The plugin never auto-syncs these. Updates are manual and gated by the
curator skill with explicit user approval (same as adding a registry
entry).

## Why this is separate from `.claude/agents/` and `skills/`

`.claude/agents/` and `skills/` are the plugin's OWN agents and skills —
loaded by Claude Code as part of the plugin install. Anything in
`.claude/external/` is a vendored copy of someone else's resource, kept
distinct so:

- Updates to upstream don't silently overwrite plugin code.
- Provenance is obvious: anything under `external/` came from somewhere
  else, with an `_source.json` file recording where + when.
- Removing the plugin doesn't remove vendored external resources that
  other tools might also depend on.

## How an entry lands here

1. User runs `/curate <task>` (or the curator triggers from `/one-shot`
   when no strong local match exists).
2. Curator searches and presents candidates.
3. User approves an entry AND opts in to local mirroring.
4. Curator fetches the upstream file(s) and writes to `external/<kind>/`.
5. Curator writes `_source.json` with the upstream URL, commit SHA (if
   available), license, and `fetched_at`.

Step 4 is optional — by default, registry entries are pointers only and
nothing lands here. Local mirroring is for users with specific needs
(offline, pinning, air-gapped environments).

---

This directory is empty until the curator fills it.
