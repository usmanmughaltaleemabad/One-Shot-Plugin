#!/usr/bin/env python3
"""
Autonomy Level Tracker — Tier 7A

Maps Anthropic's 5-level autonomy framework onto this plugin's
operations. Each level relaxes (or tightens) the user-approval gates
the SKILL.md inserts at critical points. Session count drives
suggested level-ups — users who run 20+ clean generations get
offered the next level.

Levels (from Anthropic's published taxonomy):

  operator     User explicitly approves every action.
               Default for first 5 sessions. No --apply auto-runs.
               Migrations always asked.

  collaborator Auto-approve low-risk reads + dry-runs.
               --apply still asked. Migrations still asked.
               Recommended after 5+ clean sessions.

  consultant   Auto-approve --apply on non-migration wires.
               Migrations still asked. Cost-budget gate enforced.
               Recommended after 20+ clean sessions.

  approver     Auto-approve everything except destructive ops
               (delete data, drop tables, rm -rf).
               Recommended after 50+ clean sessions OR explicit opt-in.

  observer     Full autonomy. Plugin reports what it did,
               not what it's about to do. Requires explicit opt-in;
               never auto-suggested.

Session counting:

  - .beads/sessions.jsonl records each /one-shot invocation
  - A session is "clean" if critic returned SHIPPED on first iteration
  - autonomy_level.suggest_next() looks at last 10 sessions and
    proposes a level-up if 80%+ were clean

CLI:
    autonomy_level.py get-level
    autonomy_level.py record-session --result shipped --duration-ms 12345
    autonomy_level.py suggest-next
    autonomy_level.py set-level --level collaborator
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional

from lib.base_script import bootstrap_runtime, setup_logging
bootstrap_runtime()

logger = setup_logging(__name__)


LEVELS = ["operator", "collaborator", "consultant", "approver", "observer"]
SESSIONS_PATH = Path(".beads/sessions.jsonl")
CONFIG_PATH = Path(".beads/autonomy.json")


# Per-level gate configuration
LEVEL_GATES = {
    "operator": {
        "auto_approve_dry_run": False,
        "auto_approve_apply": False,
        "auto_approve_migrations": False,
        "auto_approve_critic_loop": False,
        "destructive_ops_require_yes": True,
    },
    "collaborator": {
        "auto_approve_dry_run": True,
        "auto_approve_apply": False,
        "auto_approve_migrations": False,
        "auto_approve_critic_loop": False,
        "destructive_ops_require_yes": True,
    },
    "consultant": {
        "auto_approve_dry_run": True,
        "auto_approve_apply": True,
        "auto_approve_migrations": False,
        "auto_approve_critic_loop": True,
        "destructive_ops_require_yes": True,
    },
    "approver": {
        "auto_approve_dry_run": True,
        "auto_approve_apply": True,
        "auto_approve_migrations": True,
        "auto_approve_critic_loop": True,
        "destructive_ops_require_yes": True,
    },
    "observer": {
        "auto_approve_dry_run": True,
        "auto_approve_apply": True,
        "auto_approve_migrations": True,
        "auto_approve_critic_loop": True,
        "destructive_ops_require_yes": False,
    },
}

# Promotion thresholds: (next_level, min_clean_sessions, clean_rate_threshold)
PROMOTION_RULES = [
    ("collaborator", 5, 0.80),
    ("consultant", 20, 0.80),
    ("approver", 50, 0.85),
    # observer is opt-in only
]


@dataclass
class SessionRecord:
    ts: str
    result: str            # shipped | looped | escalated | aborted
    iterations: int
    duration_ms: int
    task_keywords: List[str] = field(default_factory=list)
    cost_usd: Optional[float] = None

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class AutonomyConfig:
    current_level: str = "operator"
    last_promoted_at: Optional[str] = None
    explicit_lock: bool = False     # if True, never auto-suggest level-ups

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class SuggestionReport:
    current_level: str
    suggested_level: Optional[str]
    recent_sessions: int
    clean_rate: float
    reason: str

    def to_dict(self) -> Dict:
        return asdict(self)


# ─── Persistence ────────────────────────────────────────────────────────────

def _config_path(repo_root: Path) -> Path:
    return repo_root / CONFIG_PATH


def _sessions_path(repo_root: Path) -> Path:
    return repo_root / SESSIONS_PATH


def load_config(repo_root: Path) -> AutonomyConfig:
    path = _config_path(repo_root)
    if not path.exists():
        return AutonomyConfig()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return AutonomyConfig(**data)
    except (json.JSONDecodeError, TypeError):
        return AutonomyConfig()


def save_config(repo_root: Path, config: AutonomyConfig) -> None:
    path = _config_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config.to_dict(), indent=2), encoding="utf-8")


def record_session(repo_root: Path, record: SessionRecord) -> None:
    path = _sessions_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(record.to_dict()) + "\n")


def load_sessions(repo_root: Path,
                  limit: Optional[int] = None) -> List[SessionRecord]:
    path = _sessions_path(repo_root)
    if not path.exists():
        return []
    out: List[SessionRecord] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            data = json.loads(line)
            out.append(SessionRecord(**data))
        except (json.JSONDecodeError, TypeError):
            continue
    if limit:
        out = out[-limit:]
    return out


# ─── Logic ──────────────────────────────────────────────────────────────────

def gates_for_level(level: str) -> Dict[str, bool]:
    return dict(LEVEL_GATES.get(level, LEVEL_GATES["operator"]))


def suggest_next_level(repo_root: Path,
                       lookback: int = 10) -> SuggestionReport:
    config = load_config(repo_root)
    sessions = load_sessions(repo_root)
    recent = sessions[-lookback:] if sessions else []
    clean = sum(1 for s in recent if s.result == "shipped" and s.iterations == 1)
    rate = (clean / len(recent)) if recent else 0.0

    if config.explicit_lock:
        return SuggestionReport(
            current_level=config.current_level,
            suggested_level=None,
            recent_sessions=len(recent),
            clean_rate=round(rate, 3),
            reason="autonomy level explicitly locked; no suggestion",
        )

    current_idx = LEVELS.index(config.current_level) \
        if config.current_level in LEVELS else 0
    suggested: Optional[str] = None
    reason = "not enough clean sessions for next level"

    for level, min_count, threshold in PROMOTION_RULES:
        next_idx = LEVELS.index(level)
        if next_idx <= current_idx:
            continue
        total_clean_lifetime = sum(
            1 for s in sessions if s.result == "shipped" and s.iterations == 1
        )
        if total_clean_lifetime >= min_count and rate >= threshold:
            suggested = level
            reason = (f"{total_clean_lifetime} lifetime clean sessions "
                      f"+ {rate:.0%} recent clean rate "
                      f">= threshold {threshold:.0%}")
            break

    return SuggestionReport(
        current_level=config.current_level,
        suggested_level=suggested,
        recent_sessions=len(recent),
        clean_rate=round(rate, 3),
        reason=reason,
    )


def set_level(repo_root: Path, level: str,
              lock: bool = False) -> AutonomyConfig:
    if level not in LEVELS:
        raise ValueError(f"unknown autonomy level: {level}. options: {LEVELS}")
    config = load_config(repo_root)
    config.current_level = level
    config.last_promoted_at = dt.datetime.now(dt.timezone.utc).replace(
        microsecond=0, tzinfo=None).isoformat() + "Z"
    config.explicit_lock = lock
    save_config(repo_root, config)
    return config


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Manage autonomy level + session tracking"
    )
    parser.add_argument("--repo-root", default=".")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("get-level", help="Print current level + gates")

    sp_rec = sub.add_parser("record-session", help="Record a /one-shot run")
    sp_rec.add_argument("--result", required=True,
                        choices=["shipped", "looped", "escalated", "aborted"])
    sp_rec.add_argument("--iterations", type=int, default=1)
    sp_rec.add_argument("--duration-ms", type=int, default=0)
    sp_rec.add_argument("--cost-usd", type=float, default=None)
    sp_rec.add_argument("--task-keywords", nargs="*", default=[])

    sub.add_parser("suggest-next", help="Suggest next level based on history")

    sp_set = sub.add_parser("set-level", help="Manually set the level")
    sp_set.add_argument("--level", required=True, choices=LEVELS)
    sp_set.add_argument("--lock", action="store_true",
                        help="Disable auto-suggestion of further level-ups")

    args = parser.parse_args()
    repo = Path(args.repo_root).resolve()

    if args.cmd == "get-level":
        config = load_config(repo)
        gates = gates_for_level(config.current_level)
        print(json.dumps({
            "current_level": config.current_level,
            "explicit_lock": config.explicit_lock,
            "last_promoted_at": config.last_promoted_at,
            "gates": gates,
        }, indent=2))
        return

    if args.cmd == "record-session":
        record_session(repo, SessionRecord(
            ts=dt.datetime.now(dt.timezone.utc).replace(
                microsecond=0, tzinfo=None).isoformat() + "Z",
            result=args.result,
            iterations=args.iterations,
            duration_ms=args.duration_ms,
            cost_usd=args.cost_usd,
            task_keywords=list(args.task_keywords),
        ))
        suggestion = suggest_next_level(repo)
        print(json.dumps({
            "recorded": True,
            "suggestion": suggestion.to_dict(),
        }, indent=2))
        return

    if args.cmd == "suggest-next":
        suggestion = suggest_next_level(repo)
        print(json.dumps(suggestion.to_dict(), indent=2))
        return

    if args.cmd == "set-level":
        config = set_level(repo, args.level, lock=args.lock)
        print(json.dumps({
            "current_level": config.current_level,
            "explicit_lock": config.explicit_lock,
            "gates": gates_for_level(config.current_level),
        }, indent=2))
        return


if __name__ == "__main__":
    main()
