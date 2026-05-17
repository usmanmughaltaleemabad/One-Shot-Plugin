"""SQLAlchemy async models for payment processor."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, DateTime, Numeric, String, Text
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase


class Base(AsyncAttrs, DeclarativeBase):
    """Base model for all entities."""
    pass


class Payment(Base):
    """Payment entity."""

    __tablename__ = "payments"

    id = Column(String, primary_key=True)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    stripe_charge_id = Column(String, unique=True, nullable=False)
    status = Column(String, default="pending")
    metadata = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Refund(Base):
    """Refund entity."""

    __tablename__ = "refunds"

    id = Column(String, primary_key=True)
    payment_id = Column(String, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    stripe_refund_id = Column(String, unique=True)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)


class IdempotencyKey(Base):
    """Idempotency key tracking."""

    __tablename__ = "idempotency_keys"

    key = Column(String, primary_key=True)
    payment_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
