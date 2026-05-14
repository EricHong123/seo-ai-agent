"""Production middleware: rate limiting + API key authentication."""

import time
import asyncio
from collections import defaultdict
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from config.settings import settings


# ── Rate Limiter (Token Bucket) ─────────────────────────

class TokenBucket:
    def __init__(self, rate: int, burst: int):
        self.rate = rate          # tokens per second
        self.burst = burst        # max bucket size
        self.tokens = float(burst)
        self.last_refill = time.monotonic()

    def consume(self, tokens: int = 1) -> bool:
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
        self.last_refill = now
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False


class RateLimitMiddleware(BaseHTTPMiddleware):
    """In-memory per-IP rate limiting.

    Configurable limits per path prefix.
    Defaults are generous for local use, restrictive enough to prevent abuse.
    """

    # (path_prefix, rate_per_sec, burst)
    ENDPOINT_LIMITS = [
        ("/api/agent/run", 2, 5),      # 2 req/s, burst 5 → ~120/min max
        ("/kb/upload", 5, 10),          # 5 req/s, burst 10
        ("/settings", 1, 3),            # Settings — very restrictive
        ("/api/skills", 3, 8),          # Skill generation
        ("default", 10, 30),            # Everything else — generous
    ]

    def __init__(self, app):
        super().__init__(app)
        self._buckets: dict[str, TokenBucket] = {}
        self._cleanup_task = None

    def _get_bucket(self, key: str, rate: int, burst: int) -> TokenBucket:
        if key not in self._buckets:
            self._buckets[key] = TokenBucket(rate, burst)
        return self._buckets[key]

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        client_ip = request.client.host if request.client else "unknown"
        key = f"{client_ip}:{path}"

        # Find matching limit
        for prefix, rate, burst in self.ENDPOINT_LIMITS:
            if path.startswith(prefix):
                break
        else:
            rate, burst = 10, 30

        bucket = self._get_bucket(key, rate, burst)

        if not bucket.consume():
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again later."},
                headers={"Retry-After": str(int(1.0 / rate))},
            )

        response = await call_next(request)
        return response


# ── Auth Middleware ──────────────────────────────────────

# Protected paths that require authentication
PROTECTED_PREFIXES = [
    "/settings",
    "/api/agent/run",
    "/kb/upload",
    "/api/skills/pptx",
    "/api/skills/excel",
    "/api/skills/browser",
    "/api/skills/files",
    "/analytics",
    "/api/content",
]

# Paths always open (health, docs, UI, basic KB read)
PUBLIC_PREFIXES = [
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/static",
    "/",
    "/kb/files",
    "/kb/search",
    "/projects",
    "/api/skills/seo/status",
    "/api/skills/files",
]


class AuthMiddleware(BaseHTTPMiddleware):
    """Simple API key authentication.

    Configure API_KEY in .env. If not set, auth is disabled (dev mode).
    """

    def __init__(self, app):
        super().__init__(app)
        self.api_key = self._load_key()

    def _load_key(self):
        # Read from .env — same format as other settings
        import os
        from pathlib import Path
        env_path = Path(__file__).parent.parent.parent / ".env"
        if env_path.exists():
            for line in env_path.read_text().split("\n"):
                if line.startswith("API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
        return os.environ.get("API_KEY", "")

    async def dispatch(self, request: Request, call_next):
        # Skip if no key configured (dev mode)
        if not self.api_key:
            return await call_next(request)

        path = request.url.path

        # Allow public paths
        for prefix in PUBLIC_PREFIXES:
            if path.startswith(prefix):
                return await call_next(request)

        # Check if path is protected
        is_protected = any(path.startswith(p) for p in PROTECTED_PREFIXES)
        if not is_protected:
            return await call_next(request)

        # Verify API key
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
        else:
            token = request.query_params.get("api_key", "")

        if token != self.api_key:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing API key. Use Authorization: Bearer <key>"},
            )

        return await call_next(request)
