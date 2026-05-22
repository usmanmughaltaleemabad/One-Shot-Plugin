---
type: implementation-plan
last_verified: 2026-05-21
owner: usman
scope: Harness Phase 7 — domain standards enforcement
---

# Harness Phase 7 — Domain Standards Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development. Each task is 10-20 minutes. Checkpoint after Task 5 before wiring hooks.

**Goal:** Create `.claude/standards/` directory with 8 enforceable domain rules that codify plugin best practices.

**Architecture:** YAML + Markdown standards that are:
- **Discoverable** (REGISTRY.md lists all with enforcement strategy)
- **Enforceable** (2 rules wired into PreToolUse/PostToolUse hooks)
- **Extensible** (README explains how to add new standards)

**Tech Stack:** Markdown, YAML, Python (for hook integration)

---

## File Structure

```
.claude/standards/
├── REGISTRY.md              ← Master index (40 lines)
├── generated-code.md        ← GEN-001 to GEN-008 (120 lines)
├── testing.md               ← Test coverage + isolation rules (80 lines)
├── security.md              ← OWASP + secret detection (100 lines)
├── fk-validation.md         ← FK relationship integrity (60 lines)
├── api-documentation.md     ← OpenAPI + schema (70 lines)
├── performance.md           ← N+1 queries, indexing (60 lines)
└── README.md                ← How to extend standards (50 lines)
```

---

## Task 1: Create `.claude/standards/` Directory & REGISTRY.md

**Files:**
- Create: `.claude/standards/REGISTRY.md`

- [ ] **Step 1: Create directory**

```bash
mkdir -p .claude/standards
```

- [ ] **Step 2: Write REGISTRY.md**

```markdown
---
type: reference
last_verified: 2026-05-21
owner: usman
---

# Standards Registry

Master index of all domain rules enforced in code generation.

## How Standards Work

1. **Define** — each standard in its own file (generated-code.md, testing.md, etc.)
2. **Enforce** — via hooks (PreToolUse blocks, PostToolUse validation) or agent checks
3. **Extend** — add new standards by creating a file + updating REGISTRY

## Active Standards (8 total)

| ID | Category | Rule | Enforcement | Exempt? |
|---|---|---|---|---|
| GEN-001 | Generated Code | All generated code must include tests | Hook: PostToolUse scans for test file | marked @skip-test |
| GEN-002 | Generated Code | Foreign key relationships auto-validated | Hook: PostToolUse validates FK syntax | N/A |
| GEN-003 | Security | Security scan (OWASP top 10) before ship | Agent: reviewer runs bandit/semgrep | marked @unsafe |
| GEN-004 | API Documentation | API endpoints documented in OpenAPI | Hook: PostToolUse checks openapi.json | marked @undocumented |
| GEN-005 | Code Quality | All models include type hints | Hook: PostToolUse scans types | marked @untyped |
| GEN-006 | Security | No hardcoded secrets (scan with truffleHog) | Hook: PostToolUse runs truffleHog | none |
| GEN-007 | Migrations | Migrations reversible (Alembic UP/DOWN) | Agent: migration-verifier runs migrations | none |
| GEN-008 | Performance | N+1 query detection on ORMs | Agent: performance-auditor scans ORM | marked @slow-ok |

## Standard Files

- [generated-code.md](generated-code.md) — GEN-001, GEN-002, GEN-005
- [testing.md](testing.md) — Test coverage, isolation requirements
- [security.md](security.md) — GEN-003, GEN-006
- [api-documentation.md](api-documentation.md) — GEN-004
- [performance.md](performance.md) — GEN-008
- [fk-validation.md](fk-validation.md) — GEN-002 detailed rules

## How to Add a New Standard

1. Create a new file (e.g., `.claude/standards/logging.md`)
2. Include YAML frontmatter + rule definition (see any file for template)
3. Add row to REGISTRY table
4. (Optional) Wire into hook if enforcement is automated

See [README.md](README.md) for details.
```

- [ ] **Step 3: Commit**

```bash
git add .claude/standards/REGISTRY.md
git commit -m "feat(P7): initialize standards registry"
```

---

## Task 2: Write Generated Code Standards (GEN-001, GEN-002, GEN-005)

**Files:**
- Create: `.claude/standards/generated-code.md`

- [ ] **Step 1: Write generated-code.md**

```markdown
---
type: reference
last_verified: 2026-05-21
owner: usman
---

# Generated Code Standards

Rules for code produced by the one-shot pipeline.

## GEN-001: All Generated Code Must Include Tests

**Rule:** Every generated file with business logic must have a corresponding test file.

**Scope:**
- Models, services, API endpoints, background jobs: REQUIRED
- Config files, migrations, type stubs: EXEMPT
- Mark files with `@skip-test` comment to exempt

**Enforcement:** Hook: PostToolUse scans for test files
```python
# Example: if generated file is services/cart.py, must have tests/test_cart.py
```

**Exemption Pattern:**
```python
# @skip-test
# config: migrations config, no logic to test
class MigrationConfig:
    pass
```

**How to Test:** After generation, `pytest tests/ -v` must pass all tests.

---

## GEN-002: Foreign Key Relationships Auto-Validated

**Rule:** All foreign key declarations must be syntactically valid and point to existing models.

**Scope:**
- All ORM models (SQLAlchemy, Django ORM, etc.)
- Relationships defined via ForeignKey or relationship()
- Must match schema in spec.json

**Enforcement:** Hook: PostToolUse runs validation script
```python
# Validates:
# - FK column type matches referenced PK type
# - Referenced model exists
# - No circular references without explicit backref
```

**Valid Example (SQLAlchemy):**
```python
class Cart(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    user: Mapped["User"] = relationship("User", back_populates="carts")
```

**Invalid Example (caught by GEN-002):**
```python
class Cart(Base):
    user_id: Mapped[int] = mapped_column(ForeignKey("NonExistentModel.id"))
    # ❌ NonExistentModel doesn't exist
```

---

## GEN-005: All Models Include Type Hints

**Rule:** All model definitions must use type hints for all attributes.

**Scope:**
- Pydantic models (FastAPI)
- SQLAlchemy mapped classes
- TypedDict definitions
- Django models

**Enforcement:** Hook: PostToolUse scans for untyped attributes

**Valid Example (Pydantic):**
```python
class CartItem(BaseModel):
    id: int
    quantity: int
    price: Decimal
    cart_id: int
```

**Invalid Example (caught by GEN-005):**
```python
class CartItem(BaseModel):
    id = 1  # ❌ Missing type hint
    quantity: int
```

**Exemption:** Mark with `@untyped` if absolutely necessary (rare).
```python
class LegacyModel:  # @untyped — maintains compatibility with old code
    data = None
```
```

- [ ] **Step 2: Commit**

```bash
git add .claude/standards/generated-code.md
git commit -m "feat(P7): add generated code standards (GEN-001, GEN-002, GEN-005)"
```

---

## Task 3: Write Testing Standards

**Files:**
- Create: `.claude/standards/testing.md`

- [ ] **Step 1: Write testing.md**

```markdown
---
type: reference
last_verified: 2026-05-21
owner: usman
---

# Testing Standards

Rules for test coverage and quality in generated code.

## Test Coverage Requirement

**Rule:** Generated code must have ≥80% test coverage.

**How Measured:**
```bash
pytest --cov=src tests/ --cov-report=term-missing
```

**Coverage by Module Type:**
- Models/schemas: ≥90% (simple logic, easy to test)
- Service/business logic: ≥85% (core logic, all paths covered)
- API endpoints: ≥80% (happy path + error cases)
- Utilities: ≥75% (optional, dependencies can vary)

**Enforcement:** Critic agent measures coverage post-generation. Fails if <80%.

## Test Isolation

**Rule:** Tests must not depend on each other or external services.

**Requirements:**
- Each test is independent (no shared state)
- Use fixtures for setup/teardown
- Mock external APIs (don't call real APIs)
- Use in-memory database for unit tests

**Valid Example:**
```python
@pytest.fixture
def cart():
    return Cart(id=1, user_id=1)

def test_add_item_to_cart(cart):
    cart.add_item(item_id=1, quantity=1)
    assert len(cart.items) == 1
```

**Invalid Example:**
```python
# ❌ Depends on external API
def test_process_payment():
    response = stripe.charge(amount=100)
    assert response.status == "success"
```

## Test Naming

**Rule:** Test names must clearly describe what's being tested.

**Pattern:** `test_<function>_<scenario>_<expected_result>`

**Valid Examples:**
- `test_calculate_discount_with_bulk_order_returns_lower_price()`
- `test_add_item_to_empty_cart_increments_count()`
- `test_invalid_email_raises_validation_error()`

**Invalid Examples:**
- `test_it_works()` — unclear
- `test_1()` — no meaning
```

- [ ] **Step 2: Commit**

```bash
git add .claude/standards/testing.md
git commit -m "feat(P7): add testing standards"
```

---

## Task 4: Write Security Standards (GEN-003, GEN-006)

**Files:**
- Create: `.claude/standards/security.md`

- [ ] **Step 1: Write security.md**

```markdown
---
type: reference
last_verified: 2026-05-21
owner: usman
---

# Security Standards

Rules for secure code generation.

## GEN-003: OWASP Top 10 Compliance

**Rule:** All generated code must pass security scanning for OWASP Top 10 vulnerabilities.

**Top 10 Categories Scanned:**
1. Injection (SQL, OS, LDAP, etc.)
2. Broken Authentication
3. Sensitive Data Exposure
4. XML External Entities (XXE)
5. Access Control Bypass
6. Security Misconfiguration
7. Cross-Site Scripting (XSS)
8. Insecure Deserialization
9. Using Components with Known Vulnerabilities
10. Insufficient Logging & Monitoring

**Enforcement:** Reviewer agent runs bandit (Python) or semgrep (multi-language)

**Valid Example:**
```python
# ✅ Uses parameterized queries
def get_user(user_id: int) -> User:
    return db.query(User).filter(User.id == user_id).first()
```

**Invalid Example (caught by GEN-003):**
```python
# ❌ SQL injection vulnerability
def get_user(user_id: str) -> User:
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return db.execute(query)
```

## GEN-006: No Hardcoded Secrets

**Rule:** Generated code must not contain hardcoded credentials, API keys, or secrets.

**Scope:**
- Database passwords, API keys, OAuth tokens
- Private encryption keys
- AWS/Azure/GCP credentials

**Enforcement:** Hook: PostToolUse runs truffleHog (secret detection)

**Valid Example:**
```python
# ✅ Secrets from environment
db_password = os.getenv("DB_PASSWORD")
api_key = os.getenv("ANTHROPIC_API_KEY")
```

**Invalid Example (caught by GEN-006):**
```python
# ❌ Hardcoded secret
api_key = "sk-proj-abcdef123456"
db_password = "mysecret123"
```

**Exemption:** Mark with `@unsafe` only in test fixtures
```python
@pytest.fixture
def mock_api_key():  # @unsafe — test fixture only
    return "test-key-12345"
```
```

- [ ] **Step 2: Commit**

```bash
git add .claude/standards/security.md
git commit -m "feat(P7): add security standards (GEN-003, GEN-006)"
```

---

## Task 5: Write API Documentation & Performance Standards

**Files:**
- Create: `.claude/standards/api-documentation.md`
- Create: `.claude/standards/performance.md`

- [ ] **Step 1: Write api-documentation.md**

```markdown
---
type: reference
last_verified: 2026-05-21
owner: usman
---

# API Documentation Standards

## GEN-004: API Endpoints Documented in OpenAPI

**Rule:** All generated API endpoints must be documented in OpenAPI specification.

**Scope:**
- FastAPI: auto-generated via docstrings + type hints
- Django REST: explicit serializers + docstrings
- Spring: Swagger annotations

**Enforcement:** Generator produces openapi.json; reviewer validates schema matches endpoints.

**Valid Example (FastAPI):**
```python
@app.post("/carts", response_model=CartResponse)
async def create_cart(request: CartCreate) -> CartResponse:
    """Create a new shopping cart.
    
    Parameters:
      request: Cart creation details
    
    Returns:
      CartResponse: Created cart with ID
    """
    cart = Cart(**request.dict())
    db.add(cart)
    db.commit()
    return cart
```

**Invalid Example (caught by GEN-004):**
```python
@app.post("/carts")  # ❌ No docstring, missing response_model
def create_cart(request):
    return Cart()
```
```

- [ ] **Step 2: Write performance.md**

```markdown
---
type: reference
last_verified: 2026-05-21
owner: usman
---

# Performance Standards

## GEN-008: N+1 Query Detection

**Rule:** Generated ORM code must not have N+1 query patterns.

**Pattern to Avoid:**
```python
# ❌ N+1: Loop queries the database repeatedly
carts = db.query(Cart).all()
for cart in carts:
    items = cart.items  # Queries 1x per cart (N queries)
    print(items)
```

**Correct Pattern:**
```python
# ✅ Single query with eager loading
carts = db.query(Cart).options(joinedload(Cart.items)).all()
for cart in carts:
    items = cart.items  # Already loaded (1 query total)
    print(items)
```

**Enforcement:** Performance auditor scans generated code for missing joinedload/prefetch_related.

**Exemption:** Mark with `@slow-ok` if intentional (rare)
```python
def get_cart_with_details(cart_id):  # @slow-ok — intentional for batch processing
    # ...
```
```

- [ ] **Step 3: Commit**

```bash
git add .claude/standards/api-documentation.md .claude/standards/performance.md
git commit -m "feat(P7): add API documentation and performance standards (GEN-004, GEN-008)"
```

---

## Task 6: Write FK Validation & README

**Files:**
- Create: `.claude/standards/fk-validation.md`
- Create: `.claude/standards/README.md`

- [ ] **Step 1: Write fk-validation.md**

```markdown
---
type: reference
last_verified: 2026-05-21
owner: usman
---

# Foreign Key Validation Standards

Detailed rules for validating foreign key relationships (GEN-002).

## Validation Rules

1. **Type Match:** FK column type must match referenced PK type
2. **Model Exists:** Referenced model must be defined in the same generation or existing codebase
3. **No Circular References:** Unless explicitly handled with backref/back_populates
4. **Cascade Semantics:** ON DELETE behavior must match domain logic

## Validation Script

The hook runs this logic:
```python
def validate_foreign_keys(spec_json: dict, generated_files: list) -> bool:
    errors = []
    for entity in spec_json['entities']:
        for rel in entity.get('foreign_keys', []):
            # Check type match
            if not type_matches(rel['type'], rel['references_type']):
                errors.append(f"Type mismatch in {entity.name}.{rel.column}")
            
            # Check model exists
            if not model_exists(rel['references_model']):
                errors.append(f"Model {rel['references_model']} not found")
    
    return len(errors) == 0, errors
```
```

- [ ] **Step 2: Write README.md**

```markdown
---
type: reference
last_verified: 2026-05-21
owner: usman
---

# Standards Directory

Home of domain rules enforced in the one-shot-prompting plugin.

## How Standards Work

**Define** → **Enforce** → **Extend**

1. **Define:** Each standard in its own file (e.g., `generated-code.md`)
2. **Enforce:** Via hooks (PreToolUse/PostToolUse) or agent checks
3. **Extend:** Add new standards by creating a file + updating REGISTRY.md

## Using Standards

When you run `/one-shot`, the pipeline automatically:
1. Checks generated code against all active standards
2. Blocks code that violates mandatory rules (GEN-003, GEN-006)
3. Logs violations and suggests fixes

## Adding a New Standard

### Step 1: Create the file
```bash
touch .claude/standards/your-standard.md
```

### Step 2: Write the standard
```markdown
---
type: reference
last_verified: YYYY-MM-DD
owner: your-name
---

# Your Standard Name

**Rule:** Clear one-sentence rule

**Scope:** What this applies to

**Enforcement:** How it's checked

**Valid Example:**
```code
```

**Invalid Example:**
```code
```

**Exemption:** If applicable, how to exempt
```

### Step 3: Update REGISTRY.md
Add row to standards table:
```markdown
| ID | Category | Rule | Enforcement | Exempt? |
| YOUR-001 | Category | Your rule | Hook: ... | yes/no |
```

### Step 4: (Optional) Wire into hook
If enforcement is automatic, add to `.claude/hooks/PostToolUse.py`

### Step 5: Commit
```bash
git add .claude/standards/your-standard.md REGISTRY.md
git commit -m "feat(standards): add your-standard"
```

## Current Standards

See [REGISTRY.md](REGISTRY.md) for the full list of 8 active standards.

## Questions?

- **How do I disable a standard?** Add `@exemption-name` comment to code
- **Can I override a standard?** Only with exemption marker; mandatory rules cannot be overridden
- **How do I report a false positive?** Open an issue with the rule ID (e.g., GEN-001)
```

- [ ] **Step 3: Commit**

```bash
git add .claude/standards/fk-validation.md .claude/standards/README.md
git commit -m "feat(P7): add FK validation guide and standards README"
```

---

## Task 7: Wire GEN-001 (Test Coverage) into PostToolUse Hook

**Files:**
- Modify: `.claude/hooks/PostToolUse.py`

- [ ] **Step 1: Read the current hook**

```bash
cat .claude/hooks/PostToolUse.py | head -50
```

Expected: Hook runs post-tool-use validation checks.

- [ ] **Step 2: Add GEN-001 validation function to PostToolUse.py**

Append to file:
```python
def check_GEN_001_test_coverage(file_path: str, file_content: str) -> tuple[bool, str]:
    """GEN-001: All generated code must include tests."""
    
    # Skip non-Python files and test files themselves
    if not file_path.endswith('.py') or file_path.startswith('tests/'):
        return True, "OK"
    
    # Skip exempted files
    if '@skip-test' in file_content:
        return True, "OK (exempted)"
    
    # Extract expected test file path
    test_file = file_path.replace('src/', 'tests/test_').replace('.py', '_test.py')
    
    # Check if test file exists (stub OK)
    import os
    if os.path.exists(test_file):
        return True, "OK"
    
    return False, f"GEN-001 FAIL: No test file found for {file_path}. Expected: {test_file}"
```

- [ ] **Step 3: Add check to hook's main logic**

Find the line that looks like:
```python
def on_tool_write(file_path: str, file_content: str) -> bool:
    """Run all post-write validation checks."""
```

Add this after existing checks:
```python
    # GEN-001: Test coverage
    success, message = check_GEN_001_test_coverage(file_path, file_content)
    if not success:
        logger.warning(message)
        # Don't block; log as warning
```

- [ ] **Step 4: Test the hook**

Create a test file to verify:
```bash
cat > /tmp/test_gen001.py << 'EOF'
import sys
sys.path.insert(0, './.claude/hooks')
from PostToolUse import check_GEN_001_test_coverage

# Test 1: File with test coverage (should pass)
result, msg = check_GEN_001_test_coverage('src/models/user.py', 'class User: pass')
assert result == False, "Expected to fail (no test file)"
print("✅ Test 1 passed")

# Test 2: Exempted file (should pass)
result, msg = check_GEN_001_test_coverage('src/config.py', '@skip-test\nclass Config: pass')
assert result == True, "Expected to pass (exempted)"
print("✅ Test 2 passed")

print("All GEN-001 tests passed!")
EOF
python /tmp/test_gen001.py
```

- [ ] **Step 5: Commit**

```bash
git add .claude/hooks/PostToolUse.py
git commit -m "feat(P7): wire GEN-001 (test coverage) into PostToolUse hook"
```

---

## Task 8: Wire GEN-006 (No Hardcoded Secrets) into PostToolUse Hook

**Files:**
- Modify: `.claude/hooks/PostToolUse.py`

- [ ] **Step 1: Add secret detection function**

Append to PostToolUse.py:
```python
def check_GEN_006_no_secrets(file_path: str, file_content: str) -> tuple[bool, str]:
    """GEN-006: No hardcoded secrets (API keys, passwords, tokens)."""
    
    import re
    
    # Skip test fixtures marked @unsafe
    if '@unsafe' in file_content:
        return True, "OK (test fixture exempted)"
    
    # Patterns to detect
    secret_patterns = [
        (r'api_key\s*=\s*["\']sk-[a-zA-Z0-9]{20,}["\']', 'API key'),
        (r'password\s*=\s*["\'][^"\']{8,}["\']', 'Password'),
        (r'secret\s*=\s*["\'][^"\']{8,}["\']', 'Secret'),
        (r'token\s*=\s*["\'][a-zA-Z0-9_-]{20,}["\']', 'Token'),
    ]
    
    for pattern, secret_type in secret_patterns:
        if re.search(pattern, file_content):
            return False, f"GEN-006 FAIL: Hardcoded {secret_type} detected in {file_path}"
    
    return True, "OK"
```

- [ ] **Step 2: Add check to main hook logic**

Add after GEN-001 check:
```python
    # GEN-006: No hardcoded secrets
    success, message = check_GEN_006_no_secrets(file_path, file_content)
    if not success:
        logger.error(message)
        raise ValidationError(message)  # Block this!
```

- [ ] **Step 3: Test the function**

```bash
cat > /tmp/test_gen006.py << 'EOF'
import sys
sys.path.insert(0, './.claude/hooks')
from PostToolUse import check_GEN_006_no_secrets

# Test 1: Code with hardcoded secret (should fail)
code = 'api_key = "sk-proj-12345678901234567890"'
result, msg = check_GEN_006_no_secrets('config.py', code)
assert result == False, "Expected to fail"
print("✅ Test 1 passed")

# Test 2: Code with env var (should pass)
code = 'api_key = os.getenv("ANTHROPIC_API_KEY")'
result, msg = check_GEN_006_no_secrets('config.py', code)
assert result == True, "Expected to pass"
print("✅ Test 2 passed")

# Test 3: Test fixture exempted (should pass)
code = '@unsafe\ndef test_auth():\n    token = "test-token-123"'
result, msg = check_GEN_006_no_secrets('tests/test_auth.py', code)
assert result == True, "Expected to pass (exempted)"
print("✅ Test 3 passed")

print("All GEN-006 tests passed!")
EOF
python /tmp/test_gen006.py
```

- [ ] **Step 4: Commit**

```bash
git add .claude/hooks/PostToolUse.py
git commit -m "feat(P7): wire GEN-006 (no hardcoded secrets) into PostToolUse hook"
```

---

## Checkpoint: P7 Complete

**Deliverables:**
- ✅ `.claude/standards/` directory with 8 rule files
- ✅ REGISTRY.md documenting all standards
- ✅ README.md explaining how to extend standards
- ✅ 2 rules (GEN-001, GEN-006) wired into hooks

**Tests:**
- ✅ GEN-001 validation tests passed
- ✅ GEN-006 validation tests passed
- ✅ All 7 commits created

**Next:** P7 standards are ready. Can now be used by P9 evaluation and integrated into pipeline.
