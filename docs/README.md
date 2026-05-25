---
type: reference
last_verified: 2026-05-25
owner: claude
---

# Documentation Index — ONE SHOT PLUGIN v1.1.0

Navigation guide to all plugin documentation. Start here to find what you need.

---

## Quick Start

| Need | Document |
|---|---|
| **First time?** | [AUDIT_ME_FIRST.md](../AUDIT_ME_FIRST.md) |
| **Plugin philosophy** | [architecture/agent-first-principle.md](architecture/agent-first-principle.md) |
| **How to run /one-shot** | [../README.md](../README.md) |
| **Commands + flags** | [../CLAUDE.md](../CLAUDE.md) |

---

## Core Architecture

### Agent-First Principle

- **[architecture/agent-first-principle.md](architecture/agent-first-principle.md)** — Why agents are first-class. How skills route to them. Why deterministic muscles stay in Python.

### Pipeline Stages

The generation pipeline evolves across versions. Start with the current version first, then explore historical tiers for deep dives.

- **[tier35-agentic.md](tier35-agentic.md)** — v1.0.0 foundation: Tier 3.5, the agentic restructure
- **[tier4-self-extending.md](tier4-self-extending.md)** — v4.0 additions: predictive failures, autonomy, multi-iteration critic
- **[tier5-observability.md](tier5-observability.md)** — OTel monitoring (WS1), docs drift (WS2), rollback (WS3), prediction (WS4), workflow orchestration (WS5)

### Historical Tier Docs (Deep Reference)

- [tier1-pipeline.md](tier1-pipeline.md) — Foundations: codebase-aware extraction
- [tier2-pipeline.md](tier2-pipeline.md) — Closed loop: critic + auto-patch
- [tier25-pipeline.md](tier25-pipeline.md) — Spec-driven multi-entity generation
- [tier3-pipeline.md](tier3-pipeline.md) — Self-improvement: curriculum, drift detection

---

## TIER A Workstreams (v1.1.0)

Five independent workstreams shipping together. Each has its own validation report.

| Workstream | Focus | Docs |
|---|---|---|
| **WS1** | Real-Time OTel Monitoring | [observability/README.md](observability/README.md), [observability/production-collector.md](observability/production-collector.md) |
| **WS2** | Docs Drift Detection | [../CHANGELOG.md](../CHANGELOG.md) (WS2 section) |
| **WS3** | Autonomous Rollback | [rollback-strategy.md](rollback-strategy.md) |
| **WS4** | Predictive Failures | [predictive-failures.md](predictive-failures.md) |
| **WS5** | awesome-ai-apps Integration | [patterns-from-awesome.md](patterns-from-awesome.md), [awesome-integration-quick-start.md](awesome-integration-quick-start.md) |

---

## Operations & Deployment

### Getting Started

- **[../README.md](../README.md)** — Full feature overview, examples, framework support
- **[LAUNCH_NARRATIVE.md](LAUNCH_NARRATIVE.md)** — Positioning and elevator pitch
- **[VALUE_PROP_ONEPAGER.md](VALUE_PROP_ONEPAGER.md)** — One-page summary for stakeholders

### Production

- **[production-deployment.md](production-deployment.md)** — 5-stage runbook: pre-flight → migration → secrets → observability → rollback
- **[observability/README.md](observability/README.md)** — Local Jaeger + Prometheus stack (docker-compose)
- **[CI_SETUP.md](CI_SETUP.md)** — Enable live E2E CI (Anthropic API key required)

### Troubleshooting

- **[../TROUBLESHOOTING.md](../TROUBLESHOOTING.md)** — Common issues + fixes
- **[predictive-failures.md](predictive-failures.md)** — Understanding failure predictions
- **[rollback-strategy.md](rollback-strategy.md)** — Rollback scenarios and safety

---

## Patterns & Integration

### awesome-ai-apps Patterns

- **[patterns-from-awesome.md](patterns-from-awesome.md)** — Enterprise patterns extracted from awesome-ai-apps
- **[awesome-integration-quick-start.md](awesome-integration-quick-start.md)** — Quick start for multi-stage workflows

### MCP Integration

- **[mcp-services.md](mcp-services.md)** — Available MCP services (GitHub, Slack, etc.)
- **[mcp_github_integration_guide.md](mcp_github_integration_guide.md)** — Detailed GitHub MCP setup

### Examples

- **[cookbook.md](cookbook.md)** — Worked examples for common feature types
- **[standalone-usage.md](standalone-usage.md)** — Using the plugin without Claude Code (Cursor, CLI, GitHub Actions)

---

## Skill Development

### Authoring

- **[skill-authoring.md](skill-authoring.md)** — How to write a SKILL.md
- **[testing.md](testing.md)** — How to test skills locally
- **[../skills/CLAUDE.md](../skills/CLAUDE.md)** — Skill index and conventions

### Scripts

- **[scripts-index.md](scripts-index.md)** — All 50+ deterministic scripts listed with purpose
- **[phase-status.md](phase-status.md)** — Which phases are real vs stubs (legacy reference)

---

## Scoring & Assessment

- **[scorecard-v4.md](scorecard-v4.md)** — Honest 0–10 scoring across 36+ dimensions
- **[scorecard.md](scorecard.md)** — v1.0.0 scorecard (legacy)
- **[PATH_C_IMPLEMENTATION_SUMMARY.md](PATH_C_IMPLEMENTATION_SUMMARY.md)** — Path C (Gradient Descent) completion summary

---

## For Plugin Authors

### Setting Up Your Plugin

- **[../CLAUDE.md](../CLAUDE.md)** — Root router: quick navigation
- **[../AUDIT_ME_FIRST.md](../AUDIT_ME_FIRST.md)** — What to read in what order
- **[../CONTRIBUTING.md](../CONTRIBUTING.md)** — Code style, test policy, agent policy

### Marketplace

- **[../MARKETPLACE_SUBMISSION.md](../MARKETPLACE_SUBMISSION.md)** — Submission artifact
- **[POSITIONING.md](POSITIONING.md)** — Market positioning + differentiation

---

## Version History

- **[../CHANGELOG.md](../CHANGELOG.md)** — Full release history (v1.1.0 current)
- **[../IMPLEMENTATION_STATUS.md](../IMPLEMENTATION_STATUS.md)** — Feature status tracker

---

## What to Read When

### "I want to understand the plugin's philosophy"
1. [architecture/agent-first-principle.md](architecture/agent-first-principle.md)
2. [tier35-agentic.md](tier35-agentic.md)
3. [../AUDIT_ME_FIRST.md](../AUDIT_ME_FIRST.md)

### "I want to deploy this to production"
1. [production-deployment.md](production-deployment.md)
2. [observability/README.md](observability/README.md)
3. [../README.md](../README.md) (framework support section)

### "I want to extend it"
1. [../CONTRIBUTING.md](../CONTRIBUTING.md)
2. [skill-authoring.md](skill-authoring.md)
3. [scripts-index.md](scripts-index.md)

### "I want to integrate awesome-ai-apps patterns"
1. [patterns-from-awesome.md](patterns-from-awesome.md)
2. [awesome-integration-quick-start.md](awesome-integration-quick-start.md)
3. [mcp-services.md](mcp-services.md)

### "I want to use the CLI (not Claude Code)"
1. [standalone-usage.md](standalone-usage.md)
2. [../README.md](../README.md) (Quick Start section)

---

**Last Updated:** 2026-05-25 (v1.1.0 TIER A completion)
