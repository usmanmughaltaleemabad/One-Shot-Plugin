#!/usr/bin/env python3
"""
Auto Rule Extractor — v1.0.0  (closes part of the self-improvement gap)

Watches recent git history for fixes applied to GENERATED files (e.g.
in `/tmp/osp-*/` sandboxes, or under `<project>/<entity>/`), pattern-matches
each diff into a candidate ``auto_patch`` rule, and writes the proposal
to `.beads/proposed_patch_rules.jsonl`.

Each candidate rule has shape:

    {
        "id": "rule-20260518-001",
        "ts": "...",
        "trigger_pattern": "<regex matched in the original generated text>",
        "replacement_template": "<the substitution that fixed it>",
        "sample_files": ["product/router.py"],
        "diagnostic_signature": "...",
        "occurrences": 1,
        "promoted_to_auto_patch": false
    }

When the same trigger pattern recurs ≥ N times across distinct sandboxes,
the proposer surfaces it as "ready for promotion to auto_patch.py" — a
human (or another Claude session) reviews and merges it as a real rule
(rule code: P5 / P6 / ...). The extractor never edits auto_patch.py
directly; promotion is an explicit user action.

CLI:
    python auto_rule_extractor.py extract --since "1 hour ago"
    python auto_rule_extractor.py list-candidates
    python auto_rule_extractor.py promote --rule-id rule-20260518-001
"""

from __future__ import annotations

import argparse
import datetime as dt
import difflib
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional

from lib.base_script import bootstrap_runtime, setup_logging
bootstrap_runtime()

logger = setup_logging(__name__)

PROPOSALS_PATH = Path(".beads/proposed_patch_rules.jsonl")


# ─── Data shapes ─────────────────────────────────────────────────────────────

@dataclass
class RuleCandidate:
    id: str
    ts: str
    trigger_pattern: str
    replacement_template: str
    sample_files: List[str]
    diagnostic_signature: str = ""
    occurrences: int = 1
    promoted_to_auto_patch: bool = False

    def to_dict(self) -> Dict:
        return asdict(self)


# ─── Diff parsing ───────────────────────────────────────────────────────────

def _git_diff_files(repo_root: Path, since: Optional[str]) -> List[Dict]:
    """Return a list of {file, old_text, new_text} for files changed
    since the given git revision/time."""
    cmd_args = ["git", "-C", str(repo_root), "log",
                "--name-only", "--pretty=format:__COMMIT__%H"]
    if since:
        cmd_args.append(f"--since={since}")
    else:
        cmd_args.extend(["-n", "20"])
    try:
        proc = subprocess.run(cmd_args, capture_output=True, text=True,
                              encoding="utf-8", timeout=30)
    except FileNotFoundError:
        logger.warning("git not on PATH; cannot extract rules")
        return []
    if proc.returncode != 0:
        logger.warning("git log failed: %s", proc.stderr)
        return []

    files: List[Dict] = []
    current_commit: Optional[str] = None
    for line in proc.stdout.splitlines():
        if line.startswith("__COMMIT__"):
            current_commit = line[len("__COMMIT__"):]
            continue
        if not line.strip() or current_commit is None:
            continue
        # Filter to files plausibly under sandbox or generated patterns
        if not _is_candidate_file(line):
            continue
        old_text, new_text = _file_versions(repo_root, current_commit, line)
        if old_text is None or new_text is None or old_text == new_text:
            continue
        files.append({"commit": current_commit, "file": line,
                      "old_text": old_text, "new_text": new_text})
    return files


_CANDIDATE_PATTERNS = [
    re.compile(r".*/router\.py$"),
    re.compile(r".*/models\.py$"),
    re.compile(r".*/schemas\.py$"),
    re.compile(r"tests/test_.*\.py$"),
    re.compile(r".*/test_.*_api\.py$"),
    re.compile(r"osp-(verify|critic|sandbox)-.*"),
]


def _is_candidate_file(path: str) -> bool:
    path = path.replace("\\", "/")
    return any(pat.search(path) for pat in _CANDIDATE_PATTERNS)


def _file_versions(repo_root: Path, commit: str, path: str) -> tuple:
    """Return (old, new) — old = parent of commit, new = commit."""
    try:
        old = subprocess.run(
            ["git", "-C", str(repo_root), "show", f"{commit}^:{path}"],
            capture_output=True, text=True, encoding="utf-8", timeout=10,
        )
        new = subprocess.run(
            ["git", "-C", str(repo_root), "show", f"{commit}:{path}"],
            capture_output=True, text=True, encoding="utf-8", timeout=10,
        )
    except Exception as exc:
        logger.debug("git show failed for %s: %s", path, exc)
        return None, None
    if old.returncode != 0 or new.returncode != 0:
        return None, None
    return old.stdout, new.stdout


# ─── Pattern extraction ─────────────────────────────────────────────────────

def _diff_to_pattern(old_text: str, new_text: str) -> Optional[Dict]:
    """Reduce a file diff to a single-line trigger → replacement rule when
    the change is small and templatable.

    Strategy:
      * Use difflib to find a single contiguous changed region
      * If the change is one or two lines AND fits an "old_chunk →
        new_chunk" pattern, produce a regex from old_chunk and a
        template from new_chunk
      * Reject if the change is large (>5 lines) — those are not
        candidate auto_patch rules

    Returns ``{trigger_pattern, replacement_template}`` or None.
    """
    old_lines = old_text.splitlines(keepends=True)
    new_lines = new_text.splitlines(keepends=True)
    matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
    opcodes = matcher.get_opcodes()
    # Filter to replace operations only
    changes = [op for op in opcodes if op[0] in ("replace", "insert", "delete")]
    if len(changes) != 1:
        return None
    tag, i1, i2, j1, j2 = changes[0]
    old_chunk = "".join(old_lines[i1:i2]).strip()
    new_chunk = "".join(new_lines[j1:j2]).strip()
    if not old_chunk and not new_chunk:
        return None
    if len(old_chunk.splitlines()) > 5 or len(new_chunk.splitlines()) > 5:
        return None
    # Build a conservative regex: escape the old chunk, leave it literal
    trigger = re.escape(old_chunk)
    replacement = new_chunk
    return {"trigger_pattern": trigger, "replacement_template": replacement}


# ─── Persistence ────────────────────────────────────────────────────────────

def _load_proposals(path: Path) -> List[RuleCandidate]:
    if not path.exists():
        return []
    out: List[RuleCandidate] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            data = json.loads(line)
            out.append(RuleCandidate(**data))
        except (json.JSONDecodeError, TypeError):
            continue
    return out


def _save_proposals(path: Path, proposals: List[RuleCandidate]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "\n".join(json.dumps(p.to_dict()) for p in proposals)
    path.write_text(payload + ("\n" if payload else ""), encoding="utf-8")


def _hash_pattern(pattern: str) -> str:
    return hashlib.sha256(pattern.encode("utf-8")).hexdigest()[:12]


def _next_id(proposals: List[RuleCandidate]) -> str:
    today = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d")
    count = sum(1 for p in proposals if p.id.startswith(f"rule-{today}"))
    return f"rule-{today}-{count + 1:03d}"


# ─── Public entry ────────────────────────────────────────────────────────────

def extract(repo_root: Path, since: Optional[str] = None) -> List[RuleCandidate]:
    proposals_path = repo_root / PROPOSALS_PATH
    existing = _load_proposals(proposals_path)
    by_hash: Dict[str, RuleCandidate] = {
        _hash_pattern(p.trigger_pattern): p for p in existing
    }

    diffs = _git_diff_files(repo_root, since)
    for diff in diffs:
        rule = _diff_to_pattern(diff["old_text"], diff["new_text"])
        if not rule:
            continue
        h = _hash_pattern(rule["trigger_pattern"])
        if h in by_hash:
            existing_rule = by_hash[h]
            existing_rule.occurrences += 1
            if diff["file"] not in existing_rule.sample_files:
                existing_rule.sample_files.append(diff["file"])
        else:
            candidate = RuleCandidate(
                id=_next_id(list(by_hash.values())),
                ts=dt.datetime.now(dt.timezone.utc).replace(
                    microsecond=0, tzinfo=None).isoformat() + "Z",
                trigger_pattern=rule["trigger_pattern"],
                replacement_template=rule["replacement_template"],
                sample_files=[diff["file"]],
                diagnostic_signature="",
                occurrences=1,
                promoted_to_auto_patch=False,
            )
            by_hash[h] = candidate

    final = list(by_hash.values())
    _save_proposals(proposals_path, final)
    return final


def list_candidates(repo_root: Path) -> List[RuleCandidate]:
    return _load_proposals(repo_root / PROPOSALS_PATH)


def promote(repo_root: Path, rule_id: str) -> Optional[RuleCandidate]:
    proposals = _load_proposals(repo_root / PROPOSALS_PATH)
    for p in proposals:
        if p.id == rule_id:
            p.promoted_to_auto_patch = True
            _save_proposals(repo_root / PROPOSALS_PATH, proposals)
            return p
    return None


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Extract auto_patch rule candidates from git diffs of "
                    "generated/fix-up commits"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    sp_extract = sub.add_parser("extract", help="Scan recent commits")
    sp_extract.add_argument("--since", default="1 day ago",
                            help="Git --since value (e.g. '1 hour ago')")
    sp_extract.add_argument("--repo-root", default=".")
    sp_extract.add_argument("--json", action="store_true")

    sp_list = sub.add_parser("list-candidates", help="Print proposals")
    sp_list.add_argument("--repo-root", default=".")
    sp_list.add_argument("--json", action="store_true")
    sp_list.add_argument("--min-occurrences", type=int, default=1)

    sp_promote = sub.add_parser("promote", help="Mark a candidate as promoted")
    sp_promote.add_argument("--rule-id", required=True)
    sp_promote.add_argument("--repo-root", default=".")

    args = parser.parse_args()
    root = Path(args.repo_root).resolve()

    if args.cmd == "extract":
        candidates = extract(root, since=args.since)
        if args.json:
            print(json.dumps([c.to_dict() for c in candidates], indent=2))
        else:
            print(f"EXTRACTED {len(candidates)} CANDIDATE RULE(S) "
                  f"since '{args.since}'")
            for c in candidates:
                if c.promoted_to_auto_patch:
                    continue
                print(f"  {c.id}  occurrences={c.occurrences}  "
                      f"files={len(c.sample_files)}")
                print(f"    trigger: {c.trigger_pattern[:80]}…")
                print(f"    replace: {c.replacement_template[:80]}…")
        return

    if args.cmd == "list-candidates":
        candidates = list_candidates(root)
        filtered = [c for c in candidates
                    if c.occurrences >= args.min_occurrences]
        if args.json:
            print(json.dumps([c.to_dict() for c in filtered], indent=2))
        else:
            print(f"{len(filtered)} CANDIDATE(S) "
                  f"(occurrences >= {args.min_occurrences})")
            for c in filtered:
                tag = "[promoted]" if c.promoted_to_auto_patch else "[pending]"
                print(f"  {tag} {c.id}  ×{c.occurrences}  "
                      f"first seen {c.ts}")
        return

    if args.cmd == "promote":
        promoted = promote(root, args.rule_id)
        if promoted:
            print(f"marked {promoted.id} as promoted_to_auto_patch=true")
            print("now edit skills/one-shot-generator/scripts/auto_patch.py "
                  "to add a P5/P6/... rule using the trigger/replacement")
        else:
            print(f"no candidate with id {args.rule_id}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
