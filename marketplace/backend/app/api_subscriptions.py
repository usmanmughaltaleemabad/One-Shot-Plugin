"""Subscription management endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime, timedelta
import uuid
import stripe

from app.database import get_db
from app.models import Subscription, User, Agent
from app.schemas import SubscriptionCreate, SubscriptionResponse
from app.api_auth import get_current_user

router = APIRouter(prefix="/api/v1/subscriptions", tags=["subscriptions"])

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


@router.post("", response_model=SubscriptionResponse, status_code=201)
async def create_subscription(
    request: SubscriptionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create subscription to agent (initiate Stripe billing)."""

    # Verify agent exists and has a price
    result = await db.execute(select(Agent).where(Agent.id == request.agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if agent.price_usd == 0:
        raise HTTPException(status_code=400, detail="Agent is free, no subscription needed")

    # Check if already subscribed
    existing = await db.execute(
        select(Subscription).where(
            and_(
                Subscription.user_id == current_user.id,
                Subscription.agent_id == request.agent_id,
                Subscription.status.in_(["active", "past_due"]),
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already subscribed to this agent")

    # Create Stripe customer if needed
    if not current_user.stripe_customer_id:
        customer = stripe.Customer.create(email=current_user.email, name=current_user.name)
        current_user.stripe_customer_id = customer.id
        await db.commit()

    # Create Stripe subscription
    try:
        stripe_subscription = stripe.Subscription.create(
            customer=current_user.stripe_customer_id,
            items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": f"{agent.name} Subscription",
                            "description": agent.description,
                        },
                        "unit_amount": agent.price_usd,
                        "recurring": {"interval": "month", "interval_count": 1},
                    }
                }
            ],
            payment_behavior="default_incomplete",
            expand=["latest_invoice.payment_intent"],
        )
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")

    # Create subscription record
    subscription = Subscription(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        agent_id=request.agent_id,
        stripe_subscription_id=stripe_subscription.id,
        stripe_customer_id=current_user.stripe_customer_id,
        status="active",
        price_usd=agent.price_usd,
        current_period_end=datetime.utcnow() + timedelta(days=30),
    )

    db.add(subscription)
    await db.commit()
    await db.refresh(subscription)

    return SubscriptionResponse.from_orm(subscription)


@router.delete("/{subscription_id}")
async def cancel_subscription(
    subscription_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel subscription."""

    result = await db.execute(
        select(Subscription).where(Subscription.id == subscription_id)
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    if subscription.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Cancel Stripe subscription
    try:
        stripe.Subscription.delete(subscription.stripe_subscription_id)
    except stripe.error.StripeError:
        pass  # Log but don't fail

    subscription.status = "canceled"
    subscription.canceled_at = datetime.utcnow()
    await db.commit()

    return {"detail": "Subscription canceled"}


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(
    subscription_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get subscription details."""

    result = await db.execute(
        select(Subscription).where(Subscription.id == subscription_id)
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    if subscription.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    return SubscriptionResponse.from_orm(subscription)


@router.get("", response_model=list[SubscriptionResponse])
async def list_subscriptions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's subscriptions."""

    result = await db.execute(
        select(Subscription)
        .where(Subscription.user_id == current_user.id)
        .order_by(Subscription.created_at.desc())
    )
    subscriptions = result.scalars().all()

    return [SubscriptionResponse.from_orm(s) for s in subscriptions]


import os
