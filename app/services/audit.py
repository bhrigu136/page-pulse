"""URL audit service — core business logic.

This module contains the AuditService class that orchestrates URL auditing:
cache lookup, HTTP request execution, HTML parsing, and result caching.
"""

from __future__ import annotations

import asyncio
import hashlib
import re
import time
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import httpx
import structlog

from app.core.constants import CACHE_HEADERS, SECURITY_HEADERS
from app.core.errors import AuditError, ErrorCode
from app.schemas.response import AuditResult

if TYPE_CHECKING:
    from app.cache.backend import CacheBackend

logger = structlog.stdlib.get_logger(__name__)

# Precompiled regex for HTML parsing — avoids re-compilation per request
_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
_META_DESC_RE = re.compile(
    r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']*)["\']',
    re.IGNORECASE,
)
_META_DESC_RE_ALT = re.compile(
    r'<meta[^>]+content=["\']([^"\']*)["\'][^>]+name=["\']description["\']',
    re.IGNORECASE,
)


class AuditService:
    """Orchestrates URL auditing with caching and concurrency control.

    Args:
        http_client: Shared async HTTP client for making requests.
        cache: Cache backend for storing/retrieving audit results.
        semaphore: Concurrency limiter for outbound HTTP requests.
        request_timeout: Timeout in seconds for each HTTP request.
        cache_ttl: Time-to-live in seconds for cached results.
    """

    def __init__(
        self,
        http_client: httpx.AsyncClient,
        cache: CacheBackend,
        semaphore: asyncio.Semaphore,
        request_timeout: float,
        cache_ttl: int,
    ) -> None:
        self._client = http_client
        self._cache = cache
        self._semaphore = semaphore
        self._timeout = request_timeout
        self._cache_ttl = cache_ttl

    async def audit(self, url: str) -> tuple[AuditResult, bool]:
        """Perform a URL audit, returning the result and whether it was cached.

        Args:
            url: The validated URL to audit.

        Returns:
            A tuple of (AuditResult, cached: bool).

        Raises:
            AuditError: On timeout, DNS failure, connection errors, or unexpected failures.
        """
        cache_key = self._make_cache_key(url)

        # Check cache
        cached_data = await self._cache.get(cache_key)
        if cached_data is not None:
            logger.info("cache_hit", url=url)
            return AuditResult(**cached_data), True

        logger.info("cache_miss", url=url)

        # Perform the audit with concurrency control
        result = await self._execute_audit(url)

        # Store in cache
        await self._cache.set(cache_key, result.model_dump(mode="json"), self._cache_ttl)

        return result, False

    async def _execute_audit(self, url: str) -> AuditResult:
        """Execute the HTTP request and build the audit result."""
        async with self._semaphore:
            try:
                start = time.monotonic()
                response = await self._client.get(
                    url,
                    follow_redirects=True,
                    timeout=self._timeout,
                )
                elapsed_ms = round((time.monotonic() - start) * 1000, 2)
            except httpx.TimeoutException as exc:
                raise AuditError(
                    code=ErrorCode.TIMEOUT,
                    message=f"Request to {url} timed out after {self._timeout}s",
                    status_code=504,
                ) from exc
            except httpx.ConnectError as exc:
                error_msg = str(exc).lower()
                if "name resolution" in error_msg or "getaddrinfo" in error_msg or "nodename nor servname" in error_msg:
                    raise AuditError(
                        code=ErrorCode.DNS_FAILURE,
                        message=f"DNS resolution failed for {url}",
                        status_code=502,
                    ) from exc
                raise AuditError(
                    code=ErrorCode.CONNECTION_REFUSED,
                    message=f"Connection refused for {url}",
                    status_code=502,
                ) from exc
            except httpx.HTTPError as exc:
                raise AuditError(
                    code=ErrorCode.INTERNAL_ERROR,
                    message=f"HTTP error while auditing {url}: {exc}",
                    status_code=502,
                ) from exc

        # Parse the response
        final_url = str(response.url)
        content_text = response.text

        return AuditResult(
            url=url,
            final_url=final_url,
            status_code=response.status_code,
            response_time_ms=elapsed_ms,
            https_enabled=final_url.startswith("https://"),
            redirect_count=len(response.history),
            page_title=self._extract_title(content_text),
            meta_description=self._extract_meta_description(content_text),
            content_length=self._get_content_length(response),
            server_header=response.headers.get("Server"),
            security_headers=self._collect_headers(response, SECURITY_HEADERS),
            cache_headers=self._collect_headers(response, CACHE_HEADERS),
            timestamp=datetime.now(timezone.utc),
        )

    @staticmethod
    def _make_cache_key(url: str) -> str:
        """Generate a deterministic cache key from a URL."""
        return f"audit:{hashlib.sha256(url.encode()).hexdigest()}"

    @staticmethod
    def _extract_title(html: str) -> str | None:
        """Extract the <title> content from HTML."""
        match = _TITLE_RE.search(html)
        return match.group(1).strip() if match else None

    @staticmethod
    def _extract_meta_description(html: str) -> str | None:
        """Extract the meta description content from HTML."""
        match = _META_DESC_RE.search(html) or _META_DESC_RE_ALT.search(html)
        return match.group(1).strip() if match else None

    @staticmethod
    def _get_content_length(response: httpx.Response) -> int | None:
        """Get content length from header or computed from body."""
        header_val = response.headers.get("Content-Length")
        if header_val:
            try:
                return int(header_val)
            except ValueError:
                return len(response.content) if response.content else None
        # Fall back to actual body length
        return len(response.content) if response.content else None

    @staticmethod
    def _collect_headers(
        response: httpx.Response,
        header_names: tuple[str, ...],
    ) -> dict[str, str | None]:
        """Collect specified headers from the response."""
        return {
            name: response.headers.get(name)
            for name in header_names
        }
