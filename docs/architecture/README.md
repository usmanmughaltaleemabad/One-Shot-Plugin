---
type: guide
last_verified: 2026-05-25
owner: claude
---

# Architecture Index

Comprehensive guides to the one-shot-prompting plugin architecture, principles, and design patterns.

## Core Principles

| Guide | Purpose | Audience |
|-------|---------|----------|
| **[agent-first-principle.md](./agent-first-principle.md)** | Universal rule set: All reasoning to agents, all deterministic ops to scripts | Everyone — start here |
| **[../tier35-agentic.md](../tier35-agentic.md)** | How the agentic restructure happened + why | Architects, auditors |
| **[../IMPLEMENTATION_STATUS.md](../IMPLEMENTATION_STATUS.md)** | What's built, what's planned, what's beta | PMs, integrators |

## Execution Models

| Guide | Purpose | Audience |
|-------|---------|----------|
| **[../path-to-10.md](../path-to-10.md)** | Roadmap to production (11 pillars, next tier) | Stakeholders, feature planners |
| **[../phase-status.md](../phase-status.md)** | Current phase + dependencies | Team leads, prioritization |

## Pipeline Documentation

| Stage File | Covers | Audience |
|-----------|--------|----------|
| **[../skills/one-shot-generate/SKILL.md](../../skills/one-shot-generate/SKILL.md)** | Main conducting script (dispatcher) | Everyone running a generation |
| **[../skills/one-shot-generate/stages/plan.md](../../skills/one-shot-generate/stages/plan.md)** | Stages 0–2.7 (Plan phase) | Architects, curriculum teams |
| **[../skills/one-shot-generate/stages/build.md](../../skills/one-shot-generate/stages/build.md)** | Stage 3 (Implementer + Test-Author) | Implementer agent, test authors |
| **[../skills/one-shot-generate/stages/verify.md](../../skills/one-shot-generate/stages/verify.md)** | Stages 4–5.9 (Verify phase) | Reviewers, security scanners |
| **[../skills/one-shot-generate/stages/ship.md](../../skills/one-shot-generate/stages/ship.md)** | Stages 6–8.5 (Ship phase) | Wirer, critic, curriculum |

## Agents

All agent definitions live in [.claude/agents/](../../.claude/agents/).

| Agent | Role | Model | When |
|-------|------|-------|------|
| `architect.md` | Schema + FK design | Sonnet | Stage 2 (planning) |
| `implementer.md` | File body generation | Haiku | Stage 3 (build, parallelized) |
| `test-author.md` | Test generation | Sonnet | Stage 3 (build, parallel) |
| `reviewer.md` | Security + style gate | Sonnet | Stage 5 (serial) |
| `doubter.md` | Adversarial pass | Sonnet | Stage 5.5 (serial) |
| `wirer.md` | Inject into main.py | Haiku | Stage 6 (serial) |
| `critic.md` | Test verdict + loop | Sonnet | Stage 7 (serial, max 3 iter) |
| `service-author.md` | Service/API generation | Sonnet | Stage 2.7 (when invariants exist) |
| `consistency-checker.md` | Cross-agent logic validation | Sonnet | Stage 5.7 (parallel with SAST) |
| `security-scanner.md` | SAST + dependency audit | Sonnet | Stage 5.7 (parallel) |
| `docs-author.md` | Comprehensive docs | Sonnet | Stage 2, 8 (documentation) |
| `rollback-agent.md` | Failure → revert decision | Sonnet | Stage 7+ (autonomous rollback) |
| `memory-propagator.md` | Curriculum update + learning | Sonnet | Stage 8.5 (async, non-blocking) |

## Scripts & Tools

All scripts live in [scripts/](../../scripts/).

| Category | Scripts | Purpose |
|----------|---------|---------|
| **Scanning** | `codebase_graph.py`, `extract_domain_model.py`, `curriculum_check.py` | Extract structure from code/description |
| **Verification** | `verify_syntax.py`, `contract_validator.py`, `security_deep_scan.py` | Validate correctness deterministically |
| **Patching** | `auto_patch.py`, `migrate_syntax.py` | Apply known fixes |
| **Wiring** | `auto_wirer.py`, `migration_generator.py` | Inject into existing files |
| **Cost** | `cost_budget.py`, `token_counter.py` | Token estimation + tracking |
| **Observability** | `otel_tracer.py`, `span_propagation.py` | OTel span emission |
| **Learning** | `beads_writer.py`, `curriculum_refresh.py`, `failure_detector.py` | Persist + learn from failures |

## Observability & Cost Control

| Guide | Purpose | Audience |
|-------|---------|----------|
| **[../observability/README.md](../observability/README.md)** | Observability stack overview | Ops, debuggers |
| **[../observability/span-propagation.md](../observability/span-propagation.md)** | OTel tracing architecture | Ops, telemetry teams |
| **[../observability/production-collector.md](../observability/production-collector.md)** | Jaeger/OTel in production | Production deployment |

## Workstreams & Integrations

| Workstream | Purpose | Guides |
|-----------|---------|--------|
| **WS1 — OTel** | End-to-end observability | [observability/](../observability/) |
| **WS2 — Docs Drift** | Detect stale documentation | [../LAUNCH_NARRATIVE.md](../LAUNCH_NARRATIVE.md) |
| **WS3 — Rollback** | Autonomous failure recovery | [../TROUBLESHOOTING.md](../TROUBLESHOOTING.md) |
| **WS4 — Predictive** | Failure prevention (cache) | [../predictive-failures.md](../predictive-failures.md) |
| **WS5 — awesome-ai-apps** | Community integration | [../patterns-from-awesome.md](../patterns-from-awesome.md) |

## How to Use This Index

**I want to understand the architecture:**
1. Start: [agent-first-principle.md](./agent-first-principle.md) (5–10 min read)
2. Deep dive: [../tier35-agentic.md](../tier35-agentic.md) (how we got here)
3. See it in action: [../../skills/one-shot-generate/SKILL.md](../../skills/one-shot-generate/SKILL.md)

**I'm implementing a new agent:**
1. Read: [agent-first-principle.md](./agent-first-principle.md) § Implementation Guidelines
2. Reference: Pick a similar agent from [.claude/agents/](../../.claude/agents/)
3. Handoff contract: agent-first-principle.md § Agent Dispatching Pattern

**I'm writing a deterministic script:**
1. Read: [agent-first-principle.md](./agent-first-principle.md) § Deterministic Operations
2. Template: Check existing scripts in [scripts/](../../scripts/)
3. Contract: agent-first-principle.md § Script Testing Requirements

**I'm debugging a stage failure:**
1. Find the stage: [agent-first-principle.md](./agent-first-principle.md) § 14-Stage Pipeline
2. Check the code: Stage file in [skills/one-shot-generate/stages/](../../skills/one-shot-generate/stages/)
3. View spans: [../observability/span-propagation.md](../observability/span-propagation.md)

**I'm auditing the project:**
1. Entry: [../../AUDIT_ME_FIRST.md](../../AUDIT_ME_FIRST.md)
2. Agent-first rules: [agent-first-principle.md](./agent-first-principle.md) § Common Patterns
3. Test coverage: [../../COMPREHENSIVE_HARNESS_REPORT.md](../../COMPREHENSIVE_HARNESS_REPORT.md)

---

## Quick Links

**Files & Directories:**
- Plugin router: [../../CLAUDE.md](../../CLAUDE.md)
- Main skill: [../../skills/one-shot-generate/SKILL.md](../../skills/one-shot-generate/SKILL.md)
- All agents: [../../.claude/agents/](../../.claude/agents/)
- All scripts: [../../scripts/](../../scripts/)
- Tests: [../../tests/](../../tests/)

**External Docs:**
- Release notes: [../../CHANGELOG.md](../../CHANGELOG.md)
- Implementation status: [../../IMPLEMENTATION_STATUS.md](../../IMPLEMENTATION_STATUS.md)
- Troubleshooting: [../../TROUBLESHOOTING.md](../../TROUBLESHOOTING.md)

---

**Last Updated:** 2026-05-25  
**Type:** guide  
**Owner:** claude
