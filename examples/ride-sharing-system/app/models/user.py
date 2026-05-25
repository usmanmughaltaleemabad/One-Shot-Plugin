"""User entity — root of the auth + identity model.

Roles (passenger / driver / admin / support) are encoded as an enum on
``User.role`` rather than as separate tables; profile extensions
(Driver, Passenger) live in their own tables joined by user_id.
"""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base


class UserRole(enum.StrEnum):
    passenger = "passenger"
    driver = "driver"
    admin = "admin"
    support = "support"
    corporate = "corporate"
    payment_admin = "payment_admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(32), unique=True, index=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, native_enum=False), nullable=False, default=UserRole.passenger)

    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    profile_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    document_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
