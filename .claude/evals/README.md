---
type: reference
last_verified: 2026-05-21
owner: usman
---

# Evaluation Harness

Measure plugin quality across 6 service-level objectives.

## Quick Start

Run all evals:
```bash
python eval_runner.py --output baselines/$(date +%Y-%m-%d)-v1.0.0-baseline.jsonl
```

Run single eval task:
```bash
python eval_runner.py --task fastapi-shopping-cart-v1
```

## Artifacts

- **tasks.yaml** — 30 representative code generation scenarios
- **eval_runner.py** — orchestrates tasks, collects metrics
- **slos.md** — 6 service-level objectives with targets
- **baselines/*.jsonl** — append-only baseline results

## Metrics Collected

For each task, eval harness measures:

| Metric | Target | Why |
|---|---|---|
| Routing Quality | ≥95% | Did router pick correct agent? |
| Cost | ≤$0.50 | How much did it cost? |
| Test Pass Rate | ≥90% | Do generated tests pass? |
| Code Quality | ≥80/100 | Cyclomatic complexity + types + style |
| Security | 100% | Zero critical vulnerabilities |
| Activation Time | ≤5 min | Time from prompt to commit |

## Understanding Results

Each result is a JSON object:
```json
{
  "task_id": "fastapi-shopping-cart-v1",
  "framework": "fastapi",
  "difficulty": "easy",
  "timestamp": "2026-05-21T12:30:45",
  "metrics": {
    "routing_quality": 0.99,
    "cost_usd": 0.42,
    "test_pass_rate": 0.94,
    "code_quality_score": 82.5,
    "security_compliance": 1.0,
    "activation_time_seconds": 165
  },
  "status": "pass"
}
```

## Adding New Tasks

1. Edit `tasks.yaml` and add new task object
2. Include: id, description, framework, difficulty, expected_entities, expected_fks
3. Run: `python eval_runner.py --task <new-task-id>`
4. Commit: `git add tasks.yaml && git commit -m "eval: add <new-task>"`

## Baselines

Baseline JSONL files track metrics over time. Each run appends results:
```
{...task 1 results...}
{...task 2 results...}
{...task 3 results...}
```

Compare baselines to identify regressions:
```bash
python baselines/compare.py 2026-05-21-v1.0.0-baseline.jsonl 2026-05-22-v1.0.1-baseline.jsonl
```

## SLOs

See [slos.md](slos.md) for detailed definitions of each service-level objective.
