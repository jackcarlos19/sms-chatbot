import asyncio
from datetime import datetime, time, timedelta, timezone

from sqlalchemy import Select, select

from app.database import AsyncSessionFactory
from app.models.availability import AvailabilitySlot


def _build_slots(start_date: datetime) -> list[tuple[datetime, datetime]]:
    slots: list[tuple[datetime, datetime]] = []
    opening = time(hour=9, minute=0)
    closing = time(hour=17, minute=0)
    slot_size = timedelta(minutes=30)

    for day_offset in range(7):
        day = (start_date + timedelta(days=day_offset)).date()
        if day.weekday() >= 5:  # Skip Saturday (5) and Sunday (6)
            continue
        current = datetime.combine(day, opening, tzinfo=timezone.utc)
        day_end = datetime.combine(day, closing, tzinfo=timezone.utc)
        while current < day_end:
            slot_end = current + slot_size
            slots.append((current, slot_end))
            current = slot_end
    return slots


async def seed() -> None:
    now = datetime.now(timezone.utc)
    target_slots = _build_slots(now)
    created = 0

    async with AsyncSessionFactory() as session:
        for start_time, end_time in target_slots:
            existing_query: Select[tuple[AvailabilitySlot]] = select(
                AvailabilitySlot
            ).where(
                AvailabilitySlot.start_time == start_time,
                AvailabilitySlot.end_time == end_time,
                AvailabilitySlot.provider_id.is_(None),
            )
            existing = await session.execute(existing_query)
            if existing.scalar_one_or_none() is not None:
                continue

            session.add(
                AvailabilitySlot(
                    provider_id=None,
                    start_time=start_time,
                    end_time=end_time,
                    buffer_minutes=0,
                    slot_type="standard",
                    is_available=True,
                )
            )
            created += 1

        await session.commit()

    print(f"Created {created} availability slots")


if __name__ == "__main__":
    asyncio.run(seed())
