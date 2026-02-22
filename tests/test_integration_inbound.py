from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from typing import Any

import pytest

from app.core.exceptions import SlotUnavailableError
from app.services.ai_service import IntentResult
from app.services.conversation_service import ConversationService


class FakeAIService:
    def __init__(self) -> None:
        self.detect_calls = 0

    async def detect_intent(
        self,
        message: str,
        conversation_history: list[dict[str, Any]],
        available_slots: list[dict[str, Any]] | None = None,
        current_appointment: dict[str, Any] | None = None,
        conversation_state: str = "idle",
        contact_timezone: str = "UTC",
    ) -> IntentResult:
        _ = (
            conversation_history,
            available_slots,
            current_appointment,
            conversation_state,
            contact_timezone,
        )
        self.detect_calls += 1
        text = (message or "").strip().lower()

        if "reschedule" in text:
            return IntentResult("RESCHEDULE", 0.95, {}, "Let's reschedule.", [])
        if "cancel" in text:
            return IntentResult("CANCEL", 0.95, {}, "Let's cancel.", [])
        if any(token in text for token in ["yes", "confirm", "yep"]):
            return IntentResult("CONFIRM", 0.95, {}, "Confirmed.", [])
        if any(token in text for token in ["no", "nope"]):
            return IntentResult("DENY", 0.95, {}, "No problem.", [])
        if text.isdigit():
            return IntentResult("SELECT_SLOT", 0.9, {}, "Selecting slot.", [])
        if "book" in text:
            return IntentResult("BOOK", 0.95, {}, "Let's book.", [])
        return IntentResult("QUESTION", 0.7, {}, "Could you share more details?", [])

    async def parse_slot_selection(
        self, message: str, presented_slots: list[dict[str, Any]]
    ) -> str | None:
        text = (message or "").strip().lower()
        if not presented_slots:
            return None
        if text.isdigit():
            index = int(text)
            if 1 <= index <= len(presented_slots):
                return str(presented_slots[index - 1]["slot_id"])
        return None

    def generate_slot_presentation(
        self, slots: list[dict[str, Any]], timezone_name: str
    ) -> str:
        _ = timezone_name
        lines = ["Here are some available times:"]
        for idx, slot in enumerate(slots, start=1):
            lines.append(f"{idx}) {slot.get('display', slot.get('start_time'))}")
        lines.append("Reply with a number to book.")
        return "\n".join(lines)

    def generate_confirmation(
        self, appointment: dict[str, Any], timezone_name: str
    ) -> str:
        _ = timezone_name
        return f"You're all set! Your appointment is confirmed for {appointment.get('start_time')}."


class FakeSMSService:
    def __init__(self) -> None:
        self.sent: list[dict[str, Any]] = []

    async def send_message(
        self,
        to: str,
        body: str,
        force_send: bool = False,
        campaign_id: str | None = None,
    ):
        self.sent.append(
            {
                "to": to,
                "body": body,
                "force_send": force_send,
                "campaign_id": campaign_id,
            }
        )
        return SimpleNamespace()


@dataclass
class FakeSchedulingService:
    slots: dict[uuid.UUID, SimpleNamespace]
    appointments: dict[uuid.UUID, SimpleNamespace] = field(default_factory=dict)
    fail_once_slot_ids: set[uuid.UUID] = field(default_factory=set)
    book_calls: list[tuple[uuid.UUID, uuid.UUID]] = field(default_factory=list)
    cancel_calls: list[uuid.UUID] = field(default_factory=list)
    reschedule_calls: list[tuple[uuid.UUID, uuid.UUID]] = field(default_factory=list)

    async def get_available_slots(
        self,
        date_from: datetime,
        date_to: datetime,
        provider_id: uuid.UUID | None = None,
        limit: int = 5,
    ) -> list[SimpleNamespace]:
        _ = (date_from, date_to, provider_id)
        available = [slot for slot in self.slots.values() if slot.is_available]
        available.sort(key=lambda slot: slot.start_time)
        return available[:limit]

    async def book_appointment(self, contact_id: uuid.UUID, slot_id: uuid.UUID):
        self.book_calls.append((contact_id, slot_id))
        slot = self.slots[slot_id]
        if slot_id in self.fail_once_slot_ids:
            self.fail_once_slot_ids.remove(slot_id)
            raise SlotUnavailableError("slot stale")
        if not slot.is_available:
            raise SlotUnavailableError("slot taken")
        slot.is_available = False
        appt = SimpleNamespace(
            id=uuid.uuid4(),
            contact_id=contact_id,
            slot_id=slot_id,
            status="confirmed",
            booked_at=datetime.now(timezone.utc),
            rescheduled_from_id=None,
        )
        self.appointments[appt.id] = appt
        return appt

    async def cancel_appointment(
        self, appointment_id: uuid.UUID, reason: str | None = None
    ):
        _ = reason
        self.cancel_calls.append(appointment_id)
        appt = self.appointments[appointment_id]
        appt.status = "cancelled"
        self.slots[appt.slot_id].is_available = True
        return appt

    async def reschedule_appointment(
        self, appointment_id: uuid.UUID, new_slot_id: uuid.UUID
    ):
        self.reschedule_calls.append((appointment_id, new_slot_id))
        old = self.appointments[appointment_id]
        new_slot = self.slots[new_slot_id]
        if not new_slot.is_available:
            raise SlotUnavailableError("slot taken")
        self.slots[old.slot_id].is_available = True
        old.status = "rescheduled"
        new_slot.is_available = False
        replacement = SimpleNamespace(
            id=uuid.uuid4(),
            contact_id=old.contact_id,
            slot_id=new_slot_id,
            status="confirmed",
            booked_at=datetime.now(timezone.utc),
            rescheduled_from_id=old.id,
        )
        self.appointments[replacement.id] = replacement
        return replacement

    async def get_fresh_alternatives(
        self,
        exclude_slot_ids: list[uuid.UUID],
        date_from: datetime | None = None,
        limit: int = 5,
        provider_id: uuid.UUID | None = None,
    ) -> list[SimpleNamespace]:
        _ = (date_from, provider_id)
        excluded = set(exclude_slot_ids)
        alternatives = [
            slot
            for slot in self.slots.values()
            if slot.is_available and slot.id not in excluded
        ]
        alternatives.sort(key=lambda slot: slot.start_time)
        return alternatives[:limit]


class FakeDBSession:
    def add(self, obj: object) -> None:
        _ = obj

    async def flush(self) -> None:
        return None

    async def commit(self) -> None:
        return None


class FakeSessionContext:
    def __init__(self, session: FakeDBSession) -> None:
        self._session = session

    async def __aenter__(self) -> FakeDBSession:
        return self._session

    async def __aexit__(self, exc_type, exc, tb) -> None:
        _ = (exc_type, exc, tb)
        return None


@pytest.fixture
def integration_env(monkeypatch):
    now = datetime.now(timezone.utc)
    slot_1 = SimpleNamespace(id=uuid.uuid4(), start_time=now + timedelta(hours=1), is_available=True)
    slot_2 = SimpleNamespace(id=uuid.uuid4(), start_time=now + timedelta(hours=2), is_available=True)
    slot_3 = SimpleNamespace(id=uuid.uuid4(), start_time=now + timedelta(hours=3), is_available=True)
    slots = {slot_1.id: slot_1, slot_2.id: slot_2, slot_3.id: slot_3}

    ai = FakeAIService()
    sms = FakeSMSService()
    scheduling = FakeSchedulingService(slots=slots)
    service = ConversationService(
        ai_service=ai,
        scheduling_service=scheduling,
        sms_service=sms,
        redis_client=None,
    )

    contacts_by_phone: dict[str, SimpleNamespace] = {}
    states_by_contact: dict[uuid.UUID, SimpleNamespace] = {}
    fake_session = FakeDBSession()
    sid_counter = {"value": 0}

    monkeypatch.setattr(
        "app.services.conversation_service.AsyncSessionFactory",
        lambda: FakeSessionContext(fake_session),
    )

    async def fake_get_contact(_session, phone_number: str):
        return contacts_by_phone.get(phone_number)

    async def fake_get_or_create_state(_session, contact_id: uuid.UUID):
        state = states_by_contact.get(contact_id)
        if state is None:
            state = SimpleNamespace(
                contact_id=contact_id,
                current_state="idle",
                context={},
                last_message_at=None,
                expires_at=None,
            )
            states_by_contact[contact_id] = state
        return state

    async def fake_get_contact_appointments(
        contact_id: uuid.UUID, status_filter: list[str] | None = None
    ):
        statuses = set(status_filter or ["confirmed"])
        return [
            appt
            for appt in scheduling.appointments.values()
            if appt.contact_id == contact_id and appt.status in statuses
        ]

    async def fake_get_slot(slot_id: uuid.UUID):
        return scheduling.slots.get(slot_id)

    monkeypatch.setattr(service, "_get_contact", fake_get_contact)
    monkeypatch.setattr(service, "_get_or_create_state", fake_get_or_create_state)
    monkeypatch.setattr(service, "_get_contact_appointments", fake_get_contact_appointments)
    monkeypatch.setattr(service, "_get_slot", fake_get_slot)

    def create_contact(phone: str, status: str = "opted_in") -> SimpleNamespace:
        contact = SimpleNamespace(
            id=uuid.uuid4(),
            phone_number=phone,
            timezone="UTC",
            opt_in_status=status,
            opt_in_date=None,
            opt_out_date=None,
        )
        contacts_by_phone[phone] = contact
        return contact

    async def send_message(phone: str, text: str):
        sid_counter["value"] += 1
        sms_sid = f"SM_INTEGRATION_{sid_counter['value']}"
        before = len(sms.sent)
        await service.process_inbound_message(phone, text, sms_sid)
        new_messages = sms.sent[before:]
        contact = contacts_by_phone.get(phone)
        state = states_by_contact.get(contact.id) if contact else None
        return state, new_messages

    return {
        "service": service,
        "ai": ai,
        "sms": sms,
        "scheduling": scheduling,
        "contacts": contacts_by_phone,
        "states": states_by_contact,
        "create_contact": create_contact,
        "send_message": send_message,
    }


@pytest.mark.asyncio
async def test_booking_happy_path(integration_env) -> None:
    phone = "+15550100001"
    contact = integration_env["create_contact"](phone, status="opted_in")

    state, outbound = await integration_env["send_message"](
        phone, "I'd like to book an appointment"
    )
    assert state is not None
    assert state.current_state == "showing_slots"
    assert len(outbound) == 1
    assert "available times" in outbound[0]["body"].lower()

    state, outbound = await integration_env["send_message"](phone, "1")
    assert state.current_state == "confirming_booking"
    assert len(outbound) == 1
    assert "reply yes to confirm" in outbound[0]["body"].lower()

    state, outbound = await integration_env["send_message"](phone, "yes")
    assert state.current_state == "idle"
    assert len(outbound) == 1
    assert "confirmed" in outbound[0]["body"].lower()
    assert len(integration_env["scheduling"].book_calls) == 1
    booked_contact_id, _ = integration_env["scheduling"].book_calls[0]
    assert booked_contact_id == contact.id


@pytest.mark.asyncio
async def test_cancel_happy_path(integration_env) -> None:
    phone = "+15550100002"
    contact = integration_env["create_contact"](phone, status="opted_in")
    slot = next(iter(integration_env["scheduling"].slots.values()))
    slot.is_available = False
    appt = SimpleNamespace(
        id=uuid.uuid4(),
        contact_id=contact.id,
        slot_id=slot.id,
        status="confirmed",
        booked_at=datetime.now(timezone.utc),
        rescheduled_from_id=None,
    )
    integration_env["scheduling"].appointments[appt.id] = appt

    state, outbound = await integration_env["send_message"](phone, "cancel my appointment")
    assert state is not None
    assert state.current_state == "confirming_cancel"
    assert len(outbound) == 1
    assert "confirm cancellation" in outbound[0]["body"].lower()

    state, outbound = await integration_env["send_message"](phone, "yes")
    assert state.current_state == "idle"
    assert len(outbound) == 1
    assert "cancelled" in outbound[0]["body"].lower()
    assert integration_env["scheduling"].cancel_calls == [appt.id]


@pytest.mark.asyncio
async def test_reschedule_happy_path(integration_env) -> None:
    phone = "+15550100003"
    contact = integration_env["create_contact"](phone, status="opted_in")
    slot_ids = list(integration_env["scheduling"].slots.keys())
    old_slot = integration_env["scheduling"].slots[slot_ids[0]]
    old_slot.is_available = False
    appt = SimpleNamespace(
        id=uuid.uuid4(),
        contact_id=contact.id,
        slot_id=old_slot.id,
        status="confirmed",
        booked_at=datetime.now(timezone.utc),
        rescheduled_from_id=None,
    )
    integration_env["scheduling"].appointments[appt.id] = appt

    state, outbound = await integration_env["send_message"](phone, "reschedule")
    assert state is not None
    assert state.current_state == "reschedule_show_slots"
    assert len(outbound) == 1
    assert "available times" in outbound[0]["body"].lower()

    state, outbound = await integration_env["send_message"](phone, "2")
    assert state.current_state == "confirming_reschedule"
    assert len(outbound) == 1
    assert "reply yes or no" in outbound[0]["body"].lower()

    state, outbound = await integration_env["send_message"](phone, "yes")
    assert state.current_state == "idle"
    assert len(outbound) == 1
    assert "confirmed" in outbound[0]["body"].lower()
    assert len(integration_env["scheduling"].reschedule_calls) == 1


@pytest.mark.asyncio
async def test_opted_out_user_gets_no_response(integration_env) -> None:
    phone = "+15550100004"
    contact = integration_env["create_contact"](phone, status="opted_out")

    state, outbound = await integration_env["send_message"](phone, "book an appointment")
    assert state is None
    assert outbound == []
    assert integration_env["ai"].detect_calls == 0
    assert contact.id not in integration_env["states"]


@pytest.mark.asyncio
async def test_slot_taken_shows_alternatives(integration_env) -> None:
    phone = "+15550100005"
    contact = integration_env["create_contact"](phone, status="opted_in")

    state, _ = await integration_env["send_message"](phone, "book")
    assert state is not None
    assert state.current_state == "showing_slots"

    state, _ = await integration_env["send_message"](phone, "1")
    assert state.current_state == "confirming_booking"
    selected_slot_id = uuid.UUID(str(state.context["selected_slot_id"]))
    integration_env["scheduling"].fail_once_slot_ids.add(selected_slot_id)

    state, outbound = await integration_env["send_message"](phone, "yes")
    assert state.current_state == "showing_slots"
    assert len(outbound) == 1
    assert "just booked by someone else" in outbound[0]["body"].lower()
    assert len(integration_env["scheduling"].book_calls) == 1
    assert contact.id in integration_env["states"]


@pytest.mark.asyncio
async def test_max_retries_resets_to_idle(integration_env) -> None:
    phone = "+15550100006"
    contact = integration_env["create_contact"](phone, status="opted_in")

    state, _ = await integration_env["send_message"](phone, "book")
    assert state is not None
    assert state.current_state == "showing_slots"

    state, _ = await integration_env["send_message"](phone, "what")
    assert state.current_state == "showing_slots"

    state, _ = await integration_env["send_message"](phone, "blah")
    assert state.current_state == "showing_slots"

    state, outbound = await integration_env["send_message"](phone, "???")
    assert state.current_state == "idle"
    assert len(outbound) == 1
    assert "let's reset" in outbound[0]["body"].lower()
    assert contact.id in integration_env["states"]
