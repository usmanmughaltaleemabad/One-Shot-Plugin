"""SupportTicket — for safety / fraud / billing complaints."""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base


class TicketStatus(enum.StrEnum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    escalated = "escalated"


class TicketPriority(enum.StrEnum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class TicketCategory(enum.StrEnum):
    payment_issue = "payment_issue"
    safety = "safety"
    lost_item = "lost_item"
    quality = "quality"
    fraud = "fraud"
    other = "other"


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    creator_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    ride_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("rides.id"), nullable=True, index=True)

    category: Mapped[TicketCategory] = mapped_column(Enum(TicketCategory, native_enum=False), nullable=False, index=True)
    status: Mapped[TicketStatus] = mapped_column(Enum(TicketStatus, native_enum=False), default=TicketStatus.open, index=True)
    priority: Mapped[TicketPriority] = mapped_column(Enum(TicketPriority, native_enum=False), default=TicketPriority.medium, index=True)

    description: Mapped[str] = mapped_column(String(4000), nullable=False)
    attachments: Mapped[str | None] = mapped_column(String(2048), nullable=True)  # JSON list of URLs

    assigned_agent_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    resolution_notes: Mapped[str | None] = mapped_column(String(4000), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
