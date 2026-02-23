from __future__ import annotations

import asyncio
import re
from typing import Any

import structlog
from sqlalchemy import select
from twilio.base.exceptions import TwilioRestException
from twilio.request_validator import RequestValidator
from twilio.rest import Client

from app.config import get_settings
from app.core.compliance import handle_compliance, is_compliance_keyword
from app.core.masking import mask_phone_number
from app.database import AsyncSessionFactory
from app.models.contact import Contact
from app.models.message import Message

logger = structlog.get_logger(__name__)
E164_REGEX = re.compile(r"^\+[1-9]\d{1,14}$")
NON_RETRYABLE_TWILIO_CODES = {"21211", "21610"}


class ContactOptedOutError(Exception):
    pass


class SMSService:
    def __init__(self, twilio_client: Client | None = None) -> None:
        self._settings = get_settings()
        self._client = twilio_client or Client(
            self._settings.twilio_account_sid, self._settings.twilio_auth_token
        )
        self._validator = RequestValidator(self._settings.twilio_auth_token)

    def validate_signature(
        self, url: str, params: dict[str, str], signature: str
    ) -> bool:
        return self._validator.validate(url, params, signature or "")

    async def send_message(
        self,
        to: str,
        body: str,
        campaign_id: str | None = None,
        force_send: bool = False,
    ) -> Message:
        if not E164_REGEX.match(to):
            raise ValueError(f"Invalid phone number format: {to}")

        async with AsyncSessionFactory() as session:
            contact = await self._get_or_create_contact(session, to)
            if contact.opt_in_status == "opted_out" and not force_send:
                raise ContactOptedOutError(f"Contact {to} has opted out.")

            message = Message(
                contact_id=contact.id,
                direction="outbound",
                body=body,
                status="queued",
                campaign_id=campaign_id,
            )
            session.add(message)
            await session.flush()

            for attempt in range(3):
                retry_delay = 2**attempt
                try:
                    logger.info(
                        "sending_sms_attempt",
                        to=mask_phone_number(to),
                        attempt=attempt + 1,
                    )
                    twilio_message = await asyncio.to_thread(
                        self._client.messages.create,
                        body=body,
                        from_=self._settings.twilio_phone_number,
                        to=to,
                        status_callback=self._settings.twilio_status_callback_url,
                    )
                    message.sms_sid = twilio_message.sid
                    message.status = "sent"
                    await session.commit()
                    await session.refresh(message)
                    return message
                except TwilioRestException as exc:
                    twilio_code = str(exc.code) if exc.code is not None else ""
                    is_retryable = (
                        exc.status in {429, 500, 502, 503, 504}
                        and twilio_code not in NON_RETRYABLE_TWILIO_CODES
                    )
                    logger.warning(
                        "send_sms_failed",
                        to=mask_phone_number(to),
                        attempt=attempt + 1,
                        status=exc.status,
                        code=twilio_code,
                    )
                    if attempt == 2 or not is_retryable:
                        message.status = "failed"
                        message.error_code = twilio_code or None
                        message.error_message = str(exc)
                        await session.commit()
                        raise
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "send_sms_exception",
                        to=mask_phone_number(to),
                        attempt=attempt + 1,
                        error=str(exc),
                    )
                    if attempt == 2:
                        message.status = "failed"
                        message.error_message = str(exc)
                        await session.commit()
                        raise

                await asyncio.sleep(retry_delay)

        raise RuntimeError("Failed to send message after retries")

    async def retry_send(self, body: str, to: str) -> str:
        """Retry sending via Twilio and return the new message SID."""
        twilio_msg = await asyncio.to_thread(
            self._client.messages.create,
            body=body,
            from_=self._settings.twilio_phone_number,
            to=to,
            status_callback=self._settings.twilio_status_callback_url,
        )
        return str(twilio_msg.sid)

    async def handle_inbound(
        self,
        from_number: str,
        body: str,
        sms_sid: str,
        conversation_service: Any = None,
    ) -> None:
        """Process an inbound SMS. Called as a BackgroundTask after webhook returns 200.

        Flow:
        1. Log inbound message to database
        2. Check compliance keywords (STOP/START/HELP) — handle immediately
        3. Route to conversation service for AI-powered processing
        """
        logger.info(
            "inbound_sms_received",
            from_number=mask_phone_number(from_number),
            sms_sid=sms_sid,
        )
        async with AsyncSessionFactory() as session:
            contact = await self._get_or_create_contact(session, from_number)
            inbound_message = Message(
                contact_id=contact.id,
                direction="inbound",
                body=body,
                sms_sid=sms_sid,
                status="received",
            )
            session.add(inbound_message)

            is_keyword, keyword_type = is_compliance_keyword(body)
            if is_keyword and keyword_type:
                response_text = handle_compliance(
                    contact=contact,
                    keyword_type=keyword_type,
                    business_name=self._settings.business_name,
                    support_number=self._settings.support_phone_number,
                )
                await session.commit()
                await self.send_message(from_number, response_text, force_send=True)
                logger.info(
                    "compliance_keyword_handled",
                    from_number=mask_phone_number(from_number),
                    keyword_type=keyword_type,
                )
                return

            await session.commit()

        # Route non-compliance messages to the conversation engine
        if conversation_service is not None:
            await conversation_service.process_inbound_message(
                phone_number=from_number, body=body, sms_sid=sms_sid
            )
        else:
            logger.warning(
                "no_conversation_service",
                from_number=mask_phone_number(from_number),
                sms_sid=sms_sid,
            )

    async def update_status(
        self,
        sms_sid: str,
        status: str,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> None:
        async with AsyncSessionFactory() as session:
            message_result = await session.execute(
                select(Message).where(Message.sms_sid == sms_sid)
            )
            message = message_result.scalar_one_or_none()
            if message is None:
                logger.warning("status_update_missing_message", sms_sid=sms_sid)
                return

            message.status = status
            message.error_code = error_code
            message.error_message = error_message
            await session.commit()

    async def _get_or_create_contact(self, session: Any, phone_number: str) -> Contact:
        result = await session.execute(
            select(Contact).where(Contact.phone_number == phone_number)
        )
        contact = result.scalar_one_or_none()
        if contact is not None:
            return contact

        contact = Contact(phone_number=phone_number, opt_in_status="pending")
        session.add(contact)
        await session.flush()
        return contact
