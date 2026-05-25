---
type: reference
last_verified: 2026-05-25
owner: claude
---

# Policy Engine — Phase 3-T1

Fine-grained agent access control, cost tracking, and budget gates for one-shot-prompting.

## Overview

The policy engine enables teams to:
- Define **profiles** (dev, ci, audit, etc.) with specific agents and budgets
- **Enforce cost limits** per generation and per month
- **Track actual spending** in `.beads/cost_ledger.jsonl`
- **Validate accuracy** against actual API costs (within 2%)
- **Resolve profiles** from CLI, environment variables, or config file

**Example usage:**
```bash
# Use 'ci' profile with tight budget
one-shot --profile ci "build shopping cart" @./project

# Monitor monthly spend
one-shot --report

# Check if cost would exceed budget before committing
one-shot --profile dev --budget=0.30 "add payments" @./project
```

## Architecture

### Components

1. **PolicySchema** (`policy_schema.py`): Dataclasses for profiles, budgets, roles
2. **ProfileManager** (`profile_manager.py`): Load profiles from CLI/env/file with fallback hierarchy
3. **CostTracker** (`cost_tracker.py`): Record costs, query monthly/lifetime totals, validate accuracy
4. **PolicyEngine** (`policy_schema.py`): Core logic for budget checks, cost tracking, profile merging

### Directory Structure

```
.claude/policies/
├── __init__.py              # Package exports
├── policy_schema.py         # PolicyProfile, PolicyEngine, BudgetConfig
├── profile_manager.py       # Load profiles from multiple sources
└── cost_tracker.py          # Cost ledger and reporting

examples/policies/
└── default.yaml             # Example config file

docs/governance/
└── policy-engine.md         # This file
```

## Profiles

A profile defines:
- **roles**: which agents are allowed (architect, implementer, test-author, reviewer, critic, wirer)
- **budgets**: cost limits per generation and per month
- **autonomy**: execution autonomy (none, low, high)
- **description**: human-readable purpose

### Built-in Profiles

| Profile | Roles | Per-Gen Budget | Monthly Budget | Autonomy | Use Case |
|---------|-------|---|---|---|---|
| **dev** | all 6 | $10 | $500 | high | Rapid iteration, full feature development |
| **ci** | implementer, reviewer | $2 | $100 | low | Automated PR generation, validation |
| **audit** | reviewer | $5 | $50 | none | Compliance, code review only |

### Custom Profiles

Define in `~/.claude/one-shot.policy.yml`:

```yaml
profiles:
  custom:
    roles:
      - architect
      - implementer
    budgets:
      cost_per_generation: 3.0
      cost_per_month: 150.0
    autonomy: low
    description: "Custom profile for my team"
```

## Profile Resolution (Priority Order)

Profiles are resolved with this hierarchy (highest to lowest):

1. **CLI argument**: `one-shot --profile ci <feature>`
2. **Environment variable**: `export OSP_PROFILE=audit`
3. **Config file**: `~/.claude/one-shot.policy.yml`
4. **Defaults**: `dev` (if nothing specified)

Example:
```bash
# Explicitly use 'ci' profile (overrides env or config)
one-shot --profile ci "feature" @./project

# Use profile from environment if set
export OSP_PROFILE=audit
one-shot "feature" @./project

# Use profile from config file
# (must be in ~/.claude/one-shot.policy.yml)
one-shot "feature" @./project
```

## Cost Tracking

### Ledger Format

Costs are recorded in `.beads/cost_ledger.jsonl` (JSONL = JSON Lines):

```json
{"date": "2026-05-25", "feature": "shopping cart", "cost_usd": 0.42, "model": "sonnet", "tokens": {"input": 5000, "output": 2000}, "profile": "dev", "generation_id": "gen-abc123"}
{"date": "2026-05-25", "feature": "user auth", "cost_usd": 0.38, "model": "haiku", "tokens": {"input": 3000, "output": 1500}, "profile": "ci", "generation_id": "gen-def456"}
```

### Recording Costs

In SKILL.md or agents, record costs after generation:

```python
from .claude.policies import CostTracker
from pathlib import Path

tracker = CostTracker(beads_dir=Path(".beads"))
tracker.record_cost(
    cost=0.42,
    feature="shopping cart",
    model="sonnet",
    tokens={"input": 5000, "output": 2000},
    profile="dev",
    generation_id="gen-001",
)
```

### Querying Costs

**Lifetime cost:**
```python
from .claude.policies import PolicyEngine

engine = PolicyEngine()
total = engine.get_lifetime_cost()
print(f"Total spend: ${total:.2f}")
```

**Monthly cost:**
```python
current_month = engine.get_monthly_cost()  # Current month
may_2026 = engine.get_monthly_cost("2026-05")
```

**Remaining monthly budget:**
```python
profile = engine.load_profile("dev")
remaining = engine.get_remaining_monthly_budget(profile)
if remaining < 10:
    print(f"Warning: Only ${remaining:.2f} left in monthly budget")
```

## Budget Gates

### Per-Generation Gate

Before starting a generation, check if estimated cost exceeds budget:

```python
from .claude.policies import PolicyProfile, BudgetConfig, PolicyEngine

profile = PolicyProfile(
    name="strict",
    budgets=BudgetConfig(cost_per_generation=0.50),
)

engine = PolicyEngine()
estimated_cost = 0.42

if not engine.check_budget(estimated_cost, profile):
    print(f"Cost ${estimated_cost} exceeds budget ${profile.budgets.cost_per_generation}")
    # Fall back to templated generation or ask user
```

### Monthly Budget Gate

After recording costs, check remaining monthly budget:

```python
remaining = engine.get_remaining_monthly_budget(profile)
if remaining < 0.10:
    print(f"Monthly budget exhausted. Remaining: ${remaining:.2f}")
    # Warn user or block further generations
```

## Accuracy Validation

Compare ledger against actual API costs recorded in `.beads/cost_observations.jsonl`:

```python
from .claude.policies import CostTracker
from pathlib import Path

tracker = CostTracker(beads_dir=Path(".beads"))
result = tracker.validate_accuracy(tolerance_pct=2.0)

if result["status"] == "valid":
    print(f"Ledger is accurate: {result['ledger_total']:.2f} vs {result['observations_total']:.2f}")
else:
    print(f"Drift detected: {result['deviation_pct']:.1f}% (tolerance: {result['tolerance_pct']}%)")
```

**Success criteria**: Accuracy within 2% of actual API spend.

## Usage Examples

### Example 1: Cost-Conscious Development

```bash
# Use 'lite' profile with $0.50/generation limit
one-shot --profile lite "build user model" @./project

# Monitor spend
one-shot --report
```

### Example 2: CI/CD Pipeline

```bash
# In GitHub Actions or similar
export OSP_PROFILE=ci
one-shot "implement service" @./project --apply
```

### Example 3: Compliance Audit

```bash
# Audit-only profile, no agent access
export OSP_PROFILE=audit
one-shot --review "check code quality" @./project
```

### Example 4: Team Dashboard

```python
# Generate monthly report for team
from .claude.policies import CostTracker

tracker = CostTracker(beads_dir=Path(".beads"))
report = tracker.get_monthly_report("2026-05")

print(f"May 2026 Spend: ${report['total_cost']:.2f}")
print(f"  by model: {report['by_model']}")
print(f"  by profile: {report['by_profile']}")
```

## Configuration

### Setting Up a Policy File

1. Create `~/.claude/one-shot.policy.yml`:
   ```bash
   cp examples/policies/default.yaml ~/.claude/one-shot.policy.yml
   ```

2. Edit to customize profiles:
   ```yaml
   profiles:
     myteam:
       roles: [architect, implementer, reviewer]
       budgets:
         cost_per_generation: 5.0
         cost_per_month: 200.0
       autonomy: high
       description: "My team's standard profile"
   ```

3. Use it:
   ```bash
   one-shot --profile myteam "feature" @./project
   ```

### Environment Variable Setup

```bash
# ~/.bashrc or ~/.zshrc
export OSP_PROFILE=ci

# Or in GitHub Actions:
# - name: Generate code
#   env:
#     OSP_PROFILE: ci
#   run: one-shot "feature" @./project
```

### Backward Compatibility

If no policy file exists, the engine **gracefully falls back** to defaults:
- Profile defaults to `dev`
- No cost limits enforced
- Costs still tracked (if ledger path is available)

This ensures existing code continues to work without changes.

## Testing

Run policy tests:

```bash
python -m pytest tests/test_policy_engine.py -v

# Expected: 47 tests pass
#   - BudgetConfig merging
#   - PolicyProfile merging and to_dict
#   - Default profiles existence
#   - PolicyEngine profile loading, budget checks, cost tracking
#   - ProfileManager resolution hierarchy
#   - CostTracker reports and validation
#   - Integration: full workflow, budget gates, monthly accumulation
```

## Integration with SKILL.md

The policy engine is used in SKILL.md's 1.5 stage (cost-budget gate):

```yaml
# Stage 1.5: Cost-Budget Gate
- name: "1.5 — cost-budget gate"
  description: "Check if estimated cost exceeds budget"
  agent: policy-engine (deterministic)
  inputs:
    - plan.json (from stage 1)
    - profile (from CLI or env)
  outputs:
    - proceed: true/false
    - remaining_budget: float
    - explanation: str
```

If cost exceeds budget:
- User is warned with remaining monthly budget
- Can proceed with `--apply` flag or fall back to templated generation with `--templated`

## FAQ

**Q: Can I use multiple profiles?**  
A: Yes, profiles can be merged. Use `--profile dev,ci` to merge (dev first, ci overrides).

**Q: What if the ledger gets corrupted?**  
A: Corrupted lines are skipped, valid lines are processed. The tracker is fault-tolerant.

**Q: How accurate is cost tracking?**  
A: Within 2% of actual API costs. Validated using `.beads/cost_observations.jsonl`.

**Q: What if I exceed budget?**  
A: The gate blocks the generation by default. Set `--budget=0` to skip the gate.

**Q: Can I reset monthly budget?**  
A: Monthly budget resets automatically on the first day of each month. Ledger is never deleted.

## Implementation Details

### Profile Merge Algorithm

Profiles are merged left-to-right with "override if non-empty" semantics:

```
merge([dev, ci]) →
  dev.name="dev" + ci.name="ci" → "ci" (ci wins)
  dev.roles=[architect, ...] + ci.roles=[implementer, ...] → [implementer, ...] (ci wins)
  dev.autonomy="high" + ci.autonomy="low" → "low" (ci wins)
  dev.budgets merge: both specified → ci wins
```

### Cost Calculation Accuracy

Costs are calculated as:
```
cost = (input_tokens / 1,000,000) * price_per_input_mtok +
       (output_tokens / 1,000,000) * price_per_output_mtok
```

Prices (as of mid-2026):
| Model | Input | Output |
|-------|-------|--------|
| Haiku | $0.80/Mtok | $4.00/Mtok |
| Sonnet | $3.00/Mtok | $15.00/Mtok |
| Opus | $15.00/Mtok | $75.00/Mtok |

### Ledger Consistency

The ledger is append-only (JSONL format) for durability:
- Each entry is a complete JSON object
- Entries are timestamped (date, not datetime)
- No transactions or rollbacks
- Safe for concurrent reads/writes (OS-level file locking)

## Future Enhancements

1. **Team dashboards**: Upload ledger to server for team-wide reporting
2. **Forecasting**: Predict monthly spend based on velocity
3. **Alerts**: Email/Slack notifications when approaching budget
4. **Custom cost models**: Support for non-Anthropic models (OpenAI, etc.)
5. **Profiles as code**: Generate profiles programmatically (CI/CD)

---

**Last updated:** 2026-05-25  
**Status:** Phase 3-T1 Complete  
**Tests:** 47/47 passing
