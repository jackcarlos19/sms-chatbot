from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone

from arq import cron
from sqlalchemy import select

from app.core.quiet_hours import is_in_quiet_hours, seconds_until_quiet_hours_end
from app.database import AsyncSessionFactory
from app.models.campaign import Campaign
from app.models.campaign_recipient import CampaignRecipient
from app.models.contact import Contact
from app.models.conversation import ConversationState
from app.models.message import Message
from app.services.campaign_service import CampaignService
from app.services.sms_service import SMSService


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


async def process_campaign_batch(ctx: dict, campaign_id: str, offset: int, batch_size: int = 50) -> int:
    sms_service = SMSService()
    campaign_service = CampaignService()
    processed = 0
    campaign_uuid = uuid.UUID(str(campaign_id))

    async with AsyncSessionFactory() as session:
        campaign_result = await session.execute(select(Campaign).where(Campaign.id == campaign_uuid))
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
            contact_result = await session.execute(select(Contact).where(Contact.id == recipient.contact_id))
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

            rendered = campaign_service.render_template(campaign, contact)
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
        await ctx["redis"].enqueue_job("process_campaign_batch", campaign_id, offset + batch_size, batch_size)
    return processed


async def retry_failed_sends(ctx: dict) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=5)
    retried = 0
    sms_service = SMSService()

    async with AsyncSessionFactory() as session:
        queued_result = await session.execute(
            select(Message).where(
                Message.status == "queued",
                Message.created_at < cutoff,
            )
        )
        queued = queued_result.scalars().all()
        for msg in queued:
            contact_result = await session.execute(select(Contact).where(Contact.id == msg.contact_id))
            contact = contact_result.scalar_one_or_none()
            if contact is None:
                continue
            try:
                sent = await sms_service.send_message(
                    to=contact.phone_number,
                    body=msg.body,
                    campaign_id=str(msg.campaign_id) if msg.campaign_id else None,
                )
                msg.status = sent.status
                msg.sms_sid = sent.sms_sid
                retried += 1
            except Exception:  # noqa: BLE001
                msg.status = "failed"
            await session.commit()
    return retried


class WorkerSettings:
    functions = [expire_conversations, process_campaign_batch, retry_failed_sends]
    cron_jobs = [
        cron(expire_conversations, minute={0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55}),
        cron(retry_failed_sends, minute={0, 10, 20, 30, 40, 50}),
    ]
