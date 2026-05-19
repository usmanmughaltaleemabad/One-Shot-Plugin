## Stage 5 — Reviewer agent

Spawn the reviewer to gate on security/perf/style:

```text
Agent({
  description: "Reviewer: security + perf + style audit",
  subagent_type: "general-purpose",
  prompt: """
    Read .claude/agents/reviewer.md.
    Files to review: <list paths under /tmp/osp-out>
    Spec.json: <paste /tmp/osp-spec.json>
    Codebase graph imports: <paste>

    Emit REVIEW: PASS or REVIEW: REVISE per the agent spec.
    On REVISE, name the responsible agent (implementer / test-author)
    and the specific file:line:issue.
  """
})
```

If REVISE, route fixes back to the named agent and re-run reviewer (max 2
review iterations). If still red after 2, escalate to the user.

**Reviewer input compression (caveman):** If the reviewer prompt would
exceed ~8000 tokens (verbose generated code + spec + graph), invoke the
**caveman** skill to compress the input first:

```!
@./../../caveman/SKILL.md
```

Pass `--preserve-code --preserve-errors --target-reduction=60`. Caveman
strips commentary but keeps every code block, error message, and decision.
Typical savings: 40-75% input tokens for reviewer iteration loops.

Skip caveman when the user passed `--no-compress` or when total prompt
size is under 8k tokens (no savings worth the extra step).

---

## Stage 5.5 — Doubt-driven adversarial pass (DEFAULT ON)

**Run this stage unless the user passed `--no-doubt`.** The reviewer
reads the spec, the implementer's reasoning, and previous review
history — that context makes it biased toward "this looks fine."
Stage 5.5 spawns a FRESH-CONTEXT **doubter** agent per artifact. The
doubter receives ONLY:
  1. The artifact's content (the generated file)
  2. The contract it must satisfy (entity attrs + test_contract + invariants)

It does NOT receive the spec.json's reasoning or the implementer/reviewer
notes. That information withholding is the point — it prevents
agreement bias and surfaces the bugs that "looks reasonable" reviews miss.

Initialise:
```!
python "../one-shot-generator/scripts/doubt_driver.py" init --sandbox <sandbox-dir>
```

For each artifact the implementer + reviewer produced:

```text
Agent({
  description: "Doubter: fresh-context adversarial review of <path>",
  subagent_type: "general-purpose",
  prompt: """
    Read .claude/agents/doubter.md.
    Artifact path: <path>
    Artifact content: <paste full file content>
    Contract: <paste ONLY entity + test_contract + invariants from spec.json>
    Emit findings + verdict per the agent spec.
  """
})
```

Capture the doubter's JSON output, then:
```!
python "../one-shot-generator/scripts/doubt_driver.py" record \
    --sandbox <sandbox-dir> \
    --artifact <path> \
    --verdict /tmp/osp-doubt-verdict.json
```

The driver returns one of three decisions:
  - `PROCEED` — no `contract_violation` or `actionable_gap` findings.
    Advance to Stage 6.
  - `LOOP_TO_IMPLEMENTER` — re-spawn the implementer with the
    `blocking_findings` list as the "why". After it rewrites the file,
    spawn the doubter again (round 2).
  - `ESCALATE` — max 2 doubt rounds OR same fingerprints across rounds
    (doubt theater). Stop, surface to user.

This stage is bounded: max 2 doubt rounds per artifact, max ~$0.04 per
round at sonnet pricing.

---

## Stage 5.7 — Cross-agent consistency + security deep scan (DEFAULT ON)

Reviewer, doubter, and critic each look at ONE thing in isolation
(code, contract-vs-artifact, tests). They miss subtle drift BETWEEN
agents — the architect declares an invariant, the implementer doesn't
enforce it, no single reviewer notices because each agent did its
local job. This stage runs after Stage 5.5 and closes that gap.

**Two checks run in parallel. Both default-on, opt out via
`--no-consistency-check` / `--no-security-scan` respectively.**

### 5.7a — Cross-agent consistency

```!
python "../one-shot-generator/scripts/cross_agent_consistency.py" \
    --spec /tmp/osp-spec.json \
    --generated-dir /tmp/osp-out \
    --reviewer-verdict /tmp/osp-reviewer.json \
    --doubt-state <sandbox>/.osp-doubt-state.json \
    --strict
```

Verifies five invariants ACROSS agent outputs:

| Check | Catches |
|---|---|
| `SPEC_ATTRS_MATCH_MODEL` | implementer dropped a field declared in spec.json |
| `INVARIANT_ENFORCED` | service.py too sparse to honestly enforce N spec invariants |
| `SPEC_RELATIONSHIPS_MATCH_FKS` | relationship in spec but FK column missing in model |
| `REVIEWER_FINDINGS_ADDRESSED` | reviewer flagged X; X is still present after fix iteration |
| `DOUBTER_FINDINGS_ADDRESSED` | doubt rounds didn't shrink blocking findings (theater) |

Verdict `BLOCKED` → halt the run; surface the violations to the user.

### 5.7b — Security deep scan (deterministic SAST)

```!
python "../one-shot-generator/scripts/security_deep_scan.py" \
    --target /tmp/osp-out \
    --strict
```

Runs ~20 SAST rules across AUTH / INJECTION / CRYPTO / ACCESS / EXPOSURE
categories:

- **AUTH**: hardcoded AWS/GitHub/Slack/Google tokens; RSA private keys
  in source; JWT secret as literal string
- **INJECTION**: SQL injection via f-string / format / concat / template
  literals; `subprocess.run(..., shell=True)`; `os.system()`; path
  traversal patterns
- **CRYPTO**: MD5/SHA1 for security; bcrypt cost < 12; `random.*` for
  tokens (must be `secrets.*`); hardcoded IV/salt
- **ACCESS**: `eval()` / `exec()` with user input; `pickle.load()` from
  untrusted source; `yaml.load()` without SafeLoader
- **EXPOSURE**: `DEBUG=True` literal; CORS `allow_origins=['*']` (HIGH
  if combined with `allow_credentials=True`)

Any HIGH finding → BLOCK. MEDIUM with `--strict` → also BLOCK.

### Why this stage matters (Gemini review):

> Multi-agent complexity can backfire: when 10 different AI agents
> start talking to each other, passing specs, and writing code in
> parallel, things can go sideways. While it has a "Critic" agent to
> catch test failures, subtle logic bugs or security flaws could still
> slip through.

This stage is the deterministic safety net for the "subtle logic bugs
or security flaws" case. Critic runs tests (which the implementer
also wrote — possible coverage gap). 5.7 runs cross-agent invariants
and a fixed SAST ruleset — coverage NOT determined by what the
implementer chose to test.

