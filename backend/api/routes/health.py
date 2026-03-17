"""Health check endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"
    service: str = "WenxinLens API"


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/")
async def root() -> dict:
    return {
        "message": "Welcome to WenxinLens — AI Cultural Interpretation for Chinese Ancient Architecture",
        "docs": "/docs",
        "health": "/health",
    }
