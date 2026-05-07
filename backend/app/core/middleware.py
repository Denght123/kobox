from collections import defaultdict, deque
from time import monotonic
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import Settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, settings: Settings) -> None:
        super().__init__(app)
        self.settings = settings

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
        response.headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        if self.settings.is_production:
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, settings: Settings) -> None:
        super().__init__(app)
        self.settings = settings
        self.window_seconds = max(1, settings.rate_limit_window_seconds)
        self.requests_by_key: defaultdict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not self.settings.enable_rate_limit or self._is_excluded_path(request.url.path):
            return await call_next(request)

        limit = self._limit_for_path(request.url.path)
        if limit > 0 and self._is_limited(request, limit):
            return JSONResponse(
                status_code=429,
                content={
                    "code": "rate_limited",
                    "message": "Too many requests. Please wait a moment and try again.",
                },
                headers={"Retry-After": str(self.window_seconds)},
            )
        return await call_next(request)

    def _is_limited(self, request: Request, limit: int) -> bool:
        now = monotonic()
        key = f"{self._client_ip(request)}:{self._bucket_for_path(request.url.path)}"
        timestamps = self.requests_by_key[key]
        while timestamps and now - timestamps[0] > self.window_seconds:
            timestamps.popleft()
        if len(timestamps) >= limit:
            return True
        timestamps.append(now)
        if len(self.requests_by_key) > 20_000:
            self._drop_stale_buckets(now)
        return False

    def _drop_stale_buckets(self, now: float) -> None:
        stale_keys = [
            key
            for key, timestamps in self.requests_by_key.items()
            if not timestamps or now - timestamps[-1] > self.window_seconds
        ]
        for key in stale_keys[:5_000]:
            self.requests_by_key.pop(key, None)

    def _limit_for_path(self, path: str) -> int:
        if path.startswith("/api/auth/"):
            return self.settings.rate_limit_auth_requests
        if path.startswith("/api/anime/search"):
            return self.settings.rate_limit_search_requests
        if path.startswith("/api/"):
            return self.settings.rate_limit_api_requests
        return 0

    @staticmethod
    def _bucket_for_path(path: str) -> str:
        if path.startswith("/api/auth/"):
            return "auth"
        if path.startswith("/api/anime/search"):
            return "search"
        return "api"

    @staticmethod
    def _is_excluded_path(path: str) -> bool:
        return path in {"/health", "/health/live", "/health/ready"} or path.startswith("/uploads/")

    @staticmethod
    def _client_ip(request: Request) -> str:
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"
