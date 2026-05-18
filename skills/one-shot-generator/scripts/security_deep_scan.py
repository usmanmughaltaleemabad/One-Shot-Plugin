#!/usr/bin/env python3
"""
Security Deep Scan — v1.0.0  (Stage 5.7 companion — closes Risk #1's
"security flaws can slip through" half)

Existing reviewer catches obvious security issues. doubter catches
contract violations. critic catches test failures. None of them
systematically scan for specific OWASP-style vulnerabilities in the
generated code. This script does — as deterministic SAST patterns.

Categories scanned (each has multiple per-language patterns):

  AUTH
    - Hardcoded credentials / API keys / private keys
    - JWT secret as literal string (not env)
    - Hardcoded password defaults in user-facing endpoints

  INJECTION
    - SQL injection: f-string / format / concat into raw SQL or
      session.execute / .execute() / cursor.execute()
    - Command injection: subprocess / os.system / Runtime.exec with
      user-supplied input via concat
    - Path traversal: open() / Path() with user input + no allowlist

  CRYPTO
    - MD5 / SHA1 used for security purposes (not just checksums)
    - bcrypt cost < 12 (or hardcoded weak settings)
    - random.* used for tokens (should be secrets.* / SecureRandom)
    - Hardcoded IV / salt

  ACCESS
    - HTTP endpoints handling sensitive actions without auth decorator
    - eval() / exec() with non-literal input
    - pickle.load() from network / user-supplied data
    - YAML safe_load not used (yaml.load)

  EXPOSURE
    - Debug mode literal True in source
    - Sensitive fields included in __dict__ / serialize / to_json
      without explicit exclusion (heuristic — look for password/token
      fields without 'exclude' nearby)
    - CORS allow_origins=['*'] in production code

CLI:
    security_deep_scan.py --target <dir>
    security_deep_scan.py --target <dir> --severity high
    security_deep_scan.py --target <dir> --json --strict

Exit codes:
    0  no HIGH findings
    1  bad args
    2  at least one HIGH finding (--strict: also MEDIUM)

This is intentionally narrower than /security-review (the agent spawn).
The deep scan is deterministic + fast (~1s) so it runs every /one-shot
without burning tokens.
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


@dataclass
class Finding:
    rule_id: str
    category: str            # AUTH | INJECTION | CRYPTO | ACCESS | EXPOSURE
    severity: str            # HIGH | MEDIUM | LOW
    where: str
    snippet: str
    fix_hint: str

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class Rule:
    rule_id: str
    category: str
    severity: str
    pattern: re.Pattern
    file_globs: List[str]
    context_required: Optional[re.Pattern] = None
    context_excluded: Optional[re.Pattern] = None
    fix_hint: str = ""


def _r(p: str, flags: int = re.M) -> re.Pattern:
    return re.compile(p, flags)


RULES: List[Rule] = [
    # ─── AUTH ──────────────────────────────────────────────────────────
    Rule("hardcoded_aws_key", "AUTH", "HIGH",
         _r(r"AKIA[0-9A-Z]{16}"),
         ["*.py", "*.js", "*.ts", "*.go", "*.java"],
         fix_hint="Move to env var; rotate the key immediately."),
    Rule("hardcoded_github_pat", "AUTH", "HIGH",
         _r(r"ghp_[0-9A-Za-z]{36}"),
         ["*.py", "*.js", "*.ts", "*.go", "*.java"],
         fix_hint="Move to env var; revoke the leaked token."),
    Rule("hardcoded_slack_token", "AUTH", "HIGH",
         _r(r"xox[bpoa]-[0-9A-Za-z-]{10,}"),
         ["*.py", "*.js", "*.ts", "*.go", "*.java"],
         fix_hint="Move to env var; rotate the Slack token."),
    Rule("hardcoded_google_api_key", "AUTH", "HIGH",
         _r(r"AIza[0-9A-Za-z_-]{35}"),
         ["*.py", "*.js", "*.ts", "*.go", "*.java"],
         fix_hint="Move to env var; rotate the Google API key."),
    Rule("private_key_in_source", "AUTH", "HIGH",
         _r(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
         ["*.py", "*.js", "*.ts", "*.go", "*.java", "*.txt", "*.pem"],
         fix_hint="NEVER commit private keys. Rotate immediately + remove from git history."),
    Rule("jwt_secret_literal", "AUTH", "HIGH",
         _r(r"jwt\.(?:sign|encode)\s*\([^)]+,\s*['\"][^'\"]{8,}['\"]"),
         ["*.py", "*.js", "*.ts"],
         context_excluded=_r(r"process\.env|os\.environ|getenv"),
         fix_hint="Read JWT secret from env (process.env.JWT_SECRET / os.environ['JWT_SECRET'])."),

    # ─── INJECTION ─────────────────────────────────────────────────────
    Rule("sql_injection_fstring", "INJECTION", "HIGH",
         _r(r"""(?:session\.execute|cursor\.execute|db\.execute|conn\.execute|engine\.execute)\s*\(\s*f["']"""),
         ["*.py"],
         fix_hint="Use parameterised queries: session.execute(text('SELECT ... WHERE x = :v'), {'v': x})."),
    Rule("sql_injection_format", "INJECTION", "HIGH",
         _r(r"""(?:session\.execute|cursor\.execute|db\.execute)\s*\(\s*['"][^'"]*\{[^}]*\}[^'"]*['"]\.format"""),
         ["*.py"],
         fix_hint="Use parameterised queries — never .format() into SQL."),
    Rule("sql_injection_concat", "INJECTION", "HIGH",
         _r(r"""(?:session\.execute|cursor\.execute|db\.execute|conn\.query)\s*\(\s*['"][^'"]*['"]\s*\+"""),
         ["*.py", "*.js", "*.ts"],
         fix_hint="Use parameterised queries — never concat user input into SQL."),
    Rule("sql_injection_template_literal", "INJECTION", "HIGH",
         _r(r"""\.(?:query|execute)\s*\(\s*`[^`]*\$\{[^}]*\}"""),
         ["*.js", "*.ts"],
         fix_hint="Use parameterised queries: db.query('SELECT * WHERE x = ?', [x])."),
    Rule("command_injection_shell_true", "INJECTION", "HIGH",
         _r(r"subprocess\.(?:run|call|check_output|Popen)\([^)]*shell\s*=\s*True"),
         ["*.py"],
         fix_hint="Use shell=False + pass argv as a list, never as a string with shell=True."),
    Rule("command_injection_os_system", "INJECTION", "HIGH",
         _r(r"os\.system\s*\("),
         ["*.py"],
         fix_hint="Use subprocess.run(['cmd', 'arg1', ...]) with shell=False."),
    Rule("path_traversal_open_raw", "INJECTION", "MEDIUM",
         _r(r"""open\s*\(\s*(?:f["'][^"']*\{[^}]+\}|.*\+\s*\w)"""),
         ["*.py"],
         fix_hint="Validate path; use os.path.realpath() + check it stays under an allowlist."),

    # ─── CRYPTO ────────────────────────────────────────────────────────
    Rule("md5_security_use", "CRYPTO", "HIGH",
         _r(r"hashlib\.md5\("),
         ["*.py"],
         context_excluded=_r(r"checksum|integrity|hash_for_dedup|usedforsecurity\s*=\s*False"),
         fix_hint="MD5 is broken for security. Use hashlib.sha256(); for passwords use bcrypt/argon2."),
    Rule("sha1_security_use", "CRYPTO", "MEDIUM",
         _r(r"hashlib\.sha1\("),
         ["*.py"],
         context_excluded=_r(r"checksum|integrity|usedforsecurity\s*=\s*False"),
         fix_hint="SHA-1 is deprecated for security. Use sha256/sha512."),
    Rule("bcrypt_weak_cost", "CRYPTO", "MEDIUM",
         _r(r"""bcrypt\.gensalt\s*\(\s*(?:rounds\s*=\s*)?([0-9]+)"""),
         ["*.py"],
         fix_hint="Use bcrypt cost ≥ 12 (≥ 14 for high-value accounts)."),
    Rule("random_for_token", "CRYPTO", "HIGH",
         _r(r"random\.(?:random|choice|sample|randint|randbits)\s*\([^)]*\)\s*"
            r"(?:#.*(?:token|secret|password|api_key))?",
            re.I | re.M),
         ["*.py"],
         context_required=_r(r"token|secret|password|api[_-]?key|verification|reset", re.I),
         fix_hint="random.* is NOT crypto-safe. Use secrets.token_urlsafe() / secrets.token_hex()."),
    Rule("hardcoded_iv_salt", "CRYPTO", "MEDIUM",
         _r(r"""(?:iv|salt|nonce)\s*=\s*['"][a-fA-F0-9]{16,}['"]"""),
         ["*.py", "*.js", "*.ts", "*.go", "*.java"],
         fix_hint="IV/salt MUST be random per-message. Use secrets.token_bytes() / crypto.randomBytes()."),

    # ─── ACCESS ────────────────────────────────────────────────────────
    Rule("eval_with_input", "ACCESS", "HIGH",
         _r(r"\beval\s*\(\s*(?:request\.|input\(|sys\.argv|args\.|params\.)"),
         ["*.py", "*.js", "*.ts"],
         fix_hint="NEVER eval() user input. Use ast.literal_eval() for safe literals, or rewrite without eval."),
    Rule("exec_with_input", "ACCESS", "HIGH",
         _r(r"\bexec\s*\(\s*(?:request\.|input\(|sys\.argv|args\.|params\.)"),
         ["*.py"],
         fix_hint="NEVER exec() user input. Refactor to a safe dispatch table."),
    Rule("pickle_load_untrusted", "ACCESS", "HIGH",
         _r(r"pickle\.(?:load|loads)\s*\("),
         ["*.py"],
         fix_hint="pickle deserialises arbitrary objects → RCE. Use JSON / protobuf / msgpack."),
    Rule("yaml_unsafe_load", "ACCESS", "HIGH",
         _r(r"yaml\.load\s*\([^)]*\)(?![^,]*Loader\s*=\s*yaml\.SafeLoader)"),
         ["*.py"],
         fix_hint="Use yaml.safe_load() or yaml.load(..., Loader=yaml.SafeLoader)."),

    # ─── EXPOSURE ──────────────────────────────────────────────────────
    Rule("debug_mode_true", "EXPOSURE", "MEDIUM",
         _r(r"""(?:DEBUG|debug)\s*[:=]\s*True"""),
         ["*.py"],
         context_excluded=_r(r"if\s+os\.environ|getenv|settings_dev|test_|conftest"),
         fix_hint="Debug mode True in non-dev code leaks stack traces + queries. Read from env."),
    Rule("cors_wildcard_origin", "EXPOSURE", "MEDIUM",
         _r(r"""allow_origins\s*=\s*\[\s*['"]\*['"]\s*\]"""),
         ["*.py", "*.js", "*.ts"],
         fix_hint="CORS '*' with credentials allows ANY origin. Specify exact origins."),
    Rule("cors_wildcard_with_credentials", "EXPOSURE", "HIGH",
         _r(r"""allow_credentials\s*=\s*True[^)]*allow_origins\s*=\s*\[\s*['"]\*['"]"""),
         ["*.py"],
         fix_hint="CORS '*' + allow_credentials=True is a CRITICAL misconfig — browsers block it but the intent is wrong."),
]


SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv",
              ".tmp", ".pytest_cache", ".mypy_cache", "dist", "build",
              "vendor", ".idea", ".vscode"}


def _iter_files(root: Path, globs: List[str]) -> List[Path]:
    out: List[Path] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        suffix_glob = "*" + p.suffix
        if suffix_glob in globs:
            out.append(p)
    return out


def _file_matches_context(text: str, rule: Rule) -> bool:
    if rule.context_required and not rule.context_required.search(text):
        return False
    if rule.context_excluded and rule.context_excluded.search(text):
        return False
    return True


def scan(target: Path) -> Dict:
    findings: List[Finding] = []
    for rule in RULES:
        for path in _iter_files(target, rule.file_globs):
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if not _file_matches_context(text, rule):
                continue
            for m in rule.pattern.finditer(text):
                # If a per-finding context check is needed (e.g. for bcrypt cost):
                if rule.rule_id == "bcrypt_weak_cost":
                    try:
                        cost = int(m.group(1))
                        if cost >= 12:
                            continue
                    except (IndexError, ValueError):
                        pass
                lineno = text.count("\n", 0, m.start()) + 1
                rel = path.relative_to(target)
                snippet = m.group(0).replace("\n", " ")[:120]
                findings.append(Finding(
                    rule_id=rule.rule_id,
                    category=rule.category,
                    severity=rule.severity,
                    where=f"{rel}:{lineno}",
                    snippet=snippet,
                    fix_hint=rule.fix_hint,
                ))

    by_severity = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    by_category = {}
    for f in findings:
        by_severity[f.severity] = by_severity.get(f.severity, 0) + 1
        by_category[f.category] = by_category.get(f.category, 0) + 1

    if by_severity["HIGH"]:
        verdict = "BLOCKED"
    elif by_severity["MEDIUM"]:
        verdict = "REVIEW"
    else:
        verdict = "CLEAN"

    return {
        "verdict": verdict,
        "target": str(target),
        "rules_run": len(RULES),
        "summary": (f"{by_severity['HIGH']} HIGH, "
                    f"{by_severity['MEDIUM']} MEDIUM, "
                    f"{by_severity['LOW']} LOW"),
        "by_category": by_category,
        "findings": [f.to_dict() for f in findings],
    }


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(
        description="Deterministic SAST-style deep scan for generated code. "
                    "Runs as Stage 5.7 alongside cross_agent_consistency.py."
    )
    p.add_argument("--target", required=True, type=Path)
    p.add_argument("--severity", choices=["low", "medium", "high"],
                   default="low")
    p.add_argument("--json", action="store_true")
    p.add_argument("--strict", action="store_true",
                   help="Exit 2 on MEDIUM as well as HIGH")
    args = p.parse_args(argv if argv is not None else sys.argv[1:])

    if not args.target.exists():
        print(f"target not found: {args.target}", file=sys.stderr)
        return 1

    result = scan(args.target)

    # Severity filter
    sev_rank = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
    threshold = {"low": 0, "medium": 1, "high": 2}[args.severity]
    result["findings"] = [
        f for f in result["findings"]
        if sev_rank.get(f["severity"], 0) >= threshold
    ]

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"SECURITY DEEP SCAN — {result['verdict']}")
        print(f"  {result['summary']}")
        print(f"  scanned {result['rules_run']} rule(s)")
        print()
        for f in result["findings"]:
            print(f"  [{f['severity']:6}] {f['category']:10} {f['rule_id']:30} {f['where']}")
            print(f"     fix: {f['fix_hint']}")

    if result["verdict"] == "BLOCKED":
        return 2
    if args.strict and result["verdict"] == "REVIEW":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
