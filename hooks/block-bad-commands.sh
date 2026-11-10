#!/bin/bash
# PreToolUse hook: block dangerous bash commands
#
# Claude Code hooks receive event JSON on stdin (not via $CLAUDE_TOOL_INPUT).
# Reference: https://docs.anthropic.com/en/docs/claude-code/hooks

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null)

# Block FUTURE_PLAN.md commit (local-only file, should never be pushed)
if echo "$COMMAND" | grep -qE "git\s+(add|commit).*FUTURE_PLAN"; then
  echo "ERROR: FUTURE_PLAN.md is local only (gitignored). Do not commit it." >&2
  exit 2
fi

# Block git commit if plugin.json version doesn't match CHANGELOG
if echo "$COMMAND" | grep -qE "git\s+commit"; then
  PLUGIN_VERSION=$(grep -o '"version"\s*:\s*"[^"]*"' "${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json" 2>/dev/null | cut -d'"' -f4)
  CHANGELOG_VERSION=$(head -5 "${CLAUDE_PLUGIN_ROOT}/CHANGELOG.md" 2>/dev/null | grep -o "v[0-9.]*" | head -1)

  if [ -n "$PLUGIN_VERSION" ] && [ -n "$CHANGELOG_VERSION" ]; then
    if [ "$PLUGIN_VERSION" != "${CHANGELOG_VERSION#v}" ]; then
      echo "ERROR: plugin.json version ($PLUGIN_VERSION) != CHANGELOG.md version (${CHANGELOG_VERSION#v}). Bump one before committing." >&2
      exit 2
    fi
  fi
fi

# Block committing .env or secrets.
# The group keeps "credentials" and "secret" tied to git add/commit; without it,
# alternation precedence blocked any command that merely mentioned those words.
if echo "$COMMAND" | grep -qE "git\s+(add|commit).*(\.env|credentials|secret)"; then
  echo "ERROR: Do not commit .env files or credentials. These must be local-only." >&2
  exit 2
fi

# Block force push to main.
# Inspect each `git push ...` segment on its own (up to ; & |) so text in later
# chained commands (e.g. `gh pr create --base main`) is ignored, and require a
# real force flag (--force, --force-with-lease, -f, combined short flags like
# -uf) or a +refspec, rather than any "-f" substring such as "-form" or "-fix".
while IFS= read -r PUSH_SEGMENT; do
  FORCED=0
  TO_MAIN=0
  echo "$PUSH_SEGMENT" | grep -qE "(^|\s)(--force(-with-lease)?(=\S*)?|-[A-Za-z]*f[A-Za-z]*)(\s|$)" && FORCED=1
  echo "$PUSH_SEGMENT" | grep -qE "\s\+\S*main(\s|$)" && FORCED=1
  echo "$PUSH_SEGMENT" | grep -qE "(\s|:|\+)main(\s|$)" && TO_MAIN=1
  if [ "$FORCED" = 1 ] && [ "$TO_MAIN" = 1 ]; then
    echo "ERROR: Force push to main is blocked. Use a PR or ask repo owner." >&2
    exit 2
  fi
done < <(echo "$COMMAND" | grep -oE "git\s+push[^;&|]*")

exit 0
