"""Minimal FastAPI application for testing."""

from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

app = FastAPI(
    title="Minimal API",
    description="Test fixture for auto-wiring",
    version="0.1.0"
)

# Database setup
DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/api")
def root():
    """Root API endpoint."""
    return {"message": "Welcome to Minimal API"}
