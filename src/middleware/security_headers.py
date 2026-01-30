from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Equivalent to helmet in Express — sets common security headers."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "0"
        response.headers["Strict-Transport-Security"] = (
            "max-age=15552000; includeSubDomains"
        )
        response.headers["Referrer-Policy"] = "no-referrer"

        # Skip CSP for Swagger docs (needs inline scripts + CDN assets)
        if not request.url.path.startswith("/docs") and not request.url.path.startswith("/openapi"):
            response.headers["Content-Security-Policy"] = "default-src 'self'"

        return response
