---
description: Detect documentation drift and propose updates. Runs codebase_diff + spawns the docs-author agent to write a proposal at .tmp/docs-drift-{timestamp}.md. Never mutates docs directly — you review and merge.
argument-hint: "[--since <git-rev>] [--target README|all]"
allowed-tools: Read, Grep, Glob, Bash, Task
---

Invoke the **docs-author** agent:

/one-shot-prompting:docs-drift $ARGUMENTS

The docs-author agent compares your current codebase against the cached
graph, identifies added/removed/modified entities, and proposes README +
docstring updates in a single markdown file. You review, you commit.
