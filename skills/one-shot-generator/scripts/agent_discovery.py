#!/usr/bin/env python3
"""
Agent Discovery — v1.0.0  (Tier 4 self-extending plugin)

Given a natural-language task, return a ranked list of agents / skills /
MCP servers that match it best — drawing from THREE sources:

  1. Local agents in this plugin (`.claude/agents/*.md`)
  2. Local skills in this plugin (`skills/*/SKILL.md`)
  3. External registries in `.claude/registry/{agents,skills,mcp_servers}.json`

Matching is keyword-based (Jaccard over normalised triggers + specialty
tokens) with two boosts:
  * **same-specialty bonus**: an entry whose `specialty` list contains a
    keyword that also appears in the task tokens gets +0.15.
  * **preferred-over-local bonus**: if an external agent has
    ``preferred_over_local: <name>`` and that local agent would otherwise
    win, the external one steals the slot.

The discovery output is consumed by `one-shot-generate/SKILL.md` Stage 0.5
to surface "you might want to use X instead of / in addition to your
local Y" guidance before the agentic pipeline fires.

CLI:
    python agent_discovery.py "shopping cart with line items"
    python agent_discovery.py "ui test with lighthouse audit" --limit 5
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from lib.base_script import bootstrap_runtime, setup_logging
bootstrap_runtime()

logger = setup_logging(__name__)


_STOPWORDS = {
    "add", "create", "build", "generate", "make", "with", "and", "or",
    "for", "the", "a", "an", "to", "of", "in", "on", "by", "as", "via",
    "feature", "module", "service", "api", "complete", "full", "ready",
}


# ─── Data shapes ─────────────────────────────────────────────────────────────

@dataclass
class DiscoveryHit:
    id: str
    kind: str                 # "local-agent" | "local-skill" | "external-agent"
                              # | "external-skill" | "external-mcp"
    score: float
    matched_keywords: List[str]
    description: str
    invocation_hint: str      # how to actually use this from the main flow
    preferred_over_local: Optional[str] = None
    source_file: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class DiscoveryReport:
    task: str
    task_tokens: List[str]
    hits: List[DiscoveryHit] = field(default_factory=list)
    recommendations: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "task": self.task,
            "task_tokens": self.task_tokens,
            "hits": [h.to_dict() for h in self.hits],
            "recommendations": self.recommendations,
        }


# ─── Tokenisation + scoring ─────────────────────────────────────────────────

def _tokens(text: str) -> Set[str]:
    return {tok for tok in re.findall(r"[a-zA-Z_]{3,}", text.lower())
            if tok not in _STOPWORDS}


def _overlap_coefficient(a: Set[str], b: Set[str]) -> float:
    """Overlap coefficient: |A∩B| / min(|A|, |B|).

    Better than Jaccard for this use case: agents/MCPs declare many
    trigger words and we don't want to penalise them for being
    well-described. We just want to know "does the task talk about
    things this entry knows about?"
    """
    if not a or not b:
        return 0.0
    return len(a & b) / min(len(a), len(b))


# Kept for tests / explicit Jaccard callers
def _jaccard(a: Set[str], b: Set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


# ─── Source loaders ─────────────────────────────────────────────────────────

REPO_ROOT_DEFAULT = Path(__file__).resolve().parents[3]


def _load_local_agents(repo: Path) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    agents_dir = repo / ".claude" / "agents"
    if not agents_dir.is_dir():
        return out
    for path in sorted(agents_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        front_match = re.search(r"^---\n(.+?)\n---", text, re.DOTALL)
        if not front_match:
            continue
        front = front_match.group(1)
        name = _yaml_scalar(front, "name") or path.stem
        description = _yaml_scalar(front, "description") or ""
        # An agent's "trigger words" are its description text + filename
        triggers = list(_tokens(description + " " + path.stem))
        out.append({
            "id": name,
            "kind": "local-agent",
            "description": description,
            "triggers": triggers,
            "specialty": triggers,  # local agents don't declare separate specialty
            "source_file": str(path.relative_to(repo)).replace("\\", "/"),
            "invocation_hint": f'Spawn via Task with subagent_type matching the plugin\'s "{name}" agent.',
        })
    return out


def _load_local_skills(repo: Path) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    skills_dir = repo / "skills"
    if not skills_dir.is_dir():
        return out
    for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
        text = skill_md.read_text(encoding="utf-8", errors="ignore")
        front_match = re.search(r"^---\n(.+?)\n---", text, re.DOTALL)
        if not front_match:
            continue
        front = front_match.group(1)
        name = _yaml_scalar(front, "name") or skill_md.parent.name
        description = _yaml_scalar(front, "description") or ""
        triggers = list(_tokens(description + " " + name))
        out.append({
            "id": name,
            "kind": "local-skill",
            "description": description,
            "triggers": triggers,
            "specialty": triggers,
            "source_file": str(skill_md.relative_to(repo)).replace("\\", "/"),
            "invocation_hint": f'Invoke via /one-shot-prompting:{name} or call the skill directly from the orchestrator.',
        })
    return out


def _yaml_scalar(front: str, key: str) -> Optional[str]:
    """Tiny single-line YAML scalar extractor (no full YAML parser dep).

    Handles ``key: value`` (single line) and ``key: |`` (block scalar
    continuation lines). Returns first line's value if block.
    """
    m = re.search(rf"^{re.escape(key)}:\s*(.+)$", front, re.MULTILINE)
    if not m:
        return None
    val = m.group(1).strip()
    if val == "|" or val == ">":
        # Block scalar — pick up the first non-blank indented line
        lines = front.splitlines()
        idx = next((i for i, l in enumerate(lines)
                    if l.startswith(f"{key}:")), None)
        if idx is None:
            return None
        for ln in lines[idx + 1:]:
            stripped = ln.strip()
            if stripped:
                return stripped
        return None
    return val.strip('"').strip("'")


def _load_registry(repo: Path, filename: str, kind: str,
                   list_key: str) -> List[Dict[str, Any]]:
    path = repo / ".claude" / "registry" / filename
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        logger.warning("registry %s is malformed: %s", filename, exc)
        return []
    out: List[Dict[str, Any]] = []
    for entry in data.get(list_key, []):
        triggers = list(_tokens(
            entry.get("description", "") + " "
            + " ".join(entry.get("triggers") or [])
            + " " + " ".join(entry.get("specialty") or [])
        ))
        entry_copy = dict(entry)
        entry_copy["kind"] = kind
        entry_copy["triggers_normalised"] = triggers
        out.append(entry_copy)
    return out


# ─── Scoring + matching ─────────────────────────────────────────────────────

def _score_entry(entry: Dict[str, Any], task_tokens: Set[str]) -> float:
    trig = set(entry.get("triggers_normalised") or entry.get("triggers") or [])
    base = _overlap_coefficient(task_tokens, trig)
    specialty = set(entry.get("specialty") or [])
    if specialty & task_tokens:
        base += 0.15
    return min(base, 1.0)


def discover(*, task: str, repo: Path,
             limit: int = 8,
             min_score: float = 0.10) -> DiscoveryReport:
    task_tokens = _tokens(task)

    all_entries: List[Dict[str, Any]] = []
    all_entries += _load_local_agents(repo)
    all_entries += _load_local_skills(repo)
    all_entries += _load_registry(repo, "agents.json", "external-agent", "agents")
    all_entries += _load_registry(repo, "skills.json", "external-skill", "skills")
    all_entries += _load_registry(repo, "mcp_servers.json", "external-mcp", "servers")

    scored: List[DiscoveryHit] = []
    for entry in all_entries:
        score = _score_entry(entry, task_tokens)
        if score < min_score:
            continue
        matched = sorted(task_tokens & set(entry.get("triggers_normalised")
                                            or entry.get("triggers") or []))
        scored.append(DiscoveryHit(
            id=entry["id"],
            kind=entry["kind"],
            score=round(score, 3),
            matched_keywords=matched,
            description=entry.get("description", ""),
            invocation_hint=entry.get("invocation_hint")
                            or entry.get("use_case_in_pipeline")
                            or "(no hint)",
            preferred_over_local=entry.get("preferred_over_local"),
            source_file=entry.get("source_file"),
        ))

    scored.sort(key=lambda h: h.score, reverse=True)
    top = scored[:limit]

    # Recommendations: explicit suggestions the SKILL.md can surface.
    recs: List[Dict[str, str]] = []
    for hit in top:
        if hit.preferred_over_local:
            # The registry author marked this external as preferred over
            # one of our local agents; surface that as a routing hint.
            recs.append({
                "type": "route-override",
                "external": hit.id,
                "replaces_local": hit.preferred_over_local,
                "reason": f"registry marks {hit.id} as preferred over local "
                          f"{hit.preferred_over_local} when keywords match",
            })
        elif hit.kind in ("external-agent", "external-skill", "external-mcp") \
                and hit.score >= 0.30:
            recs.append({
                "type": "consider-using",
                "external": hit.id,
                "reason": f"strong keyword match ({hit.score:.2f}) — may add value "
                          "beyond the local pipeline",
            })
    return DiscoveryReport(
        task=task,
        task_tokens=sorted(task_tokens),
        hits=top,
        recommendations=recs,
    )


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Discover the best agents/skills/MCPs for a task"
    )
    parser.add_argument("task", nargs="+", help="Task description")
    parser.add_argument("--repo", default=None, help="Plugin repo root")
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--min-score", type=float, default=0.10)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo = Path(args.repo).resolve() if args.repo else REPO_ROOT_DEFAULT
    report = discover(task=" ".join(args.task), repo=repo,
                      limit=args.limit, min_score=args.min_score)

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
        return

    print(f"DISCOVERY — {report.task!r}")
    print("─" * 60)
    print(f"  task tokens: {', '.join(report.task_tokens[:10])}"
          + ("…" if len(report.task_tokens) > 10 else ""))
    if not report.hits:
        print("  no matches above threshold — proceed with the local pipeline as-is")
        return
    print()
    print(f"TOP MATCHES ({len(report.hits)})")
    for h in report.hits:
        kind_short = h.kind.replace("local-", "L:").replace("external-", "X:")
        print(f"  [{h.score:.2f}] [{kind_short:<10}] {h.id}")
        print(f"           matched: {', '.join(h.matched_keywords[:6])}")
        print(f"           {h.description[:90]}{'…' if len(h.description) > 90 else ''}")
        if h.preferred_over_local:
            print(f"           ★ preferred over local '{h.preferred_over_local}'")
    if report.recommendations:
        print()
        print("RECOMMENDATIONS")
        for r in report.recommendations:
            if r["type"] == "route-override":
                print(f"  → swap local '{r['replaces_local']}' for external "
                      f"'{r['external']}' on this task")
            else:
                print(f"  → consider also invoking '{r['external']}' "
                      f"({r['reason']})")


if __name__ == "__main__":
    main()
