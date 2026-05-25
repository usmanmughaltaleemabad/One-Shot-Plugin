"""Pydantic schemas — request/response contracts for the API.

Kept in a single module for the example. In a real codebase each
domain would have its own ``schemas/`` package mirroring ``models/``.
"""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field

from .models.driver import DriverStatus
from .models.payment import PaymentMethodKind, PaymentStatus
from .models.ride import RideStatus
from .models.support_ticket import TicketCategory, TicketPriority, TicketStatus
from .models.user import UserRole
from .models.vehicle import VehicleStatus, VehicleType


# ─── Auth ────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    phone: str | None = None
    password: str = Field(min_length=8)
    full_name: str | None = None
    role: UserRole = UserRole.passenger


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# ─── User ────────────────────────────────────────────────────────────

class UserRead(BaseModel):
    id: int
    email: EmailStr
    phone: str | None
    role: UserRole
    full_name: str | None
    profile_verified: bool
    document_verified: bool
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None


# ─── Driver ──────────────────────────────────────────────────────────

class DriverProfileCreate(BaseModel):
    license_number: str
    license_expiry: date
    vehicle_id: int | None = None


class DriverRead(BaseModel):
    id: int
    user_id: int
    license_number: str
    license_expiry: date
    vehicle_id: int | None
    rating_avg: float
    total_rides: int
    status: DriverStatus
    is_verified: bool

    model_config = {"from_attributes": True}


class DriverStatusUpdate(BaseModel):
    status: DriverStatus


class DriverLocationUpdate(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    accuracy_m: float | None = None
    heading_deg: float | None = Field(default=None, ge=0, le=360)
    speed_kmh: float | None = Field(default=None, ge=0)


# ─── Vehicle ─────────────────────────────────────────────────────────

class VehicleCreate(BaseModel):
    license_plate: str
    vin: str
    make: str
    model: str
    year: int = Field(ge=1990, le=2100)
    color: str | None = None
    capacity: int = Field(default=4, ge=1, le=12)
    vehicle_type: VehicleType = VehicleType.economy


class VehicleRead(BaseModel):
    id: int
    license_plate: str
    vin: str
    make: str
    model: str
    year: int
    color: str | None
    capacity: int
    vehicle_type: VehicleType
    status: VehicleStatus

    model_config = {"from_attributes": True}


# ─── Ride ────────────────────────────────────────────────────────────

class RideCreate(BaseModel):
    pickup_lat: float = Field(ge=-90, le=90)
    pickup_lng: float = Field(ge=-180, le=180)
    pickup_address: str
    dropoff_lat: float = Field(ge=-90, le=90)
    dropoff_lng: float = Field(ge=-180, le=180)
    dropoff_address: str
    vehicle_type: VehicleType = VehicleType.economy
    scheduled_time: datetime | None = None
    special_requests: str | None = None
    promo_code: str | None = None


class RideRead(BaseModel):
    id: int
    passenger_id: int
    driver_id: int | None
    status: RideStatus
    pickup_address: str
    dropoff_address: str
    estimated_fare_cents: int | None
    actual_fare_cents: int | None
    surge_multiplier: float
    distance_km: float | None
    duration_minutes: int | None
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class RideStatusUpdate(BaseModel):
    status: RideStatus
    reason: str | None = None  # used when cancelling


# ─── Payment ─────────────────────────────────────────────────────────

class PaymentRead(BaseModel):
    id: int
    ride_id: int
    amount_cents: int
    currency: str
    status: PaymentStatus
    method: PaymentMethodKind
    base_fare_cents: int
    surge_cents: int
    tip_cents: int
    promo_discount_cents: int
    taxes_cents: int
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class TipAdd(BaseModel):
    tip_cents: int = Field(ge=0)


# ─── Rating ──────────────────────────────────────────────────────────

class RatingCreate(BaseModel):
    ride_id: int
    ratee_id: int
    rating: int = Field(ge=1, le=5)
    comment: str | None = None


class RatingRead(BaseModel):
    id: int
    ride_id: int
    rater_id: int
    ratee_id: int
    rating: int
    comment: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Support ─────────────────────────────────────────────────────────

class TicketCreate(BaseModel):
    category: TicketCategory
    description: str = Field(min_length=10)
    ride_id: int | None = None
    priority: TicketPriority = TicketPriority.medium


class TicketRead(BaseModel):
    id: int
    creator_id: int
    ride_id: int | None
    category: TicketCategory
    status: TicketStatus
    priority: TicketPriority
    description: str
    created_at: datetime
    resolved_at: datetime | None

    model_config = {"from_attributes": True}


class TicketStatusUpdate(BaseModel):
    status: TicketStatus
    resolution_notes: str | None = None


# ─── Promo codes ─────────────────────────────────────────────────────

class PromoCodeCreate(BaseModel):
    code: str = Field(min_length=3, max_length=32)
    discount_cents: int = 0
    discount_percent: int = Field(default=0, ge=0, le=100)
    max_redemptions: int | None = None
    valid_until: datetime | None = None


class PromoCodeRead(BaseModel):
    id: int
    code: str
    discount_cents: int
    discount_percent: int
    redemptions: int
    max_redemptions: int | None
    is_active: bool
    valid_until: datetime | None

    model_config = {"from_attributes": True}
