# Page Pulse API

## Endpoints

### GET /health
Returns a simple health check payload.

Example:

```bash
curl http://localhost:8000/health
```

### POST /audit
Audits a URL and returns response metadata, headers, and cache status.

Example:

```bash
curl -X POST http://localhost:8000/audit \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://example.com"}'
```

### Response envelope

Successful response:

```json
{
  "success": true,
  "data": {
    "url": "https://example.com",
    "final_url": "https://example.com",
    "status_code": 200,
    "response_time_ms": 32.1,
    "https_enabled": true,
    "redirect_count": 0,
    "page_title": "Example",
    "meta_description": null,
    "content_length": 1256,
    "server_header": "nginx",
    "security_headers": {},
    "cache_headers": {},
    "timestamp": "2026-07-25T00:00:00Z"
  },
  "cached": false,
  "request_id": "uuid"
}
```
