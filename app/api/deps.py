"""Shared service singletons and FastAPI dependency providers.

All services are created once at import time and shared across the application.
This avoids duplicate Twilio clients, Redis connections, and OpenAI clients.
"""
from __future__ import annotations

from functools import lru_cache

from redis.asyncio import Redis, from_url as redis_from_url

from app.config import get_settings
from app.core.idempotency import IdempotencyService
from app.services.ai_service import AIService
from app.services.campaign_service import CampaignService
from app.services.scheduling_service import SchedulingService
from app.services.sms_service import SMSService


@lru_cache
def get_redis_client() -> Redis:
    settings = get_settings()
    return redis_from_url(settings.redis_url, decode_responses=True)


@lru_cache
def get_sms_service() -> SMSService:
    return SMSService()


@lru_cache
def get_ai_service() -> AIService:
    return AIService()


@lru_cache
def get_scheduling_service() -> SchedulingService:
    return SchedulingService()


@lru_cache
def get_idempotency_service() -> IdempotencyService:
    return IdempotencyService(redis_client=get_redis_client())


@lru_cache
def get_campaign_service() -> CampaignService:
    return CampaignService()


def get_conversation_service():
    """Import here to avoid circular dependency."""
    from app.services.conversation_service import ConversationService

    return ConversationService(
        ai_service=get_ai_service(),
        scheduling_service=get_scheduling_service(),
        sms_service=get_sms_service(),
        redis_client=get_redis_client(),
    )
