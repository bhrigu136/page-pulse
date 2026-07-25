# Failure Analysis

This document records realistic failure scenarios for the current implementation and how the repository handles them today.

## Redis unavailable

- Symptoms: The application continues to run but the cache backend falls back to in-memory storage.
- Root cause: The service attempts to initialize Redis only when REDIS_URL is provided. If Redis is unavailable or the connection fails, the application logs a warning and uses InMemoryCacheBackend.
- Current handling: The cache factory catches exceptions from the Redis backend initialization path and falls back to memory.
- User impact: Requests still succeed, but cache state is not shared across instances and is lost on restart.
- Recovery strategy: Restart the application with a valid Redis configuration or rely on the in-memory cache until the dependency is restored.
- Future improvements: Add explicit health checks for Redis and expose cache-backend state to operators.

## External website timeout

- Symptoms: The audit request fails with a structured 504 response.
- Root cause: The outbound HTTP request to the target URL exceeds the configured request timeout.
- Current handling: The audit service catches httpx.TimeoutException and raises AuditError with the TIMEOUT code and status code 504.
- User impact: The client receives a structured error payload with the request_id.
- Recovery strategy: Retry manually or adjust the timeout configuration if the target site is slow.
- Future improvements: Add retry logic with backoff and circuit-breaker behavior.

## DNS lookup failure

- Symptoms: The audit request returns a structured 502 response with the DNS_FAILURE code.
- Root cause: The service experiences a DNS resolution failure while attempting the outbound HTTP request.
- Current handling: The audit service checks the exception text for DNS-related indicators and raises AuditError with the DNS_FAILURE code and status code 502.
- User impact: The client receives an error response rather than a success payload.
- Recovery strategy: Validate the target URL and the network environment.
- Future improvements: Add more explicit upstream network diagnostics and retry strategies.

## Connection refused

- Symptoms: The audit request returns a structured 502 response with the CONNECTION_REFUSED code.
- Root cause: The outbound HTTP connection is rejected by the remote host or the network path.
- Current handling: The audit service catches httpx.ConnectError and maps it to the CONNECTION_REFUSED error code when the error is not recognized as a DNS failure.
- User impact: The client receives an error envelope with the request ID.
- Recovery strategy: Confirm the remote endpoint is reachable and the network path is healthy.
- Future improvements: Distinguish additional connection failure classes and add diagnostic context.

## Rate limit exceeded

- Symptoms: The audit endpoint returns a 429 response.
- Root cause: The route uses an in-process rate limiter keyed by client IP and the request count exceeds the configured limit within the configured window.
- Current handling: The route raises AuditError with the RATE_LIMITED code and the HTTP status code 429.
- User impact: The caller sees a structured error response and cannot submit further audit requests until the window resets.
- Recovery strategy: Wait for the rate-limit window to expire or adjust the limit configuration.
- Future improvements: Use a shared rate-limit store so limits work correctly across multiple instances.

## Invalid URL

- Symptoms: The client receives a 422 response.
- Root cause: The request body contains a URL that does not use http or https or does not include a valid host.
- Current handling: The request model validates the URL and raises a Pydantic validation error. The application converts this into a structured response with the INVALID_URL code.
- User impact: The request fails fast before an outbound network call is made.
- Recovery strategy: Correct the URL format and resubmit the request.
- Future improvements: Return more explicit field-level validation feedback.

## Render restart

- Symptoms: The service temporarily becomes unavailable and existing in-memory cache entries are lost.
- Root cause: The implementation uses an in-memory cache, so cache state is not persisted across restarts.
- Current handling: The application restarts cleanly and serves new requests; the current route handlers and service are stateless beyond the in-memory cache.
- User impact: New requests may experience cache misses until the cache is repopulated.
- Recovery strategy: Restarting the service recovers normal operation, but cache warm-up is not automatic.
- Future improvements: Introduce persistent cache storage or an external state store.

## Cache corruption

- Symptoms: The cache backend can return malformed data, which can fail the AuditResult model construction.
- Root cause: The repository does not include explicit validation around cached payload integrity beyond using the model constructor when a cached value is returned.
- Current handling: The service returns the cached data as an AuditResult model and depends on the model to validate the structure.
- User impact: A malformed cache entry could cause a runtime error during deserialization.
- Recovery strategy: The current implementation does not include a dedicated recovery path beyond normal cache miss behavior.
- Future improvements: Add checksum validation or explicit cache-entry validation before use.

## Unexpected exception

- Symptoms: An uncaught exception can surface as a generic server error.
- Root cause: The repository defines explicit handling for AuditError and validation errors, but the service does not include a general-purpose exception handler for unexpected exceptions.
- Current handling: The current implementation does not show a dedicated generic exception handler in the main application file.
- User impact: Unexpected failures may produce a generic FastAPI error response rather than a consistent envelope.
- Recovery strategy: Review the application logs and address the underlying exception.
- Future improvements: Add a general exception handler that maps unexpected exceptions to a structured error response.
