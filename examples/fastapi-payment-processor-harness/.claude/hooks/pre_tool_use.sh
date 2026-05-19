#!/usr/bin/env bash
# Pre-tool guard for FastAPI harness.
# Blocks dangerous patterns before Bash or Write executes.

TOOL="$1"
INPUT=$(cat)

if [[ "$TOOL" == "Bash" ]]; then
  CMD=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('command',''))" 2>/dev/null)
  # Block destructive DB commands
  if echo "$CMD" | grep -qE 'DROP TABLE|TRUNCATE|DELETE FROM.*WHERE 1'; then
    echo "BLOCKED: destructive SQL requires manual confirmation" >&2
    exit 1
  fi
  # Block committing .env
  if echo "$CMD" | grep -qE 'git add.*\.env|git commit.*\.env'; then
    echo "BLOCKED: .env must not be committed" >&2
    exit 1
  fi
fi

exit 0
