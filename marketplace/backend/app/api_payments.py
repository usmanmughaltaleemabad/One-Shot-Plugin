"""Payment and webhook handling."""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import stripe
import os
from datetime import datetime
import uuid

from app.database import get_db
from app.models import Subscription, Transaction, Payout, Agent, User
from app.schemas import TransactionResponse

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")


@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle Stripe webhook events."""

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "invoice.payment_succeeded":
        invoice = event["data"]["object"]
        subscription_id = invoice.get("subscription")

        if subscription_id:
            result = await db.execute(
                select(Subscription).where(
                    Subscription.stripe_subscription_id == subscription_id
                )
            )
            subscription = result.scalar_one_or_none()

            if subscription:
                # Create transaction record
                transaction = Transaction(
                    id=str(uuid.uuid4()),
                    type="payment_succeeded",
                    user_id=subscription.user_id,
                    agent_id=subscription.agent_id,
                    amount_usd=subscription.price_usd,
                    platform_fee_usd=int(subscription.price_usd * 0.3),
                    creator_payout_usd=int(subscription.price_usd * 0.7),
                    stripe_charge_id=invoice.get("charge"),
                    stripe_transaction_id=invoice.get("id"),
                    metadata={"stripe_invoice_id": invoice.get("id")},
                )
                db.add(transaction)

                # Update subscription status
                subscription.status = "active"
                subscription.current_period_end = datetime.fromtimestamp(
                    invoice.get("period_end")
                )

                await db.commit()

    elif event["type"] == "invoice.payment_failed":
        invoice = event["data"]["object"]
        subscription_id = invoice.get("subscription")

        if subscription_id:
            result = await db.execute(
                select(Subscription).where(
                    Subscription.stripe_subscription_id == subscription_id
                )
            )
            subscription = result.scalar_one_or_none()

            if subscription:
                subscription.status = "past_due"
                await db.commit()

    elif event["type"] == "customer.subscription.deleted":
        subscription_obj = event["data"]["object"]
        stripe_id = subscription_obj.get("id")

        result = await db.execute(
            select(Subscription).where(Subscription.stripe_subscription_id == stripe_id)
        )
        subscription = result.scalar_one_or_none()

        if subscription:
            subscription.status = "canceled"
            subscription.canceled_at = datetime.utcnow()
            await db.commit()

    return {"status": "received"}


@router.get("/creators/{creator_id}/analytics")
async def creator_analytics(
    creator_id: str,
    current_user: User = Depends(None),
    db: AsyncSession = Depends(get_db),
):
    """Get creator analytics (requires auth as creator)."""

    result = await db.execute(select(User).where(User.id == creator_id))
    creator = result.scalar_one_or_none()

    if not creator or not creator.is_creator:
        raise HTTPException(status_code=404, detail="Creator not found")

    # Get creator's agents
    agents_result = await db.execute(
        select(Agent).where(Agent.creator_id == creator_id)
    )
    agents = agents_result.scalars().all()
    agent_ids = [a.id for a in agents]

    # Calculate revenue
    revenue_result = await db.execute(
        select(func.sum(Transaction.amount_usd)).where(
            Transaction.agent_id.in_(agent_ids),
            Transaction.type == "payment_succeeded",
        )
    )
    total_revenue = revenue_result.scalar() or 0

    # Calculate payout
    payout_result = await db.execute(
        select(func.sum(Transaction.creator_payout_usd)).where(
            Transaction.agent_id.in_(agent_ids)
        )
    )
    total_payout = payout_result.scalar() or 0

    # Calculate subscriptions
    subscriptions_result = await db.execute(
        select(func.count(Subscription.id)).where(
            Subscription.agent_id.in_(agent_ids),
            Subscription.status.in_(["active", "past_due"]),
        )
    )
    active_subscriptions = subscriptions_result.scalar() or 0

    return {
        "creator_id": creator_id,
        "total_agents": len(agents),
        "total_revenue_usd": total_revenue,
        "total_payout_usd": total_payout,
        "active_subscriptions": active_subscriptions,
        "agents": [{"id": a.id, "name": a.name, "price_usd": a.price_usd} for a in agents],
    }


@router.get("/creators/{creator_id}/payouts")
async def creator_payouts(
    creator_id: str,
    current_user: User = Depends(None),
    db: AsyncSession = Depends(get_db),
):
    """Get creator's payout history."""

    result = await db.execute(
        select(Payout)
        .where(Payout.creator_id == creator_id)
        .order_by(Payout.created_at.desc())
    )
    payouts = result.scalars().all()

    return [
        {
            "id": p.id,
            "month": p.month,
            "year": p.year,
            "total_revenue_usd": p.total_revenue_usd,
            "platform_fee_usd": p.platform_fee_usd,
            "amount_paid_usd": p.amount_paid_usd,
            "status": p.status,
            "paid_at": p.paid_at,
        }
        for p in payouts
    ]
