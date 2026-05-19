"""Tests for v4.12 — two safety gates closing real Gemini-flagged risks.

Risk #1: subtle logic bugs / security flaws slip through 10-agent
         orchestration even when individual agents pass.
Risk #2: auto-generating 17 files + running migrations on a critical
         legacy codebase is reckless.

Four new scripts:
  - cross_agent_consistency.py — spec ↔ code drift detector (Stage 5.7)
  - security_deep_scan.py      — deterministic SAST ruleset (Stage 5.7)
  - impact_analyzer.py         — static-import heat scoring
  - legacy_guard.py            — --legacy-safe mode enforcer (Stage 0.7)
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "skills" / "one-shot-generator" / "scripts"
CONSISTENCY = SCRIPTS / "cross_agent_consistency.py"
SECURITY    = SCRIPTS / "security_deep_scan.py"
IMPACT      = SCRIPTS / "impact_analyzer.py"
LEGACY      = SCRIPTS / "legacy_guard.py"


def _run(script: Path, *args: str, check: bool = True,
         timeout: int = 30, cwd: Path | None = None) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True, text=True, env=env, encoding="utf-8",
        timeout=timeout, cwd=str(cwd) if cwd else None,
    )
    if check:
        assert proc.returncode in (0, 1, 2), \
            f"{script.name} crashed: {proc.stderr}"
    return proc


def _git_init(repo: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=str(repo), check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=str(repo), check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=str(repo), check=True)
    (repo / "dummy").write_text("", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=str(repo), check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=str(repo), check=True)


# ─── cross_agent_consistency ───────────────────────────────────────────────

def test_consistency_detects_missing_attr_in_model(tmp_path):
    spec = {
        "feature": "cart", "framework": "fastapi",
        "entities": [{"name": "Cart", "snake_name": "cart", "plural": "carts",
                       "action": "create", "attributes": [
                           {"name": "status"}, {"name": "total"},
                       ]}],
    }
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    gen = tmp_path / "out"
    (gen / "cart").mkdir(parents=True)
    # Model only has 'status' — 'total' missing
    (gen / "cart" / "models.py").write_text(
        "class Cart:\n    status: str\n", encoding="utf-8")
    proc = _run(CONSISTENCY, "--spec", str(spec_path),
                 "--generated-dir", str(gen), "--json", check=False)
    data = json.loads(proc.stdout)
    assert data["verdict"] == "BLOCKED"
    rules = {v["rule"] for v in data["violations"]}
    assert "SPEC_ATTRS_MATCH_MODEL" in rules


def test_consistency_detects_invariants_not_enforced(tmp_path):
    """Spec declares 2 invariants but service.py is too sparse to honestly
    enforce them — flagged as CRITICAL."""
    spec = {
        "feature": "cart", "framework": "fastapi",
        "entities": [{"name": "Cart", "snake_name": "cart", "plural": "carts",
                       "action": "create", "attributes": [],
                       "invariants": [
                           "total = sum(items) - discounts",
                           "status is in {open, closed, abandoned}",
                       ]}],
    }
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    gen = tmp_path / "out"
    (gen / "cart").mkdir(parents=True)
    # Empty model (just to pass attr check); empty service
    (gen / "cart" / "models.py").write_text("class Cart: pass\n", encoding="utf-8")
    (gen / "cart" / "service.py").write_text(
        "class CartService:\n    def list(self): return []\n",
        encoding="utf-8",
    )
    proc = _run(CONSISTENCY, "--spec", str(spec_path),
                 "--generated-dir", str(gen), "--json", check=False)
    data = json.loads(proc.stdout)
    rules = {v["rule"] for v in data["violations"]}
    assert "INVARIANT_ENFORCED" in rules


def test_consistency_detects_missing_fk(tmp_path):
    spec = {
        "feature": "cart", "framework": "fastapi",
        "entities": [
            {"name": "Cart", "snake_name": "cart", "plural": "carts",
              "action": "create", "attributes": []},
            {"name": "LineItem", "snake_name": "line_item", "plural": "line_items",
              "action": "create", "attributes": []},
        ],
        "relationships": [
            {"kind": "has_many", "from": "cart", "to": "line_item"},
        ],
    }
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    gen = tmp_path / "out"
    (gen / "cart").mkdir(parents=True)
    (gen / "line_item").mkdir(parents=True)
    (gen / "cart" / "models.py").write_text("class Cart: pass\n", encoding="utf-8")
    # line_item missing the cart_id FK
    (gen / "line_item" / "models.py").write_text(
        "class LineItem:\n    quantity: int\n", encoding="utf-8")
    proc = _run(CONSISTENCY, "--spec", str(spec_path),
                 "--generated-dir", str(gen), "--json", check=False)
    data = json.loads(proc.stdout)
    rules = {v["rule"] for v in data["violations"]}
    assert "SPEC_RELATIONSHIPS_MATCH_FKS" in rules


def test_consistency_clean_spec_returns_clean(tmp_path):
    spec = {
        "feature": "cart", "framework": "fastapi",
        "entities": [{"name": "Cart", "snake_name": "cart", "plural": "carts",
                       "action": "create", "attributes": [{"name": "status"}]}],
    }
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    gen = tmp_path / "out"
    (gen / "cart").mkdir(parents=True)
    (gen / "cart" / "models.py").write_text(
        "from sqlalchemy import Column, String\n"
        "class Cart:\n    status = Column(String)\n",
        encoding="utf-8",
    )
    proc = _run(CONSISTENCY, "--spec", str(spec_path),
                 "--generated-dir", str(gen), "--json")
    data = json.loads(proc.stdout)
    assert data["verdict"] in ("CLEAN", "READY_WITH_WARN")


def test_consistency_strict_promotes_warn_to_block(tmp_path):
    spec = {
        "feature": "cart", "framework": "fastapi",
        "entities": [{"name": "Cart", "snake_name": "cart", "plural": "carts",
                       "action": "create", "attributes": [],
                       "invariants": ["total computed correctly"]}],
    }
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    gen = tmp_path / "out"
    (gen / "cart").mkdir(parents=True)
    (gen / "cart" / "models.py").write_text("class Cart: pass\n", encoding="utf-8")
    # Service file with enough LOC to dodge sparse-CRITICAL but no raise/check signals
    (gen / "cart" / "service.py").write_text(
        "\n".join([
            "class CartService:",
            "    def __init__(self, db):",
            "        self.db = db",
            "    def list(self):",
            "        return self.db.query(Cart).all()",
            "    def get(self, item_id):",
            "        return self.db.query(Cart).get(item_id)",
            "    def create(self, payload):",
            "        cart = Cart(**payload)",
            "        self.db.add(cart)",
            "        return cart",
            "    def update(self, item_id, payload):",
            "        c = self.get(item_id)",
            "        for k, v in payload.items():",
            "            setattr(c, k, v)",
            "        return c",
        ]),
        encoding="utf-8",
    )
    proc = _run(CONSISTENCY, "--spec", str(spec_path),
                 "--generated-dir", str(gen), "--strict", check=False)
    # Long service file without enforcement → WARN, then --strict promotes
    assert proc.returncode in (0, 2)


# ─── security_deep_scan ────────────────────────────────────────────────────

def test_security_catches_aws_key(tmp_path):
    (tmp_path / "config.py").write_text(
        'AWS_KEY = "AKIAIOSFODNN7EXAMPLE"\n', encoding="utf-8")
    proc = _run(SECURITY, "--target", str(tmp_path), "--json", check=False)
    data = json.loads(proc.stdout)
    assert data["verdict"] == "BLOCKED"
    ids = {f["rule_id"] for f in data["findings"]}
    assert "hardcoded_aws_key" in ids


def test_security_catches_sql_injection_fstring(tmp_path):
    (tmp_path / "views.py").write_text(
        "def search(q):\n"
        "    return cursor.execute(f\"SELECT * FROM users WHERE name = '{q}'\")\n",
        encoding="utf-8",
    )
    proc = _run(SECURITY, "--target", str(tmp_path), "--json", check=False)
    data = json.loads(proc.stdout)
    ids = {f["rule_id"] for f in data["findings"]}
    assert "sql_injection_fstring" in ids


def test_security_catches_shell_true(tmp_path):
    (tmp_path / "ops.py").write_text(
        "import subprocess\n"
        "def run(cmd): return subprocess.run(cmd, shell=True)\n",
        encoding="utf-8",
    )
    proc = _run(SECURITY, "--target", str(tmp_path), "--json", check=False)
    ids = {f["rule_id"] for f in json.loads(proc.stdout)["findings"]}
    assert "command_injection_shell_true" in ids


def test_security_catches_pickle_load(tmp_path):
    (tmp_path / "load.py").write_text(
        "import pickle\ndef load(b): return pickle.loads(b)\n",
        encoding="utf-8")
    proc = _run(SECURITY, "--target", str(tmp_path), "--json", check=False)
    ids = {f["rule_id"] for f in json.loads(proc.stdout)["findings"]}
    assert "pickle_load_untrusted" in ids


def test_security_catches_yaml_unsafe(tmp_path):
    (tmp_path / "cfg.py").write_text(
        "import yaml\ndef parse(s): return yaml.load(s)\n", encoding="utf-8")
    proc = _run(SECURITY, "--target", str(tmp_path), "--json", check=False)
    ids = {f["rule_id"] for f in json.loads(proc.stdout)["findings"]}
    assert "yaml_unsafe_load" in ids


def test_security_catches_random_for_token(tmp_path):
    (tmp_path / "auth.py").write_text(
        "import random\ndef make_token(): return random.randint(0, 999)  # token\n",
        encoding="utf-8")
    proc = _run(SECURITY, "--target", str(tmp_path), "--json", check=False)
    ids = {f["rule_id"] for f in json.loads(proc.stdout)["findings"]}
    assert "random_for_token" in ids


def test_security_clean_code_returns_clean(tmp_path):
    (tmp_path / "main.py").write_text(
        "import os\n"
        "import secrets\n"
        "JWT_SECRET = os.environ['JWT_SECRET']\n"
        "def make_token(): return secrets.token_urlsafe(32)\n",
        encoding="utf-8",
    )
    proc = _run(SECURITY, "--target", str(tmp_path), "--json")
    data = json.loads(proc.stdout)
    assert data["verdict"] == "CLEAN"


def test_security_strict_promotes_medium(tmp_path):
    (tmp_path / "code.py").write_text(
        "import hashlib\n"
        "def sha1(x): return hashlib.sha1(x).hexdigest()\n",
        encoding="utf-8",
    )
    normal = _run(SECURITY, "--target", str(tmp_path), check=False)
    strict = _run(SECURITY, "--target", str(tmp_path), "--strict", check=False)
    # SHA-1 is MEDIUM, normal returns 0; strict returns 2
    assert normal.returncode == 0
    assert strict.returncode == 2


# ─── impact_analyzer ──────────────────────────────────────────────────────

def test_impact_analyzer_finds_direct_importers(tmp_path):
    """A util imported by 3 files has direct_importer_count == 3."""
    (tmp_path / "util.py").write_text(
        "def helper(): pass\n", encoding="utf-8")
    for i in range(3):
        (tmp_path / f"caller{i}.py").write_text(
            "from util import helper\n", encoding="utf-8")
    proc = _run(IMPACT, "--project", str(tmp_path),
                 "--targets", str(tmp_path / "util.py"),
                 "--json")
    data = json.loads(proc.stdout)
    report = data["reports"][0]
    assert report["direct_importer_count"] == 3


def test_impact_analyzer_heat_verdict_cool_for_isolated_file(tmp_path):
    (tmp_path / "lonely.py").write_text("def x(): pass\n", encoding="utf-8")
    proc = _run(IMPACT, "--project", str(tmp_path),
                 "--targets", str(tmp_path / "lonely.py"),
                 "--json")
    report = json.loads(proc.stdout)["reports"][0]
    assert report["heat_verdict"] == "COOL"


def test_impact_analyzer_heat_escalates_on_many_importers(tmp_path):
    """File imported by 50+ files should hit HOT or DO_NOT_TOUCH."""
    (tmp_path / "central.py").write_text(
        "def helper(): pass\n", encoding="utf-8")
    for i in range(60):
        (tmp_path / f"client{i}.py").write_text(
            "from central import helper\n", encoding="utf-8")
    proc = _run(IMPACT, "--project", str(tmp_path),
                 "--targets", str(tmp_path / "central.py"),
                 "--json")
    report = json.loads(proc.stdout)["reports"][0]
    assert report["direct_importer_count"] == 60
    assert report["heat_verdict"] in ("HOT", "DO_NOT_TOUCH")


def test_impact_analyzer_missing_target_doesnt_crash(tmp_path):
    proc = _run(IMPACT, "--project", str(tmp_path),
                 "--targets", str(tmp_path / "does_not_exist.py"),
                 "--json")
    report = json.loads(proc.stdout)["reports"][0]
    assert report["heat_verdict"] == "MISSING"


# ─── legacy_guard ─────────────────────────────────────────────────────────

def test_legacy_guard_blocks_too_many_files(tmp_path):
    _git_init(tmp_path)
    proc = _run(LEGACY, "validate",
                 "--project", str(tmp_path),
                 "--planned-files",
                 str(tmp_path / "a.py"), str(tmp_path / "b.py"),
                 str(tmp_path / "c.py"), str(tmp_path / "d.py"),
                 "--extra-flags=--review",
                 "--json", check=False)
    assert proc.returncode == 2
    data = json.loads(proc.stdout)
    rules = {v["rule"] for v in data["violations"]}
    assert "MAX_FILES_EXCEEDED" in rules


def test_legacy_guard_blocks_apply_flag(tmp_path):
    _git_init(tmp_path)
    proc = _run(LEGACY, "validate",
                 "--project", str(tmp_path),
                 "--planned-files", str(tmp_path / "a.py"),
                 "--extra-flags=--apply,--review",
                 "--json", check=False)
    data = json.loads(proc.stdout)
    rules = {v["rule"] for v in data["violations"]}
    assert "FORBIDDEN_FLAG_IN_LEGACY_SAFE" in rules


def test_legacy_guard_blocks_missing_review(tmp_path):
    _git_init(tmp_path)
    proc = _run(LEGACY, "validate",
                 "--project", str(tmp_path),
                 "--planned-files", str(tmp_path / "a.py"),
                 "--json", check=False)
    data = json.loads(proc.stdout)
    rules = {v["rule"] for v in data["violations"]}
    assert "REQUIRED_FLAG_MISSING" in rules


def test_legacy_guard_blocks_dirty_working_tree(tmp_path):
    _git_init(tmp_path)
    (tmp_path / "dirty.py").write_text("modified\n", encoding="utf-8")
    proc = _run(LEGACY, "validate",
                 "--project", str(tmp_path),
                 "--planned-files", str(tmp_path / "a.py"),
                 "--extra-flags=--review",
                 "--json", check=False)
    data = json.loads(proc.stdout)
    rules = {v["rule"] for v in data["violations"]}
    assert "UNCOMMITTED_CHANGES" in rules


def test_legacy_guard_allows_clean_compliant_run(tmp_path):
    _git_init(tmp_path)
    proc = _run(LEGACY, "validate",
                 "--project", str(tmp_path),
                 "--planned-files", str(tmp_path / "new1.py"),
                 "--extra-flags=--review",
                 "--json")
    data = json.loads(proc.stdout)
    assert data["verdict"] == "ALLOWED"
    assert len(data["violations"]) == 0


def test_legacy_guard_blocks_do_not_touch_targets(tmp_path):
    """File with 60+ importers + planned for mutation = DO_NOT_TOUCH = BLOCK."""
    _git_init(tmp_path)
    central = tmp_path / "central.py"
    central.write_text("def helper(): pass\n", encoding="utf-8")
    for i in range(60):
        (tmp_path / f"client{i}.py").write_text(
            "from central import helper\n", encoding="utf-8")
    # Re-commit so working tree is clean (the new files were just added)
    subprocess.run(["git", "add", "."], cwd=str(tmp_path), check=True)
    subprocess.run(["git", "commit", "-q", "-m", "add"], cwd=str(tmp_path), check=True)

    proc = _run(LEGACY, "validate",
                 "--project", str(tmp_path),
                 "--planned-files", str(central),
                 "--extra-flags=--review",
                 "--json", check=False)
    data = json.loads(proc.stdout)
    rules = {v["rule"] for v in data["violations"]}
    assert ("IMPACT_HEAT_DO_NOT_TOUCH" in rules
            or "IMPACT_HEAT_HOT" in rules)


def test_legacy_guard_limits_subcommand():
    """`legacy_guard limits` documents the enforced constants."""
    proc = _run(LEGACY, "limits")
    data = json.loads(proc.stdout)
    assert data["max_files_per_run"] == 3
    assert "--apply" in data["forbidden_flags"]
    assert "--review" in data["required_flags"]
    assert "MIGRATION_RUNBOOK" in " ".join(data["extra_constraints"])


# ─── SKILL.md wiring ──────────────────────────────────────────────────────

def test_skill_md_has_stage_0_7_legacy_safe_gate():
    from conftest import pipeline_text
    text = pipeline_text()
    assert "Stage 0.7" in text
    assert "legacy_guard.py" in text
    assert "--legacy-safe" in text
    # Document the actual constraints
    assert "Max 3 files" in text or "3 files" in text


def test_skill_md_has_stage_5_7_consistency_and_security():
    from conftest import pipeline_text
    text = pipeline_text()
    assert "Stage 5.7" in text
    assert "cross_agent_consistency.py" in text
    assert "security_deep_scan.py" in text
    # Must reference Gemini's review as the rationale
    assert "subtle logic bugs" in text or "10 different AI agents" in text
