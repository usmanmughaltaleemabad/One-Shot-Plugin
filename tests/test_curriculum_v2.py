"""
Tests for curriculum_v2.py — embedding-based failure prediction.

Tests the semantic similarity matching approach using embeddings,
including curriculum loading, similarity computation, and predictions.
"""

import json
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile

# Add scripts directory to path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "skills" / "one-shot-generator" / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "skills" / "one-shot-generator" / "scripts" / "lib"))

from curriculum_v2 import (
    FailurePrediction,
    find_similar_failures,
    load_curriculum,
    predict_failure,
)


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
        {
            "id": "bd-004",
            "task_text": "database migration with foreign keys",
            "reason": "Migration fails because FK reference column has wrong type",
            "mitigation": "Verify both columns use same integer type (Integer, not String)",
        },
        {
            "id": "bd-005",
            "task_text": "user registration flow with email validation",
            "reason": "Email regex validation too strict, rejects valid emails",
            "mitigation": "Use RFC 5322 compliant email regex or rely on email service validation",
        },
    ]

    with open(curriculum_file, "w", encoding="utf-8") as f:
        for entry in curriculum_entries:
            f.write(json.dumps(entry) + "\n")

    return curriculum_file


class TestLoadCurriculum:
    """Tests for load_curriculum function."""

    def test_load_curriculum_from_file(self, tmp_path):
        """Test loading curriculum from a specific file."""
        curriculum_file = create_test_curriculum(tmp_path)
        curriculum = load_curriculum(curriculum_file)

        assert len(curriculum) == 5
        assert curriculum[0]["id"] == "bd-001"
        assert "shopping cart" in curriculum[0]["task_text"]

    def test_load_curriculum_empty_file(self, tmp_path):
        """Test loading from empty curriculum file."""
        curriculum_file = tmp_path / "empty.jsonl"
        curriculum_file.write_text("")

        curriculum = load_curriculum(curriculum_file)
        assert curriculum == []

    def test_load_curriculum_file_not_found(self):
        """Test loading from non-existent file."""
        curriculum = load_curriculum(Path("/nonexistent/path/curriculum.jsonl"))
        assert curriculum == []

    def test_load_curriculum_with_invalid_json_lines(self, tmp_path):
        """Test that invalid JSON lines are skipped."""
        curriculum_file = tmp_path / "mixed.jsonl"
        curriculum_file.write_text(
            '{"id": "bd-001", "task_text": "valid"}\n'
            "invalid json line\n"
            '{"id": "bd-002", "task_text": "also valid"}\n'
        )

        curriculum = load_curriculum(curriculum_file)
        assert len(curriculum) == 2
        assert curriculum[0]["id"] == "bd-001"
        assert curriculum[1]["id"] == "bd-002"

    def test_load_curriculum_with_blank_lines(self, tmp_path):
        """Test that blank lines are handled gracefully."""
        curriculum_file = tmp_path / "with_blanks.jsonl"
        curriculum_file.write_text(
            '{"id": "bd-001", "task_text": "first"}\n'
            "\n"
            '{"id": "bd-002", "task_text": "second"}\n'
            "   \n"
        )

        curriculum = load_curriculum(curriculum_file)
        assert len(curriculum) == 2


class TestFindSimilarFailures:
    """Tests for find_similar_failures function."""

    def test_find_similar_failures_empty_task(self, tmp_path):
        """Test with empty task text."""
        curriculum_file = create_test_curriculum(tmp_path)
        curriculum = load_curriculum(curriculum_file)

        result = find_similar_failures("", curriculum=curriculum)
        assert result == []

    def test_find_similar_failures_empty_curriculum(self):
        """Test with empty curriculum."""
        result = find_similar_failures("shopping cart", curriculum=[])
        assert result == []

    def test_find_similar_failures_no_curriculum(self, monkeypatch):
        """Test when curriculum file doesn't exist (returns empty)."""
        # Mock load_curriculum to return empty
        import curriculum_v2
        monkeypatch.setattr(curriculum_v2, "load_curriculum", lambda *args, **kw: [])
        result = find_similar_failures("test task")
        assert result == []

    def test_find_similar_failures_curriculum_without_embeddings(self, tmp_path):
        """Test with curriculum but no embeddings available.

        When sentence-transformers is unavailable, get_embedding returns None
        and we should get empty results (graceful degradation).
        """
        curriculum_file = create_test_curriculum(tmp_path)
        curriculum = load_curriculum(curriculum_file)

        # Mock get_embedding to return None (embeddings unavailable)
        import curriculum_v2
        original_get_embedding = curriculum_v2.get_embedding

        def mock_get_embedding(_: str):
            return None

        curriculum_v2.get_embedding = mock_get_embedding
        try:
            result = find_similar_failures("shopping cart", curriculum=curriculum)
            assert result == []
        finally:
            curriculum_v2.get_embedding = original_get_embedding

    def test_find_similar_failures_includes_similarity_score(self, tmp_path):
        """Test that returned results include similarity score."""
        curriculum_file = create_test_curriculum(tmp_path)
        curriculum = load_curriculum(curriculum_file)

        # Try to find similar failures
        result = find_similar_failures(
            "shopping cart with items",
            curriculum=curriculum,
            threshold=0.0,  # Accept all, even low similarities
        )

        # If embeddings are available, check structure
        if result:
            for item in result:
                assert "similarity" in item
                assert isinstance(item["similarity"], (int, float))
                assert 0.0 <= item["similarity"] <= 1.0

    def test_find_similar_failures_respects_threshold(self, tmp_path):
        """Test that threshold filters results correctly."""
        curriculum_file = create_test_curriculum(tmp_path)
        curriculum = load_curriculum(curriculum_file)

        # High threshold should filter out most/all results
        high_threshold_result = find_similar_failures(
            "something unrelated",
            curriculum=curriculum,
            threshold=0.99,
        )

        # Low threshold should allow more results (if embeddings available)
        low_threshold_result = find_similar_failures(
            "something unrelated",
            curriculum=curriculum,
            threshold=0.0,
        )

        # low_threshold should have >= high_threshold results
        assert len(low_threshold_result) >= len(high_threshold_result)

    def test_find_similar_failures_sorted_by_similarity(self, tmp_path):
        """Test that results are sorted by similarity descending."""
        curriculum_file = create_test_curriculum(tmp_path)
        curriculum = load_curriculum(curriculum_file)

        result = find_similar_failures(
            "shopping cart",
            curriculum=curriculum,
            threshold=0.0,  # Accept all
        )

        if len(result) > 1:
            # Check descending order
            similarities = [r.get("similarity", 0.0) for r in result]
            assert similarities == sorted(similarities, reverse=True)


class TestPredictFailure:
    """Tests for predict_failure function."""

    def test_predict_failure_returns_prediction_object(self, tmp_path):
        """Test that predict_failure returns a FailurePrediction."""
        curriculum_file = create_test_curriculum(tmp_path)
        curriculum = load_curriculum(curriculum_file)

        result = predict_failure("shopping cart", curriculum=curriculum)

        assert isinstance(result, FailurePrediction)
        assert hasattr(result, "will_fail")
        assert hasattr(result, "reason")
        assert hasattr(result, "similarity")

    def test_predict_failure_empty_task(self, tmp_path):
        """Test with empty task text."""
        curriculum_file = create_test_curriculum(tmp_path)
        curriculum = load_curriculum(curriculum_file)

        result = predict_failure("", curriculum=curriculum)

        assert result.will_fail is False
        assert result.similarity == 0.0

    def test_predict_failure_no_similar_failures(self, tmp_path):
        """Test when no similar failures found."""
        curriculum_file = create_test_curriculum(tmp_path)
        curriculum = load_curriculum(curriculum_file)

        result = predict_failure(
            "xyz_unlikely_nonsense_task",
            curriculum=curriculum,
            threshold=0.99,
        )

        assert result.will_fail is False
        assert "No similar failures" in result.reason or len(result.reason) > 0

    def test_predict_failure_with_similar_failures(self, tmp_path):
        """Test when similar failures are found."""
        curriculum_file = create_test_curriculum(tmp_path)
        curriculum = load_curriculum(curriculum_file)

        # Use exact match (or very close)
        result = predict_failure(
            "shopping cart with line items and discounts",
            curriculum=curriculum,
            threshold=0.0,
        )

        # If embeddings available and match found, should have warning
        if result.will_fail:
            assert result.similarity > 0.0
            assert result.mitigation is not None or result.reason
            assert result.bead_id is not None

    def test_predict_failure_most_similar_used(self, tmp_path):
        """Test that the most similar failure is returned."""
        curriculum_file = create_test_curriculum(tmp_path)
        curriculum = load_curriculum(curriculum_file)

        result = predict_failure(
            "shopping cart",
            curriculum=curriculum,
            threshold=0.0,
        )

        # If multiple similar failures found, most_similar should be used
        # (highest similarity score)
        if result.will_fail:
            similar = find_similar_failures("shopping cart", curriculum=curriculum,
                                            threshold=0.0)
            if similar:
                assert result.similarity == similar[0].get("similarity", 0.0)

    def test_predict_failure_to_dict(self, tmp_path):
        """Test that FailurePrediction.to_dict() works."""
        result = FailurePrediction(
            will_fail=True,
            reason="Test reason",
            similarity=0.85,
            mitigation="Test mitigation",
            bead_id="bd-001",
        )

        d = result.to_dict()
        assert isinstance(d, dict)
        assert d["will_fail"] is True
        assert d["reason"] == "Test reason"
        assert d["similarity"] == 0.85
        assert d["mitigation"] == "Test mitigation"
        assert d["bead_id"] == "bd-001"


class TestCurriculumIntegration:
    """Integration tests for curriculum_v2."""

    def test_curriculum_loading_and_prediction_flow(self, tmp_path):
        """Test the full flow: load curriculum, find similar, predict."""
        curriculum_file = create_test_curriculum(tmp_path)

        # Load curriculum
        curriculum = load_curriculum(curriculum_file)
        assert len(curriculum) > 0

        # Find similar failures for a task
        similar = find_similar_failures("payment processing", curriculum=curriculum)
        # Should return list (may be empty if no embeddings)
        assert isinstance(similar, list)

        # Predict failure
        prediction = predict_failure("payment processing", curriculum=curriculum)
        assert isinstance(prediction, FailurePrediction)

    def test_curriculum_fields_preserved(self, tmp_path):
        """Test that curriculum entry fields are preserved in results."""
        curriculum_file = tmp_path / "test.jsonl"
        test_entry = {
            "id": "test-001",
            "task_text": "example task",
            "reason": "test reason",
            "mitigation": "test mitigation",
            "extra_field": "should be preserved",
        }
        curriculum_file.write_text(json.dumps(test_entry) + "\n")

        curriculum = load_curriculum(curriculum_file)
        assert curriculum[0]["extra_field"] == "should be preserved"

    def test_curriculum_different_task_text_keys(self, tmp_path):
        """Test curriculum entries with different task text key names."""
        curriculum_file = tmp_path / "test.jsonl"
        curriculum_file.write_text(
            '{"id": "bd-1", "task_text": "first entry"}\n'
            '{"id": "bd-2", "task": "second entry"}\n'
        )

        curriculum = load_curriculum(curriculum_file)
        assert len(curriculum) == 2
        # Both should be loadable
        similar = find_similar_failures("entry", curriculum=curriculum)
        # May return 0-2 results depending on embeddings
        assert isinstance(similar, list)
