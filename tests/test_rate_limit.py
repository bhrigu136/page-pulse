from __future__ import annotations

from fastapi.testclient import TestClient

from app.config import get_settings


def test_rate_limit_exceeded(client: TestClient) -> None:
    settings = get_settings()
    settings.rate_limit = "1/minute"

    for _ in range(2):
        response = client.post(
            "/audit",
            json={"url": "https://example.com"},
        )

    assert response.status_code == 429
