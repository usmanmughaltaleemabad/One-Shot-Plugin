#!/usr/bin/env python3
"""
Approval Gate — v1.0.0  (Stage 5.9 human-in-the-loop for autonomous runs)

In interactive `/one-shot` use, HITL is implicit: `--apply` is off by
default, `/ship-check` runs before mutation, the user types "y" to
proceed. In **autonomous** runs (GitHub Actions, scheduled jobs,
`agentic_session_driver --mode live-api` from CI) there's no terminal
to type at.

This gate closes the gap. It POSTs the wire plan + ship-check verdict +
diff summary to a webhook URL, then either:
  - polls a callback endpoint for an `approved: true` response (timeout
    after `--timeout-minutes`, default 60), OR
  - emits a request ID and exits 0 with status=pending; a separate
    process can resume with `--resume <id> --approved true`.

Both modes work. The webhook payload is generic enough to wire into:
  - GitHub PR review comments (post the diff; resolve by closing PR)
  - Slack interactive messages (post; user clicks "Approve")
  - Custom approval portal (your own UI)
  - PagerDuty / Opsgenie (if the change touches production)

Inspired by Gemini's review of the v4.10 pipeline (Stage 5.9 HITL
blindspot). Closes a real autonomous-mode gap.

CLI:

    # Mode 1 — POST + poll (blocks until approved / denied / timeout)
    approval_gate.py request \\
        --webhook-url https://hooks.slack.com/services/... \\
        --callback-url https://my-approval-portal/api/decision \\
        --plan /tmp/osp-wire-plan.json \\
        --ship-gates /tmp/osp-ship-verdict.json \\
        --timeout-minutes 60

    # Mode 2 — POST only (returns immediately; resume later)
    approval_gate.py request \\
        --webhook-url https://... \\
        --plan /tmp/osp-wire-plan.json \\
        --emit-only

    approval_gate.py resume --request-id <id> --approved true
    approval_gate.py status --request-id <id>

Decision values returned (JSON to stdout):
    {
      "status": "approved" | "denied" | "pending" | "timed_out" | "error",
      "request_id": "...",
      "approver": "<from callback>",
      "approved_at": "...Z" | null,
      "denial_reason": "..." | null,
      "decision_url": "..."  // optional link back to PR / Slack thread
    }

Exit codes:
    0  approved
    1  bad args / webhook unreachable
    2  denied OR timed_out

State lives in `.beads/approvals/{request_id}.json` so the resume
command works across processes / restarts.
"""

from __future__ import annotations

import argparse
import json
import secrets
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from lib.base_script import bootstrap_runtime, setup_logging
bootstrap_runtime()
logger = setup_logging(__name__)


APPROVALS_DIR = Path(".beads") / "approvals"
DEFAULT_TIMEOUT_MIN = 60
POLL_INTERVAL_SECONDS = 5


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _state_path(repo_root: Path, request_id: str) -> Path:
    return repo_root / APPROVALS_DIR / f"{request_id}.json"


def _read_state(repo_root: Path, request_id: str) -> Dict[str, Any]:
    p = _state_path(repo_root, request_id)
    if not p.exists():
        raise FileNotFoundError(f"approval state not found: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def _write_state(repo_root: Path, request_id: str, state: Dict[str, Any]) -> None:
    p = _state_path(repo_root, request_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _post_webhook(url: str, payload: Dict[str, Any], *,
                   timeout_s: int = 10) -> Dict[str, Any]:
    """POST JSON to webhook; return {status_code, body, ok}."""
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=body, method="POST",
        headers={"Content-Type": "application/json",
                  "User-Agent": "one-shot-prompting/approval-gate"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            return {
                "status_code": resp.status,
                "body": resp.read().decode("utf-8", errors="replace"),
                "ok": 200 <= resp.status < 300,
            }
    except urllib.error.HTTPError as e:
        return {
            "status_code": e.code,
            "body": e.read().decode("utf-8", errors="replace"),
            "ok": False,
        }
    except urllib.error.URLError as e:
        return {"status_code": 0, "body": str(e.reason), "ok": False}


def _get_callback(url: str, *, timeout_s: int = 10) -> Dict[str, Any]:
    req = urllib.request.Request(
        url, method="GET",
        headers={"User-Agent": "one-shot-prompting/approval-gate"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            text = resp.read().decode("utf-8", errors="replace")
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                parsed = {"raw": text}
            return {"status_code": resp.status, "body": parsed,
                    "ok": 200 <= resp.status < 300}
    except urllib.error.HTTPError as e:
        return {"status_code": e.code, "body": {"error": str(e)}, "ok": False}
    except urllib.error.URLError as e:
        return {"status_code": 0, "body": {"error": str(e.reason)}, "ok": False}


def _build_payload(request_id: str, *,
                    plan: Optional[Dict],
                    ship_gates: Optional[Dict],
                    summary: str) -> Dict[str, Any]:
    """Generic payload — webhook receiver maps fields into their format."""
    return {
        "request_id": request_id,
        "created_at": _now_iso(),
        "source": "one-shot-prompting",
        "stage": "5.9-pre-ship-approval",
        "summary": summary,
        "wire_plan": plan,
        "ship_gates": ship_gates,
        "decision_callback_hint": (
            "POST { 'request_id': '...', 'approved': true|false, "
            "'approver': '...', 'reason': '...' } to your approval API; "
            "OR have your portal expose a GET endpoint returning that shape "
            "and pass --callback-url to poll it."
        ),
    }


# ─── Subcommands ───────────────────────────────────────────────────────────

def cmd_request(args: argparse.Namespace, repo_root: Path) -> int:
    """POST the approval payload to webhook. Either return immediately
    (with status=pending + request_id) OR poll the callback URL until
    approved/denied/timeout."""
    request_id = "ap_" + secrets.token_hex(8)
    plan = None
    if args.plan and Path(args.plan).exists():
        plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    ship_gates = None
    if args.ship_gates and Path(args.ship_gates).exists():
        ship_gates = json.loads(Path(args.ship_gates).read_text(encoding="utf-8"))

    payload = _build_payload(
        request_id,
        plan=plan,
        ship_gates=ship_gates,
        summary=args.summary or "/one-shot pre-ship approval requested",
    )

    state: Dict[str, Any] = {
        "request_id": request_id,
        "created_at": _now_iso(),
        "webhook_url": args.webhook_url,
        "callback_url": args.callback_url,
        "status": "pending",
        "payload": payload,
        "approver": None,
        "approved_at": None,
        "denial_reason": None,
    }
    _write_state(repo_root, request_id, state)

    # POST to webhook
    resp = _post_webhook(args.webhook_url, payload)
    if not resp["ok"]:
        state["status"] = "error"
        state["error"] = f"webhook returned {resp['status_code']}: {resp['body'][:200]}"
        _write_state(repo_root, request_id, state)
        print(json.dumps({"status": "error", "request_id": request_id,
                          "error": state["error"]}, indent=2))
        return 1

    # Emit-only mode — return immediately
    if args.emit_only or not args.callback_url:
        print(json.dumps({
            "status": "pending",
            "request_id": request_id,
            "webhook_posted": True,
            "webhook_response_code": resp["status_code"],
            "resume_with": f"approval_gate.py resume --request-id {request_id} --approved true",
        }, indent=2))
        return 0

    # Polling mode
    timeout_seconds = (args.timeout_minutes or DEFAULT_TIMEOUT_MIN) * 60
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        cb = _get_callback(args.callback_url)
        if cb["ok"]:
            body = cb["body"] if isinstance(cb["body"], dict) else {}
            # Body must match { request_id, approved, approver?, reason? }
            if body.get("request_id") == request_id:
                if body.get("approved") is True:
                    state["status"] = "approved"
                    state["approver"] = body.get("approver", "(unknown)")
                    state["approved_at"] = _now_iso()
                    _write_state(repo_root, request_id, state)
                    print(json.dumps(state, indent=2))
                    return 0
                if body.get("approved") is False:
                    state["status"] = "denied"
                    state["denial_reason"] = body.get("reason", "(no reason given)")
                    _write_state(repo_root, request_id, state)
                    print(json.dumps(state, indent=2))
                    return 2
        time.sleep(POLL_INTERVAL_SECONDS)

    state["status"] = "timed_out"
    _write_state(repo_root, request_id, state)
    print(json.dumps(state, indent=2))
    return 2


def cmd_resume(args: argparse.Namespace, repo_root: Path) -> int:
    """Out-of-band decision: a separate process / human / cron job sets
    approved=true|false on a pending request."""
    state = _read_state(repo_root, args.request_id)
    if state["status"] != "pending":
        print(json.dumps({"status": "error",
                          "reason": f"request is in state '{state['status']}', not 'pending'",
                          "request_id": args.request_id}, indent=2),
              file=sys.stderr)
        return 1
    if args.approved:
        state["status"] = "approved"
        state["approver"] = args.approver or "(cli-resume)"
        state["approved_at"] = _now_iso()
    else:
        state["status"] = "denied"
        state["denial_reason"] = args.reason or "(no reason given)"
    _write_state(repo_root, args.request_id, state)
    print(json.dumps(state, indent=2))
    return 0 if args.approved else 2


def cmd_status(args: argparse.Namespace, repo_root: Path) -> int:
    state = _read_state(repo_root, args.request_id)
    print(json.dumps(state, indent=2))
    if state["status"] == "approved":
        return 0
    if state["status"] in {"denied", "timed_out"}:
        return 2
    return 0   # pending is not an error condition


def cmd_list(args: argparse.Namespace, repo_root: Path) -> int:
    d = repo_root / APPROVALS_DIR
    if not d.exists():
        print(json.dumps({"approvals": [], "total": 0}, indent=2))
        return 0
    entries = []
    for p in sorted(d.glob("ap_*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            entries.append({
                "request_id": data["request_id"],
                "status": data["status"],
                "created_at": data["created_at"],
                "approver": data.get("approver"),
            })
        except (json.JSONDecodeError, KeyError):
            continue
    print(json.dumps({"approvals": entries, "total": len(entries)}, indent=2))
    return 0


# ─── CLI ───────────────────────────────────────────────────────────────────

def _parse(argv: List[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Pre-ship human-in-the-loop approval gate for "
                    "autonomous /one-shot runs."
    )
    p.add_argument("--repo-root", type=Path, default=Path.cwd())
    sub = p.add_subparsers(dest="cmd", required=True)

    p_req = sub.add_parser("request",
                            help="POST approval payload to webhook; "
                                 "optionally poll callback URL.")
    p_req.add_argument("--webhook-url", required=True,
                        help="Where to POST the approval payload.")
    p_req.add_argument("--callback-url", default=None,
                        help="If set, poll this URL for a decision.")
    p_req.add_argument("--plan", type=Path, default=None,
                        help="Path to wire plan JSON.")
    p_req.add_argument("--ship-gates", type=Path, default=None,
                        help="Path to ship-gates verdict JSON.")
    p_req.add_argument("--summary", default=None,
                        help="One-line summary for the webhook receiver.")
    p_req.add_argument("--timeout-minutes", type=int, default=DEFAULT_TIMEOUT_MIN,
                        help="Max minutes to poll callback (default 60).")
    p_req.add_argument("--emit-only", action="store_true",
                        help="Return immediately after POST; don't poll.")

    p_res = sub.add_parser("resume",
                            help="Out-of-band: set approved=true|false "
                                 "on a pending request.")
    p_res.add_argument("--request-id", required=True)
    p_res.add_argument("--approved", type=lambda x: x.lower() == "true",
                        required=True,
                        help="'true' or 'false'.")
    p_res.add_argument("--approver", default=None)
    p_res.add_argument("--reason", default=None,
                        help="Required if --approved=false.")

    p_st = sub.add_parser("status",
                           help="Look up the current state of a request.")
    p_st.add_argument("--request-id", required=True)

    sub.add_parser("list", help="List all approval requests in the repo.")

    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = _parse(argv if argv is not None else sys.argv[1:])
    repo_root = args.repo_root.resolve()
    try:
        if args.cmd == "request":
            return cmd_request(args, repo_root)
        if args.cmd == "resume":
            return cmd_resume(args, repo_root)
        if args.cmd == "status":
            return cmd_status(args, repo_root)
        if args.cmd == "list":
            return cmd_list(args, repo_root)
    except FileNotFoundError as e:
        print(json.dumps({"status": "error", "error": str(e)}, indent=2),
              file=sys.stderr)
        return 1
    return 1


if __name__ == "__main__":
    sys.exit(main())
