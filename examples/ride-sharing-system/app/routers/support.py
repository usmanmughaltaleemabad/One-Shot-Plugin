"""Support ticket endpoints."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_db
from ..deps import get_current_user, require_role
from ..models.support_ticket import SupportTicket, TicketStatus
from ..models.user import User, UserRole
from ..schemas import TicketCreate, TicketRead, TicketStatusUpdate

router = APIRouter(prefix="/api/v1/support", tags=["support"])


@router.post("/tickets", response_model=TicketRead, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    payload: TicketCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TicketRead:
    ticket = SupportTicket(
        creator_id=user.id,
        ride_id=payload.ride_id,
        category=payload.category,
        priority=payload.priority,
        description=payload.description,
    )
    db.add(ticket)
    await db.commit()
    await db.refresh(ticket)
    return TicketRead.model_validate(ticket)


@router.get("/tickets/{ticket_id}", response_model=TicketRead)
async def get_ticket(
    ticket_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TicketRead:
    t = (await db.execute(select(SupportTicket).where(SupportTicket.id == ticket_id))).scalar_one_or_none()
    if t is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ticket not found")
    if user.id != t.creator_id and user.role not in (UserRole.admin, UserRole.support):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    return TicketRead.model_validate(t)


@router.put("/tickets/{ticket_id}/status", response_model=TicketRead)
async def update_ticket_status(
    ticket_id: int,
    payload: TicketStatusUpdate,
    user: User = Depends(require_role(UserRole.admin, UserRole.support)),
    db: AsyncSession = Depends(get_db),
) -> TicketRead:
    t = (await db.execute(select(SupportTicket).where(SupportTicket.id == ticket_id))).scalar_one_or_none()
    if t is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ticket not found")
    t.status = payload.status
    if payload.resolution_notes is not None:
        t.resolution_notes = payload.resolution_notes
    if payload.status == TicketStatus.resolved:
        t.resolved_at = datetime.utcnow()
    t.assigned_agent_id = user.id
    await db.commit()
    await db.refresh(t)
    return TicketRead.model_validate(t)
