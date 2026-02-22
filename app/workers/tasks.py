from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone

import structlog
from arq import cron
from arq.connections import RedisSettings
from sqlalchemy import select, update

from app.config import get_settings
from app.core.quiet_hours import is_in_quiet_hours, seconds_until_quiet_hours_end
from app.database import AsyncSessionFactory
from app.models.campaign import Campaign
from app.models.campaign_recipient import CampaignRecipient
from app.models.contact import Contact
from app.models.conversation import ConversationState
from app.models.message import Message
from app.services.campaign_service import CampaignService
from app.services.sms_service import SMSService

logger = structlog.get_logger(__name__)


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
        logger.info("conversations_expired", count=len(expired))
        return len(expired)


async def process_campaign_batch(
    ctx: dict, campaign_id: str, offset: int, batch_size: int = 50
) -> int:
    sms_service = SMSService()
    campaign_service = CampaignService()
    processed = 0
    campaign_uuid = uuid.UUID(str(campaign_id))

    async with AsyncSessionFactory() as session:
        campaign_result = await session.execute(
            select(Campaign).where(Campaign.id == campaign_uuid)
        )
        campaign = campaign_result.scalar_one_or_none()
        if campaign is None or campaign.status == "paused":
            return 0
        campaign.status = "active"
        await session.commit()

        recipients_result = await session.execute(
            select(CampaignRecipient)
            .where(CampaignRecipient.campaign_id == campaign.id)
            .order_by(CampaignRecipient.id)
            .offset(offset)
            .limit(batch_size)
        )
        recipients = recipients_result.scalars().all()

        delayed = False
        for recipient in recipients:
            contact_result = await session.execute(
                select(Contact).where(Contact.id == recipient.contact_id)
            )
            contact = contact_result.scalar_one_or_none()
            if contact is None or contact.opt_in_status != "opted_in":
                recipient.status = "skipped"
                await session.commit()
                continue

            now = datetime.now(timezone.utc)
            if campaign.respect_timezone and is_in_quiet_hours(
                now_utc=now,
                timezone_name=contact.timezone,
                quiet_start=campaign.quiet_hours_start,
                quiet_end=campaign.quiet_hours_end,
            ):
                if "redis" in ctx:
                    defer_by = seconds_until_quiet_hours_end(
                        now_utc=now,
                        timezone_name=contact.timezone,
                        quiet_start=campaign.quiet_hours_start,
                        quiet_end=campaign.quiet_hours_end,
                    )
                    await ctx["redis"].enqueue_job(
                        "process_campaign_batch",
                        str(campaign.id),
                        offset,
                        batch_size,
                        _defer_by=defer_by,
                    )
                delayed = True
                break

            try:
                rendered = campaign_service.render_template(campaign, contact)
            except KeyError as exc:
                logger.warning(
                    "template_render_failed",
                    campaign_id=str(campaign.id),
                    contact_id=str(contact.id),
                    missing_key=str(exc),
                )
                recipient.status = "failed"
                await session.commit()
                continue

            try:
                await sms_service.send_message(
                    to=contact.phone_number,
                    body=rendered,
                    campaign_id=str(campaign.id),
                )
                recipient.status = "sent"
                recipient.sent_at = datetime.now(timezone.utc)
                processed += 1
            except Exception:  # noqa: BLE001
                recipient.status = "failed"
            await session.commit()
            await asyncio.sleep(1)

    if "redis" in ctx and not delayed and len(recipients) == batch_size:
        await ctx["redis"].enqueue_job(
            "process_campaign_batch", campaign_id, offset + batch_size, batch_size
        )
    return processed


async def retry_failed_sends(ctx: dict) -> int:  # noqa: ARG001
    """Retry messages stuck in 'queued' status for over 5 minutes.

    FIX: Updates the EXISTING message record's status directly instead of
    creating a duplicate via sms_service.send_message().
    """
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=5)
    retried = 0
    sms_service = SMSService()

    async with AsyncSessionFactory() as session:
        queued_result = await session.execute(
            select(Message)
            .where(Message.status == "queued", Message.created_at < cutoff)
            .limit(50)
        )
        queued = queued_result.scalars().all()
        for msg in queued:
            contact_result = await session.execute(
                select(Contact).where(Contact.id == msg.contact_id)
            )
            contact = contact_result.scalar_one_or_none()
            if contact is None:
                msg.status = "failed"
                msg.error_message = "Contact not found"
                await session.commit()
                continue
            try:
                # Send via Twilio but update THIS record, don't create a new one
                import asyncio as _asyncio
                from twilio.base.exceptions import TwilioRestException

                twilio_message = await _asyncio.to_thread(
                    sms_service._client.messages.create,
                    body=msg.body,
                    from_=sms_service._settings.twilio_phone_number,
                    to=contact.phone_number,
                    status_callback=sms_service._settings.twilio_status_callback_url,
                )
                msg.sms_sid = twilio_message.sid
                msg.status = "sent"
                retried += 1
            except Exception as exc:  # noqa: BLE001
                msg.status = "failed"
                msg.error_message = str(exc)
            await session.commit()
    logger.info("retry_failed_sends_complete", retried=retried)
    return retried


def _parse_redis_url(url: str) -> RedisSettings:
    """Parse redis://host:port/db into arq RedisSettings."""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    return RedisSettings(
        host=parsed.hostname or "redis",
        port=parsed.port or 6379,
        database=int(parsed.path.lstrip("/") or "0"),
        password=parsed.password,
    )


class WorkerSettings:
    settings = get_settings()
    redis_settings = _parse_redis_url(settings.redis_url)

    functions = [expire_conversations, process_campaign_batch, retry_failed_sends]
    cron_jobs = [
        cron(
            expire_conversations, minute={0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55}
        ),
        cron(retry_failed_sends, minute={0, 10, 20, 30, 40, 50}),
    ]
