---
name: jugnu-positioning
description: Agentic skill for generating and maintaining positioning narratives, launch copy, and marketing materials
---

# Jugnu Positioning Skill

Generate and maintain product positioning, launch narratives, and marketing copy using the Jugnu framework (problem-solution-differentiation).

## Invocation

```bash
/jugnu-positioning "<product>" @./path [--update] [--format=narrative|copy|sales]
```

Examples:
```bash
/jugnu-positioning "Claude Code plugin for agentic scaffolding" @./ --format=narrative
/jugnu-positioning "Developer tool" @./ --update --format=copy
```

## What This Skill Does

**Input:** Product description, target audience, existing codebase context
**Output:** 
- Position statement (problem + solution + differentiation)
- Launch narratives (email, blog, Twitter, LinkedIn, HN submission)
- Sales one-pager (ROI, technical specs, partnership opportunities)
- Value proposition document
- Updated README opening

**Agents Used:**
- **positioning-architect** (sonnet) — analyzes problem space, competitive landscape, creates positioning framework
- **narrative-writer** (haiku) — generates launch copy, email, blog, social media
- **sales-writer** (haiku) — creates value props, ROI calculations, partnership docs
- **integrator** (haiku) — updates README, MARKETPLACE_SUBMISSION, CHANGELOG

## Use Cases

### New Product Launch
```bash
/jugnu-positioning "AI-powered slide deck generator for startups" @./ --format=narrative
# Generates: problem statement, solution, differentiation, launch emails, blog post
```

### Reposition Existing Product
```bash
/jugnu-positioning "Move from internal developer tool to global SaaS" @./ --update --format=copy
# Updates: positioning.md, launch narrative, README, marketplace submission
```

### Generate Sales Materials
```bash
/jugnu-positioning "Enterprise licensing for one-shot generation" @./ --format=sales
# Generates: value prop onepager, ROI table, partnership opportunities
```

## Output Files

Default output location: `docs/`

- `POSITIONING.md` — positioning strategy (problem/solution/differentiation)
- `LAUNCH_NARRATIVE.md` — launch copy (email, blog, social, HN)
- `VALUE_PROP_ONEPAGER.md` — sales document
- `README.md` (updated) — integrated new opening
- `MARKETPLACE_SUBMISSION.md` (updated) — updated plugin description

## Flags

- `--update` — update existing docs (default: create new)
- `--format=narrative|copy|sales` — which output to focus on (default: all)
- `--dry-run` — show outputs without writing files
- `--audience=enterprise|startup|community` — tailor messaging

## Framework

Uses **Jugnu Framework** (problem-solution-differentiation):

1. **Problem** — What frustrates developers today?
2. **Solution** — How does your product solve it?
3. **Differentiation** — Why you, not alternatives?
4. **Proof Points** — Evidence (speed, cost, reliability, adoption)
5. **Messaging Hooks** — Memorable lines for marketing

## Technical Details

**Skill Tools:**
- `read_files` — analyze existing codebase, existing marketing docs
- `write_files` — create/update positioning files
- `git` — commit changes if `--apply` flag used

**Agents:**
- `positioning-architect` (sonnet) — $0.15-0.25 per run
- `narrative-writer` (haiku) — $0.03-0.05 per run
- `sales-writer` (haiku) — $0.03-0.05 per run
- `integrator` (haiku) — $0.02-0.03 per run

Typical cost: **$0.25-0.40 per positioning refresh**

## Integration

Works with:
- `slides-from-spec` — generates presentation decks from positioning
- `one-shot-generate` — uses positioning in feature generation context
- `marketplace` — submits positioning to plugin marketplaces

## Examples

### Example 1: New Tool Launch
```bash
/jugnu-positioning "LLM-powered database migration tool" @./my-project
```

**Output:**
- Positioning identifies: "Developers spend days on migrations. Migrations are mechanical. LLMs excel at mechanical tasks."
- Solution: "Migrations written by Claude, tested, reversible, integrated with your ORM"
- Differentiation: "Only tool that understands existing schema + generates idiomatic migrations"
- Launch email, blog post, Twitter thread, LinkedIn post, HN submission
- Sales one-pager showing: $X saved per migration, enterprise safety features, proof of accuracy

### Example 2: Reposition for Global Audience
```bash
/jugnu-positioning "Expand from internal-only to global developer SaaS" @./ --update
```

**Output Updates:**
- Position emphasizes: global distribution, multi-framework support, cost-transparency
- Launch narrative includes: early adopter benefits, roadmap visibility, partnership opportunities
- Sales one-pager adds: regional pricing, SLA, enterprise support tiers
- README opening refreshed with global positioning
- Marketplace submission updated

### Example 3: Partner Pitch
```bash
/jugnu-positioning "Design partner program" @./ --format=sales --audience=enterprise
```

**Output:**
- Value prop onepager focused on: co-marketing, revenue share, exclusive features
- Partner positioning: "Solve scaffolding at enterprise scale"
- 6-month roadmap showing partner input channels
- ROI table for partners: "How many deals, what margin, success rate"
