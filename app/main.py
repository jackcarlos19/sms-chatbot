from __future__ import annotations

import os
import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api.admin import router as admin_router
from app.api.deps import get_redis_client, get_sms_service
from app.api.webhooks import router as webhooks_router
from app.config import get_settings
from app.core.exceptions import SMSChatbotError
from app.core.logging import configure_structured_logging
from app.database import AsyncSessionFactory
from app.database import engine
from app.schemas import HealthResponse

settings = get_settings()
configure_structured_logging()
log = structlog.get_logger(__name__)


def _validate_production_secrets() -> None:
    if settings.app_env not in ("production", "staging"):
        return
    insecure_defaults = {
        "secret_key": "change-me-in-production",
        "admin_api_key": "change-this-admin-key",
        "admin_password": "change-this-admin-password",
        "admin_session_secret": "change-this-session-secret",
    }
    for attr, default_val in insecure_defaults.items():
        if getattr(settings, attr, None) == default_val:
            raise RuntimeError(
                f"FATAL: {attr.upper()} has its default value. "
                "Set a real value in .env before running in production."
            )


_validate_production_secrets()


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    _ = app_instance
    log.info("app_starting", env=settings.app_env)
    yield
    log.info("app_shutting_down")
    try:
        redis_client = get_redis_client()
        await redis_client.aclose()
    except Exception:  # noqa: BLE001
        pass
    await engine.dispose()


app = FastAPI(title="SMS Chatbot API", lifespan=lifespan)
app.include_router(webhooks_router)
app.include_router(admin_router)

# --- Admin SPA static serving ---
_admin_dist = os.path.join(os.path.dirname(__file__), "..", "admin", "dist")
if os.path.isdir(_admin_dist):
    _admin_assets = os.path.join(_admin_dist, "assets")
    if os.path.isdir(_admin_assets):
        app.mount(
            "/admin/assets",
            StaticFiles(directory=_admin_assets),
            name="admin-assets",
        )

    @app.get("/admin")
    async def admin_root():
        return FileResponse(os.path.join(_admin_dist, "index.html"))

    @app.get("/admin/{rest_of_path:path}")
    async def admin_spa(rest_of_path: str):
        return FileResponse(os.path.join(_admin_dist, "index.html"))

app.mount("/static", StaticFiles(directory="app/static"), name="static")


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


@app.get("/api/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    db_status = "error"
    redis_status = "error"
    errors: dict[str, str] = {}

    try:
        async with AsyncSessionFactory() as session:
            await session.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as exc:
        errors["db"] = str(exc)

    try:
        redis_client = get_redis_client()
        await redis_client.ping()
        redis_status = "ok"
    except Exception as exc:
        errors["redis"] = str(exc)

    if db_status != "ok" or redis_status != "ok":
        raise HTTPException(
            status_code=503,
            detail={
                "status": "red",
                "db": db_status,
                "redis": redis_status,
                "error": errors,
            },
        )

    return HealthResponse(status="green", db=db_status, redis=redis_status)


@app.get("/demo")
async def demo_redirect():
    from fastapi.responses import RedirectResponse

    return RedirectResponse("/static/simulator.html")
