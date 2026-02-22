from __future__ import annotations

import uuid

import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.admin import router as admin_router
from app.api.deps import get_redis_client, get_sms_service
from app.api.webhooks import router as webhooks_router
from app.config import get_settings
from app.core.exceptions import SMSChatbotError
from app.core.logging import configure_structured_logging
from app.database import AsyncSessionFactory

settings = get_settings()
configure_structured_logging()
log = structlog.get_logger(__name__)
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
        sms_service = get_sms_service()
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

    try:
        async with AsyncSessionFactory() as session:
            await session.execute(text("SELECT 1"))
        db_status = "ok"

        redis_client = get_redis_client()
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

    return {"status": "green", "db": db_status, "redis": redis_status}
