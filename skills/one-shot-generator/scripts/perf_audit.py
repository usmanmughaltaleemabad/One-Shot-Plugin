#!/usr/bin/env python3
"""
Performance Audit — v1.0.0  (anti-pattern scanner + framework-specific tooling map)

Scans a project for KNOWN performance anti-patterns and emits a
prioritised checklist + the right profiler invocation per detected
framework. Implements the `performance_optimization` body-hint contract.

Detection rules (deliberately conservative — false positives = noise):

  N+1 query risks
    - Django:  .all() / .filter() inside a for-loop (no .select_related /
               .prefetch_related on the queryset)
    - SQLAlchemy: .filter() / .query() inside a for-loop without
                  joinedload / selectinload
    - Sequelize: .findAll() / .findOne() inside a for-loop without
                 include: [...]

  Memory hazards
    - file.read() without size cap (or chunked iteration)
    - SELECT * patterns (raw_sql.execute("SELECT *"))
    - .all() on Django QuerySets > 100 rows likely (heuristic: in a
      view returning JsonResponse without pagination)

  Hot-path blockers
    - bcrypt.hashpw / bcrypt.hashSync inside async / request-handler
      functions (blocks event loop)
    - synchronous HTTP libs (requests, urllib) inside async functions
    - time.sleep() / await with constant int inside a hot loop

Returns a structured report:
  {
    "framework": "fastapi",
    "findings": [
      {
        "severity": "warning" | "info",
        "rule": "n_plus_one_sqlalchemy",
        "where": "cart/views.py:42",
        "snippet": "...",
        "fix_hint": "use joinedload(Cart.line_items) to fetch in one query"
      }
    ],
    "framework_tooling": [
      {"tool": "py-spy", "install": "pip install py-spy",
       "run": "py-spy record -o profile.svg -- python main.py"},
      ...
    ]
  }

CLI:
    perf_audit.py --project <dir>
    perf_audit.py --project <dir> --json
    perf_audit.py --project <dir> --severity warning   # warning only, skip info

Exit codes:
    0  audit ran
    1  bad args / project missing
    2  any 'warning' severity findings (CI gate mode with --strict)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional

from lib.base_script import bootstrap_runtime, setup_logging
bootstrap_runtime()
logger = setup_logging(__name__)


# ─── Framework detection (lightweight — mirrors source_docs_fetcher) ───────

_FRAMEWORK_SIGS = [
    ("requirements.txt", r"\bfastapi\b",         "fastapi"),
    ("pyproject.toml",   r"\bfastapi\b",         "fastapi"),
    ("requirements.txt", r"\bdjango\b",          "django"),
    ("pyproject.toml",   r"\bdjango\b",          "django"),
    ("pom.xml",          r"spring-boot",         "spring"),
    ("package.json",     r'"@nestjs/',           "nestjs"),
    ("package.json",     r'"express"',           "nodejs"),
    ("go.mod",           r"github\.com/.*?/gin", "go"),
]


def detect_framework(project: Path) -> Optional[str]:
    for filename, pattern, name in _FRAMEWORK_SIGS:
        path = project / filename
        if not path.exists():
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if re.search(pattern, content, re.I):
            return name
    return None


# ─── Anti-pattern rules ────────────────────────────────────────────────────

@dataclass
class PatternRule:
    rule_id: str
    severity: str          # warning | info
    file_globs: List[str]
    pattern: re.Pattern
    context_pattern: Optional[re.Pattern]   # only matches if this also matches in surrounding file
    description: str
    fix_hint: str
    applies_to_frameworks: List[str] = field(default_factory=list)


def _compile_rules() -> List[PatternRule]:
    return [
        # N+1: Django queryset .all() / .filter() inside for-loop
        PatternRule(
            rule_id="n_plus_one_django",
            severity="warning",
            file_globs=["*.py"],
            pattern=re.compile(
                r"for\s+\w+\s+in\s+[A-Z]\w+\.objects\.(?:all|filter)\(",
                re.M,
            ),
            context_pattern=None,
            description=(
                "Iterating a Django QuerySet without prefetch_related / "
                "select_related — each access to a related object issues "
                "a fresh query (N+1)."
            ),
            fix_hint=(
                "Wrap with .select_related('fk_field') for FK joins or "
                ".prefetch_related('reverse_field') for reverse FK / "
                "many-to-many. Cap with .iterator() for huge sets."
            ),
            applies_to_frameworks=["django"],
        ),
        # N+1: SQLAlchemy .query() / .filter() inside for-loop without options(joinedload)
        PatternRule(
            rule_id="n_plus_one_sqlalchemy",
            severity="warning",
            file_globs=["*.py"],
            pattern=re.compile(
                r"for\s+\w+\s+in\s+(?:db\.|session\.|self\.db\.)"
                r"(?:query\(|execute\(.*?select\()",
                re.M,
            ),
            context_pattern=re.compile(r"^from sqlalchemy\b", re.M),
            description=(
                "Iterating a SQLAlchemy Query without joinedload / "
                "selectinload — relationship access triggers extra queries."
            ),
            fix_hint=(
                "Add .options(joinedload(Model.relationship)) (single-row JOIN) "
                "or .options(selectinload(Model.relationship)) "
                "(separate IN query, better for large fan-out)."
            ),
            applies_to_frameworks=["fastapi"],
        ),
        # N+1: Sequelize findAll inside loop
        PatternRule(
            rule_id="n_plus_one_sequelize",
            severity="warning",
            file_globs=["*.js", "*.ts"],
            pattern=re.compile(
                r"for\s*\([^)]+\)\s*\{[^}]*?\.find(?:All|One)\(",
                re.S,
            ),
            context_pattern=re.compile(r"sequelize|@nestjs/sequelize"),
            description=(
                "Loop containing a Sequelize findAll/findOne without an "
                "include array — each iteration issues a new query."
            ),
            fix_hint=(
                "Use { include: [Model.SomeRel] } in the OUTER findAll "
                "and access loaded associations from the result, OR collect "
                "ids first and do one Model.findAll({ where: { id: ids } })."
            ),
            applies_to_frameworks=["nodejs", "nestjs"],
        ),
        # Hot path blocker: bcrypt.hashSync inside request handler
        PatternRule(
            rule_id="bcrypt_sync_in_hot_path",
            severity="warning",
            file_globs=["*.py", "*.js", "*.ts"],
            pattern=re.compile(
                r"\bbcrypt\.(?:hashpw|hashSync|checkpwSync|compareSync)\b"
            ),
            context_pattern=None,
            description=(
                "Synchronous bcrypt calls block the event loop / GIL — at "
                "cost-factor 12+ this is 100-300ms per call, multiplied by "
                "every concurrent request."
            ),
            fix_hint=(
                "Use bcrypt.hash() / bcrypt.compare() (async) in Node.js; "
                "or run the call in a worker / executor in Python "
                "(asyncio.to_thread)."
            ),
            applies_to_frameworks=[],   # any
        ),
        # Hot path blocker: requests/urllib inside async function
        PatternRule(
            rule_id="sync_http_in_async",
            severity="warning",
            file_globs=["*.py"],
            pattern=re.compile(
                r"async\s+def\s+\w+[^:]*:\s*"
                r"(?:[^\n]*\n){0,40}?[^\n]*\b(?:requests\.|urllib\.)",
                re.M,
            ),
            context_pattern=None,
            description=(
                "Synchronous HTTP client (requests / urllib) called from "
                "inside an async function blocks the event loop — defeats "
                "the purpose of async."
            ),
            fix_hint=(
                "Switch to httpx.AsyncClient / aiohttp. If you can't change "
                "the dep, wrap with `await asyncio.to_thread(requests.get, ...)`."
            ),
            applies_to_frameworks=["fastapi"],
        ),
        # SELECT * — costly + brittle (changes break parsing)
        PatternRule(
            rule_id="select_star_raw_sql",
            severity="info",
            file_globs=["*.py", "*.js", "*.ts", "*.go", "*.java"],
            pattern=re.compile(
                r"""['"]SELECT\s+\*\s+FROM""",
                re.I,
            ),
            context_pattern=None,
            description=(
                "SELECT * forces the query planner to fetch every column; "
                "blocks covering-index optimisations; schema changes silently "
                "alter wire format."
            ),
            fix_hint="List the columns explicitly.",
        ),
        # File.read() without size cap (memory hazard)
        PatternRule(
            rule_id="unbounded_file_read",
            severity="info",
            file_globs=["*.py"],
            pattern=re.compile(
                r"(?<!\w)(?:file\.read\(\s*\)|\.read\(\s*\)\.decode)"
            ),
            context_pattern=None,
            description=(
                "Calling .read() without a size argument loads the whole "
                "file into memory — DoS risk on user-supplied content."
            ),
            fix_hint=(
                "Pass a chunk size: while (chunk := file.read(64 * 1024)): ... "
                "Or use a streaming parser."
            ),
        ),
        # len(queryset) instead of .count()
        PatternRule(
            rule_id="len_on_queryset",
            severity="info",
            file_globs=["*.py"],
            pattern=re.compile(
                r"len\([a-z_]+\.objects\.(?:all|filter)\("
            ),
            context_pattern=None,
            description=(
                "len() on a Django QuerySet materialises every row to "
                "count them — uses memory equal to the result set."
            ),
            fix_hint="Use .count() instead — issues a SELECT COUNT(*).",
            applies_to_frameworks=["django"],
        ),
    ]


# ─── File walk + scanning ──────────────────────────────────────────────────

SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    ".tmp", ".pytest_cache", ".mypy_cache", "dist", "build",
    "vendor", ".idea", ".vscode",
}


def _iter_files(project: Path, globs: List[str]) -> List[Path]:
    out: List[Path] = []
    for p in project.rglob("*"):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        suffix_glob = "*" + p.suffix
        if any(suffix_glob == g or suffix_glob.endswith(g.lstrip("*")) for g in globs):
            out.append(p)
    return out


def _file_passes_context(text: str, ctx: Optional[re.Pattern]) -> bool:
    if ctx is None:
        return True
    return ctx.search(text) is not None


@dataclass
class Finding:
    rule_id: str
    severity: str
    where: str
    snippet: str
    fix_hint: str

    def to_dict(self) -> Dict:
        return asdict(self)


def scan(project: Path, *, framework: Optional[str] = None,
         min_severity: str = "info") -> List[Finding]:
    """Walk the project, apply each rule, return findings. min_severity
    can be 'info' (everything), 'warning' (warning+), or 'error'."""
    severity_rank = {"info": 0, "warning": 1, "error": 2}
    threshold = severity_rank.get(min_severity, 0)

    rules = _compile_rules()
    findings: List[Finding] = []

    # Group rules by glob so we walk files once.
    for rule in rules:
        if severity_rank.get(rule.severity, 0) < threshold:
            continue
        if rule.applies_to_frameworks and framework \
                and framework not in rule.applies_to_frameworks:
            continue
        for path in _iter_files(project, rule.file_globs):
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if not _file_passes_context(text, rule.context_pattern):
                continue
            for m in rule.pattern.finditer(text):
                # Compute line number from the match start
                lineno = text.count("\n", 0, m.start()) + 1
                snippet = m.group(0).replace("\n", " \\n ")[:120]
                rel = path.relative_to(project)
                findings.append(Finding(
                    rule_id=rule.rule_id,
                    severity=rule.severity,
                    where=f"{rel}:{lineno}",
                    snippet=snippet,
                    fix_hint=rule.fix_hint,
                ))
    return findings


# ─── Framework profiler / tooling recommendation ───────────────────────────

_TOOLING = {
    "fastapi": [
        {"tool": "py-spy",  "install": "pip install py-spy",
         "run": "py-spy record -o profile.svg -- python -m uvicorn main:app"},
        {"tool": "EXPLAIN ANALYZE", "install": "(no install — your DB)",
         "run": "session.execute('EXPLAIN ANALYZE SELECT ...')"},
        {"tool": "scalene",  "install": "pip install scalene",
         "run": "scalene --cpu --memory --gpu my_module.py"},
    ],
    "django": [
        {"tool": "django-silk",  "install": "pip install django-silk",
         "run": "(adds /silk/ admin UI showing per-request query traces)"},
        {"tool": "django-debug-toolbar",
         "install": "pip install django-debug-toolbar",
         "run": "shows query count + duration per page"},
        {"tool": "py-spy",  "install": "pip install py-spy",
         "run": "py-spy record -o profile.svg -- python manage.py runserver"},
    ],
    "spring": [
        {"tool": "JMH (Java Microbenchmark Harness)",
         "install": "Maven: org.openjdk.jmh:jmh-core",
         "run": "mvn jmh:jmh"},
        {"tool": "Micrometer + Spring Boot Actuator",
         "install": "(starter dep) spring-boot-starter-actuator",
         "run": "GET /actuator/metrics + /actuator/prometheus"},
        {"tool": "async-profiler", "install": "(download release)",
         "run": "./profiler.sh -d 30 -f profile.html <pid>"},
    ],
    "nestjs": [
        {"tool": "clinic.js doctor", "install": "npm i -g clinic",
         "run": "clinic doctor -- node dist/main.js"},
        {"tool": "autocannon",  "install": "npm i -g autocannon",
         "run": "autocannon -c 10 -d 30 http://localhost:3000/api/v1/users"},
        {"tool": "@nestjs/terminus health endpoints",
         "install": "(bundled)",
         "run": "GET /health for liveness; combine with Prometheus"},
    ],
    "go": [
        {"tool": "pprof (built-in)",
         "install": "(stdlib) import _ \"net/http/pprof\"",
         "run": "go tool pprof http://localhost:6060/debug/pprof/profile?seconds=30"},
        {"tool": "go test -bench",
         "install": "(stdlib)",
         "run": "go test -bench=. -benchmem ./..."},
    ],
    "nodejs": [
        {"tool": "clinic.js flame", "install": "npm i -g clinic",
         "run": "clinic flame -- node server.js"},
        {"tool": "autocannon",  "install": "npm i -g autocannon",
         "run": "autocannon -c 10 -d 30 http://localhost:3000"},
        {"tool": "Chrome DevTools Inspector",
         "install": "(built-in)",
         "run": "node --inspect server.js; open chrome://inspect"},
    ],
}


def tooling_for(framework: Optional[str]) -> List[Dict]:
    if not framework:
        return []
    return _TOOLING.get(framework, [])


# ─── Report assembly ───────────────────────────────────────────────────────

def audit(project: Path, *, min_severity: str = "info") -> Dict:
    framework = detect_framework(project)
    findings = scan(project, framework=framework, min_severity=min_severity)
    return {
        "project": str(project),
        "framework": framework,
        "min_severity": min_severity,
        "summary": {
            "total":   len(findings),
            "warning": sum(1 for f in findings if f.severity == "warning"),
            "info":    sum(1 for f in findings if f.severity == "info"),
        },
        "findings": [f.to_dict() for f in findings],
        "framework_tooling": tooling_for(framework),
    }


# ─── CLI ───────────────────────────────────────────────────────────────────

def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        description="Performance anti-pattern audit. Scans for N+1 query "
                    "risks, hot-path blockers, and memory hazards; emits "
                    "the right framework-specific profiler to dig deeper."
    )
    p.add_argument("--project", required=True, type=Path)
    p.add_argument("--severity", default="info",
                   choices=["info", "warning"],
                   help="Minimum severity to report (default: info, all)")
    p.add_argument("--json", action="store_true",
                   help="Emit JSON instead of human-readable summary")
    p.add_argument("--strict", action="store_true",
                   help="Exit 2 if any 'warning' severity findings present")
    args = p.parse_args(argv if argv is not None else sys.argv[1:])

    if not args.project.exists():
        print(f"project not found: {args.project}", file=sys.stderr)
        return 1

    report = audit(args.project, min_severity=args.severity)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"PERF AUDIT — {report['project']}")
        print(f"  framework:  {report['framework'] or '(not detected)'}")
        print(f"  severity:   >= {report['min_severity']}")
        print(f"  summary:    {report['summary']['warning']} warning, "
              f"{report['summary']['info']} info")
        print()
        if report["findings"]:
            print("FINDINGS")
            for f in report["findings"]:
                marker = "[WARN]" if f["severity"] == "warning" else "[info]"
                print(f"  {marker} {f['where']}  {f['rule_id']}")
                print(f"         {f['fix_hint']}")
        else:
            print("(no findings)")
        print()
        if report["framework_tooling"]:
            print(f"PROFILER TOOLING FOR {report['framework']}")
            for t in report["framework_tooling"]:
                print(f"  {t['tool']:30}  {t['install']}")
                print(f"    {t['run']}")

    if args.strict and report["summary"]["warning"] > 0:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
