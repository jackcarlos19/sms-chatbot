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
        if any(token in text for token in ["reschedule", "move"]):
            return IntentResult("RESCHEDULE", 0.95, {}, "Let's reschedule.", [])
        if "cancel" in text:
            return IntentResult("CANCEL", 0.95, {}, "Let's cancel.", [])
        if any(token in text for token in ["yes", "confirm", "yep"]):
            return IntentResult("CONFIRM", 0.95, {}, "Confirmed.", [])
        if any(token in text for token in ["no", "nope"]):
            return IntentResult("DENY", 0.95, {}, "No problem.", [])
        if any(ch.isdigit() for ch in text):
            return IntentResult("SELECT_SLOT", 0.9, {}, "Selecting slot.", [])
        if "book" in text:
            return IntentResult("BOOK", 0.95, {}, "Let's book.", [])
        return IntentResult("QUESTION", 0.7, {}, "Could you share more details?", [])

    async def parse_slot_selection(
        self,
        message: str,
        presented_slots: list[dict[str, Any]],
        timezone_name: str = "UTC",
    ) -> str | None:
        _ = timezone_name
        text = (message or "").strip().lower()
        if not presented_slots:
            return None
        if text.isdigit():
            idx = int(text)
            if 1 <= idx <= len(presented_slots):
                return str(presented_slots[idx - 1]["slot_id"])
        if "first" in text:
            return str(presented_slots[0]["slot_id"])
        if "second" in text and len(presented_slots) > 1:
            return str(presented_slots[1]["slot_id"])
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
        start = appointment.get("start_time")
        return f"You're all set! Your appointment is confirmed for {start}."


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

    async def get_available_slots(
        self,
        date_from: datetime,
        date_to: datetime,
        provider_id: uuid.UUID | None = None,
        limit: int = 5,
    ) -> list[SimpleNamespace]:
        _ = (date_from, date_to, provider_id)
        available = [slot for slot in self.slots.values() if slot.is_available]
        available.sort(key=lambda s: s.start_time)
        return available[:limit]

    async def book_appointment(self, contact_id: uuid.UUID, slot_id: uuid.UUID):
        slot = self.slots[slot_id]
        if slot_id in self.fail_once_slot_ids:
            self.fail_once_slot_ids.remove(slot_id)
            raise SlotUnavailableError("stale")
        if not slot.is_available:
            raise SlotUnavailableError("taken")
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
        appt = self.appointments[appointment_id]
        appt.status = "cancelled"
        self.slots[appt.slot_id].is_available = True
        return appt

    async def reschedule_appointment(
        self, appointment_id: uuid.UUID, new_slot_id: uuid.UUID
    ):
        old = self.appointments[appointment_id]
        new_slot = self.slots[new_slot_id]
        if not new_slot.is_available:
            raise SlotUnavailableError("taken")
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
        choices = [
            s for s in self.slots.values() if s.is_available and s.id not in excluded
        ]
        choices.sort(key=lambda s: s.start_time)
        return choices[:limit]


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
def service_bundle(monkeypatch):
    now = datetime.now(timezone.utc)
    slot_a = SimpleNamespace(id=uuid.uuid4(), start_time=now + timedelta(hours=1), is_available=True)
    slot_b = SimpleNamespace(id=uuid.uuid4(), start_time=now + timedelta(hours=2), is_available=True)
    slot_c = SimpleNamespace(id=uuid.uuid4(), start_time=now + timedelta(hours=3), is_available=True)
    slots = {slot_a.id: slot_a, slot_b.id: slot_b, slot_c.id: slot_c}

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
        contact_id: uuid.UUID,
        status_filter: list[str] | None = None,
        session: Any | None = None,
    ):
        _ = session
        statuses = set(status_filter or ["confirmed"])
        return [
            appt
            for appt in scheduling.appointments.values()
            if appt.contact_id == contact_id and appt.status in statuses
        ]

    async def fake_get_slot(slot_id: uuid.UUID, session: Any | None = None):
        _ = session
        return scheduling.slots.get(slot_id)

    monkeypatch.setattr(service, "_get_contact", fake_get_contact)
    monkeypatch.setattr(service, "_get_or_create_state", fake_get_or_create_state)
    monkeypatch.setattr(service, "_get_contact_appointments", fake_get_contact_appointments)
    monkeypatch.setattr(service, "_get_slot", fake_get_slot)

    def create_contact(phone: str, status: str = "pending") -> SimpleNamespace:
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

    return service, ai, sms, scheduling, contacts_by_phone, states_by_contact, create_contact


@pytest.mark.asyncio
async def test_unknown_number_is_ignored_without_contact_record(service_bundle) -> None:
    service, ai, sms, _, contacts, _, _ = service_bundle
    phone = "+15552220000"

    await service.process_inbound_message(phone, "book", "SM2")

    assert phone not in contacts
    assert ai.detect_calls == 0
    assert sms.sent == []


@pytest.mark.asyncio
async def test_full_booking_flow(service_bundle) -> None:
    service, _, sms, scheduling, _, states, create_contact = service_bundle
    phone = "+15553330000"
    contact = create_contact(phone, status="opted_in")

    await service.process_inbound_message(phone, "book", "SM3")
    state = states[contact.id]
    assert state.current_state == "showing_slots"

    await service.process_inbound_message(phone, "1", "SM4")
    state = states[contact.id]
    assert state.current_state == "confirming_booking"

    await service.process_inbound_message(phone, "yes", "SM5")
    state = states[contact.id]
    assert state.current_state == "idle"
    assert any(appt.status == "confirmed" for appt in scheduling.appointments.values())
    assert any("confirmed" in item["body"].lower() for item in sms.sent)


@pytest.mark.asyncio
async def test_full_cancel_flow(service_bundle) -> None:
    service, _, _, scheduling, _, states, create_contact = service_bundle
    phone = "+15554440000"
    contact = create_contact(phone, status="opted_in")
    slot = next(iter(scheduling.slots.values()))
    slot.is_available = False
    appt = SimpleNamespace(
        id=uuid.uuid4(),
        contact_id=contact.id,
        slot_id=slot.id,
        status="confirmed",
        booked_at=datetime.now(timezone.utc),
        rescheduled_from_id=None,
    )
    scheduling.appointments[appt.id] = appt

    await service.process_inbound_message(phone, "cancel", "SM6")
    state = states[contact.id]
    assert state.current_state == "confirming_cancel"

    await service.process_inbound_message(phone, "yes", "SM7")
    assert scheduling.appointments[appt.id].status == "cancelled"
    assert slot.is_available is True


@pytest.mark.asyncio
async def test_cancel_keyword_confirms_when_already_confirming_cancel(service_bundle) -> None:
    service, _, _, scheduling, _, states, create_contact = service_bundle
    phone = "+15554449999"
    contact = create_contact(phone, status="opted_in")
    slot = next(iter(scheduling.slots.values()))
    slot.is_available = False
    appt = SimpleNamespace(
        id=uuid.uuid4(),
        contact_id=contact.id,
        slot_id=slot.id,
        status="confirmed",
        booked_at=datetime.now(timezone.utc),
        rescheduled_from_id=None,
    )
    scheduling.appointments[appt.id] = appt

    await service.process_inbound_message(phone, "cancel", "SM6a")
    assert states[contact.id].current_state == "confirming_cancel"
    await service.process_inbound_message(phone, "cancel", "SM6b")
    assert scheduling.appointments[appt.id].status == "cancelled"


@pytest.mark.asyncio
async def test_full_reschedule_flow(service_bundle) -> None:
    service, _, _, scheduling, _, states, create_contact = service_bundle
    phone = "+15555550000"
    contact = create_contact(phone, status="opted_in")
    slot_ids = list(scheduling.slots.keys())
    old_slot = scheduling.slots[slot_ids[0]]
    new_slot = scheduling.slots[slot_ids[1]]
    old_slot.is_available = False
    appt = SimpleNamespace(
        id=uuid.uuid4(),
        contact_id=contact.id,
        slot_id=old_slot.id,
        status="confirmed",
        booked_at=datetime.now(timezone.utc),
        rescheduled_from_id=None,
    )
    scheduling.appointments[appt.id] = appt

    await service.process_inbound_message(phone, "reschedule", "SM8")
    state = states[contact.id]
    assert state.current_state == "reschedule_show_slots"

    await service.process_inbound_message(phone, "1", "SM9")
    state = states[contact.id]
    assert state.current_state == "confirming_reschedule"

    await service.process_inbound_message(phone, "yes", "SM10")
    state = states[contact.id]
    assert state.current_state == "idle"
    assert any(
        appt_obj.rescheduled_from_id == appt.id
        for appt_obj in scheduling.appointments.values()
    )
    assert new_slot.is_available is False
    assert old_slot.is_available is True


@pytest.mark.asyncio
async def test_reschedule_rejection_keeps_existing_appointment(service_bundle) -> None:
    service, _, sms, scheduling, _, states, create_contact = service_bundle
    phone = "+15555558888"
    contact = create_contact(phone, status="opted_in")
    old_slot = next(iter(scheduling.slots.values()))
    old_slot.is_available = False
    appt = SimpleNamespace(
        id=uuid.uuid4(),
        contact_id=contact.id,
        slot_id=old_slot.id,
        status="confirmed",
        booked_at=datetime.now(timezone.utc),
        rescheduled_from_id=None,
    )
    scheduling.appointments[appt.id] = appt

    await service.process_inbound_message(phone, "reschedule", "SM8a")
    assert states[contact.id].current_state == "reschedule_show_slots"
    await service.process_inbound_message(phone, "I don't want it", "SM8b")
    assert states[contact.id].current_state == "idle"
    assert "stays as-is" in sms.sent[-1]["body"]


@pytest.mark.asyncio
async def test_staleness_recovery_returns_to_showing_slots(service_bundle) -> None:
    service, _, sms, scheduling, _, states, create_contact = service_bundle
    phone = "+15556660000"
    contact = create_contact(phone, status="opted_in")
    slot_id = next(iter(scheduling.slots.keys()))
    scheduling.fail_once_slot_ids.add(slot_id)

    await service.process_inbound_message(phone, "book", "SM11")
    await service.process_inbound_message(phone, "1", "SM12")
    await service.process_inbound_message(phone, "yes", "SM13")

    state = states[contact.id]
    assert state.current_state == "showing_slots"
    assert "just booked by someone else" in sms.sent[-1]["body"].lower()


@pytest.mark.asyncio
async def test_showing_slots_rejection_offers_alternatives(service_bundle) -> None:
    service, _, sms, scheduling, _, states, create_contact = service_bundle
    phone = "+15556661111"
    contact = create_contact(phone, status="opted_in")
    now = datetime.now(timezone.utc)
    for idx in range(4, 8):
        new_id = uuid.uuid4()
        scheduling.slots[new_id] = SimpleNamespace(
            id=new_id,
            start_time=now + timedelta(hours=idx),
            is_available=True,
        )

    await service.process_inbound_message(phone, "book", "SM11a")
    assert states[contact.id].current_state == "showing_slots"
    await service.process_inbound_message(phone, "Those times don't work for me", "SM11b")
    assert states[contact.id].current_state == "showing_slots"
    assert "other times" in sms.sent[-1]["body"].lower()


@pytest.mark.asyncio
async def test_mid_flow_intent_change_to_cancel(service_bundle) -> None:
    service, _, sms, _, _, states, create_contact = service_bundle
    phone = "+15557770000"
    contact = create_contact(phone, status="opted_in")

    await service.process_inbound_message(phone, "book", "SM14")
    await service.process_inbound_message(phone, "1", "SM15")
    await service.process_inbound_message(phone, "cancel", "SM16")

    state = states[contact.id]
    assert state.current_state != "confirming_booking"
    assert "cancel" in sms.sent[-1]["body"].lower()


@pytest.mark.asyncio
async def test_get_or_create_state_resets_expired_state() -> None:
    service = ConversationService(
        ai_service=FakeAIService(),
        scheduling_service=FakeSchedulingService(slots={}),
        sms_service=FakeSMSService(),
        redis_client=None,
    )

    expired_state = SimpleNamespace(
        contact_id=uuid.uuid4(),
        current_state="showing_slots",
        context={"history": [{"role": "user", "content": "book"}]},
        last_message_at=datetime.now(timezone.utc) - timedelta(hours=3),
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
    )

    class _FakeResult:
        def scalar_one_or_none(self):
            return expired_state

    class _FakeSession:
        async def execute(self, _query):
            return _FakeResult()

        def add(self, _obj: object) -> None:
            return None

        async def flush(self) -> None:
            return None

    resolved = await service._get_or_create_state(_FakeSession(), expired_state.contact_id)
    assert resolved.current_state == "idle"
    assert resolved.context == {}
    assert resolved.expires_at is None
