#!/usr/bin/env python3
"""
Prompt Versioner — Tier 7A (Self-Healing Prompts)

Git-tracked semver lineage for every SKILL.md and agent .md. When
``self_improvement_proposer`` produces a proposal, this script splices
it as a markdown diff against the current version, tags the proposal,
and records the proposed change in ``.beads/prompt_history.jsonl``.

**Like ``promote_rule.py`` for auto_patch, this is propose-not-apply.**
The user reviews + merges the proposed diff manually.

Semver convention for prompt versions:
  - MAJOR: breaking change (renamed agent, removed tools)
  - MINOR: new capability added (e.g. new must_emit_endpoints)
  - PATCH: clarifications, anti-pattern additions

CLI:
    prompt_versioner.py current --skill one-shot-generate
    prompt_versioner.py propose --skill one-shot-generate --bump minor \
        --proposal /tmp/proposal.md
    prompt_versioner.py history --skill one-shot-generate
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from lib.base_script import bootstrap_runtime, setup_logging
bootstrap_runtime()

logger = setup_logging(__name__)


HISTORY_PATH = Path(".beads/prompt_history.jsonl")
SKILLS_DIR = Path("skills")
AGENTS_DIR = Path(".claude/agents")


@dataclass
class PromptVersion:
    target: str           # "skill:one-shot-generate" or "agent:architect"
    version: str          # "1.2.0"
    sha256: str           # of current file content
    last_modified: str    # ISO
    proposed_change: Optional[str] = None  # path to proposal markdown
    accepted: bool = False

    def to_dict(self) -> Dict:
        return asdict(self)


# ─── Helpers ────────────────────────────────────────────────────────────────

def _read_history(repo_root: Path) -> List[PromptVersion]:
    path = repo_root / HISTORY_PATH
    if not path.exists():
        return []
    out: List[PromptVersion] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            out.append(PromptVersion(**json.loads(line)))
        except (json.JSONDecodeError, TypeError):
            continue
    return out


def _append_history(repo_root: Path, entry: PromptVersion) -> None:
    path = repo_root / HISTORY_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(entry.to_dict()) + "\n")


def _resolve_target(repo_root: Path, target_kind: str,
                    name: str) -> Optional[Path]:
    if target_kind == "skill":
        candidate = repo_root / SKILLS_DIR / name / "SKILL.md"
        if candidate.exists():
            return candidate
    if target_kind == "agent":
        candidate = repo_root / AGENTS_DIR / f"{name}.md"
        if candidate.exists():
            return candidate
    return None


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def _bump(version: str, kind: str) -> str:
    """Bump semver."""
    parts = version.split(".")
    if len(parts) != 3:
        return "1.0.0"
    major, minor, patch = (int(p) for p in parts)
    if kind == "major":
        return f"{major + 1}.0.0"
    if kind == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def _latest_version_for_target(history: List[PromptVersion],
                               target: str) -> str:
    relevant = [h for h in history if h.target == target]
    if not relevant:
        return "1.0.0"
    return relevant[-1].version


# ─── Public entry ────────────────────────────────────────────────────────────

def get_current(repo_root: Path, kind: str, name: str) -> Optional[Dict]:
    path = _resolve_target(repo_root, kind, name)
    if not path:
        return None
    history = _read_history(repo_root)
    target = f"{kind}:{name}"
    return {
        "target": target,
        "file": str(path.relative_to(repo_root)).replace("\\", "/"),
        "current_version": _latest_version_for_target(history, target),
        "current_sha256": _hash_file(path),
        "history_entries": sum(1 for h in history if h.target == target),
    }


def propose_change(repo_root: Path, *, kind: str, name: str,
                   bump: str, proposal_path: Path,
                   notes: Optional[str] = None) -> PromptVersion:
    path = _resolve_target(repo_root, kind, name)
    if path is None:
        raise FileNotFoundError(f"{kind}:{name} not found")
    if not proposal_path.exists():
        raise FileNotFoundError(f"proposal not found: {proposal_path}")
    target = f"{kind}:{name}"
    history = _read_history(repo_root)
    current_version = _latest_version_for_target(history, target)
    new_version = _bump(current_version, bump)

    entry = PromptVersion(
        target=target,
        version=new_version,
        sha256=_hash_file(path),
        last_modified=dt.datetime.now(dt.timezone.utc).replace(
            microsecond=0, tzinfo=None).isoformat() + "Z",
        proposed_change=str(proposal_path),
        accepted=False,
    )
    _append_history(repo_root, entry)
    logger.info("recorded proposal: %s → %s", target, new_version)
    return entry


def list_history(repo_root: Path, kind: Optional[str] = None,
                 name: Optional[str] = None) -> List[Dict]:
    history = _read_history(repo_root)
    if kind and name:
        target = f"{kind}:{name}"
        history = [h for h in history if h.target == target]
    elif kind:
        history = [h for h in history if h.target.startswith(f"{kind}:")]
    return [h.to_dict() for h in history]


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Semver-track prompt (skill / agent .md) versions"
    )
    parser.add_argument("--repo-root", default=".")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sp_cur = sub.add_parser("current")
    sp_cur.add_argument("--kind", choices=["skill", "agent"], required=True)
    sp_cur.add_argument("--name", required=True)

    sp_pro = sub.add_parser("propose")
    sp_pro.add_argument("--kind", choices=["skill", "agent"], required=True)
    sp_pro.add_argument("--name", required=True)
    sp_pro.add_argument("--bump", choices=["major", "minor", "patch"],
                        default="patch")
    sp_pro.add_argument("--proposal", required=True,
                        help="Path to a markdown file with the proposed diff/note")
    sp_pro.add_argument("--notes", default=None)

    sp_his = sub.add_parser("history")
    sp_his.add_argument("--kind", choices=["skill", "agent"], default=None)
    sp_his.add_argument("--name", default=None)

    args = parser.parse_args()
    repo = Path(args.repo_root).resolve()

    if args.cmd == "current":
        info = get_current(repo, args.kind, args.name)
        if info is None:
            print(f"target not found: {args.kind}:{args.name}", file=sys.stderr)
            sys.exit(1)
        print(json.dumps(info, indent=2))
        return

    if args.cmd == "propose":
        entry = propose_change(
            repo, kind=args.kind, name=args.name,
            bump=args.bump, proposal_path=Path(args.proposal),
            notes=args.notes,
        )
        print(json.dumps(entry.to_dict(), indent=2))
        return

    if args.cmd == "history":
        entries = list_history(repo, kind=args.kind, name=args.name)
        print(json.dumps(entries, indent=2))
        return


if __name__ == "__main__":
    main()
