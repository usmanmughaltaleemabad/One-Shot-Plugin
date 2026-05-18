#!/usr/bin/env python3
"""
Learnings Hub — Tier 9 (Cross-Agent Learning + Capability Marketplace)

Append-only log of "agent X worked well for task Y" observations. After
enough learnings accumulate, the curator + discovery score agents using
both keyword overlap AND empirical track record.

Storage: ``.claude/registry/learnings.jsonl``

Each learning is shaped:

    {
        "ts": "2026-05-18T03:00:00Z",
        "agent_id": "claude-code/code-reviewer",
        "task_keywords": ["review", "code", "security"],
        "outcome": "succeeded",
        "duration_ms": 12000,
        "cost_usd": 0.06,
        "notes": "caught a SQL injection in the auth endpoint"
    }

The discovery script consumes this log to boost agents with proven
track record. Specifically:

    rating(agent) = 0.5 * keyword_overlap
                  + 0.3 * past_success_rate
                  + 0.2 * recency_factor

Outcomes feed back into agent_discovery's ranking, turning the
registry from a static list into a self-improving marketplace.

CLI:
    learnings_hub.py record --agent <id> --outcome succeeded \\
        --task-keywords <words> --duration-ms <ms> [--cost-usd <usd>]
    learnings_hub.py rate --agent <id>
    learnings_hub.py top-agents --limit 10
    learnings_hub.py export-anonymized  -- for sharing learnings
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import statistics
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional

from lib.base_script import bootstrap_runtime, setup_logging
bootstrap_runtime()

logger = setup_logging(__name__)


LEARNINGS_PATH = Path(".claude/registry/learnings.jsonl")


@dataclass
class Learning:
    ts: str
    agent_id: str
    task_keywords: List[str]
    outcome: str           # succeeded | failed | inconclusive
    duration_ms: int = 0
    cost_usd: Optional[float] = None
    notes: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class AgentRating:
    agent_id: str
    sample_count: int
    success_rate: float
    avg_duration_ms: float
    avg_cost_usd: Optional[float]
    last_used_at: Optional[str]
    recency_factor: float
    overall_rating: float    # 0-1 composite

    def to_dict(self) -> Dict:
        return asdict(self)


# ─── Persistence ────────────────────────────────────────────────────────────

def _load(repo_root: Path) -> List[Learning]:
    path = repo_root / LEARNINGS_PATH
    if not path.exists():
        return []
    out: List[Learning] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            out.append(Learning(**json.loads(line)))
        except (json.JSONDecodeError, TypeError):
            continue
    return out


def _append(repo_root: Path, learning: Learning) -> None:
    path = repo_root / LEARNINGS_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(learning.to_dict()) + "\n")


# ─── Rating logic ───────────────────────────────────────────────────────────

def _recency_factor(last_ts: Optional[str]) -> float:
    """Exponential decay: 1.0 if used today, 0.5 if 30 days ago,
    0.25 at 90, ~0 beyond 180 days."""
    if last_ts is None:
        return 0.0
    try:
        last = dt.datetime.fromisoformat(last_ts.rstrip("Z"))
    except ValueError:
        return 0.0
    now = dt.datetime.now()
    days_ago = max(0, (now - last).days)
    return 0.5 ** (days_ago / 30)


def rate_agent(repo_root: Path, agent_id: str) -> AgentRating:
    learnings = [l for l in _load(repo_root) if l.agent_id == agent_id]
    if not learnings:
        return AgentRating(
            agent_id=agent_id,
            sample_count=0,
            success_rate=0.5,    # neutral prior for unknown agents
            avg_duration_ms=0,
            avg_cost_usd=None,
            last_used_at=None,
            recency_factor=0.0,
            overall_rating=0.5,
        )
    successes = sum(1 for l in learnings if l.outcome == "succeeded")
    success_rate = successes / len(learnings)
    avg_duration = statistics.mean(l.duration_ms for l in learnings) \
        if any(l.duration_ms for l in learnings) else 0
    costs = [l.cost_usd for l in learnings if l.cost_usd is not None]
    avg_cost = statistics.mean(costs) if costs else None
    last_ts = max((l.ts for l in learnings), default=None)
    recency = _recency_factor(last_ts)
    # Composite rating
    sample_factor = min(len(learnings) / 10, 1.0)   # saturate at 10+ samples
    overall = (
        0.5 * success_rate
        + 0.3 * sample_factor
        + 0.2 * recency
    )
    return AgentRating(
        agent_id=agent_id,
        sample_count=len(learnings),
        success_rate=round(success_rate, 3),
        avg_duration_ms=round(avg_duration, 1),
        avg_cost_usd=round(avg_cost, 4) if avg_cost else None,
        last_used_at=last_ts,
        recency_factor=round(recency, 3),
        overall_rating=round(overall, 3),
    )


def top_agents(repo_root: Path, limit: int = 10) -> List[AgentRating]:
    learnings = _load(repo_root)
    agent_ids = {l.agent_id for l in learnings}
    ratings = [rate_agent(repo_root, a) for a in agent_ids]
    ratings.sort(key=lambda r: r.overall_rating, reverse=True)
    return ratings[:limit]


def dashboard(repo_root: Path, *, window_days: int = 30,
              drift_threshold: float = 0.15) -> Dict:
    """Richer view than top-agents: surfaces trends + drift warnings.

    For each agent:
      - recent success rate (last N days, default 30)
      - prior success rate (the N days before that)
      - drift = recent - prior; flag if drift < -drift_threshold (default
        15-point drop) — that's the "something changed, investigate" signal.

    Returns:
      {
        "window_days": 30,
        "drift_threshold": 0.15,
        "total_learnings": int,
        "total_agents": int,
        "agents": [
          {
            "agent_id": "local/architect",
            "recent_sample_count": int,
            "recent_success_rate": float,
            "prior_success_rate": float,
            "drift": float,
            "drift_flag": "stable" | "warming" | "degrading",
            ...
          },
          ...
        ],
        "overall": {
          "total_runs_recent": int,
          "success_rate_recent": float,
          "agents_degrading": int,
        }
      }
    """
    learnings = _load(repo_root)
    now = dt.datetime.now()
    cutoff_recent = now - dt.timedelta(days=window_days)
    cutoff_prior = now - dt.timedelta(days=window_days * 2)

    def _parse_ts(ts: str) -> Optional[dt.datetime]:
        try:
            return dt.datetime.fromisoformat(ts.rstrip("Z"))
        except ValueError:
            return None

    by_agent: Dict[str, Dict[str, List[Learning]]] = {}
    for l in learnings:
        parsed = _parse_ts(l.ts)
        if parsed is None:
            continue
        bucket = by_agent.setdefault(l.agent_id, {"recent": [], "prior": []})
        if parsed >= cutoff_recent:
            bucket["recent"].append(l)
        elif parsed >= cutoff_prior:
            bucket["prior"].append(l)

    def _rate(rows: List[Learning]) -> float:
        if not rows:
            return 0.0
        return sum(1 for r in rows if r.outcome == "succeeded") / len(rows)

    agent_rows: List[Dict] = []
    for agent_id, buckets in by_agent.items():
        recent = buckets["recent"]
        prior = buckets["prior"]
        if not recent and not prior:
            continue
        r_rate = _rate(recent)
        p_rate = _rate(prior) if prior else r_rate   # no prior data → use current
        drift = r_rate - p_rate
        if not prior:
            flag = "no_baseline"
        elif drift < -drift_threshold:
            flag = "degrading"
        elif drift > drift_threshold:
            flag = "warming"
        else:
            flag = "stable"
        agent_rows.append({
            "agent_id": agent_id,
            "recent_sample_count": len(recent),
            "recent_success_rate": round(r_rate, 3),
            "prior_sample_count": len(prior),
            "prior_success_rate": round(p_rate, 3) if prior else None,
            "drift": round(drift, 3),
            "drift_flag": flag,
        })
    # Sort: degrading first (loudest alert), then by recent sample count.
    flag_order = {"degrading": 0, "no_baseline": 1, "stable": 2, "warming": 3}
    agent_rows.sort(key=lambda r: (flag_order.get(r["drift_flag"], 99),
                                    -r["recent_sample_count"]))

    total_recent = sum(r["recent_sample_count"] for r in agent_rows)
    total_succ_recent = sum(
        r["recent_sample_count"] * r["recent_success_rate"]
        for r in agent_rows
    )
    return {
        "window_days": window_days,
        "drift_threshold": drift_threshold,
        "total_learnings": len(learnings),
        "total_agents": len(agent_rows),
        "agents": agent_rows,
        "overall": {
            "total_runs_recent": total_recent,
            "success_rate_recent": round(total_succ_recent / total_recent, 3)
                if total_recent else 0.0,
            "agents_degrading": sum(1 for r in agent_rows
                                     if r["drift_flag"] == "degrading"),
        },
    }


def export_anonymized(repo_root: Path) -> Dict:
    """Strip notes + actor identifiers from learnings for sharing."""
    learnings = _load(repo_root)
    anon = []
    for l in learnings:
        clone = l.to_dict()
        # Hash the agent_id so its identity is preserved across the
        # community without leaking who used what
        clone["agent_id_hash"] = hashlib.sha256(
            l.agent_id.encode()).hexdigest()[:12]
        clone.pop("agent_id", None)
        clone.pop("notes", None)
        anon.append(clone)
    return {
        "exported_at": dt.datetime.now(dt.timezone.utc).replace(
            microsecond=0, tzinfo=None).isoformat() + "Z",
        "total": len(anon),
        "learnings": anon,
    }


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Manage the cross-agent learnings hub + agent ratings"
    )
    parser.add_argument("--repo-root", default=".")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sp_rec = sub.add_parser("record")
    sp_rec.add_argument("--agent", required=True)
    sp_rec.add_argument("--outcome", required=True,
                        choices=["succeeded", "failed", "inconclusive"])
    sp_rec.add_argument("--task-keywords", nargs="*", default=[])
    sp_rec.add_argument("--duration-ms", type=int, default=0)
    sp_rec.add_argument("--cost-usd", type=float, default=None)
    sp_rec.add_argument("--notes", default="")

    sp_rat = sub.add_parser("rate")
    sp_rat.add_argument("--agent", required=True)

    sp_top = sub.add_parser("top-agents")
    sp_top.add_argument("--limit", type=int, default=10)

    sp_dash = sub.add_parser("dashboard",
                              help="Trend analysis + drift detection over a rolling window")
    sp_dash.add_argument("--window-days", type=int, default=30)
    sp_dash.add_argument("--drift-threshold", type=float, default=0.15,
                          help="Flag 'degrading' if recent success rate drops by "
                               "more than this fraction (default 0.15 = 15 points)")

    sub.add_parser("export-anonymized")

    args = parser.parse_args()
    repo = Path(args.repo_root).resolve()

    if args.cmd == "record":
        _append(repo, Learning(
            ts=dt.datetime.now(dt.timezone.utc).replace(
                microsecond=0, tzinfo=None).isoformat() + "Z",
            agent_id=args.agent,
            task_keywords=list(args.task_keywords),
            outcome=args.outcome,
            duration_ms=args.duration_ms,
            cost_usd=args.cost_usd,
            notes=args.notes,
        ))
        print(f"recorded learning for {args.agent} ({args.outcome})")
        return

    if args.cmd == "rate":
        print(json.dumps(rate_agent(repo, args.agent).to_dict(), indent=2))
        return

    if args.cmd == "top-agents":
        ratings = top_agents(repo, args.limit)
        print(json.dumps([r.to_dict() for r in ratings], indent=2))
        return

    if args.cmd == "dashboard":
        print(json.dumps(
            dashboard(repo, window_days=args.window_days,
                      drift_threshold=args.drift_threshold),
            indent=2,
        ))
        return

    if args.cmd == "export-anonymized":
        print(json.dumps(export_anonymized(repo), indent=2))
        return


if __name__ == "__main__":
    main()
