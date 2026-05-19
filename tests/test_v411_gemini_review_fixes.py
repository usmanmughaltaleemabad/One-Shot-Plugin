"""Tests for v4.11 — fixes from Gemini's review of the v4.10 pipeline.

Three fixes shipped:

1. Source-driven doc lookup moved from Stage 2.3 (post-architect)
   to Stage 1.8 (pre-architect). The architect now sees current
   framework conventions while designing the spec — not after,
   when deprecated patterns would already be baked in.

2. Migration-order trade-off explicitly documented in SKILL.md
   Stage 6.5. Three sub-cases for modifying existing entities
   (add NULL column, add NOT NULL column, rename/drop column) with
   the exact safety behaviour for each.

3. New approval_gate.py + agentic_session_driver
   --require-approval-webhook flag. Closes the HITL gap for
   autonomous CI runs: POSTs the wire plan + ship-check verdict to
   a webhook, optionally polls a callback URL for approved=true/false.
   Two modes: emit-only (non-blocking, caller resumes via CLI) and
   poll (blocking, callback contract).
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "skills" / "one-shot-generator" / "scripts"
APPROVAL = SCRIPTS / "approval_gate.py"
DRIVER = SCRIPTS / "agentic_session_driver.py"
SKILL = REPO_ROOT / "skills" / "one-shot-generate" / "SKILL.md"
RUNNER = SCRIPTS / "live_api_runner.py"

# Make runner importable so we can poke its prompt builders directly
sys.path.insert(0, str(SCRIPTS))
from live_api_runner import build_user_prompt   # noqa: E402


def _run(script: Path, *args: str, check: bool = True,
         timeout: int = 30) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True, text=True, env=env, encoding="utf-8",
        timeout=timeout,
    )
    if check:
        assert proc.returncode in (0, 1, 2), \
            f"{script.name} crashed: {proc.stderr}"
    return proc


# ─── Fix #1 — Source-doc lookup moved to Stage 1.8 ─────────────────────────

def test_skill_md_has_stage_1_8_source_doc_lookup():
    from conftest import pipeline_text; text = pipeline_text()
    # The new Stage 1.8 must exist AND come before Stage 2 architect
    s18_idx = text.find("## Stage 1.8 — Source-driven doc lookup")
    s2_idx = text.find("## Stage 2 — Architect agent")
    assert s18_idx != -1, "Stage 1.8 missing"
    assert s2_idx != -1, "Stage 2 missing"
    assert s18_idx < s2_idx, "Stage 1.8 must come before Stage 2 architect"


def test_skill_md_old_stage_2_3_marked_deprecated():
    """Stage 2.3 anchor must still exist (for backward-compat links) but
    must explicitly say it was moved to 1.8."""
    from conftest import pipeline_text; text = pipeline_text()
    assert "## Stage 2.3" in text
    # Must contain the deprecation note
    # Anchor for cross-reference
    assert "DEPRECATED" in text.split("## Stage 2.3", 1)[1].split("---", 1)[0]
    assert "moved to Stage 1.8" in text or "moved to [Stage 1.8" in text


def test_skill_md_architect_prompt_template_includes_source_excerpts():
    """The architect Task prompt template in SKILL.md must include the
    source_excerpts paste-in slot from Stage 1.8."""
    from conftest import pipeline_text; text = pipeline_text()
    # Architect prompt section
    architect_section = text[text.find("## Stage 2 — Architect agent"):
                              text.find("## Stage 2.3")]
    assert "source_excerpts" in architect_section.lower() \
        or "official-doc excerpts" in architect_section.lower(), \
        "architect prompt template missing source_excerpts slot"
    assert "Stage 1.8" in architect_section, \
        "architect prompt must reference Stage 1.8 as the source of excerpts"


def test_architect_prompt_builder_includes_source_excerpts():
    """live_api_runner.py's _architect_prompt must inject source_excerpts
    into the prompt body."""
    excerpts_text = (
        "FastAPI 0.115: use Annotated[Depends(get_db)] for type-safe deps. "
        "Pydantic v2: model_config = ConfigDict(from_attributes=True)."
    )
    prompt = build_user_prompt(
        "architect",
        spawn_input={"task": "build a cart"},
        context={
            "domain_model": {"entities": [{"name": "Cart"}]},
            "graph_summary": "FastAPI 0.115 project",
            "source_excerpts": excerpts_text,
        },
    )
    assert "FastAPI 0.115" in prompt
    assert "Annotated" in prompt
    assert "ConfigDict" in prompt
    assert "canonical" in prompt.lower() or "override" in prompt.lower(), \
        "architect must be told to TRUST excerpts over training data"


def test_architect_prompt_falls_back_when_no_source_excerpts():
    """No excerpts (greenfield project) → falls back gracefully, doesn't crash."""
    prompt = build_user_prompt(
        "architect",
        spawn_input={"task": "build a cart"},
        context={"domain_model": {}, "graph_summary": "(no graph)"},
    )
    # Falls back to a sensible placeholder
    assert "(none" in prompt.lower() or "skipped" in prompt.lower() \
        or "no manifest" in prompt.lower(), \
        "architect prompt must indicate when no source excerpts available"


# ─── Fix #2 — Migration order trade-off documented ────────────────────────

def test_skill_md_documents_migration_order_tradeoff():
    from conftest import pipeline_text; text = pipeline_text()
    # The trade-off section must exist under Stage 6.5
    s65 = text.split("### Stage 6.5", 1)[1].split("## Stage 7", 1)[0]
    # Must call out the three sub-cases for ALTER patterns
    assert "Why migration AFTER" in s65 or "AFTER implementer" in s65, \
        "Stage 6.5 must explain the migration-after-implementer ordering"
    assert "greenfield" in s65.lower(), \
        "must distinguish greenfield from ALTER cases"
    assert "NOT NULL" in s65, \
        "must surface the NOT NULL backfill case explicitly"
    assert "expand/contract" in s65.lower() \
        or "two-step" in s65.lower() \
        or "MIGRATION_RUNBOOK" in s65, \
        "must reference the rename/drop manual runbook path"


# ─── Fix #3 — Webhook approval gate ────────────────────────────────────────

class _ApprovalCallbackServer:
    """Local HTTP server that simulates a webhook receiver + callback API.
    Tests configure what to POST/GET and assert the approval_gate behaviour."""

    def __init__(self, approved: bool | None = None,
                 reason: str | None = None,
                 approver: str = "ci-bot"):
        self.approved = approved
        self.reason = reason
        self.approver = approver
        self.posted_payloads: list = []
        self.server: HTTPServer | None = None
        self.thread: threading.Thread | None = None

    def start(self) -> tuple[str, str]:
        """Returns (webhook_url, callback_url)."""
        approved = self.approved
        approver = self.approver
        reason = self.reason
        posted = self.posted_payloads
        latest_request_id = {"id": None}

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *a, **k): pass

            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length).decode("utf-8")
                try:
                    parsed = json.loads(body)
                except json.JSONDecodeError:
                    parsed = {}
                posted.append(parsed)
                if "request_id" in parsed:
                    latest_request_id["id"] = parsed["request_id"]
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"ok": true}')

            def do_GET(self):
                if approved is None:
                    # Simulate "still pending" — return 404 / no decision yet
                    self.send_response(204)
                    self.end_headers()
                    return
                payload = {
                    "request_id": latest_request_id["id"],
                    "approved": approved,
                    "approver": approver,
                }
                if reason:
                    payload["reason"] = reason
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(payload).encode("utf-8"))

        self.server = HTTPServer(("127.0.0.1", 0), Handler)
        port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever,
                                        daemon=True)
        self.thread.start()
        base = f"http://127.0.0.1:{port}"
        return f"{base}/webhook", f"{base}/callback"

    def stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()


@pytest.fixture
def callback_server():
    """Yield a factory; tear it down after each test."""
    servers: list[_ApprovalCallbackServer] = []

    def make(*, approved: bool | None = None, reason: str | None = None,
             approver: str = "ci-bot") -> _ApprovalCallbackServer:
        s = _ApprovalCallbackServer(approved=approved, reason=reason,
                                      approver=approver)
        s.start()
        servers.append(s)
        return s

    yield make
    for s in servers:
        s.stop()


def test_approval_gate_emit_only_returns_pending(tmp_path, callback_server):
    s = callback_server(approved=None)
    webhook, _ = s.start()  # restart fresh — start() is idempotent? no, but ok
    # Actually use the one made by the factory
    s2 = callback_server()
    webhook2, _ = s2.start() if False else (webhook, "")
    proc = _run(APPROVAL,
                "--repo-root", str(tmp_path),
                "request",
                "--webhook-url", webhook,
                "--emit-only")
    data = json.loads(proc.stdout)
    assert data["status"] == "pending"
    assert data["request_id"].startswith("ap_")
    assert "resume_with" in data
    # Webhook received the POST
    assert len(s.posted_payloads) >= 1
    sent = s.posted_payloads[0]
    assert sent["source"] == "one-shot-prompting"
    assert sent["stage"] == "5.9-pre-ship-approval"


def test_approval_gate_polling_returns_approved(tmp_path, callback_server):
    s = callback_server(approved=True, approver="alice")
    webhook, callback = s.start() if False else (None, None)
    # Reuse the started one
    proc = _run(APPROVAL,
                "--repo-root", str(tmp_path),
                "request",
                "--webhook-url", "http://127.0.0.1:" + str(s.server.server_address[1]) + "/webhook",
                "--callback-url", "http://127.0.0.1:" + str(s.server.server_address[1]) + "/callback",
                "--timeout-minutes", "1",
                timeout=30)
    data = json.loads(proc.stdout)
    assert data["status"] == "approved"
    assert data["approver"] == "alice"
    assert data["approved_at"] is not None


def test_approval_gate_polling_returns_denied(tmp_path, callback_server):
    s = callback_server(approved=False, reason="too risky for prod")
    base = f"http://127.0.0.1:{s.server.server_address[1]}"
    proc = _run(APPROVAL,
                "--repo-root", str(tmp_path),
                "request",
                "--webhook-url", f"{base}/webhook",
                "--callback-url", f"{base}/callback",
                "--timeout-minutes", "1",
                timeout=30, check=False)
    assert proc.returncode == 2   # denied
    data = json.loads(proc.stdout)
    assert data["status"] == "denied"
    assert "too risky" in data["denial_reason"]


def test_approval_gate_resume_subcommand(tmp_path, callback_server):
    """Out-of-band resume: emit-only → resume true → status reflects approval."""
    s = callback_server()
    webhook = f"http://127.0.0.1:{s.server.server_address[1]}/webhook"

    # Step 1 — emit-only request
    r = _run(APPROVAL, "--repo-root", str(tmp_path),
              "request", "--webhook-url", webhook, "--emit-only")
    rid = json.loads(r.stdout)["request_id"]

    # Step 2 — resume with approved=true
    r2 = _run(APPROVAL, "--repo-root", str(tmp_path),
               "resume", "--request-id", rid,
               "--approved", "true", "--approver", "bob")
    d2 = json.loads(r2.stdout)
    assert d2["status"] == "approved"
    assert d2["approver"] == "bob"

    # Step 3 — status confirms
    r3 = _run(APPROVAL, "--repo-root", str(tmp_path),
               "status", "--request-id", rid)
    d3 = json.loads(r3.stdout)
    assert d3["status"] == "approved"


def test_approval_gate_resume_denial_exits_2(tmp_path, callback_server):
    s = callback_server()
    webhook = f"http://127.0.0.1:{s.server.server_address[1]}/webhook"
    r = _run(APPROVAL, "--repo-root", str(tmp_path),
              "request", "--webhook-url", webhook, "--emit-only")
    rid = json.loads(r.stdout)["request_id"]

    r2 = _run(APPROVAL, "--repo-root", str(tmp_path),
               "resume", "--request-id", rid,
               "--approved", "false",
               "--reason", "scope creep",
               check=False)
    assert r2.returncode == 2
    d2 = json.loads(r2.stdout)
    assert d2["status"] == "denied"
    assert d2["denial_reason"] == "scope creep"


def test_approval_gate_list_lists_all_requests(tmp_path, callback_server):
    s = callback_server()
    webhook = f"http://127.0.0.1:{s.server.server_address[1]}/webhook"
    # Create 3 requests
    ids = []
    for _ in range(3):
        r = _run(APPROVAL, "--repo-root", str(tmp_path),
                  "request", "--webhook-url", webhook, "--emit-only")
        ids.append(json.loads(r.stdout)["request_id"])

    lst = _run(APPROVAL, "--repo-root", str(tmp_path), "list")
    data = json.loads(lst.stdout)
    assert data["total"] == 3
    assert {a["request_id"] for a in data["approvals"]} == set(ids)
    assert all(a["status"] == "pending" for a in data["approvals"])


def test_approval_gate_unreachable_webhook_returns_error(tmp_path):
    """Webhook is down → error status (not crash)."""
    proc = _run(APPROVAL, "--repo-root", str(tmp_path),
                 "request",
                 "--webhook-url", "http://127.0.0.1:65534/never",
                 "--emit-only", check=False)
    assert proc.returncode == 1
    data = json.loads(proc.stdout)
    assert data["status"] == "error"


def test_approval_gate_resume_rejects_non_pending(tmp_path, callback_server):
    s = callback_server()
    webhook = f"http://127.0.0.1:{s.server.server_address[1]}/webhook"
    r = _run(APPROVAL, "--repo-root", str(tmp_path),
              "request", "--webhook-url", webhook, "--emit-only")
    rid = json.loads(r.stdout)["request_id"]
    # Approve once
    _run(APPROVAL, "--repo-root", str(tmp_path),
          "resume", "--request-id", rid, "--approved", "true")
    # Try to re-approve — should refuse
    proc = _run(APPROVAL, "--repo-root", str(tmp_path),
                 "resume", "--request-id", rid,
                 "--approved", "false", "--reason", "changed my mind",
                 check=False)
    assert proc.returncode == 1
    err = json.loads(proc.stderr)
    assert "pending" in err["reason"]


# ─── Session driver: new flags exist ──────────────────────────────────────

def test_session_driver_accepts_require_approval_webhook_flag():
    """Confirms the flag is registered + the help text describes it."""
    proc = subprocess.run(
        [sys.executable, str(DRIVER), "--help"],
        capture_output=True, text=True, encoding="utf-8", timeout=10,
    )
    assert proc.returncode == 0
    assert "--require-approval-webhook" in proc.stdout
    assert "--approval-callback-url" in proc.stdout
    assert "--approval-timeout-minutes" in proc.stdout
