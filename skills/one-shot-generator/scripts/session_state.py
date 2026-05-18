#!/usr/bin/env python3
"""
Session State Machine — v1.0.0  (closes the "wasted tokens on /one-shot
restart" pain point)

The pipeline has 14 stages. If something fails at Stage 7 (critic),
running /one-shot again re-runs Stages 0..6 from scratch — burning
~$0.40 on identical planning + building work. Users will rarely
accept that.

This script gives the orchestrator a deterministic checkpoint primitive.
After each successful stage, the orchestrator calls:

    session_state.py checkpoint --session <id> --stage <name> --payload <json>

Stage payloads are stored in `<project>/.osp/sessions/{session_id}/`:

    .osp/sessions/run-2026-05-18-T13:30:00/
        00-curriculum.json
        01-extract_domain.json
        02-architect.json          ← /tmp/osp-spec.json saved here
        02.3-source-doc-plan.json
        03-implementer.json        ← all generated file paths + checksums
        05-reviewer.json           ← reviewer verdict
        ...
        _manifest.json             ← stages completed, last_failure, hint

When the user runs `/one-shot --resume`:

    session_state.py last --project <project>     # show most recent run
    session_state.py resume --session <id>        # emit the JSON the
                                                    orchestrator needs to
                                                    skip already-done stages

Critical: this script ONLY stores + retrieves. The orchestrator decides
which stages to skip. Skip logic:

  - If `_manifest.last_completed_stage == "6.5-migration"`, skip Stages
    0..6.5 and resume at Stage 7 (critic).
  - If user appends a `--hint`, override the spec.json with the hint
    inlined, restart from Stage 3 (implementer) — earlier stages keep
    their checkpoints valid.

CLI:
    session_state.py init --project <dir> [--feature <text>]
        -> creates a new session id, writes empty manifest

    session_state.py checkpoint --session <id> --stage <name> \
                                --payload-file <path-or-> --status ok|failed
        -> appends a stage to the manifest + persists the payload

    session_state.py list --project <dir>
        -> lists all sessions in chronological order

    session_state.py last --project <dir>
        -> prints the most recent session's manifest

    session_state.py resume --session <id>
        -> prints resume instructions: which stages are skippable,
           where the cached artifacts live, what the next stage is

    session_state.py prune --project <dir> --keep N
        -> deletes all but the N most recent sessions
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from lib.base_script import bootstrap_runtime, setup_logging
bootstrap_runtime()
logger = setup_logging(__name__)


SESSIONS_DIR = Path(".osp") / "sessions"
MANIFEST_NAME = "_manifest.json"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _session_id() -> str:
    """Millisecond precision so rapid-fire init calls produce distinct IDs."""
    now = datetime.now(timezone.utc)
    return "run-" + now.strftime("%Y%m%d-%H%M%S-") + f"{now.microsecond // 1000:03d}"


def _session_dir(project: Path, session_id: str) -> Path:
    return project / SESSIONS_DIR / session_id


def _manifest_path(project: Path, session_id: str) -> Path:
    return _session_dir(project, session_id) / MANIFEST_NAME


def _read_manifest(project: Path, session_id: str) -> Dict[str, Any]:
    path = _manifest_path(project, session_id)
    if not path.exists():
        raise FileNotFoundError(f"manifest not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _write_manifest(project: Path, session_id: str, manifest: Dict[str, Any]) -> None:
    path = _manifest_path(project, session_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")


# ─── init ──────────────────────────────────────────────────────────────────

def init_session(project: Path, feature: str = "") -> Dict[str, Any]:
    session_id = _session_id()
    session_dir = _session_dir(project, session_id)
    session_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "session_id": session_id,
        "project": str(project),
        "feature": feature,
        "created_at": _now_iso(),
        "stages": [],
        "last_completed_stage": None,
        "last_failure_stage": None,
        "status": "in_progress",
    }
    _write_manifest(project, session_id, manifest)
    return manifest


# ─── checkpoint ────────────────────────────────────────────────────────────

def checkpoint(project: Path, session_id: str, stage: str,
               payload: Any, status: str = "ok",
               hint: Optional[str] = None) -> Dict[str, Any]:
    manifest = _read_manifest(project, session_id)
    payload_path = _session_dir(project, session_id) / f"{stage}.json"
    payload_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    entry = {
        "stage": stage,
        "recorded_at": _now_iso(),
        "status": status,
        "payload_path": str(payload_path.relative_to(project)),
    }
    if hint:
        entry["hint"] = hint
    manifest["stages"].append(entry)
    if status == "ok":
        manifest["last_completed_stage"] = stage
    else:
        manifest["last_failure_stage"] = stage
        manifest["status"] = "failed"
    _write_manifest(project, session_id, manifest)
    return manifest


# ─── list / last ───────────────────────────────────────────────────────────

def list_sessions(project: Path) -> List[Dict[str, Any]]:
    sessions_root = project / SESSIONS_DIR
    if not sessions_root.exists():
        return []
    out: List[Dict[str, Any]] = []
    for d in sorted(sessions_root.iterdir()):
        if not d.is_dir():
            continue
        try:
            m = _read_manifest(project, d.name)
        except FileNotFoundError:
            continue
        out.append({
            "session_id": m["session_id"],
            "feature": m.get("feature", ""),
            "created_at": m["created_at"],
            "status": m["status"],
            "stages_completed": len([s for s in m["stages"]
                                       if s["status"] == "ok"]),
            "last_completed_stage": m.get("last_completed_stage"),
        })
    return out


def last_session(project: Path) -> Optional[Dict[str, Any]]:
    sessions = list_sessions(project)
    if not sessions:
        return None
    # Sort by created_at descending
    sessions.sort(key=lambda s: s["created_at"], reverse=True)
    sid = sessions[0]["session_id"]
    return _read_manifest(project, sid)


# ─── resume ────────────────────────────────────────────────────────────────

# Stages with cached artifacts that are SAFE to skip on resume.
# Later stages depend on earlier ones, so we resume from the first
# stage AFTER last_completed_stage.
KNOWN_STAGES_IN_ORDER = [
    "0-curriculum",
    "0.5-discovery",
    "0.7-legacy-guard",
    "1-extract-domain",
    "1.5-cost-budget",
    "1.8-source-docs",
    "2-architect",
    "2.5-spec-review",
    "2.6-incremental-plan",
    "2.7-service-author",
    "3-implementer-parallel",
    "4-verify-patch",
    "5-reviewer",
    "5.5-doubter",
    "5.7-consistency-security",
    "5.9-approval-gate",
    "6-wire",
    "6.5-migration",
    "7-critic",
    "8-record",
]


def resume_plan(project: Path, session_id: str,
                 hint: Optional[str] = None) -> Dict[str, Any]:
    """Build a resume plan: which stages to skip + where the cached
    artifacts live + which stage to start from."""
    manifest = _read_manifest(project, session_id)
    last_done = manifest.get("last_completed_stage")
    if not last_done:
        return {
            "session_id": session_id,
            "resume_from": KNOWN_STAGES_IN_ORDER[0],
            "skip_stages": [],
            "cached_artifacts": [],
            "note": "no completed stages — resume from beginning",
        }

    try:
        idx = KNOWN_STAGES_IN_ORDER.index(last_done)
    except ValueError:
        # Unknown stage name — be conservative; resume from start
        return {
            "session_id": session_id,
            "resume_from": KNOWN_STAGES_IN_ORDER[0],
            "skip_stages": [],
            "cached_artifacts": [s["payload_path"] for s in manifest["stages"]],
            "note": f"unknown stage '{last_done}' — resume from beginning",
        }

    skip = KNOWN_STAGES_IN_ORDER[:idx + 1]
    # If the user passed a hint, invalidate later spec-dependent stages.
    # A hint after Stage 2 means the spec changed; the user wants to
    # re-run implementer + downstream. Drop "2.5-spec-review" and beyond
    # from skip; only skip 0..2 (the cheap pre-architect stages).
    if hint:
        # Find the architect stage; skip everything BEFORE it but not after.
        cutoff = KNOWN_STAGES_IN_ORDER.index("3-implementer-parallel")
        skip = KNOWN_STAGES_IN_ORDER[:cutoff]
        # Also remove stages that ran but are now invalidated
        resume_from = "3-implementer-parallel"
    else:
        resume_from = (KNOWN_STAGES_IN_ORDER[idx + 1]
                        if idx + 1 < len(KNOWN_STAGES_IN_ORDER)
                        else "8-record")

    return {
        "session_id": session_id,
        "feature": manifest.get("feature", ""),
        "resume_from": resume_from,
        "skip_stages": skip,
        "hint": hint,
        "cached_artifacts": [s["payload_path"] for s in manifest["stages"]
                              if s["status"] == "ok"],
        "estimated_savings_usd": round(0.025 * len(skip), 3),
        "note": (f"Resuming from {resume_from}; skipping {len(skip)} "
                  f"cached stage(s)"),
    }


# ─── prune ─────────────────────────────────────────────────────────────────

def prune_sessions(project: Path, keep: int) -> Dict[str, Any]:
    sessions = list_sessions(project)
    sessions.sort(key=lambda s: s["created_at"], reverse=True)
    to_delete = sessions[keep:]
    deleted = 0
    for s in to_delete:
        path = _session_dir(project, s["session_id"])
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
            deleted += 1
    return {"kept": len(sessions) - deleted, "deleted": deleted}


# ─── CLI ───────────────────────────────────────────────────────────────────

def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        description="Session checkpoint + resume primitives for /one-shot. "
                    "Lets the orchestrator skip cached stages on retry."
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init",
                              help="Start a new session; print the manifest")
    p_init.add_argument("--project", required=True, type=Path)
    p_init.add_argument("--feature", default="")

    p_chk = sub.add_parser("checkpoint",
                             help="Record a stage outcome + persist its payload")
    p_chk.add_argument("--project", required=True, type=Path)
    p_chk.add_argument("--session", required=True)
    p_chk.add_argument("--stage", required=True,
                       choices=KNOWN_STAGES_IN_ORDER)
    p_chk.add_argument("--payload-file", type=Path, default=None,
                       help="Path to a JSON file with the stage payload; "
                            "use '-' to read JSON from stdin")
    p_chk.add_argument("--payload-json", default=None,
                       help="Inline JSON payload (alternative to --payload-file)")
    p_chk.add_argument("--status", default="ok", choices=["ok", "failed"])
    p_chk.add_argument("--hint", default=None,
                       help="Optional user-supplied hint for downstream stages")

    p_list = sub.add_parser("list", help="List all sessions")
    p_list.add_argument("--project", required=True, type=Path)

    p_last = sub.add_parser("last", help="Show the most recent session")
    p_last.add_argument("--project", required=True, type=Path)

    p_res = sub.add_parser("resume",
                             help="Build a resume plan from cached stages")
    p_res.add_argument("--project", required=True, type=Path)
    p_res.add_argument("--session", required=True,
                       help="Session ID (or 'last' for the most recent)")
    p_res.add_argument("--hint", default=None)

    p_pr = sub.add_parser("prune",
                            help="Delete old sessions, keep N most recent")
    p_pr.add_argument("--project", required=True, type=Path)
    p_pr.add_argument("--keep", type=int, default=10)

    args = p.parse_args(argv if argv is not None else sys.argv[1:])
    project = args.project.resolve()

    if args.cmd == "init":
        m = init_session(project, args.feature)
        print(json.dumps(m, indent=2))
        return 0

    if args.cmd == "checkpoint":
        if args.payload_file:
            if str(args.payload_file) == "-":
                payload = json.load(sys.stdin)
            else:
                payload = json.loads(args.payload_file.read_text(encoding="utf-8"))
        elif args.payload_json:
            payload = json.loads(args.payload_json)
        else:
            payload = {}
        try:
            m = checkpoint(project, args.session, args.stage, payload,
                            status=args.status, hint=args.hint)
        except FileNotFoundError as e:
            print(json.dumps({"error": str(e)}), file=sys.stderr)
            return 1
        print(json.dumps(m, indent=2))
        return 0

    if args.cmd == "list":
        print(json.dumps(list_sessions(project), indent=2))
        return 0

    if args.cmd == "last":
        m = last_session(project)
        if m is None:
            print(json.dumps({"error": "no sessions found"}), file=sys.stderr)
            return 1
        print(json.dumps(m, indent=2))
        return 0

    if args.cmd == "resume":
        sid = args.session
        if sid == "last":
            m = last_session(project)
            if m is None:
                print(json.dumps({"error": "no session to resume"}), file=sys.stderr)
                return 1
            sid = m["session_id"]
        try:
            plan = resume_plan(project, sid, hint=args.hint)
        except FileNotFoundError as e:
            print(json.dumps({"error": str(e)}), file=sys.stderr)
            return 1
        print(json.dumps(plan, indent=2))
        return 0

    if args.cmd == "prune":
        result = prune_sessions(project, args.keep)
        print(json.dumps(result, indent=2))
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
