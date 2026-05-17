#!/usr/bin/env python3
"""
Beads Curriculum — v0.9.0  (Tier 3 learning loop)

Reads ``.beads/failures.jsonl`` and surfaces past failures that look
similar to the current task, so the orchestrator (and Claude composing the
response) can pre-empt mistakes the plugin has already made.

The matching is intentionally simple — a Jaccard-style overlap of task
tokens plus a phase-equality bonus. We don't need embeddings or vector
search for the current scale; a few hundred beads of accumulated history
is plenty for keyword overlap to be useful.

CLI:
    python beads_curriculum.py "shopping cart with line items" --phase phase2
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from lib.base_script import bootstrap_runtime, setup_logging
bootstrap_runtime()

logger = setup_logging(__name__)

_STOPWORDS = {
    "add", "create", "build", "generate", "make", "with", "and", "or",
    "for", "the", "a", "an", "to", "of", "in", "on", "by", "as", "via",
    "feature", "module", "service", "api", "rest", "crud", "endpoint",
    "endpoints", "system", "complete", "full", "ready", "production",
}


@dataclass
class CurriculumHit:
    bead_id: str
    similarity: float
    same_phase: bool
    summary: str
    advice: str

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class CurriculumReport:
    task: str
    phase: Optional[str]
    total_beads: int
    hits: List[CurriculumHit] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "task": self.task,
            "phase": self.phase,
            "total_beads": self.total_beads,
            "hits": [h.to_dict() for h in self.hits],
        }


def _tokenize(text: str) -> set:
    return {tok for tok in re.findall(r"[a-zA-Z_]+", text.lower())
            if tok and tok not in _STOPWORDS}


def _similarity(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _summarise_bead(bead: Dict[str, Any]) -> str:
    diags = bead.get("diagnostics", []) or []
    if not diags:
        return f"{bead.get('kind', 'failure')} with no diagnostic detail"
    first = diags[0]
    msg = first.get("message") if isinstance(first, dict) else str(first)
    return f"{bead.get('kind', 'failure')}: {msg[:140]}"


def _advice_for(bead: Dict[str, Any]) -> str:
    """Map known failure signatures to actionable advice for the next attempt."""
    diags = bead.get("diagnostics") or []
    messages = " ".join(
        d.get("message", "") if isinstance(d, dict) else str(d) for d in diags
    ).lower()
    if "401" in messages:
        return ("test/router contract drift — set test_contract.auth='none' "
                "in spec.json if no auth middleware is generated")
    if '"next"' in messages or "pagination" in messages:
        return ("pagination contract drift — set test_contract.pagination='list' "
                "or generate a paginated envelope on the router side")
    if "placeholder" in messages:
        return "template placeholder leaked — run auto_patch with --resource-hint"
    if "modulenotfounderror" in messages or "importerror" in messages:
        return "missing module — pass codebase_imports so the patcher can rewrite default paths"
    return "no canned advice — review the bead's diagnostics manually"


def consult(*, task: str, phase: Optional[str] = None,
            failures_path: Path,
            min_similarity: float = 0.2,
            limit: int = 5) -> CurriculumReport:
    if not failures_path.exists():
        return CurriculumReport(task=task, phase=phase, total_beads=0)
    task_tokens = _tokenize(task)
    hits: List[CurriculumHit] = []
    total = 0
    for line in failures_path.read_text(encoding="utf-8").splitlines():
        try:
            bead = json.loads(line)
        except json.JSONDecodeError:
            continue
        total += 1
        bead_tokens = _tokenize(bead.get("task", ""))
        sim = _similarity(task_tokens, bead_tokens)
        same_phase = phase is not None and bead.get("phase") == phase
        if same_phase:
            sim = min(1.0, sim + 0.1)
        if sim < min_similarity:
            continue
        hits.append(CurriculumHit(
            bead_id=bead.get("id", "<unknown>"),
            similarity=round(sim, 3),
            same_phase=same_phase,
            summary=_summarise_bead(bead),
            advice=_advice_for(bead),
        ))
    hits.sort(key=lambda h: h.similarity, reverse=True)
    return CurriculumReport(task=task, phase=phase, total_beads=total,
                            hits=hits[:limit])


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Surface past failures similar to the current task"
    )
    parser.add_argument("task", nargs="+", help="Current feature task")
    parser.add_argument("--phase", default=None,
                        help="Generator phase (phase2/phase3) for same-phase bonus")
    parser.add_argument("--failures",
                        default=".beads/failures.jsonl",
                        help="Path to failures.jsonl (relative to repo root)")
    parser.add_argument("--repo-root", default=None,
                        help="Repo root containing .beads/")
    parser.add_argument("--json", action="store_true",
                        help="Emit JSON only")
    args = parser.parse_args()

    if args.repo_root:
        repo_root = Path(args.repo_root).resolve()
    else:
        cur = Path.cwd().resolve()
        while cur != cur.parent and not (cur / ".beads").exists():
            cur = cur.parent
        repo_root = cur

    failures = repo_root / args.failures
    report = consult(task=" ".join(args.task), phase=args.phase,
                     failures_path=failures)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
        return
    print(f"CURRICULUM ({report.total_beads} past failures on file)")
    if not report.hits:
        print("  no similar past failures — proceed without warnings")
        return
    for h in report.hits:
        marker = " (same phase)" if h.same_phase else ""
        print(f"  • [{h.similarity:.2f}{marker}] {h.bead_id}")
        print(f"      {h.summary}")
        print(f"      advice: {h.advice}")


if __name__ == "__main__":
    main()
