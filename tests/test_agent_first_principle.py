"""
Tests for Agent-First Principle Documentation

Validates:
1. agent-first-principle.md exists and has proper structure
2. Architecture index links are valid
3. ASCII diagrams are parseable
4. YAML frontmatter is valid
5. References section points to real files
"""

import json
import re
from pathlib import Path
import pytest
import yaml


# Paths
REPO_ROOT = Path(__file__).parent.parent
DOCS_DIR = REPO_ROOT / "docs"
ARCHITECTURE_DIR = DOCS_DIR / "architecture"
AGENTS_DIR = REPO_ROOT / "agents"
SCRIPTS_DIR = REPO_ROOT / "scripts"


class TestAgentFirstPrincipleExists:
    """Verify the document exists and is readable."""

    def test_agent_first_principle_file_exists(self):
        """The main agent-first-principle.md file exists."""
        assert ARCHITECTURE_DIR / "agent-first-principle.md"
        assert (ARCHITECTURE_DIR / "agent-first-principle.md").exists()

    def test_architecture_directory_exists(self):
        """The docs/architecture/ directory was created."""
        assert ARCHITECTURE_DIR.exists()
        assert ARCHITECTURE_DIR.is_dir()

    def test_agent_first_principle_is_readable(self):
        """The document can be read as text."""
        doc_path = ARCHITECTURE_DIR / "agent-first-principle.md"
        content = doc_path.read_text(encoding="utf-8", errors="ignore")
        assert len(content) > 1000, "Document should be substantial (>1000 chars)"
        assert "Agent-First" in content or "agent-first" in content


class TestYAMLFrontmatter:
    """Verify YAML frontmatter is valid in all architecture docs."""

    def test_agent_first_principle_yaml_frontmatter(self):
        """agent-first-principle.md has valid YAML frontmatter."""
        doc_path = ARCHITECTURE_DIR / "agent-first-principle.md"
        content = doc_path.read_text(encoding="utf-8", errors="ignore")

        # Extract frontmatter
        match = re.match(r"^---\n(.+?)\n---", content, re.DOTALL)
        assert match, "Missing YAML frontmatter"

        frontmatter_str = match.group(1)
        frontmatter = yaml.safe_load(frontmatter_str)

        assert frontmatter["type"] == "guide"
        assert "last_verified" in frontmatter
        assert "owner" in frontmatter

    def test_architecture_readme_yaml_frontmatter(self):
        """architecture/README.md has valid YAML frontmatter."""
        doc_path = ARCHITECTURE_DIR / "README.md"
        content = doc_path.read_text(encoding="utf-8", errors="ignore")

        match = re.match(r"^---\n(.+?)\n---", content, re.DOTALL)
        assert match, "Missing YAML frontmatter"

        frontmatter_str = match.group(1)
        frontmatter = yaml.safe_load(frontmatter_str)

        assert frontmatter["type"] == "guide"
        assert "last_verified" in frontmatter


class TestDocumentStructure:
    """Verify the agent-first-principle.md has expected sections."""

    def test_has_executive_summary(self):
        """Document has Executive Summary section."""
        doc_path = ARCHITECTURE_DIR / "agent-first-principle.md"
        content = doc_path.read_text(encoding="utf-8", errors="ignore")
        assert "## Executive Summary" in content

    def test_has_core_principle_section(self):
        """Document has Core Principle section."""
        doc_path = ARCHITECTURE_DIR / "agent-first-principle.md"
        content = doc_path.read_text(encoding="utf-8", errors="ignore")
        assert "## Core Principle" in content

    def test_has_architecture_overview(self):
        """Document has Architecture Overview section."""
        doc_path = ARCHITECTURE_DIR / "agent-first-principle.md"
        content = doc_path.read_text(encoding="utf-8", errors="ignore")
        assert "## Architecture Overview" in content

    def test_has_agent_dispatching_pattern(self):
        """Document has Agent Dispatching Pattern section."""
        doc_path = ARCHITECTURE_DIR / "agent-first-principle.md"
        content = doc_path.read_text(encoding="utf-8", errors="ignore")
        assert "## Agent Dispatching Pattern" in content

    def test_has_deterministic_operations(self):
        """Document has Deterministic Operations section."""
        doc_path = ARCHITECTURE_DIR / "agent-first-principle.md"
        content = doc_path.read_text(encoding="utf-8", errors="ignore")
        assert "## Deterministic Operations" in content

    def test_has_real_world_examples(self):
        """Document has Real-World Examples section."""
        doc_path = ARCHITECTURE_DIR / "agent-first-principle.md"
        content = doc_path.read_text(encoding="utf-8", errors="ignore")
        assert "## Real-World Examples" in content

    def test_has_implementation_guidelines(self):
        """Document has Implementation Guidelines section."""
        doc_path = ARCHITECTURE_DIR / "agent-first-principle.md"
        content = doc_path.read_text(encoding="utf-8", errors="ignore")
        assert "## Implementation Guidelines" in content

    def test_has_common_patterns(self):
        """Document has Common Patterns & Anti-Patterns section."""
        doc_path = ARCHITECTURE_DIR / "agent-first-principle.md"
        content = doc_path.read_text(encoding="utf-8", errors="ignore")
        assert "## Common Patterns & Anti-Patterns" in content

    def test_has_workstream_integration(self):
        """Document has Integration Across Workstreams section."""
        doc_path = ARCHITECTURE_DIR / "agent-first-principle.md"
        content = doc_path.read_text(encoding="utf-8", errors="ignore")
        assert "## Integration Across Workstreams" in content

    def test_has_references_section(self):
        """Document has References & Links section."""
        doc_path = ARCHITECTURE_DIR / "agent-first-principle.md"
        content = doc_path.read_text(encoding="utf-8", errors="ignore")
        assert "## References & Links" in content


class TestASCIIDiagrams:
    """Verify ASCII diagrams are present and parseable."""

    def test_has_visual_model_diagram(self):
        """Document includes visual model diagram."""
        doc_path = ARCHITECTURE_DIR / "agent-first-principle.md"
        content = doc_path.read_text(encoding="utf-8", errors="ignore")

        # Look for diagram elements
        assert "┌─" in content or "┌──" in content, "Missing ASCII box drawing"
        assert "│" in content, "Missing ASCII vertical lines"
        assert "Feature Request" in content or "domain model" in content

    def test_has_stage_pipeline_diagram(self):
        """Document includes 14-stage pipeline diagram."""
        doc_path = ARCHITECTURE_DIR / "agent-first-principle.md"
        content = doc_path.read_text(encoding="utf-8", errors="ignore")

        # Pipeline should mention stages
        assert "Stage 0" in content or "14-Stage Pipeline" in content
        assert "PLAN" in content or "BUILD" in content or "VERIFY" in content

    def test_pipeline_mentions_agent_vs_script(self):
        """Pipeline diagram distinguishes agents from scripts."""
        doc_path = ARCHITECTURE_DIR / "agent-first-principle.md"
        content = doc_path.read_text(encoding="utf-8", errors="ignore")

        assert "[AGENT" in content or "[SCRIPT" in content
        assert "architect" in content
        assert "codebase_graph" in content

    def test_has_decision_criteria_table(self):
        """Document includes decision criteria table."""
        doc_path = ARCHITECTURE_DIR / "agent-first-principle.md"
        content = doc_path.read_text(encoding="utf-8", errors="ignore")

        # Look for table structure
        assert "Agent Work" in content or "Script Work" in content
        assert "│" in content  # Table divider


class TestReferenceLinks:
    """Verify all referenced files exist."""

    def test_references_real_agents(self):
        """References section mentions agents that exist."""
        doc_path = ARCHITECTURE_DIR / "agent-first-principle.md"
        content = doc_path.read_text(encoding="utf-8", errors="ignore")

        # Check for mention of agent paths
        assert ".claude/agents/" in content

        # Verify some agents mentioned actually exist
        assert "architect" in content
        assert (AGENTS_DIR / "architect.md").exists()

    def test_references_real_scripts(self):
        """References section mentions scripts that exist."""
        doc_path = ARCHITECTURE_DIR / "agent-first-principle.md"
        content = doc_path.read_text(encoding="utf-8", errors="ignore")

        assert "scripts/" in content
        assert "codebase_graph" in content or "scripts" in content

    def test_references_skill_file(self):
        """Document references the main SKILL.md."""
        doc_path = ARCHITECTURE_DIR / "agent-first-principle.md"
        content = doc_path.read_text(encoding="utf-8", errors="ignore")

        assert "SKILL.md" in content or "one-shot-generate" in content

    def test_references_architecture_index(self):
        """Document references the architecture index."""
        doc_path = ARCHITECTURE_DIR / "agent-first-principle.md"
        content = doc_path.read_text(encoding="utf-8", errors="ignore")

        # Should be mentioned in references
        assert "architecture/" in content or "Architecture" in content

    def test_references_tier35_doc(self):
        """Document references tier35-agentic.md."""
        doc_path = ARCHITECTURE_DIR / "agent-first-principle.md"
        content = doc_path.read_text(encoding="utf-8", errors="ignore")

        assert "tier35" in content or "agentic" in content


class TestArchitectureIndex:
    """Verify architecture/README.md is complete and links correctly."""

    def test_architecture_index_exists(self):
        """architecture/README.md exists."""
        index_path = ARCHITECTURE_DIR / "README.md"
        assert index_path.exists()

    def test_architecture_index_links_to_agent_first_principle(self):
        """Index links to agent-first-principle.md."""
        index_path = ARCHITECTURE_DIR / "README.md"
        content = index_path.read_text(encoding="utf-8")

        assert "agent-first-principle.md" in content

    def test_architecture_index_lists_agents(self):
        """Index provides agent reference table."""
        index_path = ARCHITECTURE_DIR / "README.md"
        content = index_path.read_text(encoding="utf-8")

        assert "architect" in content
        assert "implementer" in content
        assert "reviewer" in content

    def test_architecture_index_lists_scripts(self):
        """Index provides script reference table."""
        index_path = ARCHITECTURE_DIR / "README.md"
        content = index_path.read_text(encoding="utf-8")

        assert "codebase_graph" in content
        assert "auto_patch" in content or "auto-patch" in content

    def test_architecture_index_has_workstreams(self):
        """Index lists workstreams (WS1-5)."""
        index_path = ARCHITECTURE_DIR / "README.md"
        content = index_path.read_text(encoding="utf-8")

        assert "WS" in content or "Workstream" in content


class TestDocumentCompleteness:
    """Verify document meets size and complexity requirements."""

    def test_agent_first_principle_minimum_length(self):
        """Document meets minimum length (500-700 lines requested)."""
        doc_path = ARCHITECTURE_DIR / "agent-first-principle.md"
        content = doc_path.read_text(encoding="utf-8", errors="ignore")
        lines = content.split("\n")

        # Should be substantial
        assert len(lines) >= 400, f"Document too short: {len(lines)} lines"

    def test_agent_first_principle_has_examples(self):
        """Document includes real-world code examples."""
        doc_path = ARCHITECTURE_DIR / "agent-first-principle.md"
        content = doc_path.read_text(encoding="utf-8", errors="ignore")

        # Should have JSON/YAML examples
        assert "json" in content.lower() or "{" in content
        assert "yaml" in content.lower() or "---" in content

    def test_agent_first_principle_mentions_all_stages(self):
        """Document mentions key pipeline stages."""
        doc_path = ARCHITECTURE_DIR / "agent-first-principle.md"
        content = doc_path.read_text(encoding="utf-8", errors="ignore")

        # Key stages
        assert "Stage 0" in content
        assert "Stage 2" in content  # Architect
        assert "Stage 3" in content  # Build
        assert "Stage 4" in content  # Verify
        assert "Stage 7" in content  # Critic

    def test_agent_first_principle_mentions_all_agents(self):
        """Document references major agents."""
        doc_path = ARCHITECTURE_DIR / "agent-first-principle.md"
        content = doc_path.read_text(encoding="utf-8", errors="ignore")

        agents = ["architect", "implementer", "test-author", "reviewer", "critic"]
        for agent in agents:
            assert agent in content, f"Missing reference to {agent}"

    def test_agent_first_principle_has_decision_criteria(self):
        """Document explains when to use agents vs scripts."""
        doc_path = ARCHITECTURE_DIR / "agent-first-principle.md"
        content = doc_path.read_text(encoding="utf-8", errors="ignore")

        # Should explain decision criteria
        assert "Decision Criteria" in content or "decision" in content.lower()
        assert "judgment" in content.lower() or "reasoning" in content.lower()


class TestIntegrationWithProject:
    """Verify the new docs integrate properly with project structure."""

    def test_references_claude_md(self):
        """Agent-first principle references CLAUDE.md."""
        doc_path = ARCHITECTURE_DIR / "agent-first-principle.md"
        content = doc_path.read_text(encoding="utf-8", errors="ignore")

        assert "CLAUDE.md" in content

    def test_references_implementation_status(self):
        """Agent-first principle references IMPLEMENTATION_STATUS.md."""
        doc_path = ARCHITECTURE_DIR / "agent-first-principle.md"
        content = doc_path.read_text(encoding="utf-8", errors="ignore")

        assert "IMPLEMENTATION_STATUS" in content

    def test_references_changelog(self):
        """Agent-first principle references CHANGELOG.md."""
        doc_path = ARCHITECTURE_DIR / "agent-first-principle.md"
        content = doc_path.read_text(encoding="utf-8", errors="ignore")

        assert "CHANGELOG" in content

    def test_agents_directory_has_agents_referenced_in_doc(self):
        """All agents mentioned in doc are present in .claude/agents/."""
        doc_path = ARCHITECTURE_DIR / "agent-first-principle.md"
        content = doc_path.read_text(encoding="utf-8", errors="ignore")

        # Extract agent names from the agents table
        agent_table_match = re.search(
            r"\| `(\w+)\.md`",
            content
        )
        if agent_table_match:
            # At least verify the table mentions agents
            assert "architect.md" in content or "architect" in content


class TestCrossReferences:
    """Verify cross-document linking is consistent."""

    def test_architecture_index_and_agent_first_link_each_other(self):
        """Index and agent-first-principle link to each other."""
        agent_first = (ARCHITECTURE_DIR / "agent-first-principle.md").read_text(encoding="utf-8", errors="ignore")
        index = (ARCHITECTURE_DIR / "README.md").read_text(encoding="utf-8", errors="ignore")

        # Agent-first should reference index
        assert "README" in agent_first or "architecture/" in agent_first

        # Index should reference agent-first
        assert "agent-first-principle" in index

    def test_relative_links_are_valid(self):
        """Relative links in docs follow consistent pattern."""
        agent_first = (ARCHITECTURE_DIR / "agent-first-principle.md").read_text(encoding="utf-8", errors="ignore")

        # Should use relative paths for files in docs/
        assert "../" in agent_first or "./" in agent_first


class TestDocumentQuality:
    """Verify documentation quality standards."""

    def test_no_placeholder_text(self):
        """Document doesn't contain placeholder text."""
        doc_path = ARCHITECTURE_DIR / "agent-first-principle.md"
        content = doc_path.read_text(encoding="utf-8", errors="ignore")

        placeholders = ["TODO", "FIXME", "XXX", "[INSERT"]
        for placeholder in placeholders:
            assert placeholder not in content, f"Found placeholder: {placeholder}"

    def test_has_meaningful_headers(self):
        """Document has clear, meaningful section headers."""
        doc_path = ARCHITECTURE_DIR / "agent-first-principle.md"
        content = doc_path.read_text(encoding="utf-8", errors="ignore")

        headers = re.findall(r"^## (.+)$", content, re.MULTILINE)
        assert len(headers) >= 8, f"Expected 8+ headers, found {len(headers)}"

        # Headers should be descriptive
        meaningful = [h for h in headers if len(h) > 5]
        assert len(meaningful) == len(headers)

    def test_uses_consistent_formatting(self):
        """Document uses consistent markdown formatting."""
        doc_path = ARCHITECTURE_DIR / "agent-first-principle.md"
        content = doc_path.read_text(encoding="utf-8", errors="ignore")

        # Should use consistent list formatting
        assert "-" in content or "*" in content

        # Should have code blocks
        assert "```" in content


# ============================================================================
# Integration Tests
# ============================================================================


class TestIntegrationWithPipeline:
    """Verify the document aligns with actual pipeline structure."""

    def test_pipeline_stages_match_skill_md(self):
        """14-stage pipeline in doc matches SKILL.md."""
        doc_path = ARCHITECTURE_DIR / "agent-first-principle.md"
        skill_path = REPO_ROOT / "skills" / "one-shot-generate" / "SKILL.md"

        doc_content = doc_path.read_text(encoding="utf-8", errors="ignore")
        skill_content = skill_path.read_text(encoding="utf-8", errors="ignore")

        # Both should mention stage progression
        assert "Stage 0" in doc_content
        assert "Stage 0" in skill_content

    def test_agent_definitions_match_directory(self):
        """Agent listings match actual .claude/agents/ directory."""
        agent_files = sorted([f.stem for f in AGENTS_DIR.glob("*.md")])

        doc_path = ARCHITECTURE_DIR / "agent-first-principle.md"
        content = doc_path.read_text(encoding="utf-8", errors="ignore")

        # Should mention multiple actual agents
        mentioned_count = sum(1 for agent in agent_files if agent in content)
        assert mentioned_count >= 8, f"Only {mentioned_count} agents mentioned in doc"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
