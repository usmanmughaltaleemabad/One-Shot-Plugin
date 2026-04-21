---
description: Use when the user asks for a complete sidecar feature module in a single prompt with no back-and-forth. Trigger phrases include "one-shot", "generate this feature", "add a module that", "write a sidecar for", "I need a plugin that listens for X and does Y". Produces module + tests + README in one response with stated assumptions. User iterates by rerunning with overrides, not by answering follow-up questions. Do NOT use for vague multi-feature requests (refuse narrowly), cross-cutting changes (refuse with reason), or projects without event-driven shape (refuse with explanation).
---

# One-Shot Feature Generator

Generate a complete sidecar feature module from a single prompt. No approval gates. No clarifying questions. Claude decides, states assumptions, ships.

## The one-shot contract

When a user requests a feature, produce everything in ONE response:

1. **Assumptions block** (top) — every non-trivial choice made, why
2. **Module file** — the complete sidecar
3. **Test file** — at least two tests covering the stated behavior
4. **README** — events consumed/emitted, command, one usage example
5. **Install line** — one command the user can run
6. **Rerun hints** (bottom) — how to override key assumptions

No "please confirm." No "would you like X or Y." No spec phase. If the output is wrong, the user reruns with specific constraints. That's the iteration loop.

## Internal reasoning (not shown to user)

Before generating, Claude resolves ambiguity internally:

**Interpret vocabulary precisely.** If the user says "throttle," decide whether they mean "drop excess," "queue and delay," or "reject with error." Pick the most common meaning for the domain. State the choice in the assumptions block.

**Enumerate edge cases silently.** Empty payload, missing fields, clock skew, concurrent events, new user, inactive user, resource cleanup, timeouts, null values. Handle the likely ones in code; note the handling in assumptions; mention non-handled ones in rerun hints.

**Pick defensible defaults.** When the user doesn't specify algorithm, window size, storage, failure mode — pick what a senior engineer would defend in review. State the reasoning in assumptions.

**Enumerate proposed events.** If the feature needs new events, just include them in the module. List them in the "events emitted" section of the README. Don't wait for catalog approval — if the user has a strict catalog, they'll rerun with "use existing event `X` instead."

## The assumptions block (mandatory, always first)

Every response starts with an `## Assumptions` block. This is the contract that replaces the spec phase — it makes every decision visible in the same turn as the code.

Structure:

```
## Assumptions

**Interpretation:** I read "[user's phrase]" as "[specific meaning]".
Alternative: "[what they might have meant instead]" — rerun with
"[specific override phrase]" if you wanted that.

**Algorithm:** [chosen] because [one-sentence reason].
Alternatives considered: [list]. Rerun with "use [X] instead" to override.

**Storage:** [chosen] because [reason].
**Window/timing:** [chosen] because [reason].
**Failure mode:** [chosen] because [reason].

**Edge cases handled:** [list briefly]
**Edge cases NOT handled:** [list briefly] — rerun with "also handle [X]" to include.

**New events proposed:** [list]
If you have an existing event catalog, rerun with "use events [X, Y]" to
constrain.

**Language:** [Python/Go/Rust/JavaScript/TypeScript] with type hints and linting compliance (PEP 8/Black/Flake8 for Python, idiomatic style for others).

**Project shape assumed:** Event-driven, [language], has an async bus
(or will use something like [specific bus]).
```

If any of these don't apply to the request (e.g. no algorithm choice needed), omit that line. Never pad.

## Language Support

**Supported Languages:**
- **Python** (default if not specified) — async, type hints, PEP 8 compliant, Black/Flake8 clean
- **Go** — goroutines, idiomatic error handling, formatted with gofmt
- **Rust** — async/await, strong typing, clippy compliant
- **JavaScript/TypeScript** — async, with JSDoc comments and TypeScript types (if --typescript)
- **Java** — async patterns, proper exception handling, following Google style guide

**Language Detection:** If user specifies language in prompt ("in Go", "Rust sidecar", etc.), generate in that language. Otherwise default to Python.

**Type Hints:** ALL languages use their native type system:
- Python: type annotations (`def foo(x: str) -> bool:`)
- Go: explicit types (`func Foo(x string) bool`)
- Rust: strong typing (`fn foo(x: &str) -> bool`)
- TypeScript: full typing enabled
- Java: generic types and annotations

**Code Quality:** Generated code passes standard linting:
- Python: PEP 8 + Black + Flake8
- Go: gofmt + go vet
- Rust: clippy with default lint settings
- TypeScript: eslint with recommended config
- Java: Google style guide

## Deliverables (after assumptions block)

**Module file.** Complete, copy-pasteable, in the target language. Uses the project's idioms and conventions. No imports from other skills. No reach into a specific core implementation — write against a generic `Bus` interface with `subscribe` and `emit`, and note in the README what the user needs to adapt if their bus has a different API. Code must pass linting and include type hints in the target language's style.

**Test file.** Two tests minimum. One for the happy path event/command. One for an edge case from the assumptions block. Use the target language's standard test framework.

**README.md.** Structure:
- One-paragraph what it does
- Events consumed (list with payload shape)
- Events emitted (list with payload shape, including new ones from assumptions)
- Command if applicable
- One usage example
- Adaptation notes — what needs to change if the user's bus has different method names

**Install line.** One line. Either copy instructions or `/inject`-style if their system has it.

**Rerun hints block** (bottom). Structure:

```
## To iterate

If something is wrong, rerun with one of these additions to your prompt:

- "In Rust" / "In Go" / "In TypeScript" — generate in different language
- "Use X instead of Y" — changes an algorithm/storage choice
- "Also handle [edge case]" — adds error handling (null safety, timeouts, concurrency)
- "Use existing event [X] instead of creating a new one" — matches your catalog
- "Target [specific bus library]" — adapts to your actual event system
- "No type hints" — remove type annotations (not recommended)
- "Skip linting compliance" — omit formatting/style compliance (not recommended)
- "Make it [stricter/looser/faster/smaller]" — general tone adjustment
```

## When to refuse (narrowly, in one response)

One-shot means one feature. Refuse with a specific reason, not a conversation:

**Multi-feature requests:** "This request contains N distinct features: [list]. One-shot means one feature. Rerun with just one, then run again for the others."

**Cross-cutting / core changes:** "This requires modifying the project's core, not adding a sidecar. One-shot only generates sidecars. You'll need a design conversation for this, then come back for pieces that are genuinely event-subscriber-shaped."

**Not event-driven shape:** "This plugin generates event-subscribing sidecar modules. Your request ([what they asked]) is better served by [appropriate approach]. This plugin isn't the right tool."

**Genuinely ambiguous:** Very rare if you pick defensible defaults. Only refuse if the request is literally "add a feature" with no other information. Ask for one sentence more — but frame it as a prompt rewrite, not a conversation: "Rerun with a specific trigger and outcome, like 'when X happens, emit Y'."

Refusals are themselves one-shot responses. Don't start a dialogue.

## What makes this genuinely one-shot (and not spec-first)

- Claude produces code in the first response. Every time. No "awaiting approval."
- Decisions are stated, not negotiated. The user sees them, the user reruns if wrong.
- Ambiguity is resolved via defensible defaults, not user questions.
- Refusals are complete responses, not requests for clarification.
- The iteration loop is "rerun with constraints," not "answer questions and continue."

If Claude finds itself wanting to ask a clarifying question, it should instead pick the likely answer, state it as an assumption, and ship. The user reruns if wrong.

## Response template

```
## Assumptions

[assumptions block]

## Module: `<skill_name>/<skill_name>.<ext>`

[complete module code]

## Tests: `<skill_name>/test_<skill_name>.<ext>`

[complete test code]

## README: `<skill_name>/README.md`

[complete README]

## Install

[one line]

## To iterate

[rerun hints]
```

Keep prose between sections minimal. The user wants code and the info to iterate, not explanation.
