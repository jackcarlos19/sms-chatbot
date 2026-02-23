"""Simple in-memory sliding-window rate limiter."""
from __future__ import annotations

import time
from collections import defaultdict

from fastapi import HTTPException, Request


class RateLimiter:
    def __init__(self) -> None:
        self._windows: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str, max_requests: int, window_seconds: int) -> None:
        now = time.monotonic()
        cutoff = now - window_seconds
        hits = self._windows[key]
        self._windows[key] = [t for t in hits if t > cutoff]
        if len(self._windows[key]) >= max_requests:
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later.",
            )
        self._windows[key].append(now)


_limiter = RateLimiter()


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit(request: Request, prefix: str, max_requests: int, window: int) -> None:
    key = f"{prefix}:{get_client_ip(request)}"
    _limiter.check(key, max_requests, window)
