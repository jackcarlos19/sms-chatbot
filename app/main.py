from __future__ import annotations

import uuid

import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from redis.asyncio import from_url as redis_from_url
from sqlalchemy import text

from app.api.admin import router as admin_router
from app.api.webhooks import router as webhooks_router
from app.config import get_settings
from app.core.exceptions import SMSChatbotError
from app.core.logging import configure_structured_logging
from app.database import AsyncSessionFactory
from app.services.sms_service import SMSService

settings = get_settings()
configure_structured_logging()
log = structlog.get_logger(__name__)
sms_service = SMSService()
app = FastAPI(title="SMS Chatbot API")
app.include_router(webhooks_router)
app.include_router(admin_router)


@app.middleware("http")
async def attach_correlation_id(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    request.state.correlation_id = correlation_id
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


@app.exception_handler(SMSChatbotError)
async def handle_chatbot_error(request: Request, exc: SMSChatbotError):
    correlation_id = getattr(request.state, "correlation_id", None)
    log.error("chatbot_error", error=exc.message, correlation_id=correlation_id)
    reply_phone = getattr(request.state, "reply_phone", None)
    if exc.user_message and reply_phone:
        await sms_service.send_message(
            to=reply_phone, body=exc.user_message, force_send=True
        )
    return JSONResponse(
        status_code=500,
        content={"error": exc.message, "correlation_id": correlation_id},
    )


@app.get("/api/health")
async def health_check() -> dict[str, str]:
    db_status = "error"
    redis_status = "error"
    redis_client = None

    try:
        async with AsyncSessionFactory() as session:
            await session.execute(text("SELECT 1"))
        db_status = "ok"

        redis_client = redis_from_url(settings.redis_url, decode_responses=True)
        await redis_client.ping()
        redis_status = "ok"
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "red",
                "db": db_status,
                "redis": redis_status,
                "error": str(exc),
            },
        ) from exc
    finally:
        if redis_client is not None:
            await redis_client.aclose()

    return {"status": "green", "db": db_status, "redis": redis_status}
