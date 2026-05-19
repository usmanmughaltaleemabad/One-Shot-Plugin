#!/usr/bin/env bash
TOOL="$1"
INPUT=$(cat)

if [[ "$TOOL" == "Write" ]] || [[ "$TOOL" == "Edit" ]]; then
  FILE=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('file_path',''))" 2>/dev/null)
  if [[ "$FILE" =~ \.py$ ]] && [ -f "$FILE" ]; then
    if ! python3 -m py_compile "$FILE" 2>/dev/null; then
      echo "WARNING: $FILE has a syntax error" >&2
    fi
  fi
fi
exit 0
