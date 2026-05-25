"""PromoCode — discount codes redeemable by passengers."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base


class PromoCode(Base):
    __tablename__ = "promo_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)

    discount_cents: Mapped[int] = mapped_column(Integer, default=0)         # flat discount
    discount_percent: Mapped[int] = mapped_column(Integer, default=0)        # 0-100
    max_redemptions: Mapped[int | None] = mapped_column(Integer, nullable=True)
    redemptions: Mapped[int] = mapped_column(Integer, default=0)

    valid_from: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
