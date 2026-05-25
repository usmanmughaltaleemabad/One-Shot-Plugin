---
type: guide
last_verified: 2026-05-25
owner: claude
---

# Agent-First Universal Rule Set

The foundational architectural principle that governs all reasoning and computation in one-shot-prompting.

## Executive Summary

**Core Principle:** All reasoning tasks are dispatched to Claude models via agents (through the Task tool); deterministic operations are handled by Python scripts. This separation ensures that complex judgment calls benefit from LLM reasoning while expensive deterministic operations are optimized through deterministic code.

### Why This Matters

The Plugin started as a Python application generating code via f-string templates. That approach produced three problems:

1. **Template leaks**  -  escaped variables, malformed imports, incorrect indentation
2. **Brittle reasoning**  -  templates couldn't adapt to new patterns or frameworks
3. **Wasted compute**  -  Python was trying to do things it's bad at (creative reasoning) while ignoring things it's good at (fast, deterministic scanning)

**Agent-first solves this** by:
- Moving code generation into Claude (reasoning, correctness, adaptability)
- Keeping expensive scanning/patching/wiring in Python (speed, determinism, cost control)
- Creating a clear contract between layers (JSON I/O, no tight coupling)

### Key Benefits

| Benefit | How Agent-First Delivers |
|---------|-------------------------|
| **Correctness** | Claude reasons about context; Python verifies deterministically |
| **Cost Control** | Only dispatch complex decisions to Claude; use Python for scanning/patching |
| **Debuggability** | Clear separation = clear failure modes; stack traces point to layer |
| **Maintainability** | New patterns = new agents; old scripts keep working |
| **Speed** | Python handles I/O-bound scanning in parallel; Claude thinks while Python runs |

### Tradeoffs

| Tradeoff | Acceptance |
|----------|-----------|
| **More coordination** | Accepted  -  YAML frontmatter + JSON protocol ensure contract |
| **Agent dispatch latency** | Accepted  -  agents run in parallel; overhead ≤ 2s per dispatch |
| **Token cost** | Minimized  -  cost gates + caching + haiku routing keep spend <$1/gen |

---

## Core Principle

### Formal Definition

An **Agent-First architecture** is one where:

1. **Reasoning tasks** (any decision requiring judgment, context, or creative thinking) run via Claude agents dispatched through the Task tool
2. **Deterministic operations** (scanning, parsing, patching, wiring, cost estimation) run as Python scripts
3. **JSON protocol** governs all I/O between agents and scripts
4. **No agent does deterministic work**  -  if it can be computed, it should be Python
5. **No script makes architectural decisions**  -  if it requires judgment, it should be an agent

### Decision Criteria

Use this table to decide whether a task should run as an agent or script:

```
┌────────────────────────────────────┬──────────────┬───────────────────┐
│ Characteristic                     │ Agent Work   │ Script Work       │
├────────────────────────────────────┼──────────────┼───────────────────┤
│ Requires judgment/creativity       │ ✅ Yes       │ ❌ No             │
│ Output varies by context           │ ✅ Yes       │ ❌ No             │
│ Cost-sensitive (runs frequently)   │ ❌ No        │ ✅ Yes            │
│ Can be unit tested deterministically│ ❌ No       │ ✅ Yes            │
│ Same input → same output           │ ❌ No        │ ✅ Yes            │
│ Needs codebase AST/reflection      │ ⚠️ Haiku     │ ✅ Python         │
│ Is it a Python standard library op?│ ❌ No        │ ✅ Yes            │
└────────────────────────────────────┴──────────────┴───────────────────┘
```

### Examples

**AGENT WORK** (run via Task tool):
- `architect`  -  reads spec + codebase, reasons about DB schema, FK relationships, invariants
- `implementer`  -  reads spec + tests, writes file body with context-aware patterns
- `reviewer`  -  reads all generated code, reasons about security, perf, style
- `critic`  -  reads test output, reasons about root cause, decides loop vs ship
- `docs-author`  -  reads code + task description, writes comprehensive documentation
- `rollback-agent`  -  reads failure patterns, reasons about which commit to revert

**SCRIPT WORK** (run via Python):
- `codebase_graph.py`  -  AST-scan, extract classes/functions/imports (deterministic)
- `extract_domain_model.py`  -  regex-scan user description for entities (deterministic)
- `auto_patch.py`  -  apply known fixes to common bugs (deterministic)
- `auto_wirer.py`  -  inject imports + function calls into main.py (deterministic)
- `curriculum_check.py`  -  lookup past failures for this task (deterministic)
- `cost_budget.py`  -  estimate tokens for agent dispatch (deterministic)

### Visual Model

```
┌─────────────────────────────────────────────────────────────────┐
│                     Feature Request (Natural Language)           │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  Stage 0: Curriculum    │ (script)
                    │   Check + Scan         │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │ Stage 1: Extract Domain │ (script)
                    │ Model + Cost Gate       │
                    └────────────┬────────────┘
                                 │
             ┌───────────────────▼───────────────────┐
             │    Stage 2: Architect Agent (Sonnet)   │ (agent)
             │  → spec.json (DB schema, relationships)│
             └───────────────────┬───────────────────┘
                                 │
           ┌─────────────────────▼─────────────────────┐
           │  Stage 3: Implementer (H) + Test-Author   │ (agents, parallel)
           │       (S) write code bodies               │
           └──────────────┬──────────────┬──────────────┘
                          │              │
          ┌───────────────▼────┐  ┌──────▼───────────┐
          │ Implementer × N     │  │ Test-Author (S) │
          │ (Haiku, file bodies)│  │ (Sonnet, tests) │
          └───────────────┬────┘  └──────┬───────────┘
                          │              │
                          └──────┬───────┘
                                 │
                    ┌────────────▼────────────┐
                    │ Stage 4: Verify + Patch │ (script)
                    │  (syntax, auto-fixes)   │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │ Stage 5: Reviewer Agent │ (agent)
                    │   (Sonnet, security)    │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │ Stage 5.5: Doubter Agent│ (agent)
                    │ (adversarial pass)      │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │ Stage 6: Auto-Wire      │ (script)
                    │  (inject into main.py)  │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │ Stage 7: Critic Agent   │ (agent)
                    │ (Sonnet, pytest verdict)│
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │ Stage 8: Record + Learn │ (script)
                    │  (refresh graph, beads) │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   Working Code Shipped   │
                    └────────────────────────┘
```

---

## Architecture Overview

### 14-Stage Pipeline

The one-shot-prompting pipeline spans 14 stages, orchestrated by the conducting skill (`SKILL.md`). Stages fall into 4 phases: PLAN, BUILD, VERIFY, SHIP.

```
PHASE 0: PLAN (Stages 0 – 2.7)
├─ Stage 0    : Curriculum check            [SCRIPT]
├─ Stage 0.3  : Predictive failure scan     [SCRIPT]
├─ Stage 0.7  : Legacy-safe gate            [SCRIPT]
├─ Stage 1    : Scan + extract domain       [SCRIPT]
├─ Stage 1.5  : Cost-budget gate            [SCRIPT]
├─ Stage 1.8  : Source-driven doc lookup    [SCRIPT]
├─ Stage 2    : Architect agent → spec.json [AGENT: architect]
├─ Stage 2.5  : Spec review (--review)      [USER]
├─ Stage 2.6  : Incremental slicing         [SCRIPT]
└─ Stage 2.7  : Service-author (invariants) [AGENT: service-author]

PHASE 1: BUILD (Stage 3)
├─ Stage 3    : Implementer × N + Test-Author [AGENTS: implementer, test-author, PARALLEL}
└─ (OR --tdd-strict routes through tdd-cycle skill)

PHASE 2: VERIFY (Stages 4 – 5.9)
├─ Stage 4    : Verify + auto-patch         [SCRIPT]
├─ Stage 5    : Reviewer agent              [AGENT: reviewer, SERIAL]
├─ Stage 5.5  : Doubter agent               [AGENT: doubter, SERIAL]
├─ Stage 5.7  : Cross-agent consistency     [SCRIPT + AGENT: consistency-checker, SAST]
└─ Stage 5.9  : Approval gate webhook       [USER/WEBHOOK]

PHASE 3: SHIP (Stages 6 – 8.5)
├─ Stage 6    : Auto-wire + migration       [SCRIPT: auto_wirer, migration_generator]
├─ Stage 6.5  : Migration (Alembic/Django)  [SCRIPT]
├─ Stage 7    : Critic loop (max 3 iter)    [AGENT: critic, SERIAL, WITH pytest]
├─ Stage 8    : Record + refresh            [SCRIPT: beads_writer, codebase_graph]
└─ Stage 8.5  : Dream (curriculum mine)     [AGENT: memory-propagator, ASYNC]
```

### Agent vs Script Distribution

**13 Agents:**
1. `architect`  -  spec generation from domain model (Sonnet)
2. `implementer`  -  file body generation (Haiku, parallelized ×N)
3. `test-author`  -  test generation (Sonnet)
4. `reviewer`  -  security/perf/style gate (Sonnet)
5. `doubter`  -  adversarial pass (Sonnet)
6. `wirer`  -  inject imports/calls (Haiku)
7. `critic`  -  test verdict + loop decision (Sonnet, multi-iter)
8. `service-author`  -  service generation when invariants exist (Sonnet)
9. `consistency-checker`  -  cross-agent logic validation (Sonnet)
10. `security-scanner`  -  SAST / dependency audit (Sonnet)
11. `docs-author`  -  comprehensive doc generation (Sonnet)
12. `rollback-agent`  -  revert logic + picking commits (Sonnet)
13. `memory-propagator`  -  curriculum update + learning (Sonnet)

**50+ Scripts:**
- Scanning: `codebase_graph.py`, `extract_domain_model.py`, `curriculum_check.py`
- Verification: `verify_syntax.py`, `auto_patch.py`, `security_deep_scan.py`
- Wiring: `auto_wirer.py`, `migration_generator.py`
- Observability: `otel_tracer.py`, `span_propagation.py`
- Cost: `cost_budget.py`, `token_counter.py`
- Learning: `beads_writer.py`, `curriculum_refresh.py`, `failure_detector.py`

### Data Flow

```
Scan / AST Extract
    ↓
  spec.json (agent output)
    ↓
  plan.json (deterministic mapping)
    ↓
  file list (agents generate bodies)
    ↓
  generated files (verify script checks)
    ↓
  patched files (auto-patch)
    ↓
  wired main.py (auto-wire script)
    ↓
  pytest run → test results
    ↓
  critic verdict → loop/ship (agent decision)
    ↓
  beads recorded (curriculum refresh)
```

---

## Agent Dispatching Pattern

### Task Tool Usage

All agents are dispatched via the **Task tool** from the main SKILL.md conducting script. This ensures:
- Isolated execution context (agent can't corrupt parent)
- Cost tracking (Task tool reports tokens)
- Timeout protection (agent can't hang)
- Parallelization (multiple agents can run simultaneously)

### Dispatch Signature

```yaml
# Example: architect agent dispatch
task:
  type: agent
  agent_id: architect
  input:
    domain_model: { entities: [...], relationships: [...] }
    codebase_context: { classes: [...], imports: [...] }
    framework: "django"
    budget: 0.30
  timeout_seconds: 120
  cost_estimate: 0.12
```

### Input/Output Protocol (JSON)

**Agent Input Format:**
```json
{
  "domain_model": {
    "entities": [
      {
        "name": "User",
        "fields": {
          "id": "integer",
          "email": "string"
        }
      }
    ],
    "relationships": [
      {
        "from": "Order",
        "to": "LineItem",
        "type": "has_many"
      }
    ]
  },
  "codebase_context": {
    "language": "python",
    "framework": "django",
    "existing_models": [...],
    "import_root": "myapp"
  },
  "constraints": {
    "budget_usd": 0.30,
    "max_iterations": 3
  }
}
```

**Agent Output Format:**
```json
{
  "status": "success",
  "output": {
    "spec": { "entities": [...], "schema": [...] },
    "reasoning": "Why this design was chosen"
  },
  "confidence": 0.95,
  "cost_actual": 0.12,
  "duration_seconds": 15.3
}
```

### Context Passing Between Agents

Agents run sequentially or in parallel, but **always** hand off data through JSON:

```
architect (Sonnet)
    ↓
    └─→ emits spec.json
        ↓
implementer (Haiku) × N [PARALLEL]
test-author (Sonnet) [PARALLEL]
    ├─→ read spec.json
    ├─→ read codebase context
    └─→ emit file bodies (JSON)
        ↓
reviewer (Sonnet)
    ├─→ reads all generated files
    ├─→ reads spec.json
    └─→ emits review (JSON: findings, severity, fixes)
        ↓
critic (Sonnet)
    ├─→ reads generated files
    ├─→ reads pytest output (from script)
    └─→ emits verdict (JSON: loop/ship)
```

### Parallelization Rules

**Parallel stages (speed up):**
- Stage 3: `implementer × N` + `test-author` run simultaneously
- Stage 5.7: consistency-checker + security-scanner run in parallel
- Stage 8.5: memory-propagator runs async (non-blocking)

**Serial stages (dependency chain):**
- Stage 2 → Stage 3 (architect must finish before implementers start)
- Stage 3 → Stage 4 (code must exist before verify)
- Stage 5 → Stage 5.5 (reviewer must finish before doubter)
- Stage 7 → Stage 8 (all loops must complete before recording)

---

## Deterministic Operations

### Role of Python Scripts

Python scripts are the "muscles" of the system  -  they do I/O-bound scanning, pattern matching, AST traversal, and cost-sensitive wiring. They run in milliseconds; agents run in seconds. The division minimizes token spend while keeping reasoning in Claude.

### When to Use Scripts vs Agents

| Task | Why Script? | Example |
|------|------------|---------|
| Scan 10,000 lines of Python | Deterministic AST walk | `codebase_graph.py` |
| Find all imports in a file | Regex + AST (no judgment) | Extract imports for spec |
| Diff code before/after | Binary comparison | `codebase_diff.py` |
| Apply 4 known bug fixes | Deterministic rule set | `auto_patch.py` |
| Inject import into main.py | Line number + regex | `auto_wirer.py` |
| Estimate tokens for agent call | Tiktoken count | `cost_budget.py` |
| **When SHOULD you use an agent?** | ← Decision requires judgment | Decide what to patch vs ship |

### Common Script Categories

**1. Scanners**  -  Extract structure without judgment
- `codebase_graph.py`  -  AST walk, emit class/function tree
- `curriculum_check.py`  -  lookup past failures for this task
- `extract_domain_model.py`  -  regex entities from description
- `cost_budget.py`  -  estimate tokens

**2. Verifiers**  -  Check correctness deterministically
- `verify_syntax.py`  -  parse Python, check for syntax errors
- `contract_validator.py`  -  check type hints, FK constraints
- `security_deep_scan.py`  -  SAST, SQL injection, secrets patterns

**3. Patchers**  -  Apply known fixes
- `auto_patch.py`  -  fix indentation, missing imports, type hints
- `migrate_syntax.py`  -  Django 3→4, Rails 6→7 migrations

**4. Wirers**  -  Inject into existing files
- `auto_wirer.py`  -  add import, call function in main.py
- `migration_generator.py`  -  emit Alembic/Flyway migration

**5. Recorders**  -  Persist learnings
- `beads_writer.py`  -  record failure + context to `.beads/issues.jsonl`
- `curriculum_refresh.py`  -  update learned patterns
- `failure_detector.py`  -  classify bugs (syntax, logic, missing import)

### Cost Optimization Through Determinism

Script operations are **1000× cheaper** than agent dispatch:
- `codebase_graph.py` on a 10MB codebase: <1s, $0.000
- `architect` agent on same codebase: 15s, $0.12

By moving I/O-bound work to Python, we:
- Reduce token spend from $2/gen to $0.30–0.80/gen
- Speed up wall-clock time (parallel execution while agents think)
- Make failures debuggable (stack traces pinpoint the layer)

---

## Real-World Examples

### Example 1: How Architect Agent Dispatches Spec Generation

**Input:** Domain model extracted by script
```python
domain_model = {
    "entities": [
        {"name": "User", "fields": {...}},
        {"name": "Order", "fields": {...}},
        {"name": "LineItem", "fields": {...}}
    ],
    "relationships": [
        {"from": "Order", "to": "LineItem", "type": "has_many"}
    ]
}
```

**Agent Task Dispatch (from SKILL.md Stage 2):**
```yaml
task:
  agent_id: architect
  input:
    domain_model: $domain_model
    codebase_context: $graph
    framework: "django"
  budget: 0.12
```

**Agent Output (spec.json):**
```json
{
  "entities": [
    {
      "name": "User",
      "table": "user",
      "fields": [
        {"name": "id", "type": "integer", "pk": true},
        {"name": "email", "type": "string", "unique": true}
      ]
    },
    {
      "name": "Order",
      "table": "order",
      "fields": [
        {"name": "id", "type": "integer", "pk": true},
        {"name": "user_id", "type": "integer", "fk": "user.id"}
      ]
    },
    {
      "name": "LineItem",
      "table": "line_item",
      "fields": [
        {"name": "order_id", "type": "integer", "fk": "order.id"}
      ]
    }
  ]
}
```

**Deterministic Follow-up (Stage 2.6):**
Script `scaffold_planner.py` reads `spec.json`, emits `plan.json`:
```json
{
  "files_to_create": [
    {
      "path": "app/models.py",
      "imports": ["from django.db import models"],
      "entities": ["User", "Order", "LineItem"]
    }
  ]
}
```

---

### Example 2: Verify Script Runs Deterministic Checks on Generated Code

**Input:** Generated `models.py` from implementer agent
```python
class User(models.Model):
    email = models.CharField(max_length=255)
    # missing: created_at, updated_at
```

**Deterministic Verification (Stage 4):**
```bash
python verify_syntax.py --file app/models.py
# Output: JSON with findings
{
  "syntax_ok": true,
  "missing_imports": [],
  "violations": [
    {
      "rule": "timestamp_fields_required",
      "severity": "high",
      "line": 1,
      "fix": "Add created_at = models.DateTimeField(auto_now_add=True)"
    }
  ]
}
```

**Auto-Patch (Stage 4, `auto_patch.py`):**
```bash
python auto_patch.py --file app/models.py --violations $violations
# Edits file in-place, adds missing fields
```

**Verification: No Agent Needed**  -  All decisions are rule-based (syntax, FK integrity, required fields).

---

### Example 3: Critic Agent Decides Loop vs Ship

**Input:** Pytest output after implementer generated code
```
FAILED tests/test_models.py::TestOrder::test_line_items
AssertionError: Order.line_items should be QuerySet, got NoneType
```

**Agent Task (Stage 7):**
```yaml
task:
  agent_id: critic
  input:
    generated_files: {...}
    test_output: "FAILED tests/test_models.py::..."
    failure_count: 1
    spec: {...}
  budget: 0.10
```

**Agent Output (Verdict):**
```json
{
  "status": "loop",
  "reasoning": "Missing reverse relation on LineItem.order. Requires implementer re-run.",
  "fix_required": "Add related_name='line_items' to FK field",
  "confidence": 0.98,
  "next_step": "re_run_implementer"
}
```

**Back to Stage 3:** Implementer runs again with critic's feedback in context, fixes the relation.

**Then back to Stage 7:** Critic re-runs, tests pass, verdict is "ship".

---

### Example 4: Memory-Propagator Agent Updates Curriculum

**Input:** Failure patterns from Stage 8 beads recording
```json
{
  "failures": [
    {"pattern": "missing_reverse_relation", "count": 3, "frameworks": ["django"]},
    {"pattern": "unimported_models", "count": 5, "frameworks": ["all"]}
  ]
}
```

**Agent Task (Stage 8.5):**
```yaml
task:
  agent_id: memory-propagator
  input:
    failure_patterns: $failures
    curriculum_path: ".beads/"
    dry_run: false
  timeout: 60
```

**Agent Output (Curriculum Update):**
```json
{
  "curriculum_updated": true,
  "new_learnings": [
    {
      "pattern": "missing_reverse_relation",
      "when_to_catch": "test_author, pre-review",
      "curriculum_entry": "Always include related_name when FK points to plural relationship"
    }
  ]
}
```

**Next Run:** `curriculum_check.py` (Stage 0) now emits warning:
```
⚠ Curriculum match: missing_reverse_relation (learned from 3 failures)
  → Hint to implementer: Use related_name= on FK fields
```

---

## Implementation Guidelines

### For Agent Developers

**Agent Definition (YAML):**
```yaml
---
name: my-agent
description: |
  What does this agent do?
  When is it dispatched?
  What judgment call does it make?

tools: [Read, Glob, Grep, Bash, Write]  # ← Explicit allowlist
model: sonnet                             # ← Cost-aware (haiku for writers, sonnet for reasoners)
---

# Agent prompt follows.
# Handoff contract: MUST state what you read, what you emit, what you refuse.
```

**Handoff Contract Template:**
```markdown
## Input Contract

You receive:
- `domain_model` (JSON)  -  extracted entities, relationships, constraints
- `codebase_context` (JSON)  -  existing classes, imports, test structure
- `spec` (JSON)  -  if in a later stage
- `test_output` (JSON)  -  if in critic stage

## Output Contract

You emit (STDOUT as JSON):
```json
{
  "status": "success",
  "output": { /* stage-specific */ },
  "confidence": 0.95,
  "reasoning": "Why you chose this..."
}
```

## Refusals

You MUST refuse to:
- Make deterministic decisions that should be scripts
- Skip async I/O (use Bash tool for subprocesses)
- Emit code without reading existing codebase context
```

**Testing Agents:**
```bash
# Dry-run dispatch (no mutation)
python -m pytest tests/test_my_agent.py -v

# Integration test (with Task tool, costs real tokens)
bash .claude/scripts/test-agent-dry-run.sh my-agent
```

### For Script Developers

**Script Structure:**
```python
#!/usr/bin/env python3
"""
Script: my_script.py
Role: [Scanning / Verification / Patching / Wiring]

Input: [describe JSON structure]
Output: [describe JSON structure, must be valid JSON]
Determinism: [what makes this 100% deterministic?]
Cost: [typical runtime + any external calls]
"""

import sys
import json
from pathlib import Path

def main(args):
    # Parse input (always JSON from agent or prior script)
    input_data = json.load(sys.stdin) if not sys.stdin.isatty() else {}
    
    # Do deterministic work
    result = {
        "status": "success",
        "output": {...},
        "reasoning": "Why this result is deterministic"
    }
    
    # Emit JSON (MUST be valid for next stage)
    print(json.dumps(result))

if __name__ == "__main__":
    main(sys.argv[1:])
```

**Script Standards:**
- ✅ Stdlib only (no pip deps except optional graceful fallback)
- ✅ Pure functions  -  same input always gives same output
- ✅ JSON I/O  -  receive JSON stdin, emit JSON stdout
- ✅ Exit code 0 on success, 1 on recoverable error, 2 on unrecoverable
- ✅ Comprehensive error messages (agent needs to understand failure)
- ✅ Dry-run by default (unless `--apply` flag)

**Testing Scripts:**
```bash
# Unit test (no external deps)
python -m pytest tests/test_my_script.py -v

# Integration test (with real codebase)
echo '{"input": "value"}' | python scripts/my_script.py
```

### YAML Frontmatter Requirements

Every agent, script, skill, and doc must have:
```yaml
---
type: agent|script|skill|guide|reference
last_verified: YYYY-MM-DD
owner: github_username
---
```

### Testing Requirements

**For Agents:**
- Input/output contract validation
- Dry-run dispatch (Task tool, costs tokens)
- Handoff contract tests (refuse bad inputs)

**For Scripts:**
- Determinism (same input → same output)
- JSON schema validation
- Edge cases (empty input, malformed JSON, missing keys)
- Dry-run vs apply behavior

---

## Common Patterns & Anti-Patterns

### ✅ GOOD: Agent Makes Judgment, Script Optimizes

**Pattern:**
1. Agent reads domain model, reasons about schema
2. Script applies schema to codebase (deterministic)
3. Agent reads generated code, reviews for logic
4. Script auto-patches known issues
5. Script cost: $0.001; Agent cost: $0.12

**Why it works:**
- Expensive reasoning happens once (agent)
- Cheap operations parallelized (scripts)
- Clear separation = clear debugging

**Example:** Architect (agent) decides "this needs denormalization" → Script applies it via raw SQL migration.

---

### ❌ AVOID: Agent Doing Deterministic Computation

**Anti-pattern:**
```
Agent reads spec.json and:
1. Counts entities (should be script)
2. Calculates depth of relationship tree (should be script)
3. Estimates number of tests needed (should be script)
4. Chooses implementation strategy (GOOD  -  agent)
```

**Why it fails:**
- Wastes 3 Claude calls on arithmetic
- Makes agent slower (waiting for Python isn't parallelizable)
- Cost: $0.05 wasted on 3 simple counts

**Fix:** Script emits:
```json
{
  "entity_count": 7,
  "relationship_depth": 3,
  "estimated_test_count": 42
}
```

Agent reads that and makes strategic choice.

---

### ❌ AVOID: Script Making Architectural Decisions

**Anti-pattern:**
```python
# auto_patch.py
if "User" in entities and "Order" in entities:
    # Decide to add denormalization
    sql += "ALTER TABLE order ADD COLUMN total_amount..."
```

**Why it fails:**
- Script has no context (why denormalize? Is it right for this schema?)
- Can't adapt to new patterns
- Makes errors that an agent would catch

**Fix:** Architect agent decides denormalization is needed → Script applies it deterministically.

---

### ✅ GOOD: Clear Separation of Concerns

**Pattern:**
```
Script Layer:          Agent Layer:
─────────────          ────────────
scan code              reason about schema
extract imports        review for logic
apply patches          decide loop vs ship
wire files             assess risk
calculate cost         evaluate trade-offs
```

**Contracts are clear:**
- Script says: "I found 3 import violations"
- Agent says: "Here's why we need to fix them"
- Script says: "Applied the fixes"
- Agent says: "Ready to ship" or "Loop"

---

## Integration Across Workstreams

The Agent-First principle is demonstrated across all workstreams:

### WS1  -  Observability (OTel Span Propagation)

- **Agent stages** emit attribute spans (what they decided)
- **Script stages** emit duration spans (how long they took)
- **OTel tracer** correlates both, traces end-to-end latency

```
pipeline_start
├─ curriculum_check (script, 50ms, 0 tokens)
├─ architect (agent, 15s, $0.12 tokens)
├─ implementer×3 (agent, 12s, $0.25 tokens, PARALLEL)
├─ verify (script, 2s, 0 tokens)
└─ pipeline_end (total 42s, $0.37 cost)
```

### WS2  -  Docs Drift Detection

- **docs-author agent** reads code, writes comprehensive docs
- **codebase_diff script** compares old docs vs new code
- **drift detector** flags where docs fell behind
- **docs-author agent** (feedback loop) rewrites stale sections

**Pattern:** Agent → Script → Agent (bidirectional reasoning)

### WS3  -  Rollback & Failure Handling

- **failure_detector script** classifies error type (syntax, logic, missing)
- **rollback-agent** reasons: "Should we revert this commit or fix it?"
- **rollback script** executes the decision (revert vs patch)
- **curriculum_update** records learning for next time

**Pattern:** Script detects, Agent decides, Script executes, Script learns

### WS4  -  Predictive Failures (Embedding Cache)

- **curriculum_check script** looks up past failures (deterministic lookup)
- **embedding cache** (Redis/MCP) caches failure vectors
- **memory-propagator agent** reads cache, updates curriculum
- **Stage 0.3 script** emits predictive warnings

**Pattern:** Script optimizes lookup, Agent optimizes learning

### WS5  -  awesome-ai-apps Integration

The awesome-ai-apps workstream demonstrates **all patterns**:
- Agent generates scaffold → Script wires it → Script verifies it
- Agent reviews code → Script patches known issues
- Script calculates cost → Agent decides budget
- Agent documents → Script diffs → Agent refines

---

## References & Links

### Core Architecture Docs

- **[tier35-agentic.md](../tier35-agentic.md)**  -  The agentic restructure (when this started)
- **[path-to-10.md](../path-to-10.md)**  -  Roadmap to production (11 pillars)
- **[IMPLEMENTATION_STATUS.md](../../IMPLEMENTATION_STATUS.md)**  -  What's built vs planned
- **[CHANGELOG.md](../../CHANGELOG.md)**  -  Release history + features per tier

### Agent & Script Definitions

- **[.claude/agents/](../../.claude/agents/)**  -  All 13 agent definitions
  - `architect.md`, `implementer.md`, `test-author.md`, `reviewer.md`, etc.
- **[scripts/](../../scripts/)**  -  All deterministic operations
  - `codebase_graph.py`, `auto_patch.py`, `auto_wirer.py`, etc.

### Pipeline Execution

- **[skills/one-shot-generate/SKILL.md](../../skills/one-shot-generate/SKILL.md)**  -  The conducting script (entry point)
- **[skills/one-shot-generate/stages/](../../skills/one-shot-generate/stages/)**  -  Stage files (plan.md, build.md, verify.md, ship.md)
- **[commands/one-shot.md](../../commands/one-shot.md)**  -  Slash command definition

### Observability & Cost

- **[docs/observability/span-propagation.md](../observability/span-propagation.md)**  -  OTel tracing architecture
- **[docs/observability/README.md](../observability/README.md)**  -  Observability index

### Testing & Validation

- **[tests/](../../tests/)**  -  701 tests across all stages
- **[COMPREHENSIVE_HARNESS_REPORT.md](../../COMPREHENSIVE_HARNESS_REPORT.md)**  -  Test results + coverage

### Navigation

- **[CLAUDE.md](../../CLAUDE.md)**  -  Plugin router (this file links to other docs)
- **[AUDIT_ME_FIRST.md](../../AUDIT_ME_FIRST.md)**  -  Where to start auditing

---

**Last Verified:** 2026-05-25  
**Owner:** claude  
**Type:** guide
