#!/usr/bin/env bash
# Spring Boot post-write: lightweight check only (compilation needs Maven)
TOOL="$1"; INPUT=$(cat)
if [[ "$TOOL" == "Write" ]] || [[ "$TOOL" == "Edit" ]]; then
  FILE=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('file_path',''))" 2>/dev/null)
  if [[ "$FILE" =~ \.java$ ]]; then
    echo "INFO: $FILE written — run mvn test to validate" >&2
  fi
fi
exit 0
