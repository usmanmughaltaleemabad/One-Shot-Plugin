"""RideRequest — pending dispatch entry; lives until a driver matches or it expires."""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base


class RideRequestStatus(enum.StrEnum):
    pending = "pending"
    matched = "matched"
    expired = "expired"
    cancelled = "cancelled"


class RideRequest(Base):
    __tablename__ = "ride_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    passenger_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    pickup_lat: Mapped[float] = mapped_column(Float, nullable=False)
    pickup_lng: Mapped[float] = mapped_column(Float, nullable=False)
    pickup_address: Mapped[str] = mapped_column(String(512), nullable=False)
    dropoff_lat: Mapped[float] = mapped_column(Float, nullable=False)
    dropoff_lng: Mapped[float] = mapped_column(Float, nullable=False)
    dropoff_address: Mapped[str] = mapped_column(String(512), nullable=False)

    status: Mapped[RideRequestStatus] = mapped_column(
        Enum(RideRequestStatus, native_enum=False), default=RideRequestStatus.pending, index=True
    )
    matched_driver_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    available_drivers_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
