from __future__ import annotations

from datetime import datetime, timezone

from arq import cron
from sqlalchemy import select

from app.database import AsyncSessionFactory
from app.models.conversation import ConversationState


async def expire_conversations(ctx: dict) -> int:  # noqa: ARG001
    now = datetime.now(timezone.utc)
    async with AsyncSessionFactory() as session:
        result = await session.execute(
            select(ConversationState).where(
                ConversationState.expires_at < now,
                ConversationState.current_state != "idle",
            )
        )
        expired = result.scalars().all()
        for state in expired:
            state.current_state = "idle"
            state.context = {}
            state.expires_at = None
        await session.commit()
        return len(expired)


class WorkerSettings:
    functions = [expire_conversations]
    cron_jobs = [cron(expire_conversations, minute={0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55})]
