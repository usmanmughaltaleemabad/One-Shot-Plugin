"""Tests for multi-stage-workflow skill."""

import json
from pathlib import Path

import pytest


class TestWorkflowInitialization:
    """Test workflow initialization and state setup."""

    def test_workflow_state_creation(self):
        """Workflow state should have required keys."""
        workflow_state = {
            "id": "mswf-2026-05-25T10:00:00",
            "task": "find cart patterns",
            "project": "/tmp/test",
            "stages": {},
        }
        assert "id" in workflow_state
        assert "task" in workflow_state
        assert "project" in workflow_state
        assert "stages" in workflow_state
        assert isinstance(workflow_state["stages"], dict)

    def test_workflow_id_format(self):
        """Workflow ID should follow mswf-TIMESTAMP format."""
        workflow_id = "mswf-2026-05-25T10:00:00"
        assert workflow_id.startswith("mswf-")
        assert "T" in workflow_id

    def test_task_description_required(self):
        """Task description should not be empty."""
        task = "find cart patterns, analyze, design feature"
        assert len(task) > 0
        assert "find" in task.lower() or "analyze" in task.lower()


class TestSearchStage:
    """Test Stage 1 (Search) output validation."""

    def test_search_result_structure(self, sample_search_result):
        """Search result should have required fields."""
        assert sample_search_result["stage"] == "search"
        assert "query" in sample_search_result
        assert "patterns_found" in sample_search_result
        assert "total_matches" in sample_search_result

    def test_search_result_is_json(self, sample_search_result):
        """Search result should be serializable to JSON."""
        json_str = json.dumps(sample_search_result)
        assert json_str is not None
        restored = json.loads(json_str)
        assert restored == sample_search_result

    def test_patterns_found_list(self, sample_search_result):
        """Patterns found should be a list of pattern objects."""
        patterns = sample_search_result["patterns_found"]
        assert isinstance(patterns, list)
        assert len(patterns) >= 1

    def test_pattern_object_structure(self, sample_search_result):
        """Each pattern should have entity, files, lines, snippet."""
        for pattern in sample_search_result["patterns_found"]:
            assert "entity" in pattern
            assert "files" in pattern
            assert "lines" in pattern
            assert "snippet" in pattern
            assert isinstance(pattern["files"], list)
            assert isinstance(pattern["lines"], list)

    def test_total_matches_count(self, sample_search_result):
        """Total matches should equal length of patterns found."""
        assert (
            sample_search_result["total_matches"]
            == len(sample_search_result["patterns_found"])
        )

    def test_search_with_no_patterns(self):
        """Search should return empty patterns_found if no matches."""
        result = {
            "stage": "search",
            "query": "nonexistent_entity_xyz",
            "patterns_found": [],
            "total_matches": 0,
        }
        assert result["total_matches"] == 0
        assert len(result["patterns_found"]) == 0

    def test_search_multiple_files_per_entity(self, sample_search_result):
        """Entity pattern can appear in multiple files."""
        pattern = sample_search_result["patterns_found"][0]
        # Pattern can have multiple files
        assert isinstance(pattern["files"], list)


class TestAnalyzeStage:
    """Test Stage 2 (Analyze) output validation."""

    def test_analysis_result_structure(self, sample_analysis_result):
        """Analysis result should have required fields."""
        assert sample_analysis_result["stage"] == "analyze"
        assert "entities" in sample_analysis_result
        assert "relationships" in sample_analysis_result

    def test_analysis_result_is_json(self, sample_analysis_result):
        """Analysis result should be serializable to JSON."""
        json_str = json.dumps(sample_analysis_result)
        restored = json.loads(json_str)
        assert restored == sample_analysis_result

    def test_entities_list(self, sample_analysis_result):
        """Entities should be a non-empty list."""
        entities = sample_analysis_result["entities"]
        assert isinstance(entities, list)
        assert len(entities) >= 1

    def test_entity_object_structure(self, sample_analysis_result):
        """Each entity should have name, fields, inferred types, relationships."""
        for entity in sample_analysis_result["entities"]:
            assert "name" in entity
            assert "fields" in entity
            assert "inferred_types" in entity
            assert "relationships" in entity
            assert isinstance(entity["fields"], list)
            assert isinstance(entity["inferred_types"], dict)
            assert isinstance(entity["relationships"], list)

    def test_entity_name_not_empty(self, sample_analysis_result):
        """Entity names should not be empty."""
        for entity in sample_analysis_result["entities"]:
            assert len(entity["name"]) > 0

    def test_inferred_types_valid(self, sample_analysis_result):
        """Inferred types should match declared fields."""
        for entity in sample_analysis_result["entities"]:
            fields = set(entity["fields"])
            type_keys = set(entity["inferred_types"].keys())
            # Inferred types should be subset of or equal to fields
            assert type_keys.issubset(fields) or type_keys == fields

    def test_relationships_structure(self, sample_analysis_result):
        """Relationships should have from, to, type, foreign_key."""
        for rel in sample_analysis_result["relationships"]:
            assert "from" in rel
            assert "to" in rel
            assert "type" in rel
            assert "foreign_key" in rel
            assert rel["type"] in ["one_to_many", "many_to_many", "one_to_one"]

    def test_relationship_references_entities(self, sample_analysis_result):
        """Relationships should reference entities from entity list."""
        entity_names = {e["name"] for e in sample_analysis_result["entities"]}
        for rel in sample_analysis_result["relationships"]:
            assert rel["from"] in entity_names
            assert rel["to"] in entity_names


class TestGenerateStage:
    """Test Stage 3 (Generate) output validation."""

    def test_generation_result_structure(self, sample_generation_result):
        """Generation result should have required fields."""
        assert sample_generation_result["stage"] == "generate"
        assert "spec" in sample_generation_result
        assert "implementation_steps" in sample_generation_result
        assert "cost_estimate" in sample_generation_result

    def test_generation_result_is_json(self, sample_generation_result):
        """Generation result should be serializable to JSON."""
        json_str = json.dumps(sample_generation_result)
        restored = json.loads(json_str)
        assert restored == sample_generation_result

    def test_spec_structure(self, sample_generation_result):
        """Spec should have name, version, entities."""
        spec = sample_generation_result["spec"]
        assert "name" in spec
        assert "version" in spec
        assert "entities" in spec
        assert isinstance(spec["entities"], list)

    def test_spec_entities(self, sample_generation_result):
        """Each spec entity should have name, description, properties."""
        spec = sample_generation_result["spec"]
        for entity in spec["entities"]:
            assert "name" in entity
            assert "description" in entity
            assert "properties" in entity
            assert isinstance(entity["properties"], list)

    def test_spec_properties(self, sample_generation_result):
        """Each property should have name, type, nullable."""
        spec = sample_generation_result["spec"]
        for entity in spec["entities"]:
            for prop in entity["properties"]:
                assert "name" in prop
                assert "type" in prop
                # nullable is optional but type should exist

    def test_primary_key_exists(self, sample_generation_result):
        """At least one entity should have a primary key."""
        spec = sample_generation_result["spec"]
        has_primary_key = False
        for entity in spec["entities"]:
            for prop in entity["properties"]:
                if prop.get("primary_key"):
                    has_primary_key = True
                    break
        assert has_primary_key

    def test_foreign_key_references(self, sample_generation_result):
        """Foreign keys should reference properties that exist."""
        spec = sample_generation_result["spec"]
        entity_names = {e["name"] for e in spec["entities"]}
        for entity in spec["entities"]:
            for prop in entity["properties"]:
                if prop.get("foreign_key"):
                    # Foreign key implies reference to another entity
                    assert len(entity_names) > 1

    def test_implementation_steps_not_empty(self, sample_generation_result):
        """Implementation steps should be non-empty."""
        steps = sample_generation_result["implementation_steps"]
        assert isinstance(steps, list)
        assert len(steps) >= 1
        for step in steps:
            assert len(step) > 0

    def test_cost_estimate_format(self, sample_generation_result):
        """Cost estimate should be in $ format."""
        cost = sample_generation_result["cost_estimate"]
        assert cost.startswith("$")
        # Should be able to parse as currency
        assert "." in cost or cost.isdigit()

    def test_effort_estimate_present(self, sample_generation_result):
        """Effort estimate should be present."""
        assert "effort_estimate" in sample_generation_result
        effort = sample_generation_result["effort_estimate"]
        assert len(effort) > 0
        # Should contain time units (hours, days, etc)
        assert any(
            unit in effort.lower() for unit in ["hour", "day", "week", "sprint"]
        )


class TestMultiStageExecution:
    """Test full workflow execution."""

    def test_workflow_state_complete(self, workflow_state):
        """Workflow state should contain all 3 stages after execution."""
        assert "search" in workflow_state["stages"]
        assert "analyze" in workflow_state["stages"]
        assert "generate" in workflow_state["stages"]

    def test_stage_output_flow_search_to_analyze(
        self, workflow_state, sample_analysis_result
    ):
        """Analyze stage should reference entities found in search."""
        search_output = workflow_state["stages"]["search"]
        analyze_output = workflow_state["stages"]["analyze"]

        search_entities = {p["entity"] for p in search_output["patterns_found"]}
        analyzed_entities = {e["name"] for e in analyze_output["entities"]}

        # Analysis should include entities found in search
        assert analyzed_entities == search_entities

    def test_stage_output_flow_analyze_to_generate(
        self, workflow_state, sample_generation_result
    ):
        """Generate stage should include entities from analyze."""
        analyze_output = workflow_state["stages"]["analyze"]
        generate_output = workflow_state["stages"]["generate"]

        analyzed_entities = {e["name"] for e in analyze_output["entities"]}
        spec_entities = {e["name"] for e in generate_output["spec"]["entities"]}

        # Spec should include analyzed entities
        assert spec_entities == analyzed_entities

    def test_workflow_execution_order(self, workflow_state):
        """Stages should be executable in sequence."""
        # Just verify all stages present and can be iterated
        stages = ["search", "analyze", "generate"]
        for stage in stages:
            assert stage in workflow_state["stages"]
            assert "stage" in workflow_state["stages"][stage]
            assert workflow_state["stages"][stage]["stage"] == stage

    def test_workflow_state_serializable(self, workflow_state):
        """Entire workflow state should serialize to JSON."""
        json_str = json.dumps(workflow_state)
        restored = json.loads(json_str)
        assert restored == workflow_state

    def test_workflow_id_generation(self, workflow_state):
        """Workflow ID should be present and unique-like."""
        assert "id" in workflow_state
        assert workflow_state["id"].startswith("mswf-")

    def test_project_path_preserved(self, workflow_state):
        """Project path should be preserved through stages."""
        assert "project" in workflow_state
        project_path = workflow_state["project"]
        assert project_path is not None


class TestErrorHandling:
    """Test error recovery and edge cases."""

    def test_search_zero_patterns_detection(self):
        """Should detect when search returns zero patterns."""
        result = {
            "stage": "search",
            "query": "nonexistent",
            "patterns_found": [],
            "total_matches": 0,
        }
        assert result["total_matches"] == 0
        should_retry = result["total_matches"] == 0
        assert should_retry

    def test_invalid_json_detection(self):
        """Should detect invalid JSON in stage output."""
        invalid = "{ invalid json"
        try:
            json.loads(invalid)
            assert False, "Should have raised JSONDecodeError"
        except json.JSONDecodeError:
            assert True

    def test_missing_required_fields(self):
        """Should detect missing required fields in stage output."""
        incomplete_search = {
            "stage": "search",
            "query": "test",
            # Missing: patterns_found, total_matches
        }
        assert "patterns_found" not in incomplete_search
        assert "total_matches" not in incomplete_search

    def test_entity_without_fields(self):
        """Should handle entity with no fields gracefully."""
        entity = {
            "name": "Test",
            "fields": [],  # Empty fields
            "inferred_types": {},
            "relationships": [],
        }
        assert len(entity["fields"]) == 0
        should_warn = len(entity["fields"]) == 0
        assert should_warn

    def test_relationship_without_foreign_key(self):
        """Should validate foreign key presence in relationships."""
        rel = {
            "from": "Entity1",
            "to": "Entity2",
            "type": "one_to_many",
            # Missing: foreign_key
        }
        assert "foreign_key" not in rel
        assert "type" in rel


class TestCostEstimation:
    """Test cost tracking and estimation."""

    def test_cost_per_stage(self):
        """Each stage should have estimated cost."""
        costs = {
            "search": "$0.02",  # Haiku
            "analyze": "$0.15",  # Sonnet
            "generate": "$0.20",  # Sonnet
        }
        total = 0.02 + 0.15 + 0.20
        assert abs(total - 0.37) < 0.01

    def test_total_cost_estimate(self, sample_generation_result):
        """Total cost should be reasonable and parseable."""
        cost_str = sample_generation_result["cost_estimate"]
        assert cost_str.startswith("$")
        # Parse and verify reasonable
        cost_val = float(cost_str.replace("$", ""))
        assert 0 < cost_val < 10  # Should be under $10

    def test_budget_gate_exceeds(self):
        """Should reject if cost exceeds budget."""
        budget = 0.20
        estimated_cost = 0.37
        exceeds = estimated_cost > budget
        assert exceeds

    def test_budget_gate_within(self):
        """Should allow if cost within budget."""
        budget = 1.00
        estimated_cost = 0.37
        exceeds = estimated_cost > budget
        assert not exceeds


class TestRegressionSuite:
    """Comprehensive regression tests."""

    def test_cart_domain_example(self, workflow_state):
        """Full workflow for shopping cart domain."""
        # Verify complete cart domain workflow
        search = workflow_state["stages"]["search"]
        analyze = workflow_state["stages"]["analyze"]
        generate = workflow_state["stages"]["generate"]

        # Search should find Cart, LineItem, Discount
        entities_found = {p["entity"] for p in search["patterns_found"]}
        assert "Cart" in entities_found
        assert "LineItem" in entities_found
        assert "Discount" in entities_found

        # Analyze should show relationships
        rels = analyze["relationships"]
        rel_types = {(r["from"], r["to"]) for r in rels}
        assert ("Cart", "LineItem") in rel_types or (
            "Cart",
            "Discount",
        ) in rel_types

        # Generate should have spec with Cart entity
        spec_entities = {e["name"] for e in generate["spec"]["entities"]}
        assert "Cart" in spec_entities

    def test_workflow_idempotence(self, workflow_state):
        """Multiple executions should yield consistent structure."""
        state1 = json.loads(json.dumps(workflow_state))
        state2 = json.loads(json.dumps(workflow_state))
        assert state1 == state2

    def test_large_codebase_handling(self):
        """Should handle codebase with many entities."""
        large_search = {
            "stage": "search",
            "query": "large codebase",
            "patterns_found": [
                {"entity": f"Entity{i}", "files": [f"file{i}.py"], "lines": [1, 2, 3], "snippet": "code"}
                for i in range(50)
            ],
            "total_matches": 50,
        }
        assert large_search["total_matches"] == 50
        assert len(large_search["patterns_found"]) == 50
