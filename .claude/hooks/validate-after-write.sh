#!/bin/bash
# PostToolUse hook: validate writes

FILEPATH=$(echo "$CLAUDE_TOOL_OUTPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('file_path',''))" 2>/dev/null)

# Syntax check Python files
if echo "$FILEPATH" | grep -qE "\.py$"; then
  if ! python3 -m py_compile "$FILEPATH" 2>/tmp/syntax-error; then
    echo "ERROR: Python syntax error in $FILEPATH:" >&2
    cat /tmp/syntax-error >&2
    exit 2
  fi
fi

# Check for YAML frontmatter on markdown docs (except CLAUDE.md)
if echo "$FILEPATH" | grep -qE "\.md$" && ! echo "$FILEPATH" | grep -qE "CLAUDE\.md$"; then
  if ! head -5 "$FILEPATH" | grep -q "^---"; then
    echo "WARNING: $FILEPATH is missing YAML frontmatter. Add: ---\ntype: reference|runbook|investigation|plan|router\nlast_verified: YYYY-MM-DD\nowner: your-name\n---" >&2
  fi
fi

# Check shell scripts have shebang
if echo "$FILEPATH" | grep -qE "\.sh$"; then
  if ! head -1 "$FILEPATH" | grep -q "^#!/"; then
    echo "WARNING: $FILEPATH is missing shebang (#!/bin/bash). Add it at line 1." >&2
  fi
fi

exit 0
