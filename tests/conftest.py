from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.schemas.response import AuditResult


class StubAuditService:
    def __init__(self, result: AuditResult | None = None, error: Exception | None = None) -> None:
        self.result = result
        self.error = error

    async def audit(self, url: str):
        if self.error is not None:
            raise self.error
        if self.result is None:
            self.result = AuditResult(
                url=url,
                final_url=url,
                status_code=200,
                response_time_ms=12.3,
                https_enabled=True,
                redirect_count=0,
                page_title="Example",
                meta_description="Example page",
                content_length=10,
                server_header="nginx",
                security_headers={},
                cache_headers={},
                timestamp=datetime.now(timezone.utc),
            )
        return self.result, False


@pytest.fixture
def app():
    app = create_app()
    app.state.audit_service = StubAuditService()
    return app


@pytest.fixture
def client(app):
    with TestClient(app) as test_client:
        yield test_client
