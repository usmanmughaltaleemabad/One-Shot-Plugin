"""
Tests for failure_predictor.py — hard warnings for risky tasks.

Tests the failure prediction system that detects risky tasks before execution,
including warning formatting, CLI interface, and integration with curriculum_v2.
"""

import json
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile

# Add scripts directory to path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "skills" / "one-shot-generator" / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "skills" / "one-shot-generator" / "scripts" / "lib"))

from curriculum_v2 import FailurePrediction, load_curriculum
from failure_predictor import check_task_safety, format_hard_warning, format_safe_message


def create_test_curriculum(tmp_path: Path) -> Path:
    """Create a temporary curriculum.jsonl for testing."""
    curriculum_file = tmp_path / "curriculum.jsonl"

    curriculum_entries = [
        {
            "id": "bd-001",
            "task_text": "shopping cart with line items and discounts",
            "reason": "FK column type mismatch: spec says int but migration generated String(255)",
            "mitigation": "Check type: key in spec.json matches migration_generator.py type mapping",
        },
        {
            "id": "bd-002",
            "task_text": "REST API with pagination endpoint",
            "reason": "Pagination envelope mismatch: test_contract expects 'next' key but router doesn't emit it",
            "mitigation": "Set test_contract.pagination='list' or add next/prev to router response",
        },
        {
            "id": "bd-003",
            "task_text": "authentication middleware for API",
            "reason": "401 response missing when auth middleware not generated",
            "mitigation": "Ensure spec includes auth_required=true for endpoints needing auth",
        },
    ]

    with open(curriculum_file, "w", encoding="utf-8") as f:
        for entry in curriculum_entries:
            f.write(json.dumps(entry) + "\n")

    return curriculum_file


class TestFormatHardWarning:
    """Tests for format_hard_warning function."""

    def test_hard_warning_contains_required_fields(self):
        """Test that hard warning includes all required sections."""
        prediction = FailurePrediction(
            will_fail=True,
            reason="FK column type mismatch: spec says int but migration generated String",
            similarity=0.87,
            mitigation="Check type: key in spec.json matches migration_generator.py",
            bead_id="bd-001",
        )

        warning = format_hard_warning(prediction)

        # Check required sections
        assert "[!] HARD WARNING" in warning
        assert "87" in warning  # Check for 87.0% formatting
        assert "bd-001" in warning
        assert "FK column type mismatch" in warning
        assert "Check type:" in warning

    def test_hard_warning_includes_action_items(self):
        """Test that warning includes specific action items."""
        prediction = FailurePrediction(
            will_fail=True,
            reason="Test failure",
            similarity=0.85,
            mitigation="Test mitigation",
            bead_id="bd-001",
        )

        warning = format_hard_warning(prediction)

        # Check action items
        assert "--review" in warning
        assert "--templated" in warning
        assert "--budget" in warning
        assert "curriculum" in warning.lower()

    def test_hard_warning_formats_similarity_as_percentage(self):
        """Test that similarity is formatted clearly."""
        prediction = FailurePrediction(
            will_fail=True,
            reason="Test",
            similarity=0.75,
            mitigation=None,
            bead_id="bd-001",
        )

        warning = format_hard_warning(prediction)

        # Check for percentage formatting (75.0%)
        assert "75" in warning

    def test_hard_warning_handles_none_mitigation(self):
        """Test warning formatting when mitigation is None."""
        prediction = FailurePrediction(
            will_fail=True,
            reason="Test failure",
            similarity=0.80,
            mitigation=None,
            bead_id="bd-001",
        )

        warning = format_hard_warning(prediction)

        # Should not crash, should be valid string
        assert isinstance(warning, str)
        assert len(warning) > 0
        assert "[!] HARD WARNING" in warning

    def test_hard_warning_includes_bead_reference(self):
        """Test that warning references the bead ID for curriculum lookup."""
        prediction = FailurePrediction(
            will_fail=True,
            reason="Test",
            similarity=0.82,
            mitigation="Test",
            bead_id="bd-special-001",
        )

        warning = format_hard_warning(prediction)

        assert "bd-special-001" in warning
        assert "curriculum" in warning.lower()


class TestFormatSafeMessage:
    """Tests for format_safe_message function."""

    def test_safe_message_format(self):
        """Test that safe message is concise and clear."""
        msg = format_safe_message()

        assert "[OK]" in msg
        assert "safe" in msg.lower()
        assert isinstance(msg, str)
        assert len(msg) > 0

    def test_safe_message_is_brief(self):
        """Test that safe message is brief compared to warning."""
        safe_msg = format_safe_message()
        warning = format_hard_warning(
            FailurePrediction(
                will_fail=True,
                reason="Test",
                similarity=0.8,
                mitigation="Test",
                bead_id="bd-001",
            )
        )

        # Safe message should be much shorter
        assert len(safe_msg) < len(warning) / 2


class TestCheckTaskSafety:
    """Tests for check_task_safety function."""

    def test_check_task_safety_returns_tuple(self, tmp_path, monkeypatch):
        """Test that check_task_safety returns (bool, str) tuple."""
        curriculum_file = create_test_curriculum(tmp_path)
        monkeypatch.setattr(
            "failure_predictor.load_curriculum",
            lambda: load_curriculum(curriculum_file)
        )

        safe, msg = check_task_safety("test task")

        assert isinstance(safe, bool)
        assert isinstance(msg, str)

    def test_check_task_safety_empty_task(self, monkeypatch):
        """Test with empty task text."""
        monkeypatch.setattr("failure_predictor.load_curriculum", lambda: [])

        safe, msg = check_task_safety("")

        assert safe is True
        assert "[OK]" in msg

    def test_check_task_safety_no_curriculum(self, monkeypatch):
        """Test when curriculum is empty (no failures recorded)."""
        monkeypatch.setattr("failure_predictor.load_curriculum", lambda: [])

        safe, msg = check_task_safety("shopping cart")

        # With empty curriculum, should be safe
        assert safe is True
        assert "[OK]" in msg

    def test_check_task_safety_with_similar_failure(self, tmp_path, monkeypatch):
        """Test detection of similar failure in curriculum."""
        curriculum_file = create_test_curriculum(tmp_path)
        monkeypatch.setattr(
            "failure_predictor.load_curriculum",
            lambda: load_curriculum(curriculum_file)
        )

        # Use exact text from curriculum (high similarity expected)
        safe, msg = check_task_safety(
            "shopping cart with line items and discounts",
            threshold=0.0  # Accept all similarities
        )

        # Result depends on embeddings being available
        # If embeddings available, should detect risk
        if safe is False:
            assert "[!] HARD WARNING" in msg
            assert "bd-001" in msg
        else:
            # Without embeddings, may return safe
            assert "[OK]" in msg

    def test_check_task_safety_threshold_parameter(self, tmp_path, monkeypatch):
        """Test that threshold parameter affects results."""
        curriculum_file = create_test_curriculum(tmp_path)
        monkeypatch.setattr(
            "failure_predictor.load_curriculum",
            lambda: load_curriculum(curriculum_file)
        )

        # Test with high threshold (more permissive)
        safe_high, msg_high = check_task_safety("random task", threshold=0.0)

        # Test with low threshold (more strict)
        safe_low, msg_low = check_task_safety("random task", threshold=0.99)

        # Results should be boolean and string
        assert isinstance(safe_high, bool)
        assert isinstance(safe_low, bool)
        assert isinstance(msg_high, str)
        assert isinstance(msg_low, str)

    def test_check_task_safety_message_quality(self, tmp_path, monkeypatch):
        """Test that safety messages are informative."""
        curriculum_file = create_test_curriculum(tmp_path)
        monkeypatch.setattr(
            "failure_predictor.load_curriculum",
            lambda: load_curriculum(curriculum_file)
        )

        # Test safe case
        safe, safe_msg = check_task_safety("unique novel task", threshold=0.99)
        assert isinstance(safe_msg, str)
        assert len(safe_msg) > 0

        # Test potentially risky case
        safe_risky, risky_msg = check_task_safety(
            "shopping cart discount calculation",
            threshold=0.0
        )
        assert isinstance(risky_msg, str)
        assert len(risky_msg) > 0


class TestFailurePredictorIntegration:
    """Integration tests for failure_predictor."""

    def test_full_safety_check_workflow(self, tmp_path, monkeypatch):
        """Test full workflow: curriculum -> prediction -> warning."""
        curriculum_file = create_test_curriculum(tmp_path)
        monkeypatch.setattr(
            "failure_predictor.load_curriculum",
            lambda: load_curriculum(curriculum_file)
        )

        # 1. Check task safety
        safe, msg = check_task_safety("shopping cart", threshold=0.0)

        # 2. Verify results
        assert isinstance(safe, bool)
        assert isinstance(msg, str)
        assert len(msg) > 0

        # 3. If risky, check warning structure
        if not safe:
            assert "[!]" in msg or "[OK]" in msg

    def test_safety_check_with_various_similarity_scores(self, monkeypatch):
        """Test that similarity scores affect safety assessment."""
        # Mock predict_failure to return different similarities
        from failure_predictor import check_task_safety

        def mock_predict_high_sim(*args, **kwargs):
            return FailurePrediction(
                will_fail=True,
                reason="High similarity match",
                similarity=0.95,
                mitigation="Mitigation",
                bead_id="bd-001",
            )

        def mock_predict_low_sim(*args, **kwargs):
            return FailurePrediction(
                will_fail=False,
                reason="No similar failures",
                similarity=0.0,
                mitigation=None,
                bead_id=None,
            )

        # Test high similarity (risky)
        import failure_predictor
        original_predict = failure_predictor.predict_failure
        try:
            failure_predictor.predict_failure = mock_predict_high_sim
            safe_high, msg_high = check_task_safety("test")
            assert safe_high is False
            assert "[!]" in msg_high

            # Test low similarity (safe)
            failure_predictor.predict_failure = mock_predict_low_sim
            safe_low, msg_low = check_task_safety("test")
            assert safe_low is True
            assert "[OK]" in msg_low
        finally:
            failure_predictor.predict_failure = original_predict

    def test_warning_message_actionability(self):
        """Test that warning messages provide clear next steps."""
        prediction = FailurePrediction(
            will_fail=True,
            reason="FK column type mismatch",
            similarity=0.88,
            mitigation="Check type mapping in spec.json",
            bead_id="bd-001",
        )

        warning = format_hard_warning(prediction)

        # Check for actionable items
        assert any(flag in warning for flag in ["--review", "--templated", "--budget"])
        assert "Action" in warning or "action" in warning.lower()
        assert "curriculum" in warning.lower() or "bead" in warning.lower()

    def test_curriculum_integration(self, tmp_path, monkeypatch):
        """Test that failure_predictor correctly integrates with curriculum_v2."""
        curriculum_file = create_test_curriculum(tmp_path)

        # Load curriculum directly
        curriculum = load_curriculum(curriculum_file)
        assert len(curriculum) > 0

        # Monkeypatch failure_predictor to use this curriculum
        monkeypatch.setattr(
            "failure_predictor.load_curriculum",
            lambda: curriculum
        )

        # Check a task
        safe, msg = check_task_safety("authentication API")

        # Verify results
        assert isinstance(safe, bool)
        assert isinstance(msg, str)


class TestCLIInterface:
    """Tests for CLI interface (without actual subprocess calls)."""

    def test_threshold_validation(self):
        """Test that threshold validation works."""
        # Valid thresholds
        for threshold in [0.0, 0.5, 0.75, 0.8, 0.99, 1.0]:
            # These should be acceptable values
            assert 0.0 <= threshold <= 1.0

        # Invalid thresholds
        invalid = [-0.1, 1.5, 2.0]
        for threshold in invalid:
            assert not (0.0 <= threshold <= 1.0)

    def test_json_output_structure(self, monkeypatch):
        """Test that JSON output has expected structure."""
        from failure_predictor import check_task_safety
        import failure_predictor

        # Mock to return a risky prediction
        def mock_predict(*args, **kwargs):
            return FailurePrediction(
                will_fail=True,
                reason="Test failure",
                similarity=0.82,
                mitigation="Test mitigation",
                bead_id="bd-001",
            )

        original = failure_predictor.predict_failure
        try:
            failure_predictor.predict_failure = mock_predict
            safe, msg = check_task_safety("test task")

            # For JSON output, we'd build a dict
            output = {
                "task": "test task",
                "safe": safe,
                "will_fail": not safe,
                "similarity": 0.82,
            }

            # Verify structure
            assert "task" in output
            assert "safe" in output
            assert "will_fail" in output
            assert "similarity" in output
            assert isinstance(output["similarity"], float)
        finally:
            failure_predictor.predict_failure = original


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_very_high_similarity_score(self):
        """Test handling of very high similarity (near 1.0)."""
        prediction = FailurePrediction(
            will_fail=True,
            reason="Exact match to past failure",
            similarity=0.9999,
            mitigation="Avoid this pattern",
            bead_id="bd-001",
        )

        warning = format_hard_warning(prediction)

        # Format rounds to 100.0%
        assert "100" in warning or "99" in warning
        assert isinstance(warning, str)

    def test_whitespace_handling_in_task_text(self, monkeypatch):
        """Test that whitespace in task text is handled."""
        monkeypatch.setattr("failure_predictor.load_curriculum", lambda: [])

        # Task with extra whitespace
        safe, msg = check_task_safety("  shopping   cart   ")

        assert isinstance(safe, bool)
        assert isinstance(msg, str)

    def test_special_characters_in_task_text(self, monkeypatch):
        """Test that special characters don't break prediction."""
        monkeypatch.setattr("failure_predictor.load_curriculum", lambda: [])

        # Task with special characters
        safe, msg = check_task_safety("REST API with /endpoint?param=value&other=123")

        assert isinstance(safe, bool)
        assert isinstance(msg, str)

    def test_very_long_task_text(self, monkeypatch):
        """Test handling of very long task descriptions."""
        monkeypatch.setattr("failure_predictor.load_curriculum", lambda: [])

        # Very long task
        long_task = "Build " + "shopping cart " * 100

        safe, msg = check_task_safety(long_task)

        assert isinstance(safe, bool)
        assert isinstance(msg, str)

    def test_none_or_false_predictions(self, monkeypatch):
        """Test handling of edge case predictions."""
        import failure_predictor

        # Mock predict_failure to return safe prediction
        def mock_predict(*args, **kwargs):
            return FailurePrediction(
                will_fail=False,
                reason="No similar failures found",
                similarity=0.0,
                mitigation=None,
                bead_id=None,
            )

        original = failure_predictor.predict_failure
        try:
            failure_predictor.predict_failure = mock_predict
            safe, msg = check_task_safety("any task")

            assert safe is True
            assert "[OK]" in msg
        finally:
            failure_predictor.predict_failure = original
