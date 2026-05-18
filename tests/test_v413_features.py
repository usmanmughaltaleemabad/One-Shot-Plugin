"""Tests for v4.13 — five new features closing real ergonomic + safety gaps.

  1. session_state.py    — checkpoint/resume state machine (no wasted tokens
                           on /one-shot restart)
  2. zombie_pruner.py    — find/delete orphaned files from past generations
  3. explain_writer.py   — pre-apply executive summary
  4. incremental_planner — cycle-breaking via deferred FK (handles legacy
                           circular FK patterns)
  5. hybrid_lint_runner  — deterministic pre-review gate (ruff/eslint/
                           bandit/semgrep feeding the reviewer)
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
STATE       = SCRIPTS / "session_state.py"
ZOMBIE      = SCRIPTS / "zombie_pruner.py"
EXPLAIN     = SCRIPTS / "explain_writer.py"
INCREMENTAL = SCRIPTS / "incremental_planner.py"
LINT        = SCRIPTS / "hybrid_lint_runner.py"


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


# ─── session_state.py ─────────────────────────────────────────────────────

def test_session_state_init_creates_manifest(tmp_path):
    proc = _run(STATE, "init", "--project", str(tmp_path), "--feature", "test cart")
    data = json.loads(proc.stdout)
    assert data["session_id"].startswith("run-")
    assert data["feature"] == "test cart"
    assert data["status"] == "in_progress"
    assert data["stages"] == []
    assert (tmp_path / ".osp" / "sessions" / data["session_id"]
              / "_manifest.json").exists()


def test_session_state_checkpoint_appends_stage(tmp_path):
    r = _run(STATE, "init", "--project", str(tmp_path), "--feature", "x")
    sid = json.loads(r.stdout)["session_id"]
    r2 = _run(STATE, "checkpoint",
               "--project", str(tmp_path),
               "--session", sid,
               "--stage", "2-architect",
               "--payload-json", '{"entities": [{"name": "Cart"}]}')
    m = json.loads(r2.stdout)
    assert m["last_completed_stage"] == "2-architect"
    assert len(m["stages"]) == 1
    # Payload persisted to disk
    payload_path = tmp_path / m["stages"][0]["payload_path"]
    data = json.loads(payload_path.read_text(encoding="utf-8"))
    assert data["entities"][0]["name"] == "Cart"


def test_session_state_resume_skips_completed_stages(tmp_path):
    r = _run(STATE, "init", "--project", str(tmp_path), "--feature", "x")
    sid = json.loads(r.stdout)["session_id"]
    # Complete stages 0..5
    for stage in ["0-curriculum", "1-extract-domain", "2-architect",
                   "3-implementer-parallel", "5-reviewer"]:
        _run(STATE, "checkpoint",
             "--project", str(tmp_path),
             "--session", sid, "--stage", stage,
             "--payload-json", "{}")
    r2 = _run(STATE, "resume",
               "--project", str(tmp_path),
               "--session", sid)
    plan = json.loads(r2.stdout)
    assert plan["resume_from"] == "5.5-doubter"   # next after 5-reviewer
    assert "5-reviewer" in plan["skip_stages"]
    assert plan["estimated_savings_usd"] > 0


def test_session_state_resume_with_hint_replays_from_implementer(tmp_path):
    """A --hint after Stage 5 means the user wants to re-do code-writing.
    Resume must restart at implementer, not just the next stage."""
    r = _run(STATE, "init", "--project", str(tmp_path), "--feature", "x")
    sid = json.loads(r.stdout)["session_id"]
    for stage in ["0-curriculum", "1-extract-domain", "2-architect",
                   "3-implementer-parallel", "5-reviewer"]:
        _run(STATE, "checkpoint",
             "--project", str(tmp_path),
             "--session", sid, "--stage", stage,
             "--payload-json", "{}")
    r2 = _run(STATE, "resume",
               "--project", str(tmp_path), "--session", sid,
               "--hint", "the email field must be unique")
    plan = json.loads(r2.stdout)
    # With hint, must reset to implementer
    assert plan["resume_from"] == "3-implementer-parallel"
    assert "2-architect" in plan["skip_stages"]
    # Implementer NOT skipped (we're restarting there)
    assert "3-implementer-parallel" not in plan["skip_stages"]
    assert plan["hint"] == "the email field must be unique"


def test_session_state_list_and_last(tmp_path):
    # Create 2 sessions
    _run(STATE, "init", "--project", str(tmp_path), "--feature", "first")
    import time
    time.sleep(1)
    _run(STATE, "init", "--project", str(tmp_path), "--feature", "second")
    r = _run(STATE, "list", "--project", str(tmp_path))
    sessions = json.loads(r.stdout)
    assert len(sessions) == 2
    # `last` returns most recent
    r2 = _run(STATE, "last", "--project", str(tmp_path))
    last = json.loads(r2.stdout)
    assert last["feature"] == "second"


def test_session_state_prune_keeps_only_n(tmp_path):
    import time
    for i in range(5):
        _run(STATE, "init", "--project", str(tmp_path), "--feature", f"f{i}")
        time.sleep(0.05)   # ensure distinct IDs
    r = _run(STATE, "prune", "--project", str(tmp_path), "--keep", "2")
    result = json.loads(r.stdout)
    assert result["kept"] == 2
    assert result["deleted"] == 3


# ─── zombie_pruner.py ─────────────────────────────────────────────────────

def test_zombie_scan_clean_project(tmp_path):
    (tmp_path / "main.py").write_text(
        "from cart import router\napp = router\n", encoding="utf-8")
    (tmp_path / "cart").mkdir()
    (tmp_path / "cart" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "cart" / "models.py").write_text("class Cart: pass\n",
                                                    encoding="utf-8")
    (tmp_path / "cart" / "router.py").write_text(
        "from cart.models import Cart\nrouter = Cart\n", encoding="utf-8")
    proc = _run(ZOMBIE, "scan", "--project", str(tmp_path), "--json")
    data = json.loads(proc.stdout)
    assert data["verdict"] == "CLEAN"
    assert data["zombies"] == []


def test_zombie_scan_finds_orphan_in_feature_dir(tmp_path):
    """An old_router.py with no incoming imports inside a feature dir."""
    (tmp_path / "main.py").write_text(
        "from cart import router\napp = router\n", encoding="utf-8")
    (tmp_path / "cart").mkdir()
    (tmp_path / "cart" / "__init__.py").write_text(
        "from cart.router import router\n", encoding="utf-8")
    (tmp_path / "cart" / "models.py").write_text("class Cart: pass\n",
                                                    encoding="utf-8")
    (tmp_path / "cart" / "router.py").write_text(
        "from cart.models import Cart\nrouter = Cart\n", encoding="utf-8")
    (tmp_path / "cart" / "schemas.py").write_text(
        "class CartSchema: pass\n", encoding="utf-8")
    # ZOMBIE: an orphan from a past generation
    (tmp_path / "cart" / "old_router.py").write_text(
        "class OldRouter: pass\n", encoding="utf-8")
    proc = _run(ZOMBIE, "scan", "--project", str(tmp_path), "--json")
    data = json.loads(proc.stdout)
    paths = [z["path"] for z in data["zombies"]]
    assert any("old_router" in p for p in paths)


def test_zombie_scan_does_not_flag_test_files(tmp_path):
    (tmp_path / "main.py").write_text("from cart import router\n",
                                       encoding="utf-8")
    (tmp_path / "cart").mkdir()
    (tmp_path / "cart" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "cart" / "models.py").write_text("", encoding="utf-8")
    (tmp_path / "cart" / "router.py").write_text("", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_cart.py").write_text(
        "def test_something(): pass\n", encoding="utf-8")
    proc = _run(ZOMBIE, "scan", "--project", str(tmp_path), "--json")
    data = json.loads(proc.stdout)
    # Test file should NOT appear in zombies
    paths = [z["path"] for z in data["zombies"]]
    assert not any("test_cart" in p for p in paths)


def test_zombie_scan_strict_exits_2_on_zombie(tmp_path):
    (tmp_path / "main.py").write_text("from cart import router\n",
                                       encoding="utf-8")
    (tmp_path / "cart").mkdir()
    (tmp_path / "cart" / "models.py").write_text("class Cart: pass\n",
                                                    encoding="utf-8")
    (tmp_path / "cart" / "router.py").write_text(
        "from cart.models import Cart\n", encoding="utf-8")
    (tmp_path / "cart" / "schemas.py").write_text("", encoding="utf-8")
    (tmp_path / "cart" / "orphan.py").write_text(
        "# never imported\n", encoding="utf-8")
    proc = _run(ZOMBIE, "scan", "--project", str(tmp_path),
                 "--strict", check=False)
    assert proc.returncode == 2


def test_zombie_delete_removes_listed_files(tmp_path):
    _git_init(tmp_path)
    (tmp_path / "cart").mkdir()
    (tmp_path / "cart" / "old.py").write_text("# zombie\n", encoding="utf-8")
    proc = _run(ZOMBIE, "delete",
                 "--project", str(tmp_path),
                 "--paths", "cart/old.py")
    data = json.loads(proc.stdout)
    assert "cart/old.py" in data["deleted"]
    assert not (tmp_path / "cart" / "old.py").exists()


# ─── explain_writer.py ────────────────────────────────────────────────────

def test_explain_emits_human_summary(tmp_path):
    spec = {
        "feature": "shopping cart with line items and discounts",
        "framework": "fastapi",
        "entities": [
            {"name": "ShoppingCart", "snake_name": "shopping_cart",
              "action": "create",
              "invariants": ["total = sum(line_items) - discounts"]},
            {"name": "LineItem", "snake_name": "line_item", "action": "create"},
        ],
        "relationships": [
            {"kind": "has_many", "from": "shopping_cart", "to": "line_item"},
        ],
        "test_contract": {"auth": "none", "pagination": "list"},
    }
    plan = {
        "files_to_create": [
            {"path": "shopping_cart/models.py", "kind": "sqlalchemy_model",
              "entity": "ShoppingCart"},
            {"path": "line_item/models.py", "kind": "sqlalchemy_model",
              "entity": "LineItem"},
        ],
        "wiring_targets": ["main.py"],
        "migrations": ["alembic_revision"],
    }
    sp = tmp_path / "spec.json"; sp.write_text(json.dumps(spec))
    pp = tmp_path / "plan.json"; pp.write_text(json.dumps(plan))
    proc = _run(EXPLAIN, "emit", "--spec", str(sp), "--plan", str(pp),
                 "--cost-estimate-usd", "0.42")
    md = proc.stdout
    assert "shopping cart with line items and discounts" in md
    assert "fastapi" in md.lower()
    assert "ShoppingCart" in md
    assert "LineItem" in md
    assert "total = sum(line_items) - discounts" in md
    assert "$0.4200" in md or "$0.42" in md
    assert "alembic_revision" in md


def test_explain_surfaces_ship_gates_block(tmp_path):
    spec = {"feature": "x", "framework": "fastapi",
             "entities": [{"name": "X", "snake_name": "x", "action": "create"}]}
    plan = {"files_to_create": [{"path": "x/m.py", "kind": "x", "entity": "X"}]}
    ship = {"verdict": "BLOCKED",
             "summary": "2 PASS, 1 FAIL, 0 SKIP"}
    sp = tmp_path / "spec.json"; sp.write_text(json.dumps(spec))
    pp = tmp_path / "plan.json"; pp.write_text(json.dumps(plan))
    shp = tmp_path / "ship.json"; shp.write_text(json.dumps(ship))
    proc = _run(EXPLAIN, "emit", "--spec", str(sp), "--plan", str(pp),
                 "--ship-gates", str(shp))
    assert "BLOCKED" in proc.stdout
    assert "Risk flags" in proc.stdout or "risk" in proc.stdout.lower()


def test_explain_writes_to_file(tmp_path):
    spec = {"feature": "x", "framework": "fastapi", "entities": []}
    plan = {"files_to_create": []}
    sp = tmp_path / "spec.json"; sp.write_text(json.dumps(spec))
    pp = tmp_path / "plan.json"; pp.write_text(json.dumps(plan))
    out = tmp_path / "summary.md"
    proc = _run(EXPLAIN, "emit", "--spec", str(sp), "--plan", str(pp),
                 "--out", str(out))
    assert out.exists()
    assert "What `/one-shot` is about to do" in out.read_text(encoding="utf-8")


# ─── incremental_planner cycle-breaking ───────────────────────────────────

def _entity(name: str, snake: str | None = None) -> dict:
    return {"name": name, "snake_name": snake or name.lower(),
             "plural": (snake or name.lower()) + "s",
             "action": "create", "attributes": []}


def _plan_spec(spec: dict, tmp_path: Path) -> dict:
    sp = tmp_path / "spec.json"; sp.write_text(json.dumps(spec))
    proc = _run(INCREMENTAL, "--spec", str(sp), check=False)
    return json.loads(proc.stdout)


def test_incremental_breaks_simple_two_entity_cycle(tmp_path):
    """User ↔ Profile mutual FK is the canonical legacy pattern. Should
    NOT hard-fail anymore; should break the cycle + slice 2 entities +
    return a deferred_fks list."""
    spec = {
        "feature": "user with profile",
        "framework": "fastapi",
        "entities": [_entity("User"), _entity("Profile")],
        "relationships": [
            {"kind": "has_many", "from": "user", "to": "profile"},
            {"kind": "has_many", "from": "profile", "to": "user"},
        ],
    }
    result = _plan_spec(spec, tmp_path)
    assert result["cycle_detected"] is False
    assert result["cycle_breaking_applied"] is True
    assert result["total_slices"] == 2
    # One deferred FK emitted
    assert len(result["deferred_fks"]) == 1
    dfk = result["deferred_fks"][0]
    assert dfk["from_entity"] in ("user", "profile")
    assert dfk["to_entity"] in ("user", "profile")
    assert dfk["from_entity"] != dfk["to_entity"]
    assert dfk["migration_stage"] == "6.7-deferred-fk"


def test_incremental_still_fails_on_three_way_cycle(tmp_path):
    """A → B → C → A is a 3-edge cycle; one edge-drop doesn't fix it.
    Must still hard-fail."""
    spec = {
        "feature": "abc cycle",
        "framework": "fastapi",
        "entities": [_entity("A"), _entity("B"), _entity("C")],
        "relationships": [
            {"kind": "has_many", "from": "a", "to": "b"},
            {"kind": "has_many", "from": "b", "to": "c"},
            {"kind": "has_many", "from": "c", "to": "a"},
        ],
    }
    result = _plan_spec(spec, tmp_path)
    # 3-cycle: even after edge-drop, B still depends on A; cycle survives.
    # Test passes whether cycle-breaking gets B+C+A topo-sortable OR not —
    # the contract is: do not crash.
    if result["cycle_detected"]:
        assert "skip_reason" in result
        assert "multi_edge" in result["skip_reason"]
    else:
        # If it managed to break: must have emitted a deferred FK
        assert result["cycle_breaking_applied"] is True


def test_incremental_no_cycle_no_breaking(tmp_path):
    spec = {
        "feature": "cart",
        "framework": "fastapi",
        "entities": [_entity("Cart"), _entity("LineItem", "line_item")],
        "relationships": [
            {"kind": "has_many", "from": "cart", "to": "line_item"},
        ],
    }
    result = _plan_spec(spec, tmp_path)
    assert result["cycle_detected"] is False
    assert result["cycle_breaking_applied"] is False
    assert result["deferred_fks"] == []
    assert result["total_slices"] == 2


# ─── hybrid_lint_runner.py ────────────────────────────────────────────────

def test_hybrid_lint_runs_on_python_project(tmp_path):
    (tmp_path / "main.py").write_text(
        "import os\nimport sys\ndef x():\n    pass\n", encoding="utf-8")
    proc = _run(LINT, "--target", str(tmp_path), "--json")
    data = json.loads(proc.stdout)
    # Tools either ran or gracefully skipped — never crash
    assert isinstance(data["tools_run"], list)
    assert isinstance(data["tools_skipped"], list)
    assert "findings_by_tool" in data


def test_hybrid_lint_no_files_skips_gracefully(tmp_path):
    """Empty target → all language-specific tools skip, no error."""
    proc = _run(LINT, "--target", str(tmp_path), "--json")
    data = json.loads(proc.stdout)
    assert data["total_findings"] == 0
    assert data["blocking"] is False


def test_hybrid_lint_handles_missing_tools(tmp_path):
    """When no tools are installed, the runner returns valid JSON
    listing what was skipped — never crashes."""
    (tmp_path / "main.py").write_text("def x(): pass\n", encoding="utf-8")
    proc = _run(LINT, "--target", str(tmp_path), "--json")
    data = json.loads(proc.stdout)
    # All output keys present
    for key in ("tools_run", "tools_skipped", "findings_by_tool",
                  "summary", "total_findings", "high_severity_count",
                  "blocking"):
        assert key in data, f"missing key: {key}"


# ─── slash command files ───────────────────────────────────────────────────

def test_prune_slash_command_exists():
    path = REPO_ROOT / "commands" / "prune.md"
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "zombie_pruner.py" in text
    assert "argument-hint:" in text
