#!/usr/bin/env bash
TOOL="$1"; INPUT=$(cat)
if [[ "$TOOL" == "Bash" ]]; then
  CMD=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('command',''))" 2>/dev/null)
  if echo "$CMD" | grep -qE 'npm publish|rm -rf node_modules.*&&.*rm'; then
    echo "BLOCKED: potentially destructive npm command" >&2; exit 1
  fi
fi
exit 0
