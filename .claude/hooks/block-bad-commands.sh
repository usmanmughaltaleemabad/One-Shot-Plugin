#!/bin/bash
# PreToolUse hook: block dangerous bash commands

COMMAND=$(echo "$CLAUDE_TOOL_INPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('command',''))" 2>/dev/null)

# Block FUTURE_PLAN.md commit (local-only file, should never be pushed)
if echo "$COMMAND" | grep -qE "git\s+(add|commit).*FUTURE_PLAN"; then
  echo "ERROR: FUTURE_PLAN.md is local only (gitignored). Do not commit it." >&2
  exit 2
fi

# Block git commit if plugin.json version doesn't match CHANGELOG
if echo "$COMMAND" | grep -qE "git\s+commit"; then
  PLUGIN_VERSION=$(grep -o '"version"\s*:\s*"[^"]*"' .claude-plugin/plugin.json 2>/dev/null | cut -d'"' -f4)
  CHANGELOG_VERSION=$(head -5 CHANGELOG.md 2>/dev/null | grep -o "v[0-9.]*" | head -1)

  if [ -n "$PLUGIN_VERSION" ] && [ -n "$CHANGELOG_VERSION" ]; then
    if [ "$PLUGIN_VERSION" != "${CHANGELOG_VERSION#v}" ]; then
      echo "ERROR: plugin.json version ($PLUGIN_VERSION) ≠ CHANGELOG.md version (${CHANGELOG_VERSION#v}). Bump one before committing." >&2
      exit 2
    fi
  fi
fi

# Block committing .env or secrets
if echo "$COMMAND" | grep -qE "git\s+(add|commit).*\.env|credentials|secret"; then
  echo "ERROR: Do not commit .env files or credentials. These must be local-only." >&2
  exit 2
fi

# Block force push to main
if echo "$COMMAND" | grep -qE "git\s+push.*--force.*main|git\s+push.*-f.*main"; then
  echo "ERROR: Force push to main is blocked. Use a PR or ask repo owner." >&2
  exit 2
fi

exit 0
