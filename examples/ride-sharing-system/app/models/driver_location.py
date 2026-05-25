"""DriverLocation — high-frequency GPS pings.

In production this would be a separate hot store (Redis geo set, PostGIS
geography column). For the example we use a normal table with a geohash
prefix for cheap nearby-lookups.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ..db import Base


class DriverLocation(Base):
    __tablename__ = "driver_locations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    driver_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lng: Mapped[float] = mapped_column(Float, nullable=False)
    accuracy_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    heading_deg: Mapped[float | None] = mapped_column(Float, nullable=True)
    speed_kmh: Mapped[float | None] = mapped_column(Float, nullable=True)

    geohash: Mapped[str] = mapped_column(String(12), index=True, nullable=False)

    is_online: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_on_trip: Mapped[bool] = mapped_column(Boolean, default=False)

    timestamp_server: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    timestamp_client: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
