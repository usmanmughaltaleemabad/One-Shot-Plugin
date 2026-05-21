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
