#!/bin/bash
# Stop hook: session-end checks

echo "=== PLUGIN SESSION END CHECK ==="

# Check for unclosed beads
if [ -f ".beads/status.jsonl" ]; then
  OPEN_COUNT=$(grep -c '"status":"open"' .beads/status.jsonl 2>/dev/null || echo 0)
  if [ "$OPEN_COUNT" -gt 0 ]; then
    echo "REMINDER: $OPEN_COUNT open bead(s). Update status if work is done."
    echo ""
    grep '"status":"open"' .beads/status.jsonl | python3 -c "
import json,sys
for line in sys.stdin:
    try:
        d = json.loads(line)
        print(f\"  • {d.get('id','?')}: {d.get('title','?')}\")
    except: pass
" 2>/dev/null
  fi
fi

# Check for unstaged changes
echo ""
echo "UNSTAGED CHANGES:"
if ! git diff --quiet 2>/dev/null; then
  UNSTAGED=$(git diff --stat 2>/dev/null | tail -1)
  echo "  $UNSTAGED"
  echo "  Run 'git add .' and 'git commit' before closing."
else
  echo "  None (working tree clean)."
fi

# Check for untracked files
UNTRACKED=$(git ls-files --others --exclude-standard 2>/dev/null | wc -l)
if [ "$UNTRACKED" -gt 0 ]; then
  echo "  $UNTRACKED untracked file(s). Run 'git status' to see them."
fi

echo ""
echo "============================"

exit 0
