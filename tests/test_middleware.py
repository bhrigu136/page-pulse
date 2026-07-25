from __future__ import annotations

from fastapi.testclient import TestClient


def test_request_id_present(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"]


def test_request_id_unique(client: TestClient) -> None:
    first = client.get("/health")
    second = client.get("/health")

    assert first.headers["X-Request-ID"] != second.headers["X-Request-ID"]
