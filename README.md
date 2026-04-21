# one-shot-prompting

A Claude Code plugin for **genuine one-shot feature generation**. One prompt in, complete working module out — no approval gates, no clarifying questions, no back-and-forth.

## The one-shot ideology

You type one sentence describing a feature. Claude produces:
- A complete sidecar module
- Tests
- A README
- An explicit list of every assumption Claude made

If an assumption is wrong, you rerun with a specific override ("use sliding window instead," "handle clock skew too," "use my existing `order.placed` event"). Iteration is through regeneration, not conversation.

This is deliberately different from spec-first tools (like parts of Superpowers), which gate output behind an approval phase. Spec-first is safer for high-stakes work. One-shot is faster for flow work where you'd rather read code than read a plan.

## Who this is for

Developers who:
- Work on event-driven projects (bots, game servers, real-time systems, event-sourced apps)
- Want flow, not collaboration — you'd rather regenerate than negotiate
- Write clear task sentences and can spot wrong assumptions by reading them
- Are comfortable discarding output and rerunning when Claude guesses wrong

## Who this is NOT for

- Projects without an event bus (use normal Claude for those)
- CRUD apps, UI components, data science notebooks
- High-stakes features where you want review-before-code (use a spec-first tool instead)
- Teams where every feature needs alignment before implementation

If the plugin generates something wrong, you rerun. That's the design. If you hate regenerating, this isn't the right tool for you — you want spec-first.

## Installation

### From the Claude Code marketplace (once approved)

```
/plugin install one-shot-prompting@claude-plugins-official
```

### Local development

```
git clone https://github.com/one-shot-prompting/one-shot-prompting
claude --plugin-dir ./one-shot-prompting
```

## Usage

```
/one-shot-prompting:generate Add a rate limiter that throttles message.received per user to 10 per minute, dropping excess
```

Claude responds with assumptions + module + tests + README + install line + rerun hints — all in one turn.

If the algorithm Claude picked is wrong for you:

```
/one-shot-prompting:generate Add a rate limiter that throttles message.received per user to 10 per minute, dropping excess. Use token bucket, not sliding window.
```

Just rerun with the constraint added. Claude regenerates the whole thing with the new constraint applied.

## Example response structure

Every response follows this shape:

```
## Assumptions
**Interpretation:** I read "throttle" as "drop excess events."
Alternative: queue and delay — rerun with "queue events instead of dropping"

**Algorithm:** sliding window log because your phrase "rolling 60 seconds"
maps to sliding-window semantics. Alternatives: token bucket, fixed window.

**Storage:** in-memory dict because no persistence was requested.
**Window:** 60 seconds because you said "per minute."
**Failure mode:** drop + emit rate.exceeded event.

**Edge cases handled:** missing user_id, first-time user, inactive cleanup
**NOT handled:** clock skew, cross-instance coordination — rerun with
"also handle clock skew" if needed.

**New events proposed:** rate.exceeded { user_id, count, window_s, ts }
Rerun with "use existing event X instead" to match your catalog.

**Project shape:** Python, async event bus (asyncio-based)

## Module: `rate_limiter/rate_limiter.py`
[full code]

## Tests: `rate_limiter/test_rate_limiter.py`
[full code]

## README: `rate_limiter/README.md`
[full README]

## Install
Copy rate_limiter/ into your skills directory and import it.

## To iterate
- "Use token bucket instead of sliding window"
- "Also handle clock skew"
- "Use existing event X instead of rate.exceeded"
- "Target tokio broadcast" (if using Rust)
- "Make it persist across restarts"
```

Every field above is actionable. You scan the assumptions, find what's wrong, rerun with the specific override.

## When the plugin refuses

Some requests can't be one-shot and the plugin refuses narrowly:

- **Multi-feature requests:** "Your request contains 3 features. Rerun with one."
- **Cross-cutting changes:** "This needs core modification, not a sidecar. Use a design conversation."
- **Wrong project shape:** "This isn't event-driven work. Use regular Claude for this."

Refusals are final responses, not invitations to discuss. Rerun with a narrower request.

## Honest limitations

**Does not guarantee working code.** Claude's first guess is often right, sometimes wrong. You regenerate when wrong. If you hate that workflow, use a spec-first tool.

**Generated code assumes a generic async bus.** If your project uses Django signals, NestJS EventEmitter, specific Rust channels, etc., you adapt using the "adaptation notes" in the generated README. The plugin doesn't know your specific bus API.

**No catalog awareness.** If your project has a strict SKILLS.md event catalog, the plugin proposes new events it thinks are reasonable. You rerun with catalog constraints if they don't match.

**Not tested on every language.** The approach is language-agnostic in principle. In practice, verify Claude generates idiomatic code in your stack before committing.

## Comparison to spec-first plugins

| | One-shot (this plugin) | Spec-first (Superpowers, etc.) |
|---|---|---|
| Turns to first code | 1 | 2+ |
| Wrong output cost | Rerun | Ongoing conversation |
| Best for | Flow work, clear intent | High-stakes, unclear intent |
| Iteration style | Regenerate with constraints | Answer questions, continue |
| Default assumptions | Visible, overrideable | Surfaced during review |

They're both valid tools. Pick based on how you want to work.

## Before submitting to the marketplace (if forking)

1. Replace `YOUR-GITHUB-USERNAME` and `Your Name` in all files
2. Test locally with `claude --plugin-dir ./one-shot-prompting`
3. Generate at least one real feature on a real project
4. Confirm the assumptions block covers everything important
5. Push to a public GitHub repo
6. Submit via [claude.ai/settings/plugins/submit](https://claude.ai/settings/plugins/submit)

See `SUBMISSION_CHECKLIST.md` for the full pre-submission list.

## License

MIT. See LICENSE.
