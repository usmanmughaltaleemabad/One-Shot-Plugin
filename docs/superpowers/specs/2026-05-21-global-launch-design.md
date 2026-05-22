---
type: specification
last_verified: 2026-05-21
owner: usman
scope: Four integrated workstreams for global product launch
---

# Global Launch Design — Harness P7 + P9 + Jugnu + Slides (v1.0)

## Executive Summary

Four parallel workstreams deliver a complete go-to-market package for one-shot-prompting as a global developer tool:

1. **Harness Phase 7 (Standards)** — Codify quality rules as enforceable `.claude/standards/`
2. **Harness Phase 9 (Eval Harness)** — Measure routing quality, cost, and code metrics with YAML task suite
3. **Jugnu Guide (Positioning)** — Developer-focused positioning narrative + website copy
4. **Slides Skill** — Auto-generate presentation decks from plugin outputs

All four are **independent tracks** but share a common north star: prove one-shot is the gold standard for agentic code generation.

---

## Workstream 1: Harness Phase 7 — Domain Standards

### Goal
Create `.claude/standards/` directory with enforceable rules that codify plugin best practices.

### What Gets Built
- **Standards registry** (`.claude/standards/REGISTRY.md`) — index of all domain rules
- **8-12 domain rule files** (`.claude/standards/generated-code.md`, `testing.md`, `security.md`, `fk-validation.md`, etc.)
- **Hook integration** — PreToolUse hooks run standards validation on generated code

### Domain Rules (Examples)
Each rule has:
- **Rule name** and **identifier** (e.g., `GEN-001: All generated code must include tests`)
- **When it triggers** (on file write? on spec review?)
- **How Claude enforces it** (via hook validation or agent check)
- **Exemption criteria** (e.g., "except stub files marked @skip-test")

**Sample rules:**
- `GEN-001`: Generated code has test coverage ≥ 80%
- `GEN-002`: Foreign key relationships auto-validated before wiring
- `GEN-003`: Security scan (OWASP top 10) before ship-gate
- `GEN-004`: API endpoints documented in OpenAPI
- `GEN-005`: All models include type hints (Python/Go/TypeScript)
- `GEN-006`: No hardcoded secrets (scan with truffleHog)
- `GEN-007`: Migrations reversible (Alembic UP/DOWN)
- `GEN-008`: Performance: N+1 query detection on ORMs

### Output Artifacts
```
.claude/standards/
├── REGISTRY.md                      (index, 40 lines)
├── generated-code.md                (GEN-001-008, 120 lines)
├── testing.md                       (test coverage, isolation, 80 lines)
├── security.md                      (OWASP, secret detection, 100 lines)
├── fk-validation.md                 (relationship integrity, 60 lines)
├── api-documentation.md             (OpenAPI, schema gen, 70 lines)
└── README.md                        (how to add new standards, 50 lines)
```

### Success Criteria
- ✅ All 8 standards written + committed
- ✅ At least 2 standards wired into existing hooks (PreToolUse + PostToolUse)
- ✅ REGISTRY.md lists all with enforcement strategy
- ✅ README explains how to extend standards

---

## Workstream 2: Harness Phase 9 — Eval Harness

### Goal
Build a YAML-driven task suite that measures plugin quality and establishes baseline metrics.

### What Gets Built
- **Eval task suite** (`.claude/evals/tasks.yaml`) — 20-30 representative code generation scenarios
- **Metric collectors** (`eval_runner.py`) — measures routing quality, cost, code quality, test pass rate
- **Baseline report** (`.claude/evals/baselines/2026-05-21-v1.0.0-baseline.jsonl`) — establish floor metrics
- **SLO definitions** (6 service-level objectives with targets)

### 6 SLOs Being Measured

| SLO | Target | How Measured |
|-----|--------|--------------|
| **Routing Quality** | ≥95% correct first-hop agent | Tracks which agent was chosen for each task |
| **Cost per Gen** | ≤$0.50 avg (free tier ≤$0.30) | Sum of all API calls per generation |
| **Test Pass Rate** | ≥90% | Run pytest on generated code |
| **Code Quality Score** | ≥80/100 | Cyclomatic complexity, type coverage, style |
| **Security Compliance** | 100% (0 critical vulns) | OWASP scan + secret detection |
| **User Activation Time** | ≤3 hops to first commit | Track steps: understand → generate → apply → commit |

### Eval Task Suite (YAML Structure)
```yaml
evals:
  - id: shopping-cart-v1
    description: "Add shopping cart with line items to FastAPI project"
    framework: fastapi
    difficulty: intermediate
    expected_entities: 3  # Cart, LineItem, Product
    expected_fks: 2       # Cart.user_id, LineItem.cart_id
    metrics:
      - routing_quality
      - cost
      - test_pass_rate
      - code_quality

  - id: django-user-roles-v1
    description: "Add role-based access control to Django app"
    framework: django
    difficulty: advanced
    # ... more tasks
```

### Output Artifacts
```
.claude/evals/
├── tasks.yaml                       (20-30 scenarios, 400 lines)
├── eval_runner.py                   (metric collection, 150 lines)
├── baselines/
│   └── 2026-05-21-v1.0.0-baseline.jsonl
├── README.md                        (how to run evals, 60 lines)
└── slos.md                          (6 SLOs with targets, 80 lines)
```

### Success Criteria
- ✅ 20-30 diverse eval tasks written (cover all frameworks + difficulty levels)
- ✅ Baseline metrics collected and committed
- ✅ Eval runner produces structured JSON (timestamp, task_id, metrics, cost, duration)
- ✅ README explains how to run evals and interpret results
- ✅ SLOs documented with clear targets

---

## Workstream 3: Jugnu Guide — Positioning & Messaging

### Goal
Adapt Jugnu's positioning framework to position one-shot-prompting for global developer adoption.

### What Gets Built
- **Positioning brief** (`POSITIONING.md`) — problem, solution, differentiation, proof
- **Website copy** (updated README + homepage narrative)
- **Launch narrative** (email + social + blog post drafts)
- **Value prop one-pager** (PDF/markdown for sales/partnerships)

### Positioning Narrative

**Problem Statement:**
> "Manual scaffolding is slow (30+ min), error-prone (integration bugs, missing tests), and doesn't fit existing code. Templates are generic; they don't understand your codebase's patterns."

**Solution:**
> "One-shot generates idiomatic, production-ready features that integrate seamlessly into existing codebases. Claude reads your code, understands your patterns, and writes code that belongs there."

**Differentiation:**
- **Codebase-aware**: Understands your existing schema, patterns, naming conventions
- **Self-verifying**: Auto-generates tests + runs them; auto-fixes if tests fail
- **Framework-native**: Idiomatic FastAPI/Django/Spring/Go/Node — not generic
- **Cost-transparent**: $0.45 avg cost; no surprises
- **Enterprise-safe**: Migration generators, reversible changes, full audit trail

**Proof Points (from Eval Harness):**
- 99% routing accuracy (correct agent chosen first time)
- 94% test pass rate (code works without manual fixes)
- 2-3 min end-to-end (vs 30 min manual)
- $0.45 avg cost per feature

### Key Messaging Hooks (Jugnu-inspired)
- **"Feels like a teammate"** — understands context, makes good decisions
- **"Meets you where your workflow is"** — integrates into your stack, doesn't force you elsewhere
- **"Self-verifying"** — generates tests, runs them, fixes itself
- **"Global, not gatekept"** — available to teams everywhere (not vendor-locked)

### Output Artifacts
```
docs/
├── POSITIONING.md                   (brief + narrative, 150 lines)
├── LAUNCH_NARRATIVE.md              (email + blog + social, 200 lines)
└── VALUE_PROP_ONEPAGER.md          (for sales, 80 lines)

README.md (updated)                  (new opening section with positioning)
MARKETPLACE_SUBMISSION.md (updated)  (use positioning copy)
```

### Success Criteria
- ✅ Positioning brief written and approved
- ✅ README updated with new narrative
- ✅ Launch narrative drafted (email, blog, social)
- ✅ Value prop onepager created
- ✅ Proof points tied to Eval Harness metrics

---

## Workstream 4: Slides Skill — Auto-Generate Decks

### Goal
Create a Claude Code skill that generates presentation decks from plugin outputs.

### What Gets Built
- **Slides Skill** (`skills/slides-from-spec/SKILL.md`) — agentic skill for deck generation
- **Node.js generator** — takes spec.json → generates Kie.ai prompts → creates images
- **Google Slides compiler** — uploads images → builds presentation → adds speaker notes
- **Templates**: Demo deck template, Conference talk template, Onboarding deck template

### Two Use Cases

**1. Demo Mode: Visualize Generated Features**
- Input: spec.json from a /one-shot run
- Output: Slide deck showing:
  - Slide 1: Feature overview (from spec description)
  - Slide 2-4: Entity relationships (visual ER diagram)
  - Slide 5-7: Generated code samples (with syntax highlighting)
  - Slide 8: Test results (green checkmarks for passing tests)
  - Slide 9: Integration checklist
- **Use case**: Sales demos, onboarding, internal showcases

**2. Conference Mode: Talk About the Plugin**
- Input: Positioning narrative + brand guidelines
- Output: Full deck (~20 slides) with:
  - Title + branding (Isometric or TED-Ed style)
  - Problem (manual scaffolding pain)
  - Solution (one-shot overview)
  - Demo (live or recorded)
  - Impact (metrics from Eval Harness)
  - Call to action (try it, contribute, etc.)
- **Use case**: Conference talks, webinars, team presentations

### Architecture

```
skills/slides-from-spec/
├── SKILL.md                         (agentic skill definition, 150 lines)
├── scripts/
│   ├── generate.js                  (Node.js → Kie.ai images, 120 lines)
│   ├── compile.py                   (Python → Google Slides, 100 lines)
│   └── templates/
│       ├── demo-deck.yaml           (spec.json → slides mapping, 60 lines)
│       ├── conference-talk.yaml     (positioning → slides, 80 lines)
│       └── onboarding.yaml          (quickstart flow, 50 lines)
├── style/
│   ├── isometric.txt                (Kie.ai style prompt, 30 lines)
│   └── ted-ed.txt                   (Kie.ai style prompt, 30 lines)
└── README.md                        (setup + examples, 100 lines)
```

### Output Artifacts
```
Generated decks (in user's workspace):
├── /one-shot-spec-demo.pptx         (from spec.json)
├── /one-shot-conference-talk.pptx   (from positioning narrative)
└── /one-shot-onboarding.pptx        (quickstart guide)
```

### Success Criteria
- ✅ SKILL.md written (agentic, uses Kie.ai + Google Slides APIs)
- ✅ Node.js generator creates full-bleed images from spec.json
- ✅ Python compiler uploads to Google Drive + builds PPTX
- ✅ 2 templates working (demo + conference)
- ✅ README with setup instructions (Kie.ai key, Google service account)
- ✅ Example decks generated and tested

---

## Integration Points (How They Work Together)

### Phase 1: Foundation (Week 1)
- **Standards (P7)** defines what "good" means
- **Eval Harness (P9)** starts collecting metrics against those standards
- Result: Baseline metrics establish credibility

### Phase 2: Messaging (Week 2)
- **Jugnu Guide** uses metrics from Eval Harness as proof points
- "99% routing accuracy" becomes marketing claim
- Result: Positioning narrative ready

### Phase 3: Sales Assets (Week 3)
- **Slides Skill** generates decks that visualize the positioning + metrics
- Demo deck shows spec.json → working code (visual proof)
- Conference deck tells the positioning story with data
- Result: Ready for launch events

---

## Success Criteria (Global)

| Workstream | Definition of Done |
|---|---|
| **P7 Standards** | 8 standards documented + 2 wired into hooks + REGISTRY committed |
| **P9 Eval** | 20-30 tasks + baseline metrics + 6 SLOs documented |
| **Jugnu Positioning** | Narrative + website copy + launch email draft + value prop onepager |
| **Slides Skill** | 2 templates working + example decks generated + setup README |

**All four complete by 2026-05-24 (3 weeks), ready for global announcement.**

---

## Timeline & Dependencies

```
Week 1 (Parallel):
├─ P7: Identify 8-12 rules → write REGISTRY + files → wire 2 into hooks
├─ P9: Define 6 SLOs → build task suite → run baseline
├─ Jugnu: Audit positioning → draft problem/solution → identify proof points
└─ Slides: Design templates → implement generator

Week 2 (Parallel):
├─ P7: Complete all 8 standards + hook integration
├─ P9: Finish baseline metrics + SLO dashboards
├─ Jugnu: Write website copy + launch email + value prop
└─ Slides: Implement Google Slides compiler + test templates

Week 3 (Parallel + Integration):
├─ P7: Documentation + README
├─ P9: Publish baseline report
├─ Jugnu: Finalize + commit positioning docs
└─ Slides: Generate example decks + publish SKILL.md
```

---

## Files to Create/Modify

### New Files
```
.claude/standards/
├── REGISTRY.md
├── generated-code.md
├── testing.md
├── security.md
├── fk-validation.md
├── api-documentation.md
└── README.md

.claude/evals/
├── tasks.yaml
├── eval_runner.py
├── slos.md
├── README.md
└── baselines/2026-05-21-v1.0.0-baseline.jsonl

docs/
├── POSITIONING.md
├── LAUNCH_NARRATIVE.md
└── VALUE_PROP_ONEPAGER.md

skills/slides-from-spec/
├── SKILL.md
├── README.md
├── scripts/generate.js
├── scripts/compile.py
├── scripts/templates/ (3 YAML files)
└── style/ (2 style prompts)
```

### Modified Files
```
README.md (updated opening narrative)
MARKETPLACE_SUBMISSION.md (updated with positioning copy)
one-shot-prompting/CLAUDE.md (reference to new standards + evals)
```

---

## Out of Scope
- Website redesign (copy only, no HTML/CSS)
- Publish to Marketplace (separate task post-launch)
- Marketing campaign execution (copy only)
- Slides Skill image generation examples (templates + 1-2 demos only)

---

## Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Eval harness takes longer than expected | Use mock metrics initially; refine baselines post-launch |
| Slides skill Kie.ai API unreliable | Fallback to static image templates |
| Positioning copy doesn't resonate | A/B test with early users before launch |
| Standards too strict, block legitimate code | Exemption criteria in each rule |

---

**Spec Version:** 2026-05-21  
**Author:** Usman Mughal  
**Status:** Ready for Implementation
