---
type: reference
last_verified: 2026-05-16
owner: claude
---

# Metadata Contract

Frontmatter requirements for all documents.

---

## Minimum Required Frontmatter

Every markdown file (except CLAUDE.md) must have YAML frontmatter:

```yaml
---
type: router|runbook|reference|investigation|plan|changelog
last_verified: YYYY-MM-DD
owner: your-name
---
```

**Enforced by:** `.claude/hooks/validate-after-write.sh`

---

## Full Frontmatter (when relevant)

Use these fields when applicable:

```yaml
---
type: reference
last_verified: 2026-05-16
owner: claude
status: active
related_beads: ["bd-001", "bd-002"]
parent: docs/index.md
---
```

| Field | Required | When | Values |
|-------|----------|------|--------|
| `type` | ✅ | Always | router, runbook, reference, investigation, plan, changelog |
| `last_verified` | ✅ | Always | YYYY-MM-DD (ISO date) |
| `owner` | ✅ | Always | Name or "claude" |
| `status` | ⏳ | For investigation, plan | active, archived |
| `related_beads` | ⏳ | If doc created for specific beads | ["bd-001", "bd-002"] |
| `parent` | ⏳ | For L3 docs | Path to L2 router that links to it |

---

## Field Definitions

### type (required)

Document type. Controls line limits and load behavior.

See `.claude/standards/DOC_TYPE_SYSTEM.md` for full definitions.

```yaml
type: reference
```

---

### last_verified (required)

ISO date: YYYY-MM-DD. When the content was last checked for accuracy.

**Why:** Staleness detection. Hooks can warn if `last_verified` exceeds SLO.

```yaml
last_verified: 2026-05-16
```

**SLOs by type:**

| Type | Max staleness |
|------|---|
| router (L1, L2) | 1 month |
| runbook | 2 months |
| reference | 2 months |
| investigation | N/A (append "archived" when resolved) |
| plan | N/A (append "archived" when done) |
| changelog | No SLO (append-only) |

**When to update:** Fix a typo, clarify a step, add a note, change a tool version, etc. → bump `last_verified`.

---

### owner (required)

Person or agent responsible for keeping doc fresh.

```yaml
owner: claude
owner: sabeena
owner: haroon
```

**Why:** When a doc is stale, owner knows who to ping.

---

### status (for investigation, plan)

Document lifecycle state.

```yaml
status: active      # work in progress
status: archived    # completed, kept for reference
```

**Rules:**
- Only used for investigation and plan types
- Investigations: `active` while debugging, `archived` when issue resolved
- Plans: `active` while executing, `archived` when done
- Archive old investigations/plans quarterly (move to history/)

---

### related_beads (optional)

Which beads this doc was created to support.

```yaml
related_beads: ["bd-001", "bd-002"]
```

**Why:** Tie doc to work tracking. Helps understand "why was this doc written?"

---

### parent (for L3 docs)

The L2 router that links to this doc.

```yaml
parent: docs/index.md
parent: skills/CLAUDE.md
```

**Why:** Navigation. Helps find the doc's home directory.

---

## CLAUDE.md Exception

Root `CLAUDE.md` is special:
- Must have frontmatter with `type: router`
- Does NOT follow line limit (but should stay < 100 for practice)
- Is always loaded, so freshness is critical

```yaml
---
type: router
last_verified: 2026-05-16
owner: claude
---

# one-shot-prompting Plugin — Claude Operating Manual
```

---

## Enforcement

### Pre-commit hook (validate-after-write.sh)

Runs after every .md Write/Edit:

```bash
if ! head -5 "$FILE" | grep -q "^---"; then
  echo "ERROR: $FILE missing frontmatter"
  exit 2
fi
```

Blocks writes if frontmatter is missing.

### Smoke test (bash .claude/scripts/smoke-test.sh)

Validates all .md files:

```bash
# Check all docs have frontmatter
for f in docs/*.md; do
  head -5 "$f" | grep -q "^---" || echo "FAIL: $f missing frontmatter"
done
```

---

## Example: Creating a New Reference Doc

1. Create file:
   ```bash
   touch docs/new-reference.md
   ```

2. Add frontmatter:
   ```yaml
   ---
   type: reference
   last_verified: 2026-05-16
   owner: claude
   parent: docs/index.md
   ---

   # New Reference

   Content here...
   ```

3. Link from parent:
   ```markdown
   | [new-reference.md](new-reference.md) | What this doc answers |
   ```

4. Commit:
   ```bash
   git add docs/new-reference.md
   git commit -m "docs: Add new reference (type: reference, parent: docs/)"
   ```

---

## Staleness Detection (Future)

When implemented, this hook will run at session-start:

```python
from datetime import date, timedelta

def check_staleness(filepath, frontmatter):
    doc_type = frontmatter.get('type')
    last_verified = frontmatter.get('last_verified')
    
    slos = {
        'router': 30,
        'runbook': 60,
        'reference': 60,
        # others have no SLO
    }
    
    if doc_type in slos:
        days_old = (date.today() - parse_iso_date(last_verified)).days
        if days_old > slos[doc_type]:
            print(f"STALE: {filepath} ({days_old}d old, limit {slos[doc_type]}d)")
```

---

## Summary Checklist

Before committing a new .md file:

- [ ] File has YAML frontmatter with `type`, `last_verified`, `owner`
- [ ] `type` is one of: router, runbook, reference, investigation, plan, changelog
- [ ] `last_verified` is today's date in YYYY-MM-DD format
- [ ] `owner` is a name or "claude"
- [ ] For investigations/plans: `status` field included (active|archived)
- [ ] For L3 docs: `parent` field points to L2 router
- [ ] Line count matches doc type limit (see DOC_TYPE_SYSTEM.md)
- [ ] Smoke test passes: `bash .claude/scripts/smoke-test.sh`

Done!
