---
type: reference
last_verified: 2026-05-25
owner: claude
version: v1.2.0
---

# Tier 4 — Self-Extending Plugin

Tier 4 is the layer that lets the plugin **grow** across sessions. The
agentic pipeline (Tier 3.5) is bounded by what's installed. Tier 4 makes
that boundary porous: when the pipeline encounters a task its local
agents don't handle well, it can discover external agents/skills/MCP
servers and route work to them — with explicit user approval at every
step.

## The three new pieces

| Piece | Role |
|---|---|
| `.claude/registry/{agents,skills,mcp_servers}.json` | Curated catalogue of known-good external resources |
| `skills/one-shot-generator/scripts/agent_discovery.py` | Scores task vs registry+local; emits ranked hits + recommendations |
| `skills/curator/SKILL.md` + `/curate` command | WebSearch-driven discovery of NEW resources, with user approval to register |

## How it plugs into the agentic flow

`one-shot-generate/SKILL.md` adds a new **Stage 0.5**:

```
Stage 0   Curriculum (past failures)
Stage 0.5 Discovery (registry match) ← NEW Tier 4
Stage 1   Scan + extract
Stage 2   Architect agent
…
```

Two kinds of recommendation can fire from Stage 0.5:

- **`route-override`** — registry says external agent X is preferred
  over local agent Y. When stage N would invoke Y, substitute X. The
  user is told inline.

- **`consider-using`** — external resource has a strong keyword overlap
  but doesn't directly replace anything. Surface to user as an optional
  add-on; default skip.

If discovery finds nothing, the SKILL.md logs "no strong match — run
`/curate <task>` to find one" and continues with the local pipeline.

## Initial registry (shipped 2026-05-18)

**Agents** (8 entries): pr-review-toolkit set (code-reviewer,
silent-failure-hunter, type-design-analyzer, comment-analyzer,
pr-test-analyzer, code-simplifier), plus Plan and Explore.

**Skills** (1 entry): claude-code-guide for "how do I" questions.

**MCP servers** (4 entries): chrome-devtools (UI / lighthouse / perf),
gmail, supabase, vercel. Listed as pointers — they only activate if the
user has connected them in Claude Code.

Two of the 8 agents have `preferred_over_local` set:

- `pr-test-analyzer` is preferred over our local `critic` for **PR
  review tests** (coverage analysis is its specialty; our critic runs
  pytest, which is different).
- `Plan` (builtin) is preferred over our local `architect` for **light
  pre-spec scoping conversations**. Our architect produces the full
  spec.json; Plan is lighter weight for "what would the design look like."

## How to grow the registry

```bash
# Discover what we currently have for a task
python skills/one-shot-generator/scripts/agent_discovery.py \
    "run lighthouse audit on UI" --json

# Find external candidates via WebSearch
/curate run lighthouse audit on UI
```

The curator skill:

1. Runs discovery to show what's already there
2. WebSearches Anthropic-trusted sources (`github.com/anthropics`,
   `awesome-claude-code-*`, `claude.com/docs`, `support.claude.com`,
   `code.claude.com`)
3. WebFetches candidate READMEs/definitions
4. Presents candidates with **strengths + risks + tools required**
5. On user approval, appends entry to the right registry file with
   `source_url`, `added_at`, `added_by: curator` provenance

The curator NEVER:

- installs MCP servers (the user does that)
- downloads and executes external code
- adds anything without explicit user approval
- replaces existing entries (manual edit required)

## Safety stance

| Concern | Mitigation |
|---|---|
| Curator adds malicious agent | Curator is a search + present + record-pointer tool. It never executes downloaded code. Invocation goes through Claude Code's normal Task tool which uses whatever the user has installed. |
| Registry gets polluted | Every entry has `added_at` + `source_url` provenance. Edit history goes through git. User approves each addition. |
| MCP server requires API keys | The curator's risk column flags this. The plugin never stores credentials. |
| Recommendations become noise | `min_score=0.30` threshold + `--limit` cap on `agent_discovery.py`. The SKILL.md surfaces only `route-override` (high-confidence) and `consider-using` (which user can dismiss). |

## What this unlocks

The plugin learns across sessions, not just within one. After a few
curation rounds, the registry contains a known-good lineup tuned to the
user's actual workflow. The discovery layer routes each task to the best
available specialist — internal or external — without the user having
to remember every option.

That's the real definition of "agentic, world-class one-shot software
engineering": **the system finds and uses the right tool, you don't have
to.**

## Tests

`tests/test_tier4_self_extending.py` — 13 tests covering:

- Registry files are valid JSON with expected shape (3 tests)
- External dirs exist with README (1 test)
- Discovery runs end-to-end (1 test)
- Discovery surfaces external code-reviewer for review tasks
- Discovery surfaces chrome-devtools MCP for lighthouse tasks
- Discovery emits route-override recommendations correctly
- Discovery still surfaces local agents alongside external
- Curator skill exists with WebSearch/WebFetch tools
- `/curate` slash command exists with proper frontmatter
- Main SKILL.md invokes discovery at Stage 0.5
- Main SKILL.md includes curator fallback hint

All green; total plugin test suite is now 72/72.
