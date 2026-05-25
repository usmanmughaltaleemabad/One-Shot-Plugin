"""Rating — symmetric (passenger→driver and driver→passenger)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base


class Rating(Base):
    __tablename__ = "ratings"
    __table_args__ = (CheckConstraint("rating >= 1 AND rating <= 5", name="rating_range"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ride_id: Mapped[int] = mapped_column(Integer, ForeignKey("rides.id", ondelete="CASCADE"), nullable=False, index=True)
    rater_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    ratee_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    categories: Mapped[str | None] = mapped_column(String(512), nullable=True)  # JSON-encoded list

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
