"""User profile endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..deps import get_current_user
from ..models.user import User, UserRole
from ..schemas import UserRead, UserUpdate

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def get_me(user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(user)


@router.put("/me", response_model=UserRead)
async def update_me(
    payload: UserUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.phone is not None:
        user.phone = payload.phone
    await db.commit()
    await db.refresh(user)
    return UserRead.model_validate(user)


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: int,
    requester: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    # Only the user themselves or an admin can fetch arbitrary profiles.
    if requester.id != user_id and requester.role not in (UserRole.admin, UserRole.support):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    target = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if target is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    return UserRead.model_validate(target)
