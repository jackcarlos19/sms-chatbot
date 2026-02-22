from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, Response
import structlog
from urllib.parse import parse_qs

from app.core.idempotency import IdempotencyService
from app.core.masking import mask_phone_number
from app.services.sms_service import SMSService

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/webhooks/sms", tags=["webhooks"])
sms_service = SMSService()
idempotency_service = IdempotencyService()


async def _parse_twilio_payload(request: Request) -> dict[str, str]:
    raw_body = (await request.body()).decode("utf-8")
    parsed = parse_qs(raw_body, keep_blank_values=True)
    return {key: values[0] if values else "" for key, values in parsed.items()}


@router.post("/inbound")
async def inbound_sms(request: Request, background_tasks: BackgroundTasks) -> Response:
    form = await _parse_twilio_payload(request)
    from_number = form.get("From", "")
    body = form.get("Body", "")
    sms_sid = form.get("MessageSid", "")
    request.state.reply_phone = from_number
    signature = request.headers.get("X-Twilio-Signature", "")

    if not sms_service.validate_signature(str(request.url), form, signature):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    if await idempotency_service.is_duplicate(sms_sid):
        logger.info(
            "duplicate_inbound_skipped",
            from_number=mask_phone_number(from_number),
            sms_sid=sms_sid,
        )
        return Response(content="<Response></Response>", media_type="application/xml")

    await idempotency_service.mark_processed(sms_sid)
    background_tasks.add_task(sms_service.handle_inbound, from_number, body, sms_sid)

    return Response(content="<Response></Response>", media_type="application/xml")


@router.post("/status")
async def sms_status_callback(request: Request) -> Response:
    form = await _parse_twilio_payload(request)
    sms_sid = form.get("MessageSid", "")
    message_status = form.get("MessageStatus", "")
    error_code = form.get("ErrorCode", "") or None
    error_message = form.get("ErrorMessage", "") or None
    signature = request.headers.get("X-Twilio-Signature", "")

    if not sms_service.validate_signature(str(request.url), form, signature):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    await sms_service.update_status(
        sms_sid=sms_sid,
        status=message_status,
        error_code=error_code,
        error_message=error_message,
    )
    return Response(status_code=200)
