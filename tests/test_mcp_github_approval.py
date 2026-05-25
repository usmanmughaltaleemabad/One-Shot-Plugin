"""
Test mcp_github_approval.py — GitHub MCP integration for approval gates.
"""

import pytest

# Add scripts dir to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "one-shot-generator" / "scripts"))

from mcp_github_approval import (
    ApprovalRequest,
    ApprovalDecision,
    parse_approval_comment,
    simulate_approval_flow,
)


def test_approval_request_structure():
    """Test that ApprovalRequest formats correctly."""
    request = ApprovalRequest(
        pr_number=123,
        repo="owner/repo",
        spec_summary="Add payment processing",
        cost_estimate="$0.30",
        entities=["Payment", "Invoice"],
    )

    assert request.pr_number == 123
    assert request.repo == "owner/repo"
    assert request.created_at is not None

    comment = request.to_github_comment()
    assert "Zone Approval Gate" in comment
    assert "Add payment processing" in comment
    assert "$0.30" in comment
    assert "Payment" in comment


def test_approval_decision_structure():
    """Test that ApprovalDecision has required fields."""
    decision = ApprovalDecision(
        status="approved",
        decided_by="user@example.com",
        comment="Looks good!",
    )

    assert decision.status == "approved"
    assert decision.decided_by == "user@example.com"
    assert decision.decided_at is not None


def test_parse_approval_comment_approve():
    """Test parsing '@bot approve' comment."""
    comment = "This looks good. @bot approve"
    decision = parse_approval_comment(comment)

    assert decision is not None
    assert decision.status == "approved"


def test_parse_approval_comment_deny():
    """Test parsing '@bot deny' comment."""
    comment = "Need to revise. @bot deny"
    decision = parse_approval_comment(comment)

    assert decision is not None
    assert decision.status == "denied"


def test_parse_approval_comment_revise():
    """Test parsing '@bot revise' comment."""
    comment = "Please adjust cost. @bot revise"
    decision = parse_approval_comment(comment)

    assert decision is not None
    assert decision.status == "pending"


def test_parse_approval_comment_no_command():
    """Test parsing comment with no approval command."""
    comment = "This looks okay to me, thanks."
    decision = parse_approval_comment(comment)

    assert decision is None


def test_parse_approval_comment_case_insensitive():
    """Test that approval parsing is case-insensitive."""
    comments = ["@BOT APPROVE", "@Bot Approve", "@bot APPROVE"]

    for comment in comments:
        decision = parse_approval_comment(comment)
        assert decision is not None
        assert decision.status == "approved"


def test_simulate_approval_flow():
    """Test simulated approval flow."""
    request = ApprovalRequest(
        pr_number=456,
        repo="test/repo",
        spec_summary="Add caching layer",
        entities=["Cache"],
    )

    decision = simulate_approval_flow(request)
    assert decision.status in ["approved", "denied", "pending"]
    assert decision.decided_at is not None


def test_approval_request_formatting():
    """Test that GitHub comment format is valid and readable."""
    request = ApprovalRequest(
        pr_number=789,
        repo="owner/repo",
        spec_summary="Multi-line\nspec summary",
        cost_estimate="$0.50",
        entities=["Entity1", "Entity2", "Entity3"],
    )

    comment = request.to_github_comment()

    # Check required sections
    assert "## Zone Approval Gate" in comment
    assert "Spec Summary" in comment
    assert "Cost Estimate" in comment
    assert "Entities" in comment
    assert "Decision" in comment

    # Check instructions are present
    assert "approve" in comment.lower()
    assert "deny" in comment.lower()


def test_approval_decision_pending_status():
    """Test pending decision (no decided_at timestamp)."""
    decision = ApprovalDecision(
        status="pending",
        comment="Awaiting review",
    )

    assert decision.status == "pending"
    assert decision.decided_at is None
