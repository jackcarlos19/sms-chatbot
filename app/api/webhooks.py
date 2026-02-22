from __future__ import annotations

import structlog
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, Response
from urllib.parse import parse_qs

from app.api.deps import get_conversation_service, get_idempotency_service, get_sms_service
from app.core.masking import mask_phone_number

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/webhooks/sms", tags=["webhooks"])


def _reconstruct_url(request: Request) -> str:
    """Build the URL Twilio signed against.

    Behind ngrok, load balancers, or any TLS terminator the incoming
    request.url uses http:// while Twilio signed with https://.
    X-Forwarded-Proto tells us the original scheme.
    """
    proto = request.headers.get("X-Forwarded-Proto", request.url.scheme)
    host = request.headers.get("X-Forwarded-Host", request.url.netloc)
    return f"{proto}://{host}{request.url.path}"


async def _parse_twilio_payload(request: Request) -> dict[str, str]:
    raw_body = (await request.body()).decode("utf-8")
    parsed = parse_qs(raw_body, keep_blank_values=True)
    return {key: values[0] if values else "" for key, values in parsed.items()}


async def _process_inbound_background(
    from_number: str, body: str, sms_sid: str
) -> None:
    """Runs inside BackgroundTasks — must catch all exceptions or they vanish."""
    try:
        sms_service = get_sms_service()
        conversation_service = get_conversation_service()
        await sms_service.handle_inbound(
            from_number, body, sms_sid,
            conversation_service=conversation_service,
        )
    except Exception as exc:  # noqa: BLE001
        logger.error(
            "background_inbound_processing_failed",
            from_number=mask_phone_number(from_number),
            sms_sid=sms_sid,
            error=str(exc),
            exc_info=True,
        )


@router.post("/inbound")
async def inbound_sms(request: Request, background_tasks: BackgroundTasks) -> Response:
    form = await _parse_twilio_payload(request)
    from_number = form.get("From", "")
    body = form.get("Body", "")
    sms_sid = form.get("MessageSid", "")
    request.state.reply_phone = from_number
    signature = request.headers.get("X-Twilio-Signature", "")

    sms_service = get_sms_service()
    validated_url = _reconstruct_url(request)
    if not sms_service.validate_signature(validated_url, form, signature):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    idempotency_service = get_idempotency_service()
    if await idempotency_service.is_duplicate(sms_sid):
        logger.info(
            "duplicate_inbound_skipped",
            from_number=mask_phone_number(from_number),
            sms_sid=sms_sid,
        )
        return Response(content="<Response></Response>", media_type="application/xml")

    await idempotency_service.mark_processed(sms_sid)
    background_tasks.add_task(_process_inbound_background, from_number, body, sms_sid)

    return Response(content="<Response></Response>", media_type="application/xml")


@router.post("/status")
async def sms_status_callback(request: Request) -> Response:
    form = await _parse_twilio_payload(request)
    sms_sid = form.get("MessageSid", "")
    message_status = form.get("MessageStatus", "")
    error_code = form.get("ErrorCode", "") or None
    error_message = form.get("ErrorMessage", "") or None
    signature = request.headers.get("X-Twilio-Signature", "")

    sms_service = get_sms_service()
    validated_url = _reconstruct_url(request)
    if not sms_service.validate_signature(validated_url, form, signature):
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    await sms_service.update_status(
        sms_sid=sms_sid,
        status=message_status,
        error_code=error_code,
        error_message=error_message,
    )
    return Response(status_code=200)
