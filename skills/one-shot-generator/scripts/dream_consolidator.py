#!/usr/bin/env python3
"""
Dream Consolidator — v1.0.0

Offline self-improvement pass inspired by "memory consolidation during
sleep" research. Runs after a batch of /one-shot generations to:

1. Mine recurring failure patterns from .beads/failures.jsonl
2. Validate which hardcoded advice actually led to downstream success
   (by correlating failure → retry-success sequences in decisions.jsonl)
3. Write data-driven advice entries to .beads/curriculum_advice.jsonl
   (beads_curriculum.py loads these at runtime, layered over builtins)
4. Identify body-hint gaps: error clusters that no existing body hint
   covers (written to .beads/hint_gap_proposals.jsonl for human review)
5. Prune stale beads older than 90 days with low recurrence (≥ 0 recent
   hits required to survive — beads that never fire are noise)

CLI:
    python dream_consolidator.py                      # default run
    python dream_consolidator.py --min-recurrence 2   # only act on patterns
                                                       # seen ≥ 2 times
    python dream_consolidator.py --prune-age-days 60  # more aggressive prune
    python dream_consolidator.py --dry-run             # report only, no writes
    python dream_consolidator.py --json                # machine-readable output
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from lib.base_script import bootstrap_runtime, setup_logging
bootstrap_runtime()

logger = setup_logging(__name__)

STOPWORDS = {
    "add", "create", "build", "generate", "make", "with", "and", "or",
    "for", "the", "a", "an", "to", "of", "in", "on", "by", "as", "via",
    "error", "failed", "failure", "exception", "traceback", "line",
}

# ─── Data structures ──────────────────────────────────────────────────────────

@dataclass
class AdviceEntry:
    """A data-driven advice entry derived from real failure patterns."""
    pattern: str          # regex or keyword cluster label
    advice: str
    confidence: float     # 0.0–1.0; boosted by validation evidence
    hit_count: int        # how many times this pattern was seen
    validated: bool       # True if a retry-success followed this advice
    source: str           # "dream_consolidator vN"
    last_seen: str        # ISO timestamp

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class HintGapProposal:
    """A cluster of failures that no existing body hint covers."""
    cluster_label: str
    representative_messages: List[str]
    occurrence_count: int
    suggested_hint_category: str
    source: str = "dream_consolidator"

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class PrunedBead:
    bead_id: str
    age_days: int
    reason: str

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class DreamReport:
    run_at: str
    failures_analysed: int
    patterns_found: int
    advice_written: int
    hint_gaps_proposed: int
    beads_pruned: int
    advice_entries: List[AdviceEntry] = field(default_factory=list)
    hint_gaps: List[HintGapProposal] = field(default_factory=list)
    pruned_beads: List[PrunedBead] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "run_at": self.run_at,
            "failures_analysed": self.failures_analysed,
            "patterns_found": self.patterns_found,
            "advice_written": self.advice_written,
            "hint_gaps_proposed": self.hint_gaps_proposed,
            "beads_pruned": self.beads_pruned,
            "advice_entries": [a.to_dict() for a in self.advice_entries],
            "hint_gaps": [h.to_dict() for h in self.hint_gaps],
            "pruned_beads": [p.to_dict() for p in self.pruned_beads],
        }


# ─── Error signature extraction ───────────────────────────────────────────────

# Ordered list of (label, regex) patterns. First match wins.
_SIGNATURE_PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("auth_401",         re.compile(r'\b401\b')),
    ("pagination_drift", re.compile(r'\bpaginat|\"next\"', re.I)),
    ("placeholder_leak", re.compile(r'\bplaceholder\b', re.I)),
    ("import_error",     re.compile(r'\b(modulenotfounderror|importerror)\b', re.I)),
    ("sql_injection",    re.compile(r'\bsql.inject|parameteriz', re.I)),
    ("timeout",          re.compile(r'\btimeout|timed.out\b', re.I)),
    ("null_reference",   re.compile(r'\bnull.pointer|nonetype.*has no attr|attributeerror\b', re.I)),
    ("schema_mismatch",  re.compile(r'\bschema|serializ|validat.*error\b', re.I)),
    ("migration_fail",   re.compile(r'\bmigrat.*fail|alembic|flyway\b', re.I)),
    ("test_contract",    re.compile(r'\btest.*contract|contract.*test\b', re.I)),
    ("async_missing",    re.compile(r'\bawait.*outside|async.*def.*missing\b', re.I)),
]

_BUILTIN_ADVICE: Dict[str, str] = {
    "auth_401": (
        "test/router contract drift — set test_contract.auth='none' "
        "in spec.json if no auth middleware is generated"
    ),
    "pagination_drift": (
        "pagination contract drift — set test_contract.pagination='list' "
        "or generate a paginated envelope on the router side"
    ),
    "placeholder_leak": (
        "template placeholder leaked — run auto_patch with --resource-hint"
    ),
    "import_error": (
        "missing module — pass codebase_imports so the patcher can rewrite default paths"
    ),
    "sql_injection": (
        "SQL injection risk — ensure all queries use parameterized statements; "
        "add 'no_raw_sql' to spec.json constraints"
    ),
    "timeout": (
        "operation timed out — add timeout= kwarg and circuit breaker; "
        "see body_hints COMMON_CONTRACTS timeout section"
    ),
    "null_reference": (
        "null/None dereference — add None-guard at boundary; "
        "architect should emit 'null_safety: strict' in spec.json"
    ),
    "schema_mismatch": (
        "schema/serializer mismatch — re-run extract_domain_model and "
        "confirm FK columns in spec.json match actual model fields"
    ),
    "migration_fail": (
        "migration failure — ensure Alembic/Flyway env vars are set; "
        "use --generate-migration flag to auto-create the migration"
    ),
    "test_contract": (
        "test contract drift — check spec.json test_contract block; "
        "run consistency_checker.py before ship"
    ),
    "async_missing": (
        "async/await mismatch — architect must set 'async_mode: true' in spec.json "
        "when FastAPI/async handlers are detected"
    ),
}


def _extract_signature(messages: str) -> Optional[str]:
    for label, pat in _SIGNATURE_PATTERNS:
        if pat.search(messages):
            return label
    return None


def _tokenize(text: str) -> List[str]:
    return [t for t in re.findall(r"[a-zA-Z_]{3,}", text.lower())
            if t not in STOPWORDS]


# ─── I/O helpers ──────────────────────────────────────────────────────────────

def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def _write_jsonl(path: Path, records: List[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fp:
        for r in records:
            fp.write(json.dumps(r if isinstance(r, dict) else r.to_dict()) + "\n")


def _append_jsonl(path: Path, record: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(record) + "\n")


# ─── Core consolidation logic ─────────────────────────────────────────────────

def _collect_failure_messages(bead: Dict) -> str:
    diags = bead.get("diagnostics", []) or []
    parts = []
    for d in diags:
        if isinstance(d, dict):
            parts.append(d.get("message", ""))
        else:
            parts.append(str(d))
    return " ".join(parts)


def _days_old(ts_str: Optional[str]) -> int:
    if not ts_str:
        return 0
    try:
        ts = dt.datetime.fromisoformat(ts_str.rstrip("Z"))
        return max(0, (dt.datetime.now() - ts).days)
    except ValueError:
        return 0


def mine_patterns(
    failures: List[Dict],
    min_recurrence: int,
) -> Dict[str, List[Dict]]:
    """Group failures by error signature; return groups with ≥ min_recurrence entries."""
    groups: Dict[str, List[Dict]] = defaultdict(list)
    for bead in failures:
        msg = _collect_failure_messages(bead)
        sig = _extract_signature(msg)
        if sig:
            groups[sig].append(bead)
    return {sig: beads for sig, beads in groups.items()
            if len(beads) >= min_recurrence}


def validate_advice(
    patterns: Dict[str, List[Dict]],
    decisions: List[Dict],
) -> Dict[str, bool]:
    """
    For each pattern, check whether a failure with that signature was
    followed by a success decision on the same task (within 24h).
    Returns {signature: was_validated}.
    """
    # Build a set of (task_prefix, success_ts) from decisions
    success_tasks: List[Tuple[str, dt.datetime]] = []
    for d in decisions:
        if d.get("verdict") in ("SHIP", "PASS", "success", "shipped"):
            task = d.get("task", "")
            ts_str = d.get("ts") or d.get("timestamp")
            try:
                ts = dt.datetime.fromisoformat((ts_str or "").rstrip("Z"))
                success_tasks.append((_tokenize(task), ts))
            except (ValueError, TypeError):
                continue

    validated: Dict[str, bool] = {}
    for sig, beads in patterns.items():
        found = False
        for bead in beads:
            bead_tokens = set(_tokenize(bead.get("task", "")))
            bead_ts_str = bead.get("date") or bead.get("ts")
            try:
                bead_ts = dt.datetime.fromisoformat((bead_ts_str or "").rstrip("Z"))
            except (ValueError, TypeError):
                continue
            for succ_tokens, succ_ts in success_tasks:
                # Same task family (≥ 2 token overlap) + success came after failure
                overlap = len(bead_tokens & set(succ_tokens))
                delta = (succ_ts - bead_ts).total_seconds()
                if overlap >= 2 and 0 < delta < 86_400:
                    found = True
                    break
            if found:
                break
        validated[sig] = found
    return validated


def build_advice_entries(
    patterns: Dict[str, List[Dict]],
    validated: Dict[str, bool],
    now_iso: str,
) -> List[AdviceEntry]:
    entries = []
    for sig, beads in patterns.items():
        base_advice = _BUILTIN_ADVICE.get(sig, f"recurring {sig} — review diagnostics")
        is_validated = validated.get(sig, False)
        # Confidence: base 0.5, +0.2 per occurrence above minimum, +0.2 if validated
        confidence = min(1.0, 0.5 + 0.05 * len(beads) + (0.2 if is_validated else 0))
        entries.append(AdviceEntry(
            pattern=sig,
            advice=base_advice,
            confidence=round(confidence, 2),
            hit_count=len(beads),
            validated=is_validated,
            source="dream_consolidator v1.0",
            last_seen=now_iso,
        ))
    entries.sort(key=lambda e: e.confidence, reverse=True)
    return entries


def detect_hint_gaps(
    failures: List[Dict],
    min_cluster_size: int = 2,
) -> List[HintGapProposal]:
    """Find failure clusters whose signature is UNKNOWN (no pattern matched)."""
    unmatched: List[Dict] = []
    for bead in failures:
        msg = _collect_failure_messages(bead)
        if _extract_signature(msg) is None and msg.strip():
            unmatched.append(bead)

    if not unmatched:
        return []

    # Simple token-frequency clustering: group by most-common non-stop token
    token_to_beads: Dict[str, List[Dict]] = defaultdict(list)
    for bead in unmatched:
        msg = _collect_failure_messages(bead)
        tokens = _tokenize(msg)
        if tokens:
            token_to_beads[tokens[0]].append(bead)

    proposals = []
    for token, beads in token_to_beads.items():
        if len(beads) < min_cluster_size:
            continue
        reps = list({_collect_failure_messages(b)[:120] for b in beads[:3]})
        proposals.append(HintGapProposal(
            cluster_label=token,
            representative_messages=reps,
            occurrence_count=len(beads),
            suggested_hint_category=f"UNKNOWN_{token.upper()}",
        ))
    proposals.sort(key=lambda p: p.occurrence_count, reverse=True)
    return proposals


def prune_stale_beads(
    failures: List[Dict],
    age_days: int,
    patterns: Dict[str, List[Dict]],
) -> Tuple[List[Dict], List[PrunedBead]]:
    """
    Remove beads that are:
    - Older than age_days, AND
    - Whose signature hasn't recurred recently (not in any active pattern)
    Returns (survivors, pruned_list).
    """
    active_ids = {b.get("id") for beads in patterns.values() for b in beads}
    survivors, pruned = [], []
    for bead in failures:
        age = _days_old(bead.get("date") or bead.get("ts"))
        bead_id = bead.get("id", "<unknown>")
        if age > age_days and bead_id not in active_ids:
            pruned.append(PrunedBead(
                bead_id=bead_id,
                age_days=age,
                reason=f"stale: {age}d old, no recent recurrence",
            ))
        else:
            survivors.append(bead)
    return survivors, pruned


# ─── Main consolidation entrypoint ───────────────────────────────────────────

def consolidate(
    repo_root: Path,
    min_recurrence: int = 2,
    prune_age_days: int = 90,
    dry_run: bool = False,
) -> DreamReport:
    now_iso = dt.datetime.now().isoformat(timespec="seconds")

    failures_path = repo_root / ".beads" / "failures.jsonl"
    decisions_path = repo_root / ".beads" / "decisions.jsonl"
    advice_path = repo_root / ".beads" / "curriculum_advice.jsonl"
    hint_gaps_path = repo_root / ".beads" / "hint_gap_proposals.jsonl"
    dream_log_path = repo_root / ".beads" / "dream_report.jsonl"

    failures = _load_jsonl(failures_path)
    decisions = _load_jsonl(decisions_path)

    # 1. Mine recurring error patterns
    patterns = mine_patterns(failures, min_recurrence=min_recurrence)

    # 2. Validate which advice led to subsequent success
    validated = validate_advice(patterns, decisions)

    # 3. Build advice entries
    advice_entries = build_advice_entries(patterns, validated, now_iso)

    # 4. Detect unclassified failure clusters (hint gaps)
    hint_gaps = detect_hint_gaps(failures)

    # 5. Prune stale beads
    survivors, pruned = prune_stale_beads(failures, prune_age_days, patterns)

    report = DreamReport(
        run_at=now_iso,
        failures_analysed=len(failures),
        patterns_found=len(patterns),
        advice_written=len(advice_entries),
        hint_gaps_proposed=len(hint_gaps),
        beads_pruned=len(pruned),
        advice_entries=advice_entries,
        hint_gaps=hint_gaps,
        pruned_beads=pruned,
    )

    if not dry_run:
        if advice_entries:
            _write_jsonl(advice_path, advice_entries)
            logger.info("wrote %d advice entries → %s", len(advice_entries), advice_path)
        if hint_gaps:
            _write_jsonl(hint_gaps_path, hint_gaps)
            logger.info("wrote %d hint gap proposals → %s", len(hint_gaps), hint_gaps_path)
        if pruned:
            _write_jsonl(failures_path, survivors)
            logger.info("pruned %d stale beads from %s", len(pruned), failures_path)
        _append_jsonl(dream_log_path, report.to_dict())

    return report


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Offline dream consolidation: mine failure patterns → update curriculum"
    )
    parser.add_argument(
        "--min-recurrence", type=int, default=2,
        help="Min times a pattern must appear to generate advice (default: 2)"
    )
    parser.add_argument(
        "--prune-age-days", type=int, default=90,
        help="Prune beads older than N days with no recent recurrence (default: 90)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Report findings without writing any files"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Emit JSON report to stdout"
    )
    parser.add_argument(
        "--repo-root", default=None,
        help="Repo root (default: walk up from cwd to find .beads/)"
    )
    args = parser.parse_args()

    if args.repo_root:
        repo_root = Path(args.repo_root).resolve()
    else:
        cur = Path.cwd().resolve()
        while cur != cur.parent and not (cur / ".beads").exists():
            cur = cur.parent
        repo_root = cur

    report = consolidate(
        repo_root=repo_root,
        min_recurrence=args.min_recurrence,
        prune_age_days=args.prune_age_days,
        dry_run=args.dry_run,
    )

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
        return

    tag = "[DRY-RUN] " if args.dry_run else ""
    print(f"{tag}DREAM CONSOLIDATION — {report.run_at}")
    print(f"  failures analysed  : {report.failures_analysed}")
    print(f"  patterns found     : {report.patterns_found}")
    print(f"  advice entries     : {report.advice_written}")
    print(f"  hint gap proposals : {report.hint_gaps_proposed}")
    print(f"  stale beads pruned : {report.beads_pruned}")

    if report.advice_entries:
        print("\nTOP ADVICE ENTRIES:")
        for a in report.advice_entries[:5]:
            val = "✓ validated" if a.validated else "  unvalidated"
            print(f"  [{a.confidence:.2f} conf, {a.hit_count}x, {val}] {a.pattern}")
            print(f"    → {a.advice}")

    if report.hint_gaps:
        print("\nHINT GAPS (no body hint covers these):")
        for g in report.hint_gaps[:3]:
            print(f"  [{g.occurrence_count}x] {g.cluster_label}")
            for msg in g.representative_messages[:2]:
                print(f"    e.g. {msg}")

    if report.pruned_beads:
        print(f"\nPRUNED {len(report.pruned_beads)} STALE BEADS")


if __name__ == "__main__":
    main()
