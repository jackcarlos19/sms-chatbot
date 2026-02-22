from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from zoneinfo import ZoneInfo

from sqlalchemy import select

from app.config import get_settings
from app.core.compliance import handle_compliance, is_compliance_keyword
from app.core.exceptions import SlotUnavailableError
from app.database import AsyncSessionFactory
from app.models.appointment import Appointment
from app.models.availability import AvailabilitySlot
from app.models.contact import Contact
from app.models.conversation import ConversationState
from app.services.ai_service import AIService, IntentResult
from app.services.scheduling_service import SchedulingService
from app.services.sms_service import SMSService

MAX_RETRIES = 3
STRICT_COMPLIANCE_KEYWORDS = {
    "STOP",
    "STOPALL",
    "UNSUBSCRIBE",
    "END",
    "QUIT",
    "START",
    "HELP",
    "INFO",
}


class ConversationService:
    def __init__(
        self,
        ai_service: Optional[AIService] = None,
        scheduling_service: Optional[SchedulingService] = None,
        sms_service: Optional[SMSService] = None,
    ) -> None:
        self._settings = get_settings()
        self._ai = ai_service or AIService()
        self._scheduling = scheduling_service or SchedulingService()
        self._sms = sms_service or SMSService()

    async def process_inbound_message(self, phone_number: str, body: str, sms_sid: str) -> None:
        contact = await self._get_or_create_contact(phone_number)
        normalized_body = (body or "").strip()
        normalized_upper = normalized_body.upper()

        # Compliance check is intentionally FIRST and short-circuits AI/state routing.
        is_keyword, keyword_type = is_compliance_keyword(normalized_body)
        if is_keyword and keyword_type and normalized_upper in STRICT_COMPLIANCE_KEYWORDS:
            response = handle_compliance(
                contact=contact,
                keyword_type=keyword_type,
                business_name=self._settings.business_name,
                support_number=self._settings.support_phone_number,
            )
            await self._save_contact(contact)
            await self._sms.send_message(
                to=contact.phone_number,
                body=response,
                force_send=True,
            )
            return

        state = await self._get_or_create_state(contact.id)
        context = dict(state.context or {})
        history = list(context.get("history", []))

        next_state, response_text, next_context = await self._dispatch_state_handler(
            current_state=state.current_state or "idle",
            contact=contact,
            message=normalized_body,
            context=context,
            history=history,
        )

        updated_history = self._append_history(
            history=history,
            user_message=normalized_body,
            assistant_message=response_text,
        )
        next_context["history"] = updated_history
        state.current_state = next_state
        state.context = next_context
        state.last_message_at = datetime.now(timezone.utc)
        state.expires_at = (
            datetime.now(timezone.utc) + timedelta(hours=2) if next_state != "idle" else None
        )
        await self._save_state(state)

        if response_text:
            await self._sms.send_message(to=contact.phone_number, body=response_text)

    async def _dispatch_state_handler(
        self,
        current_state: str,
        contact: Contact,
        message: str,
        context: dict[str, Any],
        history: list[dict[str, str]],
    ) -> tuple[str, str, dict[str, Any]]:
        handlers = {
            "idle": self._handle_idle,
            "showing_slots": self._handle_showing_slots,
            "confirming_booking": self._handle_confirming_booking,
            "confirming_cancel": self._handle_confirming_cancel,
            "reschedule_show_slots": self._handle_reschedule_show_slots,
            "confirming_reschedule": self._handle_confirming_reschedule,
            "awaiting_info": self._handle_awaiting_info,
        }
        handler = handlers.get(current_state, self._handle_idle)
        return await handler(contact=contact, message=message, context=context, history=history)

    async def _handle_idle(
        self,
        contact: Contact,
        message: str,
        context: dict[str, Any],
        history: list[dict[str, str]],
    ) -> tuple[str, str, dict[str, Any]]:
        intent = await self._detect_intent(contact=contact, message=message, history=history, context=context)

        if intent.intent == "BOOK":
            return await self._begin_booking(contact, intent, history)

        if intent.intent == "CANCEL":
            appointments = await self._get_contact_appointments(contact.id, status_filter=["confirmed"])
            if not appointments:
                return "idle", "I couldn't find an active appointment to cancel.", {"retry_count": 0}
            appt = appointments[0]
            slot = await self._get_slot(appt.slot_id)
            when_text = (
                self._ai.generate_confirmation({"start_time": slot.start_time}, contact.timezone)
                if slot is not None
                else "your appointment"
            )
            prompt = (
                f"I found {when_text}. Reply YES to confirm cancellation or NO to keep it."
            )
            return "confirming_cancel", prompt, {
                "pending_appointment_id": str(appt.id),
                "retry_count": 0,
                "last_intent": "CANCEL",
            }

        if intent.intent == "RESCHEDULE":
            appointments = await self._get_contact_appointments(contact.id, status_filter=["confirmed"])
            if not appointments:
                return "idle", "I couldn't find an active appointment to reschedule.", {"retry_count": 0}
            original = appointments[0]
            alternatives = await self._scheduling.get_fresh_alternatives(
                exclude_slot_ids=[original.slot_id],
                limit=5,
            )
            if not alternatives:
                return "idle", "I don't see alternative slots right now. Please try again soon.", {"retry_count": 0}
            presented = self._serialize_presented_slots(alternatives, contact.timezone)
            prompt = self._ai.generate_slot_presentation(presented, contact.timezone)
            return "reschedule_show_slots", prompt, {
                "original_appointment_id": str(original.id),
                "presented_slots": presented,
                "retry_count": 0,
                "last_intent": "RESCHEDULE",
            }

        if intent.intent in {"QUESTION", "UNCLEAR"}:
            if intent.needs_info:
                return "awaiting_info", intent.response_text, {
                    "retry_count": int(context.get("retry_count", 0)),
                    "last_intent": intent.intent,
                }
            return "idle", intent.response_text, {"retry_count": 0, "last_intent": intent.intent}

        if intent.intent in {"CONFIRM", "DENY", "SELECT_SLOT"}:
            return (
                "idle",
                "I can help you book, reschedule, or cancel. What would you like to do?",
                {"retry_count": 0, "last_intent": intent.intent},
            )

        return "idle", intent.response_text, {"retry_count": 0, "last_intent": intent.intent}

    async def _handle_showing_slots(
        self,
        contact: Contact,
        message: str,
        context: dict[str, Any],
        history: list[dict[str, str]],
    ) -> tuple[str, str, dict[str, Any]]:
        presented = list(context.get("presented_slots", []))
        intent = await self._detect_intent(contact=contact, message=message, history=history, context=context)

        if intent.intent in {"CANCEL", "RESCHEDULE"}:
            return await self._handle_idle(contact=contact, message=message, context=context, history=history)

        selected_slot_id = await self._ai.parse_slot_selection(message=message, presented_slots=presented)
        if selected_slot_id is None:
            retry_count = int(context.get("retry_count", 0)) + 1
            if retry_count >= MAX_RETRIES:
                return (
                    "idle",
                    "Let's reset. Reply BOOK whenever you're ready and I will share fresh times.",
                    {"retry_count": 0},
                )
            return (
                "showing_slots",
                "I didn't catch that slot. Reply with the number from the list.",
                {
                    **context,
                    "retry_count": retry_count,
                    "last_intent": intent.intent,
                },
            )

        display_value = self._find_presented_slot_display(presented, selected_slot_id)
        return (
            "confirming_booking",
            f"Great, should I book {display_value}? Reply YES to confirm or NO to pick another time.",
            {
                **context,
                "selected_slot_id": selected_slot_id,
                "retry_count": 0,
                "last_intent": "SELECT_SLOT",
            },
        )

    async def _handle_confirming_booking(
        self,
        contact: Contact,
        message: str,
        context: dict[str, Any],
        history: list[dict[str, str]],
    ) -> tuple[str, str, dict[str, Any]]:
        intent = await self._detect_intent(contact=contact, message=message, history=history, context=context)

        if intent.intent == "CANCEL":
            return await self._handle_idle(contact=contact, message=message, context=context, history=history)

        if intent.intent == "DENY":
            return (
                "showing_slots",
                "No problem. Reply with another slot number when ready.",
                {
                    **context,
                    "selected_slot_id": None,
                    "last_intent": "DENY",
                },
            )

        if intent.intent != "CONFIRM":
            return (
                "confirming_booking",
                "Please reply YES to confirm this slot or NO to choose another.",
                context,
            )

        selected_slot = context.get("selected_slot_id")
        if not selected_slot:
            return "showing_slots", "Let's pick a slot first. Reply with a slot number.", context

        try:
            appointment = await self._scheduling.book_appointment(
                contact_id=contact.id,
                slot_id=uuid.UUID(str(selected_slot)),
            )
            slot = await self._get_slot(appointment.slot_id)
            confirmation = self._ai.generate_confirmation(
                {"start_time": slot.start_time if slot else None},
                contact.timezone,
            )
            return "idle", confirmation, {"retry_count": 0, "last_intent": "BOOK"}
        except SlotUnavailableError:
            selected_uuid = uuid.UUID(str(selected_slot))
            alternatives = await self._scheduling.get_fresh_alternatives(
                exclude_slot_ids=[selected_uuid],
                limit=5,
            )
            if not alternatives:
                return "idle", "Sorry, that slot was taken and I have no fresh alternatives yet.", {"retry_count": 0}
            presented = self._serialize_presented_slots(alternatives, contact.timezone)
            prompt = (
                "Sorry, that slot was just booked by someone else.\n"
                + self._ai.generate_slot_presentation(presented, contact.timezone)
            )
            return (
                "showing_slots",
                prompt,
                {
                    "presented_slots": presented,
                    "retry_count": 0,
                    "last_intent": "BOOK",
                },
            )

    async def _handle_confirming_cancel(
        self,
        contact: Contact,
        message: str,
        context: dict[str, Any],
        history: list[dict[str, str]],
    ) -> tuple[str, str, dict[str, Any]]:
        intent = await self._detect_intent(contact=contact, message=message, history=history, context=context)
        appointment_id = context.get("pending_appointment_id")
        if intent.intent != "CONFIRM":
            return "idle", "OK, your appointment is still on the books.", {"retry_count": 0, "last_intent": "DENY"}
        if not appointment_id:
            return "idle", "I couldn't find the appointment to cancel.", {"retry_count": 0}

        await self._scheduling.cancel_appointment(uuid.UUID(str(appointment_id)))
        return "idle", "Done - your appointment is cancelled.", {"retry_count": 0, "last_intent": "CANCEL"}

    async def _handle_reschedule_show_slots(
        self,
        contact: Contact,
        message: str,
        context: dict[str, Any],
        history: list[dict[str, str]],
    ) -> tuple[str, str, dict[str, Any]]:
        intent = await self._detect_intent(contact=contact, message=message, history=history, context=context)
        if intent.intent == "CANCEL":
            return await self._handle_idle(contact=contact, message=message, context=context, history=history)

        presented = list(context.get("presented_slots", []))
        selected_slot_id = await self._ai.parse_slot_selection(message=message, presented_slots=presented)
        if selected_slot_id is None:
            retry_count = int(context.get("retry_count", 0)) + 1
            if retry_count >= MAX_RETRIES:
                return (
                    "idle",
                    "Let's reset for now. Reply RESCHEDULE when you want to try again.",
                    {"retry_count": 0},
                )
            return (
                "reschedule_show_slots",
                "I didn't catch that slot. Reply with one of the slot numbers.",
                {**context, "retry_count": retry_count},
            )

        selected_display = self._find_presented_slot_display(presented, selected_slot_id)
        return (
            "confirming_reschedule",
            f"Perfect - should I move your appointment to {selected_display}? Reply YES or NO.",
            {
                **context,
                "selected_slot_id": selected_slot_id,
                "retry_count": 0,
                "last_intent": "RESCHEDULE",
            },
        )

    async def _handle_confirming_reschedule(
        self,
        contact: Contact,
        message: str,
        context: dict[str, Any],
        history: list[dict[str, str]],
    ) -> tuple[str, str, dict[str, Any]]:
        intent = await self._detect_intent(contact=contact, message=message, history=history, context=context)
        if intent.intent == "DENY":
            return "idle", "No changes made. Your current appointment remains booked.", {"retry_count": 0}
        if intent.intent != "CONFIRM":
            return "confirming_reschedule", "Please reply YES to confirm the reschedule or NO to keep it.", context

        original_id = context.get("original_appointment_id")
        selected_slot_id = context.get("selected_slot_id")
        if not original_id or not selected_slot_id:
            return "idle", "I couldn't finish the reschedule flow. Let's try again.", {"retry_count": 0}

        try:
            replacement = await self._scheduling.reschedule_appointment(
                appointment_id=uuid.UUID(str(original_id)),
                new_slot_id=uuid.UUID(str(selected_slot_id)),
            )
            slot = await self._get_slot(replacement.slot_id)
            confirmation = self._ai.generate_confirmation(
                {"start_time": slot.start_time if slot else None},
                contact.timezone,
            )
            return "idle", confirmation, {"retry_count": 0, "last_intent": "RESCHEDULE"}
        except SlotUnavailableError:
            selected_uuid = uuid.UUID(str(selected_slot_id))
            alternatives = await self._scheduling.get_fresh_alternatives(
                exclude_slot_ids=[selected_uuid],
                limit=5,
            )
            if not alternatives:
                return "idle", "That new slot was taken and I have no alternatives right now.", {"retry_count": 0}
            presented = self._serialize_presented_slots(alternatives, contact.timezone)
            return (
                "reschedule_show_slots",
                "That slot was just taken. Here are fresh options:\n"
                + self._ai.generate_slot_presentation(presented, contact.timezone),
                {
                    **context,
                    "presented_slots": presented,
                    "selected_slot_id": None,
                    "retry_count": 0,
                },
            )

    async def _handle_awaiting_info(
        self,
        contact: Contact,
        message: str,
        context: dict[str, Any],
        history: list[dict[str, str]],
    ) -> tuple[str, str, dict[str, Any]]:
        # Re-run classification once user provides more detail.
        return await self._handle_idle(contact=contact, message=message, context=context, history=history)

    async def _begin_booking(
        self,
        contact: Contact,
        intent: IntentResult,
        history: list[dict[str, str]],
    ) -> tuple[str, str, dict[str, Any]]:
        _ = history  # kept for future enrichment
        now = datetime.now(timezone.utc)
        slots = await self._scheduling.get_available_slots(
            date_from=now,
            date_to=now + timedelta(days=7),
            limit=5,
        )
        if not slots:
            return "idle", "I don't see open times right now. Want me to check again later?", {"retry_count": 0}
        presented = self._serialize_presented_slots(slots, contact.timezone)
        prompt = self._ai.generate_slot_presentation(presented, contact.timezone)
        return "showing_slots", prompt, {
            "presented_slots": presented,
            "retry_count": 0,
            "last_intent": intent.intent,
        }

    async def _detect_intent(
        self,
        contact: Contact,
        message: str,
        history: list[dict[str, str]],
        context: dict[str, Any],
    ) -> IntentResult:
        available_slots = context.get("presented_slots", [])
        return await self._ai.detect_intent(
            message=message,
            conversation_history=history,
            available_slots=available_slots,
            current_appointment=None,
            conversation_state=context.get("last_state", "idle"),
            contact_timezone=contact.timezone,
        )

    @staticmethod
    def _append_history(
        history: list[dict[str, str]],
        user_message: str,
        assistant_message: str,
    ) -> list[dict[str, str]]:
        updated = list(history)
        updated.append({"role": "user", "content": user_message})
        updated.append({"role": "assistant", "content": assistant_message})
        return updated[-10:]

    def _serialize_presented_slots(
        self,
        slots: list[AvailabilitySlot],
        timezone_name: str,
    ) -> list[dict[str, Any]]:
        presented: list[dict[str, Any]] = []
        for index, slot in enumerate(slots, start=1):
            try:
                local_time = slot.start_time.astimezone(ZoneInfo(timezone_name))
            except Exception:  # noqa: BLE001
                local_time = slot.start_time.astimezone(timezone.utc)
            display = local_time.strftime("%a %b %d, %-I:%M %p")
            presented.append(
                {
                    "index": index,
                    "slot_id": str(slot.id),
                    "start_time": slot.start_time.isoformat(),
                    "display": display,
                    "id": str(slot.id),
                }
            )
        return presented

    @staticmethod
    def _find_presented_slot_display(
        presented_slots: list[dict[str, Any]],
        selected_slot_id: str,
    ) -> str:
        for slot in presented_slots:
            if str(slot.get("slot_id")) == str(selected_slot_id):
                return str(slot.get("display", f"slot {slot.get('index', '')}"))
        return "that selected time"

    async def _get_or_create_contact(self, phone_number: str) -> Contact:
        async with AsyncSessionFactory() as session:
            result = await session.execute(select(Contact).where(Contact.phone_number == phone_number))
            contact = result.scalar_one_or_none()
            if contact is not None:
                return contact

            contact = Contact(phone_number=phone_number, opt_in_status="pending")
            session.add(contact)
            await session.commit()
            await session.refresh(contact)
            return contact

    async def _save_contact(self, contact: Contact) -> None:
        async with AsyncSessionFactory() as session:
            merged = await session.merge(contact)
            session.add(merged)
            await session.commit()

    async def _get_or_create_state(self, contact_id: uuid.UUID) -> ConversationState:
        async with AsyncSessionFactory() as session:
            result = await session.execute(
                select(ConversationState).where(ConversationState.contact_id == contact_id)
            )
            state = result.scalar_one_or_none()
            if state is not None:
                return state
            state = ConversationState(contact_id=contact_id, current_state="idle", context={})
            session.add(state)
            await session.commit()
            await session.refresh(state)
            return state

    async def _save_state(self, state: ConversationState) -> None:
        async with AsyncSessionFactory() as session:
            merged = await session.merge(state)
            session.add(merged)
            await session.commit()

    async def _get_contact_appointments(
        self,
        contact_id: uuid.UUID,
        status_filter: list[str] | None = None,
    ) -> list[Appointment]:
        statuses = status_filter or ["confirmed"]
        async with AsyncSessionFactory() as session:
            query = (
                select(Appointment)
                .where(
                    Appointment.contact_id == contact_id,
                    Appointment.status.in_(statuses),
                )
                .order_by(Appointment.booked_at.desc())
            )
            result = await session.execute(query)
            return result.scalars().all()

    async def _get_slot(self, slot_id: uuid.UUID) -> AvailabilitySlot | None:
        async with AsyncSessionFactory() as session:
            result = await session.execute(select(AvailabilitySlot).where(AvailabilitySlot.id == slot_id))
            return result.scalar_one_or_none()
