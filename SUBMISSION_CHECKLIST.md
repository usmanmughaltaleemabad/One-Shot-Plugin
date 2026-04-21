# Submission Checklist

Complete every item before submitting to the Anthropic plugin marketplace. Skipping items risks rejection or poor user reviews.

## Placeholders to replace

- [ ] `YOUR-GITHUB-USERNAME` in `.claude-plugin/plugin.json`
- [ ] `YOUR-GITHUB-USERNAME` in `README.md`
- [ ] `Your Name` in `.claude-plugin/plugin.json` author field
- [ ] `[YOUR NAME]` in `LICENSE`
- [ ] Push to a public GitHub repo matching the URL in `plugin.json`

## Local testing

- [ ] Install Claude Code and authenticate
- [ ] Run `claude --plugin-dir ./one-shot-prompting`
- [ ] Confirm `/plugin` lists the plugin without errors
- [ ] Invoke `/one-shot-prompting:generate Add a logger that counts message.received events and exposes /log-count to return the count`
- [ ] Verify response has ALL of these in ONE response:
  - [ ] Assumptions block at top
  - [ ] Complete module code
  - [ ] Complete test code
  - [ ] README
  - [ ] Install line
  - [ ] Rerun hints at bottom
- [ ] Verify NO clarifying questions were asked
- [ ] Verify NO approval gate appeared

## One-shot behavior verification

These are the specific behaviors that distinguish one-shot from spec-first. Confirm each:

- [ ] Given a vague request, Claude picks a default and states it in assumptions (doesn't ask)
- [ ] Given a multi-feature request, Claude refuses with specific reason (doesn't try to do all of them)
- [ ] Given a non-event-driven request, Claude refuses narrowly (doesn't attempt)
- [ ] Given a clear request with a bad default, Claude's output is correctable via rerun with constraint
- [ ] The assumptions block surfaces at least 3 decisions for any non-trivial feature

## Real-project testing (strongly recommended)

- [ ] Pick one event-driven project you own
- [ ] Generate one real feature using `/one-shot-prompting:generate`
- [ ] Adapt the bus method names per the README's adaptation notes
- [ ] Confirm the module loads and runs in your project
- [ ] Note any places where the skill's output missed something important
- [ ] Fix the skill before submitting

## Structural validation

- [ ] `.claude-plugin/plugin.json` is valid JSON
- [ ] `name` matches directory name
- [ ] `version` uses semver
- [ ] `skills/one-shot-generator/SKILL.md` has YAML frontmatter with description
- [ ] `commands/generate.md` has YAML frontmatter with description
- [ ] README exists and is honest about limitations
- [ ] LICENSE exists
- [ ] No directories incorrectly placed inside `.claude-plugin/`

## Honesty review of README

- [ ] Does not claim "universal" applicability
- [ ] Explicitly lists who this is NOT for
- [ ] Explicitly mentions the regenerate-don't-negotiate iteration model
- [ ] Compares honestly to spec-first tools rather than dismissing them
- [ ] Lists real limitations (not tested everywhere, no catalog awareness, etc.)

## Submission

- [ ] Go to [claude.ai/settings/plugins/submit](https://claude.ai/settings/plugins/submit) or [platform.claude.com/plugins/submit](https://platform.claude.com/plugins/submit)
- [ ] Submit with your public GitHub URL
- [ ] Respond to review feedback if any

## After listing

- [ ] Monitor GitHub issues for real-user feedback
- [ ] Version bumps follow semver
- [ ] Keep a `CHANGELOG.md` for each release

---

**Critical:** if you haven't completed local testing AND real-project testing, do not submit. An untested one-shot plugin that generates wrong code on first try will get bad reviews regardless of how well the docs read.
