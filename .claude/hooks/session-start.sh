#!/bin/bash
# SessionStart hook: inject minimal context at session start.
#
# This hook prints information that is useful to Claude inside an
# interactive session. It does NOT make claims about the codebase that
# could drift from reality (the prior version printed a hardcoded
# "Phase 4-5 are STUBS" warning that contradicted the README and was
# flagged by external audit). If you need to know which phases/modules
# are real, run `python -m pytest tests/` and look at the actual code.

echo "=== PLUGIN SESSION START ==="

# Show open beads (active work). Best-effort; failure is non-fatal.
if [ -f ".beads/status.jsonl" ]; then
  OPEN=$(grep '"status":"open"' .beads/status.jsonl 2>/dev/null | tail -5)
  if [ -n "$OPEN" ]; then
    echo "OPEN BEADS (active work):"
    echo "$OPEN" | python3 -c "
import json,sys
for line in sys.stdin:
    try:
        d = json.loads(line)
        print(f\"  [{d.get('priority','?').upper()}] {d.get('id','?')}: {d.get('title','?')}\")
    except Exception:
        pass
" 2>/dev/null || echo "  [unable to parse beads]"
  else
    echo "No open beads."
  fi
fi

# CLAUDE.md size policy: keep this file ≤100 lines so it loads cheaply.
if [ -f "CLAUDE.md" ]; then
  LINES=$(wc -l < CLAUDE.md)
  if [ "$LINES" -gt 100 ]; then
    echo "⚠️  CLAUDE.md has $LINES lines (target: ≤100). Trim before next session."
  fi
fi

echo "================================"

# Best-effort docs-drift check. Silent on success, advisory on failure.
if [ -f "scripts/codebase_diff.py" ]; then
    python3 scripts/codebase_diff.py . > .beads/docs-state.json 2>&1 || true
fi

exit 0
