---
type: strategy
last_verified: 2026-05-17
owner: claude
---

# TIER 2 Execution Plan: ONE SHOT PLUGIN (Claude Code Studio)

## Strategic Vision

**Objective**: Own the Claude Code team governance + code generation market completely.

**Timeline**: 24 months (Months 0-24)  
**Market**: $50-200M TAM (unopposed)  
**Target**: $50-100M ARR by Month 24, $300-600M exit value

---

## Why TIER 2 (NOT Tier 3)

**Tier 2 = Harness + Code-Gen (Recommended)**
- Competition: ZERO
- Margins: 75-80%
- Market clarity: Very high (Claude Code developers)
- Time to dominance: 6-12 months
- Exit value: $300-600M

**Tier 3 = Full SDLC Orchestration (Deferred)**
- Competition: Anthropic, CrewAI, 20+ startups
- Margins: 30-50% (under pressure)
- Market clarity: Low (which problem are we solving?)
- Time to relevance: 18-24 months
- Exit value: $300-600M (risky, most likely $50-150M)

**Decision**: Build Tier 2 excellently. Tier 3 only if:
- Anthropic hasn't launched orchestration features by Month 12
- You've hit $10M+ ARR
- Separate team/funding
- Market still belongs to you

---

## Phase 1: Harness Solidification (Months 0-3)

### Goal
Make .claude/ the de facto standard for Claude Code team governance. Every Claude Code team should have a harness.

### What Ships

**1. Harness Documentation Suite**
- `.claude/HARNESS.md` — Complete harness specification
- `.claude/standards/` — 4 standards documents (governance framework)
- `.claude/examples/` — 5-6 production harness examples
- Harness best practices guide (when to use hooks, beads, agents)

**2. Harness Initialization System**
- `harness init` command (scaffolds .claude/ in new projects)
- Template system (Django, FastAPI, Spring, Go, Node templates)
- Validation (check harness is well-formed)
- Migration tool (convert existing CLAUDE.md to harness)

**3. Reference Implementations**
- Django + DRF harness (models, views, tests)
- FastAPI + SQLAlchemy harness (async, migrations)
- Spring Boot harness (maven, testing)
- Go + Chi harness (stdlib patterns)
- Node + Express harness (middleware, error handling)

**4. Public Agent Library**
- 20+ pre-built agents for harness
- Agents for: code review, testing, documentation, security, performance
- Each agent: documented, tested, ready to import

### Metrics (Month 3)
- [ ] 1,000+ public GitHub repos with .claude/ harness
- [ ] 100+ community agents published
- [ ] 50+ reference harnesses from teams
- [ ] Harness CLI downloaded 50k+ times
- [ ] Harness Discord community: 5k+ members

### Owner
You (primary focus)

### Critical Path
1. `.claude/HARNESS.md` — official specification
2. `harness init` — scaffolding tool
3. 5 reference harnesses — proof it works
4. Agent library (20 agents) — ecosystem foundation

---

## Phase 2: Harness + One-Shot Integration (Months 3-6)

### Goal
Make ONE SHOT PLUGIN the default code generation tool for harness users. Tight integration: harness tracks context, one-shot respects it.

### What Ships

**1. Framework-Aware Code Generation**
- One-shot reads existing harness (framework, patterns, conventions)
- Generates code that matches harness standards
- Output: SKILL.md files, not just raw code
- Auto-wiring: generated code fits perfectly into project

**2. Harness-Optimized Modules**
- All 177 one-shot modules re-validated for harness integration
- Framework-specific harnesses provide context
- Code generation is 2x faster because it has harness context

**3. Feedback Loop**
- Harness tracks what code patterns work
- One-shot learns from successful patterns
- Continuous improvement: each generation is better

**4. Pre-Built Example Projects**
- Django order service (with harness)
- FastAPI payment API (with harness)
- Spring Boot microservice (with harness)
- Go trading bot (with harness)
- Node real-time app (with harness)

### Metrics (Month 6)
- [ ] 10k-50k active one-shot users
- [ ] 50+ enterprise teams using harness + one-shot
- [ ] Average code generation time: 2-5 minutes
- [ ] User satisfaction: 4.5+ / 5.0
- [ ] $500k-1M ARR (early monetization)

### Owner
You (primary focus)

### Critical Path
1. Framework detection reading harness
2. Code generation respecting harness standards
3. Pre-built example projects (5 frameworks)
4. Documentation (how to use harness + one-shot together)

---

## Phase 3: Marketplace & Ecosystem (Months 6-12)

### Goal
Build network effects through agent/skill marketplace. Teams create → other teams discover → ecosystem grows → harness stickier.

### What Ships

**1. Agent Marketplace**
- Public marketplace (web + CLI)
- Agents: discovery, ratings, reviews
- Skills: framework-specific extensions
- Private hosting: teams can publish private agents

**2. Monetization v1**
- Freemium: Core harness + one-shot free
- Paid tier ($15-25/mo): Unlimited agents, private hosting, team management
- Enterprise ($5-50k/mo): SAML, custom SLA, compliance

**3. Ecosystem Growth**
- Revenue sharing (70% to creators, 30% to platform)
- Featured agents program
- Bounty program (fund development of critical agents)

**4. Team Management**
- Role-based access (admin, member, viewer)
- Team settings (which agents are allowed, private vs public)
- Audit logs (who generated what code)

### Metrics (Month 12)
- [ ] 500+ published agents/skills
- [ ] 50-100k paying teams ($15-25/mo)
- [ ] $2-5M ARR
- [ ] Net MRR growth: 10-15%/month
- [ ] Marketplace marketplace revenue: $500k/month (commission)

### Owner
You (primary) + 1 contractor (marketplace backend)

### Critical Path
1. Marketplace platform (web interface)
2. Payment processing (Stripe)
3. CLI integration (install agents from CLI)
4. Featured agents program (get creators to publish)

---

## Phase 4: Enterprise Motion (Months 12-18)

### Goal
Capture enterprise spending. Tech directors and engineering leaders need governance + audit.

### What Ships

**1. Enterprise Features**
- SAML/OAuth (single sign-on)
- Team management (permissions, audit logs)
- Compliance reporting (SOC2 audit trail, GDPR evidence)
- Premium agents (Anthropic-certified, security-hardened)

**2. SaaS Platform**
- Claude Code Studio dashboard (web app)
- Admin panel (manage teams, permissions, billing)
- Usage analytics (which agents, which patterns)
- Audit logs (who generated what, when, where)

**3. Compliance Package**
- SOC2 audit trails for generated code
- GDPR data handling (no PII in logs)
- HIPAA-compliant patterns (pre-built)
- Compliance reporting (automated evidence collection)

**4. Enterprise Support**
- Dedicated success manager (50+ seat teams)
- Custom SLA
- Priority support (1-hour response)
- Quarterly business reviews

### Metrics (Month 18)
- [ ] 50-150k paying teams ($15-25/mo)
- [ ] 100-200 enterprise contracts ($5-50k/mo)
- [ ] $20-50M ARR
- [ ] Gross margin: 75-80%
- [ ] Enterprise NPS: 50+

### Owner
You (product/strategy) + 2-3 contractors (SaaS platform, compliance)

### Critical Path
1. SaaS platform (basic version)
2. SAML/OAuth integration
3. Audit logging infrastructure
4. Enterprise sales outreach (50+ target accounts)

---

## Phase 5: Optimize & Scale (Months 18-24)

### Goal
Solidify market dominance. Become the default harness + code-gen platform for Claude Code teams.

### What Ships

**1. AI-Assisted Harness Optimization**
- Analyze your harness, suggest improvements
- "You're not using agent X, but Y teams with similar setup do"
- "Consider adding hook Z for your workflow"
- Continuous improvement feedback loop

**2. A/B Testing Framework**
- Test agent variations (compare results)
- Test skill variations (see which patterns work best)
- Statistical significance (which version is better?)

**3. Performance Analytics**
- Which patterns work best in your codebase?
- Generate time: fast/slow patterns
- Code quality: which agents produce highest quality?
- Team insights: who's using what agents?

**4. Integrations**
- GitHub: auto-sync harness config
- GitLab: same as GitHub
- Slack: notifications when generation completes
- Linear: link generated code to issues
- Jira: same as Linear

### Metrics (Month 24)
- [ ] 50-150k paying teams
- [ ] 200-500 enterprise contracts
- [ ] $50-100M ARR
- [ ] YoY growth: 150-200%
- [ ] Market dominance: 60-70% of Claude Code governance market

### Owner
You (product/strategy) + 3-5 contractors (platform, integrations)

### Critical Path
1. Performance analytics infrastructure
2. GitHub/GitLab integration
3. Slack/Linear integration
4. AI-assisted optimization (basic version)

---

## Revenue Roadmap

| Phase | Timeline | ARR | Customer Count | Key Milestone |
|-------|----------|-----|---|---|
| **1** | Months 0-3 | $0 | 0 paying | Free harness users: 1k |
| **2** | Months 3-6 | $500k-1M | 5-10k teams | One-shot integration shipping |
| **3** | Months 6-12 | $2-5M | 50-100k teams | Marketplace launch, freemium live |
| **4** | Months 12-18 | $20-50M | 100-200 enterprise | SaaS platform live, SAML working |
| **5** | Months 18-24 | $50-100M | 200-500 enterprise | Market dominance, analytics live |

---

## Customer Segments

### Phase 1-2: Early Adopters (Months 0-6)
- Claude Code enthusiasts
- Open-source maintainers
- Small teams (5-20 people)
- GitHub-active developers

**Channels**: Twitter, GitHub, Discord, HackerNews

### Phase 2-3: Growth Segment (Months 6-12)
- Mid-size teams (20-100 people)
- Startups (Series A/B)
- Agencies using Claude Code

**Channels**: Product Hunt, word-of-mouth, content marketing

### Phase 3-5: Enterprise Segment (Months 12+)
- Tech leaders at mid/large companies
- Engineering directors
- Teams with compliance requirements

**Channels**: Sales outreach, partnerships, case studies

---

## Success Metrics (Month 24 Target)

| Metric | Target |
|--------|--------|
| Paying teams | 50-150k |
| Enterprise customers | 200-500 |
| ARR | $50-100M |
| Gross margin | 75-80% |
| Market share (Claude Code governance) | 60-70% |
| NPS (teams) | 50+ |
| NPS (enterprise) | 55+ |
| Churn (teams) | <5% |
| Churn (enterprise) | <2% |
| Agent marketplace size | 500+ agents |
| Community agents (% of marketplace) | 70% |

---

## Decision Checkpoints

### Month 3 (End of Phase 1)
**Question**: Is harness becoming the standard?  
**Decision gate**: 
- ✅ YES → Continue to Phase 2
- ❌ NO → Pivot harness strategy (rethink messaging/approach)

### Month 6 (End of Phase 2)
**Question**: Is one-shot + harness adoption growing?  
**Decision gate**:
- ✅ YES ($500k-1M ARR, 10-50k users) → Continue to Phase 3
- ❌ NO → Reassess integration strategy

### Month 12 (End of Phase 3)
**Question**: Is marketplace sustainable? Is enterprise segment emerging?  
**Decision gate**:
- ✅ YES ($2-5M ARR, 50-100k teams) → Continue to Phase 4 (enterprise)
- ❌ NO → Focus deeper on marketplace (don't go enterprise yet)

### Month 18 (End of Phase 4)
**Question**: Have we won the market or is Anthropic competing?  
**Decision gate**:
- ✅ YES ($20-50M ARR, market is ours) → Optional: Begin Tier 3 planning (separate team)
- ❌ NO (Anthropic competing, margins pressure) → Stay focused on Tier 2, skip Tier 3

---

## What Tier 3 Looks Like (If Applicable)

**Only consider Tier 3 if:**
- Month 18 ARR > $10M
- Anthropic hasn't launched competing features
- You have clear market dominance in Tier 2
- Separate team/funding available

**Tier 3 = New Product ("Maestro AI")**
- Full SDLC orchestration (requirements → deploy → monitor)
- Separate branding (not "Claude Code Studio")
- Separate team (don't cannibalize Tier 2)
- Separate go-to-market

**Tier 3 Success Metrics:**
- Year 1: $5-10M ARR
- Year 2: $20-50M ARR
- Year 3+: $50-100M ARR

---

## Critical Success Factors

1. **Harness must become standard** (Month 3-6)
   - If not, entire strategy fails
   - Be relentless about getting developers to adopt .claude/

2. **One-shot integration must be seamless** (Month 3-6)
   - Code generation must feel native to harness
   - If it feels tacked-on, users won't use it

3. **Marketplace must have network effects** (Month 6-12)
   - Agents must be easy to discover
   - Agents must solve real problems
   - Revenue-sharing must be attractive to creators

4. **Enterprise motion must be distinct** (Month 12-18)
   - Enterprise buyers need different messaging
   - Compliance/governance is their concern
   - Sales motion must match their buying process

5. **Market must stay yours** (ongoing)
   - If Anthropic launches competing features, you lose
   - Defend by: better UX, stronger ecosystem, tighter harness integration
   - If you lose harness market share, exit becomes much smaller

---

## Monthly Milestones

### Months 0-3 (Phase 1)
- Month 1: Harness spec + init tool
- Month 2: 5 reference harnesses + 10 agents
- Month 3: Harness CLI public release, 1k+ GitHub harnesses

### Months 3-6 (Phase 2)
- Month 4: Framework detection reading harness
- Month 5: One-shot + harness integration shipping
- Month 6: 5 example projects, 10k-50k one-shot users

### Months 6-12 (Phase 3)
- Month 7: Marketplace web + CLI
- Month 8: Payment processing live (freemium)
- Month 9: 100+ published agents
- Month 12: $2-5M ARR, 50-100k teams

### Months 12-18 (Phase 4)
- Month 13: SAML/OAuth integration
- Month 14: Audit logging infrastructure
- Month 15: First enterprise contracts
- Month 18: $20-50M ARR, 100-200 enterprise

### Months 18-24 (Phase 5)
- Month 19: Performance analytics live
- Month 20: GitHub/GitLab integration
- Month 21: Slack/Linear integration
- Month 24: $50-100M ARR, market dominance

---

## Investment/Staffing Roadmap

| Phase | Timeline | Team | Funding | Primary Focus |
|-------|----------|------|---------|---|
| **1** | Months 0-3 | You (1 FTE) | Bootstrapped | Harness, init tool, references |
| **2** | Months 3-6 | You + 1 contractor (0.5 FTE) | Bootstrapped | One-shot integration |
| **3** | Months 6-12 | You + 1-2 contractors (1 FTE) | $500k-2M pre-seed/seed | Marketplace, team mgmt |
| **4** | Months 12-18 | You + 2-3 contractors (1.5 FTE) | $5-20M Series A | SaaS platform, enterprise |
| **5** | Months 18-24 | You + 3-5 contractors (2-3 FTE) | Series A runway | Optimization, integrations, scale |

---

## Exit Strategy

### Year 3-4: Acquisition Target
- $300-600M acquisition by:
  - Anthropic (strategic fit)
  - GitHub (developer platform expansion)
  - Microsoft (enterprise development tools)
  - VC-backed exit ($300-600M in Series B/C fundraising)

### Year 4-5: Public/Large Exit
- $1-3B if you scale to 200-500k teams
- IPO or large strategic acquisition

### Most Likely Outcome
- Year 3-4: $300-600M acquisition by Anthropic or GitHub
- Harness + one-shot becomes native feature in Claude Code
- Your team joins acquirer

---

## Final Decision

**This is the plan. Commit to it. Execute it. Don't deviate.**

- ✅ Phases 1-2: Non-negotiable (own harness + code-gen)
- ✅ Phases 3-4: Very likely (marketplace + enterprise)
- ⚠️ Phase 5: Optimize as needed (always improving)
- ❌ Tier 3: Only if Tier 2 is won + separate team/funding

**Month 24 vision:** ONE SHOT PLUGIN is the standard harness + code-gen platform for Claude Code teams. Unopposed market. $50-100M ARR. Acquisition target for Anthropic.

Let's execute.

---

**Status**: Active execution plan  
**Last updated**: 2026-05-17  
**Owner**: You  
**Next checkpoint**: Month 3 (Phase 1 completion)
