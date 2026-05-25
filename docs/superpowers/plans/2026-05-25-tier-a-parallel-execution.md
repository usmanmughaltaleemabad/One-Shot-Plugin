# Path to 10/10: TIER A Parallel Execution Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Dispatch fresh subagent per task, review spec compliance first, then code quality. All 4 workstreams run in parallel using Task tool (not sequential).

**Goal:** Execute all 4 TIER A items (OTel monitoring, docs drift agent, rollback agent, predictive failure detection) in parallel + integrate 3 awesome-ai-apps patterns, increasing plugin quality from ~6.5/10 to 9.0+ across observability, autonomy, and multi-agent orchestration.

**Architecture:**
- **Workstream 1 (OTel Monitoring):** Jaeger local setup, span propagation across pipeline stages 0-8, observability dashboard docs
- **Workstream 2 (Docs Drift):** Watch codebase for entity/schema changes, auto-trigger docs-author agent, land drafts in .tmp/ for review
- **Workstream 3 (Rollback Agent):** Detect failure patterns from critic verdicts, auto-revert .osp.bak files on N consecutive failures, wire git_safety.py
- **Workstream 4 (Predictive Failures):** Replace Jaccard with cosine similarity using embeddings, hard-warn when task similarity > 0.8 to known failures
- **Integration:** OTel spans capture multi-agent orchestration; rollback uses OTel traces; docs drift updates observability docs; awesome-ai-apps patterns enhance architect, curator, and learnings propagation

**Tech Stack:** OpenTelemetry + Jaeger, sentence-transformers (optional dep), Python AST parsing (codebase_diff.py), git safety checks, embedding cache (SQLite)

---

## Workstream 1: Real-Time OTel Monitoring (2-3 days)

### Files
- Create: `docs/observability/jaeger-setup.md` (docker-compose + dashboard)
- Create: `docs/observability/span-propagation.md` (trace architecture)
- Create: `docs/observability/metrics-dashboard.md` (example queries)
- Create: `.claude/agents/otel-monitor.md` (agent definition)
- Create: `scripts/otel_tracer.py` (OpenTelemetry instrumentation)
- Create: `scripts/trace_context.py` (span context propagation helper)
- Modify: `skills/one-shot-generate/SKILL.md` (inject otel_tracer.py calls in pipeline)
- Modify: `.claude-plugin/plugin.json` (add OTel setup instructions to description)
- Create: `tests/test_observability_traces.py` (trace validation tests)

### Tasks

#### Task 1: Wire Jaeger locally via docker-compose

**Files:**
- Create: `docs/observability/jaeger-setup.md`
- Create: `.docker/docker-compose.yml` (Jaeger + Prometheus)

- [ ] **Step 1: Create docker-compose.yml for Jaeger**

```yaml
version: '3.8'
services:
  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "6831:6831/udp"
      - "16686:16686"
    environment:
      COLLECTOR_ZIPKIN_HTTP_PORT: 9411
```

- [ ] **Step 2: Create Jaeger setup guide doc**

Document:
- `docker-compose up -d` to start Jaeger
- Access dashboard at http://localhost:16686
- Expected services: one-shot-prompting, architect, implementer, reviewer, critic

- [ ] **Step 3: Commit docker-compose and docs**

```bash
git add .docker/docker-compose.yml docs/observability/jaeger-setup.md
git commit -m "infra: add Jaeger docker-compose for local tracing"
```

#### Task 2: Implement OpenTelemetry instrumentation

**Files:**
- Create: `scripts/otel_tracer.py`
- Create: `scripts/trace_context.py`

- [ ] **Step 1: Write otel_tracer.py with decorator pattern**

```python
import json
from opentelemetry import trace, metrics
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource

def init_tracer(service_name: str):
    jaeger_exporter = JaegerExporter(
        agent_host_name="localhost",
        agent_port=6831,
    )
    trace.set_tracer_provider(
        TracerProvider(resource=Resource.create({SERVICE_NAME: service_name}))
    )
    trace.get_tracer_provider().add_span_processor(
        SimpleSpanProcessor(jaeger_exporter)
    )
    return trace.get_tracer(__name__)

def trace_stage(stage_name: str):
    def decorator(func):
        def wrapper(*args, **kwargs):
            tracer = trace.get_tracer(__name__)
            with tracer.start_as_current_span(stage_name) as span:
                span.set_attribute("stage", stage_name)
                result = func(*args, **kwargs)
                span.set_attribute("status", "success")
                return result
        return wrapper
    return decorator
```

- [ ] **Step 2: Write trace_context.py for context propagation**

```python
from opentelemetry.trace import set_span_in_context
from opentelemetry import trace
import contextvars

# Pass context across Task boundaries
trace_context = contextvars.ContextVar('trace_context', default=None)

def capture_context():
    return trace.get_current_span().get_span_context()

def restore_context(ctx):
    return set_span_in_context(ctx)
```

- [ ] **Step 3: Write tests for trace initialization**

```python
def test_tracer_initializes():
    tracer = init_tracer("test-service")
    assert tracer is not None
    
def test_span_created_and_exported():
    tracer = init_tracer("test-service")
    with tracer.start_as_current_span("test-span") as span:
        span.set_attribute("test", "value")
    # Verify span exported to Jaeger (manual: check localhost:16686)
```

- [ ] **Step 4: Commit instrumentation code**

```bash
git add scripts/otel_tracer.py scripts/trace_context.py tests/test_observability_traces.py
git commit -m "feat(observability): add OpenTelemetry instrumentation + context propagation"
```

#### Task 3: Wire span propagation through pipeline stages 0-8

**Files:**
- Modify: `skills/one-shot-generate/SKILL.md`
- Create: `docs/observability/span-propagation.md`

- [ ] **Step 1: Document span propagation strategy**

Create `docs/observability/span-propagation.md`:
```markdown
# Span Propagation Through Pipeline

## Stages and Spans

- **Stage 0:** curriculum → span "curriculum_check"
- **Stage 1:** scan → span "extract_domain_model"
- **Stage 2:** architect → span "generate_spec"
- **Stage 3:** implementer + test-author → span "write_code" (parallel)
- **Stage 4:** verify + patch → span "verify_and_patch"
- **Stage 5:** reviewer → span "security_review"
- **Stage 6:** wire → span "auto_wire_main"
- **Stage 7:** critic → span "run_tests"
- **Stage 8:** record → span "record_beads"

## Context Propagation

Each Task call carries trace context via environment variable `OTEL_TRACE_CONTEXT`.
```

- [ ] **Step 2: Modify SKILL.md to emit span setup in ! injection block**

In `skills/one-shot-generate/SKILL.md`, add to the `!` block after existing imports:

```python
import sys
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from otel_tracer import init_tracer, trace_stage
from trace_context import capture_context, restore_context

# Initialize tracer for this invocation
tracer = init_tracer("one-shot-generate")
```

- [ ] **Step 3: Wrap each stage call with @trace_stage decorator**

In SKILL.md stage dispatch, change:
```python
stage_result = run_stage("curriculum", ...)
```
to:
```python
@trace_stage("curriculum")
def run_curriculum():
    return run_stage("curriculum", ...)

stage_result = run_curriculum()
```

- [ ] **Step 4: Commit and test end-to-end**

```bash
git add skills/one-shot-generate/SKILL.md docs/observability/span-propagation.md
git commit -m "feat(observability): wire span propagation through pipeline stages 0-8"
```

- [ ] **Step 5: Run smoke test to verify spans flow**

```bash
bash .claude/scripts/smoke-test.sh
# Manually verify Jaeger dashboard shows traces:
# - Open http://localhost:16686
# - Search for service: one-shot-generate
# - Should see traces with stages 0-8 as child spans
```

#### Task 4: Create observability dashboard example doc

**Files:**
- Create: `docs/observability/metrics-dashboard.md`

- [ ] **Step 1: Document Jaeger dashboard queries**

```markdown
# Observability Dashboard Examples

## Query 1: Pipeline Latency by Stage

In Jaeger:
```
service.name = "one-shot-generate"
span.kind = "INTERNAL"
```

Look for:
- curriculum_check: ~100ms
- extract_domain_model: ~500ms
- generate_spec: ~3000ms (architect agent)
- write_code: ~5000ms (implementer + test-author parallel)
- verify_and_patch: ~1000ms
- security_review: ~2000ms
- auto_wire_main: ~500ms
- run_tests: ~2000ms
- record_beads: ~100ms

**Total expected: 14-15s per generation**

## Query 2: Critical Path

Spans with `span.status = "ERROR"` or `span.duration > 5000ms`:
- Identify bottlenecks
- Find failures

## Query 3: Parallel Task Efficiency

Child span count under "write_code":
- Expected: 2+ (implementer + test-author)
- Measure: actual parallelism vs sequential
```

- [ ] **Step 2: Commit dashboard docs**

```bash
git add docs/observability/metrics-dashboard.md
git commit -m "docs(observability): add Jaeger dashboard query examples"
```

---

## Workstream 2: Docs Drift Agent (3-5 days)

### Files
- Create: `.claude/agents/docs-author.md` (agent definition)
- Create: `skills/docs-drift/SKILL.md` (skill dispatcher)
- Create: `scripts/codebase_diff.py` (AST-based entity change detection)
- Create: `scripts/docs_diff_evaluator.py` (compare old vs proposed docs)
- Create: `tests/test_docs_drift.py` (drift detection tests)
- Modify: `.claude/hooks/session-start.sh` (register docs-drift watch)
- Create: `.tmp/docs-author-drafts/` (staging for human review)

### Tasks

#### Task 1: Build codebase_diff.py entity scanner

**Files:**
- Create: `scripts/codebase_diff.py`

- [ ] **Step 1: Write AST parser for entity changes**

```python
import ast
import json
from pathlib import Path
from typing import dict, list

def extract_classes_and_functions(code: str) -> dict:
    tree = ast.parse(code)
    entities = {"classes": [], "functions": [], "imports": []}
    
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            entities["classes"].append({
                "name": node.name,
                "methods": [m.name for m in node.body if isinstance(m, ast.FunctionDef)],
                "bases": [ast.unparse(b) for b in node.bases],
            })
        elif isinstance(node, ast.FunctionDef):
            if not any(isinstance(p, ast.ClassDef) for p in ast.walk(tree)):
                entities["functions"].append({
                    "name": node.name,
                    "params": [arg.arg for arg in node.args.args],
                })
        elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
            entities["imports"].append(ast.unparse(node))
    
    return entities

def scan_codebase(root: Path) -> dict:
    all_entities = {}
    for py_file in root.rglob("*.py"):
        try:
            code = py_file.read_text()
            entities = extract_classes_and_functions(code)
            all_entities[str(py_file.relative_to(root))] = entities
        except Exception as e:
            print(f"Error parsing {py_file}: {e}")
    return all_entities

def detect_changes(old_state: dict, new_state: dict) -> dict:
    changes = {
        "added_classes": [],
        "removed_classes": [],
        "added_functions": [],
        "removed_functions": [],
        "modified_classes": [],
    }
    
    old_classes = {e.get("name") for f in old_state.values() for e in f.get("classes", [])}
    new_classes = {e.get("name") for f in new_state.values() for e in f.get("classes", [])}
    
    changes["added_classes"] = list(new_classes - old_classes)
    changes["removed_classes"] = list(old_classes - new_classes)
    
    # Similar for functions...
    
    return changes

if __name__ == "__main__":
    import sys
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    state = scan_codebase(root)
    print(json.dumps(state, indent=2))
```

- [ ] **Step 2: Write tests for entity detection**

```python
def test_extract_classes():
    code = '''
class User:
    def __init__(self, name):
        self.name = name
    def get_name(self):
        return self.name
'''
    entities = extract_classes_and_functions(code)
    assert len(entities["classes"]) == 1
    assert entities["classes"][0]["name"] == "User"
    assert "get_name" in entities["classes"][0]["methods"]

def test_detect_added_class():
    old = {"file.py": {"classes": [], "functions": []}}
    new = {"file.py": {"classes": [{"name": "NewClass", "methods": []}], "functions": []}}
    changes = detect_changes(old, new)
    assert "NewClass" in changes["added_classes"]
```

- [ ] **Step 3: Commit diff detector**

```bash
git add scripts/codebase_diff.py tests/test_docs_drift.py
git commit -m "feat(docs-drift): add AST-based entity change detector"
```

#### Task 2: Create docs-author agent definition

**Files:**
- Create: `.claude/agents/docs-author.md`

- [ ] **Step 1: Write agent definition**

```markdown
---
name: docs-author
description: Automatically generate documentation updates when codebase entities change
trigger: on_codebase_diff
tools: Read, Write, Edit, Grep
model: sonnet
---

# Docs Author Agent

## Trigger

When `scripts/codebase_diff.py` detects added/removed/modified classes or functions, dispatch this agent.

**Input:**
```json
{
  "changes": {
    "added_classes": ["Cart", "LineItem"],
    "removed_classes": [],
    "added_functions": ["calculate_total"]
  },
  "codebase_root": "/path/to/project",
  "docs_root": "/path/to/docs",
  "files_touched": ["src/models.py", "src/services.py"]
}
```

## Workflow

1. Read the files that changed (via `files_touched`)
2. Extract docstrings, signatures, purpose
3. Update affected README, API docs, entity diagrams
4. **Write drafts to `.tmp/docs-author-drafts/` for human review**
5. Report proposed changes

## Example

Input: Added classes `Cart`, `LineItem` to `src/models.py`
Output:
- `.tmp/docs-author-drafts/api-entities-update.md` (proposed entity doc changes)
- `.tmp/docs-author-drafts/schema-diagram-update.md` (proposed ER diagram changes)

Human then reviews and approves before auto-commit.
```

- [ ] **Step 2: Commit agent definition**

```bash
git add .claude/agents/docs-author.md
git commit -m "feat(agents): add docs-author agent for drift detection"
```

#### Task 3: Create docs-drift skill dispatcher

**Files:**
- Create: `skills/docs-drift/SKILL.md`

- [ ] **Step 1: Write SKILL.md dispatcher**

```yaml
---
type: skill
name: docs-drift
description: Detect codebase changes and auto-generate documentation updates
trigger: manual or scheduled
tools: Task, Read, Write
model: haiku
---

# Docs Drift — Automatic Documentation Updates

## Usage

```bash
/docs-drift @./my-project
```

## What it does

1. Scan codebase for class/function definitions
2. Compare against last snapshot (stored in `.beads/docs-state.json`)
3. If changes detected:
   - Dispatch **docs-author agent** (sonnet) to generate updates
   - Write proposed drafts to `.tmp/docs-author-drafts/`
   - Print report: "3 classes added, 1 removed → update docs?"
4. Human reviews `.tmp/docs-author-drafts/` and approves
5. Auto-commit changes

## Implementation

! python scripts/codebase_diff.py --root @. --output .beads/docs-state.json --compare True

```

- [ ] **Step 2: Implement the skill**

Create `skills/docs-drift/SKILL.md` with full implementation (80-100 lines).

- [ ] **Step 3: Write tests for skill**

```python
def test_docs_drift_detects_added_entity():
    # Create test codebase with added class
    # Run skill
    # Assert .tmp/docs-author-drafts/ contains proposed update
```

- [ ] **Step 4: Commit skill**

```bash
git add skills/docs-drift/SKILL.md tests/test_docs_drift.py
git commit -m "feat(skills): add docs-drift skill for automatic doc updates"
```

#### Task 4: Wire docs-drift hook to session-start

**Files:**
- Modify: `.claude/hooks/session-start.sh`

- [ ] **Step 1: Add docs-drift watch to session-start**

In `.claude/hooks/session-start.sh`, add:

```bash
# Watch for docs drift
if [ -f "scripts/codebase_diff.py" ]; then
    echo "[Hook] Running docs-drift check..."
    python scripts/codebase_diff.py --root . --output .beads/docs-state.json --compare True
fi
```

- [ ] **Step 2: Test hook execution**

```bash
bash .claude/hooks/session-start.sh
# Should emit: "[Hook] Running docs-drift check..."
```

- [ ] **Step 3: Commit hook modification**

```bash
git add .claude/hooks/session-start.sh
git commit -m "infra(hooks): wire docs-drift check to session-start"
```

---

## Workstream 3: Autonomous Rollback Agent (3-5 days)

### Files
- Create: `.claude/agents/rollback-agent.md` (agent definition)
- Create: `scripts/git_safety.py` (safe git operations)
- Create: `scripts/rollback.py` (rollback implementation)
- Create: `scripts/failure_detector.py` (track consecutive failures)
- Create: `tests/test_rollback.py` (rollback tests)
- Modify: `skills/one-shot-generate/SKILL.md` (wire --rollback flag)
- Create: `docs/rollback-strategy.md` (rollback docs)

### Tasks

#### Task 1: Build git_safety.py for safe operations

**Files:**
- Create: `scripts/git_safety.py`

- [ ] **Step 1: Write git safety wrapper**

```python
import subprocess
import os
from pathlib import Path

def git_stash() -> bool:
    """Stash uncommitted changes safely."""
    result = subprocess.run(
        ["git", "stash"],
        capture_output=True,
        text=True,
    )
    return result.returncode == 0

def git_apply_backup(backup_path: Path) -> bool:
    """Apply .osp.bak file safely."""
    if not backup_path.exists():
        return False
    
    target = backup_path.with_suffix("")
    try:
        target.write_text(backup_path.read_text())
        return True
    except Exception as e:
        print(f"Error applying backup: {e}")
        return False

def git_commit_safe(message: str, files: list[str]) -> bool:
    """Commit with safety checks."""
    # Verify files exist
    for f in files:
        if not Path(f).exists():
            return False
    
    result = subprocess.run(
        ["git", "add"] + files,
        capture_output=True,
    )
    if result.returncode != 0:
        return False
    
    result = subprocess.run(
        ["git", "commit", "-m", message],
        capture_output=True,
    )
    return result.returncode == 0
```

- [ ] **Step 2: Write tests for git operations**

```python
def test_git_stash_succeeds(tmp_git_repo):
    # Create uncommitted file
    # Call git_stash()
    # Assert git status shows clean tree
```

- [ ] **Step 3: Commit git safety module**

```bash
git add scripts/git_safety.py tests/test_rollback.py
git commit -m "feat(scripts): add git_safety.py for safe rollback operations"
```

#### Task 2: Build failure_detector.py to track patterns

**Files:**
- Create: `scripts/failure_detector.py`

- [ ] **Step 1: Write failure tracking logic**

```python
import json
from pathlib import Path

def load_failure_state() -> dict:
    """Load failure tracking state from .beads/failures.jsonl"""
    failures = {"consecutive_failures": 0, "last_failing_spec": None}
    state_file = Path(".beads/failures.jsonl")
    
    if state_file.exists():
        lines = state_file.read_text().strip().split("\n")
        if lines:
            failures = json.loads(lines[-1])
    
    return failures

def record_failure(spec_hash: str):
    """Record a failure and increment counter."""
    state = load_failure_state()
    state["consecutive_failures"] += 1
    state["last_failing_spec"] = spec_hash
    
    state_file = Path(".beads/failures.jsonl")
    state_file.write_text(json.dumps(state) + "\n")
    
    return state["consecutive_failures"]

def reset_failure_counter():
    """Reset on success."""
    state = {"consecutive_failures": 0, "last_failing_spec": None}
    Path(".beads/failures.jsonl").write_text(json.dumps(state) + "\n")

def should_trigger_rollback(threshold: int = 3) -> bool:
    """Check if consecutive failures exceed threshold."""
    state = load_failure_state()
    return state["consecutive_failures"] >= threshold
```

- [ ] **Step 2: Write tests for failure tracking**

```python
def test_failure_counter_increments():
    reset_failure_counter()
    count = record_failure("hash1")
    assert count == 1
    count = record_failure("hash1")
    assert count == 2

def test_rollback_triggered_at_threshold():
    reset_failure_counter()
    for _ in range(3):
        record_failure("hash1")
    assert should_trigger_rollback(threshold=3) == True
```

- [ ] **Step 3: Commit failure detector**

```bash
git add scripts/failure_detector.py
git commit -m "feat(scripts): add failure_detector.py for autonomous rollback trigger"
```

#### Task 3: Implement rollback.py orchestrator

**Files:**
- Create: `scripts/rollback.py`

- [ ] **Step 1: Write rollback orchestrator**

```python
import sys
from pathlib import Path
from git_safety import git_apply_backup, git_stash, git_commit_safe
from failure_detector import should_trigger_rollback, reset_failure_counter

def execute_rollback():
    """Rollback to last successful .osp.bak state."""
    backup_dir = Path(".osp.bak")
    
    if not backup_dir.exists():
        print("No backup found (.osp.bak)")
        return False
    
    # Stash uncommitted changes
    if not git_stash():
        print("Failed to stash changes")
        return False
    
    # Apply all .*.bak files
    success = True
    for bak_file in backup_dir.glob("**/.*bak"):
        if not git_apply_backup(bak_file):
            success = False
            print(f"Failed to apply {bak_file}")
    
    if success:
        reset_failure_counter()
        print("Rollback successful")
    
    return success

if __name__ == "__main__":
    if should_trigger_rollback(threshold=3):
        execute_rollback()
    else:
        print("Rollback not triggered (failures < threshold)")
```

- [ ] **Step 2: Write rollback end-to-end test**

```python
def test_rollback_restores_backup(tmp_path):
    # Create file with content
    # Save backup (.bak)
    # Modify file
    # Call execute_rollback()
    # Assert file restored to backup state
```

- [ ] **Step 3: Commit rollback orchestrator**

```bash
git add scripts/rollback.py
git commit -m "feat(scripts): add rollback.py orchestrator for autonomous recovery"
```

#### Task 4: Wire --rollback flag to SKILL.md

**Files:**
- Modify: `skills/one-shot-generate/SKILL.md`
- Create: `docs/rollback-strategy.md`

- [ ] **Step 1: Add --rollback flag documentation**

In `skills/one-shot-generate/SKILL.md` header, add:

```yaml
# New flag
--rollback     Enable autonomous rollback on N consecutive failures (N=3 default)
```

- [ ] **Step 2: Add rollback logic to SKILL.md ! block**

```python
# After existing imports
from scripts.failure_detector import should_trigger_rollback, record_failure, reset_failure_counter
from scripts.rollback import execute_rollback

# In main SKILL logic, after critic verdict:
if should_trigger_rollback(threshold=3):
    print("[AUTO-ROLLBACK] N consecutive failures detected. Rolling back...")
    execute_rollback()
else:
    if verdict == "SHIP":
        reset_failure_counter()
    else:
        record_failure(spec_hash)
```

- [ ] **Step 3: Create rollback strategy documentation**

```markdown
# Autonomous Rollback Strategy

## When to Trigger

- Critic verdict: LOOP (failure to pass tests)
- Consecutive failures: N ≥ 3 (default)
- Spec unstable: critic loop exceeded max iterations

## What Happens

1. Stash uncommitted changes (`git stash`)
2. Apply `.osp.bak` files (last successful generation snapshot)
3. Reset failure counter on success
4. Emit success report

## Disabling Rollback

```bash
/one-shot "..." @./project --rollback=false
```
```

- [ ] **Step 4: Commit and test**

```bash
git add skills/one-shot-generate/SKILL.md docs/rollback-strategy.md
git commit -m "feat(rollback): wire autonomous rollback to SKILL.md with --rollback flag"
```

---

## Workstream 4: Predictive Failure Detection (1 week)

### Files
- Create: `scripts/embedding_cache.py` (sentence-transformers wrapper)
- Create: `scripts/curriculum_v2.py` (cosine similarity curriculum)
- Create: `scripts/failure_predictor.py` (similarity thresholding)
- Create: `tests/test_predictive_failures.py` (prediction tests)
- Modify: `skills/one-shot-generate/SKILL.md` (wire failure predictor to stage 0)
- Create: `.beads/predictions.jsonl` (prediction accuracy tracking)
- Create: `docs/predictive-failures.md` (feature docs)

### Tasks

#### Task 1: Build embedding_cache.py with optional deps

**Files:**
- Create: `scripts/embedding_cache.py`

- [ ] **Step 1: Write embedding cache module**

```python
import json
import sqlite3
from pathlib import Path
from typing import list, float

CACHE_DB = Path(".beads/embedding_cache.db")

def init_cache():
    """Initialize SQLite cache for embeddings."""
    conn = sqlite3.connect(str(CACHE_DB))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS embeddings (
            task_text TEXT PRIMARY KEY,
            embedding BLOB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def get_embedding(task_text: str) -> list[float]:
    """Get embedding from cache or compute it."""
    # Try cache first
    conn = sqlite3.connect(str(CACHE_DB))
    cursor = conn.execute("SELECT embedding FROM embeddings WHERE task_text = ?", (task_text,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return json.loads(row[0])
    
    # Compute embedding
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer("all-MiniLM-L6-v2")
        embedding = model.encode(task_text).tolist()
        
        # Cache it
        conn = sqlite3.connect(str(CACHE_DB))
        conn.execute(
            "INSERT OR REPLACE INTO embeddings (task_text, embedding) VALUES (?, ?)",
            (task_text, json.dumps(embedding))
        )
        conn.commit()
        conn.close()
        
        return embedding
    except ImportError:
        # Fallback to Jaccard similarity if sentence-transformers not installed
        return None

def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    import math
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a ** 2 for a in vec1))
    norm2 = math.sqrt(sum(b ** 2 for b in vec2))
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)
```

- [ ] **Step 2: Write tests for embedding cache**

```python
def test_embedding_cache_stores_and_retrieves():
    init_cache()
    text = "add user authentication"
    embedding = get_embedding(text)
    assert embedding is not None
    assert len(embedding) > 0
    
    # Second call should hit cache
    embedding2 = get_embedding(text)
    assert embedding == embedding2

def test_cosine_similarity():
    vec1 = [1, 0, 0]
    vec2 = [1, 0, 0]
    assert cosine_similarity(vec1, vec2) == 1.0
    
    vec3 = [0, 1, 0]
    assert cosine_similarity(vec1, vec3) == 0.0
```

- [ ] **Step 3: Commit embedding cache**

```bash
git add scripts/embedding_cache.py tests/test_predictive_failures.py
git commit -m "feat(ml): add embedding_cache.py with optional sentence-transformers support"
```

#### Task 2: Build curriculum_v2.py with cosine similarity

**Files:**
- Create: `scripts/curriculum_v2.py`

- [ ] **Step 1: Write curriculum v2 module**

```python
import json
from pathlib import Path
from embedding_cache import get_embedding, cosine_similarity

def load_curriculum() -> list[dict]:
    """Load failure curriculum from .beads/curriculum.jsonl"""
    curriculum = []
    path = Path(".beads/curriculum.jsonl")
    
    if path.exists():
        for line in path.read_text().strip().split("\n"):
            if line:
                curriculum.append(json.loads(line))
    
    return curriculum

def find_similar_failures(task_text: str, threshold: float = 0.8) -> list[dict]:
    """Find similar failures in curriculum using cosine similarity."""
    curriculum = load_curriculum()
    task_embedding = get_embedding(task_text)
    
    if task_embedding is None:
        # Fallback to text matching
        return [item for item in curriculum if task_text.lower() in item.get("task_text", "").lower()]
    
    similar = []
    for item in curriculum:
        item_embedding = get_embedding(item.get("task_text", ""))
        if item_embedding is None:
            continue
        
        sim = cosine_similarity(task_embedding, item_embedding)
        if sim >= threshold:
            similar.append({
                **item,
                "similarity_score": sim,
            })
    
    return sorted(similar, key=lambda x: x["similarity_score"], reverse=True)

def predict_failure(task_text: str) -> dict:
    """Predict if task will fail based on curriculum."""
    similar = find_similar_failures(task_text, threshold=0.8)
    
    if similar:
        # Get most similar failure
        failure = similar[0]
        return {
            "will_fail": True,
            "reason": failure.get("reason", "Unknown"),
            "similarity": failure["similarity_score"],
            "mitigation": failure.get("mitigation", "Try --templated fallback"),
        }
    
    return {"will_fail": False, "reason": "No similar failures found"}
```

- [ ] **Step 2: Write curriculum_v2 tests**

```python
def test_find_similar_failures():
    # Create curriculum with one failure
    # Add "add user auth" → "failed at validator stage"
    # Query "add authentication" 
    # Should find similarity > 0.8
    
def test_predict_failure_triggers_warning():
    # Setup curriculum with known failure
    # Query similar task
    # Assert prediction says "will_fail": True
```

- [ ] **Step 3: Commit curriculum_v2**

```bash
git add scripts/curriculum_v2.py
git commit -m "feat(ml): add curriculum_v2.py with cosine similarity prediction"
```

#### Task 3: Build failure_predictor.py with hard warnings

**Files:**
- Create: `scripts/failure_predictor.py`

- [ ] **Step 1: Write failure predictor**

```python
from curriculum_v2 import predict_failure

def check_task_safety(task_text: str) -> tuple[bool, str]:
    """Check if task is likely to fail; emit hard warning if so."""
    prediction = predict_failure(task_text)
    
    if prediction["will_fail"]:
        warning = f"""
⚠️  HARD WARNING: High similarity (>{prediction.get('similarity', 0.8):.1%}) to known failure

Reason: {prediction['reason']}
Mitigation: {prediction['mitigation']}

Consider:
1. --review flag to manually validate spec before BUILD
2. --templated fallback if agentic generation unstable
3. --budget=0.50 for iterative refinement

Continue? [y/N]
"""
        return False, warning
    
    return True, "Task appears safe; proceeding."

if __name__ == "__main__":
    import sys
    task = sys.argv[1] if len(sys.argv) > 1 else "test"
    safe, msg = check_task_safety(task)
    print(msg)
    sys.exit(0 if safe else 1)
```

- [ ] **Step 2: Write predictor tests**

```python
def test_hard_warning_emitted_for_similar_failure():
    # Setup curriculum with failure
    # Call check_task_safety with similar task
    # Assert returns False and warning message contains task similarity
    
def test_no_warning_for_novel_task():
    # Clear curriculum
    # Call check_task_safety with novel task
    # Assert returns True
```

- [ ] **Step 3: Commit predictor**

```bash
git add scripts/failure_predictor.py
git commit -m "feat(safety): add failure_predictor.py with hard warnings for risky tasks"
```

#### Task 4: Wire predictor to stage 0 of SKILL.md

**Files:**
- Modify: `skills/one-shot-generate/SKILL.md`
- Create: `docs/predictive-failures.md`

- [ ] **Step 1: Add predictor call to SKILL.md stage 0**

In `skills/one-shot-generate/SKILL.md`, after curriculum check:

```python
from scripts.failure_predictor import check_task_safety

# Stage 0: Curriculum + Predictive Check
safe, warning = check_task_safety(feature_request)
if not safe:
    print(warning)
    # User must confirm to continue (via interactive prompt or --force flag)
```

- [ ] **Step 2: Create predictive failures documentation**

```markdown
# Predictive Failure Detection

## How It Works

1. **Curriculum Learning:** Track all past failures in `.beads/curriculum.jsonl`
2. **Embedding:** Convert task text to semantic embedding (sentence-transformers)
3. **Similarity Search:** Find similar failures using cosine similarity
4. **Hard Warning:** If similarity > 80%, emit warning and ask for confirmation

## Example

Input: "add user authentication with JWT"

Curriculum has: "implement JWT auth" → failed at validator stage

Output:
```
⚠️  HARD WARNING: High similarity (87%) to known failure
Reason: Validator rule missing for Bearer token format
Mitigation: Use --review flag to inspect spec before BUILD
```

## Disabling Warnings

```bash
/one-shot "..." @./project --force  # Skip all warnings
```
```

- [ ] **Step 3: Commit and test**

```bash
git add skills/one-shot-generate/SKILL.md docs/predictive-failures.md
git commit -m "feat(prediction): wire failure predictor to stage 0 with hard warnings"
```

---

## Workstream 5: awesome-ai-apps Integration (Week 2)

### Files
- Create: `docs/patterns-from-awesome.md` (integration guide)
- Create: `skills/multi-stage-workflow/SKILL.md` (multi-stage pattern)
- Create: `.claude/agents/mcp-service-integrator.md` (MCP pattern agent)
- Create: `.claude/agents/memory-propagator.md` (memory pattern agent)
- Create: `examples/multi-stage-example.md` (example workflow)
- Create: `examples/mcp-integration-example.md` (example MCP integration)
- Create: `examples/memory-learning-example.md` (example memory propagation)

### Tasks

#### Task 1: Study awesome-ai-apps patterns (reference task)

**Files:**
- Read: awesome-ai-apps repo structure
- Create: `docs/patterns-from-awesome.md` (research output)

- [ ] **Step 1: Clone and analyze awesome-ai-apps**

```bash
cd /tmp
git clone https://github.com/Arindam200/awesome-ai-apps.git
cd awesome-ai-apps
find . -name "*.md" -o -name "*.py" | head -20
```

Identify:
- Deep researcher pattern (multi-stage: search → analyze → generate)
- MCP agent patterns (external tool discovery)
- Memory/learning agent patterns (cross-project knowledge)

- [ ] **Step 2: Document 3 key patterns**

Create `docs/patterns-from-awesome.md`:

```markdown
# Patterns from awesome-ai-apps

## Pattern 1: Multi-Stage Workflow

Example: `awesome-ai-apps/advanced_ai_agents/deep_researcher/`

**Structure:**
- Stage 1: Web search (query → results)
- Stage 2: Analysis (results → insights)
- Stage 3: Generation (insights → report)

**Applicability to one-shot-prompting:**
Add architect stage that searches for similar entity patterns in codebase history before designing.

## Pattern 2: MCP Agent Integration

Example: MCP agents for GitHub, APIs, databases

**Structure:**
- Agent registers with MCP server
- Server provides tool definitions
- Agent discovers and uses tools dynamically

**Applicability:**
Enhance curator skill to discover external MCP servers and register them.

## Pattern 3: Memory/Learning Agents

Example: Agents that retain cross-project learnings

**Structure:**
- Store learnings in vector DB or embeddings
- Retrieve relevant context for new tasks
- Update learnings as new patterns emerge

**Applicability:**
Wire learnings.jsonl into memory propagation for cross-project curriculum.
```

- [ ] **Step 3: Commit analysis**

```bash
git add docs/patterns-from-awesome.md
git commit -m "docs(research): analyze awesome-ai-apps patterns for plugin integration"
```

#### Task 2: Implement multi-stage workflow skill

**Files:**
- Create: `skills/multi-stage-workflow/SKILL.md`

- [ ] **Step 1: Write multi-stage workflow skill**

```yaml
---
type: skill
name: multi-stage-workflow
description: Multi-stage workflow orchestration (search → analyze → generate) for architect phase
trigger: /multi-stage-workflow
tools: Task
model: sonnet
---

# Multi-Stage Workflow

## Usage

```bash
/multi-stage-workflow "find cart patterns in codebase, analyze them, design new cart feature" @./project
```

## Stages

### Stage 1: Search
- Grep codebase for entity patterns
- Identify similar entities (Cart, Order, LineItem)
- Report findings

### Stage 2: Analyze
- Compare patterns
- Extract common fields, relationships
- Document architectural decisions

### Stage 3: Generate
- Design spec.json
- Incorporate learnings from Stage 2
- Output ready-to-implement spec

## Implementation

Uses 3 Task calls:
1. Search agent (haiku)
2. Analyze agent (sonnet)
3. Generate agent (sonnet)

Results flow: stage_1_output → stage_2 input → stage_3 output
```

- [ ] **Step 2: Implement the skill (full SKILL.md)**

- [ ] **Step 3: Write tests**

```python
def test_multi_stage_workflow_executes_all_stages():
    # Mock Task tool with 3 calls
    # Verify stage 1 → stage 2 → stage 3 flow
    # Assert final output is valid spec.json
```

- [ ] **Step 4: Commit skill**

```bash
git add skills/multi-stage-workflow/SKILL.md tests/test_multi_stage.py
git commit -m "feat(skills): add multi-stage-workflow skill from awesome-ai-apps pattern"
```

#### Task 3: Create MCP service integrator agent

**Files:**
- Create: `.claude/agents/mcp-service-integrator.md`

- [ ] **Step 1: Write MCP integrator agent**

```markdown
---
name: mcp-service-integrator
description: Discover and integrate external MCP services into curator skill
tools: Read, Write, Grep, Task
model: sonnet
---

# MCP Service Integrator Agent

## Trigger

On curator skill dispatch, check for `--discover-mcp` flag.

## Workflow

1. Query available MCP servers (GitHub, Linear, Slack, Google Drive, etc.)
2. Register them in `.claude/mcp-registry.json`
3. Update curator skill with new integrations
4. Document in `docs/mcp-services.md`

## Example Output

```json
{
  "mcp_services": [
    {
      "name": "github",
      "endpoint": "mcp.github.com",
      "capabilities": ["list_issues", "create_pr", "search_code"],
      "auth": "oauth"
    },
    {
      "name": "linear",
      "endpoint": "mcp.linear.app",
      "capabilities": ["query_issues", "create_issue"],
      "auth": "api_key"
    }
  ]
}
```
```

- [ ] **Step 2: Commit agent**

```bash
git add .claude/agents/mcp-service-integrator.md
git commit -m "feat(agents): add mcp-service-integrator for external tool discovery"
```

#### Task 4: Create memory propagation agent

**Files:**
- Create: `.claude/agents/memory-propagator.md`

- [ ] **Step 1: Write memory propagator agent**

```markdown
---
name: memory-propagator
description: Propagate cross-project learnings into curriculum and memory systems
tools: Read, Write, Edit
model: sonnet
---

# Memory Propagator Agent

## Trigger

After each generation completes (stage 8), dispatch this agent.

## Workflow

1. Extract learnings from `.beads/learnings.jsonl`
2. Embed learnings (semantic vectors)
3. Store in memory DB for retrieval
4. Update curriculum with failure patterns
5. Emit propagation report

## Output

Updates:
- `.beads/learnings.jsonl` (append new learnings)
- `memory/` directory (cross-project knowledge)
- `.beads/curriculum.jsonl` (updated failure patterns)

## Example Learning

```json
{
  "pattern": "has_many relationships require explicit FK columns",
  "source_task": "shopping cart with line items",
  "failure_mode": "missing cart_id in LineItem schema",
  "mitigation": "architect stage must infer FKs from relationships",
  "confidence": 0.95
}
```
```

- [ ] **Step 2: Commit agent**

```bash
git add .claude/agents/memory-propagator.md
git commit -m "feat(agents): add memory-propagator for cross-project learning"
```

#### Task 5: Create example documentation

**Files:**
- Create: `examples/multi-stage-example.md`
- Create: `examples/mcp-integration-example.md`
- Create: `examples/memory-learning-example.md`

- [ ] **Step 1: Write multi-stage example**

```markdown
# Multi-Stage Workflow Example

## Task

"Design a payment service that integrates with Stripe, handles webhooks, and logs transactions."

## Stage 1: Search

Agent searches codebase for:
- Payment entity patterns
- Webhook handling patterns
- Logging patterns

Results:
```
Found:
- Order entity with status (pending, completed, failed)
- WebhookHandler in services/
- structured_logger setup
```

## Stage 2: Analyze

Agent analyzes found patterns:
```
Common pattern:
- Payment (id, order_id, amount, status, created_at)
- Has 1:1 with Order
- Webhook validation before processing
- Structured logging with order_id context
```

## Stage 3: Generate

Agent generates spec.json:
```json
{
  "entities": [
    {
      "name": "Payment",
      "attributes": [...],
      "relationships": [{"to": "order", "kind": "belongs_to"}]
    }
  ]
}
```
```

- [ ] **Step 2: Write MCP integration example**

```markdown
# MCP Integration Example

## Task

"Discover what MCP services are available and register them."

Command:
```bash
/curator --discover-mcp
```

Output:
```
Discovered MCP services:
✅ GitHub (list_issues, create_pr, search_code)
✅ Linear (query_issues, create_issue)
✅ Slack (search_messages, post)

Updated: .claude/mcp-registry.json
Next: curator skill can now discover issues from GitHub/Linear during architect phase
```
```

- [ ] **Step 3: Write memory learning example**

```markdown
# Memory Learning Propagation Example

## Scenario

User runs:
```bash
/one-shot "add payment processing" @./ecommerce
```

Generation succeeds. At stage 8, memory-propagator agent:

1. Extracts learnings from spec, generated code, critic feedback
2. Records learning:
```json
{
  "pattern": "payment_webhook_validation",
  "description": "Always validate webhook signatures before processing",
  "source_task": "add payment processing",
  "success_rate": 0.98,
  "related_entities": ["Payment", "Order"]
}
```

3. Stores in memory DB (embeddings)
4. Updates curriculum

## Next Task

User runs:
```bash
/one-shot "add Stripe refund handling" @./other_project
```

Predictive failure detector finds similar pattern:
- "Stripe refund" similarity to "payment webhook" = 0.82
- Suggests: "Remember: validate webhook signatures before processing"

User continues with confidence.
```

- [ ] **Step 4: Commit examples**

```bash
git add examples/multi-stage-example.md examples/mcp-integration-example.md examples/memory-learning-example.md
git commit -m "docs(examples): add awesome-ai-apps pattern integration examples"
```

---

## Integration Points & Success Criteria

### Cross-Workstream Integration

1. **OTel + Rollback:** Rollback agent uses OTel traces to identify failure root cause
2. **OTel + Docs Drift:** Docs drift agent updates observability docs when new entities added
3. **Predictive + Curriculum:** Failure predictor loads curriculum trained by memory propagator
4. **MCP + Curator:** MCP integrator enhances curator skill with external tool discovery

### Success Criteria

- [ ] All 4 TIER A agents deployed and tested (24 tasks complete)
- [ ] Test count: 531 → 545+ (20+ new tests across 4 workstreams)
- [ ] OTel spans visible in Jaeger dashboard (manual verification)
- [ ] Docs drift detects ≥1 entity change and auto-generates draft
- [ ] Rollback successfully reverts to `.osp.bak` on N=3 consecutive failures
- [ ] Predictive failure detector warns on >0.8 similarity to known failure
- [ ] 3 awesome-ai-apps patterns adapted and documented (multi-stage, MCP, memory)
- [ ] 0 regressions on existing 531 tests
- [ ] v1.1.0 release candidate ready

### Timeline

- **Week 1 (May 25–31):** Workstreams 1–3 (OTel, Docs Drift, Rollback)
- **Week 2 (Jun 1–7):** Workstream 4 (Predictive) + Workstream 5 (awesome-ai-apps)
- **Week 3 (Jun 8–14):** Integration testing, final polish, v1.1.0 release

---

## Testing Strategy

Each workstream has:
- Unit tests (isolated scripts)
- Integration tests (skill + SKILL.md)
- End-to-end smoke tests (full pipeline dry-run)

Run all tests:
```bash
python -m pytest tests/test_*.py -v
bash .claude/scripts/smoke-test.sh
```
