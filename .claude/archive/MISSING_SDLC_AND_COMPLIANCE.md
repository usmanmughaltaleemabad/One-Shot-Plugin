# Missing SDLC Processes & Anthropic Plugin Compliance Gaps

**Purpose:** Specific, actionable gaps in software development practices and marketplace compliance  
**Status:** Post-infrastructure audit  
**Date:** 2026-05-09

---

## PART 1: MISSING SDLC PROCESSES

### 1. Release Management Process

**What's Missing:**
```
Current State:
  - Bump version in plugin.json manually
  - Update CHANGELOG.md manually
  - No pre-release validation
  - No beta/staging release track
  - No rollback procedure
  - No customer notification process

What Should Exist:
  - Automated version bumping (using git tags)
  - Semantic versioning policy enforced
  - Pre-release checklist (automated + manual)
  - Beta release track (.beta, .rc versions)
  - Release notes auto-generated from git commits
  - Rollback playbook for each release
  - Customer notification template
```

**Action Items:**
- [ ] Create `.github/workflows/release.yml` (automated)
  - Trigger on git tag (v1.0.0)
  - Run full test suite
  - Generate release notes from CHANGELOG.md
  - Create GitHub release
  - Publish to marketplace

- [ ] Create `RELEASE_CHECKLIST.md`
  ```
  Pre-release (48h before):
  - [ ] All tests passing
  - [ ] Security review complete
  - [ ] Documentation updated
  - [ ] Performance benchmarks ok
  - [ ] CHANGELOG.md written
  - [ ] Version bumped
  
  Release (go-live):
  - [ ] Tag git commit
  - [ ] CI/CD pipeline triggered
  - [ ] Marketplace updated
  - [ ] Announce on blog/twitter/email
  - [ ] Monitor error logs (first hour)
  
  Post-release (24h):
  - [ ] Customer feedback collected
  - [ ] Metrics validated
  - [ ] No critical bugs reported
  ```

- [ ] Create release notes template
  ```
  # v1.0.0 — Legacy Strangler Public Launch
  
  ## ✨ New Features
  - /strangler-analyze: Identify extraction candidates
  - /strangler-extract: Generate microservices
  
  ## 🐛 Bug Fixes
  - [List]
  
  ## ⚠️ Breaking Changes
  - [List]
  
  ## 📚 Migration Guide
  - [Link to docs]
  ```

---

### 2. Code Review & Quality Gates

**What's Missing:**
```
Current State:
  - PRs possible but no formal process
  - No review checklist
  - No approval workflow
  - Automated checks basic

What Should Exist:
  - Code review checklist (security, performance, style)
  - Approval workflow (2 reviewers for critical)
  - Automated quality gates (fail if < 75% coverage)
  - Style enforcement (black, pylint pass required)
  - Security scan (bandit, semgrep)
  - Type checking (mypy pass required)
```

**Action Items:**
- [ ] Create `.github/PULL_REQUEST_TEMPLATE.md`
  ```
  ## Description
  What does this PR do?
  
  ## Strangler Impact
  Does this affect strangler commands? (Yes/No)
  
  ## Testing
  How tested? What scenarios?
  
  ## Checklist
  - [ ] Code follows style guide
  - [ ] Tests added/updated
  - [ ] Documentation updated
  - [ ] No debug logging left
  - [ ] Performance impact assessed
  - [ ] Security implications considered
  ```

- [ ] Add code review checklist comment (auto-posts on PR)
  ```
  ## Code Review Checklist
  
  Maintainer will verify:
  - [ ] Follows project conventions
  - [ ] Tests cover changes
  - [ ] Performance impact acceptable
  - [ ] No security vulnerabilities
  - [ ] Documentation accurate
  - [ ] No breaking changes (or documented)
  ```

- [ ] Enforce branch protection rules (require)
  - 2 approvals for main
  - All checks pass
  - No merge while build fails

- [ ] Add `.github/workflows/code-quality.yml`
  ```yaml
  on: [pull_request]
  jobs:
    lint:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v3
        - run: pip install black pylint mypy
        - run: black --check .
        - run: pylint scripts/ skills/
        - run: mypy scripts/ skills/
    security:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v3
        - run: pip install bandit semgrep
        - run: bandit -r scripts/
    coverage:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v3
        - run: pip install pytest pytest-cov
        - run: pytest --cov=scripts --cov=skills
        - run: |
            coverage > 75% or exit 1
  ```

---

### 3. Incident Response & On-Call

**What's Missing:**
```
Current State:
  - Issues go to GitHub
  - No formal response SLA
  - No incident classification
  - No post-mortem process
  - No on-call rotation

What Should Exist:
  - Incident severity classification (P1-P4)
  - Response SLAs per severity
  - On-call rotation (email escalation)
  - Incident runbook (common failures)
  - Post-mortem template (root cause analysis)
  - Action items tracking
```

**Action Items:**
- [ ] Create `INCIDENT_RESPONSE.md`
  ```
  ## Severity Levels
  
  P1 (Critical): Complete outage
    - Response: 15 minutes
    - Resolution: 4 hours
    - Escalate: CC team leads
  
  P2 (High): Major feature broken
    - Response: 1 hour
    - Resolution: 8 hours
    - Escalate: On-call engineer
  
  P3 (Medium): Feature partially broken
    - Response: 4 hours
    - Resolution: 24 hours
    - Escalate: Backlog prioritization
  
  P4 (Low): Minor issue, workaround exists
    - Response: 1 week
    - Resolution: Next sprint
  
  ## Response Checklist
  1. Classify severity
  2. Notify stakeholders (email template)
  3. Assign on-call engineer
  4. Investigate + communicate status hourly
  5. Implement fix (or rollback)
  6. Verify resolution
  7. Schedule post-mortem (P1/P2 only)
  
  ## Post-Mortem Template
  1. What happened?
  2. Timeline (when did we notice, when resolved?)
  3. Root cause
  4. Impact (users affected, data lost?)
  5. Prevention (how to avoid?)
  6. Action items (who, by when?)
  ```

- [ ] Create on-call rotation (email: on-call@example.com)
  ```
  Week 1: engineer-a@example.com
  Week 2: engineer-b@example.com
  Week 3: engineer-c@example.com
  ```

- [ ] Create incident runbook (common failures)
  ```
  ## Strangler Analyzer Timeout
  Symptom: /strangler-analyze hangs on large codebases
  Debug: ps aux | grep analyze_codebase
  Fix: Kill process, increase timeout, retry
  
  ## Database Migration Failure
  Symptom: Extraction fails during data migration
  Debug: Check migration logs
  Fix: Rollback via backup, investigate schema diff
  
  ## Proxy Router Misconfig
  Symptom: Old code not routing to new service
  Debug: Check proxy logs
  Fix: Validate routing rules, re-deploy proxy
  ```

---

### 4. Performance & Scalability Testing

**What's Missing:**
```
Current State:
  - No load testing
  - No performance baselines
  - No bottleneck identification
  - No monitoring during tests

What Should Exist:
  - Load test plan (1k, 10k, 100k LOC)
  - Performance benchmarks documented
  - Bottleneck identified + fixed
  - Monitoring during tests (CPU, memory, time)
  - Optimization checklist
```

**Action Items:**
- [ ] Create `PERFORMANCE_BASELINE.md`
  ```
  ## Analyzer Performance
  
  Codebase Size  | Time    | Memory  | Status
  10k LOC        | 2s      | 50MB    | ✅
  100k LOC       | 15s     | 200MB   | ✅
  500k LOC       | 90s     | 800MB   | ✅
  1M LOC         | 300s    | 2GB     | ⚠️ (timeout)
  
  ## Extraction Performance
  
  Feature Size   | Time    | Generated LOC
  Small (100 LOC) | 5s     | 500 LOC
  Medium (500)    | 15s    | 2k LOC
  Large (2k)      | 45s    | 5k LOC
  ```

- [ ] Create `.github/workflows/performance.yml`
  ```yaml
  on: [push]
  jobs:
    load_test:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v3
        - run: |
            # Test on 500k LOC fixture
            time python scripts/analyze_codebase.py @./test_contexts/django_large
            # Assert: < 120 seconds
        - run: |
            # Test on 1M LOC
            time python scripts/analyze_codebase.py @./test_contexts/django_xlarge
            # Assert: < 300 seconds, memory < 2GB
  ```

- [ ] Create performance optimization checklist
  ```
  - [ ] Profile code (where is time spent?)
  - [ ] Identify bottlenecks (parsing, analysis, generation?)
  - [ ] Implement caching (memoize expensive functions)
  - [ ] Optimize algorithms (reduce redundant analysis)
  - [ ] Parallel processing (if applicable)
  - [ ] Verify improvement (before/after benchmarks)
  ```

---

### 5. Security Testing & Audits

**What's Missing:**
```
Current State:
  - Basic input validation
  - No automated security scanning
  - No penetration testing
  - No dependency vulnerability checks
  - No secret scanning

What Should Exist:
  - SAST (Static Application Security Testing)
  - Dependency scanning (pip audit)
  - Secret scanning (git-secrets)
  - DAST (Dynamic testing)
  - Annual penetration test (for enterprise)
```

**Action Items:**
- [ ] Add `.github/workflows/security.yml`
  ```yaml
  on: [push, pull_request]
  jobs:
    sast:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v3
        - run: pip install bandit semgrep
        - run: bandit -r scripts/ skills/
        - run: semgrep --config=p/security-audit scripts/
    deps:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v3
        - run: pip install pip-audit
        - run: pip-audit  # Check for known vulns
    secrets:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v3
          with: { fetch-depth: 0 }
        - run: pip install detect-secrets
        - run: detect-secrets scan
  ```

- [ ] Create `SECURITY.md`
  ```
  ## Security Considerations
  
  ### Input Validation
  - All file paths validated (no directory traversal)
  - All JSON/YAML parsed with safe loaders
  - All user input sanitized before execution
  
  ### Secret Handling
  - Never log API keys (env vars only)
  - Never commit secrets (git-secrets enforced)
  - Rotate secrets quarterly (in docs)
  
  ### Code Execution
  - Never eval() user input
  - Subprocess calls with shell=False
  - Timeout on all external calls
  
  ### Reporting Security Issues
  - Email: security@example.com
  - Response: 48h
  - Timeline: Fix + test + release in 30 days
  ```

---

### 6. Metrics & Analytics

**What's Missing:**
```
Current State:
  - No usage tracking
  - No success metrics
  - No adoption metrics
  - No feature usage

What Should Exist:
  - Usage analytics (how often used?)
  - Success metrics (% of extractions successful?)
  - Performance metrics (extraction time distribution)
  - Feature adoption (which commands used most?)
  - User satisfaction (NPS, feedback)
```

**Action Items:**
- [ ] Add telemetry to base_script.py
  ```python
  class Telemetry:
      """Track plugin usage for analytics"""
      
      def track_command(self, command, success, duration):
          """Log command execution"""
          # Send to analytics service (Segment, Mixpanel)
          event = {
              "command": command,
              "success": success,
              "duration_seconds": duration,
              "timestamp": datetime.utcnow().isoformat(),
              "user_id": os.environ.get("ANTHROPIC_USER_ID"),
          }
          # Post to /analytics endpoint
  ```

- [ ] Create `METRICS.md` (public)
  ```
  ## Success Metrics (v1.0 Goals)
  
  - 50+ enterprises using strangler by Q4 2026
  - 500+ successful extractions completed
  - 95% extraction success rate (no data loss)
  - Average extraction time: 2 days → 4 hours
  - Customer satisfaction: 4.5/5.0 NPS
  ```

---

## PART 2: ANTHROPIC PLUGIN COMPLIANCE GAPS

### 1. Plugin Manifest (plugin.json)

**Current State:** ✅ Basic manifest exists

**Missing Fields/Validations:**
```json
{
  "name": "one-shot-prompting",
  "version": "0.6.0",
  "description": "...",
  
  // MISSING: Metadata for marketplace
  "author": "...",           // ❌ MISSING
  "license": "MIT",          // ❌ MISSING or unclear
  "repository": "...",       // ❌ MISSING
  "homepage": "...",         // ❌ MISSING
  "documentation": "...",    // ❌ MISSING
  
  // MISSING: Security & permissions
  "permissions": ["file-read", "file-write"],  // ❌ Not specified
  "trustedAuthors": [],      // ❌ Not specified
  
  // MISSING: Categories & tags
  "categories": ["code-generation", "backend"],  // ❌ Not specified
  "tags": ["api", "microservices"],  // ❌ Not specified
}
```

**Action Items:**
- [ ] Update `plugin.json` with complete metadata
  ```json
  {
    "name": "one-shot-prompting",
    "version": "1.0.0",
    "description": "Enterprise legacy modernization specialist. Extract microservices from monoliths safely.",
    "author": "One-Shot Prompting Team",
    "license": "MIT",
    "repository": "https://github.com/...",
    "homepage": "https://one-shot-prompting.com",
    "documentation": "https://github.com/one-shot-prompting/docs",
    "permissions": [
      "file-read:project-files",
      "file-write:generated-code",
      "network:external-apis",
      "environment-variables"
    ],
    "commands": [
      "/one-shot-prompting:one-shot-generator",
      "/one-shot-prompting:strangler-analyze",
      "/one-shot-prompting:strangler-extract",
      "/one-shot-prompting:strangler-validate",
      "/one-shot-prompting:strangler-roadmap"
    ],
    "categories": ["code-generation", "backend", "architecture"],
    "tags": ["microservices", "legacy-modernization", "event-driven", "strangler-pattern"],
    "requirements": {
      "claude-version": "3.5+",
      "python": "3.8+"
    }
  }
  ```

---

### 2. Command Documentation Completeness

**Current State:** 🟡 Commands documented, but strangler commands missing

**Missing Strangler Commands:**
```
/one-shot-prompting:strangler-analyze     ❌ Not documented
/one-shot-prompting:strangler-extract     ❌ Not documented
/one-shot-prompting:strangler-validate    ❌ Not documented
/one-shot-prompting:strangler-roadmap     ❌ Not documented
```

**Action Items:**
- [ ] Create `commands/strangler-analyze.md`
  ```
  # /strangler-analyze — Identify Extraction Candidates
  
  **Purpose:** Analyze a monolith, identify which features can be extracted
  
  **Syntax:**
  ```
  /one-shot-prompting:strangler-analyze @./path/to/monolith
  ```
  
  **Output:**
  - List of extractable features
  - Extraction difficulty (RED/YELLOW/GREEN)
  - Suggested extraction order
  - Risk assessment per feature
  
  **Example:**
  ```
  /strangler-analyze @./django-ecommerce
  
  # Output
  Extraction Candidates (ranked by ease):
  
  1. Payment Service (Score: 9/10, Risk: GREEN)
     - Coupling: 5% external
     - Tables: payments, transactions, payment_methods
     - Est. Time: 2-4 days
  
  2. Notification Service (Score: 8/10, Risk: YELLOW)
     - Coupling: 20% external
     - Tables: notifications, notification_templates
     - Est. Time: 3-5 days
  ```
  ```

- [ ] Create `commands/strangler-extract.md`
- [ ] Create `commands/strangler-validate.md`
- [ ] Create `commands/strangler-roadmap.md`

---

### 3. Error Messages & User Experience

**Current State:** 🟡 Basic error handling

**Missing User Experience:**
```
Current:
  ERROR: File not found
  
Better (Anthropic style):
  ❌ Could not analyze codebase
  
  Path '/path/to/code' not found
  
  💡 Try:
    1. Check path is correct
    2. Ensure you have read permission
    3. Run: /help for more info
```

**Action Items:**
- [ ] Update error messages (follow Anthropic CLI style)
  ```python
  # Before
  if not os.path.exists(path):
      print(f"ERROR: {path} not found")
  
  # After
  if not os.path.exists(path):
      error(f"Could not analyze codebase", [
          f"Path '{path}' not found or not readable",
          "",
          "💡 Suggestions:",
          f"  1. Check the path is correct",
          f"  2. Ensure you have read permission",
          f"  3. Use absolute paths: /full/path/to/code",
      ])
  ```

- [ ] Add recovery suggestions for common errors
  - File not found → check path, permissions
  - Timeout → codebase too large, try subset
  - Syntax error → unsupported language or version
  - Memory error → codebase too large for system

---

### 4. Help Text & Discoverability

**Current State:** 🟡 Help text exists, but could be better

**Missing:**
```
/help                        ❌ Not documented
/one-shot-prompting:help     ❌ Not documented
--help flag                  ❌ Not consistent
```

**Action Items:**
- [ ] Ensure all commands have --help
  ```bash
  /strangler-analyze --help
  
  # Output
  Analyze a monolith for extractable features
  
  USAGE:
    /strangler-analyze @path [OPTIONS]
  
  OPTIONS:
    --frameworks=django,spring,go
    --max-depth=5
    --min-coupling-score=0.7
    --dry-run
  
  EXAMPLES:
    /strangler-analyze @./my-project
    /strangler-analyze @./my-project --frameworks=django
  ```

- [ ] Create master help page
  ```
  /one-shot-prompting:help
  
  One-Shot Prompting — Enterprise Legacy Modernization
  
  MAIN COMMANDS:
    /one-shot-prompting:strangler-analyze    Identify extraction candidates
    /one-shot-prompting:strangler-extract    Generate microservice
    /one-shot-prompting:strangler-validate   Pre-flight safety checks
    /one-shot-prompting:strangler-roadmap    Full modernization plan
  
  LEARN MORE:
    /help strangler         → Strangler pattern tutorial
    /docs                   → Full documentation
    /examples               → Example extractions
  ```

---

### 5. Examples & Getting Started

**Current State:** 🟡 Examples exist, but not strangler-focused

**What's Missing:**
```
examples/
├── django-order-service/          ✅ Exists
├── fastapi-rate-limiter/          ✅ Exists
├── go-trading-bot/                ✅ Exists
├── nestjs-realtime-api/           ✅ Exists
├── spring-payment-service/        ✅ Exists
│
├── strangler-django-extract/      ❌ MISSING
├── strangler-spring-extract/      ❌ MISSING
└── strangler-go-extract/          ❌ MISSING
```

**Action Items:**
- [ ] Create `examples/strangler-django-extract/`
  - Django monolith with 400k LOC
  - Extraction of payment service
  - Before/after structure
  - README with step-by-step walkthrough

- [ ] Create `examples/strangler-spring-extract/`
  - Spring Boot monolith
  - Extraction of user service
  - Integration example

- [ ] Create `examples/strangler-go-extract/`
  - Go monolith
  - Extraction of inventory service

---

### 6. Version & Compatibility Management

**Current State:** 🟡 Version exists, but compatibility not tracked

**Missing:**
```
plugin.json:
  "version": "0.6.0",                  ✅ Exists
  "claude-version-required": "3.5+",   ❌ MISSING
  "python-version-required": "3.8+",   ❌ MISSING
  "breaking-changes": [],              ❌ MISSING
  
CHANGELOG.md:
  # v0.6.0
  - Feature A
  - Bug fix B
  - No compatibility info                ❌ MISSING
```

**Action Items:**
- [ ] Update plugin.json
  ```json
  {
    "version": "1.0.0",
    "compatibility": {
      "claude-version": "3.5+",
      "python": "3.8+",
      "os": ["linux", "macos", "windows"]
    }
  }
  ```

- [ ] Update CHANGELOG.md with breaking changes
  ```
  # v1.0.0 (2026-05-31)
  
  ## ✨ New Features
  - /strangler-analyze command
  - /strangler-extract command
  
  ## ⚠️ Breaking Changes
  - /one-shot-generator command signature changed
  - analyze_codebase.py output format changed
  
  ## 🔄 Migration Guide
  - [Link to migration docs]
  
  ## 🔗 Compatibility
  - Claude 3.5+
  - Python 3.8+
  ```

---

### 7. Security & Permissions

**Current State:** ❌ Not specified

**Missing:**
```
plugin.json:
  "permissions": [...]  ❌ MISSING DETAILS

Current behavior (implicit):
  - Can read any file on disk ✅
  - Can write to project directory ✅
  - Can call external APIs ✅
  - Can execute subprocesses ✅
  
What should be explicit:
  - Which files can be read? (only .py, .go, .rs?)
  - Which directories can be written? (only output/?)
  - Which APIs can be called? (only Stripe, GitHub?)
  - Which subprocess commands allowed? (only safe ones?)
```

**Action Items:**
- [ ] Document permissions
  ```json
  {
    "permissions": [
      {
        "id": "file-read:project",
        "description": "Read source files for analysis",
        "types": ["*.py", "*.go", "*.java", "*.ts", "*.rs"],
        "paths": ["project/**"]
      },
      {
        "id": "file-write:output",
        "description": "Write generated code",
        "paths": ["output/**", ".one-shot/**"]
      },
      {
        "id": "network:external-apis",
        "description": "Call external APIs (Stripe, GitHub, etc.)",
        "apis": ["api.stripe.com", "api.github.com", "api.openai.com"]
      },
      {
        "id": "subprocess:analysis",
        "description": "Run analysis scripts",
        "commands": ["python", "git"]
      }
    ]
  }
  ```

- [ ] Create `SECURITY.md` with permission model

---

### 8. Testing Requirements (Anthropic Standard)

**Current State:** 🟡 Tests exist, but coverage incomplete

**Anthropic Test Requirements:**
```
✅ Unit tests for core functions
🟡 Integration tests (partial)
❌ E2E tests for all commands
❌ Backwards compatibility tests
❌ Plugin interface tests
```

**Action Items:**
- [ ] Add `tests/test_plugin_interface.py`
  ```python
  def test_command_responds_to_help():
      """Verify all commands respond to --help"""
      result = run_command("strangler-analyze --help")
      assert "USAGE:" in result
      assert "OPTIONS:" in result
      assert "EXAMPLES:" in result
  
  def test_command_error_messaging():
      """Verify error messages follow Anthropic format"""
      result = run_command("strangler-analyze @/nonexistent")
      assert "❌" in result or "ERROR:" in result
      assert "💡" in result  # Suggestions
  ```

- [ ] Add `tests/test_backwards_compat.py`
  ```python
  def test_old_command_still_works():
      """Verify v0.6 commands still work in v1.0"""
      # Old command should work or show clear deprecation
  ```

---

## FINAL SUMMARY: What Blocks Marketplace Approval

### CRITICAL (Must fix for v1.0)
- [ ] `/strangler-analyze` + `/strangler-extract` implemented
- [ ] All tests passing
- [ ] Security review passed
- [ ] Error messages follow Anthropic style guide
- [ ] Help text complete for all commands
- [ ] Examples provided (strangler-specific)
- [ ] plugin.json complete & valid

### IMPORTANT (Should fix for v1.0)
- [ ] Backwards compatibility documented
- [ ] Breaking changes noted in CHANGELOG
- [ ] Release process automated
- [ ] Code review checklist in place
- [ ] Performance baselines documented
- [ ] Incident response process defined

### NICE-TO-HAVE (Can defer to v1.1)
- [ ] Security audit completed
- [ ] Load testing at scale
- [ ] Metrics/analytics integration
- [ ] On-call rotation established
- [ ] Post-mortem process defined

---

**Status:** Gap analysis complete  
**Confidence:** High (clear path to fix)  
**Timeline:** 4 weeks to Anthropic marketplace launch
