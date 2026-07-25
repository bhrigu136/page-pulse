"""Request schemas for the audit API."""

from pydantic import BaseModel, field_validator
from urllib.parse import urlparse


class AuditRequest(BaseModel):
    """Input schema for the POST /audit endpoint.

    Accepts a URL string and validates that it uses HTTP or HTTPS.
    """

    url: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Ensure the URL has a valid HTTP(S) scheme and a non-empty host."""
        v = v.strip()
        parsed = urlparse(v)
        if parsed.scheme not in ("http", "https"):
            raise ValueError("URL must use http or https scheme")
        if not parsed.netloc:
            raise ValueError("URL must include a valid host")
        return v
