---
description: Execute implementation plans task by task. Loads Markdown plan, verifies each task with provided command, stops on failures. Resumable — fix and resume from the blocking task.
status: experimental
argument-hint: "[plan-file.md] [--start-task=N]"
allowed-tools: none
destructive: true
read-only: false
---

Invoke the execute-plan skill:

/one-shot-prompting:execute-plan $ARGUMENTS
