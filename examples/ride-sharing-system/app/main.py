"""FastAPI application factory + router wiring."""

from __future__ import annotations

from fastapi import FastAPI

from .db import init_models
from .routers import admin, auth, drivers, payments, ratings, rides, support, users


def create_app() -> FastAPI:
    app = FastAPI(
        title="Ride-sharing example",
        version="0.1.0",
        description=(
            "Example FastAPI app that demonstrates the patterns the one-shot-prompting "
            "plugin generates for an Uber-like domain. See examples/ride-sharing-system/README.md "
            "for the honest coverage matrix (endpoint count, what's stubbed, what's missing)."
        ),
    )

    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(drivers.router)
    app.include_router(rides.router)
    app.include_router(payments.router)
    app.include_router(ratings.router)
    app.include_router(support.router)
    app.include_router(admin.router)

    @app.on_event("startup")
    async def _create_tables() -> None:
        # In production this would be replaced by Alembic migrations.
        await init_models()

    @app.get("/health", tags=["meta"])
    async def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()
