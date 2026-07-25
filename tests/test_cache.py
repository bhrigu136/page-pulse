from __future__ import annotations

import asyncio

from fastapi.testclient import TestClient

from app.cache.backend import InMemoryCacheBackend
from app.main import create_app
from app.schemas.response import AuditResult
from app.services.audit import AuditService


class CacheableClient:
    def __init__(self) -> None:
        self.calls = 0

    async def get(self, url, follow_redirects=True, timeout=None):
        self.calls += 1
        class Response:
            status_code = 200
            text = "<html><title>Cached</title></html>"
            content = text.encode("utf-8")
            headers = {}
            history = []
            url = "https://example.com"
        return Response()

    async def aclose(self):
        return None


def test_cache_miss_then_hit() -> None:
    client = CacheableClient()
    app = create_app()
    app.state.audit_service = AuditService(
        http_client=client,
        cache=InMemoryCacheBackend(),
        semaphore=asyncio.Semaphore(1),
        request_timeout=0.1,
        cache_ttl=60,
    )

    with TestClient(app) as test_client:
        first = test_client.post("/audit", json={"url": "https://example.com"})
        second = test_client.post("/audit", json={"url": "https://example.com"})

    assert first.json()["cached"] is False
    assert second.json()["cached"] is True
    assert client.calls == 1


def test_cache_ttl_expiry() -> None:
    client = CacheableClient()
    cache = InMemoryCacheBackend()
    app = create_app()
    app.state.audit_service = AuditService(
        http_client=client,
        cache=cache,
        semaphore=asyncio.Semaphore(1),
        request_timeout=0.1,
        cache_ttl=1,
    )

    with TestClient(app) as test_client:
        first = test_client.post("/audit", json={"url": "https://example.com"})
        import time
        time.sleep(1.1)
        second = test_client.post("/audit", json={"url": "https://example.com"})

    assert first.json()["cached"] is False
    assert second.json()["cached"] is False
    assert client.calls == 2
