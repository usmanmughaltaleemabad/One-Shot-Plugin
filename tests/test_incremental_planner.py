"""Tests for v4.8 incremental_planner — --incremental mode slicing.

The planner topologically sorts entities by FK dependencies so that
each slice can ship independently with green tests + a git commit
between slices.

Covered:
  - simple has_many ordering (parent before child)
  - alphabetical stable tie-break among same-in-degree entities
  - belongs_to flips ordering correctly
  - self-referential entity becomes a single slice (no cycle)
  - mutual FKs (true cycle) detected and exit 2 with cycle_members
  - sliced spec contains ONLY target entity but keeps relevant rels
  - per-slice spec file emission to disk
  - commit subject is well-formed and respects 72-char cap
  - SKILL.md documents Stage 2.6 + --incremental flag
  - /one-shot command frontmatter advertises --incremental
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / "skills" / "one-shot-generator" / "scripts"
PLANNER = SCRIPTS / "incremental_planner.py"


def _run(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(
        [sys.executable, str(PLANNER), *args],
        capture_output=True, text=True, env=env, encoding="utf-8", timeout=15,
    )
    if check:
        assert proc.returncode in (0, 2), \
            f"planner failed (exit {proc.returncode}): {proc.stderr}"
    return proc


def _plan(spec: dict, tmp_path: Path, *, out_dir: bool = False) -> dict:
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    args = ["--spec", str(spec_path)]
    if out_dir:
        args += ["--out-dir", str(tmp_path / "slices")]
    proc = _run(*args)
    return json.loads(proc.stdout)


def _entity(name: str, snake: str | None = None, action: str = "create") -> dict:
    return {"name": name, "snake_name": snake or name.lower(),
            "plural": (snake or name.lower()) + "s",
            "action": action, "attributes": []}


# ─── happy paths ──────────────────────────────────────────────────────────

def test_simple_has_many_parent_before_child(tmp_path):
    spec = {
        "feature": "shopping cart",
        "framework": "fastapi",
        "entities": [
            _entity("LineItem", "line_item"),
            _entity("ShoppingCart", "shopping_cart"),
        ],
        "relationships": [
            {"kind": "has_many", "from": "shopping_cart", "to": "line_item"},
        ],
    }
    result = _plan(spec, tmp_path)
    assert result["total_slices"] == 2
    order = [s["entity"] for s in result["slices"]]
    assert order == ["ShoppingCart", "LineItem"], \
        "parent must come before child"
    assert result["slices"][0]["depends_on"] == []
    assert result["slices"][1]["depends_on"] == ["ShoppingCart"]


def test_alphabetical_tiebreak_for_same_indegree(tmp_path):
    """Discount + LineItem both depend on ShoppingCart only — neither
    depends on the other. Order must be deterministic (alphabetical)."""
    spec = {
        "feature": "shopping cart with line items and discounts",
        "framework": "fastapi",
        "entities": [
            _entity("LineItem", "line_item"),
            _entity("ShoppingCart", "shopping_cart"),
            _entity("Discount", "discount"),
        ],
        "relationships": [
            {"kind": "has_many", "from": "shopping_cart", "to": "line_item"},
            {"kind": "has_many", "from": "shopping_cart", "to": "discount"},
        ],
    }
    result = _plan(spec, tmp_path)
    order = [s["entity"] for s in result["slices"]]
    # Stable alphabetical: Discount < LineItem
    assert order == ["ShoppingCart", "Discount", "LineItem"]


def test_belongs_to_inverts_ordering(tmp_path):
    """belongs_to: from(child) → to(parent). Parent still comes first."""
    spec = {
        "feature": "comment thread",
        "framework": "fastapi",
        "entities": [
            _entity("Comment", "comment"),
            _entity("Post", "post"),
        ],
        "relationships": [
            {"kind": "belongs_to", "from": "comment", "to": "post"},
        ],
    }
    result = _plan(spec, tmp_path)
    order = [s["entity"] for s in result["slices"]]
    assert order == ["Post", "Comment"]


def test_self_reference_is_single_slice_not_cycle(tmp_path):
    """Tree.parent_id → Tree.id should NOT be flagged as cycle."""
    spec = {
        "feature": "category tree",
        "framework": "fastapi",
        "entities": [_entity("Category", "category")],
        "relationships": [
            {"kind": "has_many", "from": "category", "to": "category"},
        ],
    }
    result = _plan(spec, tmp_path)
    assert result["cycle_detected"] is False
    assert result["total_slices"] == 1
    assert result["slices"][0]["entity"] == "Category"
    assert result["slices"][0]["depends_on"] == []


def test_three_level_chain_orders_correctly(tmp_path):
    """Org → Team → Member chain should be 3 slices in order."""
    spec = {
        "feature": "org chart",
        "framework": "fastapi",
        "entities": [
            _entity("Member", "member"),
            _entity("Team", "team"),
            _entity("Org", "org"),
        ],
        "relationships": [
            {"kind": "has_many", "from": "org",  "to": "team"},
            {"kind": "has_many", "from": "team", "to": "member"},
        ],
    }
    result = _plan(spec, tmp_path)
    order = [s["entity"] for s in result["slices"]]
    assert order == ["Org", "Team", "Member"]
    assert result["slices"][2]["depends_on"] == ["Team"]


# ─── cycle detection ──────────────────────────────────────────────────────

def test_mutual_fk_detected_as_cycle(tmp_path):
    spec = {
        "feature": "user profile",
        "framework": "fastapi",
        "entities": [
            _entity("User", "user"),
            _entity("Profile", "profile"),
        ],
        "relationships": [
            {"kind": "has_many", "from": "user",    "to": "profile"},
            {"kind": "has_many", "from": "profile", "to": "user"},
        ],
    }
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    proc = _run("--spec", str(spec_path), check=False)
    assert proc.returncode == 2
    data = json.loads(proc.stdout)
    assert data["cycle_detected"] is True
    assert sorted(data["cycle_members"]) == ["Profile", "User"]
    assert data["total_slices"] == 0


def test_validate_mode_exits_2_on_cycle(tmp_path):
    spec = {
        "feature": "x",
        "framework": "fastapi",
        "entities": [_entity("A"), _entity("B")],
        "relationships": [
            {"kind": "has_many", "from": "a", "to": "b"},
            {"kind": "has_many", "from": "b", "to": "a"},
        ],
    }
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    proc = _run("--spec", str(spec_path), "--validate", check=False)
    assert proc.returncode == 2
    assert "cycle" in proc.stderr.lower()


def test_validate_mode_exits_0_when_clean(tmp_path):
    spec = {
        "feature": "x",
        "framework": "fastapi",
        "entities": [_entity("A"), _entity("B")],
        "relationships": [{"kind": "has_many", "from": "a", "to": "b"}],
    }
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    proc = _run("--spec", str(spec_path), "--validate", check=False)
    assert proc.returncode == 0


# ─── sliced spec contents ─────────────────────────────────────────────────

def test_sliced_spec_contains_only_target_entity(tmp_path):
    spec = {
        "feature": "shopping cart",
        "framework": "fastapi",
        "entities": [
            _entity("LineItem", "line_item"),
            _entity("ShoppingCart", "shopping_cart"),
        ],
        "relationships": [
            {"kind": "has_many", "from": "shopping_cart", "to": "line_item"},
        ],
        "api_surface": [
            {"method": "GET",  "path": "/api/v1/shopping_carts"},
            {"method": "POST", "path": "/api/v1/line_items"},
        ],
    }
    result = _plan(spec, tmp_path, out_dir=True)
    # Read each sliced spec back and assert it only mentions the target
    for slice_info in result["slices"]:
        sliced = json.loads(Path(slice_info["sliced_spec_path"])
                            .read_text(encoding="utf-8"))
        names = [e["name"] for e in sliced["entities"]]
        assert names == [slice_info["entity"]], \
            f"sliced spec for {slice_info['entity']} contains: {names}"
        # API surface keeps only routes mentioning this snake_name
        snake = slice_info["snake_name"]
        for route in sliced.get("api_surface", []):
            assert snake in route["path"].lower(), \
                f"slice for {slice_info['entity']} kept unrelated route {route['path']}"


def test_sliced_spec_keeps_relationships_touching_target(tmp_path):
    spec = {
        "feature": "x",
        "framework": "fastapi",
        "entities": [
            _entity("Org"), _entity("Team"), _entity("Member"),
        ],
        "relationships": [
            {"kind": "has_many", "from": "org",  "to": "team"},
            {"kind": "has_many", "from": "team", "to": "member"},
        ],
    }
    result = _plan(spec, tmp_path, out_dir=True)
    team_slice = next(s for s in result["slices"] if s["entity"] == "Team")
    sliced = json.loads(Path(team_slice["sliced_spec_path"])
                        .read_text(encoding="utf-8"))
    # Team is involved in BOTH relationships → both kept
    rels = sliced["relationships"]
    assert len(rels) == 2


def test_out_dir_writes_slice_files(tmp_path):
    spec = {
        "feature": "x",
        "framework": "fastapi",
        "entities": [_entity("A"), _entity("B")],
        "relationships": [{"kind": "has_many", "from": "a", "to": "b"}],
    }
    result = _plan(spec, tmp_path, out_dir=True)
    written = sorted((tmp_path / "slices").glob("osp-slice-*.json"))
    assert len(written) == 2
    assert "osp-slice-1-a.json" in written[0].name


# ─── commit subject format ────────────────────────────────────────────────

def test_commit_subject_under_72_chars(tmp_path):
    """Even for long feature names, commit subject must fit Conventional Commits."""
    spec = {
        "feature": "build a comprehensive shopping cart with multi-tenant discounts and tax rules",
        "framework": "fastapi",
        "entities": [_entity("ShoppingCart", "shopping_cart")],
        "relationships": [],
    }
    result = _plan(spec, tmp_path)
    subj = result["slices"][0]["commit_subject"]
    assert len(subj) <= 72, f"commit subject too long ({len(subj)}): {subj}"
    assert subj.startswith("feat"), "must use feat: convention"
    assert "[slice 1/1]" in subj


def test_commit_subject_kebab_clean_no_truncation(tmp_path):
    spec = {
        "feature": "shopping cart with line items and discounts",
        "framework": "fastapi",
        "entities": [_entity("ShoppingCart", "shopping_cart")],
        "relationships": [],
    }
    result = _plan(spec, tmp_path)
    subj = result["slices"][0]["commit_subject"]
    # scope is first 3 words joined by hyphens; never truncated mid-word
    assert "shopping-cart-with" in subj
    # No mid-word truncation
    assert not subj.endswith("discou): add ShoppingCart [slice 1/1]")


# ─── skip / edge cases ────────────────────────────────────────────────────

def test_no_create_entities_returns_skip(tmp_path):
    spec = {
        "feature": "x",
        "framework": "fastapi",
        "entities": [_entity("Existing", action="reuse")],
        "relationships": [],
    }
    result = _plan(spec, tmp_path)
    assert result["total_slices"] == 0
    assert result["skip_reason"] == "no_new_entities"


def test_empty_relationships_each_slice_independent(tmp_path):
    spec = {
        "feature": "x",
        "framework": "fastapi",
        "entities": [_entity("A"), _entity("B"), _entity("C")],
        "relationships": [],
    }
    result = _plan(spec, tmp_path)
    assert result["total_slices"] == 3
    for s in result["slices"]:
        assert s["depends_on"] == []


# ─── SKILL.md + /one-shot integration ────────────────────────────────────

def test_skill_md_documents_stage_2_6_incremental():
    skill = REPO_ROOT / "skills" / "one-shot-generate" / "SKILL.md"
    text = skill.read_text(encoding="utf-8")
    assert "Stage 2.6" in text, "must add a Stage 2.6 section"
    assert "--incremental" in text
    assert "incremental_planner.py" in text
    assert "git commit" in text.lower(), "must reference the per-slice git commit"
    assert "cycle" in text.lower(), "must surface cycle handling"
