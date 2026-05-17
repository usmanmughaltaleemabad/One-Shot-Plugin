---
type: reference
last_verified: 2026-05-18
owner: claude
---

# Path to 10/10 — Per-Dimension Roadmap

For every dimension in the comprehensive scorecard, this doc gives the
**concrete steps** to move it to 10/10. Some are mechanical (build X);
some require real-world adoption (run with N users). Each entry shows:

- **Current** score
- **Why we're not at 10** in one sentence
- **Concrete steps** ordered by leverage
- **Effort** (hours / weeks / months)
- **Blocker** (none / external / empirical)

The dimensions are sorted by **investment ROI** — closest-to-shippable
first, biggest-lift-needed last.

---

## TIER A — Buildable in days (no external dependency)

### Real-Time Agent Monitoring  (4.0 → 9.0)

**Why not 10**: OTel library wired into 5 hot-paths but never tested against a real collector backend.

**Steps**:
1. Spin up local Jaeger via `docker compose -f docs/observability/docker-compose.yml up`
2. Run `OSP_OTEL_ENABLED=1 OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317 /one-shot "..."`
3. Verify spans land in Jaeger UI; capture screenshots in docs/observability/
4. Wire span context propagation across Task spawns (use `traceparent` env var)
5. Add an alerting rule example (Tempo/Honeycomb config snippet)

**Effort**: 2-3 days. **Blocker**: none.

---

### Autonomous Performance Tuning  (2.0 → 8.0)

**Why not 10**: Zero autonomous performance work today.

**Steps**:
1. Build `perf_profiler.py` — wraps each hot-path script in `cProfile`, emits per-function p50/p95 to `.beads/perf_observations.jsonl`
2. Build `perf_tuner.py` — reads observations, suggests prompt-cache key splits, batch sizes, parallelism levels
3. Integrate into `cost_budget.py`: tune Haiku vs Sonnet routing based on observed latency × accuracy per agent
4. Add `--profile` flag to `/one-shot` that captures one trace per stage

**Effort**: 1-2 weeks. **Blocker**: none for scaffolding; 10/10 needs real perf data.

---

### Autonomous Documentation Agent  (3.0 → 9.0)

**Why not 10**: No agent that watches code drift and updates docs.

**Steps**:
1. Add `.claude/agents/docs-author.md` (subagent_type for Task)
2. Hook on `Stop` that runs `codebase_diff` and detects entity changes
3. When entities added/removed/renamed, auto-spawn docs-author to update README + the affected entity's docstring
4. Generated docs land in `.tmp/docs-drift-${SHA}.md` for human review

**Effort**: 3-5 days. **Blocker**: none.

---

### Predictive Failure Detection  (5.5 → 9.0)

**Why not 10**: Curriculum lookup uses keyword Jaccard, not embeddings; no proactive "this will fail" warnings.

**Steps**:
1. Add `embedding_cache.py` — uses local sentence-transformers (optional dep, no-op fallback) to embed task descriptions
2. Replace Jaccard in `beads_curriculum.consult()` with cosine similarity over embeddings
3. Add a "predictive warnings" mode in Stage 0: when current task has >0.8 similarity to a failed bead, surface it as a hard warning + suggest the fix
4. Track prediction accuracy via the eval harness (did the predicted failure actually fire?)

**Effort**: 1 week. **Blocker**: none (optional dep, no-op fallback).

---

### Autonomous Rollback Agent  (4.0 → 9.0)

**Why not 10**: `.osp.bak` files exist; no agent observes failure and reverts.

**Steps**:
1. Add `.claude/agents/rollback.md` (subagent_type for Task)
2. Hook on `Stop`: if the last 3 generations resulted in non-shipping critic verdicts, spawn rollback to restore `.osp.bak` files
3. Wire `--rollback` flag to `/one-shot` that restores the most recent `.osp.bak`-tagged mutation
4. Add a `git_safety.py` script that runs `git stash` before `--apply` so the user has another exit

**Effort**: 3-5 days. **Blocker**: none.

---

### Self-Healing Prompts  (4.0 → 8.0)

**Why not 10**: auto_patch heals code, not prompts. self_improvement_proposer suggests SKILL.md edits but doesn't apply them.

**Steps**:
1. Add `prompt_versioner.py` — git-tracked SKILL.md history with semver tags
2. Wire `self_improvement_proposer` → produces a markdown PATCH proposal for a specific SKILL.md
3. New `/curate-prompt <pattern>` command: WebSearch for known-good prompts for the pattern; offers to splice them in
4. Cap automatic prompt changes at "propose, never apply" — same safety stance as the curator skill

**Effort**: 1 week. **Blocker**: none.

---

### Autonomy scale tracking  (3.5 → 8.0)

**Why not 10**: No formal mapping to Anthropic's 5-level autonomy taxonomy.

**Steps**:
1. Add `autonomy_level.py` — declares 5 levels (operator / collaborator / consultant / approver / observer)
2. Each level has explicit gates: operator = every action approved; observer = no gates
3. `/one-shot --level=approver` runs without gates except critical (apply, migrations)
4. Track per-user session count via `.beads/sessions.jsonl`; suggest level-up after 20+ clean sessions
5. Surface current level in every output: `[level: collaborator | next: consultant @ 8 more clean runs]`

**Effort**: 1 week. **Blocker**: none. References: [Anthropic's autonomy framework](https://www.anthropic.com/news/measuring-agent-autonomy).

---

## TIER B — Buildable in 1-3 weeks (no external dependency)

### AI Observability beyond evals  (6.5 → 9.0)

**Why not 10**: Eval harness is single-run pass@1. No pass^k production semantics. OTel wired but not battle-tested.

**Steps**:
1. Add `pass_k_runner.py` — runs each agentic eval N times, reports pass^k vs pass@k
2. Add eval flake detection (variance > 15% → mark as flaky)
3. Wire OTel into the agent dispatcher so every Task spawn produces a child span linked to the parent /one-shot trace
4. Build a Honeycomb/Tempo dashboard JSON in `docs/observability/` as a reference

**Effort**: 2 weeks. **Blocker**: none.

---

### Cross-Agent Learning Hub  (6.5 → 9.0)

**Why not 10**: Registry has 8+1+4 entries; zero usage data; no propagation between projects.

**Steps**:
1. Add `.claude/registry/learnings.jsonl` — append-only log of "this agent worked well for tasks like X"
2. Curator skill reads learnings during discovery; agents with proven history rank higher
3. Add `share-learning` command that exports anonymized learnings.jsonl for sharing
4. Document import format so users can pull learnings from a team-wide hub

**Effort**: 1-2 weeks. **Blocker**: none.

---

### Multi-agent orchestration  (6.5 → 9.0)

**Why not 10**: Architect proven via Task twice; full parallel implementer + test-author + reviewer + critic fan-out hasn't been done in this session.

**Steps**:
1. Build `agentic_session_driver.py` — a script that, given a spec.json + plan.json, drives all 6 agents in the right order from a single Claude Code session
2. Record 5 real-world fan-outs (3 fresh projects + 2 existing-codebase additions)
3. Capture per-agent token usage; recalibrate `cost_budget` with empirical p50
4. Document the timing: average wall-clock per stage, parallelism speedup

**Effort**: 2-3 weeks. **Blocker**: needs a Claude Code session (not a subprocess test).

---

### Agent Capability Marketplace  (6.0 → 9.0)

**Why not 10**: Registry is a scaffold; no ratings, no version pinning, no install flow.

**Steps**:
1. Add `rating` + `last_verified` to each registry entry; `/curate` updates `last_verified` on revalidation
2. Add `--pin-version` to registry entries (so MCP servers reference a specific SHA)
3. Build `marketplace_sync.py` — pulls a community registry from a well-known GitHub repo, dedups vs local
4. Add badge logic: agents with ≥10 successful runs in `learnings.jsonl` get a "Verified" tag

**Effort**: 2 weeks. **Blocker**: none.

---

### Zero-shot task understanding  (6.0 → 9.0)

**Why not 10**: Rule-based extractor handles clean prose; ugly multi-clause prose needs architect compensation. No multi-turn refinement layer.

**Steps**:
1. Move extraction itself to a dedicated agent (`.claude/agents/extractor.md`) for ambiguous prose
2. Add a confidence-based router: if rule-based extractor confidence ≥ 0.8, use it (free); else spawn extractor agent (~$0.05)
3. Add a "clarify-then-extract" mode for confidence < 0.4 — extractor asks ONE question, then re-extracts

**Effort**: 1-2 weeks. **Blocker**: none. (Cost increase ~$0.05 per ambiguous run.)

---

## TIER C — Empirical (requires real-world data)

### ONE SHOT PROMPTING  (6.5 → 9.0)

**Why not 10**: Architecture is solid; production runs are zero.

**Steps**:
1. Invite 5 external developers to run `/one-shot` on real projects
2. Capture every output (recorded_replays format)
3. Score against the eval harness post-hoc
4. Build a public "win" / "loss" board with anonymized examples
5. After 20+ runs across 5+ projects, recalibrate cost_budget + body_hints

**Effort**: 4-6 weeks. **Blocker**: real users.

---

### Multi-agent orchestration (production validation)  (→ 10)

Move from 9.0 → 10.0 requires the same empirical data as ONE SHOT PROMPTING + cross-OS validation:

1. CI matrix passing on Linux + macOS + Windows × 3 Python versions
2. ≥ 50 real-world fan-outs with median wall-clock < 5 minutes
3. ≥ 95% critic-loop convergence within 3 iterations
4. ≥ 90% generated tests passing on first try in the user's venv

**Blocker**: empirical.

---

### Real-world adoption / Community  (1.5 → 7.0)

**Why not 10**: Zero users. **Note**: A "10" here is unrealistic for a solo-developer plugin in its first month. A realistic ceiling is 7-8.

**Steps**:
1. Submit to Anthropic Software Directory (`MARKETPLACE_SUBMISSION.md` is ready)
2. Publish a launch post on Anthropic Discord + Hacker News
3. Build 3 polished example videos / screencasts
4. Maintain a public bug tracker; respond to every issue in <48h
5. After 100 users, write a blog post on what surprised us

**Effort**: 3-6 months. **Blocker**: external adoption.

---

## TIER D — Already at 8.5+ (polish moves them to 10)

These dimensions are essentially "shipped well." Closing the last 1-2 points is mostly **adding the missing 5% edge cases**:

### Progressive Disclosure (Context Management)  (8.5 → 10)

**Steps**: Add per-skill `index.md` files (sub-router beneath skills/CLAUDE.md). Add a `/route <topic>` command that surfaces the right doc level for a query. **Effort**: 1 day.

### Plugin-native architecture  (8.5 → 10)

**Steps**: Submit to directory + actually appear in `/plugins` listing. Wait for the listing → 9.0. Get featured / verified badge → 10. **Effort**: 1-6 months. **Blocker**: Anthropic review timeline.

### Cost-awareness  (8.0 → 10)

**Steps**: After 20+ real `<usage>` observations, `recalibrate_from_log` produces empirical p50/p95. Add per-agent SLO ("if architect > $0.20, abort"). Wire in real-time cost ticker in the SKILL.md output. **Effort**: 2 weeks once data accumulates.

### Harness / governance  (8.0 → 10)

**Steps**: Add team RBAC layer (multi-user audit trails). Add hook-result aggregation. Add settings.json schema validation. **Effort**: 2-3 weeks.

### Tested + documented  (8.5 → 10)

**Steps**: Add CI badges to README. Generate API reference from docstrings. Record short demo screencasts. **Effort**: 1 week.

### Automated Hooks  (8.0 → 10)

**Steps**: Add `PostToolUse` hook for cost-log auto-append. Add `UserPromptSubmit` hook for cost-budget pre-flight. **Effort**: 2-3 days.

### Structured Work Tracking  (8.0 → 10)

**Steps**: Add bead lifecycle states (open → in-progress → blocked → closed). Add bead dependencies (`blocked_by: [bd-xxx]`). Add `bead query` CLI for richer searching. **Effort**: 1 week.

### Existing Codebases Analysis  (8.0 → 10)

**Steps**: Add support for monorepo layouts (pnpm-workspace.yaml, turbo.json). Add cross-module dependency graph (not just per-file entities). **Effort**: 1-2 weeks.

### Software Engineering  (8.0 → 10)

**Steps**: Add CI matrix passing (Cross-OS YAML shipped today, needs to actually run green on GitHub Actions). Add mypy/pyright type checking. Add code coverage reporting. **Effort**: 1 week.

### Direction  (9.0 → 10)

**Steps**: Honestly, "10" here means consistent execution over 6+ months. Architecturally, the direction is already right; the 1.0 gap is "did we follow through?" — answered only by time. **Effort**: 6 months of sustained shipping.

---

## TIER E — Domain-specific dimensions

### AI Engineering  (7.5 → 10)

Composite of: multi-agent fan-out (Tier C empirical), prompt versioning (Tier B), eval pass^k (Tier B), real OTel (Tier A), embedding-based retrieval (Tier B Predictive). Each subdim moves AI Engineering ~0.5 closer.

**Total effort to 10**: 6-8 weeks of focused work + empirical data.

### Intelligence  (6.5 → 9.0)

Bounded by Claude's own capability. The plugin moves this score by giving Claude better inputs (codebase_graph, beads_curriculum, body_hints, registry). To improve:

1. Better extractor for ambiguous prose (Tier B Zero-Shot work)
2. Embedding-based curriculum (Tier A Predictive)
3. Multi-turn refinement (architect can ask follow-up questions)

**Effort**: 3-4 weeks.

---

## Summary roadmap

If we picked the 5 highest-ROI items to ship over the next 30 days:

| # | Item | Effort | Dimension boost |
|---|---|---|---|
| 1 | Embedding-based curriculum (Predictive Failure Detection) | 1 week | +3.5 |
| 2 | Autonomy-level mapping (operator/.../observer) | 1 week | +4.5 |
| 3 | Real Jaeger smoke-test + dashboard examples | 3 days | +5.0 (RT monitoring) |
| 4 | Multi-agent end-to-end production run (5 fan-outs) | 2 weeks | +2.5 (Multi-agent) |
| 5 | `agentic_session_driver.py` | 1 week | +1.5 across the board |

Cumulative: ~5 weeks → average score climbs from **7.1 → 8.3**.

To go from 8.3 → 9.5: requires the empirical Tier C work (real users, real adoption).

To go from 9.5 → 10 across all dimensions: realistically requires 6+ months
of sustained shipping + community + Anthropic Directory listing + verified
badge. Even then, dimensions like "Community" might cap at 8.5 for a
solo-developer plugin in its first year.

**Practical advice**: aim for **8.5 average** by end of next month. That's
both achievable and represents "world-class plugin." 10/10 across the board
is an aspirational ceiling, not a target.
