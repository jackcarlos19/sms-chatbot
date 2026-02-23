from __future__ import annotations

import base64
import hashlib
import hmac
import json
import uuid
from datetime import datetime, timedelta, timezone
from time import monotonic
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy import and_, case, func, select

from app.api.deps import get_ai_service, get_redis_client, get_scheduling_service
from app.config import get_settings
from app.database import AsyncSessionFactory
from app.core.masking import mask_phone_number
from app.models.appointment import Appointment
from app.models.availability import AvailabilitySlot
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
logger = structlog.get_logger(__name__)
ADMIN_SESSION_COOKIE = "admin_session"


def _display_name(contact: Contact) -> str:
    parts = [contact.first_name or "", contact.last_name or ""]
    name = " ".join(p for p in parts if p).strip()
    return name if name else contact.phone_number


async def verify_admin_api_key(x_api_key: str = Header(default="")) -> None:
    settings = get_settings()
    if settings.admin_api_key and x_api_key == settings.admin_api_key:
        return
    raise HTTPException(status_code=401, detail="Invalid API key")


def _session_signing_key() -> bytes:
    settings = get_settings()
    return settings.admin_session_secret.encode("utf-8")


def _issue_admin_session_token(username: str) -> str:
    payload = {
        "admin": True,
        "username": username,
        "iat": int(datetime.now(timezone.utc).timestamp()),
    }
    payload_raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode(
        "utf-8"
    )
    payload_b64 = base64.urlsafe_b64encode(payload_raw).decode("utf-8").rstrip("=")
    signature = hmac.new(
        _session_signing_key(), payload_b64.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return f"{payload_b64}.{signature}"


def _verify_admin_session_token(token: str) -> bool:
    if "." not in token:
        return False
    payload_b64, signature = token.rsplit(".", 1)
    expected_signature = hmac.new(
        _session_signing_key(), payload_b64.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(signature, expected_signature):
        return False

    padding = "=" * (-len(payload_b64) % 4)
    try:
        payload_raw = base64.urlsafe_b64decode(payload_b64 + padding).decode("utf-8")
        data = json.loads(payload_raw)
    except (ValueError, json.JSONDecodeError):
        return False

    settings = get_settings()
    issued_at = int(data.get("iat", 0))
    now_ts = int(datetime.now(timezone.utc).timestamp())
    if issued_at <= 0:
        return False
    if now_ts - issued_at > settings.admin_session_max_age_seconds:
        return False
    return bool(data.get("admin", False))


async def verify_admin_access(
    request: Request, x_api_key: str = Header(default="")
) -> None:
    settings = get_settings()
    if settings.admin_api_key and x_api_key == settings.admin_api_key:
        return

    session_token = request.cookies.get(ADMIN_SESSION_COOKIE, "")
    if session_token and _verify_admin_session_token(session_token):
        return

    raise HTTPException(status_code=401, detail="Unauthorized")


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


class AdminLoginRequest(BaseModel):
    username: str = "admin"
    password: str


@router.post("/admin/auth/login")
async def admin_login(payload: AdminLoginRequest, response: Response) -> dict:
    settings = get_settings()
    # Prefer dedicated admin username/password; fallback to legacy ADMIN_API_KEY.
    valid_username = payload.username == settings.admin_username
    valid_password = payload.password == settings.admin_password
    legacy_password = bool(settings.admin_api_key) and payload.password == settings.admin_api_key
    if not valid_username or not (valid_password or legacy_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = _issue_admin_session_token(payload.username)
    secure_cookie = settings.app_env == "production"
    response.set_cookie(
        key=ADMIN_SESSION_COOKIE,
        value=token,
        httponly=True,
        secure=secure_cookie,
        samesite="lax",
        max_age=settings.admin_session_max_age_seconds,
        path="/",
    )
    return {"ok": True, "username": payload.username}


@router.post("/admin/auth/logout")
async def admin_logout(response: Response) -> dict:
    response.delete_cookie(ADMIN_SESSION_COOKIE, path="/")
    return {"ok": True}


@router.get("/admin/auth/me", dependencies=[Depends(verify_admin_access)])
async def admin_me() -> dict:
    return {"authenticated": True}


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
        logger.info(
            "simulator_outbound_captured",
            to=mask_phone_number(to),
            body_len=len(body or ""),
        )
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


@router.get("/dashboard/stats", dependencies=[Depends(verify_admin_access)])
async def dashboard_stats() -> dict:
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    async with AsyncSessionFactory() as session:
        contacts_result = await session.execute(
            select(
                func.count(Contact.id).label("contacts_total"),
                func.sum(
                    case((Contact.opt_in_status == "opted_in", 1), else_=0)
                ).label("contacts_opted_in"),
                func.sum(
                    case((Contact.opt_in_status == "opted_out", 1), else_=0)
                ).label("contacts_opted_out"),
            )
        )
        contacts_row = contacts_result.one()

        appointments_result = await session.execute(
            select(
                func.count(Appointment.id).label("appointments_total"),
                func.sum(
                    case(
                        (
                            and_(
                                AvailabilitySlot.start_time >= today_start,
                                AvailabilitySlot.start_time < today_end,
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ).label("appointments_today"),
                func.sum(
                    case(
                        (
                            and_(
                                Appointment.status == "confirmed",
                                AvailabilitySlot.start_time > now,
                            ),
                            1,
                        ),
                        else_=0,
                    )
                ).label("appointments_upcoming"),
            )
            .select_from(Appointment)
            .join(AvailabilitySlot, Appointment.slot_id == AvailabilitySlot.id)
        )
        appointments_row = appointments_result.one()

        messages_result = await session.execute(
            select(
                func.count(
                    case(
                        (
                            and_(
                                Message.created_at >= today_start,
                                Message.created_at < today_end,
                            ),
                            1,
                        ),
                    )
                ).label("messages_today"),
                func.count(
                    case(
                        (
                            and_(
                                Message.created_at >= today_start,
                                Message.created_at < today_end,
                                Message.direction == "inbound",
                            ),
                            1,
                        ),
                    )
                ).label("messages_inbound_today"),
                func.count(
                    case(
                        (
                            and_(
                                Message.created_at >= today_start,
                                Message.created_at < today_end,
                                Message.direction == "outbound",
                            ),
                            1,
                        ),
                    )
                ).label("messages_outbound_today"),
            )
        )
        messages_row = messages_result.one()

        activity_result = await session.execute(
            select(
                (
                    select(func.count(ConversationState.id))
                    .where(ConversationState.current_state != "idle")
                    .scalar_subquery()
                ).label("conversations_active"),
                (
                    select(func.count(Campaign.id))
                    .where(Campaign.status == "active")
                    .scalar_subquery()
                ).label("campaigns_active"),
                (select(func.count(Campaign.id)).scalar_subquery()).label(
                    "campaigns_total"
                ),
            )
        )
        activity_row = activity_result.one()

        return {
            "contacts_total": contacts_row.contacts_total or 0,
            "contacts_opted_in": contacts_row.contacts_opted_in or 0,
            "contacts_opted_out": contacts_row.contacts_opted_out or 0,
            "appointments_today": appointments_row.appointments_today or 0,
            "appointments_upcoming": appointments_row.appointments_upcoming or 0,
            "appointments_total": appointments_row.appointments_total or 0,
            "messages_today": messages_row.messages_today or 0,
            "messages_inbound_today": messages_row.messages_inbound_today or 0,
            "messages_outbound_today": messages_row.messages_outbound_today or 0,
            "conversations_active": activity_row.conversations_active or 0,
            "campaigns_active": activity_row.campaigns_active or 0,
            "campaigns_total": activity_row.campaigns_total or 0,
        }


@router.get(
    "/contacts",
    response_model=list[ContactResponse],
    dependencies=[Depends(verify_admin_access)],
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


@router.get("/contacts/{contact_id}", dependencies=[Depends(verify_admin_access)])
async def get_contact(contact_id: str) -> dict:
    try:
        cid = uuid.UUID(contact_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="Contact not found") from exc

    async with AsyncSessionFactory() as session:
        result = await session.execute(select(Contact).where(Contact.id == cid))
        contact = result.scalar_one_or_none()
        if contact is None:
            raise HTTPException(status_code=404, detail="Contact not found")

        state_result = await session.execute(
            select(ConversationState).where(ConversationState.contact_id == contact.id)
        )
        state = state_result.scalar_one_or_none()

        return {
            "id": str(contact.id),
            "phone_number": contact.phone_number,
            "first_name": contact.first_name,
            "last_name": contact.last_name,
            "timezone": contact.timezone,
            "opt_in_status": contact.opt_in_status,
            "created_at": contact.created_at.isoformat(),
            "updated_at": contact.updated_at.isoformat(),
            "conversation_state": state.current_state if state else "idle",
            "last_message_at": state.last_message_at.isoformat()
            if state and state.last_message_at
            else None,
        }


@router.get(
    "/campaigns",
    response_model=list[CampaignResponse],
    dependencies=[Depends(verify_admin_access)],
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
    dependencies=[Depends(verify_admin_access)],
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
    dependencies=[Depends(verify_admin_access)],
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


@router.get("/appointments/all", dependencies=[Depends(verify_admin_access)])
async def list_all_appointments(
    limit: int = 50, offset: int = 0, status: Optional[str] = None
) -> list[dict]:
    async with AsyncSessionFactory() as session:
        query = (
            select(Appointment, Contact, AvailabilitySlot)
            .join(Contact, Appointment.contact_id == Contact.id)
            .join(AvailabilitySlot, Appointment.slot_id == AvailabilitySlot.id)
        )
        if status:
            query = query.where(Appointment.status == status)
        query = query.order_by(AvailabilitySlot.start_time.asc()).offset(offset).limit(limit)
        result = await session.execute(query)
        rows = result.all()
        return [
            {
                "id": str(appt.id),
                "contact_id": str(appt.contact_id),
                "contact_phone": contact.phone_number,
                "contact_name": _display_name(contact),
                "slot_start": slot.start_time.isoformat(),
                "slot_end": slot.end_time.isoformat(),
                "status": appt.status,
                "booked_at": appt.booked_at.isoformat(),
            }
            for appt, contact, slot in rows
        ]


@router.get(
    "/appointments",
    response_model=list[AppointmentResponse],
    dependencies=[Depends(verify_admin_access)],
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


@router.get("/conversations", dependencies=[Depends(verify_admin_access)])
async def list_conversations(limit: int = 50, offset: int = 0) -> list[dict]:
    async with AsyncSessionFactory() as session:
        result = await session.execute(
            select(ConversationState, Contact)
            .join(Contact, ConversationState.contact_id == Contact.id)
            .order_by(ConversationState.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        rows = result.all()
        return [
            {
                "id": str(state.id),
                "contact_id": str(state.contact_id),
                "contact_phone": contact.phone_number,
                "contact_name": _display_name(contact),
                "current_state": state.current_state,
                "last_message_at": state.last_message_at.isoformat()
                if state.last_message_at
                else None,
                "updated_at": state.updated_at.isoformat(),
            }
            for state, contact in rows
        ]


@router.get("/slots", dependencies=[Depends(verify_admin_access)])
async def list_slots(days_ahead: int = 7) -> list[dict]:
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=days_ahead)

    async with AsyncSessionFactory() as session:
        result = await session.execute(
            select(AvailabilitySlot)
            .where(
                and_(
                    AvailabilitySlot.start_time >= now,
                    AvailabilitySlot.start_time <= end,
                )
            )
            .order_by(AvailabilitySlot.start_time.asc())
        )
        slots = result.scalars().all()
        return [
            {
                "id": str(slot.id),
                "start_time": slot.start_time.isoformat(),
                "end_time": slot.end_time.isoformat(),
                "is_available": slot.is_available,
                "slot_type": slot.slot_type,
            }
            for slot in slots
        ]


@router.get(
    "/messages",
    response_model=list[MessageResponse],
    dependencies=[Depends(verify_admin_access)],
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
    dependencies=[Depends(verify_admin_access)],
)
async def simulate_inbound(payload: SimulateRequest) -> dict:
    started_at = monotonic()
    logger.info(
        "simulator_inbound_started",
        phone=mask_phone_number(payload.phone_number),
        message_len=len(payload.message or ""),
        message_preview=(payload.message or "")[:80],
    )
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

    response = {
        "responses": [msg["body"] for msg in fake_sms._sent],
        "conversation_state": state.current_state if state else "idle",
        "context": state.context if state else {},
    }
    logger.info(
        "simulator_inbound_finished",
        phone=mask_phone_number(payload.phone_number),
        responses_count=len(response["responses"]),
        conversation_state=response["conversation_state"],
        elapsed_ms=round((monotonic() - started_at) * 1000, 2),
    )
    return response
