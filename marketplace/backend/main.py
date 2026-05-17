"""Marketplace API backend for ONE SHOT PLUGIN.

Enables agent discovery, publishing, subscriptions, and revenue sharing.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.api_agents import router as agents_router
from app.api_auth import router as auth_router
from app.api_subscriptions import router as subscriptions_router
from app.api_payments import router as payments_router
from app.database import async_engine
from app.models import Base

app = FastAPI(
    title="ONE SHOT PLUGIN Marketplace",
    description="Agent discovery, publishing, and subscription management",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(agents_router)
app.include_router(auth_router)
app.include_router(subscriptions_router)
app.include_router(payments_router)


@app.on_event("startup")
async def startup():
    """Initialize database tables."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "marketplace-api"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "ONE SHOT PLUGIN Marketplace API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "operational",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
