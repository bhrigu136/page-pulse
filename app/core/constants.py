"""Application-wide constants."""

APP_VERSION = "1.0.0"

# Security headers to inspect during audit
SECURITY_HEADERS = (
    "Strict-Transport-Security",
    "X-Content-Type-Options",
    "X-Frame-Options",
    "Content-Security-Policy",
    "X-XSS-Protection",
    "Referrer-Policy",
    "Permissions-Policy",
)

# Cache-related headers to inspect during audit
CACHE_HEADERS = (
    "Cache-Control",
    "ETag",
    "Last-Modified",
    "Expires",
    "Age",
)
