"""
Routing Matrix — Phase 3-T3

Deterministic routing table: (intent, complexity, risk) → (agent_name, cost_model, max_iterations)

Maps detection results to specialized agents with cost and performance estimates.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

from intent_detector import IntentType, ComplexityLevel, RiskLevel


@dataclass
class AgentSpec:
    """Specification for a specialist agent."""
    name: str
    description: str
    cost_per_token: float  # Estimated cost per 1k tokens
    max_iterations: int
    max_cost_estimate: float  # Max total cost estimate
    duration_estimate_minutes: float  # Estimated duration
    requires_security_review: bool = False
    requires_performance_review: bool = False
    requires_compliance_check: bool = False
    special_handling: list[str] = None

    def __post_init__(self):
        if self.special_handling is None:
            self.special_handling = []


class RoutingMatrix:
    """Deterministic routing matrix for intent-based agent selection."""

    # Define specialist agents
    AGENTS = {
        "simple_crud": AgentSpec(
            name="SimpleCRUD",
            description="Lightweight CRUD agent for simple entity creation",
            cost_per_token=0.15,
            max_iterations=2,
            max_cost_estimate=0.30,
            duration_estimate_minutes=5,
            requires_security_review=False,
        ),
        "complex_domain": AgentSpec(
            name="ComplexDomain",
            description="Full-featured reasoning agent for complex multi-entity systems",
            cost_per_token=0.40,
            max_iterations=5,
            max_cost_estimate=1.50,
            duration_estimate_minutes=20,
            requires_security_review=False,
        ),
        "realtime_specialist": AgentSpec(
            name="RealTimeSpecialist",
            description="WebSocket/streaming/async specialist",
            cost_per_token=0.50,
            max_iterations=5,
            max_cost_estimate=1.80,
            duration_estimate_minutes=25,
            requires_performance_review=True,
            special_handling=["async_validation", "connection_pool_testing"],
        ),
        "payment_specialist": AgentSpec(
            name="PaymentSpecialist",
            description="Stripe/payment processing specialist with security hardening",
            cost_per_token=0.60,
            max_iterations=7,
            max_cost_estimate=2.50,
            duration_estimate_minutes=30,
            requires_security_review=True,
            requires_compliance_check=True,
            special_handling=["pci_compliance_check", "encryption_validation", "token_handling"],
        ),
        "api_designer": AgentSpec(
            name="APIDesigner",
            description="REST/GraphQL API design specialist",
            cost_per_token=0.35,
            max_iterations=4,
            max_cost_estimate=1.20,
            duration_estimate_minutes=18,
            requires_security_review=False,
            special_handling=["schema_validation", "versioning_strategy"],
        ),
        "admin_dashboard": AgentSpec(
            name="AdminDashboard",
            description="Admin panel and reporting specialist",
            cost_per_token=0.40,
            max_iterations=4,
            max_cost_estimate=1.40,
            duration_estimate_minutes=22,
            requires_performance_review=True,
            special_handling=["query_optimization", "pagination_strategy"],
        ),
        "integration_specialist": AgentSpec(
            name="IntegrationSpecialist",
            description="Third-party API and webhook integration specialist",
            cost_per_token=0.45,
            max_iterations=5,
            max_cost_estimate=1.60,
            duration_estimate_minutes=24,
            requires_security_review=True,
            special_handling=["oauth_flow", "webhook_signature_validation", "rate_limiting"],
        ),
        "data_pipeline": AgentSpec(
            name="DataPipelineSpecialist",
            description="Batch processing, cron jobs, and async workers",
            cost_per_token=0.40,
            max_iterations=4,
            max_cost_estimate=1.30,
            duration_estimate_minutes=20,
            requires_performance_review=True,
            special_handling=["job_scheduling", "error_recovery", "idempotency"],
        ),
    }

    # Routing matrix: (intent, complexity, risk) → agent_name
    # Format: lower complexity and risk use simpler agents
    MATRIX: Dict[
        Tuple[IntentType, ComplexityLevel, RiskLevel], str
    ] = {
        # Simple CRUD — low/medium complexity, standard/experimental risk
        (IntentType.simple_crud, ComplexityLevel.low, RiskLevel.experimental): "simple_crud",
        (IntentType.simple_crud, ComplexityLevel.low, RiskLevel.standard): "simple_crud",
        (IntentType.simple_crud, ComplexityLevel.medium, RiskLevel.experimental): "simple_crud",
        (IntentType.simple_crud, ComplexityLevel.medium, RiskLevel.standard): "complex_domain",
        (IntentType.simple_crud, ComplexityLevel.high, RiskLevel.experimental): "complex_domain",
        (IntentType.simple_crud, ComplexityLevel.high, RiskLevel.standard): "complex_domain",
        (IntentType.simple_crud, ComplexityLevel.high, RiskLevel.production_critical): "complex_domain",
        (IntentType.simple_crud, ComplexityLevel.enterprise, RiskLevel.standard): "complex_domain",
        (IntentType.simple_crud, ComplexityLevel.enterprise, RiskLevel.production_critical): "complex_domain",
        # Complex multi-entity → always complex_domain agent
        (IntentType.complex_multi_entity, ComplexityLevel.low, RiskLevel.experimental): "complex_domain",
        (IntentType.complex_multi_entity, ComplexityLevel.low, RiskLevel.standard): "complex_domain",
        (IntentType.complex_multi_entity, ComplexityLevel.medium, RiskLevel.experimental): "complex_domain",
        (IntentType.complex_multi_entity, ComplexityLevel.medium, RiskLevel.standard): "complex_domain",
        (IntentType.complex_multi_entity, ComplexityLevel.high, RiskLevel.experimental): "complex_domain",
        (IntentType.complex_multi_entity, ComplexityLevel.high, RiskLevel.standard): "complex_domain",
        (IntentType.complex_multi_entity, ComplexityLevel.high, RiskLevel.production_critical): "complex_domain",
        (IntentType.complex_multi_entity, ComplexityLevel.enterprise, RiskLevel.standard): "complex_domain",
        (IntentType.complex_multi_entity, ComplexityLevel.enterprise, RiskLevel.production_critical): "complex_domain",
        # Real-time systems → RealTimeSpecialist (always, regardless of complexity/risk)
        (IntentType.real_time_system, ComplexityLevel.low, RiskLevel.experimental): "realtime_specialist",
        (IntentType.real_time_system, ComplexityLevel.low, RiskLevel.standard): "realtime_specialist",
        (IntentType.real_time_system, ComplexityLevel.low, RiskLevel.production_critical): "realtime_specialist",
        (IntentType.real_time_system, ComplexityLevel.medium, RiskLevel.experimental): "realtime_specialist",
        (IntentType.real_time_system, ComplexityLevel.medium, RiskLevel.standard): "realtime_specialist",
        (IntentType.real_time_system, ComplexityLevel.medium, RiskLevel.production_critical): "realtime_specialist",
        (IntentType.real_time_system, ComplexityLevel.high, RiskLevel.experimental): "realtime_specialist",
        (IntentType.real_time_system, ComplexityLevel.high, RiskLevel.standard): "realtime_specialist",
        (IntentType.real_time_system, ComplexityLevel.high, RiskLevel.production_critical): "realtime_specialist",
        (IntentType.real_time_system, ComplexityLevel.enterprise, RiskLevel.experimental): "realtime_specialist",
        (IntentType.real_time_system, ComplexityLevel.enterprise, RiskLevel.standard): "realtime_specialist",
        (IntentType.real_time_system, ComplexityLevel.enterprise, RiskLevel.production_critical): "realtime_specialist",
        # Payment systems → PaymentSpecialist (always, regardless of complexity/risk)
        (IntentType.payment_system, ComplexityLevel.low, RiskLevel.experimental): "payment_specialist",
        (IntentType.payment_system, ComplexityLevel.low, RiskLevel.standard): "payment_specialist",
        (IntentType.payment_system, ComplexityLevel.low, RiskLevel.production_critical): "payment_specialist",
        (IntentType.payment_system, ComplexityLevel.medium, RiskLevel.experimental): "payment_specialist",
        (IntentType.payment_system, ComplexityLevel.medium, RiskLevel.standard): "payment_specialist",
        (IntentType.payment_system, ComplexityLevel.medium, RiskLevel.production_critical): "payment_specialist",
        (IntentType.payment_system, ComplexityLevel.high, RiskLevel.experimental): "payment_specialist",
        (IntentType.payment_system, ComplexityLevel.high, RiskLevel.standard): "payment_specialist",
        (IntentType.payment_system, ComplexityLevel.high, RiskLevel.production_critical): "payment_specialist",
        (IntentType.payment_system, ComplexityLevel.enterprise, RiskLevel.experimental): "payment_specialist",
        (IntentType.payment_system, ComplexityLevel.enterprise, RiskLevel.standard): "payment_specialist",
        (IntentType.payment_system, ComplexityLevel.enterprise, RiskLevel.production_critical): "payment_specialist",
        # API Design
        (IntentType.api_design, ComplexityLevel.low, RiskLevel.experimental): "simple_crud",
        (IntentType.api_design, ComplexityLevel.low, RiskLevel.standard): "api_designer",
        (IntentType.api_design, ComplexityLevel.medium, RiskLevel.experimental): "api_designer",
        (IntentType.api_design, ComplexityLevel.medium, RiskLevel.standard): "api_designer",
        (IntentType.api_design, ComplexityLevel.high, RiskLevel.experimental): "api_designer",
        (IntentType.api_design, ComplexityLevel.high, RiskLevel.standard): "api_designer",
        (IntentType.api_design, ComplexityLevel.high, RiskLevel.production_critical): "api_designer",
        (IntentType.api_design, ComplexityLevel.enterprise, RiskLevel.standard): "api_designer",
        (IntentType.api_design, ComplexityLevel.enterprise, RiskLevel.production_critical): "api_designer",
        # Admin Panel
        (IntentType.admin_panel, ComplexityLevel.low, RiskLevel.experimental): "simple_crud",
        (IntentType.admin_panel, ComplexityLevel.low, RiskLevel.standard): "admin_dashboard",
        (IntentType.admin_panel, ComplexityLevel.medium, RiskLevel.experimental): "admin_dashboard",
        (IntentType.admin_panel, ComplexityLevel.medium, RiskLevel.standard): "admin_dashboard",
        (IntentType.admin_panel, ComplexityLevel.high, RiskLevel.experimental): "admin_dashboard",
        (IntentType.admin_panel, ComplexityLevel.high, RiskLevel.standard): "admin_dashboard",
        (IntentType.admin_panel, ComplexityLevel.high, RiskLevel.production_critical): "admin_dashboard",
        (IntentType.admin_panel, ComplexityLevel.enterprise, RiskLevel.standard): "admin_dashboard",
        (IntentType.admin_panel, ComplexityLevel.enterprise, RiskLevel.production_critical): "admin_dashboard",
        # Integration
        (IntentType.integration, ComplexityLevel.low, RiskLevel.experimental): "integration_specialist",
        (IntentType.integration, ComplexityLevel.low, RiskLevel.standard): "integration_specialist",
        (IntentType.integration, ComplexityLevel.medium, RiskLevel.experimental): "integration_specialist",
        (IntentType.integration, ComplexityLevel.medium, RiskLevel.standard): "integration_specialist",
        (IntentType.integration, ComplexityLevel.high, RiskLevel.experimental): "integration_specialist",
        (IntentType.integration, ComplexityLevel.high, RiskLevel.standard): "integration_specialist",
        (IntentType.integration, ComplexityLevel.high, RiskLevel.production_critical): "integration_specialist",
        (IntentType.integration, ComplexityLevel.enterprise, RiskLevel.standard): "integration_specialist",
        (IntentType.integration, ComplexityLevel.enterprise, RiskLevel.production_critical): "integration_specialist",
        # Data Pipeline
        (IntentType.data_pipeline, ComplexityLevel.low, RiskLevel.experimental): "data_pipeline",
        (IntentType.data_pipeline, ComplexityLevel.low, RiskLevel.standard): "data_pipeline",
        (IntentType.data_pipeline, ComplexityLevel.medium, RiskLevel.experimental): "data_pipeline",
        (IntentType.data_pipeline, ComplexityLevel.medium, RiskLevel.standard): "data_pipeline",
        (IntentType.data_pipeline, ComplexityLevel.high, RiskLevel.experimental): "data_pipeline",
        (IntentType.data_pipeline, ComplexityLevel.high, RiskLevel.standard): "data_pipeline",
        (IntentType.data_pipeline, ComplexityLevel.high, RiskLevel.production_critical): "data_pipeline",
        (IntentType.data_pipeline, ComplexityLevel.enterprise, RiskLevel.standard): "data_pipeline",
        (IntentType.data_pipeline, ComplexityLevel.enterprise, RiskLevel.production_critical): "data_pipeline",
    }

    @classmethod
    def get_agent(
        cls,
        intent: IntentType,
        complexity: ComplexityLevel,
        risk: RiskLevel,
    ) -> AgentSpec:
        """
        Get the recommended agent spec for the given intent/complexity/risk.

        Falls back to complex_domain if no exact match found.
        """
        agent_name = cls.MATRIX.get((intent, complexity, risk), "complex_domain")
        return cls.AGENTS.get(agent_name, cls.AGENTS["complex_domain"])

    @classmethod
    def list_agents(cls) -> Dict[str, AgentSpec]:
        """Return all available agents."""
        return cls.AGENTS.copy()
