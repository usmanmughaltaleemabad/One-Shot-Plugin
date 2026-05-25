"""Ride — the core transaction entity."""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base


class RideStatus(enum.StrEnum):
    requested = "requested"
    matched = "matched"
    accepted = "accepted"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class Ride(Base):
    __tablename__ = "rides"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    passenger_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    driver_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    status: Mapped[RideStatus] = mapped_column(Enum(RideStatus, native_enum=False), default=RideStatus.requested, index=True)

    pickup_lat: Mapped[float] = mapped_column(Float, nullable=False)
    pickup_lng: Mapped[float] = mapped_column(Float, nullable=False)
    pickup_address: Mapped[str] = mapped_column(String(512), nullable=False)
    dropoff_lat: Mapped[float] = mapped_column(Float, nullable=False)
    dropoff_lng: Mapped[float] = mapped_column(Float, nullable=False)
    dropoff_address: Mapped[str] = mapped_column(String(512), nullable=False)

    scheduled_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    matched_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    distance_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    estimated_fare_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actual_fare_cents: Mapped[int | None] = mapped_column(Integer, nullable=True)
    surge_multiplier: Mapped[float] = mapped_column(Float, default=1.0)

    special_requests: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(String(512), nullable=True)
    cancellation_by: Mapped[str | None] = mapped_column(String(32), nullable=True)  # 'passenger' | 'driver'
    cancellation_fee_cents: Mapped[int] = mapped_column(Integer, default=0)

    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
