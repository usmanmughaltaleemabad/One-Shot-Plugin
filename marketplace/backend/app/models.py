"""Database models for marketplace."""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Boolean,
    Text, ForeignKey, Enum, JSON, UniqueConstraint, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


class User(Base):
    """User model - can be creator or customer or both."""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_creator = Column(Boolean, default=False)
    stripe_customer_id = Column(String(255), unique=True)
    stripe_account_id = Column(String(255), unique=True)  # For creators (Stripe Connect)
    bio = Column(Text)
    avatar_url = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    agents = relationship("Agent", back_populates="creator")
    subscriptions = relationship("Subscription", back_populates="user")
    ratings = relationship("Rating", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")

    __table_args__ = (
        Index("idx_email_active", "email", "is_active"),
        Index("idx_creator_active", "is_creator", "is_active"),
    )


class Agent(Base):
    """Agent model - published to marketplace."""
    __tablename__ = "agents"

    id = Column(String(36), primary_key=True)
    creator_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False)  # creator/agent-name
    description = Column(Text, nullable=False)
    markdown_content = Column(Text, nullable=False)
    category = Column(String(100), nullable=False, index=True)
    keywords = Column(JSON, default=list)
    version = Column(String(50), nullable=False, default="0.1.0")
    price_usd = Column(Integer, default=0)  # In cents (0 = free)

    status = Column(String(50), default="draft")  # draft, published, deprecated
    is_public = Column(Boolean, default=True)

    rating = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)
    install_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime)

    # Relationships
    creator = relationship("User", back_populates="agents")
    versions = relationship("AgentVersion", back_populates="agent", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="agent")
    ratings = relationship("Rating", back_populates="agent", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="agent")

    __table_args__ = (
        UniqueConstraint("creator_id", "slug", name="uq_creator_slug"),
        Index("idx_status_published", "status", "published_at"),
        Index("idx_category_rating", "category", "rating"),
        Index("idx_public_status", "is_public", "status"),
    )


class AgentVersion(Base):
    """Agent version history."""
    __tablename__ = "agent_versions"

    id = Column(String(36), primary_key=True)
    agent_id = Column(String(36), ForeignKey("agents.id"), nullable=False, index=True)
    version = Column(String(50), nullable=False)
    markdown_content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    agent = relationship("Agent", back_populates="versions")

    __table_args__ = (
        UniqueConstraint("agent_id", "version", name="uq_agent_version"),
    )


class Subscription(Base):
    """Subscription model - user subscribes to agent."""
    __tablename__ = "subscriptions"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    agent_id = Column(String(36), ForeignKey("agents.id"), nullable=False, index=True)

    stripe_subscription_id = Column(String(255), unique=True)
    stripe_customer_id = Column(String(255))

    status = Column(String(50), default="active")  # active, canceled, past_due, unpaid
    price_usd = Column(Integer)  # In cents, at time of subscription

    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    current_period_end = Column(DateTime, nullable=False)
    canceled_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="subscriptions")
    agent = relationship("Agent", back_populates="subscriptions")

    __table_args__ = (
        Index("idx_user_status", "user_id", "status"),
        Index("idx_agent_status", "agent_id", "status"),
        Index("idx_period_end", "current_period_end"),
    )


class Rating(Base):
    """Rating/review model."""
    __tablename__ = "ratings"

    id = Column(String(36), primary_key=True)
    agent_id = Column(String(36), ForeignKey("agents.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)

    rating = Column(Integer, nullable=False)  # 1-5 stars
    review = Column(Text)
    helpful_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    agent = relationship("Agent", back_populates="ratings")
    user = relationship("User", back_populates="ratings")

    __table_args__ = (
        UniqueConstraint("agent_id", "user_id", name="uq_agent_user_rating"),
        Index("idx_agent_rating", "agent_id", "rating"),
    )


class Transaction(Base):
    """Financial transaction model - for reporting."""
    __tablename__ = "transactions"

    id = Column(String(36), primary_key=True)

    type = Column(String(50), nullable=False)  # subscription_created, payment_succeeded, payout
    user_id = Column(String(36), ForeignKey("users.id"), index=True)
    agent_id = Column(String(36), ForeignKey("agents.id"), index=True)

    amount_usd = Column(Integer)  # In cents
    platform_fee_usd = Column(Integer)
    creator_payout_usd = Column(Integer)

    stripe_charge_id = Column(String(255))
    stripe_transaction_id = Column(String(255), unique=True)

    metadata = Column(JSON)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="transactions")
    agent = relationship("Agent", back_populates="transactions")

    __table_args__ = (
        Index("idx_type_date", "type", "created_at"),
        Index("idx_user_date", "user_id", "created_at"),
    )


class Payout(Base):
    """Creator payout model - monthly payouts."""
    __tablename__ = "payouts"

    id = Column(String(36), primary_key=True)
    creator_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)

    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)

    total_revenue_usd = Column(Integer, nullable=False)  # In cents
    platform_fee_usd = Column(Integer, nullable=False)
    amount_paid_usd = Column(Integer, nullable=False)

    stripe_payout_id = Column(String(255), unique=True)
    status = Column(String(50), default="pending")  # pending, completed, failed

    paid_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("creator_id", "month", "year", name="uq_creator_month_year"),
        Index("idx_creator_status", "creator_id", "status"),
    )
