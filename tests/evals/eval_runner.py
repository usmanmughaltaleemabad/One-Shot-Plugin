#!/usr/bin/env python3
"""
Eval Harness Runner — Tier 4+

Runs every eval in ``tests/evals/fixtures/`` and compares against the
matching ``tests/evals/golden/`` JSON. Pure-deterministic stages only —
agentic-stage evals live in ``agentic_evals.py``.

Components scored per eval:
  * domain_extraction  — F1 over entity names + relationship triples
  * scaffold_paths     — Jaccard over file paths (must be ≥ 0.95)
  * cost_estimate      — total within ±25% of golden
  * stub_detection     — exact list match

Overall score = weighted mean. Pass threshold = 0.85.

CLI:
    python eval_runner.py                          # run all evals
    python eval_runner.py --eval cart-with-items   # single eval
    python eval_runner.py --update-golden          # regenerate goldens
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "skills" / "one-shot-generator" / "scripts"
FIXTURES = REPO_ROOT / "tests" / "evals" / "fixtures"
GOLDEN = REPO_ROOT / "tests" / "evals" / "golden"


# ─── Data shapes ─────────────────────────────────────────────────────────────

@dataclass
class ComponentScore:
    component: str
    score: float
    detail: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class EvalResult:
    eval_name: str
    components: List[ComponentScore]
    overall: float
    passed: bool

    def to_dict(self) -> Dict:
        return {
            "eval": self.eval_name,
            "components": [c.to_dict() for c in self.components],
            "overall": round(self.overall, 3),
            "passed": self.passed,
        }


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _run(script: str, *args: str) -> Tuple[int, str, str]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args],
        capture_output=True, text=True, env=env, encoding="utf-8",
        timeout=60,
    )
    return proc.returncode, proc.stdout, proc.stderr


def _f1(predicted: Set, expected: Set) -> float:
    if not predicted and not expected:
        return 1.0
    if not predicted or not expected:
        return 0.0
    tp = len(predicted & expected)
    p = tp / len(predicted)
    r = tp / len(expected)
    if p + r == 0:
        return 0.0
    return 2 * p * r / (p + r)


def _jaccard(a: Set, b: Set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


# ─── Per-component runners ──────────────────────────────────────────────────

def _run_domain_extraction(fixture: Dict[str, Any]) -> Dict[str, Any]:
    code, out, err = _run("extract_domain_model.py", "--json", fixture["task"])
    if code != 0:
        return {"error": err, "entities": [], "relationships": []}
    return json.loads(out)


def _run_scaffold_planner(spec: Dict[str, Any], tmp: Path) -> Dict[str, Any]:
    spec_path = tmp / "spec.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    code, out, err = _run("scaffold_planner.py", "--spec", str(spec_path))
    if code != 0:
        return {"error": err, "files_to_create": [], "stubs_needed": []}
    return json.loads(out)


def _run_cost_budget(plan: Dict[str, Any], tmp: Path) -> Dict[str, Any]:
    plan_path = tmp / "plan.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    code, out, err = _run("cost_budget.py", "--plan", str(plan_path), "--json")
    if code not in (0, 2):
        return {"error": err, "total_usd": 0}
    return json.loads(out)


def _build_pseudo_spec(fixture: Dict[str, Any],
                       extraction: Dict[str, Any]) -> Dict[str, Any]:
    """Produce a minimal spec.json that scaffold_planner can consume.

    For evals we shortcut the architect stage and assemble the spec
    directly from the extractor output + fixture metadata.
    """
    entities = [
        {
            "name": e["pascal"],
            "snake_name": e["name"],
            "plural": e["plural"],
            "action": "create",
            "attributes": e.get("attributes", []),
        }
        for e in extraction.get("entities", [])
    ]
    return {
        "feature": fixture.get("task", ""),
        "framework": fixture.get("framework", "fastapi"),
        "language": "python",
        "test_contract": {"auth": "none", "pagination": "list"},
        "entities": entities,
        "relationships": extraction.get("relationships", []),
        "graph_imports": fixture.get("graph_imports", {}),
        "api_surface": [],
        "wiring": {},
    }


# ─── Scoring ─────────────────────────────────────────────────────────────────

def _score_domain(extraction: Dict, expected: Dict) -> ComponentScore:
    pred_entities = {e["pascal"] for e in extraction.get("entities", [])}
    exp_entities = set(expected.get("expected_entities", []))
    entity_f1 = _f1(pred_entities, exp_entities)

    pred_rels = {
        (r.get("from") or r.get("from_entity"),
         r.get("to") or r.get("to_entity"),
         r.get("kind"))
        for r in extraction.get("relationships", [])
    }
    exp_rels = {tuple(r) for r in expected.get("expected_relationships", [])}
    rel_f1 = _f1(pred_rels, exp_rels) if exp_rels else 1.0

    score = 0.6 * entity_f1 + 0.4 * rel_f1
    detail = (f"entity F1={entity_f1:.2f} (pred={sorted(pred_entities)}, "
              f"exp={sorted(exp_entities)}); rel F1={rel_f1:.2f}")
    return ComponentScore("domain_extraction", round(score, 3), detail)


def _score_scaffold(plan: Dict, golden: Dict) -> ComponentScore:
    pred_paths = {f["path"] for f in plan.get("files_to_create", [])}
    exp_paths = {f["path"] for f in golden.get("files_to_create", [])}
    j = _jaccard(pred_paths, exp_paths)
    detail = f"jaccard(paths) = {j:.2f} ({len(pred_paths)} pred, {len(exp_paths)} exp)"
    return ComponentScore("scaffold_paths", round(j, 3), detail)


def _score_cost(estimate: Dict, golden: Dict) -> ComponentScore:
    pred = estimate.get("total_usd", 0.0)
    exp = golden.get("total_usd", 0.0)
    if exp == 0:
        score = 1.0 if pred == 0 else 0.0
    else:
        diff = abs(pred - exp) / exp
        score = max(0.0, 1.0 - diff / 0.25)  # full credit at ≤25% diff, zero at 100%
    detail = f"pred=${pred:.3f}, exp=${exp:.3f}, diff={abs(pred - exp):.3f}"
    return ComponentScore("cost_estimate", round(score, 3), detail)


def _score_stubs(plan: Dict, golden: Dict) -> ComponentScore:
    pred = sorted(plan.get("stubs_needed", []))
    exp = sorted(golden.get("stubs_needed", []))
    score = 1.0 if pred == exp else 0.0
    return ComponentScore("stub_detection", score, f"pred={pred}, exp={exp}")


# ─── Public entry ────────────────────────────────────────────────────────────

def run_eval(eval_name: str, update_golden: bool = False) -> EvalResult:
    fixture_path = FIXTURES / f"{eval_name}.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    golden_path = GOLDEN / f"{eval_name}.json"

    with tempfile.TemporaryDirectory(prefix="osp-eval-") as tmpdir:
        tmp = Path(tmpdir)
        extraction = _run_domain_extraction(fixture)
        spec = _build_pseudo_spec(fixture, extraction)
        plan = _run_scaffold_planner(spec, tmp)
        cost = _run_cost_budget(plan, tmp)

    actual = {
        "extraction": extraction,
        "files_to_create": plan.get("files_to_create", []),
        "stubs_needed": plan.get("stubs_needed", []),
        "total_usd": cost.get("total_usd", 0.0),
    }

    if update_golden:
        golden_path.parent.mkdir(parents=True, exist_ok=True)
        golden_path.write_text(json.dumps(actual, indent=2), encoding="utf-8")
        return EvalResult(eval_name, [], 1.0, True)

    if not golden_path.exists():
        return EvalResult(
            eval_name,
            [ComponentScore("missing_golden", 0.0,
                            f"no golden file at {golden_path}; run with --update-golden")],
            0.0, False,
        )

    golden = json.loads(golden_path.read_text(encoding="utf-8"))
    components = [
        _score_domain(extraction, fixture),
        _score_scaffold(plan, golden),
        _score_cost(actual, golden),
        _score_stubs(plan, golden),
    ]
    weights = {"domain_extraction": 0.4, "scaffold_paths": 0.3,
               "cost_estimate": 0.15, "stub_detection": 0.15}
    overall = sum(c.score * weights.get(c.component, 0) for c in components)
    return EvalResult(eval_name, components, round(overall, 3), overall >= 0.85)


def run_all(update_golden: bool = False) -> List[EvalResult]:
    results: List[EvalResult] = []
    for fixture_path in sorted(FIXTURES.glob("*.json")):
        results.append(run_eval(fixture_path.stem, update_golden=update_golden))
    return results


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Run deterministic eval harness")
    parser.add_argument("--eval", help="Run a single eval by name (file stem)")
    parser.add_argument("--update-golden", action="store_true",
                        help="Capture current outputs as new golden (use after intended changes)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.eval:
        results = [run_eval(args.eval, update_golden=args.update_golden)]
    else:
        results = run_all(update_golden=args.update_golden)

    if args.json:
        print(json.dumps([r.to_dict() for r in results], indent=2))
    else:
        passed = sum(1 for r in results if r.passed)
        print(f"EVAL HARNESS — {passed}/{len(results)} passed")
        print("─" * 60)
        for r in results:
            mark = "✓" if r.passed else "✗"
            print(f"  {mark} {r.eval_name:<30} {r.overall:.2f}")
            if not r.passed:
                for c in r.components:
                    print(f"      [{c.score:.2f}] {c.component}: {c.detail}")
    sys.exit(0 if all(r.passed for r in results) else 1)


if __name__ == "__main__":
    main()
