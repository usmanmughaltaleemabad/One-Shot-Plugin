#!/bin/bash
# PreToolUse hook: block dangerous bash commands
#
# Claude Code hooks receive event JSON on stdin (not via $CLAUDE_TOOL_INPUT).
# Reference: https://docs.anthropic.com/en/docs/claude-code/hooks

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('command',''))" 2>/dev/null)

block() {
  echo "$1" >&2
  exit 2
}

# Block FUTURE_PLAN.md commit (local-only file, should never be pushed)
if echo "$COMMAND" | grep -qE "git\s+(add|commit).*FUTURE_PLAN"; then
  block "ERROR: FUTURE_PLAN.md is local only (gitignored). Do not commit it."
fi

# Block git commit if plugin.json version doesn't match CHANGELOG
if echo "$COMMAND" | grep -qE "git\s+commit"; then
  PLUGIN_VERSION=$(grep -o '"version"\s*:\s*"[^"]*"' "${CLAUDE_PLUGIN_ROOT}/.claude-plugin/plugin.json" 2>/dev/null | cut -d'"' -f4)
  CHANGELOG_VERSION=$(head -5 "${CLAUDE_PLUGIN_ROOT}/CHANGELOG.md" 2>/dev/null | grep -o "v[0-9.]*" | head -1)

  if [ -n "$PLUGIN_VERSION" ] && [ -n "$CHANGELOG_VERSION" ]; then
    if [ "$PLUGIN_VERSION" != "${CHANGELOG_VERSION#v}" ]; then
      block "ERROR: plugin.json version ($PLUGIN_VERSION) != CHANGELOG.md version (${CHANGELOG_VERSION#v}). Bump one before committing."
    fi
  fi
fi

# Keep explicit sensitive-path protection on git add/commit arguments. Ordinary
# prose about these topics is not itself evidence that a sensitive file is staged.
if echo "$COMMAND" | grep -qE "git\s+add.*\.env"; then
  block "ERROR: Do not stage or commit .env files. These must be local-only."
fi

# Inspect the actual index before a commit. This also catches secrets added by
# broad staging commands such as `git add .`, without rejecting commit-message prose.
if echo "$COMMAND" | grep -qE "git\s+commit"; then
  if git diff --cached --name-only -z -- 2>/dev/null | python3 -c 'import os,sys; paths=sys.stdin.buffer.read().split(b"\0"); bad=False
for raw in paths:
    name=os.path.basename(raw).lower()
    if name == b".env" or (name.startswith(b".env.") and name not in (b".env.example", b".env.sample", b".env.template")) or name in (b"credentials", b"credentials.json", b"service-account.json", b"id_rsa", b"id_ed25519") or name.endswith((b".pem",b".p12",b".pfx",b".key")):
        bad=True
sys.exit(0 if bad else 1)' ; then
    block "ERROR: Staged paths include a credential or private-key file. Remove it before committing."
  fi

  if git diff --cached --no-ext-diff --unified=0 -- 2>/dev/null | grep -E '^\+[^+]' | grep -qE '(AKIA[0-9A-Z]{16}|ASIA[0-9A-Z]{16}|-----BEGIN ([A-Z ]+ )?PRIVATE KEY-----|gh[pousr]_[A-Za-z0-9]{30,}|sk-[A-Za-z0-9]{24,}|Bearer[[:space:]]+[A-Za-z0-9._~+/-]{24,})'; then
    block "ERROR: Staged changes match a high-confidence credential pattern. Remove the sensitive value before committing."
  fi
fi

# Block force push to main
if echo "$COMMAND" | grep -qE "git\s+push.*--force.*main|git\s+push.*-f.*main"; then
  block "ERROR: Force push to main is blocked. Use a PR or ask repo owner."
fi

exit 0
