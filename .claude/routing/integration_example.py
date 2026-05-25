"""
Integration Example — Intent-Based Routing with Stage 0.5

Shows how to integrate the intent router into the main pipeline
before the architect agent is invoked.
"""

from pathlib import Path
from intent_router import IntentRouter
from intent_detector import IntentType

# Example: How to integrate into the skill pipeline
def integrate_with_stage_0_5(
    user_request: str,
    session_id: str,
    project_root: str,
):
    """
    Example integration of intent routing with Stage 0.5.

    This would be called in the SKILL.md after initializing routing_trace.
    """
    # Initialize router
    router = IntentRouter(
        knowledge_store_path=Path(project_root) / ".beads" / "routing_decisions.jsonl"
    )

    # Route the request
    decision = router.route(user_request)

    print(f"=== Routing Decision ===")
    print(f"Intent: {decision.intent.value}")
    print(f"Complexity: {decision.complexity.value}")
    print(f"Risk: {decision.risk.value}")
    print(f"Agent: {decision.agent_name}")
    print(f"Cost Estimate: ${decision.cost_estimate:.2f}")
    print(f"Duration: {decision.duration_estimate:.0f} minutes")
    print(f"Confidence: {decision.confidence:.0%}")
    print()
    print(f"Entities: {', '.join(decision.entities_detected)}")
    print(f"Features: {', '.join(decision.features_detected)}")
    print()
    if decision.special_handling:
        print(f"Special Handling Required:")
        for item in decision.special_handling:
            print(f"  - {item}")
    print()
    if decision.similar_past_requests:
        print(f"Similar Past Requests:")
        for req in decision.similar_past_requests:
            print(f"  - {req[:80]}...")

    # Log to routing trace
    try:
        from scripts.routing_trace import get_or_create_trace
        trace = get_or_create_trace(session_id, project_root)
        trace.log_decision(
            stage='PLAN.Stage0.5',
            layer='L1_ROUTER',
            decision='route_intent',
            context={
                'user_request': user_request[:200],
                'intent': decision.intent.value,
                'complexity': decision.complexity.value,
                'risk': decision.risk.value,
                'confidence': decision.confidence,
                'agent': decision.agent_name,
            },
            consequence=f'Route to {decision.agent_name} agent (~${decision.cost_estimate:.2f}, ~{decision.duration_estimate:.0f} min)'
        )
    except ImportError:
        pass  # routing_trace not available

    # Emit to knowledge store
    try:
        from knowledge.knowledge_store import KnowledgeStore
        store = KnowledgeStore()
        store.emit_fact(
            content=f"Routing decision: '{user_request[:100]}...' → {decision.agent_name} (intent={decision.intent.value}, complexity={decision.complexity.value}, risk={decision.risk.value}, confidence={decision.confidence})",
            fact_type="routing_decision"
        )
    except ImportError:
        pass  # Knowledge store not available

    return decision


# Example usage
if __name__ == "__main__":
    # Simulated requests
    test_requests = [
        "Create a simple User CRUD",
        "Build e-commerce with Product, Order, Review entities with relationships",
        "Implement real-time notification system using WebSocket",
        "Integrate Stripe payment processing",
        "Design REST API with authentication",
        "Create admin dashboard with analytics",
        "Sync data with external API using OAuth",
        "Build batch processing pipeline with cron jobs",
    ]

    for request in test_requests:
        print(f"Request: {request}")
        try:
            decision = integrate_with_stage_0_5(request, "test-session", ".")
        except Exception as e:
            print(f"Error: {e}")
        print("\n" + "=" * 80 + "\n")
