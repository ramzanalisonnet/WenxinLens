"""
WenxinLens – FastAPI Application Entry Point
"""
from __future__ import annotations

import sys
import time
from contextlib import asynccontextmanager
from typing import AsyncIterator

import sentry_sdk
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from sentry_sdk.integrations.fastapi import FastApiIntegration
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from config import get_settings
from api.routes import recognition, chat, tour, voice, knowledge, health, advanced
from middleware.auth import APIKeyMiddleware
from middleware.logging import RequestLoggingMiddleware
from middleware.rate_limiter import limiter

settings = get_settings()

# ─── Logging ──────────────────────────────────────────────────
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> — <level>{message}</level>",
    level=settings.log_level,
    colorize=True,
)
logger.add(
    "logs/wenxinlens_{time:YYYY-MM-DD}.log",
    rotation="00:00",
    retention="30 days",
    level="INFO",
    compression="zip",
)

# ─── Sentry ───────────────────────────────────────────────────
if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        integrations=[FastApiIntegration(transaction_style="endpoint")],
        traces_sample_rate=0.2,
        environment=settings.app_env,
    )


# ─── Lifespan ─────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup and shutdown lifecycle events."""
    logger.info("WenxinLens starting up …")

    # Lazy imports to avoid circular deps
    from services.vision_service import VisionService
    from services.retrieval_service import RetrievalService
    from knowledge_graph.neo4j_client import Neo4jClient
    from rag.vector_store import VectorStore

    # Warm up vision model
    app.state.vision_service = VisionService()
    await app.state.vision_service.initialize()

    # Initialize vector store connection
    app.state.vector_store = VectorStore()
    await app.state.vector_store.initialize()

    # Initialize graph DB
    app.state.neo4j = Neo4jClient()
    await app.state.neo4j.connect()

    # Initialize retrieval service
    app.state.retrieval_service = RetrievalService(
        vector_store=app.state.vector_store,
        neo4j=app.state.neo4j,
    )

    logger.info("WenxinLens is ready  🏯")
    yield

    # Cleanup
    await app.state.neo4j.close()
    logger.info("WenxinLens shut down cleanly.")


# ─── App Factory ──────────────────────────────────────────────
def create_app() -> FastAPI:
    app = FastAPI(
        title="WenxinLens API",
        description="AI Cultural Interpretation System for Chinese Ancient Architecture",
        version="1.0.0",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # ── Middleware (order matters: outermost first) ─────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
            allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(APIKeyMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(SlowAPIMiddleware)

    # Rate limiter state
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

    # ── Routers ────────────────────────────────────────────────
    app.include_router(health.router, tags=["Health"])
    app.include_router(recognition.router, prefix="/api/v1/recognition", tags=["Recognition"])
    app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
    app.include_router(tour.router, prefix="/api/v1/tour", tags=["Tour"])
    app.include_router(voice.router, prefix="/api/v1/voice", tags=["Voice"])
    app.include_router(knowledge.router, prefix="/api/v1/knowledge", tags=["Knowledge"])
    app.include_router(advanced.router, prefix="/api/v1/advanced", tags=["Advanced Features"])

    # ── Global exception handlers ──────────────────────────────
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "request_id": request.headers.get("X-Request-ID")},
        )

    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=not settings.is_production,
        workers=1 if not settings.is_production else 4,
        proxy_headers=True,
    )
