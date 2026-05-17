#!/usr/bin/env python3
"""
Self-Improvement Proposer — v0.9.0  (Tier 3 long-tail learning)

Reads ``.beads/failures.jsonl`` and proposes concrete SKILL.md / script
updates when the same class of failure recurs N times. The output is a
markdown PR-ready proposal a human (or another Claude session) can review.

The proposer is NEVER allowed to mutate code unsupervised. Its job is to
turn accumulated pain into a written suggestion.

CLI:
    python self_improvement_proposer.py --threshold 3 --out PROPOSALS.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional

from lib.base_script import bootstrap_runtime, setup_logging
bootstrap_runtime()

logger = setup_logging(__name__)


# ─── Pattern catalogue ───────────────────────────────────────────────────────

# Each pattern is (matcher, label, proposal-template).
_PATTERNS = [
    (
        re.compile(r"401", re.IGNORECASE),
        "test_router_auth_drift",
        "Generated tests assert HTTP 401 against routers with no auth wired. "
        "Update phase2 SKILL.md to set `test_contract.auth='none'` by default, "
        "or generate auth middleware when the spec requests it. The auto_patch "
        "P1 rule patches the symptom; the SKILL.md fix removes the cause.",
    ),
    (
        re.compile(r'"next"\s+in\s+response'),
        "pagination_envelope_drift",
        "Generated tests assert `\"next\" in response.json()` against routers that "
        "return a plain list. Either generate a paginated envelope on the router "
        "side OR change the test generator to match `test_contract.pagination='list'`.",
    ),
    (
        re.compile(r"placeholder"),
        "template_placeholder_leak",
        "Unsubstituted `{plural}` / `{resource}` placeholders are leaking into "
        "generated code. Add a CI smoke check that runs the generator on a "
        "fixture and greps for `{plural}` / `{resource}` in the output.",
    ),
    (
        re.compile(r"modulenotfounderror|importerror", re.IGNORECASE),
        "missing_module_import",
        "Generated code imports from modules that don't exist in the target "
        "project. The auto_patch P4 rule rewrites well-known names; extend the "
        "codebase_graph to detect more import points (router files, settings "
        "modules) so the rewrite covers them.",
    ),
    (
        re.compile(r"nameerror"),
        "f_string_template_self",
        "Python f-string template evaluates `self` at code-generation time. "
        "Switch the relevant generator from f-string composition to "
        "`textwrap.dedent` + `.format(**kwargs)` with `{{`/`}}` escapes for "
        "any literal braces.",
    ),
]


@dataclass
class ProposalEntry:
    pattern: str
    count: int
    sample_beads: List[str]
    proposal: str

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ProposalReport:
    threshold: int
    total_beads: int
    entries: List[ProposalEntry] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "threshold": self.threshold,
            "total_beads": self.total_beads,
            "entries": [e.to_dict() for e in self.entries],
        }


def _classify(bead: Dict) -> Optional[str]:
    diags = bead.get("diagnostics") or []
    blob = " ".join(
        (d.get("message", "") if isinstance(d, dict) else str(d))
        for d in diags
    )
    for matcher, label, _ in _PATTERNS:
        if matcher.search(blob):
            return label
    return None


def analyse(failures_path: Path, threshold: int = 3) -> ProposalReport:
    if not failures_path.exists():
        return ProposalReport(threshold=threshold, total_beads=0)
    counts: Counter = Counter()
    samples: Dict[str, List[str]] = defaultdict(list)
    total = 0
    for line in failures_path.read_text(encoding="utf-8").splitlines():
        try:
            bead = json.loads(line)
        except json.JSONDecodeError:
            continue
        total += 1
        label = _classify(bead)
        if not label:
            continue
        counts[label] += 1
        samples[label].append(bead.get("id", "<unknown>"))

    proposal_by_label = {label: text for _, label, text in _PATTERNS}
    entries = [
        ProposalEntry(
            pattern=label,
            count=count,
            sample_beads=samples[label][:5],
            proposal=proposal_by_label[label],
        )
        for label, count in counts.most_common()
        if count >= threshold
    ]
    return ProposalReport(threshold=threshold, total_beads=total, entries=entries)


def render_markdown(report: ProposalReport) -> str:
    lines = ["# Self-Improvement Proposals",
             "",
             f"_Analysed {report.total_beads} bead(s); reporting patterns "
             f"that recurred ≥{report.threshold} times._",
             ""]
    if not report.entries:
        lines.append("No recurring patterns detected — no proposals at this time.")
        return "\n".join(lines) + "\n"
    for entry in report.entries:
        lines.extend([
            f"## {entry.pattern}  ({entry.count} occurrences)",
            "",
            f"**Sample beads:** {', '.join(entry.sample_beads)}",
            "",
            entry.proposal,
            "",
        ])
    return "\n".join(lines) + "\n"


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Propose plugin improvements based on recurring beads"
    )
    parser.add_argument("--failures", default=".beads/failures.jsonl")
    parser.add_argument("--repo-root", default=None)
    parser.add_argument("--threshold", type=int, default=3)
    parser.add_argument("--out", default=None,
                        help="Write markdown report to this path (default: stdout)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.repo_root:
        repo_root = Path(args.repo_root).resolve()
    else:
        cur = Path.cwd().resolve()
        while cur != cur.parent and not (cur / ".beads").exists():
            cur = cur.parent
        repo_root = cur

    failures_path = repo_root / args.failures
    report = analyse(failures_path, threshold=args.threshold)

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        markdown = render_markdown(report)
        if args.out:
            Path(args.out).write_text(markdown, encoding="utf-8")
            print(f"wrote {args.out}", file=sys.stderr)
        else:
            print(markdown)


if __name__ == "__main__":
    main()
