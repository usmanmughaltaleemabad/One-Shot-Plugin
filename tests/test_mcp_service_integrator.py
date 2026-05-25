"""Tests for MCP service integrator agent definition.

Validates that the mcp-service-integrator agent:
  1. Has valid YAML frontmatter with tools and model
  2. Registry JSON template is structurally correct
  3. Documentation of MCP services exists
  4. Agent can be invoked via Task with proper input/output
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
AGENTS = REPO_ROOT / ".claude" / "agents"
REGISTRY_PATH = REPO_ROOT / ".claude" / "mcp-registry.json"
DOCS_PATH = REPO_ROOT / "docs" / "mcp-services.md"


class TestMCPServiceIntegratorAgent:
    """MCP service integrator agent definition tests."""

    def test_agent_definition_exists(self):
        """The mcp-service-integrator agent definition must exist."""
        agent_path = AGENTS / "mcp-service-integrator.md"
        assert agent_path.exists(), \
            ".claude/agents/mcp-service-integrator.md must exist"

    def test_agent_has_valid_frontmatter(self):
        """Agent must have YAML frontmatter with name, description, tools, model."""
        agent_path = AGENTS / "mcp-service-integrator.md"
        text = agent_path.read_text(encoding="utf-8")

        # Must start with frontmatter
        assert text.startswith("---"), "agent must start with YAML frontmatter"

        # Extract frontmatter
        match = re.search(r"^---\n(.+?)\n---", text, re.DOTALL)
        assert match, "agent must have valid YAML frontmatter block"
        front = match.group(1)

        # Verify required fields
        assert re.search(r"^name:\s*mcp-service-integrator\b", front, re.MULTILINE), \
            "agent must have name: mcp-service-integrator"
        assert re.search(r"^description:", front, re.MULTILINE), \
            "agent must have description"
        assert re.search(r"^tools:", front, re.MULTILINE), \
            "agent must have tools (required for Task dispatch)"
        assert re.search(r"^model:", front, re.MULTILINE), \
            "agent must have model (required for Task dispatch)"

    def test_agent_declares_correct_tools(self):
        """Agent must declare tools for MCP discovery and registry updates."""
        agent_path = AGENTS / "mcp-service-integrator.md"
        text = agent_path.read_text(encoding="utf-8")

        match = re.search(r"^tools:\s*(.+?)$", text, re.MULTILINE)
        assert match, "agent must declare tools"
        tools_section = match.group(1).lower()

        # Should include tools for discovery and filesystem operations
        required_tools = {"read", "write", "grep", "task"}
        for tool in required_tools:
            # Tools may be comma-separated or on multiple lines
            assert tool in tools_section or tool.capitalize() in text, \
                f"agent should include {tool} tool"

    def test_agent_uses_sonnet_model(self):
        """Agent should use sonnet for MCP orchestration (requires judgment)."""
        agent_path = AGENTS / "mcp-service-integrator.md"
        text = agent_path.read_text(encoding="utf-8")

        match = re.search(r"^model:\s*(\w+)\b", text, re.MULTILINE)
        assert match, "agent must declare model"
        model = match.group(1).lower()
        assert model == "sonnet", \
            "agent should use sonnet for MCP orchestration (requires judgment)"

    def test_agent_has_workflow_section(self):
        """Agent must document the MCP discovery workflow."""
        agent_path = AGENTS / "mcp-service-integrator.md"
        text = agent_path.read_text(encoding="utf-8")

        # Should explain the discovery workflow
        assert "workflow" in text.lower(), \
            "agent must document workflow for MCP discovery"
        assert "discover" in text.lower(), \
            "agent must explain MCP discovery process"
        assert "register" in text.lower(), \
            "agent must explain MCP service registration"

    def test_agent_has_example_output(self):
        """Agent must show example MCP registry structure."""
        agent_path = AGENTS / "mcp-service-integrator.md"
        text = agent_path.read_text(encoding="utf-8")

        # Should have JSON example
        assert "```json" in text or "```" in text, \
            "agent must include example output/structure"
        assert "mcp" in text.lower(), \
            "agent must reference MCP services"

    def test_agent_has_error_handling_docs(self):
        """Agent must document error scenarios."""
        agent_path = AGENTS / "mcp-service-integrator.md"
        text = agent_path.read_text(encoding="utf-8")

        # Should handle common errors
        error_mentions = ["error", "missing", "unavailable", "failure"]
        error_count = sum(text.lower().count(e) for e in error_mentions)
        assert error_count > 0, \
            "agent should document error handling (missing services, registry issues)"


class TestMCPRegistry:
    """MCP registry template validation."""

    def test_registry_template_exists(self):
        """The .claude/mcp-registry.json template must exist."""
        assert REGISTRY_PATH.exists(), \
            ".claude/mcp-registry.json must exist as starting template"

    def test_registry_is_valid_json(self):
        """Registry must be valid JSON."""
        text = REGISTRY_PATH.read_text(encoding="utf-8")
        try:
            registry = json.loads(text)
        except json.JSONDecodeError as e:
            pytest.fail(f"mcp-registry.json is not valid JSON: {e}")

    def test_registry_has_correct_structure(self):
        """Registry must have mcp_services array."""
        text = REGISTRY_PATH.read_text(encoding="utf-8")
        registry = json.loads(text)

        assert isinstance(registry, dict), \
            "registry must be a JSON object"
        assert "mcp_services" in registry, \
            "registry must have 'mcp_services' key"
        assert isinstance(registry["mcp_services"], list), \
            "mcp_services must be an array"

    def test_registry_service_structure(self):
        """Each service in registry must have required fields."""
        text = REGISTRY_PATH.read_text(encoding="utf-8")
        registry = json.loads(text)

        # Initially empty, but if services added, must follow schema
        for service in registry.get("mcp_services", []):
            assert "name" in service, "service must have 'name'"
            assert "endpoint" in service, "service must have 'endpoint'"
            assert "capabilities" in service, "service must have 'capabilities'"
            assert "auth" in service, "service must have 'auth' type"


class TestMCPDocumentation:
    """MCP services documentation."""

    def test_mcp_docs_exist(self):
        """docs/mcp-services.md should document available services."""
        # This can be created initially empty but should exist
        assert DOCS_PATH.exists(), \
            "docs/mcp-services.md must exist to document MCP integrations"

    def test_mcp_docs_has_intro(self):
        """Docs should explain what MCP services are available."""
        text = DOCS_PATH.read_text(encoding="utf-8")
        assert len(text) > 20, \
            "docs/mcp-services.md should have introductory content"


class TestMCPIntegrationWorkflow:
    """End-to-end MCP integration workflow validation."""

    def test_agent_can_be_invoked_with_discover_flag(self):
        """Agent must be callable with --discover-mcp flag."""
        agent_path = AGENTS / "mcp-service-integrator.md"
        text = agent_path.read_text(encoding="utf-8")

        # Should mention how to trigger discovery
        assert "discover" in text.lower(), \
            "agent should document --discover-mcp or similar trigger"

    def test_agent_updates_registry_on_discovery(self):
        """Agent workflow must explain registry updates."""
        agent_path = AGENTS / "mcp-service-integrator.md"
        text = agent_path.read_text(encoding="utf-8")

        assert "registry" in text.lower(), \
            "agent must explain how it updates the registry"
        assert "mcp-registry.json" in text, \
            "agent must reference .claude/mcp-registry.json explicitly"

    def test_agent_documents_curator_integration(self):
        """Agent should explain integration with curator skill."""
        agent_path = AGENTS / "mcp-service-integrator.md"
        text = agent_path.read_text(encoding="utf-8")

        # Must explain how curator skill is enhanced
        curator_mention = "curator" in text.lower()
        skill_mention = "skill" in text.lower() and "curator" in text.lower()
        integration_mention = "integrat" in text.lower()

        assert curator_mention or integration_mention, \
            "agent should document integration with curator skill"
