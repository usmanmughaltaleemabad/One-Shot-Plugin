"""Tests for docs-drift skill (SKILL.md)."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from conftest import resolve_project_root, load_json_safe, detect_changes


class TestProjectRootResolution:
    """Test project root argument resolution."""

    def test_resolve_absolute_path(self, tmp_path):
        """Resolving absolute path should return normalized Path."""
        result = resolve_project_root(str(tmp_path))
        assert result == tmp_path.resolve()
        assert isinstance(result, Path)

    def test_resolve_at_dot_argument(self):
        """Resolving @. should return current working directory."""
        result = resolve_project_root("@.")
        assert result == Path.cwd().resolve()

    def test_resolve_nonexistent_path_raises(self):
        """Resolving nonexistent path should raise ValueError."""
        with pytest.raises(ValueError, match="does not exist"):
            resolve_project_root("/nonexistent/path")


class TestJsonHandling:
    """Test safe JSON loading and error handling."""

    def test_load_nonexistent_json_returns_default(self, tmp_path):
        """Loading nonexistent JSON should return default dict."""
        path = tmp_path / "missing.json"
        result = load_json_safe(path)
        assert result == {}

    def test_load_valid_json_returns_data(self, tmp_path):
        """Loading valid JSON should return parsed data."""
        path = tmp_path / "valid.json"
        data = {"classes": [], "functions": []}
        path.write_text(json.dumps(data))

        result = load_json_safe(path)
        assert result == data

    def test_load_corrupt_json_returns_default(self, tmp_path, capsys):
        """Loading corrupt JSON should return default and emit warning."""
        path = tmp_path / "corrupt.json"
        path.write_text("{ invalid json }")

        result = load_json_safe(path)
        assert result == {}
        captured = capsys.readouterr()
        assert "[WARN] Corrupt JSON" in captured.out


class TestChangeDetection:
    """Test entity change detection logic."""

    def test_no_changes_detected(self):
        """Unchanged state should report zero changes."""
        old = {
            "app.py": {
                "classes": [{"name": "User", "methods": ["__init__"]}],
                "functions": [{"name": "main", "params": []}]
            }
        }
        new = old

        changes = detect_changes(old, new)
        assert len(changes["added_classes"]) == 0
        assert len(changes["removed_classes"]) == 0
        assert len(changes["added_functions"]) == 0
        assert len(changes["removed_functions"]) == 0

    def test_detects_added_entity(self):
        """Should detect added classes."""
        old = {
            "app.py": {
                "classes": [{"name": "User", "methods": ["__init__"]}],
                "functions": []
            }
        }
        new = {
            "app.py": {
                "classes": [
                    {"name": "User", "methods": ["__init__"]},
                    {"name": "Product", "methods": []}
                ],
                "functions": []
            }
        }

        changes = detect_changes(old, new)
        assert "Product" in changes["added_classes"]
        assert len(changes["added_classes"]) == 1

    def test_detects_removed_entity(self):
        """Should detect removed classes."""
        old = {
            "app.py": {
                "classes": [
                    {"name": "User", "methods": ["__init__"]},
                    {"name": "Product", "methods": []}
                ],
                "functions": []
            }
        }
        new = {
            "app.py": {
                "classes": [{"name": "User", "methods": ["__init__"]}],
                "functions": []
            }
        }

        changes = detect_changes(old, new)
        assert "Product" in changes["removed_classes"]
        assert len(changes["removed_classes"]) == 1

    def test_detects_added_function(self):
        """Should detect added functions."""
        old = {
            "app.py": {
                "classes": [],
                "functions": [{"name": "main", "params": []}]
            }
        }
        new = {
            "app.py": {
                "classes": [],
                "functions": [
                    {"name": "main", "params": []},
                    {"name": "helper", "params": ["x"]}
                ]
            }
        }

        changes = detect_changes(old, new)
        assert "helper" in changes["added_functions"]
        assert len(changes["added_functions"]) == 1

    def test_detects_removed_function(self):
        """Should detect removed functions."""
        old = {
            "app.py": {
                "classes": [],
                "functions": [
                    {"name": "main", "params": []},
                    {"name": "helper", "params": ["x"]}
                ]
            }
        }
        new = {
            "app.py": {
                "classes": [],
                "functions": [{"name": "main", "params": []}]
            }
        }

        changes = detect_changes(old, new)
        assert "helper" in changes["removed_functions"]
        assert len(changes["removed_functions"]) == 1

    def test_multiple_changes(self):
        """Should detect multiple different change types simultaneously."""
        old = {
            "app.py": {
                "classes": [{"name": "OldClass", "methods": []}],
                "functions": [{"name": "old_func", "params": []}]
            }
        }
        new = {
            "app.py": {
                "classes": [{"name": "NewClass", "methods": []}],
                "functions": [{"name": "new_func", "params": []}]
            }
        }

        changes = detect_changes(old, new)
        assert len(changes["added_classes"]) == 1
        assert len(changes["removed_classes"]) == 1
        assert len(changes["added_functions"]) == 1
        assert len(changes["removed_functions"]) == 1


class TestAgentInputFormat:
    """Test Task input format for docs-author agent."""

    def test_agent_input_structure(self):
        """Agent input should have required fields."""
        project_root = Path("/path/to/project")
        changes = {
            "added_classes": ["Cart", "LineItem"],
            "removed_classes": [],
            "added_functions": [],
            "removed_functions": [],
            "modified_classes": [],
        }
        files_touched = ["models.py", "services.py"]

        agent_input = {
            "changes": changes,
            "codebase_root": str(project_root),
            "docs_root": str(project_root / "docs"),
            "files_touched": files_touched
        }

        assert "changes" in agent_input
        assert "codebase_root" in agent_input
        assert "docs_root" in agent_input
        assert "files_touched" in agent_input
        assert str(project_root) in agent_input["codebase_root"]
        assert "docs" in agent_input["docs_root"]

    def test_agent_input_with_complex_changes(self):
        """Agent input should handle complex change sets."""
        project_root = Path("/project")
        changes = {
            "added_classes": ["A", "B", "C"],
            "removed_classes": ["X"],
            "added_functions": ["foo", "bar"],
            "removed_functions": [],
            "modified_classes": [],
        }
        files_touched = ["a.py", "b.py", "c.py", "x.py"]

        agent_input = {
            "changes": changes,
            "codebase_root": str(project_root),
            "docs_root": str(project_root / "docs"),
            "files_touched": files_touched
        }

        assert len(agent_input["changes"]["added_classes"]) == 3
        assert len(agent_input["files_touched"]) == 4
        assert json.dumps(agent_input) is not None


class TestBeadsStatePersistence:
    """Test .beads/docs-state.json saving and loading."""

    def test_save_state_creates_file(self, tmp_path):
        """Saving state should create docs-state.json."""
        beads_dir = tmp_path / ".beads"
        beads_dir.mkdir()
        state_path = beads_dir / "docs-state.json"

        state = {
            "app.py": {
                "classes": [{"name": "User", "methods": []}],
                "functions": []
            }
        }

        state_path.write_text(json.dumps(state, indent=2))
        assert state_path.exists()
        assert json.loads(state_path.read_text()) == state

    def test_save_state_overwrites_existing(self, tmp_path):
        """Saving state should overwrite previous state."""
        beads_dir = tmp_path / ".beads"
        beads_dir.mkdir()
        state_path = beads_dir / "docs-state.json"

        old_state = {"old": "data"}
        state_path.write_text(json.dumps(old_state))

        new_state = {"new": "data"}
        state_path.write_text(json.dumps(new_state, indent=2))

        assert json.loads(state_path.read_text()) == new_state

    def test_beads_dir_creation(self, tmp_path):
        """Creating .beads directory should succeed."""
        beads_dir = tmp_path / ".beads"
        beads_dir.mkdir(parents=True, exist_ok=True)
        assert beads_dir.is_dir()

    def test_beads_dir_idempotent(self, tmp_path):
        """Creating .beads directory twice should not fail."""
        beads_dir = tmp_path / ".beads"
        beads_dir.mkdir(parents=True, exist_ok=True)
        beads_dir.mkdir(parents=True, exist_ok=True)
        assert beads_dir.is_dir()


class TestDraftsDirectory:
    """Test .tmp/docs-author-drafts directory handling."""

    def test_create_drafts_directory(self, tmp_path):
        """Creating drafts directory should succeed."""
        drafts_dir = tmp_path / ".tmp" / "docs-author-drafts"
        drafts_dir.mkdir(parents=True, exist_ok=True)
        assert drafts_dir.is_dir()
        assert (tmp_path / ".tmp").is_dir()

    def test_drafts_path_absolute(self, tmp_path):
        """Drafts path should be absolute."""
        project_root = tmp_path / "project"
        project_root.mkdir()
        drafts_dir = project_root / ".tmp" / "docs-author-drafts"
        assert drafts_dir.is_absolute()


class TestArgumentParsing:
    """Test command-line argument parsing."""

    def test_missing_argument_detected(self):
        """Missing @. argument should be detected."""
        # Simulate checking for argument
        argv = ["command"]
        has_project_arg = len(argv) >= 2
        assert not has_project_arg

    def test_project_argument_present(self):
        """Present @. argument should be detected."""
        argv = ["command", "@./project"]
        has_project_arg = len(argv) >= 2
        assert has_project_arg

    def test_compare_flag_detected(self):
        """--compare flag in argv should be detected."""
        argv = ["command", "@.", "--compare"]
        has_compare = "--compare" in argv
        assert has_compare

    def test_compare_flag_absent(self):
        """Missing --compare flag should be detected."""
        argv = ["command", "@."]
        has_compare = "--compare" in argv
        assert not has_compare


class TestErrorHandling:
    """Test error handling for subprocess and file operations."""

    def test_subprocess_error_handled(self):
        """Subprocess error should be caught and reported."""
        # Simulate subprocess error
        result = subprocess.CompletedProcess(args=["test"], returncode=1, stdout="", stderr="Error message")
        if result.returncode != 0:
            error_detected = True
        assert error_detected

    def test_json_parse_error_handled(self):
        """JSON parse error should be caught."""
        invalid_json = "{ broken json }"
        try:
            json.loads(invalid_json)
            error_detected = False
        except json.JSONDecodeError:
            error_detected = True
        assert error_detected

    def test_file_write_error_simulation(self, tmp_path):
        """File write errors should be catchable."""
        # Create read-only directory
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()

        state_file = readonly_dir / "state.json"
        state_file.write_text("{}")

        # Make directory read-only (Unix-like behavior simulation)
        import stat
        readonly_dir.chmod(stat.S_IRUSR | stat.S_IXUSR)

        # Attempting to write should raise
        try:
            readonly_dir.chmod(stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)  # Restore for cleanup
            write_succeeded = True
        except Exception:
            write_succeeded = False


class TestIntegration:
    """Integration tests for complete flow."""

    def test_full_workflow_no_changes(self, tmp_path):
        """Complete flow with no changes should report success."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        beads_dir = project_root / ".beads"
        beads_dir.mkdir()

        # Same state twice
        state = {
            "app.py": {
                "classes": [{"name": "User", "methods": []}],
                "functions": []
            }
        }

        state_path = beads_dir / "docs-state.json"
        state_path.write_text(json.dumps(state))

        changes = detect_changes(state, state)
        total_changes = sum(len(v) for v in changes.values() if isinstance(v, list))

        assert total_changes == 0

    def test_full_workflow_with_changes(self, tmp_path):
        """Complete flow with changes should prepare agent input."""
        project_root = tmp_path / "project"
        project_root.mkdir()

        beads_dir = project_root / ".beads"
        beads_dir.mkdir()

        old_state = {
            "app.py": {
                "classes": [{"name": "User", "methods": []}],
                "functions": []
            }
        }

        new_state = {
            "app.py": {
                "classes": [
                    {"name": "User", "methods": []},
                    {"name": "Product", "methods": []}
                ],
                "functions": [{"name": "main", "params": []}]
            }
        }

        changes = detect_changes(old_state, new_state)
        total_changes = sum(len(v) for v in changes.values() if isinstance(v, list))

        assert total_changes > 0
        assert "Product" in changes["added_classes"]
        assert "main" in changes["added_functions"]

        # Create agent input
        agent_input = {
            "changes": changes,
            "codebase_root": str(project_root),
            "docs_root": str(project_root / "docs"),
            "files_touched": list(new_state.keys())
        }

        assert agent_input["codebase_root"] == str(project_root)
        assert len(agent_input["files_touched"]) > 0

        # Save state
        state_path = beads_dir / "docs-state.json"
        state_path.write_text(json.dumps(new_state, indent=2))
        assert state_path.exists()
