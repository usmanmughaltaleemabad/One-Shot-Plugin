#!/bin/bash
# PreToolUse hook: guard dangerous file writes
# Reads tool event JSON from stdin per Claude Code hook protocol.

INPUT=$(cat)
FILEPATH=$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))" 2>/dev/null)

# Warn if writing to CLAUDE.md and it would exceed 100 lines
if echo "$FILEPATH" | grep -qE "CLAUDE\.md$"; then
  LINES=$(wc -l < "$FILEPATH" 2>/dev/null || echo 0)
  if [ "$LINES" -gt 100 ]; then
    echo "WARNING: CLAUDE.md is $LINES lines (target: <=100). Move content to docs/ or skills/CLAUDE.md." >&2
  fi
fi

# Warn (but don't block) if writing to .env
if echo "$FILEPATH" | grep -qE "^\.env$|/\.env$"; then
  echo "WARNING: Writing to .env. Verify you are not overwriting existing credentials." >&2
fi

# Block writing SKILL.md if size would exceed 2000 lines
if echo "$FILEPATH" | grep -qE "SKILL\.md$"; then
  if [ -f "$FILEPATH" ]; then
    LINES=$(wc -l < "$FILEPATH")
    if [ "$LINES" -gt 2000 ]; then
      echo "ERROR: SKILL.md would exceed 2000 lines ($LINES). Split into sub-skills first." >&2
      exit 2
    fi
  fi
fi

exit 0
