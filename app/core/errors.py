"""Application error codes and custom exception types."""

from enum import StrEnum


class ErrorCode(StrEnum):
    """Canonical error codes used in all error responses."""

    INVALID_URL = "INVALID_URL"
    TIMEOUT = "TIMEOUT"
    DNS_FAILURE = "DNS_FAILURE"
    CONNECTION_REFUSED = "CONNECTION_REFUSED"
    RATE_LIMITED = "RATE_LIMITED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class AuditError(Exception):
    """Domain exception raised during URL audit operations.

    Attributes:
        code: Machine-readable error code from ``ErrorCode``.
        message: Human-readable error description.
        status_code: HTTP status code to return to the client.
    """

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        status_code: int = 400,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)
