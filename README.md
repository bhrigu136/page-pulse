# Page Pulse

Page Pulse is a FastAPI-based URL audit service that fetches a target URL, extracts useful metadata, supports cache-backed responses, and returns structured JSON responses. It is designed for local development and deployment to Render.

## Features

- FastAPI application with health and audit endpoints
- Request ID middleware for traceability
- In-memory cache with Redis fallback support
- Structured error responses with machine-readable codes
- Lightweight audit metadata extraction from HTML responses
- Test coverage for health, middleware, audit errors, cache behavior, and rate limiting

## Quick start

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt -r requirements-dev.txt
```

3. Start the development server:

```bash
uvicorn app.main:app --reload
```

4. Visit the health endpoint:

```bash
curl http://localhost:8000/health
```

## Environment variables

Copy [.env.example](.env.example) to .env and adjust values as needed.

| Variable | Description | Default |
| --- | --- | --- |
| REDIS_URL | Optional Redis connection URL | None |
| CACHE_TTL | Cache TTL in seconds | 300 |
| REQUEST_TIMEOUT | Per-request timeout in seconds | 10.0 |
| MAX_CONCURRENT_REQUESTS | Max outbound concurrent requests | 10 |
| RATE_LIMIT | Rate limit for POST /audit | 10/minute |
| LOG_LEVEL | Logging level | INFO |
| ENVIRONMENT | Runtime environment | production |

## API usage

### Health check

```bash
curl http://localhost:8000/health
```

### Audit a URL

```bash
curl -X POST http://localhost:8000/audit \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com"}'
```

## Testing

Run the test suite:

```bash
pytest -v --tb=short
```

## Deployment

The repository includes a Render blueprint in [render.yaml](render.yaml) and a Procfile for deployment.

## Architecture summary

- API layer: [app/api/routes.py](app/api/routes.py)
- Service layer: [app/services/audit.py](app/services/audit.py)
- Cache layer: [app/cache/backend.py](app/cache/backend.py)
- Middleware: [app/middleware/request_id.py](app/middleware/request_id.py)
