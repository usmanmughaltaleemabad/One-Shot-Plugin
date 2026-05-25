"""Admin endpoints: promo codes + user suspension + dashboard counters."""

from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..deps import require_role
from ..models.payment import Payment, PaymentStatus
from ..models.promo_code import PromoCode
from ..models.ride import Ride, RideStatus
from ..models.user import User, UserRole
from ..schemas import PromoCodeCreate, PromoCodeRead

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.post("/promo-codes", response_model=PromoCodeRead, status_code=status.HTTP_201_CREATED)
async def create_promo_code(
    payload: PromoCodeCreate,
    admin: User = Depends(require_role(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
) -> PromoCodeRead:
    existing = (await db.execute(select(PromoCode).where(PromoCode.code == payload.code))).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="promo code already exists")
    promo = PromoCode(**payload.model_dump())
    db.add(promo)
    await db.commit()
    await db.refresh(promo)
    return PromoCodeRead.model_validate(promo)


@router.get("/promo-codes", response_model=list[PromoCodeRead])
async def list_promo_codes(
    admin: User = Depends(require_role(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
) -> list[PromoCodeRead]:
    rows = (await db.execute(select(PromoCode).order_by(PromoCode.created_at.desc()))).scalars().all()
    return [PromoCodeRead.model_validate(p) for p in rows]


@router.post("/users/{user_id}/suspend", status_code=status.HTTP_204_NO_CONTENT)
async def suspend_user(
    user_id: int,
    admin: User = Depends(require_role(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
) -> None:
    target = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    target.is_active = False
    await db.commit()


@router.post("/users/{user_id}/ban", status_code=status.HTTP_204_NO_CONTENT)
async def ban_user(
    user_id: int,
    admin: User = Depends(require_role(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
) -> None:
    target = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    target.is_banned = True
    target.is_active = False
    await db.commit()


@router.get("/dashboard")
async def dashboard(
    admin: User = Depends(require_role(UserRole.admin)),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Counters for the admin dashboard. Cheap aggregate query, suitable
    for the example. A production version would use materialised views
    or a metrics store, not COUNT() on the rides table."""
    today = datetime.utcnow() - timedelta(days=1)
    total_users = (await db.execute(select(func.count()).select_from(User))).scalar_one()
    active_rides = (await db.execute(
        select(func.count()).select_from(Ride).where(Ride.status.in_([
            RideStatus.requested, RideStatus.matched, RideStatus.accepted, RideStatus.in_progress
        ]))
    )).scalar_one()
    completed_today = (await db.execute(
        select(func.count()).select_from(Ride).where(Ride.completed_at >= today)
    )).scalar_one()
    revenue_today = (await db.execute(
        select(func.coalesce(func.sum(Payment.amount_cents), 0))
        .where(Payment.status == PaymentStatus.completed)
        .where(Payment.completed_at >= today)
    )).scalar_one()

    return {
        "total_users": total_users,
        "active_rides": active_rides,
        "completed_rides_24h": completed_today,
        "revenue_24h_cents": revenue_today,
    }
