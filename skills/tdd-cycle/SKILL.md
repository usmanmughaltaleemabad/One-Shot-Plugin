---
name: tdd-cycle
description: Enforce strict Red-Green-Refactor TDD cycle with phase gates. No code before failing test. Generates test-first, validates failure, generates minimal implementation, validates pass, aligns with conventions. Three phases with mandatory checkpoints between each.
argument-hint: "[feature description] [@path/to/project] [--phase=red|green|refactor]"
allowed-tools: Bash(python *)
---

# TDD Cycle — Red Green Refactor

Enforce strict test-driven development with phase gates. Each phase must complete before proceeding to the next.

## RED Phase: Write Failing Test

Generate a failing test **before any implementation code**:

```!
python "./scripts/tdd_cycle_enforcer.py" --phase=red --feature="$FEATURE" --cwd="$PROJECT_PATH"
```

Output shows:
- Test file path
- Expected failure signature (`NotImplementedError`)
- Command to run test

### Gate: Confirm Test Fails
Run the test command from above output. **MUST see the NotImplementedError or other failure.** If test passes immediately, your test is wrong — write a better test.

**[BLOCKED]** Cannot proceed to GREEN without confirming test fails for the right reason.

---

## GREEN Phase: Minimal Implementation

Generate minimal code to make failing test pass:

```!
python "./scripts/tdd_cycle_enforcer.py" --phase=green --feature="$FEATURE" --test-file="[test file from RED]" --cwd="$PROJECT_PATH"
```

Output shows:
- Implementation code
- Verify command

### Gate: Confirm All Tests Pass
Run the verify command. **ALL tests must pass with clean output.**

**[BLOCKED]** Cannot proceed to REFACTOR without confirming all tests pass.

---

## REFACTOR Phase: Align with Conventions

Refactor implementation to match codebase conventions (no behavior changes):

```!
python "./scripts/tdd_cycle_enforcer.py" --phase=refactor --impl-file="[impl file]" --cwd="$PROJECT_PATH"
```

Output shows:
- Refactored implementation
- Conventions applied
- Verify command

### Gate: Confirm Tests Still Pass
Run the verify command. **Tests must still pass. No behavior should change.**

---

## Iron Rules

1. **NO CODE BEFORE TEST** — Test always comes first. If you write code before the test, delete it and start over.
2. **VERIFY AT EACH PHASE** — Do not skip the PASS/FAIL checks. If unsure, output the actual test result to confirm.
3. **MINIMAL IMPLEMENTATION** — Write the simplest code to make the test pass. No extra features, no premature optimization.
4. **ONE BEHAVIOR PER TEST** — If your test name has "and" in it, split it into two tests.

---

**Superpowers Skill:** Can be invoked during /execute-plan when a task involves new logic.
