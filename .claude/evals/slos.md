---
type: reference
last_verified: 2026-05-21
owner: usman
---

# Service-Level Objectives (SLOs)

6 measurable targets for plugin quality. These drive evaluation harness and product credibility.

## SLO 1: Routing Quality ≥95%

**Definition:** Correct agent is selected on first attempt.

**How Measured:**
- For each eval task, did the router choose the right agent?
- Count: correct_choices / total_tasks

**Target:** ≥95% of tasks routed to correct agent
**Baseline:** TBD (run eval to establish)
**Alert Threshold:** <92% (early warning)

**Why it matters:** If routing fails, entire generation fails. This is the gating metric.

---

## SLO 2: Cost per Generation ≤$0.50

**Definition:** Average API cost per feature generation (free tier target: ≤$0.30).

**How Measured:**
- Sum all API calls per generation (claude calls, embedding calls, external API calls)
- Average across all eval tasks

**Target:** ≤$0.50 per generation
**Free tier target:** ≤$0.30
**Baseline:** TBD (run eval to establish)
**Alert Threshold:** >$0.60 (cost creep)

**Why it matters:** Cost is a barrier to adoption. Transparent pricing builds trust.

---

## SLO 3: Test Pass Rate ≥90%

**Definition:** Generated code's tests pass without manual fixes.

**How Measured:**
- For each eval task, run generated tests
- Count: passing_tests / total_tests

**Target:** ≥90% of generated tests pass
**Baseline:** TBD
**Alert Threshold:** <85%

**Why it matters:** Quality proof. "94% of generated code works immediately" is a powerful claim.

---

## SLO 4: Code Quality Score ≥80/100

**Definition:** Composite score of cyclomatic complexity, type coverage, and style.

**Formula:**
```
quality_score = (
    100 * (1 - min(cyclomatic_complexity / 10, 1)) +  # Lower complexity is better
    100 * (type_coverage / 100) +                      # % of code with type hints
    100 * (1 - lint_violations / total_lines * 100)   # % of lines with no lint issues
) / 3
```

**How Measured:**
- Run pylint, mypy, flake8 on generated code
- Calculate average across all eval tasks

**Target:** ≥80/100
**Baseline:** TBD
**Alert Threshold:** <75/100

**Why it matters:** Code quality is maintainability. Developers trust generated code if it's clean.

---

## SLO 5: Security Compliance 100%

**Definition:** Zero critical security vulnerabilities.

**How Measured:**
- Run bandit (Python) or semgrep (multi-language)
- Count critical/high issues
- Target: 0

**Security Issues Tracked:**
- SQL injection (critical)
- Hardcoded secrets (critical)
- Insecure deserialization (high)
- XXE vulnerabilities (high)

**Target:** 0 critical/high issues
**Baseline:** TBD
**Alert Threshold:** ≥1 critical issue (failure)

**Why it matters:** Enterprise trust. "100% security compliance" is a compliance requirement.

---

## SLO 6: User Activation Time ≤3 Hops

**Definition:** Steps from "I want a feature" to "feature is live".

**Hops:**
1. Read problem statement
2. Run `/one-shot "<feature>" @./project`
3. Review generated code
4. Apply to codebase (--apply flag)
5. Run tests (smoke test)
6. Commit to Git

**Target:** ≤3 hops for 80% of users
- Hop 1-2: Generation happens automatically
- Hop 3: Review (combined with Apply)
- Total: 3 hops

**How Measured:**
- User study: time from prompt to commit
- Track in eval harness: generation_time + apply_time + test_time

**Target:** ≤5 minutes end-to-end
**Baseline:** TBD
**Alert Threshold:** >8 minutes (slowdown detected)

**Why it matters:** Developer velocity. If it takes longer than manual, nobody uses it.

---

## SLO Summary Table

| SLO | Metric | Target | Free Tier | Alert |
|---|---|---|---|---|
| **Routing** | % correct first-hop | ≥95% | N/A | <92% |
| **Cost** | $ per generation | ≤$0.50 | ≤$0.30 | >$0.60 |
| **Tests** | % tests passing | ≥90% | N/A | <85% |
| **Quality** | Code quality score | ≥80/100 | N/A | <75 |
| **Security** | Critical vulns | 0 | 0 | ≥1 |
| **Speed** | Minutes (full flow) | ≤5 min | ≤5 min | >8 min |
