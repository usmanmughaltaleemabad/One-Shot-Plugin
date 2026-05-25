"""Rating endpoints: create + list per user."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..deps import get_current_user
from ..models.driver import Driver
from ..models.passenger import Passenger
from ..models.rating import Rating
from ..models.ride import Ride, RideStatus
from ..models.user import User
from ..schemas import RatingCreate, RatingRead

router = APIRouter(prefix="/api/v1/ratings", tags=["ratings"])


@router.post("", response_model=RatingRead, status_code=status.HTTP_201_CREATED)
async def create_rating(
    payload: RatingCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RatingRead:
    ride = (await db.execute(select(Ride).where(Ride.id == payload.ride_id))).scalar_one_or_none()
    if ride is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ride not found")
    if ride.status != RideStatus.completed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="can only rate a completed ride")
    if user.id not in (ride.passenger_id, ride.driver_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    # Ratee must be the other party on this ride.
    other_party = ride.driver_id if user.id == ride.passenger_id else ride.passenger_id
    if payload.ratee_id != other_party:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ratee must be the counterparty")

    rating = Rating(
        ride_id=payload.ride_id,
        rater_id=user.id,
        ratee_id=payload.ratee_id,
        rating=payload.rating,
        comment=payload.comment,
    )
    db.add(rating)
    await db.flush()

    # Update rolling average on the ratee's role-extension row.
    driver = (await db.execute(select(Driver).where(Driver.user_id == payload.ratee_id))).scalar_one_or_none()
    if driver is not None:
        prior = driver.rating_avg * driver.total_rides
        driver.rating_avg = (prior + payload.rating) / max(driver.total_rides + 1, 1)
    passenger = (await db.execute(select(Passenger).where(Passenger.user_id == payload.ratee_id))).scalar_one_or_none()
    if passenger is not None:
        prior = passenger.rating_avg * passenger.total_rides
        passenger.total_rides += 1
        passenger.rating_avg = (prior + payload.rating) / passenger.total_rides

    await db.commit()
    await db.refresh(rating)
    return RatingRead.model_validate(rating)


@router.get("/user/{user_id}", response_model=list[RatingRead])
async def list_ratings_for_user(
    user_id: int,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
) -> list[RatingRead]:
    limit = max(1, min(100, limit))
    stmt = select(Rating).where(Rating.ratee_id == user_id).order_by(Rating.created_at.desc()).limit(limit)
    rows = (await db.execute(stmt)).scalars().all()
    return [RatingRead.model_validate(r) for r in rows]
