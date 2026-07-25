"""Cache backend implementations.

Provides a protocol for cache backends and two concrete implementations:
- RedisCacheBackend: Uses Redis (Upstash-compatible) for distributed caching.
- InMemoryCacheBackend: Simple dict-based fallback for local development.
"""

from __future__ import annotations

import json
import time
from typing import Any, Protocol

import structlog

logger = structlog.stdlib.get_logger(__name__)


class CacheBackend(Protocol):
    """Abstract cache backend interface."""

    async def get(self, key: str) -> dict[str, Any] | None:
        """Retrieve a cached value by key, or None if missing / expired."""
        ...

    async def set(self, key: str, value: dict[str, Any], ttl: int) -> None:
        """Store a value under key with a time-to-live in seconds."""
        ...

    async def close(self) -> None:
        """Release any underlying resources."""
        ...


class RedisCacheBackend:
    """Redis-backed cache, compatible with Upstash (TLS) connections."""

    def __init__(self, redis_url: str) -> None:
        import redis.asyncio as aioredis

        self._client = aioredis.from_url(
            redis_url,
            decode_responses=True,
        )

    async def get(self, key: str) -> dict[str, Any] | None:
        """Retrieve a value from Redis."""
        try:
            raw = await self._client.get(key)
            if raw is None:
                return None
            return json.loads(raw)
        except Exception:
            logger.warning("redis_get_failed", key=key, exc_info=True)
            return None

    async def set(self, key: str, value: dict[str, Any], ttl: int) -> None:
        """Store a JSON-serialized value in Redis with TTL."""
        try:
            await self._client.set(key, json.dumps(value, default=str), ex=ttl)
        except Exception:
            logger.warning("redis_set_failed", key=key, exc_info=True)

    async def close(self) -> None:
        """Close the Redis connection pool."""
        await self._client.aclose()


class InMemoryCacheBackend:
    """Simple in-memory cache with TTL support.

    Intended as a fallback when Redis is unavailable. Cache is not shared
    across processes and is lost on restart.
    """

    def __init__(self) -> None:
        self._store: dict[str, tuple[dict[str, Any], float]] = {}

    async def get(self, key: str) -> dict[str, Any] | None:
        """Retrieve a value if it exists and has not expired."""
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if time.monotonic() > expires_at:
            del self._store[key]
            return None
        return value

    async def set(self, key: str, value: dict[str, Any], ttl: int) -> None:
        """Store a value with an expiry time."""
        self._store[key] = (value, time.monotonic() + ttl)

    async def close(self) -> None:
        """Clear the in-memory store."""
        self._store.clear()


async def create_cache_backend(redis_url: str | None) -> CacheBackend:
    """Factory that creates the appropriate cache backend.

    Attempts to connect to Redis if a URL is provided. Falls back to
    an in-memory backend on failure or when no URL is given.
    """
    if redis_url:
        try:
            backend = RedisCacheBackend(redis_url)
            # Verify connectivity
            await backend._client.ping()
            logger.info("cache_backend_initialized", backend="redis")
            return backend
        except Exception:
            logger.warning(
                "redis_connection_failed_falling_back_to_memory",
                exc_info=True,
            )

    logger.info("cache_backend_initialized", backend="in_memory")
    return InMemoryCacheBackend()
