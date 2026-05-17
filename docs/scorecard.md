---
type: reference
last_verified: 2026-05-18
owner: claude
---

# Plugin Scorecard — v3.5.0

Honest scoring against the dimensions Anthropic publicly emphasises for
production-grade agentic systems. Each dimension lists what we have,
what we don't, and a 0–10 score with rationale.

---

## Overall: **6.7 / 10**

Strong foundation; substantial gaps in real-world validation, observability
depth, and true autonomy.

| Dimension | Score | Δ since v2.0 |
|---|---|---|
| Harness / governance | 8.0 | +3.0 |
| Multi-agent orchestration | 6.5 | +5.0 (was 1.5 — agents were doc-only) |
| AI observability beyond evals | 5.0 | +2.5 |
| Zero-shot task understanding | 5.5 | +3.0 |
| Autonomy / closed-loop | 6.5 | +4.0 |
| Code quality + safety | 7.5 | +2.0 |
| Cost-awareness | 7.0 | +7.0 (didn't exist in v2) |
| Self-improvement | 5.5 | +5.0 (didn't exist in v2) |
| Tested + documented | 8.0 | +3.0 |
| Plugin-native architecture | 8.5 | +6.5 (was script-pile) |
| **Weighted average** | **6.7** | **+4.0** |

---

## 1. Harness / governance — **8.0 / 10**

**Have:**
- ✅ `.claude/settings.json` + `.claude/hooks/` (PreToolUse, Stop hooks)
- ✅ Standards directory (`.claude/standards/`) — doc-type taxonomy,
  invocation policy, retrieval policy, metadata contract
- ✅ Beads system (`status.jsonl`, `decisions.jsonl`, `failures.jsonl`)
- ✅ Smoke test (8 checks: scripts present, frontmatter, version
  consistency, CLAUDE.md size, beads, settings, hooks)
- ✅ Skill authoring + publishing docs

**Don't have:**
- ❌ Real-time linting hook (the validate-after-write hook is basic)
- ❌ Per-session telemetry dashboard
- ❌ Cross-team governance (multi-user RBAC, audit trails for shared use)

**Why 8.0:** the governance layer is genuinely strong for a single-user
plugin. To get to 10 you'd need team-shared policy enforcement.

---

## 2. Multi-agent orchestration — **6.5 / 10**

**Have:**
- ✅ 8 agents (`.claude/agents/*.md`) with explicit `tools:` + `model:`
- ✅ Cost-aware routing (Haiku for file-writers, Sonnet for reasoners)
- ✅ Explicit handoff contracts in each agent (what they read, what they
  emit, what they refuse)
- ✅ Independent test-author from implementer (separation defends
  against test/router contract drift)
- ✅ Critic loop with max 3 iterations + bead recording
- ✅ Architect dry-run via Task tool produced valid spec.json (~$0.10, 55s)

**Don't have:**
- ❌ Real production runs at the full parallel fan-out (one implementer
  per file × N entities in parallel — proven as a pattern, not at scale)
- ❌ Inter-agent retry/escalation with state shared in `.tmp/`
- ❌ Agent-specific telemetry (per-agent error rates, average iterations,
  cost-per-task histograms)

**Why 6.5:** structure is right; first dry-run worked. What's missing is
20-30 real runs and the operational hardening that comes from them.

---

## 3. AI observability beyond evals — **5.0 / 10**

**Have:**
- ✅ Beads as append-only failure log
- ✅ Curriculum lookup (past failures matching current task surface to
  the agent before generation)
- ✅ Cost estimator (`cost_budget.py`) with per-agent breakdown
- ✅ Self-improvement proposer (analyses failures.jsonl for recurring
  patterns ≥ 3×, emits markdown proposal)
- ✅ Verification diagnostics structured as Diagnostic dataclass with
  severity, code, file:line

**Don't have:**
- ❌ Real-time traces (no OpenTelemetry, no distributed tracing across
  Task spawns)
- ❌ Token-usage histogram per agent type
- ❌ Latency percentiles (p50/p95/p99 per stage)
- ❌ Quality scores beyond pass/fail (no LLM-as-judge of generated code)
- ❌ Eval suite of known-good vs generated outputs

**Why 5.0:** there's structured logging and replay support, but no
operational dashboards or eval harness. Moving from "logged" to
"observed" requires real telemetry plumbing.

---

## 4. Zero-shot task understanding — **5.5 / 10**

**Have:**
- ✅ Multi-entity NER from free text (`extract_domain_model.py`)
- ✅ Relationship inference (`has_many`, `belongs_to`, `many_to_many`)
- ✅ Intent classification (api / batch / auth / realtime / refactor)
- ✅ Confidence score with clarification gate at < 0.55
- ✅ Domain-specific attribute hints (cart → user_id/status/total)
- ✅ Codebase reconciliation (won't generate Product if it already exists)

**Don't have:**
- ❌ True semantic understanding — still rule-based (Jaccard, regex,
  stop-words). "Add anomaly-aware fraud scoring with sliding-window
  baselines" would extract "anomaly" or "fraud" but miss the temporal +
  statistical structure entirely
- ❌ Multi-turn refinement (Claude could refine via the architect agent,
  but that's not a separate "understanding" layer yet)
- ❌ Domain ontology learning (the entity hints are hardcoded in
  `_default_attributes_for`)

**Why 5.5:** dramatically better than v2 (where "shopping cart with line
items" extracted just "shopping"). But still nowhere near LLM-level
semantic depth. The honest path to 8+ is to delegate the "what does the
user mean" step to Claude inside the architect agent, not the Python
extractor.

---

## 5. Autonomy / closed-loop — **6.5 / 10**

**Have:**
- ✅ generate → verify → auto-patch → re-verify in `generate_and_verify`
- ✅ Auto-patch deterministically fixes 4 known bug classes (P1-P4)
- ✅ Critic loop with N-iteration cap (`run_critic_loop.py`)
- ✅ Failure routing (critic_runner emits "this failure belongs to
  test-author / implementer / architect")
- ✅ Beads recorded on escalation, curriculum surfaces them next time
- ✅ Clarification gate (halt on low confidence, ask one question)

**Don't have:**
- ❌ Full agentic regeneration loop wired in SKILL.md (the playbook
  describes "respec and re-spawn" but the prompt structure for re-spawn
  on partial failure is ambiguous)
- ❌ Long-running task resumption (no checkpoint/restart across sessions)
- ❌ Self-directed exploration (agent doesn't say "I'm uncertain about
  X, let me try Y first")

**Why 6.5:** the loop is real and the routing is real, but the
agent-driven regeneration (vs deterministic regeneration) is the next
unlock. Bucket D.1 addresses this.

---

## 6. Code quality + safety — **7.5 / 10**

**Have:**
- ✅ Static verifier flags syntax errors, template leaks, contract drift
- ✅ Reviewer agent (security/perf/style) before wire stage
- ✅ Cross-feature consistency checker (naming/schema/error/pagination/imports)
- ✅ Generated tests written independently of implementation
- ✅ `--apply` is opt-in; default is dry-run with `.osp.bak` backup
- ✅ No hardcoded secrets in generated code (P4 rewrites default imports)

**Don't have:**
- ❌ SAST integration (no Bandit/Semgrep as part of the pipeline,
  although `auto_patch` has primitive secret-detection patterns)
- ❌ Mutation testing of generated code
- ❌ Property-based test generation (only example-based via templates)

**Why 7.5:** safety practices are sound for a code generator;
production-grade code review would need real static analysis tooling
integrated.

---

## 7. Cost-awareness — **7.0 / 10**

**Have:**
- ✅ Per-agent token estimates in `cost_budget.py`
- ✅ Conservative pricing snapshot (Haiku/Sonnet/Opus)
- ✅ `--budget=USD` gate halts before spawn if estimate exceeds budget
- ✅ Tier-routed models (Haiku for file-writers — ~5× cost reduction
  versus pure-Sonnet)
- ✅ Prompt-caching strategy documented (spec.json + scanner output
  reused across agents)
- ✅ One empirical data point: architect dry-run cost $0.10, matched
  estimate

**Don't have:**
- ❌ Cache-hit rate measurement (we recommend caching; we don't track it)
- ❌ Cost per resolved-task (USD per shipped feature, including retries)
- ❌ Budget enforcement at the agent level (a runaway implementer
  agent can't be killed mid-spawn)

**Why 7.0:** has cost-awareness as a first-class concern, which most
plugins lack. Calibration and runtime enforcement are the gaps.

---

## 8. Self-improvement — **5.5 / 10**

**Have:**
- ✅ Beads system records failures with structured diagnostics
- ✅ Self-improvement proposer (≥ 3 occurrences → markdown proposal)
- ✅ Auto-patch encodes "fixes that worked in the past" as rules
- ✅ Curriculum surfaces past failures to current task

**Don't have:**
- ❌ Automatic rule extraction (when a bug is fixed manually, no
  mechanism extracts the fix as a new auto_patch rule)
- ❌ A/B testing of prompt variations
- ❌ Reward signal beyond binary pass/fail
- ❌ Self-extending agent/skill discovery (proposed in Tier 4)

**Why 5.5:** the substrate is there (logged failures + curriculum); the
loop that turns failures into NEW rules / NEW agents / NEW prompts is
manual today. Tier 4 closes part of this gap.

---

## 9. Tested + documented — **8.0 / 10**

**Have:**
- ✅ 59 invocation-based tests, all green on Py 3.14 / Windows
- ✅ 4 tier suites + 1 integration fixture suite
- ✅ Per-tier reference docs (tier1, 2, 25, 3, 35)
- ✅ Validation report documenting 8 real bugs caught by real-use testing
- ✅ Agent dry-run report
- ✅ CHANGELOG covering Tier 1 → 3.5

**Don't have:**
- ❌ Integration test of the full agentic flow (not just dry-runs)
- ❌ Cross-OS CI (Windows + Linux + macOS)
- ❌ User-facing tutorial videos / cookbook
- ❌ Versioned API stability commitments

**Why 8.0:** for a plugin this size, the test/doc coverage is strong.
The remaining gaps are operational (CI matrix) not architectural.

---

## 10. Plugin-native architecture — **8.5 / 10**

**Have:**
- ✅ Real slash command (`/one-shot`) with proper Claude Code frontmatter
- ✅ Skills as the primary unit (Claude reads SKILL.md and acts)
- ✅ Agents invocable via Task tool (proven via dry-run)
- ✅ Deterministic services as scripts the agents call
- ✅ Hooks + settings + standards under `.claude/`
- ✅ Plugin manifest (`.claude-plugin/plugin.json`) with version + tools

**Don't have:**
- ❌ MCP server integration (no external resources exposed via MCP)
- ❌ Skill discovery via Anthropic's plugin registry
- ❌ External skill/agent import mechanism (Tier 4 work)

**Why 8.5:** the plugin matches what Claude Code expects in nearly
every dimension. MCP + registry integration is the next ceiling.

---

## What to invest in next (ranked by ROI)

1. **Real-world runs**. The single highest-leverage thing is 5-10 real
   `/one-shot` invocations in different projects. Everything else
   improves with empirical data.
2. **Agent-driven regeneration loop** (Bucket D.1). Today the critic
   reroutes to the test-author via deterministic mapping; the agentic
   version where the critic explains the failure and the implementer
   regenerates is the next quality unlock.
3. **Self-extending discovery layer** (Tier 4). External MCP + agent
   registry + curator skill. Turns the plugin into a system that
   improves itself across tasks instead of within a single task.
4. **Eval harness** (closes Observability gap). Known-good fixtures +
   regression tests against generated output. Without this, "did the
   change make things better?" stays subjective.
5. **Cross-language scaffold variants** (Bucket D.2). Removes the
   FastAPI-only constraint on the agentic path.

Items 2 and 5 are covered by Bucket D in this commit. Item 3 is Tier 4.
