from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.rate_limit import RateLimiter, get_client_ip


def _request(headers: dict[str, str] | None = None, host: str = "127.0.0.1"):
    return SimpleNamespace(headers=headers or {}, client=SimpleNamespace(host=host))


def test_get_client_ip_prefers_forwarded_header() -> None:
    request = _request(headers={"X-Forwarded-For": "203.0.113.10, 10.0.0.2"})
    assert get_client_ip(request) == "203.0.113.10"


def test_rate_limiter_blocks_when_limit_reached() -> None:
    limiter = RateLimiter()
    key = "login:127.0.0.1"
    limiter.check(key, max_requests=2, window_seconds=60)
    limiter.check(key, max_requests=2, window_seconds=60)
    with pytest.raises(HTTPException) as exc:
        limiter.check(key, max_requests=2, window_seconds=60)
    assert exc.value.status_code == 429
