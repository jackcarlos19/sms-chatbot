from __future__ import annotations

import asyncio
import uuid
from collections import defaultdict
from contextlib import AsyncExitStack
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.database import AsyncSessionFactory
from app.models.appointment import Appointment
from app.models.availability import AvailabilitySlot
from app.core.exceptions import SlotUnavailableError


class SchedulingService:
    def __init__(
        self, session_factory: async_sessionmaker[AsyncSession] | None = None
    ) -> None:
        self._session_factory = session_factory or AsyncSessionFactory
        # App-level lock provides deterministic safety in single-process test runs.
        self._slot_locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    async def get_available_slots(
        self,
        date_from: datetime,
        date_to: datetime,
        provider_id: Optional[uuid.UUID] = None,
        limit: int = 5,
    ) -> list[AvailabilitySlot]:
        async with self._session_factory() as session:
            query: Select[tuple[AvailabilitySlot]] = (
                select(AvailabilitySlot)
                .where(
                    AvailabilitySlot.is_available.is_(True),
                    AvailabilitySlot.start_time >= date_from,
                    AvailabilitySlot.end_time <= date_to,
                )
                .order_by(AvailabilitySlot.start_time.asc())
            )
            if provider_id is not None:
                query = query.where(AvailabilitySlot.provider_id == provider_id)

            rows = await session.execute(query)
            candidates = rows.scalars().all()

            # Respect slot buffer by ensuring effective end time remains in-range.
            filtered = [
                slot
                for slot in candidates
                if slot.is_available
                and (slot.end_time + timedelta(minutes=int(slot.buffer_minutes or 0)))
                <= date_to
            ]
            return filtered[:limit]

    async def book_appointment(
        self, contact_id: uuid.UUID, slot_id: uuid.UUID
    ) -> Appointment:
        lock_key = str(slot_id)
        async with self._slot_locks[lock_key]:
            async with self._session_factory() as session:
                async with session.begin():
                    slot_query: Select[tuple[AvailabilitySlot]] = (
                        select(AvailabilitySlot)
                        .where(AvailabilitySlot.id == slot_id)
                        .with_for_update()
                    )
                    slot_result = await session.execute(slot_query)
                    slot = slot_result.scalar_one_or_none()
                    if slot is None or not slot.is_available:
                        raise SlotUnavailableError(
                            "The selected slot is no longer available."
                        )

                    slot.is_available = False

                    appointment = Appointment(
                        contact_id=contact_id,
                        slot_id=slot_id,
                        status="confirmed",
                        booked_at=datetime.now(timezone.utc),
                    )
                    session.add(appointment)
                    await session.flush()
                    return appointment

    async def cancel_appointment(
        self,
        appointment_id: uuid.UUID,
        reason: str | None = None,
    ) -> Appointment:
        async with self._session_factory() as session:
            async with session.begin():
                appointment_query: Select[tuple[Appointment]] = (
                    select(Appointment)
                    .where(Appointment.id == appointment_id)
                    .with_for_update()
                )
                appointment_result = await session.execute(appointment_query)
                appointment = appointment_result.scalar_one_or_none()
                if appointment is None:
                    raise ValueError("Appointment not found.")

                slot_query: Select[tuple[AvailabilitySlot]] = (
                    select(AvailabilitySlot)
                    .where(AvailabilitySlot.id == appointment.slot_id)
                    .with_for_update()
                )
                slot_result = await session.execute(slot_query)
                slot = slot_result.scalar_one_or_none()
                if slot is None:
                    raise ValueError("Linked slot not found.")

                appointment.status = "cancelled"
                appointment.cancelled_at = datetime.now(timezone.utc)
                appointment.cancellation_reason = reason
                appointment.version = int(appointment.version or 1) + 1
                slot.is_available = True
                await session.flush()
                return appointment

    async def reschedule_appointment(
        self,
        appointment_id: uuid.UUID,
        new_slot_id: uuid.UUID,
    ) -> Appointment:
        # Lock appointment first to read a stable old slot id.
        async with self._slot_locks[str(appointment_id)]:
            async with self._session_factory() as session:
                async with session.begin():
                    appointment_query: Select[tuple[Appointment]] = (
                        select(Appointment)
                        .where(Appointment.id == appointment_id)
                        .with_for_update()
                    )
                    appointment_result = await session.execute(appointment_query)
                    old_appointment = appointment_result.scalar_one_or_none()
                    if old_appointment is None:
                        raise ValueError("Appointment not found.")

                    # Ensure deterministic lock ordering for in-process guards.
                    slot_lock_keys = sorted(
                        [str(old_appointment.slot_id), str(new_slot_id)]
                    )
                    async with AsyncExitStack() as stack:
                        for key in slot_lock_keys:
                            await stack.enter_async_context(self._slot_locks[key])

                        old_slot_query: Select[tuple[AvailabilitySlot]] = (
                            select(AvailabilitySlot)
                            .where(AvailabilitySlot.id == old_appointment.slot_id)
                            .with_for_update()
                        )
                        old_slot_result = await session.execute(old_slot_query)
                        old_slot = old_slot_result.scalar_one_or_none()
                        if old_slot is None:
                            raise ValueError("Existing slot not found.")

                        new_slot_query: Select[tuple[AvailabilitySlot]] = (
                            select(AvailabilitySlot)
                            .where(AvailabilitySlot.id == new_slot_id)
                            .with_for_update()
                        )
                        new_slot_result = await session.execute(new_slot_query)
                        new_slot = new_slot_result.scalar_one_or_none()
                        if new_slot is None or not new_slot.is_available:
                            raise SlotUnavailableError(
                                "Requested reschedule slot is unavailable."
                            )

                        old_slot.is_available = True
                        new_slot.is_available = False
                        old_appointment.status = "rescheduled"
                        old_appointment.version = int(old_appointment.version or 1) + 1

                        replacement = Appointment(
                            contact_id=old_appointment.contact_id,
                            slot_id=new_slot.id,
                            status="confirmed",
                            booked_at=datetime.now(timezone.utc),
                            rescheduled_from_id=old_appointment.id,
                        )
                        session.add(replacement)
                        await session.flush()
                        return replacement

    async def get_fresh_alternatives(
        self,
        exclude_slot_ids: list[uuid.UUID],
        date_from: datetime | None = None,
        limit: int = 5,
        provider_id: uuid.UUID | None = None,
    ) -> list[AvailabilitySlot]:
        start = date_from or datetime.now(timezone.utc)
        end = start + timedelta(days=7)

        async with self._session_factory() as session:
            query: Select[tuple[AvailabilitySlot]] = (
                select(AvailabilitySlot)
                .where(
                    AvailabilitySlot.is_available.is_(True),
                    AvailabilitySlot.start_time >= start,
                    AvailabilitySlot.end_time <= end,
                )
                .order_by(AvailabilitySlot.start_time.asc())
            )
            if exclude_slot_ids:
                query = query.where(AvailabilitySlot.id.not_in(exclude_slot_ids))
            if provider_id is not None:
                query = query.where(AvailabilitySlot.provider_id == provider_id)

            rows = await session.execute(query)
            return [slot for slot in rows.scalars().all() if slot.is_available][:limit]
