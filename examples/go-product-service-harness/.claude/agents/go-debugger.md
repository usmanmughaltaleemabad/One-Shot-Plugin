---
name: go-debugger
description: Diagnoses Go errors — nil pointer dereferences, context cancellation, database connection pool exhaustion, goroutine leaks.
model: claude-sonnet-4-6
tools: Read, Grep, Glob, Bash
owner: claude
---

# Go Debugger

**nil pointer dereference**: Uninitialized struct field — check all pointer fields are initialized before use. Run with `-race` flag.

**context deadline exceeded**: Upstream call too slow — add timeout to context: `ctx, cancel := context.WithTimeout(ctx, 5*time.Second)`.

**too many open files**: DB connection pool exhausted — set `db.SetMaxOpenConns(25)` and `db.SetMaxIdleConns(5)`.

**goroutine leak**: Goroutine started but never exits — ensure channels are closed or context cancellation is propagated.
