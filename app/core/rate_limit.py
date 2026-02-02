import time
from collections import defaultdict, deque
from typing import Deque

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.requests: dict[str, Deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window = settings.rate_limit_window_seconds
        limit = settings.rate_limit_requests
        timestamps = self.requests[client_ip]

        while timestamps and timestamps[0] <= now - window:
            timestamps.popleft()

        if len(timestamps) >= limit:
            return JSONResponse(
                {"detail": "Rate limit exceeded"}, status_code=429
            )

        timestamps.append(now)
        return await call_next(request)
