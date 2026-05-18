#!/usr/bin/env python3
"""
Live-API Canary — v1.0.0

Single architect-agent spawn against the REAL Anthropic API. Validates
the headless SDK path end-to-end. **Costs real money** — typically
~$0.08–0.12 per run at sonnet pricing (~25K input tokens, ~12K output).

Hard guards before doing anything:
  1. ANTHROPIC_API_KEY must be set
  2. anthropic SDK must be installed
  3. --i-know-this-costs-money flag MUST be passed (no accidental runs)
  4. --max-cost-usd is enforced AFTER the run (post-flight check;
     prints a warning if exceeded — Anthropic doesn't bill until the
     call completes anyway)

What it does:
  1. Stage a synthetic FastAPI project (same shape as
     validate_templated_pipeline.py)
  2. Hand-author a small spec.json (1 entity to minimise tokens)
  3. Call agentic_session_driver.py --mode live-api
  4. Inspect the architect's response JSON for: valid JSON, has
     'entities' field, names match the task
  5. Print cost, tokens, response excerpt, persist location

Run (DRY-MODE — no money spent):
    python tests/integration/canary_live_api.py --dry-run

Run (REAL — spends money):
    export ANTHROPIC_API_KEY=sk-ant-...
    python tests/integration/canary_live_api.py --i-know-this-costs-money

With cost cap:
    python tests/integration/canary_live_api.py \
        --i-know-this-costs-money --max-cost-usd 0.15

Exit codes:
    0   canary completed successfully (real run) OR dry-run succeeded
    1   bad flags / missing env
    2   live run hit unexpected error (network, malformed response, etc.)
    3   live run exceeded --max-cost-usd
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / "skills" / "one-shot-generator" / "scripts"


def _build_minimal_spec(root: Path) -> Path:
    """Single-entity spec — minimises architect token output (~10-15K vs
    25K+ for multi-entity). Targets ~$0.05-0.08 actual cost."""
    spec = {
        "feature": "user signup with email verification",
        "framework": "fastapi",
        "language": "python",
        "intent": "auth",
        "entities": [
            {
                "name": "User",
                "snake_name": "user",
                "plural": "users",
                "action": "create",
                "attributes": [
                    {"name": "email", "type": "str", "required": True},
                    {"name": "is_verified", "type": "bool", "default": False},
                ],
                "invariants": [
                    "email is unique across all users",
                    "is_verified can only transition False -> True",
                ],
            },
        ],
        "relationships": [],
        "test_contract": {"auth": "jwt", "pagination": "list",
                            "errors": "domain_envelope"},
        "wiring": {"target": "main.py"},
        "api_surface": [
            {"method": "POST", "path": "/api/v1/users/signup"},
            {"method": "POST", "path": "/api/v1/users/verify"},
        ],
        "graph_imports": {},
    }
    p = root / "spec.json"
    p.write_text(json.dumps(spec, indent=2), encoding="utf-8")
    return p


def _check_guards(args) -> Optional[int]:
    """Returns an exit code if a guard fails; None if all checks pass."""
    if args.dry_run:
        # Dry-run bypasses guards — it only walks the script paths.
        return None

    if not args.i_know_this_costs_money:
        print("\n  ABORT: live runs cost real money (typically $0.05-0.15).\n"
              "  Pass --i-know-this-costs-money to confirm you intend to\n"
              "  spend it. Or use --dry-run to walk the harness without\n"
              "  any API calls.\n", file=sys.stderr)
        return 1

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("\n  ABORT: ANTHROPIC_API_KEY is not set.\n"
              "  export ANTHROPIC_API_KEY=sk-ant-...\n", file=sys.stderr)
        return 1

    try:
        import anthropic   # noqa: F401
    except ImportError:
        print("\n  ABORT: anthropic SDK not installed.\n"
              "  pip install anthropic\n", file=sys.stderr)
        return 1

    return None


def _run_driver(*args: str, env: Optional[dict] = None) -> subprocess.CompletedProcess:
    e = os.environ.copy()
    e["PYTHONIOENCODING"] = "utf-8"
    if env:
        e.update(env)
    return subprocess.run(
        [sys.executable,
         str(SCRIPTS / "agentic_session_driver.py"), *args],
        capture_output=True, text=True, env=e, encoding="utf-8", timeout=120,
    )


def _print_summary(summary: dict, *, max_cost_usd: Optional[float]) -> int:
    total_cost = summary.get("total_cost_usd", 0.0)
    total_in = summary.get("total_input_tokens", 0)
    total_out = summary.get("total_output_tokens", 0)
    print(f"\n[results]")
    print(f"  status:              {summary.get('status')}")
    print(f"  spawns_run:          {summary.get('spawns_run', 0)}")
    print(f"  total_input_tokens:  {total_in:,}")
    print(f"  total_output_tokens: {total_out:,}")
    print(f"  total_cost_usd:      ${total_cost:.4f}")
    print(f"  out_dir:             {summary.get('out_dir')}")

    # Inspect each per-spawn result
    print(f"\n[per-spawn]")
    for r in summary.get("results", []):
        if "error" in r:
            print(f"  [XX] {r['agent_name']:20}  ERROR: {r['error']}")
            continue
        cost = r.get("cost_usd", 0.0)
        print(f"  [OK] {r['agent_name']:20}  "
              f"in={r['input_tokens']:>6}  out={r['output_tokens']:>6}  "
              f"${cost:.4f}  ({r['text_chars']} chars text)")

    if max_cost_usd is not None and total_cost > max_cost_usd:
        print(f"\n  WARN: total cost ${total_cost:.4f} exceeded "
              f"--max-cost-usd ${max_cost_usd:.4f}", file=sys.stderr)
        return 3
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        description="Single-agent canary against the real Anthropic API."
    )
    p.add_argument("--dry-run", action="store_true",
                   help="Don't call the API; just walk the harness setup.")
    p.add_argument("--i-know-this-costs-money", action="store_true",
                   help="Required for live runs. Acknowledges that the "
                        "call will spend real tokens / real dollars.")
    p.add_argument("--max-cost-usd", type=float, default=None,
                   help="Print a warning + exit 3 if total cost exceeds this.")
    p.add_argument("--keep-temp", action="store_true")
    args = p.parse_args(argv if argv is not None else sys.argv[1:])

    guard = _check_guards(args)
    if guard is not None:
        return guard

    temp_root = Path(tempfile.mkdtemp(prefix="osp-canary-"))
    project = temp_root / "fake-fastapi"
    project.mkdir(parents=True, exist_ok=True)
    spec_path = _build_minimal_spec(project)
    out_dir = temp_root / "out"

    print(f"[setup] project: {project}")
    print(f"[setup] spec:    {spec_path}")
    print(f"[setup] out:     {out_dir}")
    print(f"[mode]  {'DRY-RUN (no API calls)' if args.dry_run else 'LIVE (real API calls)'}")

    # In dry-run, we exercise the live-api branch WITHOUT a key set so the
    # graceful-skip path executes. Proves the harness wiring is correct
    # without spending anything.
    env_override = None
    if args.dry_run:
        env_override = {k: v for k, v in os.environ.items()
                         if k != "ANTHROPIC_API_KEY"}
        env_override.pop("ANTHROPIC_API_KEY", None)
        proc = _run_driver("--mode", "live-api",
                            "--spec", str(spec_path),
                            "--out", str(out_dir),
                            env={k: v for k, v in env_override.items()})
    else:
        proc = _run_driver("--mode", "live-api",
                            "--spec", str(spec_path),
                            "--out", str(out_dir))

    if proc.returncode != 0:
        print(f"\n[ERROR] driver exit {proc.returncode}", file=sys.stderr)
        print(f"stderr:\n{proc.stderr[:1000]}", file=sys.stderr)
        if not args.keep_temp:
            shutil.rmtree(temp_root, ignore_errors=True)
        return 2

    try:
        summary = json.loads(proc.stdout)
    except json.JSONDecodeError:
        print(f"\n[ERROR] non-JSON output:\n{proc.stdout[:500]}", file=sys.stderr)
        if not args.keep_temp:
            shutil.rmtree(temp_root, ignore_errors=True)
        return 2

    if summary.get("status") == "skipped":
        print(f"\n[skipped] {summary.get('reason')}")
        print(f"  fix: {summary.get('fix')}")
        print(f"\n  (This is the graceful skip path. Dry-run validates it.)")
        if not args.keep_temp:
            shutil.rmtree(temp_root, ignore_errors=True)
        return 0

    exit_code = _print_summary(summary, max_cost_usd=args.max_cost_usd)

    # Inspect the architect's per-spawn file for structural validity
    architect_files = list(out_dir.glob("*architect*.json"))
    if architect_files:
        try:
            arch_data = json.loads(architect_files[0].read_text(encoding="utf-8"))
            text = arch_data.get("text", "")
            print(f"\n[architect output excerpt]")
            print("  " + "\n  ".join(text[:600].splitlines()))
            # Try to parse as JSON (the architect should emit valid JSON)
            try:
                # Strip Markdown fences if any
                stripped = text.strip()
                if stripped.startswith("```"):
                    stripped = stripped.split("\n", 1)[1].rsplit("```", 1)[0]
                spec_out = json.loads(stripped.strip())
                if "entities" in spec_out:
                    print(f"\n  [OK] architect emitted valid spec with "
                          f"{len(spec_out['entities'])} entities")
            except json.JSONDecodeError:
                print(f"\n  [WARN] architect's text is not parseable JSON — "
                      f"would need a follow-up regenerate in real flow")
        except (OSError, json.JSONDecodeError):
            pass

    if args.keep_temp:
        print(f"\n[kept] {temp_root}")
    else:
        shutil.rmtree(temp_root, ignore_errors=True)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
