"""Payment-related endpoints: history, receipt, tip."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..deps import get_current_user
from ..models.payment import Payment
from ..models.user import User, UserRole
from ..schemas import PaymentRead, TipAdd

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])


@router.get("", response_model=list[PaymentRead])
async def list_my_payments(
    user: User = Depends(get_current_user),
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
) -> list[PaymentRead]:
    limit = max(1, min(100, limit))
    stmt = (
        select(Payment)
        .where((Payment.passenger_id == user.id) | (Payment.driver_id == user.id))
        .order_by(Payment.created_at.desc())
        .limit(limit)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return [PaymentRead.model_validate(p) for p in rows]


@router.get("/{payment_id}", response_model=PaymentRead)
async def get_payment(
    payment_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaymentRead:
    p = (await db.execute(select(Payment).where(Payment.id == payment_id))).scalar_one_or_none()
    if p is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="payment not found")
    if user.id not in (p.passenger_id, p.driver_id) and user.role not in (UserRole.admin, UserRole.payment_admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    return PaymentRead.model_validate(p)


@router.post("/{payment_id}/tip", response_model=PaymentRead)
async def add_tip(
    payment_id: int,
    payload: TipAdd,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaymentRead:
    p = (await db.execute(select(Payment).where(Payment.id == payment_id))).scalar_one_or_none()
    if p is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="payment not found")
    if user.id != p.passenger_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="only the passenger can tip")
    p.tip_cents = payload.tip_cents
    p.amount_cents = (p.base_fare_cents or 0) + (p.taxes_cents or 0) + p.tip_cents - (p.promo_discount_cents or 0)
    await db.commit()
    await db.refresh(p)
    return PaymentRead.model_validate(p)
