import asyncio
import time
from collections import defaultdict, deque

from fastapi import Depends, Request

from app.core.errors import AppError


class RateLimiter:
    """Simple async sliding-window in-memory rate limiter."""

    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = asyncio.Lock()

    async def check(self, key: str, max_requests: int, window_seconds: int) -> None:
        now = time.monotonic()
        cutoff = now - window_seconds
        async with self._lock:
            bucket = self._hits[key]
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if len(bucket) >= max_requests:
                raise AppError(
                    code="RATE_LIMIT_EXCEEDED",
                    message="Too many requests. Please try again later.",
                    status_code=429,
                )
            bucket.append(now)

    async def reset(self) -> None:
        async with self._lock:
            self._hits.clear()


rate_limiter = RateLimiter()


def rate_limit(max_requests: int = 20, window_seconds: int = 60):
    async def _dependency(request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        key = f"{request.url.path}:{client_ip}"
        await rate_limiter.check(key, max_requests, window_seconds)

    return Depends(_dependency)
