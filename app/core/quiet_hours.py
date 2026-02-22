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
    current = local_now.time()

    # Handles same-day windows and midnight wraparound (e.g. 21:00 -> 09:00).
    if quiet_start < quiet_end:
        return quiet_start <= current < quiet_end
    return current >= quiet_start or current < quiet_end


def seconds_until_quiet_hours_end(
    now_utc: datetime,
    timezone_name: str,
    quiet_start: time = time(21, 0),
    quiet_end: time = time(9, 0),
) -> int:
    if not is_in_quiet_hours(
        now_utc=now_utc,
        timezone_name=timezone_name,
        quiet_start=quiet_start,
        quiet_end=quiet_end,
    ):
        return 0

    local_now = _to_local(now_utc, timezone_name)
    local_time = local_now.time()

    if local_time < quiet_end:
        end_dt = datetime.combine(local_now.date(), quiet_end, tzinfo=local_now.tzinfo)
    else:
        end_dt = datetime.combine(
            local_now.date() + timedelta(days=1), quiet_end, tzinfo=local_now.tzinfo
        )

    return max(0, int((end_dt - local_now).total_seconds()))
