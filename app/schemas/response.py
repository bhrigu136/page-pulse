"""Response schemas for the audit API."""

from datetime import datetime

from pydantic import BaseModel, Field


class AuditResult(BaseModel):
    """Detailed audit data returned for a successfully audited URL."""

    url: str
    final_url: str
    status_code: int
    response_time_ms: float
    https_enabled: bool
    redirect_count: int
    page_title: str | None = None
    meta_description: str | None = None
    content_length: int | None = None
    server_header: str | None = None
    security_headers: dict[str, str | None] = Field(default_factory=dict)
    cache_headers: dict[str, str | None] = Field(default_factory=dict)
    timestamp: datetime


class AuditResponse(BaseModel):
    """Successful audit response envelope."""

    success: bool = True
    data: AuditResult
    cached: bool = False
    request_id: str


class ErrorDetail(BaseModel):
    """Structured error information."""

    code: str
    message: str


class ErrorResponse(BaseModel):
    """Error response envelope matching the project spec."""

    success: bool = False
    error: ErrorDetail
    request_id: str


class HealthResponse(BaseModel):
    """Response schema for the GET /health endpoint."""

    status: str = "ok"
    timestamp: datetime
    version: str
