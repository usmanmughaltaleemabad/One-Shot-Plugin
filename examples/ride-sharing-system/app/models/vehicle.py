"""Vehicle — owned by a Driver, used on Rides."""

from __future__ import annotations

import enum
from datetime import date

from sqlalchemy import Date, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base


class VehicleType(enum.StrEnum):
    economy = "economy"
    comfort = "comfort"
    xl = "xl"
    premium = "premium"


class VehicleStatus(enum.StrEnum):
    active = "active"
    retired = "retired"
    maintenance = "maintenance"


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    license_plate: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    vin: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)

    make: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str] = mapped_column(String(64), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    color: Mapped[str | None] = mapped_column(String(32), nullable=True)
    capacity: Mapped[int] = mapped_column(Integer, default=4)
    vehicle_type: Mapped[VehicleType] = mapped_column(Enum(VehicleType, native_enum=False), default=VehicleType.economy)

    insurance_provider: Mapped[str | None] = mapped_column(String(128), nullable=True)
    policy_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_service_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    next_service_due: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[VehicleStatus] = mapped_column(Enum(VehicleStatus, native_enum=False), default=VehicleStatus.active)
