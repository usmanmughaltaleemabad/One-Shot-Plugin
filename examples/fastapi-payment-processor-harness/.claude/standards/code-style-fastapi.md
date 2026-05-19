---
type: standards
last_verified: 2026-05-19
owner: claude
---

# FastAPI Code Style

## Routers
All endpoints async. No blocking I/O. Use `Depends(get_db)` for sessions.

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db

router = APIRouter(prefix="/payments", tags=["payments"])

@router.post("/", response_model=PaymentResponse, status_code=201)
async def create_payment(payment_in: PaymentCreate, db: AsyncSession = Depends(get_db)):
    svc = PaymentService(db)
    return await svc.create(payment_in)
```

## Pydantic schemas
Base / Create / Read / Update pattern. Use `from_attributes = True`.

## Service layer
Business logic lives in `{entity}/service.py`, never in routers. Routers delegate; services enforce invariants.

## Errors
Raise `HTTPException` with specific status codes. Never return 200 for errors.
