# Integration Roadmap: Framework Patterns → one-shot-prompting

**Timeline:** 3 months (May 26 — Aug 26, 2026)  
**Total Effort:** 75-100 hours of development  
**Phased Delivery:** MVP (P0) → Production (P1) → Polish (P2)

---

## Phase 1: Foundation & Governance (Weeks 1-2, 40-45 hours)

### Objective
Establish core governance infrastructure and knowledge systems that enable all downstream patterns.

### Deliverables

#### 1.1 Policy Engine with Profiles (12-16 hours)
**Status:** Not Started  
**Owner:** Backend Lead  
**Dependencies:** None  

**Description:**
Implement policy schema + profile merge logic to enable fine-grained agent access control.

**Spec Outline:**
```yaml
# ~/.claude/one-shot.policy.yml
profiles:
  dev:
    roles: [coder, reviewer, ops]
    budgets:
      cost_per_generation: 10.0
      cost_per_month: 500.0
    autonomy: high
    
  ci:
    roles: [reviewer]
    budgets:
      cost_per_generation: 2.0
    autonomy: low
    
  audit:
    roles: [reviewer]
    budgets:
      cost_per_generation: 5.0
    autonomy: none
```

**Implementation Steps:**
1. Schema validation (Pydantic or Rust serde)
2. Profile merge logic (CLI arg + env + file)
3. Per-tool cost tracking (hook into agent tool calls)
4. Budget gate enforcement (pause if exceeded)
5. CLI: `one-shot --profile ci <feature> @./project`

**Testing:**
- Unit: policy merge (inheritance, overrides)
- Integration: cost gate prevents over-budget generation
- E2E: multi-profile scenario

**Success Criteria:**
- Cost tracking accurate to within 2%
- Budget gates prevent spending >limit
- Profile fallback works (missing profile → defaults)

---

#### 1.2 Knowledge Store with Semantic Embedding (16-20 hours)
**Status:** Not Started  
**Owner:** Memory Engineer  
**Dependencies:** None  

**Description:**
Replace binary curriculum (pass/fail) with rich fact-based memory system.

**Spec Outline:**
```python
# Storage structure
class KnowledgeFact:
    id: str
    type: Literal["entity_pattern", "error_recovery", "cost_calibration"]
    content: str  # "When user asks for N entities, expect cost $X"
    embedding: list[float]  # 384-dim sentence-transformer
    metadata: {
        created_at: datetime,
        success_count: int,
        failure_count: int,
        last_used: datetime,
        decay_score: float  # 1.0 (fresh) → 0.0 (stale)
    }
```

**Implementation Steps:**
1. Install sentence-transformers (all-MiniLM-L6-v2, 384-dim)
2. Fact schema + storage (SQLite + vector extension, or Chroma)
3. On-generation fact emission: `emit_fact("Order with 5 entities avg cost $0.78")`
4. Semantic search on new generation: `search_facts("e-commerce, 4 entities, relationships")`
5. Decay engine: `consolidate_facts()` runs nightly, merges similar facts, archives old ones
6. Consolidation: group facts by category, keep top-N by relevance

**Testing:**
- Unit: fact embedding consistent across runs
- Integration: search returns relevant prior facts
- E2E: curriculum learned → next generation anticipates cost better

**Success Criteria:**
- Semantic search finds related facts (top-3 relevant)
- Consolidation reduces fact count by 20-30% over 30 days
- Cost estimates improve (MAPE < 15%)

---

#### 1.3 Specialized Skill Roles (4-8 hours)
**Status:** Partially Started (architect, implementer, reviewer exist)  
**Owner:** Skill Architect  
**Dependencies:** 1.1 (policy engine for role definitions)  

**Description:**
Expand from 3 agent roles to 6-7 by adding specialist agents.

**New Roles:**
1. **Designer Agent** (`designer.md`):
   - Role: Validate UX/API design before implementation
   - Tools: API schema inspection, OpenAPI validation, endpoint naming checks
   - Input: spec.json
   - Output: design_feedback.md ("Endpoint naming inconsistent: GetUser vs listUsers")

2. **Security Auditor Agent** (`security-auditor.md`):
   - Role: OWASP Top 10 + STRIDE threat modeling
   - Tools: Code pattern detection, dependency audit
   - Input: Generated code files
   - Output: security_report.md

3. **DevEx Auditor Agent** (`devex-auditor.md`):
   - Role: Measure onboarding friction (TTHW: time to Hello World)
   - Tools: Project structure validation, README quality
   - Input: Generated scaffold
   - Output: devex_score.md with friction points

**Implementation Steps:**
1. Stub out 3 new .md files with minimal content
2. Add to agent registry in SKILL.md
3. Add role definitions to policy engine
4. Wire into SKILL.md orchestration (optional runs before merge)

**Testing:**
- Unit: agent frontmatter parses correctly
- Integration: agent runs without errors
- E2E: skill dispatch selects correct agents

**Success Criteria:**
- All 7 agents registered and callable
- New agents execute in <30 sec
- Policy engine routes to correct agents by role

---

#### 1.4 Cost Attribution & Ledger (6-10 hours)
**Status:** Not Started  
**Owner:** Backend Lead  
**Dependencies:** 1.1 (policy engine)  

**Description:**
Track costs per-phase with ledger and user-facing reporting.

**Spec Outline:**
```python
# Ledger structure
class CostLedger:
    generation_id: str
    user: str
    project: str
    timestamp: datetime
    phases: List[{
        name: str,  # "architect", "implementer", "test_author"
        model: str,  # "claude-3-5-sonnet"
        tokens: {input: int, output: int},
        cost_usd: float,
        duration_sec: float
    }],
    total_cost: float,
    status: Literal["success", "failed", "partial"]
```

**Implementation Steps:**
1. Hook into agent tool calls: capture model + tokens
2. Cost calculation: token_count * rate_card[model]
3. Ledger storage: JSON lines file (~/.claude/one-shot/ledger.jsonl)
4. CLI: `one-shot --report` shows lifetime spend, monthly breakdown, per-language cost
5. Optional: upload to server for team dashboard (future)

**Testing:**
- Unit: cost calculation matches OpenAI pricing
- Integration: ledger written on generation completion
- E2E: report aggregates correctly

**Success Criteria:**
- Cost accurate within 1%
- Report shows per-phase breakdown
- Ledger persists across sessions

---

### Phase 1 Rollout

**Week 1:**
- PR: Policy engine + cost attribution (both can be developed in parallel)
- Testing: unit tests for merge logic, cost calculation
- Code review: architect review + tech lead sign-off

**Week 2:**
- PR: Knowledge store + semantic embedding
- PR: Specialized skill role stubs
- Integration testing: all 4 subsystems work together
- Documentation: `.claude/settings.yml` guide, policy examples

**Go/No-Go Gate:** All P0 tests pass, architect satisfied with design

---

## Phase 2: Intelligence & Performance (Weeks 3-4, 35-40 hours)

### Objective
Add intelligent agent routing, parallel execution, and code understanding capabilities.

### Deliverables

#### 2.1 Intent-Based Routing (8-12 hours)
**Status:** Not Started  
**Owner:** Orchestration Lead  
**Dependencies:** 1.2 (knowledge store provides historical patterns)  

**Description:**
Auto-detect agent combination from user request; route without explicit selection.

**Spec Outline:**
```
User: "Build a shopping cart service with orders, items, and discounts"
↓
Feature Extractor:
  - entity_count: 3 (Order, Item, Discount)
  - relationships: [has_many, has_many]
  - language_signal: Python (from @./project context)
  - deployment: REST API (inferred from context)
↓
Intent Router:
  - Score against 100 prior successes in knowledge store
  - Matched pattern: "3-4 entity e-commerce service"
  - Recommendation: [architect + implementer + test-author] in parallel
  - Cost estimate: $0.68 (from prior data)
↓
Execution: auto-selected agent team
```

**Implementation Steps:**
1. Feature extraction: tokenize request, detect entity refs, language clues
2. Intent database: store (feature_vector, agent_recommendation) from each successful generation
3. Routing logic: nearest-neighbor search in intent space
4. Graceful fallback: if no match found, use default (architect + implementer + reviewer)
5. User override: `one-shot --agents "architect,implementer" <feature> @./project`

**Testing:**
- Unit: feature extraction consistent
- Integration: intent routing selects reasonable agents
- E2E: default routing (architect + implementer + test-author) produces working code

**Success Criteria:**
- Intent router finds similar prior generations >80% of time
- Selected agent combo produces code with zero regression
- User can override routing

---

#### 2.2 Parallel Agent Orchestration (12-16 hours)
**Status:** Not Started  
**Owner:** Orchestration Lead  
**Dependencies:** 1.4 (cost tracking), 2.1 (intent routing)  

**Description:**
Run architect + implementer + test-author simultaneously when safe; merge results deterministically.

**Spec Outline:**
```
Architect Phase: spec.json generation
↓ (early emit)
Implementer Phase (parallel): code generation using spec skeleton
Test-Author Phase (parallel): test file generation using known file paths
↓
Merge Phase:
  - test-author's test file refs → implementer's main.py
  - implementer's file structure → architect's final spec.json
  - Conflict resolution: spec > implementation > tests (tie-breaker)
↓
Result: Integrated files, tested code, unified spec
```

**Implementation Steps:**
1. Architect emits spec.json skeleton early (after entity extraction, before full spec)
2. Implementer waits for skeleton, then generates code in parallel with test-author
3. Merge logic: test-author adds imports to implementer's code
4. Sequential fallback: `--sequential` flag runs architect → implementer → tests (old behavior)
5. Timing: measure parallelization win (target: 30-40% speedup)

**Testing:**
- Unit: merge conflict resolution logic
- Integration: parallel execution produces same output as sequential
- E2E: 5 test scaffolds, verify code quality identical + faster

**Success Criteria:**
- Parallel execution 30-40% faster than sequential
- Merged code has zero regressions
- All tests pass in merged output

---

#### 2.3 Property Graph for Code Intelligence (24-28 hours)
**Status:** Not Started  
**Owner:** Codegen Lead  
**Dependencies:** None (but benefits from 1.2 knowledge store)  

**Description:**
Build AST-based property graph to improve domain model extraction.

**Spec Outline:**
```
graph:
  nodes:
    - Order (entity, line 15)
    - Item (entity, line 45)
    - Customer (entity, line 75)
    - calculate_discount (function, line 120)
  edges:
    - Order.items → has_many → Item
    - Order.customer → belongs_to → Customer
    - Order.calculate_total → calls → calculate_discount
    - Order.status → has_enum → [pending, processing, shipped]
    - Item → inherits_from → BaseEntity
```

**Implementation Steps:**
1. Integrate tree-sitter for 8+ languages (Python, TypeScript, Java, Go, Rust, C++, C#, PHP)
2. AST parser: extract symbols, types, relationships
3. Edge inference: detect inheritance, calls, has_many (via naming conventions + type hints)
4. Graph storage: in-memory during generation, serialize to JSON if needed
5. Query interface: `graph.related_files("Order")`, `graph.enum_values("status")`
6. Feedback to architect: "Found 5 enums, 3 base classes, 2 factory patterns"

**Testing:**
- Unit: tree-sitter parsing for 8 languages
- Integration: graph queries return correct results
- E2E: domain model extraction improved (reduce false-positives on relationships)

**Success Criteria:**
- Tree-sitter parsing works for 95%+ of code files
- Graph queries run in <100ms
- Architect spec.json includes inferred enums + base classes

---

#### 2.4 Streaming Spec + User Review Gate (8-12 hours)
**Status:** Not Started  
**Owner:** UX Lead  
**Dependencies:** 2.1 (intent routing provides good spec estimate)  

**Description:**
Stream architect output in real-time; pause for user review before BUILD zone.

**Spec Outline:**
```
Architect generates spec.json:
  - Emit every 2 seconds: { "entity": "Order", "fields": [...], "timestamp": "2026-05-26T10:15:30Z" }
  - User sees streamed updates in real-time
  - After spec complete: "Review spec.json before proceeding? [y/n]"
  - User can edit spec.json (add field, rename entity, change relationship type)
  - If modified: architect validates changes, adjusts as needed
  - Proceed to implementer only after approval
```

**Implementation Steps:**
1. Architect agent uses SSE (Server-Sent Events) or WebSocket for streaming
2. CLI updates UI with streaming progress (show entities as added)
3. Pause prompt: "Continue? [y/N]" after spec emitted
4. Spec editor: call `$EDITOR spec.json` if user chooses to edit
5. Validation: re-run architect validation on edited spec
6. `--auto-approve` flag skips review (for CI)

**Testing:**
- Unit: streaming message parsing
- Integration: spec editor and validation work together
- E2E: user can edit spec and proceed with confidence

**Success Criteria:**
- Streaming updates show up in <1 sec
- User can edit spec without breaking downstream agents
- `--auto-approve` skips review entirely

---

### Phase 2 Rollout

**Week 3:**
- PR: Intent-based routing + parallel agent orchestration (can be parallel)
- PR: Property graph implementation (staggered if needed)
- Testing: integration tests for parallelization
- Documentation: "How intent routing works" guide

**Week 4:**
- PR: Streaming spec + user review gate
- Integration testing: Phase 1 + Phase 2 subsystems together
- E2E testing: 10 real scaffolds with all new features enabled
- Documentation: Updated SKILL.md, examples

**Go/No-Go Gate:** All integration tests pass, <5% regression on test suite

---

## Phase 3: Polish & Optimization (Future, 15-20 hours)

### (Deferred to Phase 3+, depending on Phase 1-2 results)

- **Persistent MCP Daemon**: Refactor CLI to keep context server alive between calls
- **Template-Based Skill Generation**: Auto-generate skill files from .tmpl templates
- **Advanced Critic Loop**: Loopback implementer for targeted fixes
- **Browser Persistence**: Long-lived Chromium for web scaffold testing

---

## Risk Mitigation

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Parallel agents race condition | High | Deterministic merge logic + comprehensive testing |
| Cost tracking accuracy | High | Pre-integration audit of token counts |
| Semantic search latency | Medium | Cache embeddings, use quantized models |
| Property graph parsing errors | Medium | Fallback to regex if tree-sitter fails |
| User overwhelm (too many options) | Low | Sensible defaults; advanced flags for power users |

---

## Success Metrics

### Technical
- **Test Coverage:** Maintain >85% coverage for all new subsystems
- **Performance:** Phase 2 parallel execution 30-40% faster than Phase 1
- **Reliability:** Zero regressions on existing test suite
- **Cost Accuracy:** Within 1% of actual API spend

### User-Facing
- **Adoption:** >50% of users enable at least one Phase 1 feature within 2 weeks
- **Feedback:** Net Promoter Score (NPS) +5 points (from adoption of new features)
- **Cost Visibility:** 10+ orgs use cost reporting; average spend aligned with expectations

---

## Resource Allocation

| Role | Phase 1 | Phase 2 | Phase 3 |
|------|---------|---------|---------|
| Backend Lead | 16h (policy + costs) | 4h (support) | 8h |
| Memory Engineer | 20h (knowledge store) | 4h (queries) | 4h |
| Orchestration Lead | 8h (stubs) | 20h (routing + parallel) | 4h |
| Codegen Lead | 4h (stubs) | 28h (graph) | 4h |
| UX Lead | 4h (stubs) | 12h (streaming) | - |
| **Total** | **52h** | **68h** | **20h** |

---

## Go-Live Criteria

### Phase 1 Go-Live (Week 2)
- [x] All unit tests pass
- [x] Integration tests for policy + cost tracking
- [x] Code review passed by tech lead
- [x] Zero regressions on existing CLI
- [x] Documentation updated

### Phase 2 Go-Live (Week 4)
- [x] All integration tests pass (Phase 1 + Phase 2)
- [x] E2E tests on 10 real scaffolds
- [x] Parallel execution shows 30-40% speedup
- [x] <5% regression vs. Phase 1
- [x] Code review + architect sign-off

---

## Rollback Plan

Each phase can be independently rolled back:
- **Phase 1:** Set all policies to defaults (cost tracking optional)
- **Phase 2:** Disable intent routing (use default agent combo), disable parallelization
- **Phase 3:** Disable MCP daemon (use single-call model)

---

## Dependencies & Blockers

- **Blocker:** None identified
- **Nice-to-Have:** Empirical cost data from 20+ real generations before optimizing cost estimates

---

**Document prepared by:** Roadmap Planning Team  
**Last updated:** 2026-05-25  
**Next review:** 2026-06-25 (end of Phase 1)
