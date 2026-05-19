#!/usr/bin/env bash
TOOL="$1"; INPUT=$(cat)
if [[ "$TOOL" == "Write" ]] || [[ "$TOOL" == "Edit" ]]; then
  FILE=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('file_path',''))" 2>/dev/null)
  if [[ "$FILE" =~ \.(ts|js)$ ]] && command -v npx &>/dev/null; then
    npx tsc --noEmit 2>/dev/null || echo "WARNING: TypeScript errors detected in $FILE" >&2
  fi
fi
exit 0
