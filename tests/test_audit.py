from __future__ import annotations

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.errors import ErrorCode


class DummyResponse:
    def __init__(self, status_code=200, text="<html><title>Example</title></html>", headers=None):
        self.status_code = status_code
        self.text = text
        self.content = text.encode("utf-8")
        self.headers = headers or {}
        self.history = []
        self.url = "https://example.com"


@pytest.fixture
def patched_client(monkeypatch, app):
    class DummyAsyncClient:
        def __init__(self):
            self.calls = []

        async def get(self, url, follow_redirects=True, timeout=None):
            self.calls.append((url, follow_redirects, timeout))
            return DummyResponse()

        async def aclose(self):
            return None

    client = DummyAsyncClient()
    app.state.audit_service = None
    monkeypatch.setattr("app.main.httpx.AsyncClient", lambda *args, **kwargs: client)
    return client


def test_audit_valid_url(client: TestClient) -> None:
    response = client.post(
        "/audit",
        json={"url": "https://example.com"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["status_code"] == 200
    assert payload["data"]["url"] == "https://example.com"


def test_audit_invalid_url(client: TestClient) -> None:
    response = client.post(
        "/audit",
        json={"url": "ftp://example.com"},
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["error"]["code"] == ErrorCode.INVALID_URL


def test_audit_timeout(client: TestClient) -> None:
    from app.main import create_app
    from app.services.audit import AuditService
    from app.cache.backend import InMemoryCacheBackend
    import asyncio

    class TimeoutClient:
        async def get(self, url, follow_redirects=True, timeout=None):
            raise httpx.TimeoutException("timed out")

        async def aclose(self):
            return None

    app = create_app()
    app.state.audit_service = AuditService(
        http_client=TimeoutClient(),
        cache=InMemoryCacheBackend(),
        semaphore=asyncio.Semaphore(1),
        request_timeout=0.1,
        cache_ttl=60,
    )
    with TestClient(app) as test_client:
        response = test_client.post("/audit", json={"url": "https://example.com"})

    assert response.status_code == 504
    assert response.json()["error"]["code"] == ErrorCode.TIMEOUT


def test_audit_dns_failure(client: TestClient) -> None:
    from app.main import create_app
    from app.services.audit import AuditService
    from app.cache.backend import InMemoryCacheBackend
    import asyncio

    class DnsClient:
        async def get(self, url, follow_redirects=True, timeout=None):
            raise httpx.ConnectError("name resolution failed")

        async def aclose(self):
            return None

    app = create_app()
    app.state.audit_service = AuditService(
        http_client=DnsClient(),
        cache=InMemoryCacheBackend(),
        semaphore=asyncio.Semaphore(1),
        request_timeout=0.1,
        cache_ttl=60,
    )
    with TestClient(app) as test_client:
        response = test_client.post("/audit", json={"url": "https://example.com"})

    assert response.status_code == 502
    assert response.json()["error"]["code"] == ErrorCode.DNS_FAILURE


def test_audit_connection_refused(client: TestClient) -> None:
    from app.main import create_app
    from app.services.audit import AuditService
    from app.cache.backend import InMemoryCacheBackend
    import asyncio

    class ConnectClient:
        async def get(self, url, follow_redirects=True, timeout=None):
            raise httpx.ConnectError("connection refused")

        async def aclose(self):
            return None

    app = create_app()
    app.state.audit_service = AuditService(
        http_client=ConnectClient(),
        cache=InMemoryCacheBackend(),
        semaphore=asyncio.Semaphore(1),
        request_timeout=0.1,
        cache_ttl=60,
    )
    with TestClient(app) as test_client:
        response = test_client.post("/audit", json={"url": "https://example.com"})

    assert response.status_code == 502
    assert response.json()["error"]["code"] == ErrorCode.CONNECTION_REFUSED
