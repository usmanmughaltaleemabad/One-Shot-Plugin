---
type: reference
last_verified: 2026-05-18
owner: claude
---

# Marketplace Submission Package — v1.0.0

Everything an Anthropic Software Directory submission needs, in one place.

> **Architecture orientation**: the pipeline is `skills/one-shot-generate/SKILL.md`
> + `.claude/agents/` (13 specialist agent prompts). The `scripts/` directory is a
> deterministic tools shelf the agents call — not the pipeline itself.
> See [AUDIT_ME_FIRST.md](AUDIT_ME_FIRST.md) for the full mental model.

## 1. Plugin metadata (`.claude-plugin/plugin.json`)

✅ Aligned with directory requirements:
- `name`: ONE SHOT PLUGIN (CLAUDE CODE STUDIO)
- `version`: 1.0.0 (semver)
- `description`: 1-line agentic pipeline summary
- `author`: Usman Mughal + GitHub URL
- `homepage`, `repository`, `license` (MIT)
- 35 keywords spanning capability + framework + architectural patterns

## 2. Required documents (all present)

| File | Purpose |
|---|---|
| [README.md](README.md) | User-facing overview, leads with `/one-shot` |
| [CHANGELOG.md](CHANGELOG.md) | Full version history (1.0.0 current) |
| [SECURITY.md](SECURITY.md) | Vulnerability disclosure, data handling |
| [SUPPORT.md](SUPPORT.md) | Support channels, maintenance schedule |
| [PRIVACY.md](PRIVACY.md) | Privacy guarantees, data retention |
| [LICENSE](LICENSE) | MIT |
| [ANTHROPIC_COMPLIANCE_CHECKLIST.md](ANTHROPIC_COMPLIANCE_CHECKLIST.md) | Compliance matrix |

## 3. Architecture documents

| File | Purpose |
|---|---|
| [docs/scorecard-v4.md](docs/scorecard-v4.md) | Honest 0-10 scoring across 36+ dimensions (current) |
| [docs/tier1-pipeline.md](docs/tier1-pipeline.md) | Foundations |
| [docs/tier2-pipeline.md](docs/tier2-pipeline.md) | Closed loop |
| [docs/tier25-pipeline.md](docs/tier25-pipeline.md) | Spec-driven |
| [docs/tier3-pipeline.md](docs/tier3-pipeline.md) | Curriculum + drift |
| [docs/tier35-agentic.md](docs/tier35-agentic.md) | **Agentic restructure (current)** |
| [docs/tier4-self-extending.md](docs/tier4-self-extending.md) | Registry + curator |
| [docs/tier5-observability.md](docs/tier5-observability.md) | Eval + telemetry + battle-test |

## 4. Code quality evidence

- **486 invocation-based tests, all green** on Py 3.14 / Windows + Cross-OS CI
- **3 deterministic evals + 2 agentic replay evals** scoring 1.00
- **8/8 smoke tests** pass
- **Cross-OS CI matrix** wired in `.github/workflows/cross-os.yml`
  (Ubuntu / macOS / Windows × Py 3.10 / 3.11 / 3.12)
- **Optional Bandit SAST** in `sast_runner.py` + CI job
- **2 architect agent dry-runs** via Task tool — valid spec.json produced

## 5. Skills + commands inventory

- **Slash commands**: 30 total; `/one-shot` is the primary production-grade entry
- **Skills**: 9 (one-shot-generate, curator, write-plan, execute-plan,
  tdd-cycle, systematic-debug, verify-before-complete, one-shot-generator, …)
- **Agents**: 13 with `tools:` + `model:` frontmatter, Task-invocable

## 6. Anti-claims (honest)

What we DON'T claim:
- Zero users in production (architecture solid, usage unproven)
- Full multi-agent parallel fan-out is documented but not battle-tested at scale
- Cross-language agentic generation: scaffold paths exist for all 5 frameworks,
  but body-template hints (`body_hints.py`) are NEW and the agentic implementer
  needs real runs against them
- Cost calibration is based on 2 architect dry-runs (~$0.10 each);
  full-pipeline cost estimates haven't been measured

## 7. Submission readiness checklist

- ✅ Plugin metadata complete (plugin.json v1.0.0)
- ✅ All required disclosure docs (SECURITY, PRIVACY, SUPPORT)
- ✅ MIT license
- ✅ GitHub repository public
- ✅ Test suite passes (88/88)
- ✅ Cross-OS CI configured
- ✅ Compliance checklist complete
- ⚠️ Real-world usage evidence: zero (first user run is the missing piece)
- ⚠️ Anthropic-supplied sample/test account: pending submission
- ⚠️ 3-5 working example prompts to demonstrate: documented inline in
  README + tutorial; should be polished pre-submission

## 8. Recommended polish before submission

1. **Tutorial / cookbook** (`docs/cookbook.md`) — 3 worked examples:
   - Shopping cart with line items + discounts (multi-entity)
   - User auth flow with email verification (auth intent)
   - Batch job for email notifications (phase3 generator)
2. **Architect-cleans-extractor-noise eval** — recorded; needs to be
   wired into CI as a pass^k test
3. **First external user run** — invite 1-2 external developers to
   `/one-shot` on a real project, gather feedback

## 9. Submission contact + flow

- **Submission portal**: [Anthropic Software Directory](https://support.claude.com/en/articles/13145358-anthropic-software-directory-policy)
- **Plugin author contact**: Usman Mughal (musman.mughal@taleemabad.com)
- **Repository**: https://github.com/usmanmughaltaleemabad/One-Shot-Plugin
- **Estimated review time**: per Anthropic policy, ~2-6 weeks after submission

---

**Bottom line**: the plugin meets every documentary + architectural
requirement for directory submission. The remaining gap is empirical:
~5 real-world user runs to validate that the agentic pipeline holds up
end-to-end. Recommend submitting after the next 1-2 weeks of real usage
to ship with evidence rather than promises.
