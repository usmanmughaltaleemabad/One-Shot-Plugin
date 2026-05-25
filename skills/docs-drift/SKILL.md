---
type: skill
name: docs-drift
description: Detect codebase changes and auto-generate documentation updates
trigger: manual or scheduled
tools: Task, Read, Write
model: haiku
---

# Docs Drift — Automatic Documentation Updates

Scan your codebase for entity changes (added/removed/modified classes and functions) and automatically generate documentation updates. Proposes changes as drafts for human review before committing.

## Usage

```bash
/docs-drift @./my-project
```

## Pipeline

1. **Scan** — Extract class/function definitions via AST parser
2. **Compare** — Check against `.beads/docs-state.json` (last stored state)
3. **Detect** — If changes found, dispatch docs-author agent → draft to `.tmp/docs-author-drafts/`
4. **Review** — User approves drafts, then auto-commit to git

**No changes:** Reports "✓ No changes detected. Docs are up to date."

**Output:** Drafts in `.tmp/docs-author-drafts/`:
- `entities-[timestamp].md` — Entity documentation updates
- `api-[timestamp].md` — API documentation changes
- `schema-[timestamp].md` — ER diagram and schema changes

---

```!
import subprocess
import json
from pathlib import Path
import sys
from datetime import datetime

# Get project root from @. argument
project_root = Path(sys.argv[-1] if sys.argv[-1] != "@." else ".")
beads_dir = project_root / ".beads"
beads_dir.mkdir(exist_ok=True)
docs_state_path = beads_dir / "docs-state.json"

# Load current codebase state
codebase_scan_result = subprocess.run(
    [sys.executable, "scripts/codebase_diff.py", str(project_root)],
    capture_output=True,
    text=True,
)
if codebase_scan_result.returncode != 0:
    print(f"[Error] Failed to scan codebase: {codebase_scan_result.stderr}")
    sys.exit(1)

current_state = json.loads(codebase_scan_result.stdout)

# Load previous state
if docs_state_path.exists():
    previous_state = json.loads(docs_state_path.read_text())
else:
    previous_state = {}

# Detect changes
from scripts.codebase_diff import detect_changes
changes = detect_changes(previous_state, current_state)

# Check if any changes
total_changes = sum(len(v) for v in changes.values() if isinstance(v, list))

if total_changes == 0:
    print("[Docs Drift] ✓ No changes detected. Docs are up to date.")
else:
    print(f"[Docs Drift] Detected: {total_changes} changes")
    print(f"  - {len(changes['added_classes'])} added classes")
    print(f"  - {len(changes['removed_classes'])} removed classes")
    print(f"  - {len(changes['added_functions'])} added functions")

    # Create draft directory
    drafts_dir = project_root / ".tmp" / "docs-author-drafts"
    drafts_dir.mkdir(parents=True, exist_ok=True)

    # Dispatch docs-author agent via Task tool
    agent_input = {
        "changes": changes,
        "codebase_root": str(project_root),
        "docs_root": str(project_root / "docs"),
        "files_touched": list(current_state.keys())
    }
    print(f"[Docs Drift] Dispatching docs-author agent...")
    # Task tool invocation: agent="docs-author", input=agent_input
    # The skill framework will use Task tool to dispatch the agent
    # with the structured input containing change detection results

    # Save updated state
    docs_state_path.write_text(json.dumps(current_state, indent=2))
    print(f"[Docs Drift] Drafts written to: {drafts_dir}")
    print(f"[Docs Drift] Files ready for review.")
```
