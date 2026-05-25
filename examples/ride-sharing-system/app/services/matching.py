"""Driver-matching: nearest online driver inside a search radius.

Simple linear scan over recent ``DriverLocation`` rows for the example.
A real implementation would use a geospatial index (PostGIS, Redis
GEOADD, S2) and pre-filter by geohash bucket.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.driver_location import DriverLocation
from .pricing import haversine_km


_LOCATION_STALENESS_SECONDS = 60  # ignore pings older than this
_DEFAULT_RADIUS_KM = 8.0


async def find_nearest_driver(
    db: AsyncSession,
    pickup_lat: float,
    pickup_lng: float,
    radius_km: float = _DEFAULT_RADIUS_KM,
) -> int | None:
    """Return user_id of the nearest online, not-on-trip driver, or None."""
    cutoff = datetime.utcnow() - timedelta(seconds=_LOCATION_STALENESS_SECONDS)
    stmt = (
        select(DriverLocation)
        .where(DriverLocation.is_online.is_(True))
        .where(DriverLocation.is_on_trip.is_(False))
        .where(DriverLocation.timestamp_server >= cutoff)
    )
    candidates = (await db.execute(stmt)).scalars().all()

    best: tuple[float, int] | None = None
    for c in candidates:
        d = haversine_km(pickup_lat, pickup_lng, c.lat, c.lng)
        if d <= radius_km and (best is None or d < best[0]):
            best = (d, c.driver_id)
    return best[1] if best else None


def geohash_prefix(lat: float, lng: float, precision: int = 6) -> str:
    """Tiny geohash encoder (precision 6 ~ 1.2km tile). Not standard geohash
    grammar but stable enough for this example's nearby-bucket filter."""
    return f"{int((lat + 90) * 10**precision):0{precision + 2}d}_{int((lng + 180) * 10**precision):0{precision + 2}d}"
