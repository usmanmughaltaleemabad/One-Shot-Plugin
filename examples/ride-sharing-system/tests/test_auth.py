"""Auth endpoint tests."""

from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_register_returns_tokens(client, passenger_registration):
    r = await client.post("/api/v1/auth/register", json=passenger_registration)
    assert r.status_code == 201
    body = r.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email_is_409(client, passenger_registration):
    r1 = await client.post("/api/v1/auth/register", json=passenger_registration)
    assert r1.status_code == 201
    r2 = await client.post("/api/v1/auth/register", json=passenger_registration)
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_login_then_use_token(client, passenger_registration):
    await client.post("/api/v1/auth/register", json=passenger_registration)

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": passenger_registration["email"], "password": passenger_registration["password"]},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    me = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == passenger_registration["email"]


@pytest.mark.asyncio
async def test_login_bad_password_is_401(client, passenger_registration):
    await client.post("/api/v1/auth/register", json=passenger_registration)
    bad = await client.post(
        "/api/v1/auth/login",
        json={"email": passenger_registration["email"], "password": "wrong"},
    )
    assert bad.status_code == 401


@pytest.mark.asyncio
async def test_unauthenticated_me_is_401(client):
    r = await client.get("/api/v1/users/me")
    assert r.status_code == 401
