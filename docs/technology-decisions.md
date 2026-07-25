# Technology Decisions

This document records the major implementation choices present in the current codebase. Each decision is written as a lightweight Technology Decision Record (TDR) based on the code and configuration that exist today.

## TDR-001: FastAPI

- Status: Accepted
- Context: The project exposes HTTP endpoints and needs request handling, routing, and exception handling.
- Decision: Use FastAPI for the API surface.
- Why it was selected: The repository implements FastAPI routes, request validation, and response models directly in the application.
- Alternatives considered: None documented in the repository.
- Trade-offs: FastAPI is a light-weight choice for the current scope, but the current implementation is intentionally simple and does not include advanced API gateway features.
- Benefits: The implementation gains straightforward route definitions, automatic request validation through Pydantic, and a familiar Python web framework for tests and local execution.
- Limitations: The current implementation does not include authentication, API versioning, or a deeper middleware framework beyond the existing request ID middleware.

## TDR-002: httpx

- Status: Accepted
- Context: The service needs to perform outbound HTTP requests to audit a target URL.
- Decision: Use httpx as the asynchronous HTTP client.
- Why it was selected: The audit service uses httpx.AsyncClient directly for outbound GET requests with timeouts and redirects enabled.
- Alternatives considered: None documented in the repository.
- Trade-offs: httpx is well suited for async usage and matches the service’s current design, but it is currently used only for the direct audit flow and not for broader integration needs.
- Benefits: The implementation can support asynchronous request execution and structured timeout handling.
- Limitations: The service currently does not implement retries or sophisticated backoff behavior.

## TDR-003: Redis

- Status: Accepted
- Context: The service needs a cache layer and a deployment-friendly optional backing store.
- Decision: Implement a cache backend abstraction with Redis as the primary distributed cache option and in-memory as a fallback.
- Why it was selected: The implementation includes a RedisCacheBackend class and the application configuration supports REDIS_URL.
- Alternatives considered: In-memory-only caching was implemented as the fallback path when Redis is unavailable.
- Trade-offs: Redis enables persistent cache state for a deployment environment, but the current code still falls back to in-memory storage when Redis is absent or fails.
- Benefits: The service can use a shared cache backend when Redis is configured.
- Limitations: The current implementation does not validate Redis availability beyond a basic ping attempt during backend initialization.

## TDR-004: Pydantic

- Status: Accepted
- Context: The service needs explicit request and response models.
- Decision: Use Pydantic v2 models for request validation and response serialization.
- Why it was selected: The repository contains AuditRequest, AuditResponse, AuditResult, ErrorResponse, and HealthResponse models. The request body is validated through a field validator.
- Alternatives considered: None documented in the repository.
- Trade-offs: Pydantic provides strong typing and validation but adds a dependency on model definitions that must stay consistent with the service logic.
- Benefits: Validation errors are structured and route handlers can rely on typed models.
- Limitations: The current implementation does not expose richer validation handling beyond the existing URL validator and default response envelopes.

## TDR-005: Structlog

- Status: Accepted
- Context: The service needs structured logs and request-scoped context.
- Decision: Use structlog for logging setup and structured log emission.
- Why it was selected: app/utils/logging.py configures structlog processors and the middleware binds request IDs into the logging context.
- Alternatives considered: None documented in the repository.
- Trade-offs: Structlog improves structured logging, but the current implementation uses it primarily for simple event logging rather than a full observability stack.
- Benefits: Logs can carry structured fields such as request_id and event names.
- Limitations: The current project does not yet route logs to an external platform or collector.

## TDR-006: SlowAPI

- Status: Accepted
- Context: The service needs basic request rate limiting for the audit endpoint.
- Decision: Use SlowAPI for rate limiting support.
- Why it was selected: The planned architecture mentioned SlowAPI and the repository currently implements a simple in-route rate limit check without the library. The current implementation uses a lightweight custom limiter rather than the SlowAPI integration described in the earlier plan.
- Alternatives considered: A custom in-process limiter was implemented instead of full SlowAPI integration.
- Trade-offs: The custom approach is smaller and fits the current codebase, but it is less feature-rich than a full SlowAPI integration.
- Benefits: The service can enforce a basic limit for repeated requests.
- Limitations: The current implementation does not provide the broader rate-limiting features that a full SlowAPI integration would offer.

## TDR-007: Pytest

- Status: Accepted
- Context: The project needs automated verification for endpoints, middleware, cache behavior, and error handling.
- Decision: Use pytest as the test runner.
- Why it was selected: Tests exist under tests/ and the GitHub Actions workflow runs pytest.
- Alternatives considered: None documented in the repository.
- Trade-offs: pytest fits the current Python codebase well, but the current suite is focused on the implemented behaviors rather than exhaustive end-to-end coverage.
- Benefits: The project has a repeatable test workflow and automated verification for the main service behaviors.
- Limitations: The present tests cover the main flows but do not test every potential edge case.

## TDR-008: GitHub Actions

- Status: Accepted
- Context: The repository needs a simple continuous integration workflow.
- Decision: Use GitHub Actions for CI.
- Why it was selected: The repository contains a workflow file under .github/workflows/ci.yml that installs dependencies and runs pytest.
- Alternatives considered: None documented in the repository.
- Trade-offs: GitHub Actions is straightforward for the current repository size, but the workflow is minimal.
- Benefits: The project has an automated CI entry point for pull requests and pushes.
- Limitations: The current workflow does not include code coverage reporting or deployment automation.

## TDR-009: Render

- Status: Accepted
- Context: The service needs a simple deployment target.
- Decision: Use Render via the repository’s render.yaml configuration.
- Why it was selected: The repository includes a Render blueprint for a single web service.
- Alternatives considered: None documented in the repository.
- Trade-offs: Render is a simple deployment target for a small service, but the current deployment configuration is basic and does not include advanced deployment health checks beyond the application’s own /health endpoint.
- Benefits: The project can be deployed with a minimal blueprint and a standard Python web start command.
- Limitations: The current deployment model does not include horizontal scaling logic or dedicated environment management beyond the provided environment variables.
