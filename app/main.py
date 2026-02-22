from fastapi import FastAPI, HTTPException
from redis.asyncio import from_url as redis_from_url
from sqlalchemy import text

from app.config import get_settings
from app.database import AsyncSessionFactory

settings = get_settings()
app = FastAPI(title="SMS Chatbot API")


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
