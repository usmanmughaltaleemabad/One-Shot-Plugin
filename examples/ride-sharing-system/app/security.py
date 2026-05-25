"""Password hashing + JWT helpers.

For the example we use stdlib hashlib (PBKDF2-HMAC-SHA256) and PyJWT.
Production should use ``argon2-cffi`` or ``passlib[bcrypt]`` and rotate
the JWT secret from a secrets manager.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt

JWT_SECRET = os.environ.get("RIDESHARE_JWT_SECRET", "dev-secret-rotate-in-prod")
JWT_ALG = "HS256"
ACCESS_TTL = timedelta(minutes=15)
REFRESH_TTL = timedelta(days=7)
_PBKDF2_ITERATIONS = 200_000


def hash_password(password: str, salt: bytes | None = None) -> str:
    """Returns ``salt$hex_hash`` (base64-friendly)."""
    if salt is None:
        salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS)
    return salt.hex() + "$" + digest.hex()


def verify_password(password: str, encoded: str) -> bool:
    try:
        salt_hex, hash_hex = encoded.split("$", 1)
    except ValueError:
        return False
    salt = bytes.fromhex(salt_hex)
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS)
    return hmac.compare_digest(candidate.hex(), hash_hex)


def create_token(user_id: int, role: str, ttl: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + ttl).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


def create_access_token(user_id: int, role: str) -> str:
    return create_token(user_id, role, ACCESS_TTL)


def create_refresh_token(user_id: int, role: str) -> str:
    return create_token(user_id, role, REFRESH_TTL)


def decode_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
