"""Health check endpoints."""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"
    service: str = "WenxinLens API"


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/ready")
async def readiness_check(request: Request) -> JSONResponse:
    """Dependency-aware readiness probe; /health remains a liveness probe."""
    if getattr(request.app.state, "fast_startup", False):
        return JSONResponse(status_code=503, content={"status": "degraded", "reason": "FAST_STARTUP is enabled"})

    vision = getattr(request.app.state, "vision_service", None)
    vector_store = getattr(request.app.state, "vector_store", None)
    dependencies = {
        "vision": vision is not None and getattr(vision, "_initialized", False),
        "vector_store": vector_store is not None
                        and (getattr(vector_store, "_client", None) == "milvus"
                             or getattr(vector_store, "_use_faiss", False)),
        "neo4j": getattr(request.app.state, "neo4j", None) is not None
                   and getattr(getattr(request.app.state, "neo4j", None), "_driver", None) is not None,
    }
    ready = all(dependencies.values())
    return JSONResponse(
        status_code=200 if ready else 503,
        content={"status": "ready" if ready else "degraded", "dependencies": dependencies},
    )

@router.get("/")
async def root() -> dict:
    return {
        "message": "Welcome to WenxinLens — AI Cultural Interpretation for Chinese Ancient Architecture",
        "docs": "/docs",
        "health": "/health",
    }
