#!/usr/bin/env bash
TOOL="$1"; INPUT=$(cat)
if [[ "$TOOL" == "Write" ]] || [[ "$TOOL" == "Edit" ]]; then
  FILE=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('file_path',''))" 2>/dev/null)
  if [[ "$FILE" =~ \.go$ ]] && command -v gofmt &>/dev/null; then
    gofmt -l "$FILE" 2>/dev/null | grep -q . && echo "WARNING: $FILE needs gofmt" >&2
  fi
fi
exit 0
