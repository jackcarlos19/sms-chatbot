from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from time import monotonic
from typing import Optional

import structlog
from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy import and_, case, func, or_, select

from app.api.deps import get_ai_service, get_redis_client, get_scheduling_service
from app.config import get_settings
from app.core.rate_limit import rate_limit
from app.database import AsyncSessionFactory
from app.core.masking import mask_phone_number
from app.models.admin_user import AdminUser
from app.models.appointment import Appointment
from app.models.audit_event import AuditEvent
from app.models.availability import AvailabilitySlot
from app.models.campaign import Campaign
from app.models.contact import Contact
from app.models.conversation import ConversationState
from app.models.message import Message
from app.models.reminder_workflow import ReminderWorkflow
from app.models.tenant import Tenant
from app.models.waitlist_entry import WaitlistEntry
from app.schemas import (
    AppointmentResponse,
    CampaignCreateResponse,
    CampaignResponse,
    MessageResponse,
)
from app.services.conversation_service import ConversationService
from app.services.campaign_service import CampaignService
from app.services.sms_service import SMSService

router = APIRouter(prefix="/api", tags=["admin"])
logger = structlog.get_logger(__name__)
ADMIN_SESSION_COOKIE = "admin_session"
ADMIN_CSRF_COOKIE = "admin_csrf"


def _parse_uuid(value: str, detail: str) -> uuid.UUID:
    try:
        return uuid.UUID(value)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=detail) from exc


async def _resolve_tenant_id(
    session, x_tenant_id: str = ""
) -> uuid.UUID | None:  # noqa: ANN001
    if x_tenant_id:
        try:
            tid = uuid.UUID(x_tenant_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid tenant id") from exc
        tenant = await session.get(Tenant, tid)
        if tenant is None:
            raise HTTPException(status_code=404, detail="Tenant not found")
        return tid

    # Single-tenant default for now; keeps queries tenant-ready.
    result = await session.execute(select(Tenant).where(Tenant.slug == "default"))
    tenant = result.scalar_one_or_none()
    if tenant is None:
        tenant = Tenant(slug="default", name="Default Tenant")
        session.add(tenant)
        await session.flush()
    return tenant.id


def _scope_filter(model, tenant_id: uuid.UUID | None):  # noqa: ANN001
    tenant_column = getattr(model, "tenant_id", None)
    if tenant_id is None or tenant_column is None:
        return None
    return or_(tenant_column == tenant_id, tenant_column.is_(None))


def _require_admin_csrf(request: Request) -> None:
    # Cookie-backed sessions need CSRF token checks for state-changing operations.
    csrf_cookie = request.cookies.get(ADMIN_CSRF_COOKIE, "")
    csrf_header = request.headers.get("X-CSRF-Token", "")
    if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
        raise HTTPException(status_code=403, detail="CSRF validation failed")


def _actor_username_from_token(request: Request) -> str:
    token = request.cookies.get(ADMIN_SESSION_COOKIE, "")
    if "." not in token:
        return "admin"
    payload_b64, _ = token.rsplit(".", 1)
    padding = "=" * (-len(payload_b64) % 4)
    try:
        payload_raw = base64.urlsafe_b64decode(payload_b64 + padding).decode("utf-8")
        data = json.loads(payload_raw)
    except (ValueError, json.JSONDecodeError):
        return "admin"
    return str(data.get("username") or "admin")


async def _write_audit_event(
    session,  # noqa: ANN001
    *,
    tenant_id: uuid.UUID | None,
    actor_username: str,
    entity_type: str,
    entity_id: uuid.UUID | None,
    action: str,
    before_json: dict,
    after_json: dict,
    request: Request,
) -> None:
    event = AuditEvent(
        tenant_id=tenant_id,
        actor_username=actor_username,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        before_json=before_json,
        after_json=after_json,
        request_id=getattr(request.state, "correlation_id", None),
    )
    session.add(event)


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


class ContactPatchRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    timezone: Optional[str] = None
    opt_in_status: Optional[str] = None


class AppointmentCancelRequest(BaseModel):
    reason: str


class AppointmentRescheduleRequest(BaseModel):
    new_slot_id: str


class AppointmentNotesRequest(BaseModel):
    notes: str


class AppointmentBookRequest(BaseModel):
    contact_id: str
    slot_id: str


class WaitlistCreateRequest(BaseModel):
    contact_id: str
    desired_start: Optional[datetime] = None
    desired_end: Optional[datetime] = None
    notes: Optional[str] = None


class WaitlistPatchRequest(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None


class AdminUserCreateRequest(BaseModel):
    username: str
    role: str = "admin"
    is_active: bool = True


class ReminderWorkflowCreateRequest(BaseModel):
    name: str
    appointment_status: Optional[str] = None
    minutes_before: int
    channel: str = "sms"
    template: str
    is_active: bool = True


class ReminderWorkflowPatchRequest(BaseModel):
    name: Optional[str] = None
    appointment_status: Optional[str] = None
    minutes_before: Optional[int] = None
    channel: Optional[str] = None
    template: Optional[str] = None
    is_active: Optional[bool] = None


@router.post("/admin/auth/login")
async def admin_login(
    payload: AdminLoginRequest, request: Request, response: Response
) -> dict:
    rate_limit(request, "login", max_requests=5, window=60)
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
    csrf_token = secrets.token_urlsafe(32)
    response.set_cookie(
        key=ADMIN_CSRF_COOKIE,
        value=csrf_token,
        httponly=False,
        secure=secure_cookie,
        samesite="lax",
        max_age=settings.admin_session_max_age_seconds,
        path="/",
    )
    async with AsyncSessionFactory() as session:
        tenant_id = await _resolve_tenant_id(session)
        existing = await session.execute(
            select(AdminUser).where(AdminUser.username == payload.username)
        )
        if existing.scalar_one_or_none() is None:
            session.add(
                AdminUser(
                    username=payload.username,
                    role="super_admin",
                    is_active=True,
                    tenant_id=tenant_id,
                )
            )
            await session.commit()
    return {"ok": True, "username": payload.username}


@router.post("/admin/auth/logout")
async def admin_logout(response: Response) -> dict:
    response.delete_cookie(ADMIN_SESSION_COOKIE, path="/")
    response.delete_cookie(ADMIN_CSRF_COOKIE, path="/")
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
    dependencies=[Depends(verify_admin_access)],
)
async def list_contacts(
    limit: int = 50,
    offset: int = 0,
    search: str = "",
    status: str = "",
    x_tenant_id: str = Header(default=""),
) -> dict:
    async with AsyncSessionFactory() as session:
        tenant_id = await _resolve_tenant_id(session, x_tenant_id)
        base_query = select(Contact)
        count_query = select(func.count(Contact.id))
        scope = _scope_filter(Contact, tenant_id)
        if scope is not None:
            base_query = base_query.where(scope)
            count_query = count_query.where(scope)

        if search:
            like = f"%{search}%"
            full_name = func.concat(
                func.coalesce(Contact.first_name, ""),
                " ",
                func.coalesce(Contact.last_name, ""),
            )
            search_filter = Contact.phone_number.ilike(like) | full_name.ilike(like)
            base_query = base_query.where(search_filter)
            count_query = count_query.where(search_filter)

        if status and status != "all":
            base_query = base_query.where(Contact.opt_in_status == status)
            count_query = count_query.where(Contact.opt_in_status == status)

        total = (await session.execute(count_query)).scalar_one()
        result = await session.execute(
            base_query
            .order_by(Contact.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        contacts = result.scalars().all()
        return {
            "data": [
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
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(contacts) < total,
        }


@router.get("/contacts/{contact_id}", dependencies=[Depends(verify_admin_access)])
async def get_contact(contact_id: str, x_tenant_id: str = Header(default="")) -> dict:
    cid = _parse_uuid(contact_id, "Contact not found")

    async with AsyncSessionFactory() as session:
        tenant_id = await _resolve_tenant_id(session, x_tenant_id)
        query = select(Contact).where(Contact.id == cid)
        scope = _scope_filter(Contact, tenant_id)
        if scope is not None:
            query = query.where(scope)
        result = await session.execute(query)
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


@router.patch("/contacts/{contact_id}", dependencies=[Depends(verify_admin_access)])
async def patch_contact(
    contact_id: str,
    payload: ContactPatchRequest,
    request: Request,
    x_tenant_id: str = Header(default=""),
) -> dict:
    _require_admin_csrf(request)
    cid = _parse_uuid(contact_id, "Contact not found")
    async with AsyncSessionFactory() as session:
        async with session.begin():
            tenant_id = await _resolve_tenant_id(session, x_tenant_id)
            query = select(Contact).where(Contact.id == cid)
            scope = _scope_filter(Contact, tenant_id)
            if scope is not None:
                query = query.where(scope)
            result = await session.execute(query)
            contact = result.scalar_one_or_none()
            if contact is None:
                raise HTTPException(status_code=404, detail="Contact not found")

            before = {
                "first_name": contact.first_name,
                "last_name": contact.last_name,
                "timezone": contact.timezone,
                "opt_in_status": contact.opt_in_status,
            }
            if payload.first_name is not None:
                contact.first_name = payload.first_name.strip() or None
            if payload.last_name is not None:
                contact.last_name = payload.last_name.strip() or None
            if payload.timezone is not None:
                contact.timezone = payload.timezone
            if payload.opt_in_status is not None:
                contact.opt_in_status = payload.opt_in_status
            contact.tenant_id = contact.tenant_id or tenant_id

            after = {
                "first_name": contact.first_name,
                "last_name": contact.last_name,
                "timezone": contact.timezone,
                "opt_in_status": contact.opt_in_status,
            }
            await _write_audit_event(
                session,
                tenant_id=tenant_id,
                actor_username=_actor_username_from_token(request),
                entity_type="contact",
                entity_id=contact.id,
                action="contact.updated",
                before_json=before,
                after_json=after,
                request=request,
            )
            await session.flush()

            return {
                "id": str(contact.id),
                "phone_number": contact.phone_number,
                "first_name": contact.first_name,
                "last_name": contact.last_name,
                "timezone": contact.timezone,
                "opt_in_status": contact.opt_in_status,
                "created_at": contact.created_at.isoformat(),
                "updated_at": contact.updated_at.isoformat(),
            }


@router.get(
    "/campaigns",
    dependencies=[Depends(verify_admin_access)],
)
async def list_campaigns(
    limit: int = 50, offset: int = 0, x_tenant_id: str = Header(default="")
) -> dict:
    async with AsyncSessionFactory() as session:
        tenant_id = await _resolve_tenant_id(session, x_tenant_id)
        count_query = select(func.count(Campaign.id))
        base_query = select(Campaign)
        scope = _scope_filter(Campaign, tenant_id)
        if scope is not None:
            count_query = count_query.where(scope)
            base_query = base_query.where(scope)
        total = (await session.execute(count_query)).scalar_one()
        result = await session.execute(
            base_query.order_by(Campaign.created_at.desc()).offset(offset).limit(limit)
        )
        campaigns = result.scalars().all()
        return {
            "data": [
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
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(campaigns) < total,
        }


@router.post(
    "/campaigns",
    response_model=CampaignCreateResponse,
    dependencies=[Depends(verify_admin_access)],
)
async def create_campaign(
    payload: CampaignCreateRequest, x_tenant_id: str = Header(default="")
) -> dict:
    from app.api.deps import get_campaign_service

    service = get_campaign_service()
    campaign = await service.create_campaign(
        name=payload.name,
        message_template=payload.message_template,
        recipient_filter=payload.recipient_filter,
    )
    async with AsyncSessionFactory() as session:
        async with session.begin():
            tenant_id = await _resolve_tenant_id(session, x_tenant_id)
            persisted = await session.get(Campaign, campaign.id)
            if persisted is not None:
                persisted.tenant_id = persisted.tenant_id or tenant_id
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
async def update_campaign(
    campaign_id: str, payload: CampaignPatchRequest, x_tenant_id: str = Header(default="")
) -> dict:
    cid = uuid.UUID(campaign_id)
    async with AsyncSessionFactory() as session:
        async with session.begin():
            tenant_id = await _resolve_tenant_id(session, x_tenant_id)
            query = select(Campaign).where(Campaign.id == cid)
            scope = _scope_filter(Campaign, tenant_id)
            if scope is not None:
                query = query.where(scope)
            result = await session.execute(query)
            campaign = result.scalar_one_or_none()
            if campaign is None:
                raise HTTPException(status_code=404, detail="Campaign not found")
            campaign.tenant_id = campaign.tenant_id or tenant_id
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
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    search: str = "",
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    x_tenant_id: str = Header(default=""),
) -> dict:
    async with AsyncSessionFactory() as session:
        tenant_id = await _resolve_tenant_id(session, x_tenant_id)
        query = (
            select(Appointment, Contact, AvailabilitySlot)
            .join(Contact, Appointment.contact_id == Contact.id)
            .join(AvailabilitySlot, Appointment.slot_id == AvailabilitySlot.id)
        )
        count_query = (
            select(func.count(Appointment.id))
            .select_from(Appointment)
            .join(Contact, Appointment.contact_id == Contact.id)
            .join(AvailabilitySlot, Appointment.slot_id == AvailabilitySlot.id)
        )
        appt_scope = _scope_filter(Appointment, tenant_id)
        contact_scope = _scope_filter(Contact, tenant_id)
        slot_scope = _scope_filter(AvailabilitySlot, tenant_id)
        if appt_scope is not None:
            query = query.where(appt_scope)
            count_query = count_query.where(appt_scope)
        if contact_scope is not None:
            query = query.where(contact_scope)
            count_query = count_query.where(contact_scope)
        if slot_scope is not None:
            query = query.where(slot_scope)
            count_query = count_query.where(slot_scope)
        if status:
            query = query.where(Appointment.status == status)
            count_query = count_query.where(Appointment.status == status)
        if search:
            like = f"%{search}%"
            full_name = func.concat(
                func.coalesce(Contact.first_name, ""),
                " ",
                func.coalesce(Contact.last_name, ""),
            )
            search_filter = Contact.phone_number.ilike(like) | full_name.ilike(like)
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)
        if date_from is not None:
            query = query.where(AvailabilitySlot.start_time >= date_from)
            count_query = count_query.where(AvailabilitySlot.start_time >= date_from)
        if date_to is not None:
            query = query.where(AvailabilitySlot.start_time <= date_to)
            count_query = count_query.where(AvailabilitySlot.start_time <= date_to)
        total = (await session.execute(count_query)).scalar_one()
        query = query.order_by(AvailabilitySlot.start_time.asc()).offset(offset).limit(limit)
        result = await session.execute(query)
        rows = result.all()
        return {
            "data": [
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
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(rows) < total,
        }


@router.get("/appointments/{appointment_id}", dependencies=[Depends(verify_admin_access)])
async def get_appointment_detail(
    appointment_id: str, x_tenant_id: str = Header(default="")
) -> dict:
    appt_id = _parse_uuid(appointment_id, "Appointment not found")
    async with AsyncSessionFactory() as session:
        tenant_id = await _resolve_tenant_id(session, x_tenant_id)
        query = (
            select(Appointment, Contact, AvailabilitySlot)
            .join(Contact, Appointment.contact_id == Contact.id)
            .join(AvailabilitySlot, Appointment.slot_id == AvailabilitySlot.id)
            .where(Appointment.id == appt_id)
        )
        appt_scope = _scope_filter(Appointment, tenant_id)
        contact_scope = _scope_filter(Contact, tenant_id)
        slot_scope = _scope_filter(AvailabilitySlot, tenant_id)
        if appt_scope is not None:
            query = query.where(appt_scope)
        if contact_scope is not None:
            query = query.where(contact_scope)
        if slot_scope is not None:
            query = query.where(slot_scope)
        row = (await session.execute(query)).one_or_none()
        if row is None:
            raise HTTPException(status_code=404, detail="Appointment not found")
        appt, contact, slot = row
        return {
            "id": str(appt.id),
            "tenant_id": str(appt.tenant_id) if appt.tenant_id else None,
            "contact_id": str(contact.id),
            "contact_name": _display_name(contact),
            "contact_phone": contact.phone_number,
            "slot_id": str(slot.id),
            "slot_start": slot.start_time.isoformat(),
            "slot_end": slot.end_time.isoformat(),
            "status": appt.status,
            "booked_at": appt.booked_at.isoformat(),
            "cancelled_at": appt.cancelled_at.isoformat() if appt.cancelled_at else None,
            "cancellation_reason": appt.cancellation_reason,
            "notes": appt.notes,
            "rescheduled_from_id": (
                str(appt.rescheduled_from_id) if appt.rescheduled_from_id else None
            ),
            "version": appt.version,
        }


@router.post(
    "/appointments/{appointment_id}/cancel", dependencies=[Depends(verify_admin_access)]
)
async def cancel_appointment_admin(
    appointment_id: str,
    payload: AppointmentCancelRequest,
    request: Request,
    x_tenant_id: str = Header(default=""),
) -> dict:
    _require_admin_csrf(request)
    appt_id = _parse_uuid(appointment_id, "Appointment not found")
    service = get_scheduling_service()
    async with AsyncSessionFactory() as session:
        tenant_id = await _resolve_tenant_id(session, x_tenant_id)
        existing = await session.get(Appointment, appt_id)
        if existing is None:
            raise HTTPException(status_code=404, detail="Appointment not found")
        before = {
            "status": existing.status,
            "cancelled_at": existing.cancelled_at.isoformat()
            if existing.cancelled_at
            else None,
            "cancellation_reason": existing.cancellation_reason,
        }

    cancelled = await service.cancel_appointment(appt_id, reason=payload.reason)

    async with AsyncSessionFactory() as session:
        async with session.begin():
            appt = await session.get(Appointment, appt_id)
            if appt is not None:
                appt.tenant_id = appt.tenant_id or tenant_id
            await _write_audit_event(
                session,
                tenant_id=tenant_id,
                actor_username=_actor_username_from_token(request),
                entity_type="appointment",
                entity_id=appt_id,
                action="appointment.cancelled",
                before_json=before,
                after_json={
                    "status": cancelled.status,
                    "cancelled_at": cancelled.cancelled_at.isoformat()
                    if cancelled.cancelled_at
                    else None,
                    "cancellation_reason": cancelled.cancellation_reason,
                },
                request=request,
            )
    return {
        "id": str(cancelled.id),
        "status": cancelled.status,
        "cancelled_at": cancelled.cancelled_at.isoformat() if cancelled.cancelled_at else None,
        "cancellation_reason": cancelled.cancellation_reason,
    }


@router.post(
    "/appointments/{appointment_id}/reschedule",
    dependencies=[Depends(verify_admin_access)],
)
async def reschedule_appointment_admin(
    appointment_id: str,
    payload: AppointmentRescheduleRequest,
    request: Request,
    x_tenant_id: str = Header(default=""),
) -> dict:
    _require_admin_csrf(request)
    appt_id = _parse_uuid(appointment_id, "Appointment not found")
    new_slot_id = _parse_uuid(payload.new_slot_id, "Slot not found")
    service = get_scheduling_service()
    async with AsyncSessionFactory() as session:
        tenant_id = await _resolve_tenant_id(session, x_tenant_id)
        existing = await session.get(Appointment, appt_id)
        if existing is None:
            raise HTTPException(status_code=404, detail="Appointment not found")
        before = {
            "id": str(existing.id),
            "slot_id": str(existing.slot_id),
            "status": existing.status,
        }

    replacement = await service.reschedule_appointment(appt_id, new_slot_id)

    async with AsyncSessionFactory() as session:
        async with session.begin():
            repl = await session.get(Appointment, replacement.id)
            if repl is not None:
                repl.tenant_id = repl.tenant_id or tenant_id
            await _write_audit_event(
                session,
                tenant_id=tenant_id,
                actor_username=_actor_username_from_token(request),
                entity_type="appointment",
                entity_id=replacement.id,
                action="appointment.rescheduled",
                before_json=before,
                after_json={
                    "id": str(replacement.id),
                    "slot_id": str(replacement.slot_id),
                    "status": replacement.status,
                    "rescheduled_from_id": str(replacement.rescheduled_from_id),
                },
                request=request,
            )
    return {
        "id": str(replacement.id),
        "slot_id": str(replacement.slot_id),
        "status": replacement.status,
        "rescheduled_from_id": (
            str(replacement.rescheduled_from_id)
            if replacement.rescheduled_from_id
            else None
        ),
    }


@router.patch(
    "/appointments/{appointment_id}/notes", dependencies=[Depends(verify_admin_access)]
)
async def update_appointment_notes(
    appointment_id: str,
    payload: AppointmentNotesRequest,
    request: Request,
    x_tenant_id: str = Header(default=""),
) -> dict:
    _require_admin_csrf(request)
    appt_id = _parse_uuid(appointment_id, "Appointment not found")
    async with AsyncSessionFactory() as session:
        async with session.begin():
            tenant_id = await _resolve_tenant_id(session, x_tenant_id)
            appt = await session.get(Appointment, appt_id)
            if appt is None:
                raise HTTPException(status_code=404, detail="Appointment not found")
            before = {"notes": appt.notes}
            appt.notes = payload.notes
            appt.tenant_id = appt.tenant_id or tenant_id
            await _write_audit_event(
                session,
                tenant_id=tenant_id,
                actor_username=_actor_username_from_token(request),
                entity_type="appointment",
                entity_id=appt.id,
                action="appointment.notes_updated",
                before_json=before,
                after_json={"notes": appt.notes},
                request=request,
            )
            await session.flush()
            return {"id": str(appt.id), "notes": appt.notes}


@router.post("/appointments/book", dependencies=[Depends(verify_admin_access)])
async def book_appointment_admin(
    payload: AppointmentBookRequest,
    request: Request,
    x_tenant_id: str = Header(default=""),
) -> dict:
    _require_admin_csrf(request)
    contact_id = _parse_uuid(payload.contact_id, "Contact not found")
    slot_id = _parse_uuid(payload.slot_id, "Slot not found")
    service = get_scheduling_service()
    created = await service.book_appointment(contact_id=contact_id, slot_id=slot_id)
    async with AsyncSessionFactory() as session:
        async with session.begin():
            tenant_id = await _resolve_tenant_id(session, x_tenant_id)
            appt = await session.get(Appointment, created.id)
            if appt is not None:
                appt.tenant_id = appt.tenant_id or tenant_id
            await _write_audit_event(
                session,
                tenant_id=tenant_id,
                actor_username=_actor_username_from_token(request),
                entity_type="appointment",
                entity_id=created.id,
                action="appointment.booked",
                before_json={},
                after_json={
                    "contact_id": payload.contact_id,
                    "slot_id": payload.slot_id,
                    "status": created.status,
                },
                request=request,
            )
    return {
        "id": str(created.id),
        "contact_id": str(created.contact_id),
        "slot_id": str(created.slot_id),
        "status": created.status,
        "booked_at": created.booked_at.isoformat(),
    }


@router.get(
    "/appointments",
    response_model=list[AppointmentResponse],
    dependencies=[Depends(verify_admin_access)],
)
async def list_appointments(contact_id: str) -> list[dict]:
    cid = uuid.UUID(contact_id)
    async with AsyncSessionFactory() as session:
        tenant_id = await _resolve_tenant_id(session)
        query = (
            select(Appointment)
            .where(Appointment.contact_id == cid)
            .order_by(Appointment.booked_at.desc())
        )
        scope = _scope_filter(Appointment, tenant_id)
        if scope is not None:
            query = query.where(scope)
        result = await session.execute(query)
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
async def list_conversations(limit: int = 50, offset: int = 0) -> dict:
    async with AsyncSessionFactory() as session:
        total = (await session.execute(select(func.count(ConversationState.id)))).scalar_one()
        result = await session.execute(
            select(ConversationState, Contact)
            .join(Contact, ConversationState.contact_id == Contact.id)
            .order_by(ConversationState.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        rows = result.all()
        return {
            "data": [
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
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(rows) < total,
        }


@router.get("/slots", dependencies=[Depends(verify_admin_access)])
async def list_slots(days_ahead: int = 7, x_tenant_id: str = Header(default="")) -> list[dict]:
    now = datetime.now(timezone.utc)
    end = now + timedelta(days=days_ahead)

    async with AsyncSessionFactory() as session:
        tenant_id = await _resolve_tenant_id(session, x_tenant_id)
        query = (
            select(AvailabilitySlot)
            .where(
                and_(
                    AvailabilitySlot.start_time >= now,
                    AvailabilitySlot.start_time <= end,
                )
            )
            .order_by(AvailabilitySlot.start_time.asc())
        )
        scope = _scope_filter(AvailabilitySlot, tenant_id)
        if scope is not None:
            query = query.where(scope)
        result = await session.execute(query)
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
async def list_messages(contact_id: str, x_tenant_id: str = Header(default="")) -> list[dict]:
    cid = uuid.UUID(contact_id)
    async with AsyncSessionFactory() as session:
        tenant_id = await _resolve_tenant_id(session, x_tenant_id)
        query = (
            select(Message)
            .where(Message.contact_id == cid)
            .order_by(Message.created_at.desc())
        )
        scope = _scope_filter(Message, tenant_id)
        if scope is not None:
            query = query.where(scope)
        result = await session.execute(query)
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


@router.get("/audit-events", dependencies=[Depends(verify_admin_access)])
async def list_audit_events(
    entity_type: str = "",
    entity_id: str = "",
    limit: int = 50,
    x_tenant_id: str = Header(default=""),
) -> list[dict]:
    async with AsyncSessionFactory() as session:
        tenant_id = await _resolve_tenant_id(session, x_tenant_id)
        query = select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(limit)
        if tenant_id is not None:
            query = query.where(
                or_(AuditEvent.tenant_id == tenant_id, AuditEvent.tenant_id.is_(None))
            )
        if entity_type:
            query = query.where(AuditEvent.entity_type == entity_type)
        if entity_id:
            query = query.where(AuditEvent.entity_id == _parse_uuid(entity_id, "Invalid id"))
        rows = (await session.execute(query)).scalars().all()
        return [
            {
                "id": str(row.id),
                "entity_type": row.entity_type,
                "entity_id": str(row.entity_id) if row.entity_id else None,
                "action": row.action,
                "actor_username": row.actor_username,
                "before_json": row.before_json or {},
                "after_json": row.after_json or {},
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]


@router.get("/waitlist", dependencies=[Depends(verify_admin_access)])
async def list_waitlist(
    status: str = "open",
    limit: int = 100,
    x_tenant_id: str = Header(default=""),
) -> list[dict]:
    async with AsyncSessionFactory() as session:
        tenant_id = await _resolve_tenant_id(session, x_tenant_id)
        query = (
            select(WaitlistEntry, Contact)
            .join(Contact, WaitlistEntry.contact_id == Contact.id)
            .order_by(WaitlistEntry.created_at.desc())
            .limit(limit)
        )
        if status:
            query = query.where(WaitlistEntry.status == status)
        if tenant_id is not None:
            query = query.where(
                or_(WaitlistEntry.tenant_id == tenant_id, WaitlistEntry.tenant_id.is_(None))
            )
        rows = (await session.execute(query)).all()
        return [
            {
                "id": str(entry.id),
                "contact_id": str(entry.contact_id),
                "contact_name": _display_name(contact),
                "contact_phone": contact.phone_number,
                "status": entry.status,
                "desired_start": entry.desired_start.isoformat()
                if entry.desired_start
                else None,
                "desired_end": entry.desired_end.isoformat() if entry.desired_end else None,
                "notes": entry.notes,
                "created_at": entry.created_at.isoformat(),
            }
            for entry, contact in rows
        ]


@router.post("/waitlist", dependencies=[Depends(verify_admin_access)])
async def create_waitlist_entry(
    payload: WaitlistCreateRequest,
    request: Request,
    x_tenant_id: str = Header(default=""),
) -> dict:
    _require_admin_csrf(request)
    contact_id = _parse_uuid(payload.contact_id, "Contact not found")
    async with AsyncSessionFactory() as session:
        async with session.begin():
            tenant_id = await _resolve_tenant_id(session, x_tenant_id)
            contact = await session.get(Contact, contact_id)
            if contact is None:
                raise HTTPException(status_code=404, detail="Contact not found")
            entry = WaitlistEntry(
                tenant_id=tenant_id,
                contact_id=contact_id,
                desired_start=payload.desired_start,
                desired_end=payload.desired_end,
                notes=payload.notes,
            )
            session.add(entry)
            await session.flush()
            await _write_audit_event(
                session,
                tenant_id=tenant_id,
                actor_username=_actor_username_from_token(request),
                entity_type="waitlist_entry",
                entity_id=entry.id,
                action="waitlist.created",
                before_json={},
                after_json={
                    "contact_id": payload.contact_id,
                    "status": entry.status,
                },
                request=request,
            )
            return {"id": str(entry.id), "status": entry.status}


@router.patch("/waitlist/{entry_id}", dependencies=[Depends(verify_admin_access)])
async def patch_waitlist_entry(
    entry_id: str,
    payload: WaitlistPatchRequest,
    request: Request,
    x_tenant_id: str = Header(default=""),
) -> dict:
    _require_admin_csrf(request)
    wid = _parse_uuid(entry_id, "Waitlist entry not found")
    async with AsyncSessionFactory() as session:
        async with session.begin():
            tenant_id = await _resolve_tenant_id(session, x_tenant_id)
            entry = await session.get(WaitlistEntry, wid)
            if entry is None:
                raise HTTPException(status_code=404, detail="Waitlist entry not found")
            before = {"status": entry.status, "notes": entry.notes}
            if payload.status is not None:
                entry.status = payload.status
            if payload.notes is not None:
                entry.notes = payload.notes
            entry.tenant_id = entry.tenant_id or tenant_id
            await _write_audit_event(
                session,
                tenant_id=tenant_id,
                actor_username=_actor_username_from_token(request),
                entity_type="waitlist_entry",
                entity_id=entry.id,
                action="waitlist.updated",
                before_json=before,
                after_json={"status": entry.status, "notes": entry.notes},
                request=request,
            )
            return {"id": str(entry.id), "status": entry.status, "notes": entry.notes}


@router.get("/reminder-workflows", dependencies=[Depends(verify_admin_access)])
async def list_reminder_workflows(x_tenant_id: str = Header(default="")) -> list[dict]:
    async with AsyncSessionFactory() as session:
        tenant_id = await _resolve_tenant_id(session, x_tenant_id)
        query = select(ReminderWorkflow).order_by(ReminderWorkflow.created_at.desc())
        if tenant_id is not None:
            query = query.where(
                or_(
                    ReminderWorkflow.tenant_id == tenant_id,
                    ReminderWorkflow.tenant_id.is_(None),
                )
            )
        rows = (await session.execute(query)).scalars().all()
        return [
            {
                "id": str(row.id),
                "name": row.name,
                "appointment_status": row.appointment_status,
                "minutes_before": row.minutes_before,
                "channel": row.channel,
                "template": row.template,
                "is_active": row.is_active,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]


@router.post("/reminder-workflows", dependencies=[Depends(verify_admin_access)])
async def create_reminder_workflow(
    payload: ReminderWorkflowCreateRequest,
    request: Request,
    x_tenant_id: str = Header(default=""),
) -> dict:
    _require_admin_csrf(request)
    async with AsyncSessionFactory() as session:
        async with session.begin():
            tenant_id = await _resolve_tenant_id(session, x_tenant_id)
            workflow = ReminderWorkflow(
                tenant_id=tenant_id,
                name=payload.name.strip(),
                appointment_status=payload.appointment_status,
                minutes_before=payload.minutes_before,
                channel=payload.channel,
                template=payload.template.strip(),
                is_active=payload.is_active,
            )
            session.add(workflow)
            await session.flush()
            await _write_audit_event(
                session,
                tenant_id=tenant_id,
                actor_username=_actor_username_from_token(request),
                entity_type="reminder_workflow",
                entity_id=workflow.id,
                action="workflow.created",
                before_json={},
                after_json={"name": workflow.name, "minutes_before": workflow.minutes_before},
                request=request,
            )
            return {"id": str(workflow.id), "name": workflow.name}


@router.patch(
    "/reminder-workflows/{workflow_id}", dependencies=[Depends(verify_admin_access)]
)
async def patch_reminder_workflow(
    workflow_id: str,
    payload: ReminderWorkflowPatchRequest,
    request: Request,
    x_tenant_id: str = Header(default=""),
) -> dict:
    _require_admin_csrf(request)
    wid = _parse_uuid(workflow_id, "Workflow not found")
    async with AsyncSessionFactory() as session:
        async with session.begin():
            tenant_id = await _resolve_tenant_id(session, x_tenant_id)
            workflow = await session.get(ReminderWorkflow, wid)
            if workflow is None:
                raise HTTPException(status_code=404, detail="Workflow not found")
            before = {
                "name": workflow.name,
                "minutes_before": workflow.minutes_before,
                "is_active": workflow.is_active,
            }
            for key, value in payload.model_dump(exclude_none=True).items():
                setattr(workflow, key, value)
            workflow.tenant_id = workflow.tenant_id or tenant_id
            await _write_audit_event(
                session,
                tenant_id=tenant_id,
                actor_username=_actor_username_from_token(request),
                entity_type="reminder_workflow",
                entity_id=workflow.id,
                action="workflow.updated",
                before_json=before,
                after_json={
                    "name": workflow.name,
                    "minutes_before": workflow.minutes_before,
                    "is_active": workflow.is_active,
                },
                request=request,
            )
            return {
                "id": str(workflow.id),
                "name": workflow.name,
                "minutes_before": workflow.minutes_before,
                "is_active": workflow.is_active,
            }


@router.post("/admin-users", dependencies=[Depends(verify_admin_access)])
async def create_admin_user(
    payload: AdminUserCreateRequest,
    request: Request,
    x_tenant_id: str = Header(default=""),
) -> dict:
    _require_admin_csrf(request)
    async with AsyncSessionFactory() as session:
        async with session.begin():
            tenant_id = await _resolve_tenant_id(session, x_tenant_id)
            existing = await session.execute(
                select(AdminUser).where(AdminUser.username == payload.username)
            )
            if existing.scalar_one_or_none() is not None:
                raise HTTPException(status_code=400, detail="Username already exists")

            user = AdminUser(
                tenant_id=tenant_id,
                username=payload.username.strip(),
                role=payload.role.strip(),
                is_active=payload.is_active,
            )
            session.add(user)
            await session.flush()
            await _write_audit_event(
                session,
                tenant_id=tenant_id,
                actor_username=_actor_username_from_token(request),
                entity_type="admin_user",
                entity_id=user.id,
                action="admin_user.created",
                before_json={},
                after_json={
                    "username": user.username,
                    "role": user.role,
                    "is_active": user.is_active,
                },
                request=request,
            )
            return {
                "id": str(user.id),
                "username": user.username,
                "role": user.role,
                "is_active": user.is_active,
            }


@router.get("/admin-users", dependencies=[Depends(verify_admin_access)])
async def list_admin_users(x_tenant_id: str = Header(default="")) -> list[dict]:
    async with AsyncSessionFactory() as session:
        tenant_id = await _resolve_tenant_id(session, x_tenant_id)
        query = select(AdminUser).order_by(AdminUser.created_at.asc())
        if tenant_id is not None:
            query = query.where(
                or_(AdminUser.tenant_id == tenant_id, AdminUser.tenant_id.is_(None))
            )
        rows = (await session.execute(query)).scalars().all()
        return [
            {
                "id": str(row.id),
                "username": row.username,
                "role": row.role,
                "is_active": row.is_active,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]


@router.post(
    "/simulate/inbound",
    dependencies=[Depends(verify_admin_access)],
)
async def simulate_inbound(payload: SimulateRequest, request: Request) -> dict:
    rate_limit(request, "simulate", max_requests=30, window=60)
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
    simulator_sms_sid = f"SIM_{uuid.uuid4().hex[:16]}"

    async with AsyncSessionFactory() as session:
        contact = await fake_sms._get_or_create_contact(session, payload.phone_number)
        inbound = Message(
            contact_id=contact.id,
            direction="inbound",
            body=payload.message,
            status="received",
            sms_sid=simulator_sms_sid,
        )
        session.add(inbound)
        await session.commit()

    await conv_service.process_inbound_message(
        phone_number=payload.phone_number,
        body=payload.message,
        sms_sid=simulator_sms_sid,
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
