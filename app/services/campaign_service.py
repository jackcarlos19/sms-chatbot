from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.config import get_settings
from app.database import AsyncSessionFactory
from app.models.campaign import Campaign
from app.models.campaign_recipient import CampaignRecipient
from app.models.contact import Contact


class CampaignService:
    def __init__(
        self, session_factory: async_sessionmaker[AsyncSession] | None = None
    ) -> None:
        self._session_factory = session_factory or AsyncSessionFactory
        self._settings = get_settings()

    async def create_campaign(
        self,
        name: str,
        message_template: str,
        recipient_filter: Optional[dict[str, Any]] = None,
    ) -> Campaign:
        recipient_filter = recipient_filter or {}
        async with self._session_factory() as session:
            async with session.begin():
                campaign = Campaign(
                    name=name,
                    message_template=message_template,
                    status="draft",
                )
                session.add(campaign)
                await session.flush()

                recipients = await self._resolve_recipients(session, recipient_filter)
                for contact in recipients:
                    session.add(
                        CampaignRecipient(
                            campaign_id=campaign.id,
                            contact_id=contact.id,
                            status="pending",
                        )
                    )
                campaign.total_recipients = len(recipients)
                await session.flush()
                return campaign

    async def schedule_campaign(
        self, campaign_id: uuid.UUID, send_at: datetime, ctx: dict | None = None
    ) -> Campaign:
        if send_at <= datetime.now(timezone.utc):
            raise ValueError("send_at must be in the future")

        async with self._session_factory() as session:
            async with session.begin():
                result = await session.execute(
                    select(Campaign).where(Campaign.id == campaign_id)
                )
                campaign = result.scalar_one()
                campaign.status = "scheduled"
                campaign.scheduled_at = send_at
                await session.flush()

        if ctx and "redis" in ctx:
            delay = max(0, int((send_at - datetime.now(timezone.utc)).total_seconds()))
            await ctx["redis"].enqueue_job(
                "execute_campaign", str(campaign_id), _defer_by=delay
            )
        return campaign

    async def execute_campaign(
        self, campaign_id: uuid.UUID, ctx: dict | None = None
    ) -> None:
        if ctx and "redis" in ctx:
            await ctx["redis"].enqueue_job(
                "process_campaign_batch", str(campaign_id), 0, 50
            )

    async def pause_campaign(self, campaign_id: uuid.UUID) -> Campaign:
        return await self._update_status(campaign_id, "paused")

    async def resume_campaign(
        self, campaign_id: uuid.UUID, ctx: dict | None = None
    ) -> Campaign:
        campaign = await self._update_status(campaign_id, "active")
        if ctx and "redis" in ctx:
            await ctx["redis"].enqueue_job(
                "process_campaign_batch", str(campaign_id), 0, 50
            )
        return campaign

    async def get_campaign_stats(self, campaign_id: uuid.UUID) -> dict[str, int]:
        async with self._session_factory() as session:
            query = (
                select(
                    func.count().label("total"),
                    func.count(
                        case((CampaignRecipient.status == "sent", 1))
                    ).label("sent"),
                    func.count(
                        case((CampaignRecipient.status == "delivered", 1))
                    ).label("delivered"),
                    func.count(
                        case((CampaignRecipient.status == "failed", 1))
                    ).label("failed"),
                )
                .where(CampaignRecipient.campaign_id == campaign_id)
            )
            result = await session.execute(query)
            row = result.one()
            return {
                "total_recipients": int(row.total or 0),
                "sent_count": int(row.sent or 0),
                "delivered_count": int(row.delivered or 0),
                "failed_count": int(row.failed or 0),
            }

    def render_template(self, campaign: Campaign, contact: Contact) -> str:
        """Render campaign message template with contact variables.

        Uses string.Template.safe_substitute to:
        1. Never crash on missing variables (leaves placeholder as-is)
        2. Prevent attribute access injection ({first_name.__class__} stays literal)
        """
        from string import Template

        variables = {
            "first_name": getattr(contact, "first_name", None) or "there",
            "last_name": getattr(contact, "last_name", None) or "",
            "business_name": self._settings.business_name,
            "phone_number": self._settings.twilio_phone_number,
        }
        # Convert {var} style to $var style for string.Template
        template_text = campaign.message_template
        for key in variables:
            template_text = template_text.replace("{" + key + "}", "${" + key + "}")
        return Template(template_text).safe_substitute(variables)

    async def _update_status(self, campaign_id: uuid.UUID, status: str) -> Campaign:
        async with self._session_factory() as session:
            async with session.begin():
                result = await session.execute(
                    select(Campaign).where(Campaign.id == campaign_id)
                )
                campaign = result.scalar_one()
                campaign.status = status
                await session.flush()
                return campaign

    async def _resolve_recipients(
        self, session: AsyncSession, recipient_filter: dict[str, Any]
    ) -> list[Contact]:
        query = select(Contact)
        opt_in = recipient_filter.get("opt_in_status", "opted_in")
        query = query.where(Contact.opt_in_status == opt_in)
        result = await session.execute(query)
        return result.scalars().all()
