# Closing All README Gaps — v1.2.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development.

**Goal:** Close all 6 "Known gaps" from README, consolidate external folders (ay-framework, nanoGPT), integrate pi.dev patterns, update all docs.

**Architecture:** 5-phase execution. Plugin is already at v1.2.0 internally; README "Known gaps" section is stale and references v1.0.0. Many gaps are partially addressed; this plan completes and documents them honestly.

**Tech Stack:** Python 3.14, pytest, JSONL, GitHub Actions, pi.dev research (WebFetch).

---

## Actual State (as of 2026-05-25)

- **plugin.json version:** 1.1.0
- **CLAUDE.md version:** 1.2.0 (internal inconsistency to reconcile)
- **README version:** 1.2.0 in header, but "Known gaps" section labeled v1.0.0
- **Tests:** 960+ tests (99.79% pass rate per CLAUDE.md)
- **Existing replays:** 14 scenarios across 7 agent types (architect=6, others=1-2 each)
- **Untracked at parent repo root:** `ay-framework/`, `nanoGPT/`

## Phases

1. **Phase 1:** Expand replay eval coverage (add 3-4 more scenarios per non-architect agent → ~28 total)
2. **Phase 2:** Cost tracking framework + self-learning loop documentation
3. **Phase 3:** Audit/reclassify experimental commands + consolidate external folders
4. **Phase 4:** pi.dev research + integration of relevant patterns/packages
5. **Phase 5:** Update README/CHANGELOG/docs, bump to v1.2.1, tag, push

See git log for execution.
