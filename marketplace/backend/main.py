"""Marketplace API backend for ONE SHOT PLUGIN.

Enables agent discovery, publishing, subscriptions, and revenue sharing.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Initialize FastAPI app
app = FastAPI(
    title="ONE SHOT PLUGIN Marketplace",
    description="Agent discovery, publishing, and subscription management",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "marketplace-api"}


# API routes (will be added in next steps)
# - /api/v1/agents
# - /api/v1/subscriptions
# - /api/v1/auth
# - /api/v1/payments
# - /api/v1/webhooks/stripe


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
