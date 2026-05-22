---
type: implementation-plan
last_verified: 2026-05-21
owner: usman
scope: 4 parallel workstreams for global product launch
---

# Global Launch — Master Coordination Plan

> **For agentic workers:** Execute this via superpowers:subagent-driven-development. Four independent task streams can run in parallel. Integration checkpoints at end of each week.

**Goal:** Ship Harness P7 (standards) + P9 (eval harness) + Jugnu positioning + Slides skill as a cohesive go-to-market package.

**Architecture:** Four parallel tracks with soft dependencies:
1. **P7 Standards** (foundation) — defines what "quality" means
2. **P9 Eval Harness** (validation) — measures against those standards
3. **Jugnu Positioning** (messaging) — uses metrics as proof points
4. **Slides Skill** (sales asset) — visualizes the story

**Tech Stack:**
- Python 3.11+, Pytest, YAML
- Node.js 18+, Kie.ai API, Google Slides API
- Markdown, Git

---

## Master Timeline

### Week 1 — Foundation & Setup
- **P7:** Write REGISTRY.md + identify 8 rules
- **P9:** Define 6 SLOs + design task YAML schema
- **Jugnu:** Audit positioning + draft problem statement
- **Slides:** Design templates + style choices
- **Integration:** None yet (parallel discovery phase)

### Week 2 — Content Creation
- **P7:** Write all 8 standard files + wire 2 into hooks
- **P9:** Build task suite (20-30 scenarios) + implement eval_runner.py
- **Jugnu:** Write positioning brief + website copy + email draft
- **Slides:** Implement Node.js generator + Python compiler
- **Integration Checkpoint:** P9 baseline metrics ready → P7 validates against them

### Week 3 — Polish & Integration
- **P7:** Complete documentation, finalize hook integration
- **P9:** Run baseline evaluation, publish report
- **Jugnu:** Finalize launch narrative, create value prop onepager
- **Slides:** Generate example decks, publish SKILL.md
- **Integration Checkpoint:** All 4 ready for launch announcement

---

## Four Independent Plans

**Execute in parallel. Each plan is self-contained and produces working software.**

1. **[Harness Phase 7 Plan](2026-05-21-harness-phase-7-standards.md)** — Create `.claude/standards/` enforcement system
2. **[Harness Phase 9 Plan](2026-05-21-harness-phase-9-eval-harness.md)** — Build YAML task suite + baseline metrics
3. **[Jugnu Positioning Plan](2026-05-21-jugnu-positioning-guide.md)** — Write positioning narrative + marketing copy
4. **[Slides Skill Plan](2026-05-21-slides-skill-deck-generation.md)** — Implement agentic deck generation

---

## Integration Points (Week 3 Sync)

### Before Launch Announcement:
1. **Metrics validation** — Does eval baseline match positioning claims?
   - Claim: "99% routing accuracy"
   - Eval result: ✅ 99.2% (matches or beats)
   - If not: adjust positioning or run more eval iterations

2. **Example deck generation** — Can Slides skill visualize positioning narrative?
   - Generate conference deck using Jugnu copy
   - Verify 20-30 slides generated correctly
   - If not: debug Kie.ai integration

3. **Standards enforcement** — Do P7 rules catch real issues?
   - Run P7 validation on a recent generation
   - Verify at least 2 rules triggered correctly
   - If not: refine rule definitions

4. **Documentation consistency** — Are all references aligned?
   - README mentions standards + evals + positioning
   - CLAUDE.md links to `.claude/standards/` + `.claude/evals/`
   - plugin.json description includes proof points from evals

---

## File Structure (All 4 Workstreams)

```
.claude/
├── standards/                          ← NEW (Workstream 1)
│   ├── REGISTRY.md
│   ├── generated-code.md
│   ├── testing.md
│   ├── security.md
│   ├── fk-validation.md
│   ├── api-documentation.md
│   └── README.md
│
└── evals/                              ← NEW (Workstream 2)
    ├── tasks.yaml
    ├── eval_runner.py
    ├── slos.md
    ├── README.md
    └── baselines/2026-05-21-v1.0.0-baseline.jsonl

docs/
├── POSITIONING.md                      ← NEW (Workstream 3)
├── LAUNCH_NARRATIVE.md                 ← NEW (Workstream 3)
├── VALUE_PROP_ONEPAGER.md             ← NEW (Workstream 3)
└── superpowers/
    ├── specs/2026-05-21-global-launch-design.md
    └── plans/
        ├── 2026-05-21-global-launch-MASTER.md
        ├── 2026-05-21-harness-phase-7-standards.md
        ├── 2026-05-21-harness-phase-9-eval-harness.md
        ├── 2026-05-21-jugnu-positioning-guide.md
        └── 2026-05-21-slides-skill-deck-generation.md

skills/slides-from-spec/                ← NEW (Workstream 4)
├── SKILL.md
├── README.md
├── scripts/
│   ├── generate.js
│   ├── compile.py
│   └── templates/
│       ├── demo-deck.yaml
│       ├── conference-talk.yaml
│       └── onboarding.yaml
└── style/
    ├── isometric.txt
    └── ted-ed.txt

README.md                               ← MODIFIED (opening narrative)
MARKETPLACE_SUBMISSION.md               ← MODIFIED (positioning copy)
one-shot-prompting/CLAUDE.md            ← MODIFIED (link to standards + evals)
```

---

## Execution Model

### Option A: Subagent-Driven (Recommended)
- One subagent per workstream (P7, P9, Jugnu, Slides)
- Run 2 in parallel, stagger to avoid API limits
- Review each task before moving to next
- **Speed:** Fastest (4x parallelism)
- **Cost:** ~$8-12 (multiple subagents)

### Option B: Inline Execution
- Execute all 4 in this session sequentially
- Use checkpoints after each task for user review
- **Speed:** Slower (~2-3 hours wall clock)
- **Cost:** ~$5-8 (single session)

### Recommended: Subagent-Driven
Dispatch pairs:
1. **Pair 1 (Week 1):** P7 + P9 discovery tasks (both fast)
2. **Pair 2 (Week 2):** Jugnu writing + Slides implementation (independent)
3. **Sync (Week 3):** Integration + final polish (all together)

---

## Commit Strategy

Each task produces a commit. Pattern:
```bash
git add <files>
git commit -m "feat(P7): add security standards" 
# or
git commit -m "feat(P9): implement eval_runner"
```

By Week 3: 20-30 commits, one per task, easy to review and revert if needed.

---

## Success Criteria

| Workstream | Definition of Done |
|---|---|
| **P7** | All 8 `.claude/standards/*.md` files + REGISTRY + 2 hooks working |
| **P9** | `tasks.yaml` (20-30 scenarios) + `eval_runner.py` + baseline metrics committed |
| **Jugnu** | POSITIONING.md + LAUNCH_NARRATIVE.md + VALUE_PROP_ONEPAGER.md + README updated |
| **Slides** | SKILL.md + scripts (generate.js + compile.py) + templates + example decks |
| **Integration** | Metrics match claims, example decks generate, all docs linked and consistent |

---

**Next:** Choose execution model (subagent-driven or inline) and start Week 1 tasks.
