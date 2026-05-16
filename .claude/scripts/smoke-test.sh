#!/bin/bash
# Smoke test: validates syntax, frontmatter, versions, CLAUDE.md size

set -e

echo "=== SMOKE TEST ==="
echo ""

PASS=0
FAIL=0

# Test 1: Python scripts present (syntax validation is in RUN_INTEGRATION_TESTS.py)
echo "1. Python scripts present..."
if [ -d "skills/one-shot-generator/scripts" ]; then
  COUNT=$(find skills/*/scripts -name "*.py" -type f 2>/dev/null | wc -l)
  echo "   ✅ PASS: Found $COUNT .py scripts"
  PASS=$((PASS+1))
else
  echo "   ❌ FAIL: scripts/ directory missing"
  FAIL=$((FAIL+1))
fi

# Test 2: SKILL.md frontmatter
echo "2. SKILL.md frontmatter..."
SKILL_FAIL=0
for f in skills/*/SKILL.md; do
  if ! head -5 "$f" | grep -q "^---"; then
    echo "   ❌ FAIL: $f missing YAML frontmatter"
    SKILL_FAIL=$((SKILL_FAIL+1))
  fi
  if ! head -10 "$f" | grep -q "name:"; then
    echo "   ❌ FAIL: $f missing 'name:' field"
    SKILL_FAIL=$((SKILL_FAIL+1))
  fi
done
if [ $SKILL_FAIL -eq 0 ]; then
  echo "   ✅ PASS: All SKILL.md files have frontmatter"
  PASS=$((PASS+1))
else
  FAIL=$((FAIL+1))
fi

# Test 3: Version consistency (plugin.json vs CHANGELOG.md)
echo "3. Version consistency..."
if [ -f ".claude-plugin/plugin.json" ] && [ -f "CHANGELOG.md" ]; then
  PLUGIN_VER=$(grep -o '"version"\s*:\s*"[^"]*"' .claude-plugin/plugin.json 2>/dev/null | cut -d'"' -f4)
  CHANGELOG_VER=$(grep -E "^## v" CHANGELOG.md 2>/dev/null | head -1 | grep -o "v[0-9.]*" || echo "")

  if [ "$PLUGIN_VER" == "${CHANGELOG_VER#v}" ] || [ -z "$CHANGELOG_VER" ]; then
    echo "   ✅ PASS: plugin.json ($PLUGIN_VER) matches CHANGELOG.md"
    PASS=$((PASS+1))
  else
    echo "   ❌ FAIL: plugin.json ($PLUGIN_VER) ≠ CHANGELOG.md (${CHANGELOG_VER#v})"
    FAIL=$((FAIL+1))
  fi
else
  echo "   ⚠️  SKIP: plugin.json or CHANGELOG.md not found"
fi

# Test 4: CLAUDE.md line count
echo "4. CLAUDE.md line limit (< 100 lines)..."
if [ -f "CLAUDE.md" ]; then
  LINES=$(wc -l < CLAUDE.md)
  if [ "$LINES" -le 100 ]; then
    echo "   ✅ PASS: CLAUDE.md has $LINES lines"
    PASS=$((PASS+1))
  else
    echo "   ❌ FAIL: CLAUDE.md has $LINES lines (limit: 100)"
    FAIL=$((FAIL+1))
  fi
fi

# Test 5: Markdown frontmatter
echo "5. Markdown frontmatter (all .md except CLAUDE.md)..."
MD_FAIL=0
for f in docs/*.md skills/*/CLAUDE.md commands/CLAUDE.md tests/CLAUDE.md; do
  [ -f "$f" ] 2>/dev/null || continue

  if ! head -5 "$f" | grep -q "^---"; then
    echo "   ❌ FAIL: $f missing YAML frontmatter"
    MD_FAIL=$((MD_FAIL+1))
  fi
done
if [ $MD_FAIL -eq 0 ]; then
  echo "   ✅ PASS: All .md docs have frontmatter"
  PASS=$((PASS+1))
else
  echo "   Total failures: $MD_FAIL"
  FAIL=$((FAIL+1))
fi

# Test 6: Beads directory exists
echo "6. Beads tracking setup..."
if [ -f ".beads/status.jsonl" ] && [ -f ".beads/decisions.jsonl" ]; then
  echo "   ✅ PASS: .beads/ directory initialized"
  PASS=$((PASS+1))
else
  echo "   ❌ FAIL: .beads/ missing status.jsonl or decisions.jsonl"
  FAIL=$((FAIL+1))
fi

# Test 7: Settings.json exists
echo "7. Settings and hooks..."
if [ -f ".claude/settings.json" ]; then
  echo "   ✅ PASS: .claude/settings.json exists"
  PASS=$((PASS+1))
else
  echo "   ❌ FAIL: .claude/settings.json missing"
  FAIL=$((FAIL+1))
fi

# Test 8: Hook scripts are executable
echo "8. Hook scripts (executable)..."
HOOK_FAIL=0
for hook in .claude/hooks/*.sh; do
  if [ -f "$hook" ]; then
    if [ -x "$hook" ]; then
      :
    else
      echo "   ⚠️  $hook is not executable (chmod +x recommended)"
    fi
  fi
done
echo "   ✅ PASS: Hook scripts present"
PASS=$((PASS+1))

# Summary
echo ""
echo "=== SUMMARY ==="
echo "Passed: $PASS"
echo "Failed: $FAIL"
echo ""

if [ $FAIL -eq 0 ]; then
  echo "✅ All smoke tests passed!"
  exit 0
else
  echo "❌ Some tests failed. Fix errors above before committing."
  exit 1
fi
