"""
Tests that verify the 6 mattpocock-inspired skills are actually wired into
the /one-shot pipeline stages — not just listed in the README.

If any of these fail, the README's 'integrated productivity skills' claim
is overselling. Either re-wire or downgrade the claim.
"""
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).parent.parent
SKILL_DIR = REPO_ROOT / "skills" / "one-shot-generate"
SKILL = SKILL_DIR / "SKILL.md"
STAGES = SKILL_DIR / "stages"


def _stage(name: str) -> str:
    return (STAGES / f"{name}.md").read_text(encoding="utf-8")


# ─── grill-me ────────────────────────────────────────────────────────────────

def test_plan_stage_invokes_grill_me():
    """Stage 1.6 must reference the grill-me skill."""
    plan = _stage("plan")
    assert "grill-me" in plan.lower(), \
        "stages/plan.md must reference grill-me skill"
    assert "@./../../grill-me/SKILL.md" in plan, \
        "stages/plan.md must use the standard skill-include syntax"
    assert "Stage 1.6" in plan, "grill-me must live at Stage 1.6"


def test_grill_me_has_explicit_trigger_conditions():
    """The wiring must specify WHEN grill-me fires, not just that it exists."""
    plan = _stage("plan")
    # Conditions documented as: --grill flag, 0 entities, short description,
    # or low confidence
    assert "--grill" in plan
    assert "confidence" in plan.lower()


# ─── caveman ─────────────────────────────────────────────────────────────────

def test_verify_stage_invokes_caveman_for_large_prompts():
    """Reviewer/critic inputs > 8k tokens should route through caveman."""
    verify = _stage("verify")
    assert "caveman" in verify.lower()
    assert "@./../../caveman/SKILL.md" in verify
    assert "--preserve-code" in verify, \
        "caveman must preserve code blocks during compression"


def test_caveman_has_skip_condition():
    """Compression should skip when prompt is small (no savings worth the step)."""
    verify = _stage("verify")
    assert "--no-compress" in verify or "under 8k" in verify.lower()


# ─── tdd-cycle ───────────────────────────────────────────────────────────────

def test_build_stage_offers_tdd_strict_mode():
    """Stage 3 must offer routing through tdd-cycle skill."""
    build = _stage("build")
    assert "tdd-cycle" in build.lower()
    assert "@./../../tdd-cycle/SKILL.md" in build
    assert "--tdd-strict" in build
    # The 3-phase pattern must be documented
    for phase in ("red", "green", "refactor"):
        assert phase in build.lower(), \
            f"tdd-cycle integration must mention {phase} phase"


# ─── systematic-debug ────────────────────────────────────────────────────────

def test_ship_stage_invokes_systematic_debug_on_repeat_failures():
    """When critic hits the same failure twice, force root-cause investigation."""
    ship = _stage("ship")
    assert "systematic-debug" in ship.lower()
    assert "@./../../systematic-debug/SKILL.md" in ship
    # Must specify the trigger: iteration >= 2 with same failure
    assert "iteration" in ship.lower() or "iter" in ship.lower()


def test_systematic_debug_has_opt_out():
    ship = _stage("ship")
    assert "--no-systematic-debug" in ship


# ─── handoff ─────────────────────────────────────────────────────────────────

def test_record_stage_emits_handoff_on_shipped():
    """SHIPPED runs must produce a compact handoff document."""
    record = _stage("record")
    assert "handoff" in record.lower()
    assert "@./../../handoff/SKILL.md" in record
    assert "Stage 8.5" in record, "handoff lives at Stage 8.5"
    # Trigger conditions
    assert "SHIPPED" in record


def test_handoff_has_opt_out():
    record = _stage("record")
    assert "--no-handoff" in record


# ─── Dispatcher (SKILL.md) ───────────────────────────────────────────────────

def test_dispatcher_documents_all_5_skill_integration_flags():
    """SKILL.md flag section must list every wiring flag for discoverability."""
    skill = SKILL.read_text(encoding="utf-8")
    for flag in ("--grill", "--tdd-strict", "--no-compress",
                 "--no-systematic-debug", "--no-handoff"):
        assert flag in skill, \
            f"SKILL.md flag list must document {flag}"


def test_dispatcher_pipeline_summary_names_each_skill():
    """The PLAN/BUILD/VERIFY/SHIP/RECORD summary must mention the skills."""
    skill = SKILL.read_text(encoding="utf-8")
    for name in ("grill-me", "tdd-cycle", "caveman",
                 "systematic-debug", "handoff"):
        assert name in skill.lower(), \
            f"dispatcher pipeline summary must reference {name}"


# ─── Skills exist as advertised ──────────────────────────────────────────────

@pytest.mark.parametrize("skill_name", [
    "grill-me", "caveman", "tdd-cycle",
    "systematic-debug", "handoff", "write-a-skill",
])
def test_each_referenced_skill_actually_exists(skill_name):
    """No broken references — every wired skill must have its SKILL.md."""
    path = REPO_ROOT / "skills" / skill_name / "SKILL.md"
    assert path.exists(), f"skills/{skill_name}/SKILL.md must exist"
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---"), \
        f"skills/{skill_name}/SKILL.md must have YAML frontmatter"
    assert f"name: {skill_name}" in text
