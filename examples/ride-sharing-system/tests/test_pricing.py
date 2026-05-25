"""Pure-function tests for the pricing service. No DB, no FastAPI."""

from __future__ import annotations

import pytest

from app.models.vehicle import VehicleType
from app.services.pricing import compute_fare, estimate_duration_minutes, haversine_km


def test_haversine_zero_distance_when_same_point():
    assert haversine_km(40.7, -74.0, 40.7, -74.0) == pytest.approx(0.0, abs=1e-9)


def test_haversine_known_distance_nyc_to_jfk():
    # NYC Times Square ~ (40.7580, -73.9855) to JFK ~ (40.6413, -73.7781)
    d = haversine_km(40.7580, -73.9855, 40.6413, -73.7781)
    assert 20.0 < d < 25.0  # ~22 km


def test_duration_minimum_two_minutes():
    assert estimate_duration_minutes(0.0) == 2
    assert estimate_duration_minutes(0.1) == 2


def test_fare_economy_short_ride():
    # 3 km, 6 min, economy, no surge, no promo
    fare = compute_fare(distance_km=3.0, duration_minutes=6, vehicle_type=VehicleType.economy)
    assert fare.base_cents == 250
    assert fare.distance_cents == 330  # 3 * 110
    assert fare.time_cents == 150       # 6 * 25
    assert fare.surge_cents == 0
    # Subtotal 730 -> tax 58 -> total 788
    assert fare.taxes_cents == 58
    assert fare.total_cents == 788


def test_fare_premium_costs_more_than_economy_for_same_trip():
    eco = compute_fare(distance_km=10, duration_minutes=20, vehicle_type=VehicleType.economy)
    prem = compute_fare(distance_km=10, duration_minutes=20, vehicle_type=VehicleType.premium)
    assert prem.total_cents > eco.total_cents


def test_fare_with_surge():
    base = compute_fare(distance_km=5, duration_minutes=10, vehicle_type=VehicleType.economy)
    surged = compute_fare(distance_km=5, duration_minutes=10, vehicle_type=VehicleType.economy, surge_multiplier=2.0)
    assert surged.surge_cents > 0
    assert surged.total_cents > base.total_cents


def test_promo_discount_caps_at_subtotal():
    """An over-generous promo cannot make the fare negative."""
    fare = compute_fare(
        distance_km=2, duration_minutes=5,
        vehicle_type=VehicleType.economy, promo_discount_cents=999_999,
    )
    # Minimum fare floor applies even when the promo would wipe out the subtotal
    assert fare.total_cents >= 500


def test_minimum_fare_enforced():
    # Tiny ride that would otherwise be cheaper than the floor
    fare = compute_fare(distance_km=0.1, duration_minutes=1, vehicle_type=VehicleType.economy)
    assert fare.total_cents >= 500
