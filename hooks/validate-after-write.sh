#!/bin/bash
# PostToolUse hook: validate files after writes
# Reads tool event JSON from stdin per Claude Code hook protocol.

INPUT=$(cat)
FILEPATH=$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('tool_response',{}).get('file_path', d.get('tool_input',{}).get('file_path','')))" 2>/dev/null)

# Syntax-check Python files
if echo "$FILEPATH" | grep -qE "\.py$"; then
  if ! python3 -m py_compile "$FILEPATH" 2>/tmp/osp-syntax-error; then
    echo "ERROR: Python syntax error in $FILEPATH:" >&2
    cat /tmp/osp-syntax-error >&2
    exit 2
  fi
fi

# Check YAML frontmatter on markdown docs (except CLAUDE.md)
if echo "$FILEPATH" | grep -qE "\.md$" && ! echo "$FILEPATH" | grep -qE "CLAUDE\.md$"; then
  if ! head -1 "$FILEPATH" | grep -q "^---"; then
    echo "WARNING: $FILEPATH is missing YAML frontmatter (---). Add type/last_verified/owner." >&2
  fi
fi

# Check shell scripts have shebang
if echo "$FILEPATH" | grep -qE "\.sh$"; then
  if ! head -1 "$FILEPATH" | grep -q "^#!/"; then
    echo "WARNING: $FILEPATH is missing shebang (#!/bin/bash). Add it at line 1." >&2
  fi
fi

exit 0
