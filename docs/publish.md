---
type: runbook
last_verified: 2026-05-16
owner: claude
---

# Marketplace Publishing Workflow

How to publish a new version to the Claude Code marketplace.

---

## Version Bump Protocol

Every release follows this sequence:

### 1. Update CHANGELOG.md (append-only)

Add entry at the top:

```markdown
## v5.1.0 – 2026-05-16

### Added
- New feature X
- Skill Y enhancement

### Fixed
- Bug fix Z

### Changed
- Breaking change (if any)
```

**Rule:** Always include Added/Fixed/Changed sections, even if empty. Use [Keep a Changelog](https://keepachangelog.com) format.

---

### 2. Update plugin.json

Match version to CHANGELOG.md:

```json
{
  "version": "5.1.0",
  ...
}
```

Run the smoke test to validate version consistency:
```bash
bash .claude/scripts/smoke-test.sh
# Should output: ✅ plugin.json (5.1.0) matches CHANGELOG.md
```

---

### 3. Update README.md "What's Working" section

If major feature:

```markdown
### **Phase 3 (13 modules)**: Batch job systems (queues, retries, DLQ), monitoring, observability ✅ [v2.0.0]

### **New in v5.1.0**: Webhook retry backoff strategies
- Exponential backoff with jitter
- Circuit breaker pattern
```

---

### 4. Commit

```bash
git add CHANGELOG.md plugin.json README.md [any changed SKILL.md or docs]
git commit -m "release: v5.1.0 — [one-line summary of changes]"
git push origin main
```

Example:
```bash
git commit -m "release: v5.1.0 — Webhook retry backoff + exponential jitter"
```

---

### 5. Create GitHub Release

```bash
gh release create v5.1.0 --title "v5.1.0 — Webhook Retry Backoff" \
  --notes "$(sed -n '/^## v5.1.0/,/^## v/p' CHANGELOG.md | head -20)"
```

This:
- Tags the commit
- Creates a release on GitHub
- Makes it discoverable on marketplace

---

## Pre-Publish Checklist

Before bumping version:

- [ ] All tests pass: `bash .claude/scripts/smoke-test.sh`
- [ ] Integration tests pass: `python RUN_INTEGRATION_TESTS.py`
- [ ] CLAUDE.md < 100 lines
- [ ] All new .md docs have YAML frontmatter
- [ ] CHANGELOG.md has entry for this version
- [ ] README.md "What's Working" updated (if major feature)
- [ ] No `print(...)` debug statements left in scripts
- [ ] No uncommitted changes: `git status`

---

## Marketplace Submission (Manual)

Once CI passes on GitHub:

1. Go to [Claude Code Marketplace](https://claude.ai/plugins)
2. Select "Submit Plugin"
3. Upload `.claude-plugin/plugin.json`
4. Fill metadata:
   - Name: one-shot-prompting
   - Version: (auto-filled from plugin.json)
   - Description: (from README.md first paragraph)
   - Keywords: code-generation, rest-api, batch-jobs, framework-aware
5. Wait for automated review (~24 hours)
6. Address any feedback + re-submit

---

## Version Semver Convention

| Bump | When | Example |
|------|------|---------|
| Major (X.0.0) | New phase shipped, or breaking change to SKILL.md API | v3.0.0 = Phase 4 shipped |
| Minor (X.Y.0) | New skills, generators, or test contexts | v2.1.0 = new batch job generators |
| Patch (X.Y.Z) | Bug fixes, doc updates, improved error messages | v2.0.1 = fix Django ORM detection |

---

## Publishing Multiple Versions in One Day

Not recommended. Wait at least 4 hours between releases (gives time for feedback).

If critical bug found:
1. Create patch release (X.Y.Z+1)
2. Go through full checklist
3. Mark old version as deprecated in marketplace

---

## Rollback (If Marketplace Breaks)

If a published version causes widespread errors:

1. Revert commit: `git revert <commit-hash>`
2. Create new patch: `git tag v5.1.1-hotfix && git push --tags`
3. Mark v5.1.0 as deprecated in marketplace
4. Re-test everything before re-releasing as v5.1.1

---

## Analytics (After Release)

Check marketplace stats 1 week after publish:

- Downloads (target: 50+ in first week for stable release)
- User feedback (rate, comments)
- Error reports (check if Phase 4-5 stubs being invoked)

If Phase 4-5 errors appear:
→ Update `.beads/failures.jsonl` with the error
→ Add a hook to block Phase 4-5 invocation without a bead

---

## Release Cadence

- **Major versions** (X.0.0): Quarterly, when phases complete
- **Minor versions** (X.Y.0): Monthly, new generators or improvements
- **Patches** (X.Y.Z): As needed, critical bugs only

Current: v2.0.0 (Phases 0-3) ✅  
Next major: v3.0.0 (when Phase 4 ships) 📋
