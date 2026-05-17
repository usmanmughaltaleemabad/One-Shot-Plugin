#!/usr/bin/env python3
"""
Predictive Failure Detection — Tier 7A

Embedding-style cosine similarity over past failures, but **stdlib only**
— uses TF-IDF rather than neural embeddings. When the user's current
task has high similarity to a recorded failure, surface it as a hard
warning before any work begins.

Upgrade path:
  * If ``sentence-transformers`` is installed, use it for actual
    semantic embeddings (graceful fallback to TF-IDF).
  * If neither, fall back to ``beads_curriculum``'s token-Jaccard.

Why TF-IDF beats Jaccard:
  - Term frequency captures word importance ("user signup verification"
    vs "user list" both contain "user", but TF-IDF down-weights the
    common term)
  - Inverse document frequency captures rarity across the corpus
  - Cosine similarity is bounded [0, 1] and well-understood

CLI:
    predictive_failure.py "shopping cart with line items"
    predictive_failure.py "..." --threshold 0.6 --json
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from lib.base_script import bootstrap_runtime, setup_logging
bootstrap_runtime()

logger = setup_logging(__name__)


FAILURES_PATH = Path(".beads/failures.jsonl")

_STOPWORDS = {
    "add", "create", "build", "generate", "make", "with", "and", "or",
    "for", "the", "a", "an", "to", "of", "in", "on", "by", "as", "via",
    "feature", "module", "service", "api", "complete", "full", "ready",
    "into", "from", "use", "should", "must", "can", "will", "would",
    "this", "that", "these", "those", "is", "are", "be", "have", "has",
}


# ─── Data shapes ─────────────────────────────────────────────────────────────

@dataclass
class PredictionHit:
    bead_id: str
    similarity: float
    same_phase: bool
    advice: str
    summary: str
    severity: str = "info"   # info | warning | critical

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class PredictionReport:
    task: str
    total_beads: int
    method: str             # "tfidf" | "sentence-transformers" | "jaccard"
    hits: List[PredictionHit] = field(default_factory=list)
    warning_message: str = ""

    def to_dict(self) -> Dict:
        return {
            "task": self.task,
            "total_beads": self.total_beads,
            "method": self.method,
            "hits": [h.to_dict() for h in self.hits],
            "warning_message": self.warning_message,
        }


# ─── Tokenisation ───────────────────────────────────────────────────────────

def _tokenize(text: str) -> List[str]:
    raw = re.findall(r"[a-zA-Z_]{3,}", text.lower())
    return [t for t in raw if t not in _STOPWORDS]


# ─── TF-IDF cosine ──────────────────────────────────────────────────────────

def _term_frequencies(tokens: List[str]) -> Dict[str, float]:
    counts = Counter(tokens)
    total = sum(counts.values())
    if total == 0:
        return {}
    return {t: c / total for t, c in counts.items()}


def _inverse_doc_frequencies(documents: List[List[str]]) -> Dict[str, float]:
    n = len(documents)
    if n == 0:
        return {}
    doc_freq: Dict[str, int] = {}
    for doc in documents:
        seen = set(doc)
        for t in seen:
            doc_freq[t] = doc_freq.get(t, 0) + 1
    # Add 1 smoothing
    return {t: math.log((n + 1) / (df + 1)) + 1 for t, df in doc_freq.items()}


def _tfidf_vector(tokens: List[str],
                  idf: Dict[str, float]) -> Dict[str, float]:
    tf = _term_frequencies(tokens)
    return {t: weight * idf.get(t, 1.0) for t, weight in tf.items()}


def _cosine(v1: Dict[str, float], v2: Dict[str, float]) -> float:
    if not v1 or not v2:
        return 0.0
    keys = set(v1) | set(v2)
    dot = sum(v1.get(k, 0) * v2.get(k, 0) for k in keys)
    n1 = math.sqrt(sum(v * v for v in v1.values()))
    n2 = math.sqrt(sum(v * v for v in v2.values()))
    if n1 == 0 or n2 == 0:
        return 0.0
    return dot / (n1 * n2)


# ─── Optional sentence-transformers path ────────────────────────────────────

def _try_sentence_transformers():
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
        return SentenceTransformer
    except ImportError:
        return None


# ─── Severity classification ────────────────────────────────────────────────

def _advice_for(bead: Dict) -> str:
    diags = bead.get("diagnostics") or []
    blob = " ".join(
        d.get("message", "") if isinstance(d, dict) else str(d) for d in diags
    ).lower()
    if "401" in blob:
        return ("set test_contract.auth='none' to skip auth assertions, "
                "or generate auth middleware via service-author")
    if "next" in blob or "pagination" in blob:
        return ("set test_contract.pagination='list' OR generate a "
                "paginated envelope router")
    if "placeholder" in blob:
        return "run auto_patch with --resource-hint to scrub leaked placeholders"
    if "modulenotfounderror" in blob or "importerror" in blob:
        return "pass codebase_imports so the patcher rewrites default paths"
    if "nameerror" in blob and "self" in blob:
        return "switch generator from f-string composition to dedent + .format()"
    return "review the bead's diagnostics manually for context"


def _severity_for(similarity: float) -> str:
    if similarity >= 0.75:
        return "critical"
    if similarity >= 0.50:
        return "warning"
    return "info"


def _summarise_bead(bead: Dict) -> str:
    diags = bead.get("diagnostics") or []
    if not diags:
        return f"{bead.get('kind', 'failure')} (no diagnostics)"
    first = diags[0]
    msg = first.get("message") if isinstance(first, dict) else str(first)
    return f"{bead.get('kind', 'failure')}: {msg[:120]}"


# ─── Public entry ────────────────────────────────────────────────────────────

def predict(*, task: str, phase: Optional[str] = None,
            failures_path: Path,
            min_similarity: float = 0.3,
            limit: int = 5) -> PredictionReport:
    if not failures_path.exists():
        return PredictionReport(task=task, total_beads=0, method="none")

    beads: List[Dict] = []
    for line in failures_path.read_text(encoding="utf-8").splitlines():
        try:
            beads.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    if not beads:
        return PredictionReport(task=task, total_beads=0, method="tfidf")

    # Try sentence-transformers first; fall back to TF-IDF
    method = "tfidf"
    SentenceTransformerCls = _try_sentence_transformers()
    similarities: List[Tuple[Dict, float]] = []

    if SentenceTransformerCls is not None:
        method = "sentence-transformers"
        try:
            model = SentenceTransformerCls("all-MiniLM-L6-v2")
            current_emb = model.encode([task])[0]
            for bead in beads:
                bead_text = bead.get("task", "")
                if not bead_text:
                    continue
                bead_emb = model.encode([bead_text])[0]
                # cosine via dot/norm
                import numpy as np  # type: ignore
                cos = float(
                    np.dot(current_emb, bead_emb)
                    / (np.linalg.norm(current_emb) * np.linalg.norm(bead_emb))
                )
                similarities.append((bead, cos))
        except Exception as exc:
            logger.warning("sentence-transformers failed: %s; falling back", exc)
            method = "tfidf"
            similarities = []

    if not similarities:
        # TF-IDF path (always available)
        task_tokens = _tokenize(task)
        bead_token_lists = [_tokenize(b.get("task", "")) for b in beads]
        # Build IDF including current task as one doc
        all_docs = bead_token_lists + [task_tokens]
        idf = _inverse_doc_frequencies(all_docs)
        task_vec = _tfidf_vector(task_tokens, idf)
        for bead, tokens in zip(beads, bead_token_lists):
            bead_vec = _tfidf_vector(tokens, idf)
            similarities.append((bead, _cosine(task_vec, bead_vec)))

    hits: List[PredictionHit] = []
    for bead, sim in similarities:
        if sim < min_similarity:
            continue
        same_phase = phase is not None and bead.get("phase") == phase
        adjusted = min(1.0, sim + (0.05 if same_phase else 0))
        hits.append(PredictionHit(
            bead_id=bead.get("id", "<unknown>"),
            similarity=round(adjusted, 3),
            same_phase=same_phase,
            advice=_advice_for(bead),
            summary=_summarise_bead(bead),
            severity=_severity_for(adjusted),
        ))

    hits.sort(key=lambda h: h.similarity, reverse=True)
    hits = hits[:limit]

    warning = ""
    critical = [h for h in hits if h.severity == "critical"]
    if critical:
        warning = (f"⚠ {len(critical)} past failure(s) closely match this "
                   "task. Strongly consider the advice before generating.")
    elif any(h.severity == "warning" for h in hits):
        warning = ("Past failures show some similarity to this task — "
                   "review the suggested advice.")

    return PredictionReport(
        task=task, total_beads=len(beads), method=method,
        hits=hits, warning_message=warning,
    )


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Predict failures via cosine similarity against past beads"
    )
    parser.add_argument("task", nargs="+")
    parser.add_argument("--phase", default=None)
    parser.add_argument("--failures",
                        default=".beads/failures.jsonl")
    parser.add_argument("--repo-root", default=None)
    parser.add_argument("--threshold", type=float, default=0.3)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.repo_root:
        repo = Path(args.repo_root).resolve()
    else:
        cur = Path.cwd().resolve()
        while cur != cur.parent and not (cur / ".beads").exists():
            cur = cur.parent
        repo = cur

    report = predict(
        task=" ".join(args.task),
        phase=args.phase,
        failures_path=repo / args.failures,
        min_similarity=args.threshold,
        limit=args.limit,
    )

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
        return

    print(f"PREDICTIVE FAILURE SCAN")
    print(f"  Task:    {report.task}")
    print(f"  Method:  {report.method}")
    print(f"  Beads:   {report.total_beads}")
    if report.warning_message:
        print(f"  WARNING: {report.warning_message}")
    if not report.hits:
        print("  No similar past failures — proceed.")
        return
    for h in report.hits:
        marker = "🔴" if h.severity == "critical" else "🟡" if h.severity == "warning" else "ℹ️"
        print(f"  {marker} [{h.similarity:.2f}] {h.bead_id}")
        print(f"      {h.summary}")
        print(f"      advice: {h.advice}")


if __name__ == "__main__":
    main()
