from __future__ import annotations

from redis.asyncio import Redis, from_url as redis_from_url

from app.config import get_settings


class IdempotencyService:
    def __init__(self, redis_client: Redis | None = None, ttl_seconds: int = 3600) -> None:
        settings = get_settings()
        self._redis = redis_client or redis_from_url(settings.redis_url, decode_responses=True)
        self._ttl_seconds = ttl_seconds

    @staticmethod
    def _key(sms_sid: str) -> str:
        return f"message:{sms_sid}"

    async def is_duplicate(self, sms_sid: str) -> bool:
        if not sms_sid:
            return False
        return bool(await self._redis.exists(self._key(sms_sid)))

    async def mark_processed(self, sms_sid: str) -> None:
        if not sms_sid:
            return
        await self._redis.set(self._key(sms_sid), "processed", ex=self._ttl_seconds)

    async def close(self) -> None:
        await self._redis.aclose()
