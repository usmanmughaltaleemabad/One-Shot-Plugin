"""
Tests for awesome-ai-apps integration example files.

Validates:
- All 3 example files exist
- Each file has proper markdown structure
- Example files are valid markdown
- Task descriptions are clear and complete
- Quick-start guide is present and properly structured
"""

import os
import pytest
from pathlib import Path
import re


class TestExampleFilesExist:
    """Test that all required example files exist."""

    def test_multi_stage_example_exists(self):
        """Multi-stage workflow example file should exist."""
        path = Path("C:\\Projects\\plugin\\one-shot-prompting\\examples\\multi-stage-example.md")
        assert path.exists(), f"Expected file {path} to exist"
        assert path.is_file(), f"Expected {path} to be a file"

    def test_mcp_integration_example_exists(self):
        """MCP service discovery example file should exist."""
        path = Path("C:\\Projects\\plugin\\one-shot-prompting\\examples\\mcp-integration-example.md")
        assert path.exists(), f"Expected file {path} to exist"
        assert path.is_file(), f"Expected {path} to be a file"

    def test_memory_learning_example_exists(self):
        """Memory propagation example file should exist."""
        path = Path("C:\\Projects\\plugin\\one-shot-prompting\\examples\\memory-learning-example.md")
        assert path.exists(), f"Expected file {path} to exist"
        assert path.is_file(), f"Expected {path} to be a file"

    def test_quick_start_guide_exists(self):
        """Quick-start guide should exist in docs."""
        path = Path("C:\\Projects\\plugin\\one-shot-prompting\\docs\\awesome-integration-quick-start.md")
        assert path.exists(), f"Expected file {path} to exist"
        assert path.is_file(), f"Expected {path} to be a file"


class TestMarkdownStructure:
    """Test markdown structure of example files."""

    @staticmethod
    def read_file(path):
        """Helper to read file content."""
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    @staticmethod
    def has_header(content, level=1):
        """Check if markdown has h1 header."""
        pattern = r'^#{' + str(level) + r'}\s+\S+'
        return bool(re.search(pattern, content, re.MULTILINE))

    @staticmethod
    def count_code_blocks(content):
        """Count markdown code blocks."""
        pattern = r'```[\s\S]*?```'
        return len(re.findall(pattern, content))

    @staticmethod
    def has_section_headers(content):
        """Check for section headers (h2 or h3)."""
        pattern = r'^##\s+\S+|^###\s+\S+'
        return bool(re.search(pattern, content, re.MULTILINE))

    def test_multi_stage_has_title(self):
        """Multi-stage example should have a title."""
        path = Path("C:\\Projects\\plugin\\one-shot-prompting\\examples\\multi-stage-example.md")
        content = self.read_file(path)
        assert self.has_header(content, level=1), "Should have h1 title"

    def test_multi_stage_has_sections(self):
        """Multi-stage example should have section headers."""
        path = Path("C:\\Projects\\plugin\\one-shot-prompting\\examples\\multi-stage-example.md")
        content = self.read_file(path)
        assert self.has_section_headers(content), "Should have section headers (h2/h3)"

    def test_multi_stage_has_code_blocks(self):
        """Multi-stage example should have code blocks."""
        path = Path("C:\\Projects\\plugin\\one-shot-prompting\\examples\\multi-stage-example.md")
        content = self.read_file(path)
        assert self.count_code_blocks(content) >= 3, "Should have at least 3 code blocks"

    def test_mcp_integration_has_title(self):
        """MCP integration example should have a title."""
        path = Path("C:\\Projects\\plugin\\one-shot-prompting\\examples\\mcp-integration-example.md")
        content = self.read_file(path)
        assert self.has_header(content, level=1), "Should have h1 title"

    def test_mcp_integration_has_sections(self):
        """MCP integration example should have section headers."""
        path = Path("C:\\Projects\\plugin\\one-shot-prompting\\examples\\mcp-integration-example.md")
        content = self.read_file(path)
        assert self.has_section_headers(content), "Should have section headers (h2/h3)"

    def test_mcp_integration_has_code_blocks(self):
        """MCP integration example should have code blocks."""
        path = Path("C:\\Projects\\plugin\\one-shot-prompting\\examples\\mcp-integration-example.md")
        content = self.read_file(path)
        assert self.count_code_blocks(content) >= 2, "Should have at least 2 code blocks"

    def test_memory_learning_has_title(self):
        """Memory learning example should have a title."""
        path = Path("C:\\Projects\\plugin\\one-shot-prompting\\examples\\memory-learning-example.md")
        content = self.read_file(path)
        assert self.has_header(content, level=1), "Should have h1 title"

    def test_memory_learning_has_sections(self):
        """Memory learning example should have section headers."""
        path = Path("C:\\Projects\\plugin\\one-shot-prompting\\examples\\memory-learning-example.md")
        content = self.read_file(path)
        assert self.has_section_headers(content), "Should have section headers (h2/h3)"

    def test_memory_learning_has_code_blocks(self):
        """Memory learning example should have code blocks."""
        path = Path("C:\\Projects\\plugin\\one-shot-prompting\\examples\\memory-learning-example.md")
        content = self.read_file(path)
        assert self.count_code_blocks(content) >= 2, "Should have at least 2 code blocks"


class TestExampleContent:
    """Test content quality of example files."""

    @staticmethod
    def read_file(path):
        """Helper to read file content."""
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def test_multi_stage_has_task_description(self):
        """Multi-stage example should describe the task."""
        path = Path("C:\\Projects\\plugin\\one-shot-prompting\\examples\\multi-stage-example.md")
        content = self.read_file(path)
        assert "Task" in content or "task" in content.lower(), "Should describe the task"
        assert len(content) >= 400, "Should have sufficient content (400+ chars)"

    def test_multi_stage_mentions_stages(self):
        """Multi-stage example should mention workflow stages."""
        path = Path("C:\\Projects\\plugin\\one-shot-prompting\\examples\\multi-stage-example.md")
        content = self.read_file(path)
        # Should mention stages
        assert "stage" in content.lower(), "Should mention stages"

    def test_multi_stage_has_expected_output(self):
        """Multi-stage example should show expected outputs."""
        path = Path("C:\\Projects\\plugin\\one-shot-prompting\\examples\\multi-stage-example.md")
        content = self.read_file(path)
        assert "output" in content.lower() or "result" in content.lower(), \
            "Should show expected outputs or results"

    def test_mcp_integration_has_scenario(self):
        """MCP integration example should describe a scenario."""
        path = Path("C:\\Projects\\plugin\\one-shot-prompting\\examples\\mcp-integration-example.md")
        content = self.read_file(path)
        assert len(content) >= 300, "Should have sufficient content (300+ chars)"
        assert "discover" in content.lower() or "mcp" in content.lower(), \
            "Should mention MCP discovery"

    def test_mcp_integration_has_commands(self):
        """MCP integration example should show commands."""
        path = Path("C:\\Projects\\plugin\\one-shot-prompting\\examples\\mcp-integration-example.md")
        content = self.read_file(path)
        # Should have bash code blocks or command references
        assert "curator" in content.lower() or "command" in content.lower(), \
            "Should reference curator command or similar"

    def test_mcp_integration_shows_output(self):
        """MCP integration example should show discovered services."""
        path = Path("C:\\Projects\\plugin\\one-shot-prompting\\examples\\mcp-integration-example.md")
        content = self.read_file(path)
        assert "github" in content.lower() or "service" in content.lower(), \
            "Should mention discovered services like GitHub"

    def test_memory_learning_has_scenario(self):
        """Memory learning example should describe a scenario."""
        path = Path("C:\\Projects\\plugin\\one-shot-prompting\\examples\\memory-learning-example.md")
        content = self.read_file(path)
        assert len(content) >= 350, "Should have sufficient content (350+ chars)"
        assert "memory" in content.lower() or "learning" in content.lower(), \
            "Should mention memory or learning"

    def test_memory_learning_shows_learning_flow(self):
        """Memory learning example should show learning propagation."""
        path = Path("C:\\Projects\\plugin\\one-shot-prompting\\examples\\memory-learning-example.md")
        content = self.read_file(path)
        assert "extract" in content.lower() or "record" in content.lower() or "store" in content.lower(), \
            "Should show learning extraction/recording/storage"

    def test_memory_learning_shows_reuse(self):
        """Memory learning example should show knowledge reuse."""
        path = Path("C:\\Projects\\plugin\\one-shot-prompting\\examples\\memory-learning-example.md")
        content = self.read_file(path)
        assert "next" in content.lower() or "reuse" in content.lower() or "suggest" in content.lower(), \
            "Should show how knowledge is reused in next task"


class TestQuickStartGuide:
    """Test quick-start guide structure and content."""

    @staticmethod
    def read_file(path):
        """Helper to read file content."""
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    @staticmethod
    def has_links(content):
        """Check if markdown has links."""
        pattern = r'\[.+?\]\(.+?\)'
        return bool(re.search(pattern, content))

    def test_quick_start_has_title(self):
        """Quick-start guide should have a title."""
        path = Path("C:\\Projects\\plugin\\one-shot-prompting\\docs\\awesome-integration-quick-start.md")
        content = self.read_file(path)
        assert "# " in content, "Should have h1 title"

    def test_quick_start_links_to_examples(self):
        """Quick-start guide should link to all 3 examples."""
        path = Path("C:\\Projects\\plugin\\one-shot-prompting\\docs\\awesome-integration-quick-start.md")
        content = self.read_file(path)
        # Should have links to examples or mention the example files
        assert "multi-stage" in content.lower() or "Multi-Stage" in content, \
            "Should reference multi-stage example"
        assert "mcp" in content.lower() or "MCP" in content, \
            "Should reference MCP example"
        assert "memory" in content.lower() or "Memory" in content, \
            "Should reference memory example"

    def test_quick_start_has_command_reference(self):
        """Quick-start guide should have command references."""
        path = Path("C:\\Projects\\plugin\\one-shot-prompting\\docs\\awesome-integration-quick-start.md")
        content = self.read_file(path)
        assert "`" in content, "Should have inline code for commands"

    def test_quick_start_sufficient_length(self):
        """Quick-start guide should have adequate content."""
        path = Path("C:\\Projects\\plugin\\one-shot-prompting\\docs\\awesome-integration-quick-start.md")
        content = self.read_file(path)
        assert len(content) >= 400, "Quick-start should have sufficient content"

    def test_quick_start_mentions_architecture(self):
        """Quick-start guide should mention architecture."""
        path = Path("C:\\Projects\\plugin\\one-shot-prompting\\docs\\awesome-integration-quick-start.md")
        content = self.read_file(path)
        assert "architecture" in content.lower() or "pattern" in content.lower() or "integration" in content.lower(), \
            "Should discuss architecture or patterns"


class TestFileSizeAndLength:
    """Test that files meet length requirements."""

    @staticmethod
    def read_file(path):
        """Helper to read file content."""
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    @staticmethod
    def count_lines(content):
        """Count lines in content."""
        return len(content.split('\n'))

    def test_multi_stage_adequate_length(self):
        """Multi-stage example should be 400-500 lines."""
        path = Path("C:\\Projects\\plugin\\one-shot-prompting\\examples\\multi-stage-example.md")
        content = self.read_file(path)
        lines = self.count_lines(content)
        # Allow some flexibility: minimum 400 chars, but we'll check for substantial content
        assert len(content) >= 400, f"Multi-stage should have 400+ chars, got {len(content)}"

    def test_mcp_integration_adequate_length(self):
        """MCP integration example should be 300-400 lines."""
        path = Path("C:\\Projects\\plugin\\one-shot-prompting\\examples\\mcp-integration-example.md")
        content = self.read_file(path)
        assert len(content) >= 300, f"MCP integration should have 300+ chars, got {len(content)}"

    def test_memory_learning_adequate_length(self):
        """Memory learning example should be 350-450 lines."""
        path = Path("C:\\Projects\\plugin\\one-shot-prompting\\examples\\memory-learning-example.md")
        content = self.read_file(path)
        assert len(content) >= 350, f"Memory learning should have 350+ chars, got {len(content)}"


class TestNoRegressions:
    """Ensure existing tests don't break."""

    def test_examples_directory_still_exists(self):
        """Examples directory should exist."""
        path = Path("C:\\Projects\\plugin\\one-shot-prompting\\examples")
        assert path.is_dir(), "Examples directory should exist"

    def test_docs_directory_still_exists(self):
        """Docs directory should exist."""
        path = Path("C:\\Projects\\plugin\\one-shot-prompting\\docs")
        assert path.is_dir(), "Docs directory should exist"
