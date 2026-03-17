"""Request / response logging middleware."""
from __future__ import annotations

import time
import uuid

from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
        start = time.perf_counter()

        # Attach request_id for downstream access
        request.state.request_id = request_id

        logger.debug(
            f"→ [{request_id}] {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )

        response = await call_next(request)

        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{elapsed_ms:.1f}ms"

        log_fn = logger.info if response.status_code < 400 else logger.warning
        log_fn(
            f"← [{request_id}] {request.method} {request.url.path} "
            f"{response.status_code} {elapsed_ms:.1f}ms"
        )
        return response
