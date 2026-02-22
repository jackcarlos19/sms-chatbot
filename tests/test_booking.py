from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from typing import Any

import pytest

from app.core.exceptions import SMSChatbotError, SlotUnavailableError
from app.services.scheduling_service import SchedulingService


@dataclass
class Store:
    slots: dict[uuid.UUID, SimpleNamespace] = field(default_factory=dict)
    appointments: dict[uuid.UUID, SimpleNamespace] = field(default_factory=dict)
    locks: dict[uuid.UUID, asyncio.Lock] = field(default_factory=dict)
    for_update_queries: list[Any] = field(default_factory=list)

    def get_lock(self, slot_id: uuid.UUID) -> asyncio.Lock:
        if slot_id not in self.locks:
            self.locks[slot_id] = asyncio.Lock()
        return self.locks[slot_id]


class FakeResult:
    def __init__(self, items: list[Any]) -> None:
        self._items = items

    def scalar_one_or_none(self) -> Any:
        if not self._items:
            return None
        return self._items[0]

    def scalars(self) -> "FakeResult":
        return self

    def all(self) -> list[Any]:
        return list(self._items)


def _extract_where_values(query: Any) -> dict[str, Any]:
    extracted: dict[str, Any] = {}
    for clause in getattr(query, "_where_criteria", []):
        left = getattr(clause, "left", None)
        right = getattr(clause, "right", None)
        operator_name = getattr(getattr(clause, "operator", None), "__name__", "")
        if left is None:
            continue
        key = getattr(left, "key", "")
        if key and operator_name in {"eq", "ge", "le"}:
            extracted[f"{key}:{operator_name}"] = getattr(right, "value", None)
        if key and operator_name == "in_op":
            extracted[f"{key}:{operator_name}"] = list(getattr(right, "value", []))
        if key and operator_name == "not_in_op":
            extracted[f"{key}:{operator_name}"] = list(getattr(right, "value", []))
    return extracted


class FakeTransaction:
    def __init__(self, session: "FakeSession") -> None:
        self._session = session

    async def __aenter__(self) -> "FakeTransaction":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        self._session.release_slot_locks()


class FakeSession:
    def __init__(self, store: Store) -> None:
        self._store = store
        self._held_slot_locks: list[asyncio.Lock] = []

    async def __aenter__(self) -> "FakeSession":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        self.release_slot_locks()

    def begin(self) -> FakeTransaction:
        return FakeTransaction(self)

    async def execute(self, query: Any) -> FakeResult:
        model = query.column_descriptions[0]["entity"]
        values = _extract_where_values(query)
        is_for_update = getattr(query, "_for_update_arg", None) is not None

        if model.__name__ == "AvailabilitySlot":
            if is_for_update:
                self._store.for_update_queries.append(query)
                slot_id = values.get("id:eq")
                lock = self._store.get_lock(slot_id)
                await lock.acquire()
                self._held_slot_locks.append(lock)
            return FakeResult(self._filter_slots(values))

        if model.__name__ == "Appointment":
            return FakeResult(self._filter_appointments(values))

        raise AssertionError("Unsupported model query in fake session.")

    async def flush(self) -> None:
        return None

    def add(self, obj: Any) -> None:
        if obj.__class__.__name__ == "Appointment":
            if getattr(obj, "id", None) is None:
                obj.id = uuid.uuid4()
            self._store.appointments[obj.id] = obj

    def release_slot_locks(self) -> None:
        while self._held_slot_locks:
            lock = self._held_slot_locks.pop()
            if lock.locked():
                lock.release()

    def _filter_slots(self, values: dict[str, Any]) -> list[Any]:
        slots = list(self._store.slots.values())
        slot_id = values.get("id:eq")
        if slot_id is not None:
            slots = [slot for slot in slots if slot.id == slot_id]

        ge = values.get("start_time:ge")
        if ge is not None:
            slots = [slot for slot in slots if slot.start_time >= ge]
        le = values.get("end_time:le")
        if le is not None:
            slots = [slot for slot in slots if slot.end_time <= le]
        provider = values.get("provider_id:eq")
        if provider is not None:
            slots = [slot for slot in slots if slot.provider_id == provider]
        not_in = values.get("id:not_in_op")
        if not_in:
            not_in_set = set(not_in)
            slots = [slot for slot in slots if slot.id not in not_in_set]
        return slots

    def _filter_appointments(self, values: dict[str, Any]) -> list[Any]:
        appts = list(self._store.appointments.values())
        appt_id = values.get("id:eq")
        if appt_id is not None:
            appts = [appt for appt in appts if appt.id == appt_id]
        return appts


class FakeSessionFactory:
    def __init__(self, store: Store) -> None:
        self._store = store

    def __call__(self) -> FakeSession:
        return FakeSession(self._store)


@pytest.fixture
def store() -> Store:
    now = datetime.now(timezone.utc)
    slot_1 = SimpleNamespace(
        id=uuid.uuid4(),
        provider_id=None,
        start_time=now + timedelta(hours=1),
        end_time=now + timedelta(hours=2),
        buffer_minutes=0,
        is_available=True,
    )
    slot_2 = SimpleNamespace(
        id=uuid.uuid4(),
        provider_id=None,
        start_time=now + timedelta(hours=3),
        end_time=now + timedelta(hours=4),
        buffer_minutes=15,
        is_available=True,
    )
    return Store(slots={slot_1.id: slot_1, slot_2.id: slot_2})


@pytest.mark.asyncio
async def test_slot_unavailable_error_inherits_base() -> None:
    assert issubclass(SlotUnavailableError, SMSChatbotError)


@pytest.mark.asyncio
async def test_book_appointment_uses_for_update_and_marks_slot(store: Store) -> None:
    service = SchedulingService(session_factory=FakeSessionFactory(store))
    contact_id = uuid.uuid4()
    slot_id = next(iter(store.slots.keys()))

    appointment = await service.book_appointment(contact_id=contact_id, slot_id=slot_id)

    assert appointment.slot_id == slot_id
    assert store.slots[slot_id].is_available is False
    assert any(getattr(query, "_for_update_arg", None) is not None for query in store.for_update_queries)


@pytest.mark.asyncio
async def test_cancel_appointment_reopens_slot(store: Store) -> None:
    service = SchedulingService(session_factory=FakeSessionFactory(store))
    contact_id = uuid.uuid4()
    slot_id = next(iter(store.slots.keys()))

    appointment = await service.book_appointment(contact_id=contact_id, slot_id=slot_id)
    cancelled = await service.cancel_appointment(appointment.id, reason="Need to reschedule")

    assert cancelled.status == "cancelled"
    assert store.slots[slot_id].is_available is True


@pytest.mark.asyncio
async def test_reschedule_is_atomic_and_sets_link(store: Store) -> None:
    service = SchedulingService(session_factory=FakeSessionFactory(store))
    contact_id = uuid.uuid4()
    slot_ids = list(store.slots.keys())
    old_slot = slot_ids[0]
    new_slot = slot_ids[1]

    original = await service.book_appointment(contact_id=contact_id, slot_id=old_slot)
    replacement = await service.reschedule_appointment(appointment_id=original.id, new_slot_id=new_slot)

    assert store.slots[old_slot].is_available is True
    assert store.slots[new_slot].is_available is False
    assert store.appointments[original.id].status == "rescheduled"
    assert replacement.rescheduled_from_id == original.id


@pytest.mark.asyncio
async def test_get_fresh_alternatives_excludes_taken_slots(store: Store) -> None:
    service = SchedulingService(session_factory=FakeSessionFactory(store))
    slot_ids = list(store.slots.keys())

    alternatives = await service.get_fresh_alternatives(exclude_slot_ids=[slot_ids[0]])
    returned_ids = {slot.id for slot in alternatives}

    assert slot_ids[0] not in returned_ids
    assert slot_ids[1] in returned_ids


@pytest.mark.asyncio
async def test_get_available_slots_filters_range_and_availability(store: Store) -> None:
    service = SchedulingService(session_factory=FakeSessionFactory(store))
    slot_ids = list(store.slots.keys())
    store.slots[slot_ids[0]].is_available = False
    start = datetime.now(timezone.utc)
    end = start + timedelta(hours=6)

    available = await service.get_available_slots(date_from=start, date_to=end, limit=5)
    returned_ids = {slot.id for slot in available}

    assert slot_ids[0] not in returned_ids
    assert slot_ids[1] in returned_ids


@pytest.mark.asyncio
async def test_concurrent_booking_stress_exactly_one_success(store: Store) -> None:
    service = SchedulingService(session_factory=FakeSessionFactory(store))
    slot_id = next(iter(store.slots.keys()))

    async def attempt_booking() -> str:
        try:
            await service.book_appointment(contact_id=uuid.uuid4(), slot_id=slot_id)
            return "success"
        except SlotUnavailableError:
            return "unavailable"

    tasks = [attempt_booking() for _ in range(10)]
    results = await asyncio.gather(*tasks)

    assert results.count("success") == 1
    assert results.count("unavailable") == 9
