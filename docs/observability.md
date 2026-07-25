# Observability

## Current implementation

### Logging strategy

The application configures structlog in app/utils/logging.py. Logging is currently emitted to stdout with a formatter that supports either pretty console output in development or JSON output in production.

The current implementation writes structured log events for:

- application startup and shutdown,
- request receipt,
- cache hits and misses,
- audit completion,
- audit failure.

### Structured logs

Structured logging is implemented using structlog processors such as:

- log level,
- logger name,
- timestamp,
- stack info,
- request context.

The middleware binds a request_id into the structlog context for each request, allowing the logs for a single request to be correlated.

### Request IDs

Each incoming request receives a UUID value stored on request.state and emitted in the X-Request-ID response header. The request ID is also bound into structlog context for log correlation.

### Health endpoint

The GET /health endpoint returns a simple health payload with:

- status,
- timestamp,
- version.

This endpoint is suitable for basic liveness checks and deployment health verification.

## Monitoring recommendations

The following signals are worth collecting in a production environment:

- request count by endpoint,
- error count by error code,
- audit latency,
- cache hit rate,
- rate-limit events,
- outbound HTTP request failure rates.

## Metrics worth collecting

The current implementation does not emit metrics directly, but the following values would be useful to collect:

- requests per second for /health and /audit,
- response status distribution,
- p95 latency for /audit,
- number of cache hits and misses,
- number of timeout, DNS failure, and connection refusal events,
- maximum concurrent in-flight audits.

## Suggested dashboards

A practical dashboard would include:

- request volume and status codes,
- audit latency trend,
- cache hit rate over time,
- rate-limit events,
- outbound error counts by failure class.

## Suggested alerts

Recommended alerts include:

- error rate spike for /audit,
- sustained increase in timeout failures,
- cache hit rate dropping below an expected threshold,
- repeated rate-limit events,
- application health endpoint failing.

## Rollback strategy

The current implementation does not include a dedicated rollback mechanism beyond restarting the service or rolling back the deployment artifact. In a deployment environment, rollback would mean reverting the application version or deployment configuration and allowing the service to restart.

## Incident response workflow

A basic workflow for incidents would be:

1. Inspect logs for the request_id and recent error events.
2. Check the health endpoint response.
3. Determine whether the failure is caused by the target site, the cache backend, the network path, or the application itself.
4. Apply a mitigation such as restoring Redis availability, adjusting configuration, or rolling back the deployment.
5. Verify the health endpoint and repeat a known-good audit request.

## Current observability limitations

The current implementation has the following limitations:

- no external metrics backend is configured,
- no tracing system is wired into the service,
- no structured alerting pipeline is defined,
- logs are emitted to stdout but are not shown to be forwarded to a logging platform.

## Future improvements

Recommended future enhancements include:

- integrate a metrics exporter such as Prometheus,
- add distributed tracing for outbound HTTP requests,
- forward logs to a centralized logging backend,
- add synthetic checks for /health and /audit,
- expose more detailed operational health information, such as cache backend status.
