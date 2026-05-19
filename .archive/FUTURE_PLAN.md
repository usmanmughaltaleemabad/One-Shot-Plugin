# One-Shot Prompting — Future Roadmap & Strategic Plan

**Status:** LOCAL PLAN — Not committed to git. For internal strategic guidance.
**Last Updated:** 2026-05-10 (Phase 0-3 Complete, Phase 1 In Progress, Doc Cleanup Complete)
**Current Status:** 
- ✅ Phase 0: Silent Planning Engine (v0.6.1 shipped)
- ✅ Phase 2-3: REST API + Batch Jobs (v2.0.0 shipped, 44+13 = 57 modules)
- 🟡 Phase 1: Critical Integration Gaps (3/7 modules complete, May 20 target for v0.7.0)
- 📋 Phase 4-5: Planned Q3-Q4 2026
**Current Market:** 5-8% penetration, targeting 15-20% post-Phase 4+5

---

# 🎯 STRATEGIC SCOPE DECISIONS — What We Build vs What We Don't

## Core Mission
**One-Shot Prompting is the specialist in event-driven systems code generation across 5 frameworks (Django, FastAPI, Spring, Go, Node.js).**

We are NOT a generalist tool. We own a niche and defend it deeply rather than spreading thin across all code domains.

---

## WHAT WE BUILD ✅

| Domain | What | Why | Target Market |
|--------|------|-----|---|
| **Event-Driven Systems** | Handlers, orchestration, workflows, async patterns | Core expertise; 40-50% of backend code | Microservices teams, SaaS backends |
| **Multi-Framework Support** | Equal support for Django, FastAPI, Spring, Go, Node | Framework awareness = production-ready code | Enterprise with polyglot stacks |
| **Multi-File Generation** | Complete features (models+views+tests+migrations) | True one-shot = one request → production | Developers tired of manual splitting |
| **Auto-Integration** | Zero manual wiring (imports, routing, registration) | Removes 80% of post-generation friction | Teams valuing speed over control |
| **Enterprise Deployment** | Docker, Kubernetes, Terraform, CI/CD configs | Event systems need orchestration | Enterprise ops teams |
| **API Documentation** | OpenAPI/Swagger auto-generated | Developers need to know what was generated | Teams with API contracts |
| **Legacy Modernization** | Strangler pattern for incremental adoption | Existing systems are the largest market | Enterprise modernization teams |

---

## WHAT WE DON'T BUILD ❌ (By Strategic Design)

### ❌ CRUD APIs
**Decision:** NOT building CRUD endpoint generation (list/create/read/update/delete).

**Why:**
- **Dominated:** Superpowers, ChatGPT, Copilot all do this
- **Commoditized:** CRUD is simple + taught in every tutorial
- **Low Value:** CRUD doesn't need "one-shot" — users can do it manually in 5 minutes
- **Our Opportunity:** Event handlers need orchestration (complex, worth automating)

**Market Reality:** CRUD = 40% of code, but owned by 10 competitors. Event systems = 40% of code, owned by 0 specialized tools.

**Strategy:** If someone asks "generate a User API," we say: "Use Superpowers for CRUD schema; use Claude for event handlers."

**Market Impact:** Cede 40% of generic market, own 50% of valuable niche.

---

### ❌ UI Generation
**Decision:** NOT building React/Vue/Svelte/Flutter component generation.

**Why:**
- **Crowded:** 15+ competitors (Superpowers, v0, Sketch2React, etc.)
- **AI-Hard:** UI is visual + interactive; LLM generation = 50% rework rate
- **Not Event-Driven:** UI is stateful, not event-oriented
- **Our Expertise:** We know async/sync patterns, not component lifecycle

**User Reality:** "Generate a payment button" is not in our wheelhouse.

**Strategy:** Partner approach: "Use Claude + Superpowers for UI; use One-Shot for payment event handlers."

**Market Impact:** Cede 20% of market, avoid competing with 15 tools.

---

### ❌ Data Science / ML Pipelines
**Decision:** NOT building scikit-learn/TensorFlow/PyTorch code generation.

**Why:**
- **Different Expertise:** Data science = statistical thinking, not event-driven systems
- **Different Tools:** TensorFlow, Hugging Face, MLflow ecosystem (not our domain)
- **Different Users:** Data scientists, not backend engineers
- **Wrong Market:** ML is 5-10% of backend code; event systems are 40%+

**Reality Check:** "Generate a recommendation engine" requires domain knowledge we don't have.

**Strategy:** Stay in events. Let Claude handle one-off ML requests.

**Market Impact:** Avoid 10% market, keep focus sharp.

---

### ❌ Mobile App Development
**Decision:** NOT building iOS/Android/React Native app generation.

**Why:**
- **Different Framework Set:** Swift, Kotlin, React Native, Flutter (not our 5 frameworks)
- **Not Event-Driven:** Mobile is UI-first, not events-first
- **Different Platform:** App Store distribution, mobile SDKs (not our expertise)
- **Different Users:** Mobile engineers, not backend engineers

**Reality Check:** Our expertise is server-side event orchestration, not UI state management.

**Strategy:** "Use One-Shot for event-driven backend; generate mobile client separately."

**Market Impact:** Cede 15% market, stay specialist.

---

### ❌ Templating / Scaffolding Tools
**Decision:** NOT building project scaffolding (like Rails scaffold, Django startproject).

**Why:**
- **Solved:** Cookiecutter, django-admin startproject, Spring Boot Initializr all exist
- **Low Complexity:** Scaffolding is file copying + variable substitution (not worth our harness)
- **Commoditized:** Every framework has built-in scaffolding
- **Not Strategic:** We generate features, not empty projects

**Reality Check:** Users don't need "generate empty Django project" — they need "generate payment workflow in existing project."

**Strategy:** Assume project structure exists. Generate code that fits.

**Market Impact:** Not a gap; scaffolding is commodity.

---

### ❌ Configuration-Only Generation
**Decision:** NOT building Infrastructure-as-Code ONLY tools (pure Terraform/CloudFormation).

**Why:**
- **Different Market:** IaC specialists (Terraform Cloud, CloudFormation) own this
- **Not Event-Driven:** IaC is declarative, not events
- **Wrong Tool:** One-Shot is for code generation, not configuration management

**What We DO:** Generate IaC as PART OF a larger feature (event system + Docker + K8s).

**Strategy:** IaC is supporting feature, not primary focus.

**Market Impact:** No impact; IaC is bundled with event features.

---

## MARKET IMPLICATION: WHY SPECIALIZATION WINS

### Generalist Approach (❌ Avoid)
- "Do everything: CRUD, UI, ML, mobile, scaffolding, IaC"
- Result: 60% worse at events, 10% better at CRUD
- Market: Compete with ChatGPT (lose)
- Revenue: $10-20M (commodity pricing)

### Specialist Approach (✅ Our Choice)
- "Own event-driven systems completely"
- Result: 2-3x better than ChatGPT at event orchestration
- Market: 40-50% of backend code (50% adoption = 25% of market)
- Revenue: $150-210M (premium pricing for experts)

**Decision:** Specialize. Own events. Defend the niche.

---

## WHAT HAPPENS WHEN USERS ASK FOR ❌ OUT-OF-SCOPE FEATURES

**Expected user requests we'll reject:**
1. "Generate a React component for user dashboard"
   - **Response:** "One-Shot specializes in event-driven backend code. For UI, try Superpowers or Claude directly."

2. "Generate a TensorFlow recommendation model"
   - **Response:** "One-Shot is for event-driven systems, not ML. Try Claude for this request."

3. "Generate a Flutter mobile app"
   - **Response:** "One-Shot generates backend event handlers. For mobile, use Flutter documentation + Claude."

4. "Scaffold an empty Django project"
   - **Response:** "Django startproject does this faster. One-Shot generates features in existing projects."

**Strategy:** Polite redirect. Build trust by being honest about scope.

---

## ENFORCING SCOPE IN DOCUMENTATION

These decisions need to be documented in:
1. **README.md** — "What One-Shot Is Good For" section
2. **SKILL.md** — Rejection logic for out-of-scope requests
3. **Plugin description** — Clear scope boundaries
4. **Marketing materials** — "Event-driven specialist, not generalist"

**Key Message:** "One-Shot is the expert in event-driven code. Use us for events. Use other tools for CRUD, UI, and ML."

---

# ⚠️ PHASE 0: HARNESS FOUNDATION (Q1 2026) — 120h — ABSOLUTE PRIORITY

## Why Phase 0 Exists (Critical Context)

Your plugin has codebase analysis and code generation, but **lacks the harness architecture that makes true one-shot prompting work**. Without Phase 0, all subsequent phases (Gaps 1-8) will inherit a broken foundation.

**2026 Best Practice Definition of "One-Shot Prompting":**
- ✅ Single prompt → complete working feature (no follow-up needed)
- ✅ **NEVER asks clarifying questions** (uses codebase analysis instead)
- ✅ Silent decision-making (evaluates options, picks best, documents choices)
- ✅ Verification loop (validates output, self-repairs if broken)
- ✅ Override interface (slash commands for regenerate/validate/test)

**Current State:** You ask users "if context sparse, describe your stack" — **NOT true one-shot**.

**After Phase 0:** The plugin will be a genuine one-shot system with no questions ever asked.

---

## Phase 0.1: Silent Planning Engine (40h)

### Problem
Current SKILL.md jumps straight from analysis → generation. Missing: intelligent decision layer.

When user says "add auth handler," your plugin should evaluate:
- Async vs sync? (Pick based on detected framework patterns, document choice)
- Database or stateless? (Pick based on codebase conventions)
- ORM or raw SQL? (Detect from existing code)
- Testing framework? (Use what's already in project)

**Currently:** You default to first option; user has to rerun to try alternatives.

### Solution: Planning.md Decision Engine

**New file:** `skills/one-shot-generator/Planning.md`

```markdown
# Silent Planning Engine — Zero User Questions

When user invokes /one-shot-prompting:generate, BEFORE generating code:

## Step 1: Analyze Codebase Context (from analyzer output)

Extract from CODEBASE CONTEXT:
- Detected frameworks + versions
- Existing patterns (async/sync, ORM/raw SQL, DI style)
- Testing approach (pytest, unittest, jest, etc.)
- Logging library (structlog, loguru, winston, zap)
- Error handling pattern (exceptions, enums, both)
- Database type (PostgreSQL, MySQL, MongoDB, in-memory)

## Step 2: Silent Evaluation (No User Input)

For each key decision, score options:

### Decision: Async vs Sync?
```
If FastAPI detected → async (score: 9/10)
If Django detected → sync (score: 9/10)
If existing async functions → async (score: 8/10)
If existing sync functions → sync (score: 8/10)
Fallback → sync (score: 5/10, safest default)
```

### Decision: Persistence Layer?
```
If SQLAlchemy in Key Libs → SQLAlchemy ORM (score: 9/10)
If Django ORM detected → Django ORM (score: 9/10)
If raw SQL in existing code → raw SQL (score: 8/10)
If Mongo detected → pymongo/motor (score: 9/10)
Fallback → ORM (score: 7/10, safer than raw SQL)
```

### Decision: Testing Framework?
```
If pytest in dependencies → pytest (score: 9/10)
If unittest in imports → unittest (score: 8/10)
If jest detected (JS) → jest (score: 9/10)
If JUnit detected (Java) → JUnit (score: 9/10)
Fallback → pytest for Python, jest for JS (score: 7/10)
```

### Decision: Error Handling?
```
If try/except throughout → exceptions (score: 9/10)
If Result/Either pattern → return errors (score: 8/10)
If error enums → use enums (score: 8/10)
Fallback → exceptions (score: 8/10, most common)
```

## Step 3: Output Plan Block

Never ask user. Instead output:

```markdown
## PLAN DECISIONS (All Evaluated Silently)

| Decision | Choice | Score | Reason |
|----------|--------|-------|--------|
| Async/Sync | async | 9/10 | FastAPI detected; existing code is async |
| Persistence | SQLAlchemy ORM | 9/10 | Found in requirements.txt |
| Testing | pytest | 9/10 | Detected pytest.ini |
| Error Handling | exceptions | 9/10 | try/except pattern throughout |
| Logging | structlog | 8/10 | Detected in imports |

**Override:** Rerun with `--sync` or `--no-orm` to change (see Slash Commands)
```

## Step 4: Generate Based on Plan

Use decisions from Step 3 when generating code. Never deviate unless user explicitly overrides via slash command.
```

**Implementation Detail:**
- Add decision-scoring algorithm to SKILL.md
- Extract logic into `scripts/plan_decisions.py` (Python stdlib only)
- Call via `! injection` before generation prompt
- Output decision table into SKILL context
- Document all scoring logic in comments (so future versions can tune)

**Testing:**
- Run analyzer on 10 real codebases
- Verify all decisions are defensible (would you make this choice?)
- Document any defaults that feel wrong

---

## Phase 0.2: Verification Harness (35h)

### Problem
Generated code is shown to user as-is. No validation.

Example failures:
```python
# Generated code tries to import from wrong module
from .nonexistent_module import DatabaseSession  # ❌ import fails

# Generated code uses wrong ORM
User has SQLAlchemy, generated code uses Tortoise ORM  # ❌ wrong choice

# Generated code has syntax errors
async def handler(self,)  # ❌ trailing comma

# Generated code can't find models
from myapp.models import User  # ❌ User model is in different file
```

Currently: User runs code, discovers error, reruns plugin. Friction.

**True one-shot:** Verify before showing. If broken, self-repair or show error with fix.

### Solution: Verification.md Harness

**New file:** `skills/one-shot-generator/Verification.md`

```markdown
# Verification Harness — Self-Healing Generated Code

After code generation, before showing to user:

## Step 1: Syntax Validation

Language-specific:

### Python
```bash
python -m py_compile <generated_file>
```
If fails → Report error, abort

### TypeScript/JavaScript
```bash
npx tsc --noEmit <generated_file>  # for TS
node --check <generated_file>      # for JS
```

### Go
```bash
go build -o /dev/null <generated_file>
```

### Java
```bash
javac -cp <classpath> <generated_file>
```

## Step 2: Import Validation

Parse generated code. For each import:
```
for each import in generated_code:
  check if module exists in codebase
  if not found:
    - Is it a stdlib import? ✅ OK
    - Is it an external library? Check requirements.txt/package.json
    - Is it an internal module? ❌ ERROR — wrong assumption
```

## Step 3: Framework Compliance Check

Generated code must match detected framework:
```
if Django detected:
  ✅ Uses django.db.models, not SQLAlchemy
  ✅ Uses DRF serializers if DRF detected
  ❌ Using FastAPI decorators? FAIL

if FastAPI detected:
  ✅ Uses async def
  ✅ Uses Pydantic models
  ❌ Using Django ORM? FAIL
```

## Step 4: Pattern Consistency

Generated code matches existing patterns:
```
if existing code uses:
  - async/await → generated must be async
  - exceptions → generated must use exceptions
  - structlog → generated must use structlog
  - type hints → generated must be fully typed
```

## Step 5: Self-Repair Logic

If any validation fails:

```
ATTEMPT 1: Regenerate with error context
  Prompt: "Validation failed: {error}. Fix and regenerate."
  
ATTEMPT 2: If still fails, try alternative
  For imports: "Try different module path"
  For typing: "Remove type hints, use basic types"
  For async: "Convert to sync version"

ATTEMPT 3: If still fails, show user
  Output: "Could not auto-repair. Manual fix needed:"
  Show: Specific error + suggested fix
```

## Step 6: Post-Verification Output

Never show broken code. Output:

```markdown
✅ VERIFICATION PASSED

Syntax: ✅ Valid Python 3.10+
Imports: ✅ All modules found (stdlib + requests)
Framework: ✅ Django patterns detected
Consistency: ✅ Matches async/await style
Testing: ✅ pytest compatible

Ready to use. Copy to: myapp/views.py
```

OR (if auto-repair needed):

```markdown
⚠️ VERIFICATION REQUIRED AUTO-REPAIR

Original Issue: Import path was wrong
  Generated: from .models import nonexistent
  Fixed to: from myapp.models import User

After repair:
Syntax: ✅ Valid
Imports: ✅ All modules found
Framework: ✅ Django patterns detected

Ready to use. Copy to: myapp/views.py
```
```

**Implementation:**
- Create `scripts/verify_generated.py` (Python stdlib only)
- Language-specific validators:
  - Python: `ast` module + import analysis
  - TypeScript: Parse and check imports
  - Go: Basic syntax via fmt
  - Java: Check for known patterns
- Call via `! injection` after generation
- If fails, regenerate with error context (max 2 retries)
- Always show user what was verified

---

## Phase 0.3: Slash Command Overrides (25h)

### Problem
Current plugin: single entry point `/one-shot-prompting:one-shot-generator`

Can't:
- Regenerate with different options (must rerun full prompt)
- Validate without regenerating
- Test without copying code
- Explain decisions without asking user

### Solution: Slash Commands for Control

**New file:** `.claude/commands/one-shot-prompting.md`

```markdown
---
name: one-shot-prompting-controls
description: Slash commands for one-shot-prompting plugin control
---

# One-Shot Prompting Control Commands

## /osp:regenerate [FLAGS]

Regenerate code with different options (same codebase context).

```bash
/osp:regenerate                    # Use different defaults
/osp:regenerate --async            # Force async version
/osp:regenerate --sync             # Force sync version
/osp:regenerate --no-orm           # Use raw SQL instead of ORM
/osp:regenerate --raw-sql          # Explicit raw SQL
/osp:regenerate --with-validation  # Add input validation
/osp:regenerate --minimal          # Minimal code, no extras
/osp:regenerate --exhaustive       # Generate all edge cases
```

Internally: Re-run analyzer, replan with overrides, regenerate.

## /osp:validate

Run verification harness on last generated code WITHOUT regenerating.

```bash
/osp:validate
```

Output:
```
✅ Syntax valid
✅ Imports OK
✅ Framework patterns match
✅ Consistency check: async/await style matches codebase
```

## /osp:test

Generate code + run tests immediately.

```bash
/osp:test
```

Internally:
1. Generate code (with verification)
2. Create test file if not in output
3. Run tests via pytest/jest/go test
4. Show results

Output:
```
✅ Generated: auth/views.py + auth/tests/test_views.py
✅ Tests: 8 passed, 0 failed
✅ Coverage: 92%

Code is validated and tested. Ready to integrate.
```

## /osp:integrate

Copy generated code to correct locations in codebase.

```bash
/osp:integrate
```

Internally:
1. Verify generation (syntax + imports)
2. Identify correct file paths based on codebase structure
3. Copy files to right locations
4. Show what was integrated

Output:
```
✅ Files integrated:
  myapp/models.py (120 lines added)
  myapp/views.py (80 lines added)
  myapp/tests/test_auth.py (created)
  myapp/migrations/0002_add_auth.py (created)

Run migrations: python manage.py migrate
Start tests: pytest myapp/tests/test_auth.py
```

## /osp:explain

Show all decisions made in last generation.

```bash
/osp:explain
```

Output:
```
## Decisions Made in Last Generation

| Decision | Choice | Score | Reason |
|----------|--------|-------|--------|
| Async/Sync | async | 9/10 | FastAPI + existing async patterns |
| ORM | SQLAlchemy | 9/10 | Found in requirements.txt |
| Testing | pytest | 9/10 | Detected pytest.ini |
| Error Handling | exceptions | 9/10 | try/except throughout codebase |

To use different decisions:
  /osp:regenerate --sync          (to force sync)
  /osp:regenerate --no-orm        (to force raw SQL)
  /osp:regenerate --unittest      (to use unittest instead)
```

## /osp:reset

Clear generation history, start fresh.

```bash
/osp:reset
```

## /osp:status

Show last generation details.

```bash
/osp:status
```

Output:
```
Last Generation: 5 minutes ago
  Command: /one-shot-prompting:generate add user auth @/home/user/myproject
  Status: ✅ Generated + Verified
  Output: 4 files (models, views, serializers, tests)
  Next: /osp:integrate or /osp:regenerate --async
```
```

**Implementation:**
- Create `.claude/commands/one-shot-prompting.md` (markdown skill file)
- Each command calls the plugin with internal flags
- Slash commands provide friction-free control without asking user
- No new Python code needed; flags passed to existing SKILL.md logic

---

## Phase 0.4: Zero-Question Guarantee (20h)

### Problem
SKILL.md line 22: `"If the path was not found or context is sparse, ask the user for one line"`

**This violates one-shot contract.** True one-shot never asks.

### Solution: Intelligent Fallbacks

**Changes to SKILL.md:**

```markdown
## Fallback Strategy (Never Ask User)

### If path is missing:
```bash
# Instead of asking, use current directory
if @path not provided:
  use current_directory
  output: "Using current directory. To specify project, add @/path"
```

### If codebase context is sparse:
```bash
# Instead of asking, use language defaults
if context sparse (fewer than 5 files found):
  detect_language()
  if python:
    assume Django (most common Python framework)
    output assumptions block
  if javascript/typescript:
    assume Next.js (most common JS framework)
  if java:
    assume Spring Boot (most common Java framework)
  if go:
    assume stdlib http.mux (most common Go default)
```

### If framework ambiguous:
```bash
# Instead of asking, pick the most likely
if django and fastapi both detected:
  if manage.py found:
    use Django (9/10 score)
  if main.py with FastAPI app found:
    use FastAPI (9/10 score)
  else:
    use most recent modification time (9/10 score)
```

### If conventions unclear:
```bash
# Instead of asking, use framework defaults
if no convention detected:
  use framework default:
    Django → async views (most common in 2024+)
    FastAPI → async def (framework default)
    Spring → constructor injection (best practice)
    Go → context.Context first param (best practice)
```

All fallback choices documented in output:

```markdown
## Assumptions (Using Fallbacks)

Since project context was sparse, using framework defaults:
- **Framework:** Django (not detected, using most common Python framework)
- **Async/Sync:** async views (modern Django default)
- **Testing:** pytest (most common in 2024)
- **Database:** PostgreSQL with Django ORM (most common)

These were picked automatically. To override, use:
  /osp:regenerate --sync          (force sync)
  /osp:regenerate --raw-sql       (force raw SQL)
  /osp:regenerate --unittest      (force unittest)
```

## Removal of All Question Paths

Audit SKILL.md for every instance of:
- "ask the user"
- "please confirm"
- "which option"
- "do you want"
- Any prompt ending with "?"

Replace with intelligent defaults.
```

**Implementation:**
- Audit current SKILL.md (find all question paths)
- Replace with fallback logic
- Document every assumption in output
- Provide slash command override for every fallback

---

## Phase 0 Success Criteria

After Phase 0 completes, **no user is ever asked a question:**

- ✅ Codebase analyzer works standalone (can infer context)
- ✅ Planning layer evaluates options silently
- ✅ Verification harness validates and self-repairs
- ✅ Slash commands provide override without friction
- ✅ Zero question paths in SKILL.md
- ✅ All assumptions documented in output

**Test:** Run plugin on 10 unfamiliar codebases (paths you haven't seen). Never ask user anything. If you get stuck, use intelligent fallback. Document all assumptions made.

---

## Phase 0 Timeline

```
Week 1-2:   Design Planning.md decision engine + scoring algorithm
Week 2-3:   Implement scripts/plan_decisions.py + SKILL.md integration
Week 3:     Build Verification.md + scripts/verify_generated.py
Week 4:     Add slash commands + testing
Week 5:     Audit all question paths, replace with fallbacks
Week 6:     Integration testing on real codebases, refinement
```

**Target:** Complete Phase 0 by end of Q1 2026. Must ship before any v0.7.0 work.

---

## Why Phase 0 Blocks Everything

- **Without Silent Planning:** Gaps 1-8 will ask users "which option?"
- **Without Verification:** Generated code from Gaps 1-8 will be broken
- **Without Slash Commands:** Users can't recover from mistakes without reruns
- **Without Zero Questions:** Plugin is "interactive" not "one-shot"

**Phase 0 is the foundation. Build it first. Then Gaps 1-8 are easy.**

---

# ⚠️ CRITICAL BLOCKING GAPS (v0.7.0+ — After Phase 0)

**IMPORTANT:** After Phase 0 completes (Q1 2026), these gaps make your plugin NOT production-ready for complete features. You're currently positioned as "complete feature generation," but you deliver "single file generation." Close these FIRST before proceeding with v0.8.0+.

See `.claude-plugin/HONEST_CAPABILITY_AUDIT.md` for full analysis.

---

## Gap 1: Single-File Generation (BLOCKING)

### Problem
**You claim:** "Framework-correct output — Django gets models/views/serializers/urls"
**Reality:** You generate 1 file (e.g., `views.py`), not 3-4 files (models + views + serializers + urls)
**Impact:** User must manually split generated code into multiple files OR request each file separately (multiple plugin runs)

### Current State
```
Input: /one-shot-prompting:generate Add Django user auth endpoint
Output: One file (auth.py containing all logic)
Missing: Separate models.py, views.py, serializers.py, urls.py files
Result: User must copy-paste logic into correct files (friction)
```

### Solution: v0.7.0-Critical-Gaps Phase 1 — Multi-File Generation

Generate framework-specific file layouts IN ONE SHOT:

#### **For Django:**
```
Input: /one-shot-prompting:generate Add user auth system
Output:
  auth/
  ├── models.py (User model)
  ├── views.py (ViewSet)
  ├── serializers.py (DRF serializers)
  ├── urls.py (URL routing)
  ├── admin.py (Admin registration)
  ├── migrations/
  │   └── 0001_initial.py (Database migration)
  └── tests/
      └── test_auth.py (Tests)

All in ONE response. No copy-paste. Just run migrations and go.
```

#### **For FastAPI:**
```
Input: /one-shot-prompting:generate Add payment processing
Output:
  payment/
  ├── router.py (APIRouter)
  ├── schemas.py (Pydantic models)
  ├── service.py (Business logic)
  ├── models.py (SQLAlchemy models)
  ├── dependencies.py (Depends())
  └── tests/
      └── test_payment.py
```

#### **For Spring Boot:**
```
Input: /one-shot-prompting:generate Add product catalog
Output:
  product/
  ├── ProductController.java
  ├── ProductService.java
  ├── ProductRepository.java
  ├── Product.java (Entity)
  ├── ProductDTO.java
  └── ProductTest.java
```

#### **For Go:**
```
Input: /one-shot-prompting:generate Add order handler
Output:
  order/
  ├── handler.go (HTTP handler)
  ├── service.go (Business logic)
  ├── repository.go (Data access)
  ├── models.go (Structs)
  └── handler_test.go
```

**Implementation:**
- Modify SKILL.md to generate multiple files per framework
- Each file gets its own section: `## File: path/to/filename.ext`
- User copies all files to correct directories
- No manual splitting needed
- Effort: ~60 hours (~20 per major framework: Django, FastAPI, Spring)

---

## Gap 2: Auto-Wiring into Codebase (BLOCKING)

### Problem
**You claim:** "Code that integrates without refactoring"
**Reality:** Generated code must be manually imported/registered
**Impact:** User still needs 10-20 minutes of manual wiring (imports, registration, migrations)

### Current State
```
Django Example:
User gets views.py code, but must manually:
  1. Add to urls.py: from .views import MyViewSet
  2. Add to urls.py: path('api/endpoint/', MyViewSet.as_view())
  3. Run: python manage.py makemigrations && python manage.py migrate
  4. Add import to admin.py for admin registration

FastAPI Example:
User gets router.py code, but must manually:
  1. In main.py: from .router import router
  2. In main.py: app.include_router(router, prefix="/api")
  3. Update CORS/middleware if needed
```

### Solution: v0.7.0-Critical-Gaps Phase 2 — Auto-Wiring Instructions + Patches

Generate not just code, but INTEGRATION GUIDE:

#### **For Django:**
```markdown
## Integration Steps (Copy-Paste Ready)

### Step 1: Register URLs
Add to `myapp/urls.py`:
```python
from django.urls import path
from .views import AuthViewSet

urlpatterns = [
    path('api/auth/', AuthViewSet.as_view({'post': 'create'})),
]
```

### Step 2: Register in Admin (Optional)
Add to `myapp/admin.py`:
```python
from .models import AuthModel
admin.site.register(AuthModel)
```

### Step 3: Run Migrations
```bash
python manage.py makemigrations myapp
python manage.py migrate
```

### Done
Your endpoint is live at POST /api/auth/
```

#### **For FastAPI:**
```markdown
## Integration Steps

### Step 1: Mount Router
In `main.py`:
```python
from myapp.router import router
app.include_router(router, prefix="/api", tags=["payments"])
```

### Step 2: Update Dependencies (if needed)
```bash
pip install -r requirements-payment.txt
```

### Done
Your endpoints are live at /api/payments/*
```

#### **For Go:**
```markdown
## Integration Steps

### Step 1: Register Handler
In `main.go`:
```go
import "myapp/order"
http.HandleFunc("/api/orders", order.Handler)
```

### Step 2: Run
```bash
go run main.go
```
```

**Implementation:**
- Add "## Integration Steps" section to every generated README
- Provide copy-paste code snippets for:
  - URL registration (Django)
  - Router mounting (FastAPI, Express)
  - Handler registration (Go)
  - Middleware setup (if needed)
- Include CLI commands (migrations, tests, deployment)
- Effort: ~30 hours

---

## Gap 3: Database Migration File Generation (BLOCKING)

### Problem
**You claim:** "Migration awareness"
**Reality:** You note "Run `python manage.py makemigrations`" but don't generate the .py file
**Impact:** User must run Django command (which works) BUT doesn't match your "production-ready" claim for all frameworks

### Current State
```
Generated models.py:
class User(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()

What user must do:
  python manage.py makemigrations  ← Django auto-generates the file
  python manage.py migrate         ← Apply it

For Spring/Go/Rust, user must generate SQL manually.
```

### Solution: v0.7.0-Critical-Gaps Phase 3 — Generate Actual Migration Files

#### **For Django:**
```
Generate: migrations/0001_add_user_model.py
```python
from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('email', models.EmailField(unique=True)),
            ],
        ),
    ]
```

#### **For Spring/Flyway:**
```
Generate: src/main/resources/db/migration/V1__Create_user_table.sql
```sql
CREATE TABLE users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### **For Go/golang-migrate:**
```
Generate: migrations/1_create_users.up.sql
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(255) UNIQUE
);
```

#### **For Rust/Diesel:**
```
Generate: migrations/{timestamp}_create_users/up.sql
```sql
CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL
);
```

**Implementation:**
- Detect migration tool from codebase (Flyway, Alembic, golang-migrate, Diesel)
- Generate `.sql` or `.py` migration files (not just notes)
- Include rollback (`down.sql` or `down()`)
- Check for data migrations (non-destructive defaults)
- Effort: ~40 hours (~8 hours per major framework)

---

## Gap 4: Slash Command / CLI Scaffolding (BLOCKING)

### Problem
**You claim:** "One-shot feature generation"
**Reality:** Can't generate Discord/Slack commands or CLI wrappers that use the handler
**Impact:** Users building Discord bots, Slack apps, or CLIs must manually wrap your generated code

### Current State
```
User asks: Generate a rate limit handler for Discord bot
You generate: rate_limiter.py (pure business logic)
User must manually create: @bot.command() decorator + Discord wiring
Result: Not "one-shot"; requires manual integration
```

### Solution: v0.7.0-Critical-Gaps Phase 4 — Slash Command + CLI Scaffolding

#### **For Discord Bot:**
```
Input: /one-shot-prompting:generate Add rate limiter command for Discord. In Python.

Output:
  discord/
  ├── rate_limiter_service.py (Pure business logic)
  ├── rate_limiter_command.py (Discord @bot.command wrapper)
  ├── tests/
  │   ├── test_service.py
  │   └── test_command.py
  └── README.md (Setup Discord bot)

rate_limiter_command.py:
@bot.command(name='ratelimit')
async def rate_limiter(ctx, user: discord.User):
    """Check rate limit for user"""
    limiter = RateLimiter()
    allowed = await limiter.check(user.id)
    if allowed:
        await ctx.send(f"✅ {user} is within rate limit")
    else:
        await ctx.send(f"⛔ {user} exceeded rate limit")
```

#### **For Slack Bot:**
```
Input: /one-shot-prompting:generate Add payment approval for Slack. In TypeScript.

Output:
  slack/
  ├── payment_service.ts (Business logic)
  ├── payment_slash_command.ts (Slack command handler)
  └── README.md

payment_slash_command.ts:
app.command('/approve-payment', async ({ command, ack, say }) => {
  await ack();
  const service = new PaymentService();
  const result = await service.approve(command.text);
  await say(result);
});
```

#### **For CLI (Node/Python/Go):**
```
Input: /one-shot-prompting:generate Add backup command for CLI. In Go.

Output:
  cli/
  ├── backup_service.go (Business logic)
  ├── backup_command.go (CLI command handler)
  └── main.go (Entry point)

backup_command.go:
var backupCmd = &cobra.Command{
  Use: "backup",
  Short: "Create a backup",
  RunE: func(cmd *cobra.Command, args []string) error {
    svc := NewBackupService()
    return svc.Backup(context.Background())
  },
}
```

**Implementation:**
- Detect if user is building Discord/Slack/Telegram/CLI app
- Generate command wrapper + business logic separately
- User gets: handler (reusable) + command integration (platform-specific)
- Effort: ~50 hours (~12 hours per platform: Discord, Slack, Telegram, CLI)

---

## CRITICAL PRIORITY CHANGE

### Problem
**You claim:** "Framework-correct output"
**Reality:** Don't handle dependency injection (services, configs, database connections)
**Impact:** In larger apps with DI containers, user must manually wire dependencies

### Current State
```
You generate: PaymentService class
But it assumes: straight instantiation
Reality: In enterprise apps, you need:
  - Spring @Service + @Autowired
  - FastAPI dependency injection
  - Go wire/fx for dependency management
```

### Solution: v0.7.0-Critical-Gaps Phase 5 — DI-Aware Generation

#### **For Spring:**
```java
@Service
public class PaymentService {
    private final PaymentRepository repo;
    private final NotificationService notif;
    
    @Autowired
    public PaymentService(PaymentRepository repo, NotificationService notif) {
        this.repo = repo;
        this.notif = notif;
    }
}

// User just needs to @Autowired inject it
@RestController
public class PaymentController {
    @Autowired
    private PaymentService service;
}
```

#### **For FastAPI:**
```python
from fastapi import Depends

async def get_payment_service(db: Session = Depends(get_db)) -> PaymentService:
    return PaymentService(db)

@app.post("/payments")
async def create_payment(payment: PaymentSchema, service: PaymentService = Depends(get_payment_service)):
    return await service.process(payment)
```

**Implementation:**
- Analyze detected DI container/pattern
- Generate services with proper injection annotations
- Generate controller/handler with DI setup
- Effort: ~25 hours

---

## Gap 6: Multi-Handler Orchestration (BLOCKING FOR MICROSERVICES)

### Problem
**You claim:** "Complete feature generation"
**Reality:** Can't generate coordinated multi-handler features (payment system = models + webhook + notifications + retries)
**Impact:** Users building event-driven microservices must run plugin 4+ times and manually wire dependencies

### Current State
```
User wants: Complete payment system
You generate: One handler at a time
Reality: User must run plugin 4 times:
  1. /generate payment model + storage
  2. /generate webhook endpoint
  3. /generate notification sender
  4. /generate retry handler
  5. Manually wire dependencies between them
Result: Not "one-shot"; requires orchestration
```

### Solution: v0.7.0-Critical-Gaps Phase 6 — Multi-Handler Generation

#### **For Event-Driven Feature:**
```
Input: /one-shot-prompting:generate Add complete payment workflow (receive webhook → validate → charge → notify). In Python.

Output:
  payment/
  ├── handlers/
  │   ├── webhook_handler.py (Receives payment.initiated)
  │   ├── validation_handler.py (Validates payment)
  │   ├── charge_handler.py (Charges customer)
  │   └── notification_handler.py (Sends confirmation)
  │
  ├── services/
  │   ├── payment_service.py (Coordinates handlers)
  │   ├── stripe_service.py (Stripe integration)
  │   └── email_service.py (Email notifications)
  │
  ├── models/
  │   ├── payment_model.py (Payment data model)
  │   └── payment_event.py (Event schema)
  │
  ├── dependencies.py (Handler registration + DI wiring)
  │
  ├── migrations/
  │   └── 0001_create_payments.py
  │
  ├── tests/
  │   ├── test_webhook_handler.py
  │   ├── test_validation_handler.py
  │   ├── test_charge_handler.py
  │   └── test_notification_handler.py
  │
  └── README.md (Full integration guide)

dependencies.py:
# Automatic handler wiring + DI
async def payment_workflow():
    webhook = WebhookHandler(event_bus)
    validation = ValidationHandler(payment_service)
    charge = ChargeHandler(stripe_service)
    notification = NotificationHandler(email_service)
    
    # Wire: webhook → validation → charge → notification
    event_bus.subscribe('payment.initiated', webhook.handle)
    event_bus.subscribe('payment.validated', charge.handle)
    event_bus.subscribe('payment.charged', notification.handle)
```

#### **Assumptions Block Shows Dependencies:**
```
## Assumptions

**Workflow:**
1. Webhook receives payment.initiated
2. Validation runs on payment
3. Charge service runs on payment.validated
4. Notification runs on payment.charged
5. Retry handler catches errors at each stage

**Dependencies:**
- WebhookHandler → depends on PaymentService
- ChargeHandler → depends on StripeService
- NotificationHandler → depends on EmailService
- All handlers → depend on EventBus

**Events Generated:**
- payment.initiated (from webhook)
- payment.validated (from validation handler)
- payment.charged (from charge handler)
- payment.notification_sent (from notification handler)
- payment.failed (from error handler, triggers retry)
```

#### **README Includes Workflow Diagram:**
```markdown
## Workflow Diagram

payment.initiated
  ↓
[WebhookHandler] → validates schema
  ↓
payment.validated
  ↓
[ValidationHandler] → checks fraud/limits
  ↓
payment.ready_to_charge
  ↓
[ChargeHandler] → calls Stripe API
  ↓
payment.charged
  ↓
[NotificationHandler] → sends email
  ↓
payment.notification_sent

ERROR AT ANY STEP:
  → [RetryHandler] → exponential backoff → max 3 retries
  → payment.failed → dead letter queue
```

**Implementation:**
- Parse feature request for multiple handlers ("payment system = webhook + validation + charge + notify")
- Generate all handler files at once
- Create `dependencies.py` file that wires everything
- Generate workflow diagram in README
- Include integration tests that verify handler coordination
- Effort: ~70 hours (~15 hours per major framework for multi-handler orchestration)

---

## Gap 7: Configuration File Generation (BLOCKING FOR ENTERPRISE)

### Problem
**You claim:** "Framework-correct output"
**Reality:** Don't generate configuration overrides (settings.py, env configs, Docker secrets)
**Impact:** User must manually update settings files to enable generated features

### Current State
```
You generate: PaymentService class
But require: Settings configured (API keys, database, etc.)
Missing: Actual settings file updates
User must manually add:
  - STRIPE_API_KEY
  - PAYMENT_DATABASE
  - NOTIFICATION_EMAIL
  - etc.
```

### Solution: v0.7.0-Critical-Gaps Phase 7 — Configuration Generation

#### **For Django:**
```python
# Generated: settings_payment.py (or environment overrides)

# Add to settings.py:
# from .settings_payment import *

# OR use environment variables (generated in .env.example):
STRIPE_API_KEY = os.getenv('STRIPE_API_KEY')
PAYMENT_DB_HOST = os.getenv('PAYMENT_DB_HOST', 'localhost')
PAYMENT_WEBHOOK_SECRET = os.getenv('PAYMENT_WEBHOOK_SECRET')
NOTIFICATION_EMAIL_FROM = os.getenv('NOTIFICATION_EMAIL_FROM')

# .env.example:
STRIPE_API_KEY=sk_test_...
PAYMENT_DB_HOST=localhost
PAYMENT_WEBHOOK_SECRET=whsec_...
NOTIFICATION_EMAIL_FROM=noreply@example.com
```

#### **For FastAPI:**
```python
# Generated: config_payment.py

from pydantic_settings import BaseSettings

class PaymentSettings(BaseSettings):
    stripe_api_key: str
    stripe_webhook_secret: str
    database_url: str
    notification_email: str
    retry_max_attempts: int = 3
    retry_backoff_seconds: int = 60
    
    class Config:
        env_file = ".env"
        env_prefix = "PAYMENT_"

payment_config = PaymentSettings()

# .env.example:
PAYMENT_STRIPE_API_KEY=sk_test_...
PAYMENT_STRIPE_WEBHOOK_SECRET=whsec_...
PAYMENT_DATABASE_URL=postgresql://...
PAYMENT_NOTIFICATION_EMAIL=noreply@example.com
PAYMENT_RETRY_MAX_ATTEMPTS=3
```

#### **For Spring Boot:**
```yaml
# Generated: application-payment.yml

spring:
  jpa:
    hibernate:
      ddl-auto: validate
  datasource:
    url: ${PAYMENT_DATABASE_URL}
    username: ${PAYMENT_DB_USER}
    password: ${PAYMENT_DB_PASSWORD}

stripe:
  api-key: ${STRIPE_API_KEY}
  webhook-secret: ${STRIPE_WEBHOOK_SECRET}

notification:
  email-from: ${NOTIFICATION_EMAIL_FROM}
  
retry:
  max-attempts: 3
  backoff-seconds: 60
```

#### **For Docker:**
```dockerfile
# Generated: .env.docker (secrets in Docker Secrets or Vault)
# Dockerfile includes:
ARG STRIPE_API_KEY
ARG PAYMENT_DB_PASSWORD
ENV STRIPE_API_KEY=$STRIPE_API_KEY
ENV PAYMENT_DB_PASSWORD=$PAYMENT_DB_PASSWORD
```

**Implementation:**
- Generate environment variable templates (.env.example)
- Generate framework-specific config files (settings.py override, Pydantic settings, Spring Boot YAML)
- Include secrets management hints (Docker Secrets, Kubernetes Secrets, HashiCorp Vault)
- Effort: ~25 hours

---

## Gap 8: OpenAPI/Swagger Documentation Generation (MEDIUM PRIORITY)

### Problem
**You claim:** "Complete feature"
**Reality:** Don't auto-generate OpenAPI/Swagger specs for REST endpoints
**Impact:** REST API documentation must be maintained separately

### Current State
```
You generate: FastAPI router with endpoints
Missing: Auto-generated OpenAPI schema
User must manually:
  - Add @app.get("/docs") (FastAPI does this)
  - Write Swagger comments (Spring/Go)
  - Maintain OpenAPI YAML separately
```

### Solution: v0.7.0-Critical-Gaps Phase 8 — OpenAPI Generation

#### **For FastAPI (Auto):**
```python
# FastAPI auto-generates, but you can enhance with:

@app.post("/payments", 
    summary="Create payment",
    description="Initiate a payment transaction",
    response_model=PaymentResponse,
    responses={
        200: {"description": "Payment created"},
        400: {"description": "Invalid input"},
        409: {"description": "Duplicate payment"},
    }
)
async def create_payment(payment: PaymentRequest):
    """Create a new payment"""
```

#### **For Spring Boot:**
```java
@PostMapping("/payments")
@Operation(
    summary = "Create payment",
    description = "Initiate a payment transaction"
)
@ApiResponses({
    @ApiResponse(responseCode = "200", description = "Payment created"),
    @ApiResponse(responseCode = "400", description = "Invalid input"),
    @ApiResponse(responseCode = "409", description = "Duplicate payment"),
})
public ResponseEntity<PaymentResponse> createPayment(@RequestBody PaymentRequest request) {
    // ...
}
```

#### **For Express/Node:**
```typescript
// Generated: payment.openapi.yaml

openapi: 3.0.0
info:
  title: Payment API
  version: 1.0.0
paths:
  /payments:
    post:
      summary: Create payment
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PaymentRequest'
      responses:
        '200':
          description: Payment created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PaymentResponse'
```

**Implementation:**
- Generate OpenAPI decorators/annotations in code
- Generate openapi.yaml for export to external tools
- Include schema definitions for request/response types
- Generate Swagger UI setup code
- Effort: ~20 hours

---

## Summary: v0.7.0-Critical-Gaps Phase (COMPLETE VERSION)

**Current Status:** v0.6.0 (Large Codebase Support) ✅ DONE

**BLOCKING PHASE:** v0.7.0-Critical-Gaps (Target: Q2-Q3 2026, BEFORE v0.7.0-v1.0.0)

| Gap | Phase | Effort | Impact | Why First |
|---|---|---|---|---|
| **1. Multi-File Generation** | Phase 1 | 60h | 🔴 CRITICAL | Closes "single file only" |
| **2. Auto-Wiring Instructions** | Phase 2 | 30h | 🔴 CRITICAL | Closes "manual wiring" friction |
| **3. Migration File Generation** | Phase 3 | 40h | 🟠 HIGH | Makes migrations production-ready |
| **4. Slash Command Scaffolding** | Phase 4 | 50h | 🟠 HIGH | Enables Discord/Slack bots |
| **5. Dependency Injection** | Phase 5 | 25h | 🟠 HIGH | Enterprise DI containers |
| **6. Multi-Handler Orchestration** | Phase 6 | 70h | 🟠 HIGH | Microservices workflows |
| **7. Configuration Generation** | Phase 7 | 25h | 🟡 MEDIUM | Environment/secrets management |
| **8. OpenAPI/Swagger Docs** | Phase 8 | 20h | 🟡 MEDIUM | REST API documentation |
| **TOTAL** | — | **320 hours** | — | **Closes ALL production-ready gaps** |

**Implementation Timeline:**
- **Week 1-2:** Phase 1 + Phase 2 (multi-file + auto-wiring) — 🔴 START HERE
- **Week 3-4:** Phase 3 + Phase 4 (migrations + slash commands)
- **Week 5-6:** Phase 5 + Phase 6 (DI + multi-handler orchestration)
- **Week 7:** Phase 7 + Phase 8 (config + OpenAPI documentation)

**Result After v0.7.0-Critical-Gaps (All 8 Phases Complete):**

✅ **TRUE one-shot feature generation** (multiple coordinated files)
✅ **Zero manual wiring** (all imports/registration auto-generated)
✅ **Production migrations** (actual .py/.sql files, not notes)
✅ **Discord/Slack/CLI support** (command wrappers included)
✅ **Enterprise DI patterns** (Spring @Service, FastAPI Depends, Go wire)
✅ **Microservices workflows** (multi-handler orchestration + dependencies)
✅ **Configuration management** (env vars, secrets, settings files)
✅ **API documentation** (OpenAPI/Swagger auto-generated)

**HONEST OUTCOME:**
Your plugin becomes the **only one-shot feature generator that truly generates COMPLETE features**, not just single handlers.

**Only THEN proceed to:**
- v0.7.0: Bus Auto-Detection (NOW built on solid multi-file foundation)
- v0.8.0: Integration Testing + Catalog (Tests work across multiple files)
- v0.9.0: Domain Observability (Observability spans entire feature)
- v0.9.5: Dual-Mode Workflows (Preview mode shows complete feature)
- v1.0.0: Enterprise Launch (With ALL gaps closed)

---

**Current Status:** v0.6.0 (Large Codebase Support) ✅ DONE

**BLOCKING PHASE:** v0.7.0-Critical-Gaps (Target: Q2-Q3 2026, BEFORE v0.7.0-v1.0.0)

| Gap | Phase | Effort | Impact | Why First |
|---|---|---|---|---|
| **1. Multi-File Generation** | Phase 1 | 60h | HIGH | Closes "single file only" complaint |
| **2. Auto-Wiring Instructions** | Phase 2 | 30h | HIGH | Closes "10-20 min manual wiring" friction |
| **3. Migration File Generation** | Phase 3 | 40h | MEDIUM | Makes migrations truly production-ready |
| **4. Slash Commands** | Phase 4 | 50h | HIGH | Enables Discord/Slack bot use cases |
| **5. Dependency Injection** | Phase 5 | 25h | MEDIUM | Enterprise codebases with DI containers |
| **TOTAL** | — | **205 hours** | — | **Closes all "production-ready" gaps** |

**Timeline:**
- Week 1-2: Phase 1 + Phase 2 (multi-file + auto-wiring) — CRITICAL
- Week 3-4: Phase 3 + Phase 4 (migrations + slash commands)
- Week 5: Phase 5 (DI) + testing

**Result After v0.7.0-Critical-Gaps:**
- ✅ TRUE one-shot feature generation (multiple files, no manual splitting)
- ✅ Auto-wiring removes integration friction
- ✅ Migration files generated (not just noted)
- ✅ Discord/Slack/CLI command generation
- ✅ DI-aware for enterprise apps

**Only THEN proceed to:**
- v0.7.0: Bus Auto-Detection
- v0.8.0: Integration Testing + Catalog
- v0.9.0: Domain Observability
- v0.9.5: Dual-Mode Workflows
- v1.0.0: Enterprise Launch

---

## CRITICAL PRIORITY CHANGE

**IMPORTANT:** Previous roadmap prioritized market features (v0.6.0 bus auto-detection, etc.). 
**NEW PRIORITY:** Large codebase support is a **critical gap** that must be addressed FIRST.

**Progress Update (May 10, 2026):**
- ✅ Phase 0: Silent Planning Engine (v0.6.1 shipped)
- ✅ Phase 2-3: REST API generation (44 modules) + Batch Job systems (13 modules) = v2.0.0 shipped
- 🟡 Phase 1: Critical Integration Gaps (multi-file output, auto-wiring, migrations) — 3/7 complete, May 20 target
- 📋 Phase 4: Production Hardening (60 modules) — Q3 2026, v3.0.0
- 📋 Phase 5: Advanced Patterns (50 modules) — Q4 2026, v4.0.0

## Executive Summary (Updated May 10, 2026)

One-shot-prompting has achieved **57/177 modules (32%)** and proven **production-grade REST API + Batch Job generation** across 5 frameworks. Current status: v2.0.0 with Phase 0-3 complete.

**Strategic Focus (Phase 1 → v0.7.0):**
Completing critical integration gaps needed for marketplace launch:
1. **Multi-file output** — Dependency-ordered formatting
2. **Auto-wiring** — Zero-copy integration into projects
3. **Migrations** — Auto-generate schema changes
4. **Framework config** — Smart defaults for each framework
5. **Dependency injection** — Pattern-aware DI generation
6. **Environment config** — .env template creation
7. **Docker Compose** — Local dev environment setup

**Parallel Planning (Phase 4-5):**
- Phase 4: Production Hardening — DDD, CQRS, TDD, cost optimization, chaos testing, compliance (Jul-Sep 2026)
- Phase 5: Advanced Patterns — Microservices, real-time, GraphQL, ML, legacy modernization (Oct-Dec 2026)

---

## SECTION 0: Large Codebase Support — PHASE 0 Completion (v0.6.0-v2.0.0) ✅

### Current Achievement (May 10, 2026)

**Large codebase support is NOW COMPLETE** in v2.0.0:
- ✅ Codebase Analyzer (Phase 0.1) — Silent planning engine
- ✅ Context Extraction (Phase 0.2) — Verification harness
- ✅ Integration Adapter (Phase 2) — REST API generation with framework awareness
- ✅ Dependency Resolver (Phase 0.2) — Syntax + import validation
- ✅ Convention Matcher (Phase 2) — Framework-specific patterns
- ✅ Test Integration (Phase 2) — Framework test suites
- ✅ Migration Generator (Phase 1 partial) — Auto-migration support (completing May 20)
- ✅ API Consistency (Phase 2) — OpenAPI/Swagger documentation
- ✅ Documentation (Phase 2) — Auto-generated API docs
- ✅ Deployment Context (Phase 3) — Docker, Kubernetes, Terraform

**What This Enables:**
- Production-ready REST API generation for enterprise codebases
- Batch job systems with queues, monitoring, observability
- Zero manual wiring for Django, FastAPI, NestJS, Express, Spring Boot
- Real-world codebase support (proven on 10K-100K+ LOC projects)
- Enterprise market adoption (5-8% penetration → target 15-20%)

---

### 10 Missing Pieces: Detailed Implementation Plans

#### **1. Codebase Analyzer Module** (NEW MCP Tool)

**Problem:**
Including entire codebase as context burns tokens. Need intelligent extraction in <1000 tokens.

**Solution:**
```
NEW MCP Tool: codebase-analyzer

Input:
  @path/to/project
  
Output (single JSON, <1000 tokens):
  {
    "language": "python",
    "framework": ["django", "drf"],
    "patterns": {
      "error_handling": "custom_exceptions.py (CustomAPIError)",
      "logging": "structured_logging + structlog",
      "validation": "pydantic.BaseModel + custom validators",
      "async_style": "asyncio native",
      "testing": "pytest + factories"
    },
    "dependencies": {
      "critical": ["django==4.2", "drf==3.14", "pydantic==2.0"],
      "messaging": "celery + redis",
      "database": "postgresql via ORM"
    },
    "structure": {
      "app_root": "apps/",
      "tests": "tests/ (pytest)",
      "config": "config/ (settings.py, env-based)",
      "shared_libs": "libs/ (utilities, decorators, mixins)"
    },
    "conventions": {
      "naming": "snake_case (functions/vars), PascalCase (classes)",
      "docstrings": "Google style",
      "type_hints": "strict (no `Any`)",
      "error_messages": "app-specific error codes (ERR_001, etc)"
    }
  }
```

**Files to Create:**
- `src/taleemabad_data_mcp/codebase_analyzer/` — new MCP module
- `src/taleemabad_data_mcp/codebase_analyzer/detectors/` — framework/pattern detectors
  - `framework_detector.py` — detect Django, FastAPI, Spring, Rails, etc
  - `pattern_detector.py` — identify error handling, logging, validation styles
  - `dependency_analyzer.py` — parse requirements.txt, package.json, go.mod, etc
  - `structure_analyzer.py` — map directory structure

**Effort:** ~30 hours
**Testing:** Test against 10 real projects (various languages/frameworks)
**Success Metric:** <1000 token output, 90%+ accuracy on pattern detection

---

#### **2. Context Extraction Strategy** (Integration with Analyzer)

**Problem:**
How to pass "this is a Django project with DRF + Celery" without including all model definitions?

**Solution:**
SKILL.md Enhancement:

```markdown
## Input: Codebase Context

If working on existing project:

Option A (Automatic):
  @path/to/project
  
  → Claude runs codebase-analyzer internally
  → Extracts structure + patterns in <1000 tokens
  → Passes to generation prompt

Option B (Manual):
  [Provide codebase summary]
  Framework: Django 4.2 + DRF
  Patterns: Custom exception base class in errors.py, structlog-based logging
  Dependencies: asyncio, Celery for async tasks
  API Style: REST with custom error envelope {"success": bool, "data": {...}}
  
Option C (URL/File):
  Codebase: ./my-project/CODEBASE_SUMMARY.md
  [User pre-creates summary of key patterns]
```

**Implementation:**
- Add `codebase` parameter to `/one-shot-prompting:generate`
- If `@path/to/project` provided → run analyzer → extract context
- Pass extracted context (not raw codebase) to Claude generation

**Files to Modify:**
- `SKILL.md` — add codebase input section
- `commands/generate.md` — update to handle codebase parameter
- `prompts/generation.md` — update system prompt to expect codebase context

**Effort:** ~15 hours
**Success Metric:** Users can provide project path; plugin generates context-aware code

---

#### **3. Integration Adapter** (NEW Component)

**Problem:**
Plugin generates code in isolation. Django needs models.py + views.py + admin.py, but plugin generates single class.

**Solution:**
Framework-aware code generation:

```python
# NEW: src/taleemabad_data_mcp/adapters/

class DjangoAdapter:
    """Convert generic payment service → Django app structure"""
    
    def adapt_module(generic_code, project_context):
        return {
            'models.py': generic_code.transform_to_django_models(),
            'views.py': generic_code.transform_to_drf_views(),
            'serializers.py': generic_code.transform_to_drf_serializers(),
            'admin.py': generic_code.register_in_admin(),
            'migrations/0001_initial.py': generate_migration(),
            'tasks.py': extract_celery_tasks(),
            'tests/test_models.py': generate_model_tests(),
            'tests/test_views.py': generate_api_tests(),
        }

class FastAPIAdapter:
    """Convert generic service → FastAPI routers + dependencies"""
    
    def adapt_module(generic_code, project_context):
        return {
            'routers/payment.py': generic_code.as_fastapi_router(),
            'schemas/payment.py': generic_code.as_pydantic_schema(),
            'dependencies.py': add_to_existing_deps(),
            'tests/test_payment.py': generate_integration_tests(),
        }

class SpringBootAdapter:
    """Convert generic service → Spring Boot service + controller + repo"""
    ...

class RailsAdapter:
    """Convert generic service → Rails models + controllers + migrations"""
    ...

class GoAdapter:
    """Convert generic service → Go handler + interfaces + dependency injection"""
    ...
```

**Implementation Plan:**
- Detect framework from codebase analysis
- Load appropriate adapter
- Transform generic module into framework-specific files
- Update SKILL.md assumptions: "Detected Django; generated models.py, views.py, serializers.py"

**Effort:** ~60 hours (10-15 hours per adapter × 4-5 frameworks)
**Testing:** Test against real Django/FastAPI/Spring/Rails projects
**Success Metric:** 80%+ of generated files need zero refactoring

---

#### **4. Dependency Resolver** (NEW Component)

**Problem:**
Plugin generates code using pydantic v2, but project locked to v1.10 → incompatible.

**Solution:**
```python
# NEW: src/taleemabad_data_mcp/dependency_resolver/

class DependencyResolver:
    def check_compatibility(generated_code, existing_dependencies):
        """
        Check: does generated code work with existing dependencies?
        
        Input:
          generated_code: full module (imports, usage patterns)
          existing_dependencies: parsed requirements.txt / package.json / go.mod
        
        Output:
          {
            "compatible": True/False,
            "conflicts": [
              {"module": "pydantic", "generated_version": "2.0", 
               "existing": "1.10", "severity": "high",
               "fix": "Rerun with 'use pydantic v1 compatible code'"}
            ],
            "missing": ["redis", "asyncpg"],
            "suggested_updates": [
              {"module": "pytest", "from": "6.2", "to": "7.0", "reason": "async support"}
            ]
          }
        ```

**Files to Create:**
- `src/taleemabad_data_mcp/dependency_resolver/` 
  - `compatibility_checker.py` — check version conflicts
  - `requirement_parser.py` — parse requirements.txt, package.json, go.mod, Gemfile, etc
  - `suggestion_engine.py` — suggest compatible versions

**Integration:**
- After code generation, run dependency check
- Surface conflicts in assumptions block: "⚠️ Generated uses pydantic v2, project locked to v1.10. Rerun with 'use pydantic v1' to fix."
- Auto-update requirements if user approves

**Effort:** ~25 hours
**Success Metric:** Catch 95%+ of version conflicts before user runs code

---

#### **5. Convention Matcher** (NEW Component)

**Problem:**
Project uses `CustomAPIException` for errors; plugin generates `ValueError` and `TypeError` → inconsistent.

**Solution:**
Learn conventions, apply them:

```python
# NEW: src/taleemabad_data_mcp/convention_matcher/

class ConventionMatcher:
    def extract_conventions(codebase_context):
        """Learn project conventions"""
        return {
            "error_handling": {
                "base_exception": "CustomAPIException",
                "app_errors": ["ValidationError", "ResourceNotFoundError", "PermissionDeniedError"],
                "pattern": "raise CustomAPIException(code='ERR_001', message='...')"
            },
            "logging": {
                "library": "structlog",
                "pattern": "logger.info('action', user_id=user_id, data={...})"
            },
            "validation": {
                "library": "pydantic.BaseModel",
                "pattern": "class PaymentData(BaseModel): ...",
                "custom_validators": "yes"
            },
            "naming": {
                "functions": "snake_case",
                "classes": "PascalCase",
                "constants": "UPPER_SNAKE_CASE"
            },
            "docstring_style": "Google",
            "type_hints": "strict (no Any)"
        }
    
    def apply_conventions(generated_code, conventions):
        """Rewrite generated code to match conventions"""
        # Replace all ValueError → CustomAPIException
        # Replace all logger.error → logger.info with severity field
        # Ensure all functions have Google-style docstrings
        # Ensure zero `Any` type hints
        ...
```

**Implementation:**
- Run after codebase analysis
- Extract conventions (error classes, logging style, naming, docstrings)
- Rewrite generated code to match
- Update assumptions: "Applied project conventions: CustomAPIException for errors, structlog for logging"

**Effort:** ~30 hours
**Success Metric:** Generated code matches team's style 95%+

---

#### **6. Test Integration** (Enhancement)

**Problem:**
Plugin generates tests with custom `@pytest.fixture(mocks)`; project has factories in `tests/factories.py` and conftest fixtures → tests don't use existing patterns.

**Solution:**
Analyze existing tests, use same patterns:

```python
# Enhancement to test generation:

def generate_tests(generated_module, test_conventions):
    """
    test_conventions = {
      "fixtures_location": "tests/conftest.py",
      "factories_location": "tests/factories.py",
      "base_test_class": "APITestCase",
      "mock_style": "unittest.mock (not pytest-mock)",
      "existing_fixtures": ["authenticated_user", "sample_payment"]
    }
    """
    
    # Instead of:
    # @pytest.fixture
    # def mock_payment_service():
    #     return Mock()
    
    # Generate:
    # from tests.factories import PaymentFactory
    # from tests.conftest import authenticated_user
    # 
    # def test_payment_processing(authenticated_user):
    #     payment = PaymentFactory.create()
    #     ...
```

**Implementation:**
- Scan `tests/` directory for existing fixtures, factories, test patterns
- Parse conftest.py for available fixtures
- Generate tests using existing patterns
- Add generated tests to existing test files (not new files)

**Effort:** ~20 hours
**Success Metric:** Generated tests run with existing test suite 100%

---

#### **7. Migration Generator** (NEW Component)

**Problem:**
Plugin generates Payment model, but project uses Django migrations. Need to:
1. Generate migration file (0002_add_payments_table.py)
2. Ensure backward compatibility (if adding NOT NULL column, provide default)
3. Run against existing schema

**Solution:**
```python
# NEW: src/taleemabad_data_mcp/migration_generator/

class MigrationGenerator:
    def generate_migration(new_models, existing_schema, framework):
        """
        new_models: [Payment, PaymentLog] classes with fields
        existing_schema: parsed schema from migration history
        framework: 'django', 'alembic', 'flyway', 'rails', 'knex'
        
        Output:
          For Django:
            migrations/0002_add_payments_table.py
              - CreateModel for Payment
              - CreateModel for PaymentLog
              - Backward-compatible (if adding NOT NULL, includes default)
          
          For Alembic:
            alembic/versions/0002_add_payments.py
          
          etc.
        """
    
    def check_backward_compatibility(migration, existing_data):
        """
        Check: can this migration run without data loss?
        
        Example:
          migration: ADD COLUMN payment.currency NOT NULL
          existing_data: 1M payment records
          result: ❌ Backward incompatible (no default for existing records)
          fix: Add DEFAULT 'USD' or change to nullable
        """
```

**Implementation:**
- Detect migration tool (Django/Alembic/Flyway/Rails/Knex)
- Generate migration file in correct format
- Check backward compatibility; warn if issues
- Include rollback script

**Effort:** ~35 hours
**Success Metric:** Generated migrations run cleanly against live schema

---

#### **8. API Consistency Enforcer** (NEW Component)

**Problem:**
Project uses REST API with format:
```json
{
  "success": true,
  "data": {...},
  "pagination": {...}
}
```
Plugin generates different format:
```json
{
  "code": 200,
  "result": {...}
}
```

**Solution:**
Extract API conventions, enforce:

```python
# NEW: src/taleemabad_data_mcp/api_enforcer/

class APIConsistencyEnforcer:
    def extract_api_style(codebase):
        """
        Analyze existing API endpoints, extract pattern
        """
        return {
            "envelope_style": "success/data/pagination",
            "error_format": {"success": False, "error": {...}},
            "versioning": "/api/v1/",
            "auth": "Bearer token in header",
            "pagination": "limit/offset with total_count",
            "timestamps": "ISO8601 in UTC"
        }
    
    def apply_api_style(generated_endpoints, style):
        """
        Rewrite endpoints to match style
        """
        # All responses wrapped in {success, data, pagination}
        # All errors wrapped in {success: false, error: {...}}
        # All endpoints under /api/v1/
        # All timestamps ISO8601
```

**Implementation:**
- Scan existing API code (views, routes, endpoints)
- Extract response format, error handling, versioning
- Rewrite generated endpoints to match
- Update assumptions: "Matched API style to existing endpoints"

**Effort:** ~25 hours
**Success Metric:** Generated endpoints integrate seamlessly with existing API

---

#### **9. Documentation Integrator** (NEW Component)

**Problem:**
Project uses Sphinx for docs; plugin generates README.md. Generated code never shows up in docs.

**Solution:**
```python
# NEW: src/taleemabad_data_mcp/documentation_integrator/

class DocumentationIntegrator:
    def detect_doc_system(codebase):
        """
        Detect: Sphinx? MkDocs? Confluence? Plain markdown in docs/?
        """
        return {
            "system": "sphinx",
            "format": "rst",
            "location": "docs/",
            "api_doc_tool": "autodoc"
        }
    
    def generate_docs(generated_module, doc_system, codebase_context):
        """
        For Sphinx:
          Generate .rst in docs/modules/payment.rst
          Auto-include in docs/index.rst
        
        For MkDocs:
          Generate .md in docs/reference/payment.md
          Auto-include in mkdocs.yml
        
        For Confluence:
          Generate markup for Confluence page
        """
```

**Implementation:**
- Detect existing doc system
- Generate docs in matching format
- Auto-integrate into doc build (add to index, update nav)
- Update assumptions: "Generated docs in Sphinx format"

**Effort:** ~20 hours
**Success Metric:** Generated module shows up in project docs automatically

---

#### **10. Deployment Context Aware** (NEW Component)

**Problem:**
Project uses Terraform for IaC. Plugin generates Dockerfile + kubernetes-deployment.yaml, but doesn't integrate with existing Terraform modules.

**Solution:**
```python
# NEW: src/taleemabad_data_mcp/deployment_aware/

class DeploymentContextAware:
    def detect_deployment_context(codebase):
        """
        Detect: Terraform? Helm? CloudFormation? Custom scripts?
        CI/CD: GitHub Actions? GitLab CI? Jenkins?
        Environments: dev/staging/prod?
        """
        return {
            "iac": "terraform",
            "iac_location": "infrastructure/",
            "modules": ["aws_lambda", "aws_ecs", "aws_rds"],
            "ci_cd": "github_actions",
            "ci_location": ".github/workflows/",
            "environments": ["dev", "staging", "prod"],
            "registry": "ECR (AWS)"
        }
    
    def generate_deployment_artifacts(generated_code, context):
        """
        For Terraform:
          Generate terraform/modules/payment_service/
            main.tf (define service)
            variables.tf
            outputs.tf
        
        For GitHub Actions:
          Generate .github/workflows/payment-service-deploy.yml
        
        Integration:
          - Reference existing terraform modules
          - Respect environment-specific configs
          - Inherit IAM roles, VPC, security groups from existing setup
        """
```

**Implementation:**
- Scan for Terraform, Helm, CloudFormation, CI config
- Generate IaC in matching format
- Reference existing modules (don't duplicate)
- Auto-integrate into CI/CD pipeline
- Update assumptions: "Generated Terraform modules compatible with existing infrastructure"

**Effort:** ~30 hours
**Success Metric:** Generated module deploys using existing infrastructure

---

### Summary: 10 Pieces Implementation Timeline (v0.6.0-Foundation)

| # | Component | Hours | Effort | Status |
|---|-----------|-------|--------|--------|
| 1 | Codebase Analyzer | 30 | Medium | ⏳ Start first |
| 2 | Context Extraction | 15 | Low | ⏳ Depends on #1 |
| 3 | Integration Adapter | 60 | High | ⏳ Depends on #1 |
| 4 | Dependency Resolver | 25 | Medium | ⏳ Parallel |
| 5 | Convention Matcher | 30 | Medium | ⏳ Depends on #1 |
| 6 | Test Integration | 20 | Low | ⏳ Depends on #1 |
| 7 | Migration Generator | 35 | Medium | ⏳ Depends on #1 |
| 8 | API Consistency | 25 | Medium | ⏳ Depends on #1 |
| 9 | Documentation | 20 | Low | ⏳ Depends on #1 |
| 10 | Deployment Context | 30 | Medium | ⏳ Depends on #1 |
| | **TOTAL** | **290 hours** | **High Effort** | |

**Recommended Timeline:**
- **Phase 1 (Week 1-2):** Build Codebase Analyzer (#1) + Context Extraction (#2) — foundational
- **Phase 2 (Week 3-4):** Build Integration Adapter (#3) + Dependency Resolver (#4) — core integration
- **Phase 3 (Week 5-6):** Build Convention Matcher (#5) + Test Integration (#6) — code quality
- **Phase 4 (Week 7-8):** Build Migration Generator (#7) + API Consistency (#8) — data safety
- **Phase 5 (Week 9):** Build Documentation (#9) + Deployment (#10) — visibility

**Total Effort:** ~290 hours (one dev, ~7 weeks full-time)

---

## Part 1: Core Strengths to Preserve

These are **non-negotiable** — they define one-shot's identity:

### 1. Flow-First Ideology
- **What it means:** Code in 1 turn, iterate by regeneration, skip planning for simple events
- **Keep:** No approval gates, no clarifying questions, assumptions visible upfront
- **Never add:** Spec phase, approval workflows, multi-turn planning
- **Why it matters:** Developers who want speed choose us over Superpowers

### 2. Explicit Assumptions Block
- **What it means:** Every non-trivial choice is stated; user reruns with overrides, not conversations
- **Keep:** Always first section, always actionable, never vague
- **Never add:** Implicit defaults, hidden decision logic
- **Why it matters:** Users know exactly what they're getting; friction drops on iteration

### 3. Iteration by Regeneration
- **What it means:** User says "use token bucket instead" → entire module regenerated, not patched
- **Keep:** Simple to understand, stateless, encourages bold choices
- **Never add:** Incremental patching, merge conflicts, state tracking
- **Why it matters:** Low cognitive load, high velocity

### 4. Multi-Language Parity
- **What it means:** Python, Go, Rust, TypeScript, Java with idiomatic quality in each
- **Keep:** Type hints, linting compliance, language-native idioms in all 5
- **Never add:** Lowest-common-denominator code, language-specific limitations
- **Why it matters:** Dev teams can adopt regardless of tech stack

### 5. Event-Driven Focus
- **What it means:** We own the event bus ecosystem, not generic feature generation
- **Keep:** Refuse non-event-driven requests narrowly; lean into sidecar/subscriber patterns
- **Never add:** CRUD apps, UI components, cross-cutting refactors
- **Why it matters:** Deep expertise in one domain beats shallow coverage of many

---

## Part 2: Known Weaknesses & Systematic Mitigation Strategy

### Current Weaknesses (v0.5.0) and How They're Being Addressed

| Weakness | Current Impact | Root Cause | Mitigation Version | Solution |
|----------|---|---|---|---|
| **No codebase awareness** | Users must manually adapt generated code for their specific bus (asyncio vs Tokio vs NestJS EventEmitter) | Plugin assumes generic event bus; can't see project structure | v0.6.0 | Auto-detect bus from imports/package.json; generate bus-native code (no manual adaptation needed) |
| **No catalog validation** | Users must manually check generated events against their SKILLS.md; event naming conflicts possible | No access to project's event catalog; generates "reasonable" event names | v0.8.0 | Parse catalog from codebase/URL; enforce naming constraints; surface violations in assumptions block |
| **Integration tests missing** | Users generate unit tests, must wire into larger ecosystem manually; integration failures discovered late | Generated tests are isolated; no knowledge of bus initialization or other subscribers | v0.7.0 | Generate integration test scaffold that connects to real bus (mocked); include wiring instructions for detected bus |
| **Generic observability** | Observability patterns are one-size-fits-all (structured logging + OpenTelemetry + Prometheus); don't match domain | v0.4.0 observability assumes REST API pattern; event systems have different needs | v0.9.0 | Domain-specific observability: frame timing for games, latency percentiles for trading, message backlog for bots |
| **Single-feature only** | Microservices need N event handlers; users must run plugin N times | Plugin is intentionally single-shot; designed for one feature per invocation | N/A (Design constraint) | Accept as feature, not bug; users understand iteration model; document pattern for multi-handler services |

---

### Weakness Mitigation Timeline

#### **Weakness 1: No Codebase Awareness** → **v0.6.0 (Q2 2026)**
**Current:** User writes README adaptation notes: "If using asyncio, call `bus.subscribe(...)` instead of `bus.on(...)`"

**Problem:** Manual adaptation = friction; users make mistakes; generated code doesn't match their project.

**v0.6.0 Solution:**
- Scan codebase for imports: `import asyncio`, `from tokio import`, `from fastapi import`, `from django.dispatch import Signal`, etc.
- Infer bus: asyncio (Python) → generate asyncio-native code; Tokio (Rust) → generate Tokio-native; NestJS → generate EventEmitter pattern
- Update assumptions: "Detected asyncio-based Python project"
- Generate asyncio code directly: `async def handle()`, `await bus.emit()`, `asyncio.create_task()` — not generic stubs
- README says: "FastAPI BackgroundTasks" not "generic async bus"

**Success Metric:** Users copy-paste generated module, zero adaptation needed; generated code matches project's bus exactly.

---

#### **Weakness 2: No Catalog Validation** → **v0.8.0 (Q4 2026)**
**Current:** User checks generated events manually against SKILLS.md; often miss mismatches.

**Problem:** Event naming conflicts; users generate `rate.exceeded` but catalog already has `rate_limit_exceeded`; integration fails.

**v0.8.0 Solution:**
- User provides catalog URL or file path in prompt: "Generate rate limiter. Catalog: ./SKILLS.md"
- Claude parses catalog; extracts event names, schemas, constraints
- In assumptions block, state: "Generated event `rate.exceeded` not in catalog"
- User has options:
  - Rerun with "use existing event `rate_limit_exceeded` instead"
  - Rerun with "add `rate.exceeded` to catalog"
- Auto-generate catalog entry (SKILLS.md format) if user chooses to extend

**Success Metric:** Enterprise customers can enforce catalog governance; zero naming conflicts; audit trail of new events.

---

#### **Weakness 3: Integration Tests Missing** → **v0.7.0 (Q3 2026)**
**Current:** Generated tests are unit tests only; users must write integration test scaffold manually.

**Problem:** Unit tests pass; integration fails (bus not initialized, subscriber not wired); discovered in production.

**v0.7.0 Solution:**
- Generate integration test scaffold (in addition to unit tests):
  ```python
  @pytest.mark.asyncio
  async def test_rate_limiter_integration_with_bus():
      # Setup: spin up mock async bus
      bus = MockAsyncBus()
      rate_limiter = RateLimiter(bus=bus)
      
      # Emit 5 events rapidly
      for i in range(5):
          await bus.emit('message.received', {'user_id': 'user1'})
      
      # Assert: rate limit kicks in, excess events dropped
      assert rate_limiter.dropped >= 3
      
      # Assert: DLQ event emitted
      dlq_events = await bus.get_events('rate.exceeded')
      assert len(dlq_events) >= 1
  ```
- Include testcontainers setup (real Kafka/RabbitMQ in Docker):
  ```python
  @pytest.fixture
  async def kafka_broker():
      # Spin up real Kafka in testcontainer
      container = KafkaContainer(image="confluentinc/cp-kafka:7.0.1")
      container.start()
      yield container
      container.stop()
  ```
- README includes: "Run integration tests with `pytest tests/test_integration.py`"

**Success Metric:** Users run integration tests locally before deploying; confidence increases; fewer production surprises.

---

#### **Weakness 4: Generic Observability** → **v0.9.0 (Q1 2027)**
**Current:** v0.4.0 observability block is generic: structured logging, OpenTelemetry, Prometheus. Works for REST; not optimal for events.

**Problem:** Games need frame timing, trading bots need latency percentiles, ML pipelines need feature freshness — one template doesn't fit all.

**v0.9.0 Solution:**
- User specifies domain in prompt: "Add rate limiter for game server" or "trading bot" or "ML pipeline"
- Domain-specific observability generated:

**Game Server Metrics:**
```python
# Frame-aware metrics
@metric.counter('game.events_per_frame')
@metric.histogram('game.event_processing_latency_ms')
async def handle_player_moved():
    start = perf_counter()
    # ... logic ...
    latency = (perf_counter() - start) * 1000
    
# Event queue health
@metric.gauge('game.event_queue_depth')
async def monitor_queue():
    depth = await bus.queue_depth()
    return depth

# Per-player metrics
@metric.counter('game.players_active')
@metric.histogram('game.player_event_latency_ms', labels=['player_id'])
```

**Trading Bot Metrics:**
```python
# Latency-critical metrics
@metric.histogram('trade.roundtrip_latency_ms', buckets=[1, 5, 10, 50, 100])
@metric.counter('trade.missed_opportunity', help='Events arrived too late to act on')
async def handle_price_update(event):
    latency = now() - event.timestamp
    if latency > 100:  # 100ms threshold
        metric_missed_opportunity.inc()

# Cost tracking (for trading, cost per operation matters)
@metric.counter('trade.operation_cost_cents', labels=['operation_type'])
async def log_cost(operation, cost):
    metric_cost.labels(operation).inc(cost)

# P99 latency (critical for trading)
@metric.histogram('trade.p99_latency_ms')
```

**ML Pipeline Metrics:**
```python
# Feature freshness (critical for ML)
@metric.gauge('ml.feature_freshness_seconds', labels=['feature_name'])
async def monitor_feature_freshness():
    freshness = now() - last_feature_update
    metric_freshness.set(freshness)

# Inference latency
@metric.histogram('ml.inference_latency_ms', buckets=[10, 50, 100, 500, 1000])

# Data quality
@metric.gauge('ml.feature_null_percentage', labels=['feature_name'])
@metric.counter('ml.outlier_detected', labels=['feature_name'])
```

- Assumptions block: "Detected game server domain; included frame timing metrics"
- README section: "Observability for game servers: frame metrics, queue depth, per-player latency"

**Success Metric:** Generated observability is domain-appropriate; users don't need to customize metrics; monitoring works out-of-box.

---

#### **Weakness 5: Single-Feature Only** → **Design Constraint (N/A — Intentional)**
**Weakness:** Microservices need N event handlers; users run plugin N times (once per handler).

**Why This Is NOT a Bug — It's a Feature:**
- One-shot = one feature per invocation; it's the core design principle
- Users understand iteration model: "Generate handler for order.created, then for order.paid, then for order.shipped" (3 runs)
- Advantage: each handler is independently versioned, tested, deployed; no coupling
- Pattern for multi-handler services:
  ```
  Run 1: /one-shot-prompting:generate order.created handler
  Run 2: /one-shot-prompting:generate order.paid handler
  Run 3: /one-shot-prompting:generate order.shipped handler
  
  → 3 independent, well-tested modules
  → Each can be updated without affecting others
  → Each has its own rerun history
  ```

**Mitigation (Documentation, Not Code):**
- README includes: "For microservices with multiple handlers, run plugin once per handler. Each invocation generates an independent, testable module."
- Rerun hints show: "Generate another handler with 'In [language]' to create sibling handlers in same language"
- No change needed; users accept single-feature model

---

## Part 3: Strategic Gaps (vs. Superpowers & Competitors)

### Gap 1: Catalog Awareness
**Problem:**
- User has strict event catalog (SKILLS.md, event registry, proto schemas)
- We generate new events; user then has to manually wire them into catalog
- Rerun hint "use existing event X instead" requires user to know their catalog

**Current Status:** Manual override via rerun hints

**Future v0.6.0+ Solution:**
- **Phase 1 (v0.6.0):** Accept catalog URL/file in prompt: "Generate rate limiter, catalog: ./SKILLS.md"
- **Phase 2 (v0.7.0):** Auto-detect catalog in codebase via codebase-exploration MCP
- **Phase 3 (v0.8.0+):** Enforce catalog constraints by default; surface mismatches in assumptions block

**Execution:**
```
/one-shot-prompting:generate Add rate limiter for message.received. 
Catalog: https://github.com/myorg/event-catalog/SKILLS.md
```

### Gap 2: Project-Shape Detection (Bus Auto-Detection)
**Problem:**
- We assume "generic async bus"; user adapts README for their specific bus
- Possible buses: asyncio, Tokio, NestJS EventEmitter, Django signals, RabbitMQ, Kafka, etc.
- Manual adaptation creates friction; code snippets are language-agnostic stubs

**Current Status:** User provides bus name in adaptation notes

**Future v0.6.0+ Solution:**
- **Phase 1 (v0.6.0):** Accept bus hint in prompt: "In Python with asyncio" or "NestJS EventEmitter"
- **Phase 2 (v0.7.0):** Codebase exploration + auto-detect: scan imports/package.json, infer bus
- **Phase 3 (v0.8.0+):** Generate adapter code directly for detected bus (no manual edits needed)

**Execution:**
```
/one-shot-prompting:generate Add rate limiter. Auto-detect bus from codebase.

→ Claude scans imports, finds "from fastapi import FastAPI, BackgroundTasks"
→ Generates asyncio-native consumer, not generic stub
→ README says "FastAPI BackgroundTasks" not "generic async bus"
```

**Supported Bus Detection:**
| Bus | Detection Pattern | Languages | Status |
|-----|-------------------|-----------|--------|
| asyncio | `import asyncio`, `async def` | Python | v0.6.0 planned |
| Tokio | `tokio::spawn`, `#[tokio::main]` | Rust | v0.6.0 planned |
| NestJS EventEmitter | `import { EventEmitter }` | TypeScript | v0.6.0 planned |
| Django signals | `from django.dispatch import Signal` | Python | v0.6.0 planned |
| Go channels | `go func()`, `chan` | Go | v0.7.0 planned |
| Kafka | Broker connection env vars | All | v0.5.0 (done) |
| RabbitMQ | Broker connection env vars | All | v0.5.0 (done) |

### Gap 3: Integration Testing Stub Generation
**Problem:**
- We generate unit tests; user must manually wire into integration tests
- Missing: how does this module connect to rest of async ecosystem?
- Users copy unit tests, then discover integration failure

**Current Status:** Unit tests only; README has vague "integration test setup" section

**Future v0.7.0+ Solution:**
- Generate integration test scaffold that connects to real event bus (mocked or testcontainers)
- Include test helper: fixture to spin up bus, emit test event, verify response
- Show wiring pattern specific to detected bus (asyncio.create_task, go func(), tokio::spawn, etc.)

**Execution:**
```python
# Generated test with bus integration
@pytest.mark.asyncio
async def test_rate_limiter_with_bus():
    # Setup: spin up mock async bus
    bus = MockAsyncBus()
    rate_limiter = RateLimiter(bus=bus)
    
    # Emit 5 events
    for i in range(5):
        await bus.emit('message.received', {'user_id': 'user1'})
    
    # Assert rate limit + DLQ behavior
    assert rate_limiter.dropped == 3
```

### Gap 4: Cross-Module Dependency Awareness
**Problem:**
- We generate one module; don't know where it lives in larger codebase
- Can't see: shared bus initialization, other subscribers, configuration
- Generated code assumes clean insertion; might have hidden conflicts

**Current Status:** Assume user can adapt; no visibility into codebase structure

**Future v0.7.0+ Solution:**
- Codebase exploration: scan project structure, find:
  - Central event bus initialization (where?)
  - Existing subscribers (how are they wired?)
  - Configuration patterns (env vars, config files, DI containers)
  - Package/module layout
- In assumptions block, state: "Found bus init in `app/events.py`, added subscriber to that file"
- Generate instructions: "Import this module in `app/main.py`, call `await subscribe_rate_limiter(bus)`"

### Gap 5: Observability Patterns (Beyond Generic Templates)
**Problem:**
- v0.4.0 added generic OpenTelemetry/Prometheus patterns
- But observability needs vary: game servers want frame timing, bots want message latency, ML systems want feature quality
- Generic structured logging + distributed tracing works for REST; less clear for event streams

**Current Status:** Generic observability block; user customizes

**Future v0.7.0+ Solution:**
- Domain-specific observability:
  - **Games:** Frame timing, event backlog depth, player latency percentiles
  - **Bots:** Message roundtrip time, retry rates, cost per operation
  - **Real-time systems:** Event lag, buffer utilization, throughput SLOs
  - **ML pipelines:** Feature freshness, inference latency, data quality metrics
- User specifies domain in prompt: "In Python for game server" → include frame-time metrics
- Observability block grows with domain context, not just generic patterns

---

## Part 3: Market Positioning & Growth Strategy

### Why Event-Driven is Underserved
- **Trend:** Games, bots, real-time finance, IoT, streaming — all event-driven
- **Competitors:** Superpowers is general-purpose code generation; we're specialized
- **Gap:** No other plugin combines **event-driven + one-shot + multi-language + explicit assumptions**
- **Market:** Developers building event systems are less interested in spec-first; they want velocity

### Target Markets (Ranked by TAM + Fit)

| Market | Size | Fit | Why | Entry Point |
|--------|------|-----|-----|------------|
| Game Dev (game engines + multiplayer backends) | Large | Excellent | Event-driven is native; server-client comms are async | "Generate handler for player.joined event in Rust for Bevy" |
| Bot Builders (Discord/Slack/Telegram) | Medium | Excellent | Bots are pure event subscribers; multi-language needed | "Generate Discord slash command handler that listens to message.created" |
| Real-Time Finance (trading bots, market data) | Large | Very Good | Ultra-low-latency event systems; Go/Rust native | "Generate Kafka consumer for trade.executed, emit buy signal" |
| IoT + Edge Systems | Medium | Good | Devices = event sources; need Go/Rust | "Generate MQTT subscriber for sensor.reading in Go" |
| Startup Backend Teams | Large | Good | Early-stage teams build event-driven for scalability | "Generate microservice handler for order.created" |

### Marketing Strategy (Local Plan, Not Committed)

#### Phase 1: Thought Leadership (Months 1-3)
- Write: "Why Event-Driven Code Needs One-Shot" — compare to Superpowers' spec-first
- Post in: r/rust, r/golang, game dev communities, Discord bot dev servers
- Message: "Event-driven systems require constant iteration. You don't spec events upfront. Regenerate with new constraints, not conversations."
- Target: Developers already building event systems who are frustrated with spec-first tools

#### Phase 2: Product Differentiation (Months 3-6)
- Add bus auto-detection (v0.6.0)
- Add "why this is different" section to README: explicit comparison table vs Superpowers
- Create 3-5 short demo videos:
  - "Generate Kafka consumer in 30 seconds" (Rust example)
  - "Regenerate with exactly-once delivery" (showing rerun flow)
  - "Game server event handler from one sentence" (Go example)

#### Phase 3: Community Building (Months 6+)
- GitHub Discussions: "Event-driven patterns you've regenerated"
- Discord community: share generated modules, discuss design patterns
- Contribute examples to popular libraries (Bevy, tokio, Kafka, etc.)

#### Phase 4: Premium Features (v0.9.0+, Months 9+)
- Paid tier: "Catalog-aware generation" (enforce SKILLS.md automatically)
- Paid tier: "Architecture review" (get Claude to review your bus design before generating)
- Free tier: stays free; paid is convenience/assurance

### Positioning Statement (Draft)
```
One-Shot Prompting is the event-driven code generator for developers 
who iterate fast. 

Not plans. Not questions. One prompt → complete module with stated 
assumptions. Regenerate with constraints, not conversations. 

Built for game servers, trading bots, real-time systems, and teams 
that ship fast. Supports Python, Go, Rust, TypeScript, Java. 
Message queues: Kafka, RabbitMQ, SQS, Pub/Sub, Service Bus.

Unlike Superpowers (spec-first), we're flow-first. Your assumptions 
are visible. Your iteration is fast.
```

---

## Part 4: Feature Roadmap (UPDATED May 10, 2026)

### ✅ v0.6.0-v2.0.0: Large Codebase Support COMPLETE

**MILESTONE ACHIEVED (May 2026):** All 10 pieces for large codebase integration complete

**Features Delivered:**
1. ✅ Codebase Analyzer Module (Phase 0.1)
2. ✅ Context Extraction Strategy (Phase 0.2)
3. ✅ Integration Adapter (Phase 2 — REST API)
4. ✅ Dependency Resolver (Phase 0.2)
5. ✅ Convention Matcher (Phase 2)
6. ✅ Test Integration (Phase 2)
7. ✅ Migration Generator (Phase 1 — completing May 20)
8. ✅ API Consistency Enforcer (Phase 2)
9. ✅ Documentation Integrator (Phase 2)
10. ✅ Deployment Context Aware (Phase 3)

**Delivered in:**
- Phase 0: 4 modules, 475 LOC (v0.6.1)
- Phase 2-3: 57 modules, 12,486 LOC (v2.0.0)

**Outcome (Current):**
- ✅ Greenfield support
- ✅ Small project support (10-50K LOC)
- ✅ **Enterprise support (100K+ LOC, production-ready)**

---

### 🟡 v0.7.0: Critical Integration Gaps (In Progress — May 20 Target)

**Features (Phase 1 — 3/7 Complete):**
1. ✅ Multi-file output formatting (90 LOC) — Dependency-ordered generation
2. ✅ Auto-wiring into projects (250 LOC) — Django/FastAPI/Spring/Go integration
3. 🟡 Migration generation (300 LOC) — Auto-generate schema changes (integration testing)
4. 📋 Framework config generation (200 LOC) — Smart defaults per framework
5. 📋 Dependency injector (250 LOC) — DI pattern generation
6. 📋 Environment variables (100 LOC) — .env template creation
7. 📋 Docker Compose (150 LOC) — Local dev environment

**Target:** May 20, 2026 (v0.7.0 release → Marketplace launch)

---

### 📋 v3.0.0: Production Hardening (Phase 4 — Q3 2026, Jul-Sep)

**Features (60 modules):**
- DDD aggregate generation, bounded contexts
- CQRS command/event handlers
- Event sourcing with snapshots
- Distributed transaction orchestration
- TDD cycle integration (property testing, mutation testing)
- Cost optimization (Lambda, database, caching, CDN)
- Chaos engineering (service degradation, circuit breakers)
- Enterprise compliance (SOC 2, HIPAA, GDPR, PII protection)

**Effort:** 18,000 LOC

---

### 📋 v4.0.0: Advanced Patterns (Phase 5 — Q4 2026, Oct-Dec)

**Features (50 modules):**
- Microservices orchestration (Kubernetes, Helm, service mesh)
- Real-time features (WebSocket, SSE, Redis pub/sub, presence tracking)
- GraphQL API generation (schema, resolvers, subscriptions, federation)
- ML pipeline integration (feature engineering, model serving, monitoring)
- Legacy code modernization (strangler pattern, incremental migration)

**Effort:** 15,000 LOC

---

### 📊 v5.0.0: Complete Platform (Dec 2026)

**Result:** 177 modules, 47,361 LOC, 15-20% market penetration
**Success Metric:** 80%+ correct bus detection on sample projects

**Why v0.6.0-Foundation First:**
- v0.6.0 provides codebase analysis framework
- v0.7.0 uses that framework to detect bus patterns
- Without v0.6.0, v0.7.0 is just a nice-to-have; with v0.6.0, it's essential integration

---

### v0.8.0: Integration Testing + Catalog Awareness (Target: Q4 2026-Q1 2027)

**Scope:** Test scaffolding + event governance

**Features:**
- Generate integration test scaffold (not just unit tests) ← v0.6.0-Foundation makes this possible (knows existing test patterns)
- Codebase exploration: detect bus initialization location, existing subscribers
- In assumptions: "Found bus init in app/events.py; added subscriber to that module"
- Generate wiring instructions: "Import rate_limiter in app/main.py; call await rate_limiter.start()"
- Accept catalog URL/file path in prompt or auto-detect from codebase
- Enforce catalog constraints by default; surface constraint violations in assumptions

**Effort:** ~110 hours (~40 integration testing + ~50 catalog + ~20 coordination)
**Risk:** Catalog formats vary; hard to auto-detect reliably
**Success Metric:** 
- Integration test scaffold runs against real bus (mocked or testcontainers)
- Catalog constraint violations surface before generation

---

### v0.9.0: Domain-Specific Observability (Target: Q1-Q2 2027)

**Scope:** Specialized metrics for domain

**Features:**
- Accept domain hint in prompt: "for game server", "for trading bot", "for ML pipeline"
- Domain-specific metrics:
  - Games: frame timing, event queue depth, latency percentiles
  - Bots: message roundtrip time, retry rates, cost per operation
  - ML: feature freshness, inference latency, data quality
- Observability block grows with domain; generated code includes domain metrics

**Effort:** ~40 hours
**Risk:** Domain knowledge might be incomplete; need user feedback
**Success Metric:** Generated observability correctly addresses 80%+ of use case needs

---

### v0.9.5: Dual-Mode Workflows (Target: Q1-Q2 2027)

**Scope:** Optional plan-first mode + user preference detection

**Strategic Purpose:**
Capture "safer enterprise" segment without abandoning flow-first identity. Users who want speed stay in auto-generation mode; teams requiring review can opt into plan-first. **Single codebase, dual workflows.**

**The Insight:**
- Current users: "I know what I want, generate immediately" → flow-first ✅
- Enterprise procurement: "Show me what you'll build before committing" → plan-first ✅
- Both valid. Don't force one approach on everyone.

**Features:**

#### **1. Auto-Detect Workflow Based on Context**

Skill detects intent and offers appropriate mode:

```
User provides: @existing-codebase
  → Flow-First (default)
  Assumptions + Code immediately
  Reason: User knows their project; doesn't need planning reassurance
  
User provides: no codebase OR vague requirements ("generate a handler")
  → Offer Plan-First
  "Want me to outline structure first? [Yes/No]"
  Reason: Unclear intent benefits from preview before full generation
```

**Implementation:**
- Add context detection to SKILL.md: Is this greenfield? Is this existing codebase? Is requirement clear?
- If greenfield + vague: suggest `--preview` flag
- If existing codebase: default to immediate generation (they trust their context)

#### **2. Optional `--preview` Flag**

User can force preview mode anytime:

```bash
/one-shot-prompting:generate Add rate limiter for message.received --preview
```

**Output in Preview Mode:**

```
## 🔍 PREVIEW: What Will Be Generated

### File Structure
- rate_limiter.py (180 LOC)
- test_rate_limiter.py (220 LOC)
- README.md (140 LOC)
- Dockerfile (25 LOC)
- .github/workflows/test.yml (60 LOC)

### Key Decisions
- Algorithm: Sliding window log
- Storage: In-memory dict (not Redis)
- Failure mode: Drop excess, emit rate.exceeded
- Testing: pytest + asyncio mocks

### Estimated Integration Time
- Reading code: 5 min
- Wiring into codebase: 10 min
- Running tests: 2 min
- Total: ~17 min

### Ready to Generate? [Yes] [No, Change X]
```

**Then user chooses:**
- `[Yes]` → Full generation (code + tests + README + deployment)
- `[No, Change X]` → Rerun with override (same as flow-first iteration)

**This is NOT spec-first.** It's *preview-before-commit*, not *plan-before-code*. Huge difference:
- Spec-first: Plan → approval → code (2-3 turns, slow)
- Preview-first: Preview → generate (1 turn, same speed)

#### **3. Backward Compatibility**

- **Default behavior unchanged:** Flow-first mode works exactly as today
- **No approval gates:** Users can still regenerate immediately if preview shows wrong approach
- **No extra turns:** Preview is fast text (structured outline), not full reasoning

#### **4. When to Use Each Mode**

| Situation | Mode | Why |
|-----------|------|-----|
| "Add OAuth to my Django app" (exists, clear) | Flow-First | You know your codebase; context injection handles adaptation |
| "Generate a handler" (greenfield, unclear) | Preview-First | You haven't committed yet; seeing structure reduces regrets |
| "Update messaging to support exactly-once" (exists, specific) | Flow-First | Clear intent; generate immediately, iterate if wrong |
| "Build event bus from scratch" (big decision) | Preview-First | Architecture choice; worth seeing outline first |

**Enterprise adoption path:**
```
Week 1: Enterprise customer tries preview-first on test task
         "Oh, THIS is what you mean by 'assumptions visible'"
         → Builds trust, reduces procurement anxiety

Week 2: Customer uses flow-first on real task
         "Okay, immediate generation is actually faster once I trust it"
         → Realizes flow-first isn't reckless, it's *efficient*

Week 3: Customer adopts both modes situationally
         → Highest velocity
```

**Effort:** ~30 hours (~15 preview text generation logic + ~10 context detection + ~5 testing)

**Success Metric:**
- Enterprise customers who were hesitant now use v0.9.5
- Flow-first users unaffected (default mode unchanged)
- Preview mode reduces "I wish I'd seen the structure first" regrets by 80%
- NPS +10 points from enterprises
- No churn from core users

**Why This Slot (v0.9.5, not v1.0.0):**
- Builds directly on v0.9.0 (domain observability already done)
- Doesn't require v1.0.0's "polish phase"
- Serves as "soft launch" for enterprise segment before v1.0.0
- v1.0.0 becomes: "Enterprise-ready with optional planning mode"

---

### v1.0.0: Enterprise Launch (Target: Q2-Q3 2027)

**Scope:** Polish + Market Launch

**Features:**
- All gaps closed (codebase support, bus detection, integration testing, catalog, observability)
- Dual-mode workflows integrated (flow-first default, plan-first optional)
- Formal security audit (no secrets in generated code, safe by default)
- Performance profiling for all 5 languages + all 5 brokers
- Documentation: "Patterns for X" (game servers, trading bots, real-time systems)
- Marketing: blog posts, video demos, GitHub sponsor integration
- Testimonials from enterprise users ("This cut our dev time 60%")
- Marketing narrative: "Flow-first for those who know what they want. Preview-first for those who want to see first. Your choice."

**Effort:** ~120 hours (testing, marketing, positioning, polish)

**Milestone:** Ready for "Best Plugin" nominations, press outreach to developer communities

**Position After v1.0.0:**
> "One-Shot Prompting is the event-driven code generator for enterprises building event systems at scale. Supports codebases from greenfield to 100K+ LOC. 5 languages, 5 message queues, dual workflows (flow-first or preview-first). Flow-first for teams that iterate fast. Preview-first for teams that want safety."

---

### v0.7.0-v0.8.0: Feature Discovery & Developer Enablement (Parallel Track)

**Context:** Analysis of claude-howto (25K stars) revealed critical gap: 80% of users exploit only 20-30% of plugin capabilities. Discovery happens via trial-and-error or reading entire documentation. For one-shot-prompting, many developers don't realize the plugin can generate Kafka consumers, Kubernetes manifests, GitHub Actions workflows, or deployment contexts — they assume it only generates simple event handlers.

**Problem to Solve:**
- **Discoverability:** Users don't know what the plugin can do beyond basic "generate a module" use case
- **Onboarding friction:** New users face blank-slate problem: "What can I ask for?"
- **Feature underutilization:** Advanced features (deployment, observability, migration generation) exist but go unused
- **Template reuse:** Users reinvent prompt phrasing instead of copy-pasting proven templates

**Solution (4-Part Initiative):**

#### 1. **Self-Assessment CLI Tool** (`/one-shot-prompting health-check`)
Run diagnostic to discover plugin capabilities your codebase can use:
```bash
/one-shot-prompting health-check @/path/to/project
```

Output (compact human-readable report):
```
✅ Framework: Django 4.2 → plugin can generate models, views, serializers, tests
✅ Message Bus Detected: Celery + Redis → plugin can generate Celery tasks, signals
✅ Testing: pytest + factories → plugin will use existing fixtures
✅ IaC Detected: Docker, GitHub Actions → plugin can generate Dockerfile, workflows
⚠️  Logging: default Python logging → plugin uses stdlib (recommend structlog for structured logs)
❌ No migration tool detected → plugin will note "manual schema changes needed"

Capability Summary:
- Can generate: features, tests, deployment configs, CI/CD workflows
- Optimization tip: Mention @/path/to/project in prompts for better codebase-aware output
- Advanced features available: dead-letter-queue routing, exactly-once delivery, observability patterns
```

**Implementation:** ~20 hours
- Extend `analyze_codebase.py` to produce capability matrix
- Add health-check command to SKILL.md that calls analyzer and formats output
- Include recommendations (e.g., "Your project uses Django signals; ask for DLQ-aware signal handlers")

#### 2. **Template Library: 20+ Copy-Paste Prompts** (GitHub wiki or README section)
Collection of real, working prompts organized by scenario:

**Messaging (Kafka, RabbitMQ, SQS, Pub/Sub)**
```
/one-shot-prompting:one-shot-generator Add Kafka consumer for user.signup events, validate email, emit user.validated @/path/to/project

/one-shot-prompting:one-shot-generator Add exactly-once delivery SQS consumer for payment.received, charge customer, emit charge.completed @/path/to/project

/one-shot-prompting:one-shot-generator Add dead-letter-queue routing for order.placed events that fail 3 times @/path/to/project
```

**REST/GraphQL APIs**
```
/one-shot-prompting:one-shot-generator Add REST endpoint POST /users that creates a user, validates email, sends welcome email, returns user with auth token @/path/to/project

/one-shot-prompting:one-shot-generator Add GraphQL subscription for order status updates (order.created, order.shipped, order.delivered) @/path/to/project
```

**Deployment & CI/CD**
```
/one-shot-prompting:one-shot-generator Add Kafka consumer for events, include Dockerfile, Kubernetes manifest, and GitHub Actions workflow @/path/to/project

/one-shot-prompting:one-shot-generator Generate integration test scaffold that spins up RabbitMQ, emits test events, validates response @/path/to/project
```

**Observability & Monitoring**
```
/one-shot-prompting:one-shot-generator Add Kafka consumer for order.created, include OpenTelemetry tracing, Prometheus metrics, and structured logging @/path/to/project

/one-shot-prompting:one-shot-generator Add observability patterns for game server event handler (frame timing, event queue depth, latency percentiles) @/path/to/project
```

**Refactoring & Migration**
```
/one-shot-prompting:one-shot-generator Refactor user.created handler to use exactly-once delivery instead of at-least-once @/path/to/project

/one-shot-prompting:one-shot-generator Add backward-compatible user.created v2 event handler while deprecating v1 @/path/to/project
```

**Implementation:** ~30 hours
- Curate 20-25 real prompts from user feedback + internal testing
- Test each prompt on actual codebases (Django, FastAPI, Go, NestJS)
- Document where to find templates: GitHub wiki, README "Quick Start" section
- Add `/one-shot-prompting list-templates` command to discover available templates interactively

#### 3. **Examples Repository: 5-10 Real, Complete Projects**
Working example projects showing off plugin capabilities end-to-end:

- **django-order-service** (15 files): Django microservice. User runs `/one-shot-prompting:one-shot-generator` to generate order handlers, tests, deployment configs. Includes: Kafka consumer (order.created), email notifications, database migrations, GitHub Actions CI/CD, Kubernetes manifests.
- **rust-game-server** (12 files): Tokio-based multiplayer game. Shows off Rust async patterns, DLQ handling, observability metrics specific to games.
- **go-trading-bot** (10 files): Go event consumer for trade.executed events. Demonstrates low-latency patterns, Go idiomatic conventions, multiple message queues.
- **nestjs-real-time-api** (14 files): NestJS with WebSockets + Kafka. Shows TypeScript patterns, decorator-based dependency injection, integration testing.
- **python-ml-pipeline** (16 files): Python async pipeline for feature computation. Shows domain-specific observability (feature freshness, inference latency).

**Each repo includes:**
- Actual working code (not stubs)
- How the code was generated (shell commands that produced it)
- What user changed afterward (0-5% refactoring typically)
- How to extend it (rerun examples)

**Implementation:** ~50 hours
- Write 5 complete, production-grade examples
- Test each example on target stack (ensure code actually runs)
- Document generation journey for each
- Publish on GitHub with CI/CD to keep examples fresh

#### 4. **Feature Discovery Tour: Interactive Onboarding** (v0.8.0+)
In-SKILL guided tour for new users:

```
/one-shot-prompting:one-shot-generator --tour

Output:
Welcome to One-Shot Prompting! Let's find what you can build.

[1] What's your primary use case?
  a) REST API endpoints
  b) Message queue consumers (Kafka, RabbitMQ, etc.)
  c) Game server event handlers
  d) Trading bot / financial systems
  e) I'm not sure

[User selects: b]

Great! Message queue consumers are our core strength. Here's what you can do:

✅ Generate complete Kafka/RabbitMQ/SQS subscribers
✅ Add error handling, dead-letter queues, retries
✅ Include integration tests
✅ Deploy with Docker, Kubernetes, GitHub Actions
✅ Add observability (structured logging, metrics, tracing)

[2] What languages do you code in?
  a) Python
  b) Go
  c) Rust
  d) TypeScript/JavaScript
  e) Java
  f) Multiple (show examples for each)

[User selects: a]

Perfect! You can generate production-grade Python consumers with:
- Async patterns (asyncio, aioredis, aiokafka)
- Framework integration (Django signals, FastAPI background tasks, Celery)
- Testing (pytest + fixtures)
- Deployment (Docker, GitHub Actions, Kubernetes)

Try this template:
  /one-shot-prompting:one-shot-generator Add Kafka consumer for user.signup, validate email, emit user.validated @/path/to/project

More templates: /one-shot-prompting list-templates
Examples repo: https://github.com/one-shot-prompting/examples
Health check: /one-shot-prompting health-check @/path/to/project

Ready? Generate your first consumer, or explore more with --tour continue
```

**Implementation:** ~25 hours
- Add tour state machine to SKILL.md
- Create decision tree based on use case + language
- Link to templates and examples
- Track tour completions for analytics (users who complete tour have higher retention)

### v0.9.0+: Multi-Sidecar Orchestration (Future Capability)

**Problem:** Enterprise users often need multiple sidecars working together:
- Order service: consumes `order.created`, emits `order.validated`, `inventory.reserved`, `payment.charged`
- Each step may need error handling, retries, observability
- Generated code today is single-sidecar; orchestrating multi-sidecar workflows requires manual wiring

**Future Capability (not v0.8.0, post-v0.9.0):**
```
/one-shot-prompting:one-shot-generator Generate orchestrated order processing pipeline:
  [1] Kafka consumer for order.created → validate order → emit order.validated
  [2] Kafka consumer for order.validated → reserve inventory → emit inventory.reserved OR inventory.unavailable
  [3] Kafka consumer for inventory.reserved → charge payment → emit payment.charged OR payment.failed
  [4] Kafka consumer for payment.failed → refund inventory → re-emit order.created
  With: exactly-once delivery, DLQ routing, distributed tracing, metrics dashboard @/path/to/project
```

Claude generates:
- 4 separate modules (each sidecar)
- Orchestration layer (event routing, pipeline coordination)
- Integration test (spins up all sidecars, emits test order, verifies end-to-end flow)
- Observability dashboard config (track orders through all stages)

This is a **future** capability post-v0.9.0 because it requires:
1. ✅ Codebase support (v0.6.0) — understand existing patterns
2. ✅ Bus auto-detection (v0.7.0) — know which bus to use
3. ✅ Integration testing (v0.8.0) — test multi-sidecar flows
4. ✅ Catalog awareness (v0.8.0) — coordinate event types across sidecars
5. ✅ Observability (v0.9.0) — track end-to-end flows

**Effort:** ~80 hours (v0.10.0 timeframe, Q3-Q4 2027)

---

## Part 4.5: Philosophical Clarity — Flow-First vs. Plan-First

### Why Dual-Mode Is NOT "Becoming Superpowers"

**Superpowers:** Plan → Review → Code (3 turns, forced)
**Our Flow-First:** Code → Iterate (1 turn, optional preview)
**Our Dual-Mode:** Code OR Preview → Iterate (user chooses)

**Key Difference:**
- Superpowers makes you go through a plan phase. Required.
- We offer preview as an **option for those who want it**. Default still generates code.
- Superpowers: "Here's the plan. Do you approve?" → Users wait, review, discuss
- Us: "Here's what I'll build (1-second preview). Proceed or adjust?" → Users decide fast, proceed

**Why This Preserves Flow-First:**
- Preview is text, not conversation. Generated in milliseconds from the code generation logic.
- No approval gate. Users can skip preview and go straight to generation.
- No extra turns. User sees preview and says "yes" → code follows immediately.
- Same regeneration loop. If preview was wrong, rerun with override ("use token bucket instead").

**Enterprise Segment Win:**
- Procurement teams want "show before commit" — preview satisfies that
- Developer teams still want speed — flow-first satisfies that
- Both groups now happy. No compromise.

**The Strategic Insight:**
We're not compromising flow-first; we're **making it feel safer to uncertain buyers.**
- "We generate immediately" ← scary to enterprise procurement
- "We show you a preview first" ← less scary, same speed
- Different messaging, same product. Maximum market capture.

---

## Part 4.75: Competitive Analysis & Gap Closure (v0.10.0 - v1.2.0)

**Reference:** See `.claude-plugin/COMPETITIVE_ANALYSIS.md` for full audit vs. Superpowers and Anthropic best practices.

### Strategic Insight: You're Not "Super," And That's Right

**Superpowers:** "How should I code better?" (methodology + discipline)
**One-Shot (You):** "How do I generate code that fits MY codebase?" (context + framework awareness)

These are **complementary, not competitive.** You solve different problems. But there are **critical gaps** that will block enterprise adoption if not addressed.

---

### v0.10.0: Code Review Automation (Target: Q3 2027)

**Scope:** Automatic code quality gates on generated code

**Strategic Purpose:**
Superpowers has built-in code review skill. You generate code without quality gates. This gap blocks enterprise adoption ("We can't merge code without review"). Close it.

**Features:**

1. **Linting Compliance Check**
   - Auto-detect linting rules from codebase (eslint, flake8, clippy, etc.)
   - Review generated code against those rules
   - Surface violations in assumptions: "Generated 2 linting violations: [list]"
   - Allow override: `--force` if user wants to skip review

2. **Security Pattern Enforcement**
   - ❌ No hardcoded secrets (API keys, passwords)
   - ❌ No SQL injection vectors
   - ❌ No command injection risks
   - ❌ No XSS patterns (even in backend code, check for logging)
   - Block generation if critical security issue found
   - Suggestion: "Found potential SQL injection at line X; use parameterized query instead"

3. **Performance Pattern Check**
   - ❌ No blocking calls in async code (`time.sleep()` in `async def`)
   - ❌ No synchronous database queries in async handlers
   - ❌ No N+1 query patterns detected
   - Warning (not block): "Found potential N+1 at line X; consider batch fetch"

4. **Type Coverage Enforcement**
   - 100% type hints required (no `Any`, no `interface{}` in Go, no untyped in TypeScript)
   - Check all function signatures, variable declarations
   - Block if coverage < 95%

5. **Test Coverage Enforcement**
   - Minimum 2 tests per generated module
   - At least one integration test (not just unit)
   - Block generation if tests insufficient
   - Assumption block: "Generated 4 tests (1 integration, 3 unit)"

6. **Review Report in Assumptions Block**
   ```
   ## Code Review Results
   
   ✅ Linting: Compliant with project standards (flake8 + black)
   ✅ Security: No hardcoded secrets, no injection vectors
   ✅ Performance: No blocking calls in async code
   ✅ Type Coverage: 100% (Python 3.9+ strict mode)
   ✅ Test Coverage: 4 tests (1 integration, 3 unit)
   
   → Ready to merge
   ```

**Implementation:**
- Build on v0.6.0 codebase analysis (already detects linting tools)
- Add review logic to SKILL.md post-generation section
- Integrate security checks (leverage existing patterns from v0.4.0 security hardening)
- Non-blocking: review is informational; user can override with `--force`

**Effort:** ~30 hours (~10 linting, ~10 security, ~5 performance, ~5 integration)

**Success Metric:**
- Enterprise teams can enforce code review policies automatically
- Generated code passes security/linting gates 95%+ of the time
- Users trust generated code enough to merge without manual review

**Why After v1.0.0:**
- v1.0.0 is market launch; v0.10.0 is quality polish
- Complements v1.0.0 security audit (audit is human; review is automated)
- Builds on v0.6.0-Foundation (codebase analysis is prerequisite)

---

### v1.1.0: Test-First Mode (Target: Q3-Q4 2027)

**Scope:** Optional TDD workflow (tests before implementation)

**Strategic Purpose:**
Superpowers forces TDD (red-green-refactor). You generate code with tests alongside. Option: let users choose test-first. Differentiator.

**Features:**

1. **Optional --tdd Flag**
   ```bash
   /one-shot-prompting:generate Add rate limiter --tdd
   ```

2. **Workflow When --tdd Specified:**
   - Generate test file FIRST (all tests initially fail)
   - Clearly mark failures in output: "❌ 5 tests generated, all should fail initially"
   - Then generate implementation (tests should pass)
   - Output structure:
     ```
     ## Test File (Should Fail Before Implementation)
     [full test file with failing assertions]
     
     ## Implementation (Makes Tests Pass)
     [full implementation file]
     
     ## Verification
     Run: pytest test_rate_limiter.py
     Expected: ✅ All 5 tests pass
     ```

3. **Assumptions Block Includes TDD Status**
   ```
   ## Test-First Workflow
   Generated 5 tests. All should fail before running implementation code.
   After copying implementation, run pytest — all should pass.
   ```

4. **Backward Compatibility**
   - Default (no --tdd flag): tests + code in same response (current behavior)
   - With --tdd: tests first, implementation after
   - No breaking changes; purely additive

**Implementation:**
- Add `--tdd` parameter detection to SKILL.md
- Conditional generation: if --tdd, organize output differently
- Include verification instructions (how to run tests, confirm fail/pass)
- Build on v0.8.0 integration testing (reuse test scaffolding)

**Effort:** ~25 hours (~12 workflow logic, ~8 test orchestration, ~5 documentation)

**Success Metric:**
- Users choosing --tdd see tests fail first, understand intent before implementation
- Test-first discipline becomes optional (not forced)
- Differentiator vs. Superpowers: "We make TDD optional; they force it"

**Why After v0.10.0:**
- v0.10.0 enforces quality gates (tests must be good)
- v1.1.0 emphasizes test-first discipline (tests drive design)
- Sequential builds: quality first, then discipline

---

### v1.2.0: Systematic Debugging Helpers (Target: Q4 2027)

**Scope:** Help users debug failures methodically (close Superpowers' 4-phase debugging gap)

**Strategic Purpose:**
Superpowers has systematic debugging methodology (reproduce → isolate → hypothesize → verify). You have generic error handling. Close the gap.

**Features:**

1. **Error Pattern Recognition**
   - Detect common failure signatures in generated code:
     - Timeout errors (slow handler)
     - Queue depth errors (backpressure)
     - Dependency injection errors (missing wiring)
     - Type mismatches (schema evolution)
     - Concurrency issues (race conditions)
   - When user reports error: match against patterns
   - Suggest likely cause + fix

2. **Auto-Generate Repro Script**
   ```python
   # Generated by One-Shot when user says "my rate limiter isn't working"
   
   @pytest.mark.asyncio
   async def test_rate_limiter_repro():
       """Minimal repro: demonstrates the failure"""
       bus = MockAsyncBus()
       limiter = RateLimiter(bus=bus)
       
       # Repro steps based on error signature:
       # If error is "events not being dropped":
       for i in range(15):
           await bus.emit('message.received', {'user': 'alice'})
       
       # Expected: 10 accepted, 5 dropped
       # Actual: [user reports behavior]
   ```

3. **Hypothesis Testing**
   - Generate test assertions that isolate the root cause
   - "If hypothesis is true, test X should fail"
   - Guide user through debugging: "Run this test. If it fails, the problem is Y. If passes, problem is Z."

4. **Fix Suggestions (Ranked by Likelihood)**
   ```
   Based on error pattern, likely fixes:
   1. (70% likely) Check queue initialization — is bus connected?
      Fix: Verify bus.is_connected() before emitting
   
   2. (20% likely) Check timeout — handler taking too long
      Fix: Add asyncio.wait_for(handler(), timeout=5)
   
   3. (10% likely) Type mismatch in event schema
      Fix: Verify event payload matches expected schema
   ```

5. **Error Learning Loop**
   - Track error signatures across projects
   - "You've seen 3 timeout errors this month. Pattern: handlers over 1s. Consider caching."
   - Surface trends in Observability metrics

**Implementation:**
- Build error pattern catalog (30-50 common event-driven failure modes)
- Generate repro scripts on demand (using v0.8.0 test scaffolding)
- Rank fixes by likelihood (use v0.6.0 codebase context)
- Non-invasive: only activates when user reports error

**Effort:** ~40 hours (~15 pattern catalog, ~15 repro generation, ~10 ranking engine)

**Success Metric:**
- Users reporting errors get helpful guidance 80%+ of the time
- Debugging time drops 50% (vs. manual investigation)
- Users can solve problems without asking Claude again

**Why After v1.1.0:**
- v1.1.0 emphasizes test-first (tests help debugging)
- v1.2.0 helps when tests fail
- Sequential: write good tests, then debug them systematically

---

## Part 5: Competitive Moat

### Why Event-Driven?
1. **Specialized:** Competing on general feature generation is crowded. Event-driven is a niche with real demand.
2. **Deep expertise:** Each language's async patterns are different. We own them all.
3. **No conversion cost:** Event systems are already async; we don't add friction.
4. **Market growth:** Event-driven architecture is mainstream now (not bleeding-edge), so TAM is large.

### How to Maintain Moat
- **Keep flow-first:** Never add spec phase (that's Superpowers' job)
- **Stay focused:** Refuse non-event-driven requests (don't dilute)
- **Lead on buses:** Be the plugin that knows Kafka, RabbitMQ, Tokio, asyncio, etc. deeper than anyone
- **Iterate publicly:** Show regressions publicly; iterate fast when wrong
- **Own the domain:** Contribute patterns back to event-driven frameworks (Bevy, tokio, NestJS, etc.)

### What NOT to Do
- ❌ Don't become "general code generator" (that's Superpowers)
- ❌ Don't add approval gates that slow iteration (preview is optional, not gated)
- ❌ Don't support non-event-driven (dilutes brand)
- ❌ Don't slow down iteration (default flow-first; preview is bonus, not requirement)
- ❌ Don't ignore user feedback on bus-specific quirks

### Dual-Mode Advantage (v0.9.5+)

After v0.9.5, our positioning shifts:

**Superpowers:** "Safer approach with planning phase"
- Pros: High-stakes features, team alignment
- Cons: 2-3 turns to code, slower iteration

**One-Shot Flow-First (always available):** "Fastest iteration for those who know what they want"
- Pros: 1 turn to code, regenerate to adjust
- Cons: Requires confidence in your requirements

**One-Shot Dual-Mode (new in v0.9.5):** "Fast iteration with optional safety net"
- Pros: Flow-first by default, preview-first for those who want it
- Cons: None. Users choose.
- **Win:** Captures "enterprise wants preview" segment without sacrificing speed

**Market Positioning After v0.9.5:**
> "Choose your speed. Flow-first developers go straight to code. Enterprises that need preview can see the structure before generation. Same one-shot philosophy, dual workflows. Superpowers is slower and safer. We're faster and still safe."

This is **not** copying Superpowers. This is acknowledging that different segments want different reassurances, and giving them choice without forcing slowdown on anyone.

---

## Part 6: Success Metrics (Non-Committed, For Tracking)

### Plugin Health
- **Monthly active users:** 100 → 500 → 2K (v0.6→v0.7→v0.8)
- **GitHub stars:** 100 → 500 → 2K (v0.5→v0.6→v0.7)
- **User satisfaction:** "Saved me 2 hours on event setup" (NPS > 50)
- **Market fit:** "Regenerating 3-5 times per feature is normal, fast iteration beats spec-first"

### Code Quality
- **Linting compliance:** 100% across all languages
- **Type coverage:** 100% in all languages (no `any`, no `interface{}` escapes)
- **Test coverage:** Every generated module has 2+ tests
- **Security:** Zero hardcoded secrets, zero unsafe patterns

### Business Metrics (If Monetized)
- **Marketplace conversion:** 5% of viewers → installers
- **Retention:** 60%+ of installers use weekly
- **Paid tier uptake:** 10%+ of active users subscribe (at v0.9.0+)
- **Revenue:** Sustainable small team (not venture scale, but profitable)

---

## Part 7: Risks & Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|-----------|
| Codebase scanning is noisy; false bus detection | Frustration, poor UX | Medium | Phase 1: manual hints only, add auto-detection gradually, user feedback loop |
| Catalog formats too diverse to support all | Adoption ceiling | Medium | Focus on SKILLS.md + OpenAPI; user-provided adapters for others |
| Event-driven market is smaller than general code gen | TAM ceiling | Low | Data: event-driven trending up (microservices, serverless, gaming, IoT) |
| Superpowers adds event-driven support | Competition | Medium | We move faster on iteration + multi-language; maintain focus on flow-first |
| Users want to regenerate whole codebases | Out of scope | High | Remind: "One-shot = one feature"; refuse scope creep politely |

---

## Part 8: Implementation Philosophy (UPDATED with Large Codebase Priority)

### Strategic Direction Change: Large Codebase First

**Old Plan:** v0.6.0 bus auto-detection → v0.7.0 integration testing → v0.8.0 catalog

**New Plan:** v0.6.0-Foundation (all 10 large codebase pieces) → v0.7.0 bus auto-detection → v0.8.0 integration + catalog

**Why This Matters:**
- Current plugin is **harmful for enterprises** (40-60% refactoring post-generation)
- Fixing large codebase gaps is **force multiplier** for all future work
- v0.6.0-Foundation enables v0.7.0+ to work in enterprise context
- Without foundation, v0.7.0+ features add value to greenfield only

### What Changes in v0.6.0-Foundation
- ✅ Add codebase awareness (analyzer, context extraction)
- ✅ Add framework integration (adapters for Django/FastAPI/Spring/Rails/Go)
- ✅ Add dependency management (version checking, compatibility)
- ✅ Add convention learning (error handling, logging, naming styles)
- ✅ Add test pattern inheritance (use existing fixtures/factories)
- ✅ Add migration generation (backward-compatible schemas)
- ✅ Add API consistency (match existing endpoint styles)
- ✅ Add documentation integration (plug into existing doc systems)
- ✅ Add deployment awareness (integrate with existing IaC/CI-CD)

### What Stays (Unchanged)
- **Flow-first ideology:** One turn, assumptions visible, iterate by regeneration
- **Multi-language parity:** Python, Go, Rust, TypeScript, Java (now with framework adapters)
- **Explicit assumptions:** Every decision visible, always actionable (now includes codebase context)
- **Event-driven focus:** Refuse non-event work narrowly; own the bus ecosystem

### How to Avoid Scope Creep in v0.6.0-Foundation
1. **All new features must enable enterprise adoption:** If it doesn't help large codebase integration, defer to v0.7.0+
2. **All new features must reduce post-generation friction:** If users still need 20% refactoring, it's not done
3. **All new features must support all 5 languages:** Framework adapters for all major languages (Django, FastAPI, Spring, Rails, Go)
4. **All new features must be automatic:** No additional user input beyond `@path/to/codebase` (codebase analyzer handles the rest)

### Success Criteria for v0.6.0-Foundation
- 🎯 Enterprise user takes 100K LOC Django project as input
- 🎯 Plugin generates Payment module + migrations + tests + docs + deployment
- 🎯 Code needs <5% refactoring (vs current 40-60%)
- 🎯 Code integrates seamlessly with existing API, logging, error handling, database
- 🎯 User says: "This feels like it was written by our team"

---

## Final Notes for Future Reference

### Strategic Shift: Enterprise-First Approach

**Previous Mindset:** Build market features (bus auto-detection, catalog) → eventually support enterprise

**New Mindset:** Build enterprise foundation first (large codebase support) → market features become valuable on solid base

**Why This Flip:**
- Greenfield users are already well-served (v0.5.0 is excellent)
- Enterprise users are blocked (40-60% refactoring is unacceptable)
- Enterprise market is larger TAM + higher unit economics
- Enterprise features (framework adapters, convention matching) also benefit greenfield once built

**Competitive Position After v0.6.0-Foundation:**
- **Before:** "Good for small event-driven projects"
- **After:** "Production-ready for event systems at any scale"

---

### On Superpowers & Spec-First Tools
- Superpowers is **better** for: unclear requirements, high-stakes features, teams needing consensus, general code gen
- We are **better** for: clear intent, fast iteration, event-driven expertise, multi-language speed, **enterprise integration**
- **Not a rivalry:** Different tools for different workflows; we can coexist (and now serve different customer segments)

### On Market Maturity
- Event-driven architecture is **mainstream now** (not fringe)
- Kafka, RabbitMQ, async/await are standard tools
- Market is growing: game engines (Bevy), serverless (AWS Lambda), IoT (MQTT)
- **Enterprise demand:** "Make code generation work with our 100K LOC codebase" is the #1 blocker
- Timing is right to own event-driven + enterprise hybrid market

### On Long-Term Vision
- **v0.5.0:** Solid baseline (message queues in place)
- **v0.6.0-Foundation:** Break into enterprise (large codebase support) ⭐ CRITICAL ✅ DONE
- **v0.7.0-v0.8.0:** Deepen market features (bus detection, catalog, integration testing)
- **v0.9.0-v0.9.5:** Market expansion (observability, dual-mode workflows)
- **v1.0.0:** Enterprise launch (all foundations + security audit)
- **v0.10.0-v1.2.0:** Quality enforcement (code review, TDD, debugging) — Close Superpowers gaps
- **v1.3.0+:** Market dominance in event-driven + enterprise space
- **v1.5.0+:** Maintain focus on event-driven; don't become general code gen

### Decision Log

**April 21, 2026:** Realized v0.5.0 is insufficient for enterprise use. Audited 10 missing pieces. Decision: Prioritize v0.6.0-Foundation over v0.7.0 bus detection. Reason: Foundation enables all future work; bus detection alone doesn't solve enterprise friction.

**April 25, 2026:** Market insight from competitive analysis: Superpowers owns "slower but safer." We can own "fast AND safe (optional)" by offering dual workflows. Decision: Add v0.9.5 Dual-Mode Workflows before v1.0.0 launch. Rationale: Captures enterprise segment without abandoning flow-first identity. Users choose their workflow; no forced planning phase.

---

## Part 9: Strategic Evolution — From Single-Mode to Dual-Mode

### The Shift

**Previous Positioning (v0.5.0):**
"One-shot means: write prompt, get code. No planning phase. Fast iteration only."

**Issue:**
- Appeals to: Developers with clear intent + high confidence
- Repels: Enterprise buyers who want preview + risk mitigation
- Result: TAM is smaller than it could be

**New Positioning (v0.9.5+):**
"One-shot means: write prompt, preview optional, get code. You choose your safety level."

**Impact:**
- Appeals to: All developers + enterprise buyers
- Doesn't repel: Flow-first users see no change (default is unchanged)
- Result: TAM grows 2-3x without diluting core value

### Why This Is Principled, Not Compromise

**Principle:** Developers should choose their workflow, not have it forced.

**Flow-first devs:** "I know what I want, generate immediately" ✅ (happens by default, no change)
**Enterprise buyers:** "Show me first" ✅ (option available via `--preview`)

**NOT selling out:**
- Still own event-driven (no CRUD, no UI, no generic features)
- Still own multi-language parity (all 5 languages equally)
- Still own explicit assumptions (preview shows them)
- Still own regeneration iteration (preview doesn't gate generation)

**Selling smarter:**
- Same philosophy, wider appeal
- Same codebase, multiple entry points
- No performance cost (preview is lightweight)
- Maximum market capture without brand dilution

---

---

## Part 10: The Full Picture — From v0.6.0 to v1.2.0

### How These Versions Work Together

```
v0.6.0-Foundation: Codebase Awareness ✅ DONE
  ↓
v0.7.0-v0.8.0: Market Features (Bus Detection, Catalog, Integration Testing)
  ↓
v0.9.0: Domain-Specific Observability
  ↓
v0.9.5: Dual-Mode Workflows (Optional Preview-First)
  ↓
v1.0.0: Enterprise Launch ← MAIN MILESTONE
  ↓
v0.10.0: Code Review Automation ← Close Superpowers Gap #1
  ↓
v1.1.0: Test-First Mode ← Close Superpowers Gap #2 (Optional)
  ↓
v1.2.0: Debugging Helpers ← Close Superpowers Gap #3
  ↓
v1.3.0+: Market Dominance in Event-Driven + Enterprise Space
```

### Honest Competitive Position Evolution

**v0.6.0 (Now):**
> "Framework-aware code generator for existing codebases. Not Superpowers; we're different."

**v1.0.0 (Q2-Q3 2027):**
> "Enterprise-ready event-driven code generator. Fast (1-turn), smart (framework-aware), optional preview for safety. Supports 5 languages, 5 message queues, 100K+ LOC codebases."

**v1.2.0 (Q4 2027):**
> "The event-driven code generator that flows fast and codes safe. One-shot generation for speed. Optional test-first for discipline. Automatic code review for confidence. Superpowers teaches you to code better; we generate code that fits your codebase better."

### Why This Matters

You're not trying to be Superpowers. You're being the **expert in:**
- **Framework awareness** (Django, FastAPI, Spring, Rails, Go)
- **Enterprise integration** (large codebases, existing conventions)
- **Event-driven specialization** (message queues, async patterns)
- **Speed** (1 turn to production code)

Superpowers is the **expert in:**
- **Methodology** (5-phase discipline, TDD, debugging)
- **Team alignment** (planning phases, reviews)
- **General code generation** (CRUD apps, UI, etc.)

**By adding v0.10.0-v1.2.0, you're NOT becoming Superpowers. You're closing quality gaps while staying true to your core: fast, context-aware, event-driven.**

---

## Part 11: Post-v1.2.0 Remaining Gaps & Closure Strategy (v1.3.0+)

After completing v1.2.0, you'll still have 8 structural gaps that prevent 30-45% market adoption. This section details how to systematically close them.

### Gap A: Architectural Planning Integration — v1.3.0 (Q1-Q2 2028) [60 hours]

**Problem:** You generate modules for pre-designed systems. Users want to design systems INSIDE your plugin (not externally in Superpowers).

**Current State (v1.2.0):** Assume user has already done architecture; you generate implementation only.

**Proposed Solution: Architecture Assistant Skill**

```
/one-shot-prompting:architecture-design <describe system>
→ Returns:
  - Entity diagram (text-based or ASCII)
  - Event flow diagram
  - Service boundaries + responsibilities
  - Proposed file structure
  - Constraints + assumptions
  - "Ready to generate with /one-shot-prompting:generate"
```

**Implementation Details:**
- Create new skill: `skills/architecture-design/` (parallel to `one-shot-generator`)
- Use Claude to create lightweight architecture (5-10 min conversation)
- Output includes codebase structure + event catalog (feeds into generation)
- NOT a full 5-phase Superpowers-style planning (too heavy); more like "quick blueprint"
- Integrates analyzer: re-detect if user already has codebase structure

**Effort:** 60 hours
- Architecture skill design: 15h
- Diagram generation + formatting: 15h
- Analyzer integration: 10h
- Testing + docs: 20h

**Timeline:** Q1-Q2 2028 (after v1.2.0 stable)

**Success Metrics:**
- Users say "I used architecture-design, then one-shot-generator, and got a complete system"
- 70%+ of users find architecture helpful
- Reduces initial "what should I build?" questions

**Market Impact:** +10-15% (teams doing architecture + implementation together)

---

### Gap B: Team Code Review Workflow — v1.3.1 (Q2 2028) [50 hours]

**Problem:** Your code goes straight to user. Enterprise teams want "review before merge" integration with GitHub/GitLab PR workflows.

**Current State (v1.0.0):** Code review is manual; user runs auto-review (v0.10.0), but doesn't submit to PR for team review.

**Proposed Solution: GitHub/GitLab PR Integration Skill**

```
/one-shot-prompting:submit-to-pr --repo owner/repo --branch feature/auth
→ Returns:
  - Generated code submitted as draft PR
  - Auto-review comments attached
  - Links to migration files, tests, docs
  - Requires team approval before merge
  - Rerun integration: updates PR with new version
```

**Implementation Details:**
- New skill: `skills/submit-to-pr/` using GitHub/GitLab APIs
- Generate → review → create PR → team approval → merge workflow
- Pre-commit hooks integration (optional)
- Supports Azure DevOps, Bitbucket (future)
- Tracks PR status; offers "sync latest" if main changes

**Effort:** 50 hours
- GitHub API integration: 15h
- PR template generation: 10h
- Auto-review comment formatting: 10h
- Testing + docs: 15h

**Timeline:** Q2 2028 (3-4 months after v1.3.0)

**Success Metrics:**
- 50%+ of enterprise users use PR integration
- PR review cycle time <30 min (vs. current "manual review" which takes hours)
- Team velocity increases by 20-30%

**Market Impact:** +10-15% (enterprise teams with governance requirements)

---

### Gap C: TDD Learning Experience — v1.3.2 (Q2-Q3 2028) [40 hours]

**Problem:** v1.1.0 has `--tdd` flag (tests first), but doesn't explain WHY tests are structured this way. Users don't learn TDD methodology.

**Current State (v1.1.0):** `--tdd` generates tests, then implementation. No explanation or methodology coaching.

**Proposed Solution: TDD Walkthrough Mode**

```
/one-shot-prompting:generate --tdd --explain-tdd <feature>
→ Returns:
  - Test 1: explain why this test matters
  - Test 2: explain edge case covered
  - Test 3: explain failure mode prevented
  - Implementation: "These tests drive this design decision"
  - Refactoring: "Now we can safely refactor because tests protect us"
```

**Implementation Details:**
- Extend SKILL.md with TDD explanation section
- For each test, include: "Why this test? What does it catch? How would code break without it?"
- Show test-driven refactoring example (not just TDD writing)
- Add `--tdd-philosophy` flag for deep explanation (~500 extra tokens)
- Pair with v1.3.0 architecture assistant (design → tests → implementation)

**Effort:** 40 hours
- Test explanation generation: 15h
- Refactoring walkthrough: 10h
- SKILL.md expansion: 10h
- Testing + docs: 5h

**Timeline:** Q2-Q3 2028 (parallel to v1.3.1)

**Success Metrics:**
- Users report "I finally understand TDD"
- 60%+ of users switch to `--tdd` mode after trying `--tdd --explain-tdd`
- Support tickets on "why is this test here?" drop by 80%

**Market Impact:** +5% (teams learning TDD)

---

### Gap D: Production Debugging Integration — v1.3.3 (Q3 2028) [70 hours]

**Problem:** v1.2.0 helps when tests fail locally. Production team debugging (live systems, production errors) is not addressed.

**Current State (v1.2.0):** Generates debugging helpers for test failures. No production incident support.

**Proposed Solution: Production Incident Response Skill**

```
/one-shot-prompting:debug-production --error-log logs.txt --trace trace.json
→ Returns:
  - Root cause hypothesis (what likely went wrong)
  - Trace analysis (how did execution flow to failure?)
  - Repro in dev environment (steps to reproduce in staging)
  - Hotfix code (minimal fix for production)
  - Permanent fix (proper refactor + tests)
  - Monitoring additions (prevent recurrence)
```

**Implementation Details:**
- New skill: `skills/debug-production/`
- Parse error logs, stack traces, execution timelines
- Use Claude to identify patterns (out of memory? race condition? dependency timeout?)
- Generate repro scripts (testable in staging)
- Hotfix vs. permanent fix (different effort/safety tradeoffs)
- Integration with observability (suggest metrics/logs to add)
- Does NOT auto-deploy; user must approve hotfix

**Effort:** 70 hours
- Log parsing + trace analysis: 20h
- Root cause hypothesis generation: 15h
- Hotfix code generation: 15h
- Observability integration: 10h
- Testing + docs: 10h

**Timeline:** Q3 2028 (after v1.3.2)

**Success Metrics:**
- Production teams use plugin for incident response (not just generation)
- MTTR (mean time to recovery) drops 40-50%
- Support burden on ops team reduces by 30%

**Market Impact:** +5-10% (ops/SRE teams)

---

### Gap E: Legacy System Strangler Pattern — v1.4.0 (Q3-Q4 2028) [80 hours]

**Problem:** You generate clean modules for greenfield. Legacy systems (20-year-old monoliths) can't adopt your code without major refactoring.

**Current State (v1.2.0):** README says "adaptation notes" for legacy systems. That's not enough.

**Proposed Solution: Strangler Pattern Generator**

```
/one-shot-prompting:strangler --old-code legacy_app.py --feature new_auth
→ Returns:
  - New auth module (your standard generation)
  - Adapter layer (how new code calls old code, vice versa)
  - Migration strategy (how to gradually swap old → new)
  - Dual-run example (old + new running in parallel)
  - Rollback script (if new auth fails, revert to old)
  - Test harness (validate old + new produce same results)
```

**Implementation Details:**
- New skill: `skills/strangler-generator/`
- Analyze legacy code (import analysis, dependency mapping)
- Generate adapter layer automatically
- Create feature flag / routing logic (A/B test old vs. new)
- Database strategy (schema changes without downtime)
- Gradual cutover plan (week 1: 5% traffic, week 2: 50%, week 3: 100%)
- Supports Python (Django), Node.js (Express), PHP (Laravel) legacy codebases

**Effort:** 80 hours
- Legacy code analysis: 15h
- Adapter generation: 20h
- Feature flag + routing: 15h
- Database migration strategy: 15h
- Testing + docs: 15h

**Timeline:** Q3-Q4 2028 (significant effort)

**Success Metrics:**
- 50%+ of existing codebases can adopt one-shot generation
- Legacy teams report "we can now modernize incrementally"
- Adoption in enterprise (where most code is legacy) increases 2x

**Market Impact:** +30% (HUGE — legacy systems are 60-70% of enterprise)

---

### Gap F: Enterprise Cost Management — v1.3.4 (Q2 2028) [35 hours]

**Problem:** v0.9.5 estimates tokens. Enterprise teams want budget tracking, cost alerts, and optimization suggestions.

**Current State (v0.9.5):** Preview shows "this will use ~500 tokens." No enforcement or tracking.

**Proposed Solution: Cost Management Dashboard + CLI**

```
/one-shot-prompting:budget set --monthly 10000 tokens
/one-shot-prompting:usage today
→ Returns:
  - Tokens used today: 2,345 (23% of monthly budget)
  - Cost: $0.94 (at current pricing)
  - Largest generation: "auth endpoint" (892 tokens)
  - Trend: usage +15% week-over-week

/one-shot-prompting:generate --optimize <feature>
→ Returns:
  - Suggested approach: "Use dataclass instead of Pydantic (saves ~30 tokens)"
  - Token estimate: 450 (vs. baseline 650)
```

**Implementation Details:**
- Store budget settings in `.claude-plugin/budget.json`
- Track all generations in `.claude-plugin/usage-log.jsonl` (immutable)
- Warn if generation would exceed budget: "This will use 800 tokens; budget remaining is 500. Continue? [y/n]"
- Suggest optimizations: simpler libraries, fewer features, shorter READMEs
- Export usage report (CSV for finance)
- Optional: send to external cost tracking (Kubecost, AWS Cost Explorer)

**Effort:** 35 hours
- Budget system: 10h
- Usage tracking: 8h
- Cost estimation accuracy: 10h
- Optimization suggestions: 5h
- Testing + docs: 2h

**Timeline:** Q2 2028 (quick win)

**Success Metrics:**
- 80% of enterprise users set monthly budget
- 40% reduce token usage by 20-30% using optimization suggestions
- Finance teams approve tool for cost visibility

**Market Impact:** +10% (enterprise with strict budgets)

---

### Gap G: Cross-Codebase Consistency Validation — v1.4.1 (Q4 2028) [75 hours]

**Problem:** You generate modules independently. When users generate 5+ handlers, they don't interoperate (Handler A uses Pydantic, B uses dataclass; inconsistent error handling, logging).

**Current State (v1.2.0):** No validation across multiple generated modules.

**Proposed Solution: System Consistency Checker + Refactoring Generator**

```
/one-shot-prompting:check-consistency --codebase .
→ Returns:
  - INCONSISTENCY: Handler A uses Pydantic, Handler B uses dataclass
  - INCONSISTENCY: Handler A uses structlog, Handler B uses logging
  - INCONSISTENCY: Handler A has retry logic, Handler B doesn't
  - RECOMMENDATION: Extract shared library with DTO + error handling
  - ACTION: Run `/one-shot-prompting:standardize --library shared_handlers`

/one-shot-prompting:standardize --library shared_handlers
→ Returns:
  - New file: shared_handlers/dto.py (unified dataclass + Pydantic bridge)
  - Updated: handler_a.py (imports from shared, removes duplication)
  - Updated: handler_b.py (imports from shared, removes duplication)
  - New test: shared_handlers/test_consistency.py
  - Diff: removed 200 lines of duplicate code
```

**Implementation Details:**
- New skill: `skills/consistency-checker/`
- Scan all generated modules (import patterns, library usage)
- Identify inconsistencies: serialization, error handling, logging, async patterns
- Suggest shared library extraction
- Generate refactoring automatically (remove duplication, import from shared)
- Test that refactored code still works (regression test)
- Optional: enforce consistency before generation (prevent inconsistencies)

**Effort:** 75 hours
- Codebase analysis: 15h
- Inconsistency detection: 15h
- Shared library extraction: 20h
- Refactoring generation: 15h
- Testing + docs: 10h

**Timeline:** Q4 2028 (after core features stable)

**Success Metrics:**
- 70% of multi-handler systems use consistency checker
- Average codebase reduces duplication by 20-30%
- Developers report "modules talk to each other now"

**Market Impact:** +15% (systems with 5+ interconnected modules)

---

### Gap H: Non-Event-Driven Code Expansion — Out of Scope (By Design)

**Decision:** DO NOT add CRUD/UI/data science/mobile support. This would dilute your specialization.

**Strategic Foundation:** See "🎯 STRATEGIC SCOPE DECISIONS" section (top of document) for complete analysis of what we build vs. don't build.

**Quick Summary:**
- ❌ CRUD APIs (owned by Superpowers + Copilot)
- ❌ UI generation (15+ competitors, not event-driven)
- ❌ Data science / ML (different expertise, different market)
- ❌ Mobile apps (different framework set, not events)
- ✅ Event-driven systems (40-50% of backends, 0 competitors)

**Why This Matters:**
- You own "event-driven systems" niche (40-50% of production backend code)
- CRUD + UI = 40% of market, but saturated with 10+ competitors
- Your competitive advantage is DEPTH (event-driven expert), not BREADTH
- Expanding to CRUD would make you 60% worse at events to be 10% better at CRUD

**Market Math:**
- Generalist: compete with ChatGPT/Copilot for 5% of market = $10-20M
- Specialist: own 50% of event niche = 25% of valuable market = $150-210M

**Recommended Strategy:**
- Document scope boundaries in README: "For CRUD APIs, use Claude directly or Superpowers. One-Shot specializes in event-driven backend systems."
- Create integration guide: "Design schema with Superpowers; generate CRUD endpoint with Claude; use One-Shot for event handlers, orchestration, async workflows"
- Market to developers who work PRIMARILY on events (not secondarily)
- When users ask for out-of-scope features: "One-Shot is specialized for events. Here's a tool better suited for [CRUD/UI/ML]."

**Market Impact of NOT expanding:** Cede 40% of market, but own 50% of the 60% remaining (event niche). Net: you own 30% of high-value market vs. competing for 5% of generic market.

---

## Revised Complete Roadmap (v0.7.0 → v1.4.1)

| Version | Timeline | Focus | Effort | Market Impact |
|---------|----------|-------|--------|--------------|
| **v0.7.0-Critical-Gaps** | Q2-Q3 2026 | Multi-file, auto-wiring, migrations, slash commands | 320h | Foundation for v1.0.0 |
| **v0.8.0** | Q4 2026-Q1 2027 | Event catalog enforcement, integration tests | 100h | Enterprise integration |
| **v0.9.0** | Q1-Q2 2027 | Domain-specific observability (logging, metrics) | 80h | Production readiness |
| **v0.9.5** | Q2 2027 | Dual-mode workflows (flow vs. spec), cost visibility | 40h | Flow + safety |
| **v0.10.0** | Q3 2027 | Code review automation (linting, security, performance) | 30h | Quality gates |
| **v1.1.0** | Q3-Q4 2027 | Test-first mode (TDD) with learning | 25h | Methodology discipline |
| **v1.2.0** | Q4 2027 | Debugging helpers (error patterns, repro scripts) | 40h | Local dev support |
| **→ v1.0.0** | Q4 2027-Q1 2028 | Enterprise launch (after v0.7.0-v1.2.0 complete) | — | Market readiness |
| **v1.3.0** | Q1-Q2 2028 | Architecture design skill (lightweight blueprints) | 60h | Pre-generation planning |
| **v1.3.1** | Q2 2028 | GitHub/GitLab PR integration (team review workflow) | 50h | Enterprise governance |
| **v1.3.2** | Q2-Q3 2028 | TDD learning experience (explain methodology) | 40h | Knowledge transfer |
| **v1.3.3** | Q3 2028 | Production debugging integration (incident response) | 70h | Ops/SRE adoption |
| **v1.4.0** | Q3-Q4 2028 | Legacy system strangler pattern (incremental adoption) | 80h | 30% market expansion |
| **v1.3.4** | Q2 2028 (parallel) | Enterprise cost management (budgets, tracking) | 35h | Budget control |
| **v1.4.1** | Q4 2028 | Cross-codebase consistency checker + refactoring | 75h | System-wide quality |
| **→ v2.0.0** | Q1 2029+ | Market leader in event-driven code generation | — | Establish moat |

**Total Effort (v0.7.0 → v1.4.1):** ~1,200 hours (~6 months full-time, or 12 months part-time)

**Market Position by v1.4.1 (Q4 2028):**
- Own 50% of event-driven niche (+ 30% legacy modernization)
- 8-12% of global dev market
- Enterprise adoption: 40-50% of companies modernizing legacy systems
- Complementary positioning with Superpowers (not competitive)

---

**Document Status:** Local plan. Not committed to git. For strategic guidance and team discussion.
**Last Updated:** April 25, 2026 (FINAL: Full Roadmap v0.7.0 → v1.4.1 with Gap Closure Strategy Added)
**Next Review:** Before v0.9.5 planning (Q1 2027)
**Implementation Owner:** @usmanmughaltaleemabad

**Competitive Analysis Reference:** See `.claude-plugin/COMPETITIVE_ANALYSIS.md` for full audit, best practices alignment, and gap breakdown.

### Executive Summary: Three-Phase Market Conquest Strategy

**Phase 1: Foundation (Q2-Q3 2026) — v0.7.0-Critical-Gaps**
- Goal: Reality catches up with marketing ("complete features," not "single files")
- Effort: 320 hours (8 weeks)
- Do NOT launch v1.0.0 until this phase completes
- Deliverable: Production-ready, multi-file, auto-wired code generation

**Phase 2: Specialization (Q3 2027-Q1 2028) — v0.8.0 through v1.2.0**
- Goal: Close quality gaps (code review, TDD, debugging) to compete with Superpowers
- Effort: 315 hours (scattered across 6 versions)
- Deliverable: Enterprise-ready tool with optional discipline (TDD), safety (code review), and support (debugging)
- Launch v1.0.0 at end of this phase (Q4 2027-Q1 2028)

**Phase 3: Expansion (Q1-Q4 2028) — v1.3.0 through v1.4.1**
- Goal: Close remaining gaps (architecture, team workflows, legacy systems, cost management, consistency)
- Effort: 445 hours (distributed across 7 versions)
- Deliverable: Comprehensive event-driven ecosystem (50% of niche + 30% legacy market)
- Reach v2.0.0 market leader position by Q1 2029

**Total Investment:** ~1,200 hours over 3 years
**Expected ROI:** 8-12% of global dev market, focused on high-value event-driven + enterprise segments
**Competitive Position:** NOT trying to be Superpowers (methodology) — being the expert in speed + framework awareness + event-driven specialization

**COMPLETE ROADMAP TIMELINE (v0.6.0 → v2.0.0):**

```
Q2-Q3 2026
└─ 🔴 v0.7.0-Critical-Gaps (320h) ← HIGHEST PRIORITY
   ├─ Phase 1: Multi-File (60h)
   ├─ Phase 2: Auto-Wiring (30h)
   ├─ Phase 3: Migrations (40h)
   ├─ Phase 4: Slash Commands (50h)
   ├─ Phase 5: DI Wiring (25h)
   ├─ Phase 6: Multi-Handler (70h)
   ├─ Phase 7: Configuration (25h)
   └─ Phase 8: OpenAPI (20h)

Q3-Q4 2026
└─ v0.7.0: Bus Auto-Detection

Q4 2026-Q1 2027
└─ v0.8.0: Event Catalog + Integration Tests

Q1-Q2 2027
└─ v0.9.0: Domain-Specific Observability

Q2 2027
├─ v0.9.5: Dual-Mode + Cost Visibility
└─ v1.3.4: Enterprise Cost Management (35h, parallel)

Q3 2027
├─ v0.10.0: Code Review Automation (30h)
├─ v1.1.0: Test-First Mode (25h)
└─ v1.3.2: TDD Learning (40h, parallel)

Q4 2027
├─ v1.2.0: Debugging Helpers (40h)
└─ v1.0.0: ENTERPRISE LAUNCH ← Launched after all gaps closed

Q1-Q2 2028
├─ v1.3.0: Architecture Design (60h)
└─ v1.3.1: GitHub PR Integration (50h)

Q2-Q3 2028
├─ v1.3.3: Production Debugging (70h)
└─ (Optional: parallel other work)

Q3-Q4 2028
├─ v1.4.0: Legacy Strangler Pattern (80h)
└─ v1.4.1: Consistency Checker (75h)

Q1 2029+
└─ v2.0.0: Market Leader Status
```

**Key Milestones (Updated May 10, 2026):**
- ✅ **v0.6.1 (May 2026):** Phase 0 marketplace-ready
- ✅ **v2.0.0 (May 2026):** REST API (44 modules) + Batch Jobs (13 modules) shipped
- 🟡 **v0.7.0 (May 20, 2026):** Phase 1 completion (multi-file, auto-wiring, migrations) → Marketplace launch
- 📋 **v3.0.0 (Sep 2026):** Phase 4 Production Hardening (DDD, CQRS, TDD, chaos, compliance) → Enterprise ready
- 📋 **v4.0.0 (Dec 2026):** Phase 5 Advanced Patterns (microservices, real-time, GraphQL, ML, legacy) → Market leader
- 📋 **v5.0.0 (Dec 2026):** 177 modules, 47,361 LOC, 15-20% market penetration

**Current Status:** 57/177 modules (32%), 5-8% market adoption, enterprise pilots in progress

---

**Document Status:** Last updated May 10, 2026. Doc cleanup complete: 49 outdated docs archived, FUTURE_PLAN updated with current progress.
