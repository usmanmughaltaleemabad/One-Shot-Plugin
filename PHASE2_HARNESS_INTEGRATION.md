---
type: plan
last_verified: 2026-05-17
owner: claude
---

# Phase 2: Harness + One-Shot Integration (Months 3-6)

**Goal**: Make ONE SHOT PLUGIN the default code generation tool for harness users.

**Metrics**: 10-50k active users, $500k-1M ARR, 50+ enterprise teams

---

## Integration Architecture

### How One-Shot Integrates with Harness

```
User Request:
"Add user authentication with JWT"

One-Shot Workflow:
1. Read .claude/CLAUDE.md (understand project)
2. Detect framework (Django? FastAPI? Spring?)
3. Load .claude/standards/ (your team's rules)
4. Generate code respecting standards
5. Run .claude/agents/code-reviewer (validate)
6. Update .claude/beads/status.jsonl (track)
7. Return code that fits perfectly

Result:
- Generated code matches project style
- Passes code review agent
- Team standards enforced
- Decision tracked in beads
```

### Integration Points

**Reading Harness**:
- One-shot reads `.claude/CLAUDE.md` to understand project context
- One-shot checks `.claude/standards/` for team rules
- One-shot detects framework from project structure + CLAUDE.md hints

**Respecting Standards**:
- Code formatting matches `.claude/standards/code-style-*.md`
- Testing patterns follow `.claude/standards/testing-rules.md`
- Security practices match `.claude/standards/security-rules.md`

**Invoking Agents**:
- After generation, call code-reviewer agent
- Validate coverage with test-generator
- Scan for security issues
- Check performance implications

**Tracking Decisions**:
- Record what was generated in `.claude/beads/status.jsonl`
- Log which agents approved it
- Track success/failure for learning

---

## Phase 2 Deliverables

### 1. Framework Detection Engine
**File**: `skills/one-shot-generator/framework_detection_v2.py`

```python
def detect_framework_from_harness(project_path: str) -> str:
    """
    Detect framework by:
    1. Reading .claude/CLAUDE.md (hints like "Django 4.2+")
    2. Checking config files (settings.py, main.py, pom.xml, go.mod, package.json)
    3. Checking requirements/dependencies
    4. Scanning project structure
    
    Return: framework name (django, fastapi, spring, go, node)
    """
```

**Input**: Project path  
**Output**: Framework + version + detected standards  
**Usage**: Invoked by one-shot-generator before generation

### 2. Harness-Aware Code Generation
**File**: `skills/one-shot-generator/harness_aware_generation.py`

```python
def generate_code_respecting_harness(
    spec: str,
    project_path: str,
    framework: str,
) -> Dict:
    """
    Generate code that:
    1. Matches harness standards (code style, testing, security)
    2. Uses patterns from project (DRY, consistency)
    3. Includes tests (80%+ coverage)
    4. Has security validations
    5. Fits framework conventions
    
    Return: {
        "code": {file_path: code_content},
        "tests": {test_path: test_content},
        "docs": {doc_path: doc_content},
        "standards_met": [list of standards],
    }
    """
```

**Input**: User request, project path, framework  
**Output**: Code + tests + docs respecting standards

### 3. Five Example Projects
Complete working projects showing harness + one-shot integration:

**Project 1: Django Order Service (with Harness)**
- models: Order, OrderItem, Payment
- API: Create order, list orders, cancel order
- Features: JWT auth, pagination, webhook notifications
- Tests: 85%+ coverage
- Harness: .claude/ config + standards + agents

**Project 2: FastAPI Payment Processor (with Harness)**
- API: Process payment, refund, check status
- Database: PostgreSQL async
- Features: Idempotency keys, webhook callbacks, retry logic
- Tests: 80%+ coverage
- Harness: Async patterns, typing standards

**Project 3: Spring Boot User Management (with Harness)**
- API: CRUD users, roles, permissions
- Database: JPA/Hibernate
- Features: RBAC, audit logging, export/import
- Tests: MockMvc integration tests
- Harness: Spring patterns, Maven structure

**Project 4: Go Microservice (with Harness)**
- API: Product catalog service
- Database: PostgreSQL with migrations
- Features: Service discovery health checks, metrics
- Tests: Table-driven tests, mocks
- Harness: Go idioms, interface patterns

**Project 5: Node.js Real-Time API (with Harness)**
- API: WebSocket real-time updates
- Database: TypeORM entities
- Features: Authentication, subscriptions, caching
- Tests: Jest with async patterns
- Harness: TypeScript, async/await

**Each project includes**:
- Complete working code
- .claude/ harness config
- Generated code examples (showing one-shot + harness)
- Integration documentation
- Deployment instructions

### 4. Integration Documentation
**Files**: 
- `.claude/INTEGRATION_GUIDE.md` — How to use one-shot with harness
- `.claude/examples/INTEGRATION_WORKFLOW.md` — Step-by-step examples
- `skills/one-shot-generator/README.md` — Updated with harness awareness

### 5. Feedback Loop System
**File**: `.claude/beads/feedback_tracking.py`

```python
def track_generation_success(
    request: str,
    generated_code: str,
    approval: bool,
    agents_feedback: Dict,
) -> None:
    """
    Track generation for learning:
    - What was requested
    - What was generated
    - Did agents approve?
    - What feedback?
    - Did it work in production?
    """
```

---

## Implementation Timeline (Months 3-6)

### Month 3: Framework Detection + Harness Reading
- [ ] Implement framework detection from harness
- [ ] Read .claude/CLAUDE.md for project hints
- [ ] Detect standards from .claude/standards/
- [ ] Update one-shot-generator to use harness data

### Month 4: Code Generation + Standards
- [ ] Make code generation respect standards
- [ ] Integrate code-reviewer agent into workflow
- [ ] Add security scanning
- [ ] Validate test coverage

### Month 5: Example Projects + Documentation
- [ ] Create 5 example projects (Django, FastAPI, Spring, Go, Node)
- [ ] Document integration workflow
- [ ] Create integration guides
- [ ] Test on 10+ real codebases

### Month 6: Feedback Loop + Launch
- [ ] Implement success tracking (beads)
- [ ] Beta test with 100+ teams
- [ ] Measure metrics (time to generation, satisfaction, approval rate)
- [ ] Launch Phase 2 (target: 10-50k users, $500k-1M ARR)

---

## Technical Changes Required

### 1. Update one-shot-generator SKILL.md

Add these steps to generation workflow:

```markdown
## Enhanced Generation Workflow

1. **Harness Context**
   - Read .claude/CLAUDE.md
   - Detect framework
   - Load standards

2. **Framework-Specific Generation**
   - Use appropriate module set (177 modules available)
   - Generate code matching framework patterns
   - Include tests (80%+)

3. **Standards Validation**
   - Code style: Check against code-style-{framework}.md
   - Testing: Validate 80%+ coverage
   - Security: Check security standards
   - Performance: Review for bottlenecks

4. **Agent Review**
   - /call:code-reviewer (quality check)
   - /call:test-generator (coverage analysis)
   - /call:security-scanner (vulnerability scan)

5. **Decision Tracking**
   - Update .claude/beads/status.jsonl
   - Record generation request + result
   - Track agent approvals
```

### 2. Update Module Library (177 modules)

All 177 modules become harness-aware:
- Check team standards
- Respect code style
- Include tests
- Add security validations
- Follow framework patterns

### 3. New Functions

```python
# framework_detector.py
detect_framework(project_path) -> str

# standards_loader.py
load_team_standards(project_path) -> Dict

# code_generator_v2.py
generate_respecting_standards(spec, framework, standards) -> Dict

# agent_integration.py
run_validation_agents(code, framework) -> Dict

# beads_tracker.py
track_generation(request, code, approval) -> None
```

---

## Success Metrics (Month 6)

| Metric | Target | Success Indicator |
|--------|--------|---|
| **Active users** | 10-50k | 25k+ using harness + one-shot |
| **Revenue** | $500k-1M | Paying teams, enterprise deals |
| **Generation time** | 2-5 min | Average per feature request |
| **User satisfaction** | 4.5+ / 5.0 | NPS > 40 |
| **Code approval rate** | 80%+ | Code reviewers approve generated code |
| **Enterprise adoption** | 50+ teams | Large teams using full integration |

---

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|---|
| One-shot quality degrades | Medium | Extensive testing, agent validation |
| Harness reading fails | High | Fallback to framework detection |
| Standards too restrictive | Medium | Allow team customization |
| Performance impact | Medium | Cache standards, optimize detection |

---

## Go-to-Market (Month 6)

**Target Audience**:
- Teams already using harness (early adopters)
- Teams with Claude Code + development workflow
- Enterprise teams wanting governance + generation

**Channels**:
- Existing harness community (Discord, GitHub)
- One-Shot Plugin marketplace
- Case studies from 5 example projects
- Content: "Harness + One-Shot: The Claude IDE"

**Pricing** (freemium):
- Free: Core one-shot (5 modules)
- $15/mo/user: Unlimited one-shot + harness agents
- $5-50k/mo: Enterprise (SAML, compliance, premium agents)

---

## Decision Checkpoints

### End of Month 4
**Question**: Is framework detection working reliably?  
**Decision**: 
- ✅ YES → Continue
- ❌ NO → Extend Month 4, adjust approach

### End of Month 5
**Question**: Are example projects working? Is code quality good?  
**Decision**:
- ✅ YES → Launch beta
- ❌ NO → Fix issues, delay launch to Month 6.5

### End of Month 6
**Question**: Are we hitting metrics? (10-50k users, $500k+)?  
**Decision**:
- ✅ YES → Continue to Phase 3 (marketplace)
- ⚠️ PARTIAL → Extend Phase 2, focus on user acquisition
- ❌ NO → Reassess one-shot quality + harness strategy

---

## Phase 3 Preparation

At end of Phase 2, we have:
- ✅ One-shot + harness working seamlessly
- ✅ 5 example projects showing integration
- ✅ 50+ teams using full stack
- ✅ $500k+ ARR to fund next phase

Ready for Phase 3: Marketplace (agent/skill marketplace launch)

---

**Status**: Phase 2 Plan Ready  
**Start Date**: Month 3 (immediately after Phase 1)  
**Target Completion**: Month 6 with metrics validation

