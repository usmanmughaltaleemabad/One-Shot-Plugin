"""Ride endpoints: request, list, accept, cancel, complete."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..deps import get_current_user, require_role
from ..models.driver import Driver, DriverStatus
from ..models.payment import Payment, PaymentStatus
from ..models.promo_code import PromoCode
from ..models.ride import Ride, RideStatus
from ..models.user import User, UserRole
from ..schemas import RideCreate, RideRead, RideStatusUpdate
from ..services.matching import find_nearest_driver
from ..services.pricing import compute_fare, estimate_duration_minutes, haversine_km

router = APIRouter(prefix="/api/v1/rides", tags=["rides"])


def _apply_promo_amount(promo: PromoCode | None, raw_subtotal_cents: int) -> int:
    if promo is None:
        return 0
    if promo.discount_cents:
        return min(promo.discount_cents, raw_subtotal_cents)
    if promo.discount_percent:
        return raw_subtotal_cents * promo.discount_percent // 100
    return 0


@router.post("", response_model=RideRead, status_code=status.HTTP_201_CREATED)
async def request_ride(
    payload: RideCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RideRead:
    if user.role not in (UserRole.passenger, UserRole.corporate):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="only passengers can request rides")

    distance = haversine_km(payload.pickup_lat, payload.pickup_lng, payload.dropoff_lat, payload.dropoff_lng)
    duration = estimate_duration_minutes(distance)

    promo: PromoCode | None = None
    if payload.promo_code:
        promo = (await db.execute(select(PromoCode).where(PromoCode.code == payload.promo_code))).scalar_one_or_none()
        if promo is None or not promo.is_active:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid promo code")
        if promo.max_redemptions is not None and promo.redemptions >= promo.max_redemptions:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="promo code exhausted")

    # Fare is estimated with the requested vehicle type.
    pricing_subtotal = max(0, int(distance * 110) + duration * 25)
    promo_discount = _apply_promo_amount(promo, pricing_subtotal)
    fare = compute_fare(
        distance_km=distance,
        duration_minutes=duration,
        vehicle_type=payload.vehicle_type,
        surge_multiplier=1.0,
        promo_discount_cents=promo_discount,
    )

    matched_driver_id = await find_nearest_driver(db, payload.pickup_lat, payload.pickup_lng)

    ride = Ride(
        passenger_id=user.id,
        driver_id=matched_driver_id,
        status=RideStatus.matched if matched_driver_id else RideStatus.requested,
        pickup_lat=payload.pickup_lat,
        pickup_lng=payload.pickup_lng,
        pickup_address=payload.pickup_address,
        dropoff_lat=payload.dropoff_lat,
        dropoff_lng=payload.dropoff_lng,
        dropoff_address=payload.dropoff_address,
        scheduled_time=payload.scheduled_time,
        estimated_fare_cents=fare.total_cents,
        distance_km=distance,
        duration_minutes=duration,
        special_requests=payload.special_requests,
        matched_at=datetime.utcnow() if matched_driver_id else None,
    )
    db.add(ride)
    if promo is not None:
        promo.redemptions += 1
    await db.commit()
    await db.refresh(ride)
    return RideRead.model_validate(ride)


@router.get("", response_model=list[RideRead])
async def list_my_rides(
    user: User = Depends(get_current_user),
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
) -> list[RideRead]:
    limit = max(1, min(100, limit))
    stmt = (
        select(Ride)
        .where((Ride.passenger_id == user.id) | (Ride.driver_id == user.id))
        .order_by(Ride.created_at.desc())
        .limit(limit)
    )
    rides = (await db.execute(stmt)).scalars().all()
    return [RideRead.model_validate(r) for r in rides]


@router.get("/{ride_id}", response_model=RideRead)
async def get_ride(
    ride_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RideRead:
    ride = (await db.execute(select(Ride).where(Ride.id == ride_id))).scalar_one_or_none()
    if ride is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ride not found")
    if user.id not in (ride.passenger_id, ride.driver_id) and user.role not in (UserRole.admin, UserRole.support):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    return RideRead.model_validate(ride)


@router.put("/{ride_id}/status", response_model=RideRead)
async def update_ride_status(
    ride_id: int,
    payload: RideStatusUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RideRead:
    ride = (await db.execute(select(Ride).where(Ride.id == ride_id))).scalar_one_or_none()
    if ride is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ride not found")

    now = datetime.utcnow()
    new_status = payload.status

    # Transition rules — concise but enforced.
    if new_status == RideStatus.accepted and user.role == UserRole.driver:
        if ride.driver_id != user.id and ride.driver_id is not None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="not your ride")
        ride.driver_id = user.id
        ride.matched_at = ride.matched_at or now
    elif new_status == RideStatus.in_progress and user.id == ride.driver_id:
        ride.started_at = now
        # Mark driver as on_ride
        drv = (await db.execute(select(Driver).where(Driver.user_id == user.id))).scalar_one_or_none()
        if drv is not None:
            drv.status = DriverStatus.on_ride
    elif new_status == RideStatus.completed and user.id == ride.driver_id:
        ride.completed_at = now
        ride.actual_fare_cents = ride.estimated_fare_cents
        # Settle payment record
        payment = Payment(
            ride_id=ride.id,
            passenger_id=ride.passenger_id,
            driver_id=ride.driver_id,
            amount_cents=ride.actual_fare_cents or 0,
            status=PaymentStatus.completed,
            base_fare_cents=ride.actual_fare_cents or 0,
            completed_at=now,
        )
        db.add(payment)
        drv = (await db.execute(select(Driver).where(Driver.user_id == user.id))).scalar_one_or_none()
        if drv is not None:
            drv.status = DriverStatus.online
            drv.total_rides += 1
            drv.total_earnings_cents += payment.amount_cents
    elif new_status == RideStatus.cancelled and user.id in (ride.passenger_id, ride.driver_id):
        ride.cancelled_at = now
        ride.cancellation_reason = payload.reason
        ride.cancellation_by = "passenger" if user.id == ride.passenger_id else "driver"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"transition to {new_status} not allowed for role={user.role}",
        )

    ride.status = new_status
    await db.commit()
    await db.refresh(ride)
    return RideRead.model_validate(ride)
