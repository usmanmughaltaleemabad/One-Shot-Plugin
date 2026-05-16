#!/bin/bash
# SessionStart hook: inject context at session start

echo "=== PLUGIN SESSION START ==="

# Show open beads (active work)
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
    except: pass
" 2>/dev/null || echo "  [unable to parse beads]"
  else
    echo "No open beads (all work closed)."
  fi
else
  echo "No .beads/status.jsonl yet. Create it with: .beads/status.jsonl"
fi

# Show phase status (CRITICAL: real vs stub modules)
echo ""
echo "PHASE STATUS (Real vs Stub):"
if [ -f "docs/phase-status.md" ]; then
  grep -E "^\| \*\*[0-9]\*\*|^Total| Status" docs/phase-status.md | head -8
  echo ""
  echo "⚠️  Phase 4-5 are STUBS only (not implemented). See docs/phase-status.md."
else
  echo "  [docs/phase-status.md not found — run 'git pull' to update]"
fi

# Check CLAUDE.md size
if [ -f "CLAUDE.md" ]; then
  LINES=$(wc -l < CLAUDE.md)
  if [ "$LINES" -gt 100 ]; then
    echo "⚠️  CLAUDE.md has $LINES lines (target: <100). Trim before next session."
  fi
fi

echo "================================"

exit 0
