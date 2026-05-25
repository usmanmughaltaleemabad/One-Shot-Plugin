"""Smoke tests for the remaining domains: ratings, support, admin."""

from __future__ import annotations

import pytest


async def _register(client, payload):
    r = await client.post("/api/v1/auth/register", json=payload)
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


async def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_health_endpoint(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_passenger_cannot_create_promo_code(client, passenger_registration):
    t = await _register(client, passenger_registration)
    r = await client.post(
        "/api/v1/admin/promo-codes",
        json={"code": "ABC", "discount_cents": 100},
        headers=await _auth(t),
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_create_support_ticket(client, passenger_registration):
    t = await _register(client, passenger_registration)
    r = await client.post(
        "/api/v1/support/tickets",
        json={"category": "lost_item", "description": "Left my phone in car"},
        headers=await _auth(t),
    )
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "open"


@pytest.mark.asyncio
async def test_admin_dashboard_returns_counters(client, passenger_registration):
    admin = {**passenger_registration, "email": "admin@example.com", "role": "admin", "phone": "+15550001111"}
    t = await _register(client, admin)
    r = await client.get("/api/v1/admin/dashboard", headers=await _auth(t))
    assert r.status_code == 200
    body = r.json()
    assert "total_users" in body and body["total_users"] >= 1
    assert "active_rides" in body
    assert "revenue_24h_cents" in body


@pytest.mark.asyncio
async def test_cannot_rate_uncompleted_ride(client, passenger_registration):
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
    r = await client.post(
        "/api/v1/ratings",
        json={"ride_id": rid, "ratee_id": 999, "rating": 5},
        headers=await _auth(token),
    )
    assert r.status_code == 400
