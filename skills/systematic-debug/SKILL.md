---
name: systematic-debug
description: 4-phase root cause investigation. No guessing permitted. Hypothesize → Instrument → Observe → Fix. Generates targeted hypotheses, temporary logging code, compares output against predictions, fixes only confirmed root causes.
argument-hint: "[error/symptom] [@path/to/project] [--error-log=<file>]"
allowed-tools: Bash(python *)
---

# Systematic Debugging

No guessing. Four-phase investigation to find and fix root causes.

## PHASE 1: Hypothesize

Generate ranked hypotheses (max 5):

```!
python "./scripts/systematic_debug.py" --phase=hypothesize --error="$ERROR_DESCRIPTION"
```

Output shows:
- Hypothesis ID
- Confidence level (HIGH/MEDIUM/LOW)
- Distinguishing observation (what you'd see if true)
- What you would NOT see if false

**[BLOCKED]** Do not propose any fixes until you complete Phase 1.

---

## PHASE 2: Instrument

Generate temporary logging code targeting a hypothesis:

```!
python "./scripts/systematic_debug.py" --phase=instrument --hypothesis=$HYPOTHESIS_ID --language="python"
```

Output shows:
- Logging code (framework-aware: structlog, zap, winston)
- Where to add it in the code
- **Labeled as DEBUG-INSTRUMENT for removal**

### Apply & Run
1. Add the instrumentation code to the suspected function
2. Run the failing scenario
3. **Paste the full output** into next phase

---

## PHASE 3: Observe

Compare observed output against hypothesis predictions:

```!
python "./scripts/systematic_debug.py" --phase=observe --hypothesis=$HYPOTHESIS_ID --output="$PASTED_OUTPUT"
```

Output shows:
- ✅ Confirmed hypothesis(es)
- ❌ Eliminated hypothesis(es)
- Root cause ID
- Next step: FIX

**[BLOCKED]** Cannot proceed to FIX without confirmed root cause.

---

## PHASE 4: Fix

Generate targeted fix for confirmed root cause:

```!
python "./scripts/systematic_debug.py" --phase=fix --root-cause=$CONFIRMED_CAUSE_ID
```

Output shows:
- Description of fix
- Fix code
- Regression test (to prevent this bug recurring)

### Apply & Verify
1. Apply the fix (only the confirmed cause, not multiple guesses)
2. Remove all DEBUG-INSTRUMENT logging
3. Run regression test
4. Confirm test passes

---

## Iron Rules

1. **Phase 1 FIRST** — Never propose a fix without hypotheses
2. **ONE VARIABLE AT A TIME** — Change one thing per test iteration
3. **COLLECT EVIDENCE** — Log before/after boundaries, types, state
4. **READ CAREFULLY** — Check error messages, line numbers, stack traces
5. **GIVE UP AT 3** — After 3 failed fix attempts, discuss architecture with user before trying again

---

**Superpowers Skill:** Invoked when tests fail or unexpected behavior occurs during /execute-plan.
