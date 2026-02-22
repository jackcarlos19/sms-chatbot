from __future__ import annotations

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo


def _to_local(now_utc: datetime, timezone_name: str) -> datetime:
    return now_utc.astimezone(ZoneInfo(timezone_name))


def is_in_quiet_hours(
    now_utc: datetime,
    timezone_name: str,
    quiet_start: time = time(21, 0),
    quiet_end: time = time(9, 0),
) -> bool:
    local_now = _to_local(now_utc, timezone_name)
    current = local_now.timetz().replace(tzinfo=None)

    # Handles same-day windows and midnight wraparound (e.g. 21:00 -> 09:00).
    if quiet_start <= quiet_end:
        return quiet_start <= current < quiet_end
    return current >= quiet_start or current < quiet_end


def seconds_until_quiet_hours_end(
    now_utc: datetime,
    timezone_name: str,
    quiet_start: time = time(21, 0),
    quiet_end: time = time(9, 0),
) -> int:
    local_now = _to_local(now_utc, timezone_name)
    end_today = local_now.replace(
        hour=quiet_end.hour,
        minute=quiet_end.minute,
        second=0,
        microsecond=0,
    )
    if end_today <= local_now:
        end_today = end_today + timedelta(days=1)
    return max(0, int((end_today - local_now).total_seconds()))
