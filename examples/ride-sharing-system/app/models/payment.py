"""Payment — fare settlement record. Stripe payment intent is stored opaquely."""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base


class PaymentStatus(enum.StrEnum):
    pending = "pending"
    completed = "completed"
    failed = "failed"
    refunded = "refunded"


class PaymentMethodKind(enum.StrEnum):
    stripe_card = "stripe_card"
    wallet = "wallet"
    corporate = "corporate"
    cash = "cash"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ride_id: Mapped[int] = mapped_column(Integer, ForeignKey("rides.id"), nullable=False, index=True)
    passenger_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    driver_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)

    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus, native_enum=False), default=PaymentStatus.pending, index=True)
    method: Mapped[PaymentMethodKind] = mapped_column(Enum(PaymentMethodKind, native_enum=False), default=PaymentMethodKind.stripe_card)

    base_fare_cents: Mapped[int] = mapped_column(Integer, default=0)
    surge_cents: Mapped[int] = mapped_column(Integer, default=0)
    tip_cents: Mapped[int] = mapped_column(Integer, default=0)
    tolls_cents: Mapped[int] = mapped_column(Integer, default=0)
    promo_discount_cents: Mapped[int] = mapped_column(Integer, default=0)
    taxes_cents: Mapped[int] = mapped_column(Integer, default=0)

    stripe_payment_intent_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    receipt_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
