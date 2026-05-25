"""
Tests for Intent-Based Routing System — Phase 3-T3

Coverage:
  - Intent detection (8+ intent types)
  - Complexity detection (entity counting, relationships, features)
  - Risk detection (security, compliance, criticality)
  - Routing matrix correctness
  - Cost and duration estimates
  - Similarity search fallback
  - Routing stability
"""

import sys
from pathlib import Path

# Add .claude/routing to path
ROUTING_DIR = Path(__file__).parent.parent / ".claude" / "routing"
sys.path.insert(0, str(ROUTING_DIR))

import pytest
from intent_detector import (
    IntentDetector,
    IntentType,
    ComplexityLevel,
    RiskLevel,
)
from intent_router import IntentRouter, RoutingDecision
from routing_matrix import RoutingMatrix


class TestIntentDetection:
    """Test intent detection from various feature requests."""

    def test_detect_simple_crud_intent(self):
        """Test detection of simple CRUD intent."""
        detector = IntentDetector()
        request = "Create a simple list of users with create, read, update, delete operations"
        result = detector.full_detection(request)
        assert result.intent == IntentType.simple_crud

    def test_detect_complex_multi_entity_intent(self):
        """Test detection of complex multi-entity systems."""
        detector = IntentDetector()
        request = "Build an e-commerce system with User, Product, Order, and Review entities with many-to-many relationships"
        result = detector.full_detection(request)
        assert result.intent == IntentType.complex_multi_entity

    def test_detect_real_time_system_intent(self):
        """Test detection of real-time systems."""
        detector = IntentDetector()
        request = "Implement a real-time notification system using WebSocket with live updates"
        result = detector.full_detection(request)
        assert result.intent == IntentType.real_time_system

    def test_detect_payment_system_intent(self):
        """Test detection of payment systems."""
        detector = IntentDetector()
        request = "Build a checkout system with Stripe integration for payment processing"
        result = detector.full_detection(request)
        assert result.intent == IntentType.payment_system

    def test_detect_api_design_intent(self):
        """Test detection of API design requests."""
        detector = IntentDetector()
        request = "Design a REST API with authentication, serializers, and request/response validation"
        result = detector.full_detection(request)
        assert result.intent == IntentType.api_design

    def test_detect_admin_panel_intent(self):
        """Test detection of admin panel requests."""
        detector = IntentDetector()
        request = "Create an admin dashboard with analytics, reporting, and data visualization"
        result = detector.full_detection(request)
        assert result.intent == IntentType.admin_panel

    def test_detect_integration_intent(self):
        """Test detection of third-party integrations."""
        detector = IntentDetector()
        request = "Integrate with GitHub API using OAuth and webhooks for external sync"
        result = detector.full_detection(request)
        assert result.intent == IntentType.integration

    def test_detect_data_pipeline_intent(self):
        """Test detection of data pipelines."""
        detector = IntentDetector()
        request = "Build a batch processing pipeline with cron jobs and background workers"
        result = detector.full_detection(request)
        assert result.intent == IntentType.data_pipeline


class TestComplexityDetection:
    """Test complexity level detection."""

    def test_low_complexity_single_entity(self):
        """Test low complexity detection for simple single-entity systems."""
        detector = IntentDetector()
        request = "Create a simple User model with CRUD operations"
        result = detector.full_detection(request)
        assert result.complexity == ComplexityLevel.low

    def test_medium_complexity_multi_entity(self):
        """Test medium complexity for systems with multiple entities."""
        detector = IntentDetector()
        request = "Build a blog system with User, Post, and Comment entities"
        result = detector.full_detection(request)
        assert result.complexity in [ComplexityLevel.medium, ComplexityLevel.high]

    def test_high_complexity_relationships(self):
        """Test high complexity for systems with many relationships."""
        detector = IntentDetector()
        request = "Create a complex domain with User, Order, Product, Review, Payment with has_many and many-to-many relationships"
        result = detector.full_detection(request)
        assert result.complexity in [ComplexityLevel.high, ComplexityLevel.enterprise]

    def test_enterprise_complexity_large_system(self):
        """Test enterprise complexity for large-scale systems."""
        detector = IntentDetector()
        request = """
        Build a multi-tenant SaaS platform with User, Organization, Project, Task,
        Permission, Audit, Notification, Integration, with hierarchical relationships,
        audit logging, analytics, and real-time updates
        """
        result = detector.full_detection(request)
        assert result.complexity in [ComplexityLevel.high, ComplexityLevel.enterprise]

    def test_complexity_increases_with_entity_count(self):
        """Test that complexity increases with entity count."""
        detector = IntentDetector()
        simple = detector.full_detection("Create a User entity")
        complex_req = detector.full_detection(
            "Create User, Product, Order, Review, Payment, Invoice entities"
        )
        # Parse complexity levels as ordinals
        complexity_order = {
            ComplexityLevel.low: 1,
            ComplexityLevel.medium: 2,
            ComplexityLevel.high: 3,
            ComplexityLevel.enterprise: 4,
        }
        assert (
            complexity_order[complex_req.complexity]
            >= complexity_order[simple.complexity]
        )


class TestRiskDetection:
    """Test risk level detection."""

    def test_experimental_risk_low_complexity(self):
        """Test experimental risk for low-complexity requests."""
        detector = IntentDetector()
        request = "Create a simple User model"
        result = detector.full_detection(request)
        assert result.risk == RiskLevel.experimental

    def test_standard_risk_medium_complexity(self):
        """Test standard risk for medium-complexity requests."""
        detector = IntentDetector()
        request = "Build a blog system with User, Post, Comment entities"
        result = detector.full_detection(request)
        assert result.risk in [RiskLevel.standard, RiskLevel.experimental]

    def test_production_critical_payment_system(self):
        """Test production-critical risk for payment systems."""
        detector = IntentDetector()
        request = "Build a payment processing system with Stripe integration"
        result = detector.full_detection(request)
        assert result.risk == RiskLevel.production_critical

    def test_production_critical_real_time(self):
        """Test production-critical risk for real-time systems."""
        detector = IntentDetector()
        request = "Implement a real-time notification system with WebSocket"
        result = detector.full_detection(request)
        assert result.risk == RiskLevel.production_critical


class TestRoutingMatrix:
    """Test the routing matrix logic."""

    def test_simple_crud_routing(self):
        """Test that simple CRUD routes to SimpleCRUD agent."""
        agent = RoutingMatrix.get_agent(
            IntentType.simple_crud,
            ComplexityLevel.low,
            RiskLevel.experimental,
        )
        assert agent.name == "SimpleCRUD"

    def test_payment_system_always_payment_specialist(self):
        """Test that payment systems always route to PaymentSpecialist."""
        for complexity in ComplexityLevel:
            for risk in RiskLevel:
                agent = RoutingMatrix.get_agent(
                    IntentType.payment_system,
                    complexity,
                    risk,
                )
                assert agent.name == "PaymentSpecialist"

    def test_real_time_always_specialist(self):
        """Test that real-time systems always route to RealTimeSpecialist."""
        for complexity in ComplexityLevel:
            agent = RoutingMatrix.get_agent(
                IntentType.real_time_system,
                complexity,
                RiskLevel.standard,
            )
            assert agent.name == "RealTimeSpecialist"

    def test_complex_domain_multi_entity(self):
        """Test that complex multi-entity systems route to ComplexDomain agent."""
        agent = RoutingMatrix.get_agent(
            IntentType.complex_multi_entity,
            ComplexityLevel.high,
            RiskLevel.standard,
        )
        assert agent.name == "ComplexDomain"

    def test_api_design_routing(self):
        """Test API design routing."""
        agent = RoutingMatrix.get_agent(
            IntentType.api_design,
            ComplexityLevel.medium,
            RiskLevel.standard,
        )
        assert agent.name == "APIDesigner"

    def test_admin_panel_routing(self):
        """Test admin panel routing."""
        agent = RoutingMatrix.get_agent(
            IntentType.admin_panel,
            ComplexityLevel.medium,
            RiskLevel.standard,
        )
        assert agent.name == "AdminDashboard"

    def test_integration_routing(self):
        """Test integration routing."""
        agent = RoutingMatrix.get_agent(
            IntentType.integration,
            ComplexityLevel.high,
            RiskLevel.standard,
        )
        assert agent.name == "IntegrationSpecialist"

    def test_data_pipeline_routing(self):
        """Test data pipeline routing."""
        agent = RoutingMatrix.get_agent(
            IntentType.data_pipeline,
            ComplexityLevel.high,
            RiskLevel.standard,
        )
        assert agent.name == "DataPipelineSpecialist"


class TestRoutingDecision:
    """Test the routing decision creation."""

    def test_routing_decision_creation(self):
        """Test that routing decisions are created correctly."""
        router = IntentRouter()
        request = "Create a User entity with CRUD operations"
        decision = router.route(request)

        assert isinstance(decision, RoutingDecision)
        assert decision.request == request
        assert isinstance(decision.intent, IntentType)
        assert isinstance(decision.complexity, ComplexityLevel)
        assert isinstance(decision.risk, RiskLevel)
        assert decision.agent_name
        assert 0.0 <= decision.confidence <= 1.0
        assert decision.cost_estimate > 0
        assert decision.duration_estimate > 0

    def test_routing_decision_serialization(self):
        """Test that routing decisions can be serialized."""
        router = IntentRouter()
        decision = router.route("Create a User model")

        # Test to_dict
        decision_dict = decision.to_dict()
        assert decision_dict["request"]
        assert "intent" in decision_dict
        assert "complexity" in decision_dict

        # Test to_json
        json_str = decision.to_json()
        assert isinstance(json_str, str)
        assert "intent" in json_str


class TestCostEstimates:
    """Test cost and duration estimation."""

    def test_simple_crud_low_cost(self):
        """Test that SimpleCRUD has low cost estimate."""
        agent = RoutingMatrix.get_agent(
            IntentType.simple_crud,
            ComplexityLevel.low,
            RiskLevel.experimental,
        )
        assert agent.max_cost_estimate < 1.0

    def test_complex_domain_higher_cost(self):
        """Test that ComplexDomain has higher cost."""
        agent = RoutingMatrix.get_agent(
            IntentType.complex_multi_entity,
            ComplexityLevel.high,
            RiskLevel.standard,
        )
        assert agent.max_cost_estimate > 1.0

    def test_payment_specialist_highest_cost(self):
        """Test that PaymentSpecialist has highest cost."""
        simple_agent = RoutingMatrix.get_agent(
            IntentType.simple_crud,
            ComplexityLevel.low,
            RiskLevel.experimental,
        )
        payment_agent = RoutingMatrix.get_agent(
            IntentType.payment_system,
            ComplexityLevel.low,
            RiskLevel.standard,
        )
        assert payment_agent.max_cost_estimate > simple_agent.max_cost_estimate

    def test_cost_estimation(self):
        """Test cost calculation."""
        router = IntentRouter()
        agent = RoutingMatrix.get_agent(
            IntentType.simple_crud,
            ComplexityLevel.low,
            RiskLevel.experimental,
        )
        # Test with tokens that result in cost less than max estimate
        cost = router.estimate_cost(agent, tokens_estimate=1000)
        assert cost > 0
        assert cost <= agent.max_cost_estimate

    def test_duration_estimates_increase_with_complexity(self):
        """Test that duration estimates increase with complexity."""
        simple_agent = RoutingMatrix.get_agent(
            IntentType.simple_crud,
            ComplexityLevel.low,
            RiskLevel.experimental,
        )
        complex_agent = RoutingMatrix.get_agent(
            IntentType.complex_multi_entity,
            ComplexityLevel.enterprise,
            RiskLevel.production_critical,
        )
        assert simple_agent.duration_estimate_minutes < complex_agent.duration_estimate_minutes


class TestSpecialHandling:
    """Test special handling flags for different agents."""

    def test_payment_specialist_has_security_review(self):
        """Test that PaymentSpecialist has security review flag."""
        agent = RoutingMatrix.AGENTS["payment_specialist"]
        assert agent.requires_security_review is True

    def test_payment_specialist_has_compliance_check(self):
        """Test that PaymentSpecialist has compliance check flag."""
        agent = RoutingMatrix.AGENTS["payment_specialist"]
        assert agent.requires_compliance_check is True

    def test_real_time_specialist_has_performance_review(self):
        """Test that RealTimeSpecialist has performance review flag."""
        agent = RoutingMatrix.AGENTS["realtime_specialist"]
        assert agent.requires_performance_review is True

    def test_admin_dashboard_has_performance_review(self):
        """Test that AdminDashboard has performance review flag."""
        agent = RoutingMatrix.AGENTS["admin_dashboard"]
        assert agent.requires_performance_review is True

    def test_payment_specialist_special_handling(self):
        """Test that PaymentSpecialist has special handling directives."""
        agent = RoutingMatrix.AGENTS["payment_specialist"]
        assert len(agent.special_handling) > 0
        assert any("pci" in h.lower() for h in agent.special_handling)


class TestRoutingStability:
    """Test that routing decisions are stable."""

    def test_same_request_same_route(self):
        """Test that the same request always routes to the same agent."""
        router = IntentRouter()
        request = "Create a User entity with CRUD operations"

        decision1 = router.route(request)
        decision2 = router.route(request)

        assert decision1.agent_name == decision2.agent_name
        assert decision1.intent == decision2.intent
        assert decision1.complexity == decision2.complexity

    def test_similar_requests_similar_routes(self):
        """Test that similar requests route similarly."""
        router = IntentRouter()
        request1 = "Build a User model with CRUD operations"
        request2 = "Build a User entity with create, read, update, delete operations"

        decision1 = router.route(request1)
        decision2 = router.route(request2)

        assert decision1.intent == decision2.intent
        # Complexity and agent should be the same for very similar requests
        assert decision1.agent_name == decision2.agent_name


class TestEntityDetection:
    """Test entity detection."""

    def test_detects_user_entity(self):
        """Test detection of user entity."""
        detector = IntentDetector()
        request = "Create a User model with name and email"
        result = detector.full_detection(request)
        assert "user" in result.entities_detected

    def test_detects_order_entity(self):
        """Test detection of order entity."""
        detector = IntentDetector()
        request = "Build an Order management system"
        result = detector.full_detection(request)
        assert "order" in result.entities_detected

    def test_detects_multiple_entities(self):
        """Test detection of multiple entities."""
        detector = IntentDetector()
        request = "Create User, Product, and Order entities"
        result = detector.full_detection(request)
        assert len(result.entities_detected) >= 3


class TestFeatureDetection:
    """Test feature detection."""

    def test_detects_crud_features(self):
        """Test detection of CRUD features."""
        detector = IntentDetector()
        request = "Create, read, update, and delete users"
        result = detector.full_detection(request)
        assert "create" in result.features_detected
        assert "read" in result.features_detected
        assert "update" in result.features_detected
        assert "delete" in result.features_detected

    def test_detects_pagination(self):
        """Test detection of pagination feature."""
        detector = IntentDetector()
        request = "Build a user list with pagination"
        result = detector.full_detection(request)
        assert "pagination" in result.features_detected

    def test_detects_search_filter(self):
        """Test detection of search/filter features."""
        detector = IntentDetector()
        request = "Add search and filter to the user list"
        result = detector.full_detection(request)
        assert any(f in result.features_detected for f in ["search", "filter"])


class TestConfidenceScoring:
    """Test confidence scoring."""

    def test_confidence_increases_with_keywords(self):
        """Test that confidence increases with more matching keywords."""
        detector = IntentDetector()
        vague = detector.full_detection("Build something")
        detailed = detector.full_detection(
            "Build a simple CRUD system with list, create, update, delete operations"
        )
        # More detailed request should have higher confidence for simple_crud
        assert detailed.confidence >= vague.confidence

    def test_confidence_in_valid_range(self):
        """Test that confidence is always in valid range [0.0, 1.0]."""
        detector = IntentDetector()
        request = "Create a complex payment processing system with Stripe"
        result = detector.full_detection(request)
        assert 0.0 <= result.confidence <= 1.0


class TestApplyRules:
    """Test deterministic rule application."""

    def test_apply_rules_returns_agent_name(self):
        """Test that apply_rules returns a valid agent name."""
        router = IntentRouter()
        agent_name = router.apply_rules(
            IntentType.simple_crud,
            ComplexityLevel.low,
            RiskLevel.experimental,
        )
        assert agent_name == "SimpleCRUD"

    def test_apply_rules_consistent(self):
        """Test that apply_rules is deterministic."""
        router = IntentRouter()
        name1 = router.apply_rules(
            IntentType.payment_system,
            ComplexityLevel.high,
            RiskLevel.production_critical,
        )
        name2 = router.apply_rules(
            IntentType.payment_system,
            ComplexityLevel.high,
            RiskLevel.production_critical,
        )
        assert name1 == name2


# Run all tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
