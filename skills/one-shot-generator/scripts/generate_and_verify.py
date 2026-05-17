#!/usr/bin/env python3
"""
Generate-and-Verify Loop — v0.8.0

Closed-loop wrapper around any generator. The protocol:

    1. Run the generator to produce a set of files.
    2. Write those files to an isolated sandbox directory.
    3. Statically verify each generated Python file (compile, plus a
       handful of cheap semantic checks).
    4. If anything fails, hand the captured diagnostics back so a caller
       (a Claude-driven loop or the harness) can request another attempt.
    5. Repeat up to ``max_iterations``; return a structured report.

This script is intentionally framework-agnostic. The "generator" is just a
Python callable that returns ``{filename: content}``; the script knows
nothing about Phase 2 vs Phase 4. It exposes a CLI too so callers can
verify an already-generated directory without re-running the generator.

CLI:
    # Verify a directory of generated files
    python generate_and_verify.py --verify-dir ./generated_output

    # Run a phase2 generation and verify it in one go
    python generate_and_verify.py \\
        --task "add product CRUD" \\
        --project /path/to/fastapi-shop \\
        --phase phase2 \\
        --max-iterations 3
"""

from __future__ import annotations

import argparse
import ast
import importlib
import json
import re
import subprocess
import sys
import tempfile
import textwrap
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from lib.base_script import bootstrap_runtime, setup_logging
bootstrap_runtime()

logger = setup_logging(__name__)


# ─── Diagnostics ─────────────────────────────────────────────────────────────

@dataclass
class Diagnostic:
    file: str
    line: Optional[int]
    severity: str            # error | warning
    code: str                # syntax | import | empty_file | semantic
    message: str

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class VerificationReport:
    sandbox: str
    iteration: int
    files_written: List[str]
    diagnostics: List[Diagnostic]
    succeeded: bool

    def to_dict(self) -> Dict:
        return {
            "sandbox": self.sandbox,
            "iteration": self.iteration,
            "files_written": self.files_written,
            "diagnostics": [d.to_dict() for d in self.diagnostics],
            "succeeded": self.succeeded,
        }


# ─── Static checks ───────────────────────────────────────────────────────────

def _check_syntax(file: Path) -> List[Diagnostic]:
    try:
        compile(file.read_text(encoding="utf-8"), str(file), "exec")
        return []
    except SyntaxError as exc:
        return [Diagnostic(
            file=str(file.name),
            line=exc.lineno,
            severity="error",
            code="syntax",
            message=f"{exc.msg} at column {exc.offset}",
        )]


_TEMPLATE_PLACEHOLDER_RE = re.compile(
    r"\{(plural|resource|entity|aggregate|module)\}"
)


def _check_unsubstituted_templates(file: Path) -> List[Diagnostic]:
    """Flag generator templates that still contain unsubstituted placeholders.

    Catches bugs like the `{plural}` / `{resource}` issue that shipped in
    Phase 2 (fixed in the previous validation pass). Recurring this check
    on every generator output prevents the bug from coming back.
    """
    text = file.read_text(encoding="utf-8")
    diagnostics: List[Diagnostic] = []
    for match in _TEMPLATE_PLACEHOLDER_RE.finditer(text):
        # Skip f-string contexts where a single-brace `{var}` is intentional
        # ── we only flag occurrences that sit inside a docstring or comment.
        start = match.start()
        line_start = text.rfind("\n", 0, start) + 1
        line_text = text[line_start:text.find("\n", start) if text.find("\n", start) != -1 else None]
        stripped = line_text.lstrip()
        if not (stripped.startswith('"""') or stripped.startswith("'''")
                or stripped.startswith("#")):
            continue
        diagnostics.append(Diagnostic(
            file=str(file.name),
            line=text.count("\n", 0, start) + 1,
            severity="error",
            code="semantic",
            message=f"unsubstituted generator placeholder: {match.group(0)}",
        ))
    return diagnostics


def _check_test_contract_alignment(
        files: Dict[str, str]) -> List[Diagnostic]:
    """Catch the test-asserts-X-but-router-does-Y class of bug.

    Looks for paired router + test files (same resource prefix) and checks:

    * if any test asserts a 401, the router file must reference `Depends`
      pointing at an auth-style dependency or have ``HTTPException(401`` /
      ``status_code=401``.
    * if any test asserts ``"next" in response.json()`` the router must
      return a paginated envelope (look for ``return {`` or ``Page(``).
    """
    out: List[Diagnostic] = []
    router_text: Dict[str, str] = {}
    test_text: Dict[str, str] = {}
    for name, content in files.items():
        path_lower = name.lower().replace("\\", "/")
        stem = Path(name).stem.lower()
        # Use the directory + stem so 'product/router.py' is keyed as 'product/router'
        composite_key = path_lower.removesuffix(".py")
        if "router" in path_lower or "views" in path_lower:
            router_text[composite_key] = content
        elif stem.startswith("test_") or stem.endswith("_test"):
            test_text[composite_key] = content

    auth_router_marker = re.compile(r"401|Depends\([^)]*(auth|user|token)",
                                    re.IGNORECASE)
    paginated_router_marker = re.compile(r"Page\(|paginate\(|return\s+\{")

    for tname, ttext in test_text.items():
        # Pair: extract a resource token from the test path and look for any
        # router path that contains it.
        token = Path(tname).stem.replace("test_", "").replace("_api", "")
        token = token.split("_")[0] if token else ""
        partner = next((rt for rb, rt in router_text.items()
                        if token and token in rb), None)
        if partner is None:
            continue
        if "401" in ttext and not auth_router_marker.search(partner):
            out.append(Diagnostic(
                file=tname,
                line=None,
                severity="warning",
                code="semantic",
                message="test asserts HTTP 401 but matching router has no auth dependency",
            ))
        if '"next"' in ttext and not paginated_router_marker.search(partner):
            out.append(Diagnostic(
                file=tname,
                line=None,
                severity="warning",
                code="semantic",
                message='test asserts "next" in response.json() but router returns a plain list',
            ))
    return out


def _check_empty_files(file: Path) -> List[Diagnostic]:
    # __init__.py files are intentionally empty in many cases — that's a
    # valid Python package marker, not a bug. Other files being empty is.
    if file.name == "__init__.py":
        return []
    content = file.read_text(encoding="utf-8").strip()
    if not content:
        return [Diagnostic(
            file=str(file.name),
            line=None,
            severity="error",
            code="empty_file",
            message="generated file is empty",
        )]
    return []


# ─── Writing helpers ─────────────────────────────────────────────────────────

def _flatten_generator_output(payload: Dict) -> Dict[str, str]:
    """Accept either ``{filename: content}`` or the phase2 shape
    ``{"code": {...}, "tests": {...}, "docs": {...}}`` and return flat map."""
    if "code" in payload or "tests" in payload or "docs" in payload:
        merged: Dict[str, str] = {}
        for section in ("code", "tests", "docs"):
            merged.update(payload.get(section, {}) or {})
        return merged
    if "files" in payload and isinstance(payload["files"], dict):
        return payload["files"]
    return {k: v for k, v in payload.items() if isinstance(v, str)}


def write_to_sandbox(files: Dict[str, str], sandbox: Path) -> List[str]:
    written: List[str] = []
    for name, content in files.items():
        path = sandbox / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        written.append(str(path.relative_to(sandbox)).replace("\\", "/"))
    return written


# ─── Verification ────────────────────────────────────────────────────────────

from lib.telemetry import traced as _traced


@_traced("verify_directory", attr_keys=["sandbox"])
def verify_directory(sandbox: Path, files: Dict[str, str]) -> List[Diagnostic]:
    diagnostics: List[Diagnostic] = []
    for path in sandbox.rglob("*.py"):
        diagnostics.extend(_check_empty_files(path))
        diagnostics.extend(_check_syntax(path))
        diagnostics.extend(_check_unsubstituted_templates(path))
    diagnostics.extend(_check_test_contract_alignment(files))
    return diagnostics


# ─── Generator runners ───────────────────────────────────────────────────────

def _run_phase2(task: str, project: str) -> Dict[str, str]:
    """Call phase2_runner programmatically and unwrap its result."""
    from phase2_runner import run_phase2_generation
    arg_str = f"{task} @{project}".strip()
    result = run_phase2_generation(arg_str)
    if result.get("status") != "success":
        raise RuntimeError(f"phase2 generator failed: {result.get('error')}")
    return _flatten_generator_output(result)


def _run_phase3(task: str, project: str) -> Dict[str, str]:
    """Call phase3_runner via subprocess so its argparse parses correctly."""
    cmd = [sys.executable,
           str(Path(__file__).parent / "phase3_batch_jobs" / "phase3_runner.py"),
           task + (f" @{project}" if project else "")]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    # phase3 writes files to disk by default; in --format json it emits JSON
    # to stdout. Try to parse, fall back to empty.
    text = proc.stdout
    open_brace = text.find("{")
    if open_brace == -1:
        raise RuntimeError(f"phase3 generator emitted no JSON; stderr=\n{proc.stderr}")
    try:
        payload = json.loads(text[open_brace:])
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"phase3 JSON parse failed: {exc}") from exc
    return _flatten_generator_output(payload)


GENERATORS: Dict[str, Callable[[str, str], Dict[str, str]]] = {
    "phase2": _run_phase2,
    "phase3": _run_phase3,
}


# ─── Main loop ───────────────────────────────────────────────────────────────

def run_loop(*, task: str, project: str, phase: str,
             max_iterations: int = 3,
             sandbox_base: Optional[Path] = None,
             codebase_imports: Optional[Dict[str, Dict]] = None,
             auto_patch: bool = True) -> List[VerificationReport]:
    """Closed-loop generate → verify → patch → re-verify.

    ``codebase_imports`` is the ``CodebaseGraph.imports`` map; when present
    the auto-patcher rewrites the default ``from database import get_db``
    style imports to point at the project's actual module path.
    """
    if phase not in GENERATORS:
        raise ValueError(f"unknown phase: {phase}. options: {list(GENERATORS)}")
    generator = GENERATORS[phase]

    reports: List[VerificationReport] = []
    sandbox_root = sandbox_base or Path(tempfile.mkdtemp(prefix="osp-verify-"))
    sandbox_root.mkdir(parents=True, exist_ok=True)
    last_files: Dict[str, str] = {}

    for iteration in range(1, max_iterations + 1):
        sandbox = sandbox_root / f"iter_{iteration}"
        sandbox.mkdir(parents=True, exist_ok=True)
        try:
            files = generator(task, project)
        except Exception as exc:
            reports.append(VerificationReport(
                sandbox=str(sandbox),
                iteration=iteration,
                files_written=[],
                diagnostics=[Diagnostic(
                    file="<generator>", line=None, severity="error",
                    code="generator_crash", message=str(exc),
                )],
                succeeded=False,
            ))
            break
        written = write_to_sandbox(files, sandbox)
        diags = verify_directory(sandbox, files)

        # ── auto-patch attempt ────────────────────────────────────────
        # If there are any diagnostics (errors OR warnings) and auto_patch
        # is enabled, try to fix them deterministically before declaring
        # this iteration done.
        patched = False
        if auto_patch and diags:
            try:
                from auto_patch import patch as _patch
                hint = _resource_hint_from_task(task)
                patch_report = _patch(
                    sandbox=sandbox,
                    diagnostics=[d.to_dict() for d in diags],
                    codebase_imports=codebase_imports,
                    resource_hint=hint,
                )
                if patch_report.actions:
                    patched = True
                    # Re-read files from the sandbox after patching
                    refreshed: Dict[str, str] = {}
                    for path in sandbox.rglob("*"):
                        if path.is_file():
                            rel = str(path.relative_to(sandbox)).replace("\\", "/")
                            try:
                                refreshed[rel] = path.read_text(encoding="utf-8")
                            except Exception:
                                continue
                    files = refreshed
                    # Re-verify against the patched files
                    diags = verify_directory(sandbox, files)
                    for action in patch_report.actions:
                        diags.append(Diagnostic(
                            file=action.file, line=action.line,
                            severity="info", code="auto_patched",
                            message=f"{action.rule}: {action.description}",
                        ))
            except Exception as exc:
                logger.warning("auto-patch attempt failed: %s", exc)

        succeeded = not any(d.severity == "error" for d in diags)
        reports.append(VerificationReport(
            sandbox=str(sandbox),
            iteration=iteration,
            files_written=written,
            diagnostics=diags,
            succeeded=succeeded,
        ))
        last_files = files
        if succeeded:
            break
        logger.info(
            "iteration %d %s with %d diagnostics — looping",
            iteration,
            "patched" if patched else "failed",
            len(diags),
        )

    return reports


_RESOURCE_HINT_STOPWORDS = {
    "add", "create", "build", "generate", "make", "develop", "implement",
    "scaffold", "design", "draft", "ship", "extend", "expand",
    "a", "an", "the", "with", "for", "to", "of", "in", "on", "and", "or",
    "api", "crud", "rest", "endpoint", "endpoints",
}


def _resource_hint_from_task(task: str) -> Optional[str]:
    """Best-effort guess for the resource word the auto-patcher should use."""
    for token in re.findall(r"[a-zA-Z_]+", task.lower()):
        if token not in _RESOURCE_HINT_STOPWORDS:
            return token
    return None


# ─── CLI ─────────────────────────────────────────────────────────────────────

def _emit_summary(reports: List[VerificationReport]) -> None:
    last = reports[-1]
    print("VERIFICATION REPORT")
    print("─" * 60)
    print(f"  Iterations:   {len(reports)}")
    print(f"  Last sandbox: {last.sandbox}")
    print(f"  Files:        {len(last.files_written)}")
    print(f"  Result:       {'✅ PASS' if last.succeeded else '❌ FAIL'}")
    if last.diagnostics:
        print()
        print("DIAGNOSTICS")
        for d in last.diagnostics:
            line = f"L{d.line}" if d.line else "—"
            print(f"  [{d.severity}] {d.file}:{line}  {d.code}: {d.message}")
    print()
    print("---JSON---")
    print(json.dumps([r.to_dict() for r in reports], indent=2))


def main():
    parser = argparse.ArgumentParser(
        description="Generate-and-verify loop for one-shot-prompting"
    )
    parser.add_argument("--task", help="Feature description for the generator")
    parser.add_argument("--project", default="",
                        help="Path to user's project (for codebase-aware generation)")
    parser.add_argument("--phase", choices=list(GENERATORS),
                        help="Which generator to invoke")
    parser.add_argument("--max-iterations", type=int, default=3)
    parser.add_argument("--sandbox", default=None,
                        help="Sandbox directory (default: temp)")
    parser.add_argument("--verify-dir",
                        help="Skip generation; just verify an existing directory")
    args = parser.parse_args()

    if args.verify_dir:
        sandbox = Path(args.verify_dir).resolve()
        files = {}
        for path in sandbox.rglob("*"):
            if path.is_file():
                try:
                    files[str(path.relative_to(sandbox)).replace("\\", "/")] = \
                        path.read_text(encoding="utf-8")
                except Exception:
                    continue
        diags = verify_directory(sandbox, files)
        report = VerificationReport(
            sandbox=str(sandbox),
            iteration=1,
            files_written=list(files),
            diagnostics=diags,
            succeeded=not any(d.severity == "error" for d in diags),
        )
        _emit_summary([report])
        sys.exit(0 if report.succeeded else 1)

    if not args.task or not args.phase:
        parser.error("--task and --phase are required when not using --verify-dir")

    sandbox_base = Path(args.sandbox).resolve() if args.sandbox else None
    reports = run_loop(task=args.task, project=args.project,
                       phase=args.phase, max_iterations=args.max_iterations,
                       sandbox_base=sandbox_base)
    _emit_summary(reports)
    sys.exit(0 if reports[-1].succeeded else 1)


if __name__ == "__main__":
    main()
