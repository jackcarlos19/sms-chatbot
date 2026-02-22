from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from app.config import get_settings
from app.database import AsyncSessionFactory
from app.models.appointment import Appointment
from app.models.campaign import Campaign
from app.models.contact import Contact
from app.models.message import Message
from app.services.campaign_service import CampaignService

router = APIRouter(prefix="/api", tags=["admin"])


async def verify_admin_api_key(x_api_key: str = Header(default="")) -> None:
    settings = get_settings()
    if not settings.admin_api_key or x_api_key != settings.admin_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")


class CampaignCreateRequest(BaseModel):
    name: str
    message_template: str
    recipient_filter: dict = {}


class CampaignPatchRequest(BaseModel):
    status: Optional[str] = None
    scheduled_at: Optional[datetime] = None


@router.get("/contacts", dependencies=[Depends(verify_admin_api_key)])
async def list_contacts(limit: int = 100, offset: int = 0) -> list[dict]:
    async with AsyncSessionFactory() as session:
        result = await session.execute(
            select(Contact)
            .order_by(Contact.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        contacts = result.scalars().all()
        return [
            {
                "id": str(contact.id),
                "phone_number": contact.phone_number,
                "first_name": contact.first_name,
                "last_name": contact.last_name,
                "timezone": contact.timezone,
                "opt_in_status": contact.opt_in_status,
                "created_at": contact.created_at.isoformat(),
            }
            for contact in contacts
        ]


@router.get("/campaigns", dependencies=[Depends(verify_admin_api_key)])
async def list_campaigns(limit: int = 100, offset: int = 0) -> list[dict]:
    async with AsyncSessionFactory() as session:
        result = await session.execute(
            select(Campaign)
            .order_by(Campaign.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        campaigns = result.scalars().all()
        return [
            {
                "id": str(campaign.id),
                "name": campaign.name,
                "status": campaign.status,
                "scheduled_at": (
                    campaign.scheduled_at.isoformat() if campaign.scheduled_at else None
                ),
                "total_recipients": campaign.total_recipients,
                "sent_count": campaign.sent_count,
                "delivered_count": campaign.delivered_count,
                "failed_count": campaign.failed_count,
                "reply_count": campaign.reply_count,
                "created_at": campaign.created_at.isoformat(),
            }
            for campaign in campaigns
        ]


@router.post("/campaigns", dependencies=[Depends(verify_admin_api_key)])
async def create_campaign(payload: CampaignCreateRequest) -> dict:
    from app.api.deps import get_campaign_service

    service = get_campaign_service()
    campaign = await service.create_campaign(
        name=payload.name,
        message_template=payload.message_template,
        recipient_filter=payload.recipient_filter,
    )
    return {
        "id": str(campaign.id),
        "name": campaign.name,
        "status": campaign.status,
        "total_recipients": campaign.total_recipients,
    }


@router.patch("/campaigns/{campaign_id}", dependencies=[Depends(verify_admin_api_key)])
async def update_campaign(campaign_id: str, payload: CampaignPatchRequest) -> dict:
    cid = uuid.UUID(campaign_id)
    async with AsyncSessionFactory() as session:
        async with session.begin():
            result = await session.execute(select(Campaign).where(Campaign.id == cid))
            campaign = result.scalar_one_or_none()
            if campaign is None:
                raise HTTPException(status_code=404, detail="Campaign not found")
            if payload.status is not None:
                campaign.status = payload.status
            if payload.scheduled_at is not None:
                campaign.scheduled_at = payload.scheduled_at
            await session.flush()
            return {
                "id": str(campaign.id),
                "name": campaign.name,
                "status": campaign.status,
                "scheduled_at": (
                    campaign.scheduled_at.isoformat() if campaign.scheduled_at else None
                ),
            }


@router.get("/appointments", dependencies=[Depends(verify_admin_api_key)])
async def list_appointments(contact_id: str) -> list[dict]:
    cid = uuid.UUID(contact_id)
    async with AsyncSessionFactory() as session:
        result = await session.execute(
            select(Appointment)
            .where(Appointment.contact_id == cid)
            .order_by(Appointment.booked_at.desc())
        )
        appointments = result.scalars().all()
        return [
            {
                "id": str(appt.id),
                "contact_id": str(appt.contact_id),
                "slot_id": str(appt.slot_id),
                "status": appt.status,
                "booked_at": appt.booked_at.isoformat(),
                "cancelled_at": (
                    appt.cancelled_at.isoformat() if appt.cancelled_at else None
                ),
                "rescheduled_from_id": (
                    str(appt.rescheduled_from_id) if appt.rescheduled_from_id else None
                ),
            }
            for appt in appointments
        ]


@router.get("/messages", dependencies=[Depends(verify_admin_api_key)])
async def list_messages(contact_id: str) -> list[dict]:
    cid = uuid.UUID(contact_id)
    async with AsyncSessionFactory() as session:
        result = await session.execute(
            select(Message)
            .where(Message.contact_id == cid)
            .order_by(Message.created_at.desc())
        )
        messages = result.scalars().all()
        return [
            {
                "id": str(msg.id),
                "contact_id": str(msg.contact_id) if msg.contact_id else None,
                "direction": msg.direction,
                "body": msg.body,
                "sms_sid": msg.sms_sid,
                "status": msg.status,
                "error_code": msg.error_code,
                "campaign_id": str(msg.campaign_id) if msg.campaign_id else None,
                "created_at": msg.created_at.isoformat(),
            }
            for msg in messages
        ]
