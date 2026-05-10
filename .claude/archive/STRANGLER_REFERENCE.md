# Strangler Commands Reference — v2.0.0

**Complete command syntax and options for strangler feature.**

---

## COMMAND SYNTAX

All strangler commands follow this pattern:

```
/one-shot-prompting:one-shot-generator [COMMAND] [OPTIONS] [FLAGS]
```

---

## COMMANDS

### 1. ANALYZE — Identify Extractable Features

**Syntax:**
```bash
/one-shot-prompting:one-shot-generator analyze monolith @/path/to/project [OPTIONS]
```

**Required:**
- `@/path/to/project` — Path to monolith source code

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--framework` | string | auto-detect | Force framework (django, fastapi, spring, go, nestjs) |
| `--json` | flag | false | Output JSON only (no markdown table) |
| `--markdown` | flag | false | Output markdown only (no JSON) |
| `--threshold` | int | 10 | Only show features with coupling score < threshold |
| `--min-size` | int | 2 | Minimum functions per feature |
| `--max-size` | int | 50 | Maximum functions per feature |
| `--timeout` | int | 30 | Timeout in seconds |
| `--verbose` | flag | false | Show detailed analysis output |

**Output:**

**Markdown table:**
```
| Feature | Modules | Coupling | Funcs | Difficulty | Score |
|---------|---------|----------|-------|------------|-------|
| payment |   3     |  5.2/10  |  8    | YELLOW     | 6/10  |
```

**JSON:**
```json
{
  "framework": "django",
  "feature_count": 7,
  "features": [
    {
      "name": "payment",
      "modules": ["payment_service", "payment_models"],
      "difficulty": "YELLOW",
      "score": 6,
      "external_coupling": 5.2
    }
  ]
}
```

**Examples:**

```bash
# Analyze Django project
/one-shot-prompting:one-shot-generator analyze monolith @/home/user/django-ecommerce

# Analyze with JSON output only
/one-shot-prompting:one-shot-generator analyze monolith @/home/user/django-ecommerce --json

# Analyze with lower coupling threshold (only loosely coupled features)
/one-shot-prompting:one-shot-generator analyze monolith @/app --threshold=3

# Analyze verbose mode (see what's happening)
/one-shot-prompting:one-shot-generator analyze monolith @/app --verbose
```

---

### 2. EXTRACT — Generate Microservice Code

**Syntax:**
```bash
/one-shot-prompting:one-shot-generator extract {FEATURE} --language {LANG} [OPTIONS]
```

**Required:**
- `{FEATURE}` — Feature name from analysis (e.g., "payment")
- `--language` — Target language (go or fastapi)

**Options:**

| Option | Type | Values | Default | Description |
|--------|------|--------|---------|-------------|
| `--language` | string | go, fastapi | go | Programming language for service |
| `--include-adapter` | flag | — | true | Generate legacy adapter (gradual routing) |
| `--include-k8s` | flag | — | true | Generate Kubernetes manifests |
| `--include-tests` | flag | — | true | Generate integration tests |
| `--include-migrations` | flag | — | true | Generate database migrations |
| `--database` | string | postgres, mysql, mongodb | postgres | Database system |
| `--output-dir` | string | — | ./generated | Output directory for files |

**Output:** 10-15 files ready to build and deploy

**Examples:**

```bash
# Extract as Go service
/one-shot-prompting:one-shot-generator extract payment --language go

# Extract as FastAPI service
/one-shot-prompting:one-shot-generator extract payment --language fastapi

# Extract without Kubernetes (local only)
/one-shot-prompting:one-shot-generator extract payment --language go --no-k8s

# Extract to specific directory
/one-shot-prompting:one-shot-generator extract payment --language go --output-dir=/tmp/payment-service
```

---

### 3. VALIDATE — Pre-Flight Safety Checks

**Syntax:**
```bash
/one-shot-prompting:one-shot-generator validate {SERVICE} [OPTIONS]
```

**Required:**
- `{SERVICE}` — Service directory to validate

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--dry-run` | flag | false | Don't modify anything, just report |
| `--strict` | flag | false | Fail on warnings (not just errors) |
| `--check-libs` | flag | true | Validate library compatibility |
| `--check-data` | flag | true | Validate migration safety |
| `--check-api` | flag | true | Validate API compatibility |
| `--check-config` | flag | true | Validate configuration |
| `--check-perf` | flag | true | Validate performance |

**Output:**

```
[VALIDATION COMPLETE] 5/5 categories PASS
- Library Compatibility: GREEN (3 warnings)
- Data Consistency: GREEN
- Interface Breaking: YELLOW (1 warning: missing error handler)
- Configuration: GREEN
- Performance: GREEN
```

**Examples:**

```bash
# Validate service before deployment
/one-shot-prompting:one-shot-generator validate ./generated-payment

# Dry-run validation (no changes)
/one-shot-prompting:one-shot-generator validate ./generated-payment --dry-run

# Strict mode (fail on warnings)
/one-shot-prompting:one-shot-generator validate ./generated-payment --strict
```

---

### 4. ROADMAP — Plan Extraction Timeline

**Syntax:**
```bash
/one-shot-prompting:one-shot-generator roadmap --from={ANALYSIS} [OPTIONS]
```

**Required:**
- `--from` — Path to analysis JSON or "latest"

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--duration` | string | 12-24 months | Plan duration |
| `--team-size` | int | 3 | Engineers available |
| `--prioritize` | string | difficulty | Sort by (difficulty, coupling, size) |
| `--currency` | string | USD | Currency for costs |
| `--hourly-rate` | int | 150 | Developer hourly rate |

**Output:**

```
[EXTRACTION ROADMAP] 12 months | 3 engineers

Phase 1 (Weeks 1-4): Extract 3 GREEN services
- auth (score 9/10)
- email (score 8/10)
- logging (score 9/10)
Effort: 4 weeks | Cost: $48,000 | ROI: Year 2

Phase 2 (Weeks 5-12): Extract 4 YELLOW services
...

Financial Analysis:
- Total Investment: $180,000
- Annual Payoff: $60,000 (reduced ops)
- ROI Timeline: 3 years
```

**Examples:**

```bash
# Generate roadmap from analysis
/one-shot-prompting:one-shot-generator roadmap --from=monolith-analysis.json

# Generate roadmap with custom team size
/one-shot-prompting:one-shot-generator roadmap --from=latest --team-size=5

# Generate roadmap with cost analysis
/one-shot-prompting:one-shot-generator roadmap --from=latest --hourly-rate=200
```

---

## FLAGS

Global flags that work with any command:

| Flag | Type | Description |
|------|------|-------------|
| `--strangler` | boolean | Enable strangler mode (auto-routed from /one-shot-prompting) |
| `--verbose` | boolean | Show detailed output |
| `--quiet` | boolean | Suppress output (JSON only) |
| `--format` | string | Output format (json, markdown, csv) |
| `--timeout` | int | Command timeout in seconds |

---

## EXIT CODES

| Code | Meaning | Example |
|------|---------|---------|
| 0 | Success | Analysis completed without errors |
| 1 | Error | Framework not detected, path invalid |
| 2 | Validation failed | Pre-flight checks failed (strict mode) |
| 3 | Timeout | Analysis took too long (>timeout) |
| 4 | Invalid argument | Unknown flag or missing required option |

---

## EXAMPLES BY SCENARIO

### Scenario: Complete Extraction Workflow

```bash
# 1. Analyze monolith
/one-shot-prompting:one-shot-generator analyze monolith @/app --json > analysis.json

# 2. Review analysis
cat analysis.json | grep difficulty

# 3. Extract first GREEN service
/one-shot-prompting:one-shot-generator extract auth --language go

# 4. Validate extracted service
/one-shot-prompting:one-shot-generator validate ./generated-auth --dry-run

# 5. Generate timeline
/one-shot-prompting:one-shot-generator roadmap --from=analysis.json

# 6. Deploy (if validation passes)
cd generated-auth && go build && kubectl apply -f k8s-deployment.yaml
```

### Scenario: Multiple Services

```bash
# Extract multiple services in sequence
for service in auth email logging; do
  /one-shot-prompting:one-shot-generator extract $service --language go
  /one-shot-prompting:one-shot-generator validate ./generated-$service --dry-run
done
```

### Scenario: CI/CD Integration

```bash
# In your CI pipeline:

# Analyze on every commit
/one-shot-prompting:one-shot-generator analyze monolith @. --json > /tmp/analysis.json

# Extract if explicitly triggered
if [ "$EXTRACT_SERVICE" != "" ]; then
  /one-shot-prompting:one-shot-generator extract $EXTRACT_SERVICE --language go
  
  # Validate before merge
  /one-shot-prompting:one-shot-generator validate ./generated-$EXTRACT_SERVICE --strict
  
  if [ $? -eq 0 ]; then
    echo "Validation passed, ready for PR"
  else
    echo "Validation failed, review issues"
    exit 1
  fi
fi
```

---

## COMMON PATTERNS

### Get features only (no markdown clutter)
```bash
/one-shot-prompting:one-shot-generator analyze @/app --json | jq '.features[] | {name, difficulty, score}'
```

### Extract all GREEN services automatically
```bash
/one-shot-prompting:one-shot-generator analyze @/app --json | \
  jq -r '.features[] | select(.difficulty == "GREEN") | .name' | \
  xargs -I {} /one-shot-prompting:one-shot-generator extract {} --language go
```

### Validate all generated services
```bash
for service in generated-*; do
  /one-shot-prompting:one-shot-generator validate ./$service || exit 1
done
echo "All services valid!"
```

---

## PERFORMANCE TIPS

- **Analysis:** ~0.34s for 2.5K LOC, scales O(n)
- **Extraction:** <1s for any service
- **Validation:** <2s for typical service
- **Roadmap:** <5s even for 100+ services

For very large codebases (100K+ LOC):
```bash
# Use timeout and verbose to debug slowness
/one-shot-prompting:one-shot-generator analyze @/app --timeout=60 --verbose
```

---

**Version:** 2.0.0  
**Last Updated:** May 10, 2026
