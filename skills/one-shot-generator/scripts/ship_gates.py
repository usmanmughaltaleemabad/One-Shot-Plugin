#!/usr/bin/env python3
"""
Ship Gates — v1.0.0  (production-readiness checklist)

Runs deterministic gates before allowing `--apply` in production. Mirrors
the structure of Addy Osmani's shipping-and-launch skill but tailored
to what /one-shot actually produces: a tree of generated code + a
migration + a wire plan.

Gates run in three domains, each producing PASS / WARN / FAIL:

  CODE_AND_SECURITY
    - tests_pass            (pytest exits 0)
    - no_secrets_in_diff    (grep for api_key, password, BEGIN PRIVATE KEY, …)
    - no_TODO_or_FIXME      (open todos in just-generated files = scope incomplete)
    - migration_reversible  (Alembic / Django migration has downgrade)

  INFRASTRUCTURE_AND_DOCS
    - env_vars_documented   (.env.example exists; new env reads referenced)
    - health_endpoint_exists  (a /livez or /readyz route present anywhere)
    - openapi_doc_generated (FastAPI/NestJS only — /docs reachable)

  ROLLOUT_READINESS
    - feature_flag_present  (looking for is_enabled / get_flag patterns)
    - rollback_path         (.osp.bak files present from wirer)
    - canary_plan           (a small markdown stating ramp %s, halt conditions)

Output (JSON):
    {
      "verdict": "READY" | "BLOCKED" | "READY_WITH_WARN",
      "gates": [
        {"name": "tests_pass", "status": "PASS", "detail": "..."},
        ...
      ],
      "summary": "9 PASS, 1 WARN, 0 FAIL"
    }

Exit code: 0 if READY or READY_WITH_WARN; 1 if BLOCKED.

CLI:
    ship_gates.py --project <dir> [--strict]

--strict promotes WARN to FAIL.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from lib.base_script import bootstrap_runtime, setup_logging
bootstrap_runtime()
logger = setup_logging(__name__)


# ─── Gate result type ──────────────────────────────────────────────────────

@dataclass
class GateResult:
    name: str
    status: str          # PASS | WARN | FAIL | SKIP
    detail: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# ─── Helpers ───────────────────────────────────────────────────────────────

SECRET_PATTERNS = [
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"api[_-]?key\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}['\"]", re.I),
    re.compile(r"password\s*[:=]\s*['\"][^'\"]{6,}['\"]", re.I),
    re.compile(r"AKIA[0-9A-Z]{16}"),                              # AWS
    re.compile(r"AIza[0-9A-Za-z_-]{35}"),                          # Google
    re.compile(r"ghp_[0-9A-Za-z]{36}"),                            # GitHub PAT
    re.compile(r"xox[bpoa]-[0-9A-Za-z-]{10,}"),                   # Slack
]

# Patterns that mean "this file is unfinished, not ready to ship".
TODO_PATTERNS = [
    re.compile(r"\bTODO\b"),
    re.compile(r"\bFIXME\b"),
    re.compile(r"\bXXX\b"),
    re.compile(r"raise\s+NotImplementedError"),
    re.compile(r"throw\s+new\s+Error\(['\"]Not implemented"),
]


def _iter_code_files(project: Path) -> List[Path]:
    """Generated code files in the project (skip vendored / cache dirs)."""
    skip = {".git", "node_modules", "__pycache__", ".venv", "venv", ".tmp",
            ".pytest_cache", ".mypy_cache", "dist", "build"}
    exts = {".py", ".js", ".ts", ".java", ".go", ".sql"}
    out: List[Path] = []
    for p in project.rglob("*"):
        if not p.is_file():
            continue
        if any(part in skip for part in p.parts):
            continue
        if p.suffix.lower() in exts:
            out.append(p)
    return out


def _downgrade_body_is_meaningful(text: str) -> bool:
    """Parse the alembic migration text for `def downgrade(...)` and return
    True iff the body contains anything other than `pass`, ellipsis, comments,
    or docstrings. Robust against quirky formatting."""
    m = re.search(r"^def downgrade\([^)]*\)\s*:\s*\n", text, re.M)
    if not m:
        return False
    # Collect body lines: indented lines after the def, until dedent.
    body_start = m.end()
    body_lines: List[str] = []
    for line in text[body_start:].splitlines():
        if not line.strip():
            body_lines.append("")
            continue
        if line.startswith((" ", "\t")):
            body_lines.append(line)
        else:
            break
    # Strip docstrings (triple-quoted) and comments + whitespace.
    body = "\n".join(body_lines)
    # Remove triple-quoted docstrings
    body = re.sub(r'"""[\s\S]*?"""', "", body)
    body = re.sub(r"'''[\s\S]*?'''", "", body)
    # Remove single-line comments
    body = re.sub(r"#[^\n]*", "", body)
    # Strip whitespace from each line, drop empties + `pass` + `...`
    meaningful = [
        ln.strip() for ln in body.splitlines()
        if ln.strip() and ln.strip() not in ("pass", "...")
    ]
    return len(meaningful) > 0


def _grep(files: List[Path], patterns: List[re.Pattern]) -> List[Tuple[Path, int, str]]:
    hits: List[Tuple[Path, int, str]] = []
    for f in files:
        try:
            lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for lineno, line in enumerate(lines, start=1):
            for pat in patterns:
                if pat.search(line):
                    hits.append((f, lineno, line.strip()[:120]))
                    break
    return hits


# ─── Gates ─────────────────────────────────────────────────────────────────

def gate_tests_pass(project: Path) -> GateResult:
    if not (project / "tests").exists() and not list(project.glob("test_*.py")) \
            and not list(project.glob("*_test.py")):
        return GateResult("tests_pass", "SKIP", "no test directory or test_*.py files found")
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--no-header"],
        capture_output=True, text=True, cwd=str(project), encoding="utf-8",
    )
    if proc.returncode == 0:
        return GateResult("tests_pass", "PASS",
                          (proc.stdout.splitlines()[-1] if proc.stdout else "").strip())
    return GateResult("tests_pass", "FAIL",
                      f"pytest exit {proc.returncode}; last line: "
                      f"{(proc.stdout.splitlines()[-1] if proc.stdout else '').strip()}")


def gate_no_secrets(project: Path) -> GateResult:
    hits = _grep(_iter_code_files(project), SECRET_PATTERNS)
    if not hits:
        return GateResult("no_secrets_in_diff", "PASS", "no secret-pattern matches")
    samples = [f"{p.relative_to(project)}:{ln}" for p, ln, _ in hits[:3]]
    return GateResult("no_secrets_in_diff", "FAIL",
                      f"{len(hits)} suspected secret(s): {samples}")


def gate_no_todos(project: Path) -> GateResult:
    hits = _grep(_iter_code_files(project), TODO_PATTERNS)
    if not hits:
        return GateResult("no_TODO_or_FIXME", "PASS", "no TODO/FIXME/NotImplementedError")
    samples = [f"{p.relative_to(project)}:{ln}" for p, ln, _ in hits[:3]]
    # Many TODOs from a single feature = WARN; > 10 = FAIL.
    status = "FAIL" if len(hits) > 10 else "WARN"
    return GateResult("no_TODO_or_FIXME", status,
                      f"{len(hits)} TODO/FIXME marker(s): {samples}")


def gate_migration_reversible(project: Path) -> GateResult:
    alembic_dir = project / "alembic" / "versions"
    django_migrations = list(project.glob("*/migrations/[0-9]*.py"))

    if alembic_dir.exists():
        latest = sorted(alembic_dir.glob("*.py"))
        if not latest:
            return GateResult("migration_reversible", "SKIP", "no Alembic revisions")
        latest_rev = max(latest, key=lambda p: p.stat().st_mtime)
        text = latest_rev.read_text(encoding="utf-8", errors="replace")
        if _downgrade_body_is_meaningful(text):
            return GateResult("migration_reversible", "PASS",
                              f"{latest_rev.name} has non-pass downgrade")
        return GateResult("migration_reversible", "FAIL",
                          f"{latest_rev.name} downgrade is empty / `pass` — not reversible")

    if django_migrations:
        latest_dj = max(django_migrations, key=lambda p: p.stat().st_mtime)
        text = latest_dj.read_text(encoding="utf-8", errors="replace")
        # Django auto-emits reverse migrations unless RunPython without reverse_code
        if "RunPython" in text and "reverse_code" not in text:
            return GateResult("migration_reversible", "WARN",
                              f"{latest_dj.name} uses RunPython without reverse_code")
        return GateResult("migration_reversible", "PASS",
                          f"{latest_dj.name} appears reversible")

    return GateResult("migration_reversible", "SKIP",
                      "no Alembic / Django migration directory")


def gate_env_documented(project: Path) -> GateResult:
    example = project / ".env.example"
    if not example.exists():
        return GateResult("env_vars_documented", "WARN",
                          "no .env.example — consumers can't tell what vars to set")
    # Check code references some env reads.
    code_files = _iter_code_files(project)
    env_pattern = re.compile(r"\bos\.environ\b|\bos\.getenv\b|\bprocess\.env\b|@Value\(")
    hits = _grep(code_files, [env_pattern])
    if not hits:
        return GateResult("env_vars_documented", "PASS",
                          ".env.example exists; no env reads detected in code")
    return GateResult("env_vars_documented", "PASS",
                      f".env.example exists; code reads env in {len(hits)} location(s)")


def gate_health_endpoint(project: Path) -> GateResult:
    code = _iter_code_files(project)
    pat = re.compile(
        r"['\"]/(?:livez|readyz|healthz|health)['\"]"
        r"|@GetMapping\(['\"]/(?:livez|readyz|healthz|health)"
        r"|router\.get\(['\"]/(?:livez|readyz|healthz|health)"
    )
    hits = _grep(code, [pat])
    if hits:
        return GateResult("health_endpoint_exists", "PASS",
                          f"found in {hits[0][0].relative_to(project)}")
    return GateResult("health_endpoint_exists", "WARN",
                      "no /livez, /readyz, /healthz, or /health route detected")


def gate_openapi_doc(project: Path) -> GateResult:
    # FastAPI: app = FastAPI(); /docs comes free
    # NestJS: SwaggerModule.setup
    # Spring: springdoc-openapi dep + @OpenAPIDefinition or just the dep
    code = _iter_code_files(project)
    pat = re.compile(r"FastAPI\(|SwaggerModule\.setup|springdoc-openapi|@OpenAPIDefinition")
    hits = _grep(code, [pat])
    if hits:
        return GateResult("openapi_doc_generated", "PASS",
                          f"found in {hits[0][0].relative_to(project)}")
    return GateResult("openapi_doc_generated", "SKIP",
                      "framework doesn't appear to ship OpenAPI docs (Go / raw Express)")


def gate_feature_flag(project: Path) -> GateResult:
    code = _iter_code_files(project)
    pat = re.compile(
        r"is_enabled\(|isEnabled\(|get_flag\(|flags\.|featureFlag|"
        r"@FeatureFlag|LaunchDarkly|Unleash|Flagsmith"
    )
    hits = _grep(code, [pat])
    if hits:
        return GateResult("feature_flag_present", "PASS",
                          f"flag usage in {hits[0][0].relative_to(project)}")
    return GateResult("feature_flag_present", "WARN",
                      "no feature-flag pattern detected — direct release without canary capability")


def gate_rollback_path(project: Path) -> GateResult:
    backups = list(project.rglob("*.osp.bak"))
    if backups:
        return GateResult("rollback_path", "PASS",
                          f"{len(backups)} .osp.bak file(s) present (wirer ran)")
    return GateResult("rollback_path", "WARN",
                      "no .osp.bak — wirer didn't run, or already cleaned up. "
                      "Verify rollback path before --apply.")


def gate_canary_plan(project: Path) -> GateResult:
    candidates = [
        project / "ROLLOUT.md",
        project / "docs" / "ROLLOUT.md",
        project / "docs" / "rollout.md",
        project / "CANARY.md",
    ]
    for c in candidates:
        if c.exists():
            text = c.read_text(encoding="utf-8", errors="replace").lower()
            has_ramp = any(s in text for s in ["%", "canary", "ramp", "rollout"])
            has_halt = any(s in text for s in ["halt", "rollback", "abort", "error rate"])
            if has_ramp and has_halt:
                return GateResult("canary_plan", "PASS",
                                  f"{c.relative_to(project)} documents ramp + halt conditions")
            return GateResult("canary_plan", "WARN",
                              f"{c.relative_to(project)} exists but missing ramp or halt conditions")
    return GateResult("canary_plan", "WARN",
                      "no ROLLOUT.md / CANARY.md found — no documented ramp plan")


# ─── Orchestration ─────────────────────────────────────────────────────────

ALL_GATES: List[Tuple[str, Callable[[Path], GateResult]]] = [
    ("tests_pass",            gate_tests_pass),
    ("no_secrets_in_diff",    gate_no_secrets),
    ("no_TODO_or_FIXME",      gate_no_todos),
    ("migration_reversible",  gate_migration_reversible),
    ("env_vars_documented",   gate_env_documented),
    ("health_endpoint_exists", gate_health_endpoint),
    ("openapi_doc_generated", gate_openapi_doc),
    ("feature_flag_present",  gate_feature_flag),
    ("rollback_path",         gate_rollback_path),
    ("canary_plan",           gate_canary_plan),
]


def run_gates(project: Path, *, strict: bool = False) -> dict:
    results: List[GateResult] = []
    for _, fn in ALL_GATES:
        try:
            results.append(fn(project))
        except Exception as e:
            results.append(GateResult(fn.__name__.replace("gate_", ""), "FAIL",
                                       f"gate raised: {type(e).__name__}: {e}"))

    by_status = {"PASS": 0, "WARN": 0, "FAIL": 0, "SKIP": 0}
    for r in results:
        by_status[r.status] = by_status.get(r.status, 0) + 1

    if strict:
        fail_count = by_status["FAIL"] + by_status["WARN"]
    else:
        fail_count = by_status["FAIL"]

    if fail_count > 0:
        verdict = "BLOCKED"
    elif by_status["WARN"] > 0:
        verdict = "READY_WITH_WARN"
    else:
        verdict = "READY"

    return {
        "verdict": verdict,
        "strict": strict,
        "summary": f"{by_status['PASS']} PASS, {by_status['WARN']} WARN, "
                   f"{by_status['FAIL']} FAIL, {by_status['SKIP']} SKIP",
        "gates": [r.to_dict() for r in results],
    }


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description="Production-readiness gates.")
    p.add_argument("--project", required=True, type=Path)
    p.add_argument("--strict", action="store_true",
                   help="Promote WARN to FAIL.")
    args = p.parse_args(argv if argv is not None else sys.argv[1:])

    if not args.project.exists():
        print(f"project not found: {args.project}", file=sys.stderr)
        return 1
    result = run_gates(args.project, strict=args.strict)
    print(json.dumps(result, indent=2))
    return 0 if result["verdict"] != "BLOCKED" else 1


if __name__ == "__main__":
    sys.exit(main())
