---
type: reference
last_verified: 2026-05-18
owner: claude
---

# Eval Harness

Known-good inputs → expected outputs. Detects regressions across releases
without needing real Claude API calls — every eval here exercises the
**deterministic** services (extract_domain_model, scaffold_planner,
auto_patch, etc.). Agentic stages get a separate harness in
`agentic_evals.py` that does require Task invocations.

## Layout

```
tests/evals/
├── fixtures/         minimal input projects (one per framework)
├── golden/           expected outputs (JSON, frozen, regenerable)
├── eval_runner.py    runs every eval, diffs vs golden, exits 0/1
└── README.md         (this file)
```

## How to add an eval

1. Drop the input into `fixtures/<eval-name>.json` with shape:
   ```json
   {
     "task": "...",
     "framework": "fastapi",
     "project_files": {"main.py": "...", "models.py": "..."},
     "expected_entities": ["Cart", "LineItem"],
     "expected_relationships": [["cart", "line_item", "has_many"]]
   }
   ```
2. Run the eval once with `--update-golden` to capture the actual
   output as the new golden:
   ```bash
   python eval_runner.py --eval cart-with-line-items --update-golden
   ```
3. Inspect the generated `golden/<eval-name>.json` — confirm it matches
   what you'd want.
4. Subsequent runs (in CI, pre-commit, or manually) compare against
   the golden and fail on diff.

## Scoring

Each eval emits a per-component score:

| Component | Scoring |
|---|---|
| Domain extraction | F1 over entity names + relationship triples |
| Scaffold paths | Exact set match (jaccard ≥ 0.95) |
| Cost estimate | Within ±25% of golden total |
| Stub detection | Exact list match |

The overall score is the weighted mean of those. < 0.85 fails the eval.
