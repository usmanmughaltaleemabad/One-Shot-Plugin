"""Driver — extension of User with vehicle + availability + earnings."""

from __future__ import annotations

import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base


class DriverStatus(enum.StrEnum):
    offline = "offline"
    online = "online"
    on_ride = "on_ride"


class Driver(Base):
    __tablename__ = "drivers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)

    license_number: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    license_expiry: Mapped[date] = mapped_column(Date, nullable=False)
    vehicle_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("vehicles.id"), nullable=True, index=True)

    rating_avg: Mapped[float] = mapped_column(Float, default=0.0)
    total_rides: Mapped[int] = mapped_column(Integer, default=0)
    total_earnings_cents: Mapped[int] = mapped_column(Integer, default=0)

    status: Mapped[DriverStatus] = mapped_column(Enum(DriverStatus, native_enum=False), default=DriverStatus.offline, index=True)

    bank_account_token: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_verified: Mapped[bool] = mapped_column(default=False)
    verification_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
