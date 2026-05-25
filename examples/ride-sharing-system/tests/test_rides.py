"""End-to-end ride flow tests through the FastAPI app."""

from __future__ import annotations

import pytest


async def _register(client, payload):
    r = await client.post("/api/v1/auth/register", json=payload)
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


async def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_request_ride_when_no_drivers_stays_requested(client, passenger_registration):
    token = await _register(client, passenger_registration)
    resp = await client.post(
        "/api/v1/rides",
        json={
            "pickup_lat": 40.7580, "pickup_lng": -73.9855, "pickup_address": "Times Sq",
            "dropoff_lat": 40.7484, "dropoff_lng": -73.9857, "dropoff_address": "Empire State Bldg",
        },
        headers=await _auth(token),
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "requested"
    assert body["driver_id"] is None
    assert body["estimated_fare_cents"] > 0


@pytest.mark.asyncio
async def test_driver_must_have_profile_before_status_update(client, driver_registration):
    token = await _register(client, driver_registration)
    r = await client.put(
        "/api/v1/drivers/me/status",
        json={"status": "online"},
        headers=await _auth(token),
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_driver_full_flow_then_match(client, passenger_registration, driver_registration):
    driver_token = await _register(client, driver_registration)
    passenger_token = await _register(client, passenger_registration)

    # Driver onboards
    r = await client.post(
        "/api/v1/drivers/me/profile",
        json={"license_number": "DL-001", "license_expiry": "2030-01-01"},
        headers=await _auth(driver_token),
    )
    assert r.status_code == 201

    # Goes online
    r = await client.put(
        "/api/v1/drivers/me/status",
        json={"status": "online"},
        headers=await _auth(driver_token),
    )
    assert r.status_code == 200

    # Sends a GPS ping near the pickup
    r = await client.put(
        "/api/v1/drivers/me/location",
        json={"lat": 40.7580, "lng": -73.9855},
        headers=await _auth(driver_token),
    )
    assert r.status_code == 204

    # Passenger requests a ride from the same coords -> should match
    ride = await client.post(
        "/api/v1/rides",
        json={
            "pickup_lat": 40.7580, "pickup_lng": -73.9855, "pickup_address": "Times Sq",
            "dropoff_lat": 40.7484, "dropoff_lng": -73.9857, "dropoff_address": "Empire State",
        },
        headers=await _auth(passenger_token),
    )
    assert ride.status_code == 201, ride.text
    rb = ride.json()
    assert rb["status"] == "matched"
    assert rb["driver_id"] is not None


@pytest.mark.asyncio
async def test_passenger_cannot_get_someone_elses_ride(client, passenger_registration):
    rider1 = passenger_registration
    rider2 = {**passenger_registration, "email": "other@example.com", "phone": "+15559998888"}

    t1 = await _register(client, rider1)
    t2 = await _register(client, rider2)

    ride = await client.post(
        "/api/v1/rides",
        json={
            "pickup_lat": 40.0, "pickup_lng": -73.0, "pickup_address": "A",
            "dropoff_lat": 40.1, "dropoff_lng": -73.1, "dropoff_address": "B",
        },
        headers=await _auth(t1),
    )
    ride_id = ride.json()["id"]

    forbidden = await client.get(f"/api/v1/rides/{ride_id}", headers=await _auth(t2))
    assert forbidden.status_code == 403


@pytest.mark.asyncio
async def test_cancel_ride_records_reason(client, passenger_registration):
    token = await _register(client, passenger_registration)
    ride = await client.post(
        "/api/v1/rides",
        json={
            "pickup_lat": 40.0, "pickup_lng": -73.0, "pickup_address": "A",
            "dropoff_lat": 40.5, "dropoff_lng": -73.5, "dropoff_address": "B",
        },
        headers=await _auth(token),
    )
    rid = ride.json()["id"]
    cancel = await client.put(
        f"/api/v1/rides/{rid}/status",
        json={"status": "cancelled", "reason": "changed my mind"},
        headers=await _auth(token),
    )
    assert cancel.status_code == 200
    assert cancel.json()["status"] == "cancelled"


@pytest.mark.asyncio
async def test_promo_code_reduces_fare(client, passenger_registration):
    # Need an admin to mint the promo. Register one explicitly.
    admin_reg = {**passenger_registration, "email": "admin@example.com", "role": "admin", "phone": "+15550001111"}
    admin_token = await _register(client, admin_reg)
    passenger_token = await _register(client, passenger_registration)

    r = await client.post(
        "/api/v1/admin/promo-codes",
        json={"code": "WELCOME10", "discount_cents": 1000},
        headers=await _auth(admin_token),
    )
    assert r.status_code == 201, r.text

    # Two identical rides, one with promo, one without
    no_promo = await client.post(
        "/api/v1/rides",
        json={
            "pickup_lat": 40.0, "pickup_lng": -73.0, "pickup_address": "A",
            "dropoff_lat": 40.5, "dropoff_lng": -73.5, "dropoff_address": "B",
        },
        headers=await _auth(passenger_token),
    )
    with_promo = await client.post(
        "/api/v1/rides",
        json={
            "pickup_lat": 40.0, "pickup_lng": -73.0, "pickup_address": "A",
            "dropoff_lat": 40.5, "dropoff_lng": -73.5, "dropoff_address": "B",
            "promo_code": "WELCOME10",
        },
        headers=await _auth(passenger_token),
    )
    assert with_promo.json()["estimated_fare_cents"] < no_promo.json()["estimated_fare_cents"]
