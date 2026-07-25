"""FastAPI application factory and lifespan management."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator

import httpx
import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.cache.backend import create_cache_backend
from app.config import get_settings
from app.core.constants import APP_VERSION
from app.core.errors import AuditError, ErrorCode
from app.middleware.request_id import RequestIDMiddleware
from app.services.audit import AuditService
from app.utils.logging import setup_logging

logger = structlog.stdlib.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown resources."""
    settings = get_settings()
    setup_logging(settings.log_level, settings.environment)
    logger.info(
        "application_starting",
        version=APP_VERSION,
        environment=settings.environment,
    )

    if getattr(app.state, "audit_service", None) is None:
        http_client = httpx.AsyncClient(
            headers={"User-Agent": f"PagePulse/{APP_VERSION}"},
            follow_redirects=True,
        )
        cache = await create_cache_backend(settings.redis_url)
        semaphore = asyncio.Semaphore(settings.max_concurrent_requests)

        app.state.audit_service = AuditService(
            http_client=http_client,
            cache=cache,
            semaphore=semaphore,
            request_timeout=settings.request_timeout,
            cache_ttl=settings.cache_ttl,
        )
        app.state.http_client = http_client
        app.state.cache = cache
        app.state._audit_service_managed = True
    else:
        app.state._audit_service_managed = False

    logger.info("application_ready")
    yield

    # Shutdown
    logger.info("application_shutting_down")
    if getattr(app.state, "_audit_service_managed", False):
        await app.state.http_client.aclose()
        await app.state.cache.close()


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    get_settings()

    app = FastAPI(
        title="Page Pulse",
        description="Production-ready URL Audit Service",
        version=APP_VERSION,
        lifespan=lifespan,
    )

    # Middleware (order matters — outermost first)
    app.add_middleware(RequestIDMiddleware)

    # Routes
    app.include_router(router)

    # Custom exception handlers
    @app.exception_handler(AuditError)
    async def audit_error_handler(request: Request, exc: AuditError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "unknown")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {"code": exc.code, "message": exc.message},
                "request_id": request_id,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", "unknown")
        # Extract the first meaningful error message
        errors = exc.errors()
        if errors:
            first = errors[0]
            message = first.get("msg", "Validation error")
            # Check if it's a URL validation error
            field = " -> ".join(str(loc) for loc in first.get("loc", []))
            if "url" in field.lower():
                code = ErrorCode.INVALID_URL
            else:
                code = ErrorCode.INVALID_URL
        else:
            message = "Validation error"
            code = ErrorCode.INVALID_URL

        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error": {"code": code, "message": message},
                "request_id": request_id,
            },
        )

    return app


app = create_app()
