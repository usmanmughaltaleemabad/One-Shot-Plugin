---
type: checklist
version: v1.2.3
release_date: 2026-06-03
---

# Release Checklist

Reusable pre-release checklist for One-Shot Prompting. Most recently exercised for
**v1.2.3** (marketplace sync). The verification examples below reference the v1.2.0
feature baseline; adapt counts and feature names to the release in flight.

---

## Pre-Release Verification

### Code Quality
- [ ] All tests passing: `python -m pytest tests/ -q` (960+ tests, 99.79% pass rate)
- [ ] No type errors: All files have ≥96% type hint coverage
- [ ] No linting violations: `ruff check .` with zero errors
- [ ] Code formatting correct: `black --check .` with zero changes needed
- [ ] SAST scan clean: Security deep scan found zero critical issues
- [ ] Docstring coverage: ≥40% documented (fair, improvement opportunity)

### Documentation
- [ ] CLAUDE.md updated (v1.1.0 → v1.2.0, <100 lines)
- [ ] README.md updated (v1.2.0 highlights, Phase 3-4 features)
- [ ] CHANGELOG.md updated (comprehensive v1.2.0 entry)
- [ ] IMPLEMENTATION_STATUS.md updated (Phase 5 in progress)
- [ ] RELEASE_NOTES_v1.2.0.md created (this file plus features)
- [ ] RELEASE_CHECKLIST.md created (verification checklist)
- [ ] All docs/ files reviewed for accuracy
- [ ] Examples updated (ride-sharing-system README)
- [ ] Audit reports in place (Phase 4 comprehensive validation)

### Testing Checklist

#### Unit Tests
- [ ] All unit tests pass: `pytest tests/test_*.py -q`
- [ ] Phase 3 tests pass (165+): `pytest tests/test_phase3_*.py -v`
- [ ] Phase 4 audit tests pass (50+): `pytest tests/test_audit_*.py -v`
- [ ] No flaky tests: Run twice, same results both times
- [ ] No regressions: Zero test failures from v1.1.0

#### Integration Tests
- [ ] Full pipeline e2e works: `pytest tests/integration/ -q`
- [ ] Multi-agent orchestration verified: 18 agents functioning
- [ ] Skill wiring verified: 16 skills callable
- [ ] Command parsing verified: 35+ commands parse correctly
- [ ] Agent routing verified: Intent classifier routes to correct agent

#### Smoke Tests
- [ ] Smoke test suite passes: `bash .claude/scripts/smoke-test.sh`
- [ ] No errors on Windows, Linux, macOS (test on at least one)
- [ ] FastAPI example generates code: `pytest tests/test_fastapi_example.py`
- [ ] Django example generates code: `pytest tests/test_django_example.py`

#### Agentic Evaluation
- [ ] Architect agent eval passes: 14/14 replay evals ≥0.85
- [ ] Implementer agent eval passes (spot check, 3-4 samples)
- [ ] Test-author agent eval passes (spot check, 2-3 samples)
- [ ] Reviewer agent eval passes (spot check, 2-3 samples)
- [ ] Critic agent eval passes (spot check, 1-2 samples)

### Security Verification

#### SAST (Static Analysis)
- [ ] No hardcoded secrets: `rg "password|token|key|secret" --type py` = zero findings
- [ ] No SQL injection patterns: Security deep scan = zero findings
- [ ] No insecure crypto: Scan for MD5/SHA1/random-for-tokens = zero findings
- [ ] No access control bugs: RBAC patterns verified correct
- [ ] No data exposure: DEBUG=True, CORS misconfiguration scans = zero findings

#### Dynamic Analysis
- [ ] All endpoints require authentication (when needed)
- [ ] All endpoints enforce authorization (RBAC verified)
- [ ] Secrets are env-based (never hardcoded)
- [ ] Migrations are reversible (downgrade function present)
- [ ] API accepts valid input, rejects invalid input

#### Compliance
- [ ] Anthropic API key not in repo: `git log --all -S ANTHROPIC_API_KEY` = empty
- [ ] No private data in audit logs: Logs sanitized
- [ ] Privacy policy accurate: [PRIVACY.md](PRIVACY.md) matches practices
- [ ] Security.md contact email correct: musman.mughal@taleemabad.com

### Performance Verification

#### Generation Speed
- [ ] Planning time <1s: Stages 0-2 complete in <1 second
- [ ] Build time <2s: Stage 3 (parallel implementers) in <2 seconds
- [ ] Verify time <1s: Stage 4 complete in <1 second
- [ ] Review time <1s: Stage 5 complete in <1 second
- [ ] Ship time <1s: Stages 6-8 complete in <1 second
- [ ] Total wall-clock 2-3 minutes: Full pipeline completes in 2-3 min

#### Cost Control
- [ ] Budget estimates accurate: cost_budget.py estimates within 10% of actual
- [ ] Cost tracking works: .beads/cost_observations.jsonl populated
- [ ] Budget gates enforce: `--budget=0.30` halts when exceeded
- [ ] Parallel agents cost correctly: Multiple implementers sum correctly
- [ ] Haiku agents used for writers: Implementer, wirer, docs-author all haiku

#### Observability
- [ ] OTel tracing enabled: `OSP_OTEL_ENABLED=1 /one-shot "..."` produces traces
- [ ] Jaeger dashboard populates: docker-compose Jaeger shows traces
- [ ] Span attributes present: cost_usd, entities_count, intent all populated
- [ ] No trace export errors: Graceful fallback when OTLP unavailable
- [ ] Metrics available: Prometheus scraper finds metrics

### Documentation Audit

#### User-Facing Docs
- [ ] README.md is accurate: Quick start works, links valid
- [ ] QUICKSTART.md exists: (if applicable) and is current
- [ ] Troubleshooting.md covers common issues: At least 10 scenarios
- [ ] FAQ.md answers top questions: (if exists) current
- [ ] Examples are runnable: At least one full example works end-to-end

#### Developer Docs
- [ ] CONTRIBUTING.md clear: Code style, test policy, PR checklist
- [ ] ARCHITECTURE.md current: Agent-first principle documented
- [ ] Tier docs accurate: tier1-5.md match actual implementation
- [ ] Script index current: All 50+ scripts documented
- [ ] Agent definitions complete: 18 agents with roles, models, tools

#### Compliance Docs
- [ ] SECURITY.md present: Vulnerability disclosure process
- [ ] PRIVACY.md present: Data handling, retention policy
- [ ] LICENSE file present: MIT or chosen license
- [ ] CODE_OF_CONDUCT.md present: Contributor expectations
- [ ] SUPPORT.md present: Support channels, maintenance policy

### Marketplace Verification

#### Marketplace Submission
- [ ] Plugin listed in Claude Plugins Community: https://claude.com/plugins
- [ ] Marketplace README includes installation instructions
- [ ] MARKETPLACE_SYNC.md documents sync status and timeline
- [ ] Release tags created: `v4.15.1-sync-nudge`, `bump-ready/one-shot-prompting`
- [ ] GitHub issues filed: #45 (community), #2150 & #2151 (official)

#### Installation Verification
- [ ] Community marketplace: `claude plugin add one-shot-prompting` works
- [ ] Official marketplace (when approved): Plugin appears in CLI listings
- [ ] Plugin metadata current: `.claude-plugin/marketplace.json` SHA updated
- [ ] Documentation links valid: All marketplace references point to correct URLs

#### Sync Timeline
- [ ] Community sync initiated: Issue #45 filed with follow-up comments
- [ ] Official addition requested: Issues #2150 & #2151 filed with specifications
- [ ] Marketplace monitoring active: `.github/workflows/marketplace-sync-monitor.yml` configured
- [ ] Status tracking: `MARKETPLACE_SYNC.md` updated with timeline and expectations

### Git Verification

#### Commit History
- [ ] No large files committed: Max file size <50MB (ideally <10MB)
- [ ] No binary files unnecessary: Code-generation artifacts excluded
- [ ] Commit messages clear: Conventional commits format
- [ ] No merge conflicts: Clean linear history
- [ ] No incomplete commits: All WIP code is done

#### Branch Status
- [ ] Current branch is `master`: `git rev-parse --abbrev-ref HEAD` = master
- [ ] Master ahead of origin: `git log origin/master..HEAD` shows commits
- [ ] All Phase 3-4 work committed: `git status` shows no changes
- [ ] No uncommitted files: `git status --porcelain` = empty
- [ ] No untracked files (except .gitignored): `git ls-files --others --exclude-standard` = minimal

#### Tag Readiness
- [ ] Tag name format correct: `v1.2.0` (no v prefix optional)
- [ ] Tag message descriptive: Includes features, audit score, go-live verdict
- [ ] Tag points to correct commit: Feature-complete, all tests passing
- [ ] Annotated tag (not lightweight): `git cat-file -t v1.2.0` = tag

---

## Testing Checklist

### Manual Testing (Smoke Tests)
- [ ] `/one-shot "add user authentication" @./examples/fastapi-*` works (dry-run)
- [ ] `/one-shot "add shopping cart" @./examples/django-*` works (dry-run)
- [ ] `/policy "max_cost_per_week: 50"` parses correctly
- [ ] `/knowledge "shopping cart pattern"` returns semantic matches
- [ ] `/routing "auth flow"` classifies intent correctly
- [ ] Error handling works: Invalid input rejected gracefully
- [ ] Help text works: `/one-shot --help` shows all flags

### Integration Testing (End-to-End)
- [ ] Full pipeline on FastAPI project: Stages 0-8 complete
- [ ] Full pipeline on Django project: Stages 0-8 complete
- [ ] Critic loop works: Handles failures, iterates (max 3), ships or escalates
- [ ] Wiring works: main.py updated correctly with --apply
- [ ] Rollback works: Failed --apply can be reversed with /rollback
- [ ] Migrations work: Alembic revisions created, reversible

### Framework Coverage
- [ ] FastAPI project tested: Code generation works correctly
- [ ] Django project tested: Code generation works correctly
- [ ] Spring Boot project tested: Code generation works correctly
- [ ] NestJS project tested: Code generation works correctly
- [ ] Go project tested: Code generation works correctly
- [ ] Node.js project tested: Code generation works correctly

### Phase 3 Feature Testing
- [ ] Policy engine enforces budget gates: --apply blocked when over budget
- [ ] Knowledge store returns semantic matches: Previous patterns suggested
- [ ] Intent routing classifies correctly: Auth → auth specialist agent
- [ ] Curriculum learns from successes: .beads/ directory populated
- [ ] Multi-stage workflow orchestrates: /multi-stage-workflow "... then ..." works

### Phase 4 Audit Validation
- [ ] Audit report generated: `audit/AUDIT_SUMMARY_2026-05-25.md` exists
- [ ] Audit score 8.3/10: All 8 dimensions scored
- [ ] Zero critical issues found: Security, performance, stability all good
- [ ] Ride-sharing example complete: 87 endpoints, 11 tables, works
- [ ] Test coverage confirmed: 960+ tests, 99.79% pass rate

---

## Documentation Checklist

### Content Review
- [ ] No typos: Spell check passes (ignore code tokens)
- [ ] No broken links: All internal links valid
- [ ] No stale content: All commands, flags, versions current
- [ ] Examples runnable: Sample commands work as documented
- [ ] Code snippets correct: Copy-paste works without modification

### Structure Review
- [ ] README flows logically: Intro → quick start → features → examples → troubleshooting
- [ ] CLAUDE.md <100 lines: Enforced via size policy
- [ ] Index completeness: All major components referenced somewhere
- [ ] Cross-references present: Related docs linked throughout
- [ ] Version consistency: All docs say v1.2.0 (not v1.1.0)

### Format Review
- [ ] YAML frontmatter present: All .md files have type, last_verified, owner
- [ ] Code blocks syntax-highlighted: ```python, ```bash, etc.
- [ ] Tables formatted correctly: Pipes align, no missing cells
- [ ] Headings hierarchical: H1 → H2 → H3, no skips
- [ ] Emphasis consistent: **bold** for UI, `code` for commands

---

## Git Commit Checklist

### Before Committing
- [ ] All tests pass: `pytest tests/ -q` = 960+ passing
- [ ] No lint errors: `ruff check .` = zero findings
- [ ] Code formatted: `black .` = no changes
- [ ] Git status clean: `git status` shows only changes below
- [ ] Changes reviewed: All modifications make sense

### Commit Message
- [ ] Title <72 characters: Conventional Commits format
- [ ] Title descriptive: Describes what changed, not how
- [ ] Body explains why: If needed, 1-3 sentence summary
- [ ] Co-author attribution: If applicable, add Co-Authored-By
- [ ] Example: `docs(v1.2.0): comprehensive documentation update for release`

### Commit Content
- [ ] Only staging relevant files: Not test artifacts, caches, .env
- [ ] Phase 3-4 docs included: governance/, learning/, routing/ + examples/
- [ ] CHANGELOG.md included: v1.2.0 entry complete
- [ ] RELEASE_NOTES included: v1.2.0 comprehensive
- [ ] Audit reports included: Phase 4 summary + results

---

## GitHub Release Checklist

### Release Creation
- [ ] Create release from tag v1.2.0
- [ ] Title: "v1.2.0: Enterprise Policy, Learning & Routing"
- [ ] Description: Copy from RELEASE_NOTES_v1.2.0.md
- [ ] Mark as latest: Check "Set as the latest release"
- [ ] Pre-release: Unchecked (production release)

### Release Assets (Optional)
- [ ] Audit report PDF: `audit/AUDIT_SUMMARY_2026-05-25.pdf` (if generated)
- [ ] Code metrics CSV: `audit/CODE_QUALITY_METRICS.csv`
- [ ] Test results: `audit/TEST_RESULTS_v1.2.0.txt`

### Release Announcement
- [ ] GitHub Releases page: v1.2.0 visible with description
- [ ] GitHub Issues: Close Phase 3-4 tickets, reference release
- [ ] GitHub Discussions: Announce new features, ask for feedback
- [ ] Community channels: Slack, Discord, email list (if applicable)

---

## Post-Release Verification

### Deployment
- [ ] Tag pushed to remote: `git push origin v1.2.0` ✓
- [ ] Master branch pushed: `git push origin master` ✓
- [ ] GitHub release published: v1.2.0 visible on GitHub ✓
- [ ] DockerHub updated: If applicable, image pushed ✓
- [ ] Package registry updated: PyPI, npm, etc. (if applicable) ✓

### Monitoring
- [ ] Monitor error logs: Check for v1.2.0 regressions
- [ ] Monitor issue tracker: Flag any bugs reports as critical
- [ ] Monitor community: Discord, Reddit, HN for feedback
- [ ] Monitor metrics: Audit score maintained or improved
- [ ] Schedule retrospective: Plan v1.3.0 improvements

### Documentation
- [ ] Update Anthropic Directory: Submit if applicable
- [ ] Update marketplace listings: Slack, GitHub Marketplace, etc.
- [ ] Update examples in README: Link to ride-sharing example
- [ ] Update blog/changelog: External visibility
- [ ] Prepare case study: Document real-world success story

---

## Final Sign-Off

**Release Manager Verification**
- [ ] All checklists complete: All items checked ✓
- [ ] No blockers remaining: All critical issues resolved ✓
- [ ] Quality gates passed: Audit score 8.3/10 ✓
- [ ] Team approval obtained: At least one review ✓
- [ ] Ready for production: Sign-off confirmed ✓

**Sign-off:**
- Manager: _________________________  Date: _______
- Auditor: _________________________  Date: _______
- Author: __________________________  Date: _______

---

## Version History

| Version | Date | Status | Notes |
|---|---|---|---|
| 1.2.3 | 2026-06-03 | ✅ RELEASED | Marketplace sync: version bump, strict-clean manifest, network disclosure |
| 1.2.2 | 2026-05-25 | ✅ RELEASED | Audit response: deletions + corrections, no new features |
| 1.2.1 | 2026-05-25 | ✅ RELEASED | README gap closure (ride-sharing code, replay evals) |
| 1.2.0 | 2026-05-25 | ✅ RELEASED | Enterprise governance, learning, routing + Phase 4 audit |
| 1.1.0 | 2026-05-25 | ✅ SHIPPED | TIER A Workstreams (WS1-5) |
| 1.0.0 | 2026-05-19 | ✅ SHIPPED | First public release (v4.15 reset) |

---

**Release Date**: 2026-05-25  
**Audit Score**: 8.3/10  
**Test Pass Rate**: 99.79%  
**Status**: ✅ PRODUCTION READY
