from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from app.api.deps import get_ai_service, get_redis_client, get_scheduling_service
from app.config import get_settings
from app.database import AsyncSessionFactory
from app.models.appointment import Appointment
from app.models.campaign import Campaign
from app.models.contact import Contact
from app.models.conversation import ConversationState
from app.models.message import Message
from app.schemas import (
    AppointmentResponse,
    CampaignCreateResponse,
    CampaignResponse,
    ContactResponse,
    MessageResponse,
)
from app.services.conversation_service import ConversationService
from app.services.campaign_service import CampaignService
from app.services.sms_service import SMSService

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


class SimulateRequest(BaseModel):
    phone_number: str = "+15551234567"
    message: str


class SimulatorSMSService(SMSService):
    """SMS service that captures messages instead of sending via Twilio."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._sent: list[dict[str, str]] = []

    async def send_message(
        self,
        to: str,
        body: str,
        campaign_id: str | None = None,
        force_send: bool = False,
    ) -> Message:
        _ = (campaign_id, force_send)
        self._sent.append({"to": to, "body": body})
        async with AsyncSessionFactory() as session:
            contact = await self._get_or_create_contact(session, to)
            message = Message(
                contact_id=contact.id,
                direction="outbound",
                body=body,
                status="simulated",
            )
            session.add(message)
            await session.commit()
            await session.refresh(message)
            return message


@router.get(
    "/contacts",
    response_model=list[ContactResponse],
    dependencies=[Depends(verify_admin_api_key)],
)
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


@router.get(
    "/campaigns",
    response_model=list[CampaignResponse],
    dependencies=[Depends(verify_admin_api_key)],
)
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


@router.post(
    "/campaigns",
    response_model=CampaignCreateResponse,
    dependencies=[Depends(verify_admin_api_key)],
)
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


@router.patch(
    "/campaigns/{campaign_id}",
    response_model=CampaignResponse,
    dependencies=[Depends(verify_admin_api_key)],
)
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
                "total_recipients": campaign.total_recipients,
                "sent_count": campaign.sent_count,
                "delivered_count": campaign.delivered_count,
                "failed_count": campaign.failed_count,
                "reply_count": campaign.reply_count,
                "created_at": campaign.created_at.isoformat(),
            }


@router.get(
    "/appointments",
    response_model=list[AppointmentResponse],
    dependencies=[Depends(verify_admin_api_key)],
)
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


@router.get(
    "/messages",
    response_model=list[MessageResponse],
    dependencies=[Depends(verify_admin_api_key)],
)
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


@router.post(
    "/simulate/inbound",
    dependencies=[Depends(verify_admin_api_key)],
)
async def simulate_inbound(payload: SimulateRequest) -> dict:
    fake_sms = SimulatorSMSService()
    conv_service = ConversationService(
        ai_service=get_ai_service(),
        scheduling_service=get_scheduling_service(),
        sms_service=fake_sms,
        redis_client=get_redis_client(),
    )

    async with AsyncSessionFactory() as session:
        contact = await fake_sms._get_or_create_contact(session, payload.phone_number)
        inbound = Message(
            contact_id=contact.id,
            direction="inbound",
            body=payload.message,
            status="received",
            sms_sid=f"SIM_{uuid.uuid4().hex[:16]}",
        )
        session.add(inbound)
        await session.commit()

    await conv_service.process_inbound_message(
        phone_number=payload.phone_number,
        body=payload.message,
        sms_sid=f"SIM_{uuid.uuid4().hex[:16]}",
    )

    async with AsyncSessionFactory() as session:
        result = await session.execute(
            select(ConversationState)
            .join(Contact, ConversationState.contact_id == Contact.id)
            .where(Contact.phone_number == payload.phone_number)
        )
        state = result.scalar_one_or_none()

    return {
        "responses": [msg["body"] for msg in fake_sms._sent],
        "conversation_state": state.current_state if state else "idle",
        "context": state.context if state else {},
    }
