"""Fare calculation.

Pure-Python, deterministic, no external services. Real Uber-like pricing
involves dynamic surge from a real-time supply/demand index — here we use
a simple step function for the example.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from ..models.vehicle import VehicleType


_BASE_FARE_CENTS = {
    VehicleType.economy: 250,
    VehicleType.comfort: 400,
    VehicleType.xl: 550,
    VehicleType.premium: 800,
}
_PER_KM_CENTS = {
    VehicleType.economy: 110,
    VehicleType.comfort: 160,
    VehicleType.xl: 200,
    VehicleType.premium: 320,
}
_PER_MIN_CENTS = {
    VehicleType.economy: 25,
    VehicleType.comfort: 40,
    VehicleType.xl: 50,
    VehicleType.premium: 80,
}
_TAX_RATE = 0.08  # 8% sales tax
_MIN_FARE_CENTS = 500


@dataclass
class FareBreakdown:
    base_cents: int
    distance_cents: int
    time_cents: int
    surge_cents: int
    promo_discount_cents: int
    subtotal_cents: int
    taxes_cents: int
    total_cents: int


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance in km between two coordinates."""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def estimate_duration_minutes(distance_km: float) -> int:
    """30 km/h city average, 60 km/h motorway. Use 35 as a single figure."""
    return max(2, int(distance_km / 35.0 * 60))


def compute_fare(
    distance_km: float,
    duration_minutes: int,
    vehicle_type: VehicleType,
    surge_multiplier: float = 1.0,
    promo_discount_cents: int = 0,
) -> FareBreakdown:
    base = _BASE_FARE_CENTS[vehicle_type]
    distance = int(distance_km * _PER_KM_CENTS[vehicle_type])
    time = duration_minutes * _PER_MIN_CENTS[vehicle_type]

    raw_subtotal = base + distance + time
    surge = int(raw_subtotal * max(0.0, surge_multiplier - 1.0))

    pre_promo = raw_subtotal + surge
    discount = min(promo_discount_cents, pre_promo)
    subtotal = pre_promo - discount

    if subtotal < _MIN_FARE_CENTS:
        # Floor at the minimum fare AFTER the promo discount has been applied
        subtotal = _MIN_FARE_CENTS

    taxes = int(subtotal * _TAX_RATE)
    total = subtotal + taxes

    return FareBreakdown(
        base_cents=base,
        distance_cents=distance,
        time_cents=time,
        surge_cents=surge,
        promo_discount_cents=discount,
        subtotal_cents=subtotal,
        taxes_cents=taxes,
        total_cents=total,
    )
