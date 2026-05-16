---
type: runbook
last_verified: 2026-05-16
owner: claude
---

# Skill Authoring Guide

How to write a SKILL.md file and its corresponding scripts.

---

## SKILL.md Structure

Every SKILL.md has this shape:

```markdown
---
name: skill-name
description: One line describing what it does
trigger: manual | auto | suggest
---

# Skill Name

One paragraph explaining the skill's purpose and typical use case.

## Core Workflow

Step-by-step what the skill does. Number the steps.

## ! Injection Block

```!
python "./scripts/my_script.py" "$ARGUMENTS"
```

The injected script output becomes part of the prompt context.

## Flags (Optional)

| Flag | Purpose | Example |
|------|---------|---------|
| `--verbose` | Print detailed output | `--verbose` |
| `--dry-run` | Don't apply changes | `--dry-run` |

## Examples

User input → Expected output

### Example 1
`/skill-name "add auth" @/django-project`
→ Plan with Django-specific auth strategy

## Known Issues

- Issue and workaround

## Self-Improvement Log
<!-- Session-end hook appends learnings here -->
```

---

## Script Guidelines

Scripts are invoked with `$ARGUMENTS` (the full user request).

### Requirements

- **Language**: Python (3.7+)
- **Dependencies**: stdlib only — no `pip install`
- **Argument parsing**: Use `sys.argv[1]` (shell passes `$ARGUMENTS` as one arg)
- **Output**: Plain text, < 500 tokens (injected into prompt)
- **Exit code**: 0 = success, 1 = error (exit 1 makes Claude see the error)

### Skeleton

```python
#!/usr/bin/env python3
"""
One-line description of what this script does.
"""
import sys
import json
import re
from pathlib import Path

def main():
    if len(sys.argv) < 2:
        print("ERROR: No arguments provided.", file=sys.stderr)
        sys.exit(1)
    
    user_request = sys.argv[1]
    
    # Parse the request, analyze, output findings
    try:
        # Your logic here
        result = f"Analysis: {user_request}"
        print(result)
        sys.exit(0)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### Common Patterns

**Parse @ argument (codebase path)**
```python
import re
match = re.search(r'@(/[^\s]+)', user_request)
codebase_path = match.group(1) if match else None
```

**Read a file and count lines**
```python
path = Path(codebase_path) / "models.py"
if path.exists():
    lines = path.read_text().count('\n')
    print(f"models.py: {lines} lines")
```

**Output JSON for Claude to parse**
```python
import json
data = {"frameworks": ["django", "fastapi"], "modules": 4}
print(json.dumps(data))
```

---

## Testing Your Script

**Locally (without SKILL.md invocation)**
```bash
python skills/my-skill/scripts/my_script.py "test request @/tmp/project"
```

**With all test_contexts/**
```bash
for ctx in test_contexts/*.txt; do
  echo "=== Testing with $(basename $ctx) ==="
  python scripts/my_script.py "test request @$ctx"
done
```

**Integration test**
```bash
python RUN_INTEGRATION_TESTS.py
```

---

## SKILL.md Line Limits

- Small skill (one generator): 100-200 lines
- Medium skill (multi-step): 300-500 lines
- Large skill (complex orchestration): up to 1000 lines

If > 1000 lines, split into sub-skills.

---

## Frontmatter Requirements

Every SKILL.md must have:
```yaml
---
name: kebab-case-name
description: One-line summary (< 80 chars)
trigger: manual | auto | suggest
---
```

**trigger values:**
- `manual` — invoke with `/skill-name`
- `auto` — load every session (used for core harness skills)
- `suggest` — Claude mentions it but doesn't load unless user confirms

---

## Validation Checklist

Before committing a SKILL.md + script:

- [ ] SKILL.md has YAML frontmatter with name, description, trigger
- [ ] SKILL.md < 1000 lines
- [ ] Script runs locally: `python script.py "test request @/path"`
- [ ] Script has no `import` statements except stdlib
- [ ] Script exits with 0 on success, 1 on error
- [ ] Script output < 500 tokens (inject `| head -50` if needed)
- [ ] Examples section shows real input → expected output
- [ ] Known Issues section documented (or empty with comment)
