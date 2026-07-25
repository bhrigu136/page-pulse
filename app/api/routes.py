"""API route handlers.

Route handlers are thin — they validate input, delegate to services,
and format responses. No business logic lives here.
"""

from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime, timezone
import time

import structlog
from fastapi import APIRouter, Request

from app.config import get_settings
from app.core.constants import APP_VERSION
from app.core.errors import AuditError, ErrorCode
from app.schemas.request import AuditRequest
from app.schemas.response import AuditResponse, ErrorResponse, HealthResponse

logger = structlog.stdlib.get_logger(__name__)

router = APIRouter()

_RATE_LIMIT_HISTORY: dict[str, deque[float]] = defaultdict(deque)


def _parse_rate_limit(rate_limit: str) -> tuple[int, float]:
    """Parse a rate limit string like '10/minute' into a request count and window seconds."""
    try:
        limit_value, interval = rate_limit.split("/", 1)
    except ValueError:
        return 10, 60.0

    try:
        limit_count = int(limit_value)
    except ValueError:
        return 10, 60.0

    seconds = {
        "second": 1.0,
        "seconds": 1.0,
        "minute": 60.0,
        "minutes": 60.0,
        "hour": 3600.0,
        "hours": 3600.0,
        "day": 86400.0,
        "days": 86400.0,
    }.get(interval.lower())
    if seconds is None:
        return 10, 60.0
    return limit_count, seconds


@router.post("/audit", response_model=AuditResponse)
async def audit_url(request: Request, body: AuditRequest) -> AuditResponse | ErrorResponse:
    """Audit a URL and return detailed information about the response."""
    request_id: str = getattr(request.state, "request_id", "unknown")
    logger.info("audit_request_received", url=body.url)

    client_ip = request.client.host if request.client else "unknown"
    limit_count, window_seconds = _parse_rate_limit(get_settings().rate_limit)
    history = _RATE_LIMIT_HISTORY[client_ip]
    now = time.monotonic()

    while history and now - history[0] >= window_seconds:
        history.popleft()

    if len(history) >= limit_count:
        raise AuditError(
            code=ErrorCode.RATE_LIMITED,
            message="Rate limit exceeded. Please try again later.",
            status_code=429,
        )

    history.append(now)

    try:
        audit_service = request.app.state.audit_service
        result, cached = await audit_service.audit(body.url)

        logger.info(
            "audit_completed",
            url=body.url,
            cached=cached,
            status_code=result.status_code,
            response_time_ms=result.response_time_ms,
        )

        return AuditResponse(
            success=True,
            data=result,
            cached=cached,
            request_id=request_id,
        )
    except AuditError as exc:
        logger.warning(
            "audit_failed",
            url=body.url,
            error_code=exc.code,
            error_message=exc.message,
        )
        raise


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint for monitoring and load balancers."""
    return HealthResponse(
        status="ok",
        timestamp=datetime.now(timezone.utc),
        version=APP_VERSION,
    )
