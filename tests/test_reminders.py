from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from typing import Any

import pytest

from app.workers import tasks


def _extract_where_values(query: Any) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for clause in getattr(query, "_where_criteria", []):
        op_name = getattr(getattr(clause, "operator", None), "__name__", "")
        left = getattr(clause, "left", None)
        right = getattr(clause, "right", None)
        key = getattr(left, "key", "")
        if not key:
            continue
        right_value = getattr(right, "value", None)
        if op_name in {"eq", "ge", "gt", "le", "lt", "ne"}:
            values[f"{key}:{op_name}"] = right_value
        elif op_name == "ilike_op":
            values[f"{key}:ilike"] = right_value
    return values


class FakeResult:
    def __init__(self, rows: list[Any]) -> None:
        self._rows = rows

    def all(self) -> list[Any]:
        return list(self._rows)

    def scalar_one(self) -> Any:
        if not self._rows:
            return 0
        return self._rows[0]


class FakeSession:
    def __init__(
        self,
        appointment_rows: list[tuple[Any, Any, Any]],
        messages: list[Any],
    ) -> None:
        self.appointment_rows = appointment_rows
        self.messages = messages

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):  # noqa: ANN001
        return None

    async def execute(self, query):
        descriptions = getattr(query, "column_descriptions", [])
        entities = [d.get("entity") for d in descriptions]

        # Main query: select(Appointment, AvailabilitySlot, Contact)
        if len(entities) == 3 and getattr(entities[0], "__name__", "") == "Appointment":
            filtered: list[tuple[Any, Any, Any]] = []
            now = datetime.now(timezone.utc)
            start_ge = now + timedelta(hours=23, minutes=30)
            start_le = now + timedelta(hours=24, minutes=30)
            for appointment, slot, contact in self.appointment_rows:
                if appointment.status != "confirmed":
                    continue
                if slot.start_time < start_ge:
                    continue
                if slot.start_time > start_le:
                    continue
                if contact.opt_in_status == "opted_out":
                    continue
                filtered.append((appointment, slot, contact))
            return FakeResult(filtered)

        # Duplicate reminder query: select(func.count()).select_from(Message)
        values = _extract_where_values(query)
        contact_id = values.get("contact_id:eq")
        direction = values.get("direction:eq")
        body_like = values.get("body:ilike")
        created_ge = values.get("created_at:ge")
        count = 0
        for msg in self.messages:
            if contact_id is not None and msg.contact_id != contact_id:
                continue
            if direction is not None and msg.direction != direction:
                continue
            if body_like is not None:
                needle = str(body_like).replace("%", "").lower()
                if needle not in (msg.body or "").lower():
                    continue
            if created_ge is not None and msg.created_at < created_ge:
                continue
            count += 1
        return FakeResult([count])


class FakeSessionFactory:
    def __init__(self, session: FakeSession):
        self.session = session

    def __call__(self):
        return self.session


class FakeSMSService:
    def __init__(self):
        self.sent: list[dict[str, str]] = []

    async def send_message(self, to: str, body: str):
        self.sent.append({"to": to, "body": body})
        return SimpleNamespace(status="sent", sms_sid="SM_REMINDER")


def _make_triplet(
    *,
    hours_from_now: float,
    status: str = "confirmed",
    opt_in_status: str = "opted_in",
) -> tuple[Any, Any, Any]:
    contact = SimpleNamespace(
        id=uuid.uuid4(),
        phone_number="+15550000001",
        timezone="UTC",
        opt_in_status=opt_in_status,
    )
    slot = SimpleNamespace(
        id=uuid.uuid4(),
        start_time=datetime.now(timezone.utc) + timedelta(hours=hours_from_now),
    )
    appointment = SimpleNamespace(
        id=uuid.uuid4(),
        contact_id=contact.id,
        slot_id=slot.id,
        status=status,
    )
    return appointment, slot, contact


@pytest.mark.asyncio
async def test_reminder_sent_for_appointment_24h_away(monkeypatch) -> None:
    row = _make_triplet(hours_from_now=24)
    session = FakeSession(appointment_rows=[row], messages=[])
    sms = FakeSMSService()
    monkeypatch.setattr(tasks, "AsyncSessionFactory", FakeSessionFactory(session))
    monkeypatch.setattr(tasks, "SMSService", lambda: sms)

    sent = await tasks.send_appointment_reminders({})

    assert sent == 1
    assert len(sms.sent) == 1
    assert "Reminder" in sms.sent[0]["body"]
    assert "at" in sms.sent[0]["body"]


@pytest.mark.asyncio
async def test_no_reminder_for_appointment_48h_away(monkeypatch) -> None:
    row = _make_triplet(hours_from_now=48)
    session = FakeSession(appointment_rows=[row], messages=[])
    sms = FakeSMSService()
    monkeypatch.setattr(tasks, "AsyncSessionFactory", FakeSessionFactory(session))
    monkeypatch.setattr(tasks, "SMSService", lambda: sms)

    sent = await tasks.send_appointment_reminders({})

    assert sent == 0
    assert sms.sent == []


@pytest.mark.asyncio
async def test_no_duplicate_reminder(monkeypatch) -> None:
    appointment, slot, contact = _make_triplet(hours_from_now=24)
    existing_message = SimpleNamespace(
        contact_id=contact.id,
        direction="outbound",
        body="Appointment reminder: see you tomorrow!",
        created_at=datetime.now(timezone.utc) - timedelta(hours=2),
    )
    session = FakeSession(
        appointment_rows=[(appointment, slot, contact)],
        messages=[existing_message],
    )
    sms = FakeSMSService()
    monkeypatch.setattr(tasks, "AsyncSessionFactory", FakeSessionFactory(session))
    monkeypatch.setattr(tasks, "SMSService", lambda: sms)

    sent = await tasks.send_appointment_reminders({})

    assert sent == 0
    assert sms.sent == []


@pytest.mark.asyncio
async def test_no_reminder_for_opted_out_contact(monkeypatch) -> None:
    row = _make_triplet(hours_from_now=24, opt_in_status="opted_out")
    session = FakeSession(appointment_rows=[row], messages=[])
    sms = FakeSMSService()
    monkeypatch.setattr(tasks, "AsyncSessionFactory", FakeSessionFactory(session))
    monkeypatch.setattr(tasks, "SMSService", lambda: sms)

    sent = await tasks.send_appointment_reminders({})

    assert sent == 0
    assert sms.sent == []


@pytest.mark.asyncio
async def test_no_reminder_for_cancelled_appointment(monkeypatch) -> None:
    row = _make_triplet(hours_from_now=24, status="cancelled")
    session = FakeSession(appointment_rows=[row], messages=[])
    sms = FakeSMSService()
    monkeypatch.setattr(tasks, "AsyncSessionFactory", FakeSessionFactory(session))
    monkeypatch.setattr(tasks, "SMSService", lambda: sms)

    sent = await tasks.send_appointment_reminders({})

    assert sent == 0
    assert sms.sent == []
