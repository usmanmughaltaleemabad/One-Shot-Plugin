# Release Guide for One-Shot Prompting

This guide explains how to version, release, and iterate on the plugin.

## Versioning Strategy

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR** (0.X.0) — Breaking changes to the plugin's behavior or API
- **MINOR** (X.Y.0) — New features, backwards compatible (add language support, new edge cases)
- **PATCH** (X.Y.Z) — Bug fixes, documentation updates, no new features

### Examples

- **v0.1.0** → **v0.2.0** (MINOR): Added multi-language support (new feature, backwards compatible)
- **v0.2.0** → **v0.2.1** (PATCH): Fix typo in Rust edge case handling
- **v0.2.1** → **v1.0.0** (MAJOR): Change assumptions block format (breaking)

## Release Process

### Step 1: Update CHANGELOG.md

Add an entry at the top under `## [X.Y.Z] - YYYY-MM-DD`:

```markdown
## [0.3.0] - 2026-05-15

### Added
- Support for error handling with retry strategies

### Fixed
- Improved type hint generation for optional parameters

### Changed
- Expanded edge case handling documentation
```

### Step 2: Update plugin.json Version

```bash
# In .claude-plugin/plugin.json, change:
"version": "0.2.0"  →  "version": "0.3.0"
```

### Step 3: Update README (if needed)

Add new features to the README "What's New" section if this is a MINOR or MAJOR release.

### Step 4: Commit and Push

```bash
cd c:\Projects\plugin\one-shot-prompting

# Commit changes
git add CHANGELOG.md .claude-plugin/plugin.json README.md skills/one-shot-generator/SKILL.md
git commit -m "feat: [Brief description of features] (v0.3.0)"

# Push to GitHub
git push
```

### Step 5: Create a GitHub Release (Optional but Recommended)

```bash
git tag v0.3.0
git push origin v0.3.0
```

Then go to GitHub → Releases → Create a new release with your CHANGELOG entry.

## Future Improvements (Ideas for v0.3.0, v0.4.0)

### High Priority (Next Release)
- [ ] Deployment configuration generation (Docker, Kubernetes)
- [ ] CI/CD pipeline templates (GitHub Actions, GitLab CI)
- [ ] Performance profiling helpers in generated code
- [ ] Distributed tracing/logging boilerplate

### Medium Priority
- [ ] Database schema migration generation
- [ ] Event versioning and backwards compatibility
- [ ] Multi-region deployment strategies
- [ ] Authentication/authorization patterns

### Lower Priority
- [ ] GraphQL subscription sidecars
- [ ] gRPC service code generation
- [ ] WebSocket handler templates
- [ ] Machine learning model serving sidecars

## Testing Before Release

Before committing a new version:

1. **Test locally with Claude Code:**
   ```bash
   claude --plugin-dir ./one-shot-prompting
   ```

2. **Test with each supported language:**
   ```
   /one-shot-prompting:generate Add event counting. In Python.
   /one-shot-prompting:generate Add event counting. In Go.
   /one-shot-prompting:generate Add event counting. In Rust.
   /one-shot-prompting:generate Add event counting. In TypeScript.
   /one-shot-prompting:generate Add event counting. In Java.
   ```

3. **Verify generated code:**
   - Passes type checking
   - Passes linting
   - Tests run and pass
   - README is clear

## Update Anthropic Marketplace (If Breaking Changes)

If you release v1.0.0 or make breaking changes:

1. Go to https://claude.ai/settings/plugins/submit
2. Update plugin metadata if needed
3. Respond to any review questions from Anthropic

*Note: Minor versions typically don't require marketplace updates.*

## Monitoring User Feedback

After each release:

1. Check GitHub issues for bug reports
2. Look for feature requests
3. Monitor if users hit the "NOT FOR" cases
4. Iterate based on feedback

## Example Release Cycle

```
Week 1: v0.2.0 released
  - Users discover edge cases we missed
  - File issues with specific scenarios

Week 2-3: Collect feedback
  - Add better null handling
  - Improve concurrent event handling
  - Expand documentation

Week 4: v0.2.1 (PATCH)
  - Release bug fixes and improvements
  - No new features

Week 5-6: Plan v0.3.0
  - Gather feature requests
  - Design new capabilities
  - Get community input

Week 7-8: Implement v0.3.0
  - Add multi-language improvements
  - Add deployment templates
  - Update tests

Week 9: v0.3.0 released
  - Cycle repeats
```

## Communication with Users

When releasing new versions:

1. **GitHub Release Notes** — Use CHANGELOG format
2. **README Updates** — Highlight new features
3. **Commit Messages** — Use conventional commits (feat:, fix:, docs:)
4. **Issues & Discussions** — Acknowledge feedback

---

**You own this plugin.** Release improvements whenever you're ready. Users will get them automatically from the marketplace (usually within 24 hours).
