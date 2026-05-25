"""Passenger — extension of User with payment methods + ride history."""

from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base


class Passenger(Base):
    __tablename__ = "passengers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)

    home_address: Mapped[str | None] = mapped_column(String(512), nullable=True)
    work_address: Mapped[str | None] = mapped_column(String(512), nullable=True)
    rating_avg: Mapped[float] = mapped_column(Float, default=0.0)
    total_rides: Mapped[int] = mapped_column(Integer, default=0)
    emergency_contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    emergency_contact_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
