"""Driver endpoints: profile, vehicle attachment, online/offline, GPS pings."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..deps import get_current_user, require_role
from ..models.driver import Driver, DriverStatus
from ..models.driver_location import DriverLocation
from ..models.user import User, UserRole
from ..models.vehicle import Vehicle
from ..schemas import (
    DriverLocationUpdate,
    DriverProfileCreate,
    DriverRead,
    DriverStatusUpdate,
    VehicleCreate,
    VehicleRead,
)
from ..services.matching import geohash_prefix

router = APIRouter(prefix="/api/v1/drivers", tags=["drivers"])


@router.post("/me/profile", response_model=DriverRead, status_code=status.HTTP_201_CREATED)
async def create_driver_profile(
    payload: DriverProfileCreate,
    user: User = Depends(require_role(UserRole.driver)),
    db: AsyncSession = Depends(get_db),
) -> DriverRead:
    existing = (await db.execute(select(Driver).where(Driver.user_id == user.id))).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="driver profile already exists")

    driver = Driver(
        user_id=user.id,
        license_number=payload.license_number,
        license_expiry=payload.license_expiry,
        vehicle_id=payload.vehicle_id,
    )
    db.add(driver)
    await db.commit()
    await db.refresh(driver)
    return DriverRead.model_validate(driver)


@router.get("/me", response_model=DriverRead)
async def get_my_driver_profile(
    user: User = Depends(require_role(UserRole.driver)),
    db: AsyncSession = Depends(get_db),
) -> DriverRead:
    driver = (await db.execute(select(Driver).where(Driver.user_id == user.id))).scalar_one_or_none()
    if driver is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="driver profile not set up")
    return DriverRead.model_validate(driver)


@router.put("/me/status", response_model=DriverRead)
async def set_driver_status(
    payload: DriverStatusUpdate,
    user: User = Depends(require_role(UserRole.driver)),
    db: AsyncSession = Depends(get_db),
) -> DriverRead:
    driver = (await db.execute(select(Driver).where(Driver.user_id == user.id))).scalar_one_or_none()
    if driver is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="driver profile not set up")
    driver.status = payload.status
    await db.commit()
    await db.refresh(driver)
    return DriverRead.model_validate(driver)


@router.put("/me/location", status_code=status.HTTP_204_NO_CONTENT)
async def update_driver_location(
    payload: DriverLocationUpdate,
    user: User = Depends(require_role(UserRole.driver)),
    db: AsyncSession = Depends(get_db),
) -> None:
    driver = (await db.execute(select(Driver).where(Driver.user_id == user.id))).scalar_one_or_none()
    if driver is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="driver profile not set up")

    loc = DriverLocation(
        driver_id=user.id,
        lat=payload.lat,
        lng=payload.lng,
        accuracy_m=payload.accuracy_m,
        heading_deg=payload.heading_deg,
        speed_kmh=payload.speed_kmh,
        geohash=geohash_prefix(payload.lat, payload.lng),
        is_online=driver.status != DriverStatus.offline,
        is_on_trip=driver.status == DriverStatus.on_ride,
        timestamp_server=datetime.utcnow(),
    )
    db.add(loc)
    await db.commit()


@router.post("/me/vehicle", response_model=VehicleRead, status_code=status.HTTP_201_CREATED)
async def attach_vehicle(
    payload: VehicleCreate,
    user: User = Depends(require_role(UserRole.driver)),
    db: AsyncSession = Depends(get_db),
) -> VehicleRead:
    driver = (await db.execute(select(Driver).where(Driver.user_id == user.id))).scalar_one_or_none()
    if driver is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="driver profile not set up")

    duplicate = (await db.execute(select(Vehicle).where(Vehicle.license_plate == payload.license_plate))).scalar_one_or_none()
    if duplicate is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="license plate already registered")

    vehicle = Vehicle(**payload.model_dump())
    db.add(vehicle)
    await db.flush()
    driver.vehicle_id = vehicle.id
    await db.commit()
    await db.refresh(vehicle)
    return VehicleRead.model_validate(vehicle)
