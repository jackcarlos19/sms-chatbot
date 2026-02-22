from __future__ import annotations

import uuid
from datetime import datetime, time, timezone
from types import SimpleNamespace
from typing import Any

import pytest

from app.core.quiet_hours import is_in_quiet_hours, seconds_until_quiet_hours_end
from app.services.campaign_service import CampaignService
from app.workers import tasks


def _extract_where_values(query: Any) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for clause in getattr(query, "_where_criteria", []):
        left = getattr(clause, "left", None)
        right = getattr(clause, "right", None)
        op_name = getattr(getattr(clause, "operator", None), "__name__", "")
        if left is None:
            continue
        key = getattr(left, "key", "")
        if key and op_name in {"eq", "lt"}:
            values[f"{key}:{op_name}"] = getattr(right, "value", None)
    return values


class FakeResult:
    def __init__(self, items: list[Any]) -> None:
        self._items = items

    def scalar_one_or_none(self):
        return self._items[0] if self._items else None

    def scalars(self) -> "FakeResult":
        return self

    def all(self) -> list[Any]:
        return list(self._items)


class FakeSession:
    def __init__(self, campaign, recipients, contacts, messages):
        self.campaign = campaign
        self.recipients = recipients
        self.contacts = contacts
        self.messages = messages

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):  # noqa: ANN001
        return None

    async def execute(self, query):
        model = query.column_descriptions[0]["entity"]
        values = _extract_where_values(query)
        if model.__name__ == "Campaign":
            if values.get("id:eq") == self.campaign.id:
                return FakeResult([self.campaign])
            return FakeResult([])
        if model.__name__ == "CampaignRecipient":
            all_rows = [r for r in self.recipients if r.campaign_id == values.get("campaign_id:eq")]
            offset = int(getattr(getattr(query, "_offset_clause", None), "value", 0) or 0)
            limit = int(getattr(getattr(query, "_limit_clause", None), "value", len(all_rows)) or len(all_rows))
            return FakeResult(all_rows[offset : offset + limit])
        if model.__name__ == "Contact":
            match = [c for c in self.contacts if c.id == values.get("id:eq")]
            return FakeResult(match)
        if model.__name__ == "Message":
            cutoff = values.get("created_at:lt")
            rows = [m for m in self.messages if m.status == "queued" and m.created_at < cutoff]
            return FakeResult(rows)
        raise AssertionError("Unsupported query in fake session")

    async def scalar(self, query):
        _ = query
        return 0

    async def commit(self):
        return None

    async def begin(self):
        return self


class FakeSessionFactory:
    def __init__(self, session: FakeSession):
        self.session = session

    def __call__(self):
        return self.session


class FakeRedis:
    def __init__(self) -> None:
        self.jobs: list[tuple] = []

    async def enqueue_job(self, *args, **kwargs):
        self.jobs.append((args, kwargs))


class FakeSMSService:
    def __init__(self):
        self.sent: list[tuple[str, str, str | None]] = []

    async def send_message(self, to: str, body: str, campaign_id: str | None = None):
        self.sent.append((to, body, campaign_id))
        return SimpleNamespace(status="sent", sms_sid="SM1")


def test_quiet_hours_midnight_wraparound_math() -> None:
    # 02:00 local should be inside 21:00 -> 09:00 quiet window.
    now = datetime(2026, 2, 22, 7, 0, tzinfo=timezone.utc)  # 02:00 America/New_York (EST)
    assert is_in_quiet_hours(now, "America/New_York", time(21, 0), time(9, 0)) is True

    # 14:00 local should be outside quiet window.
    day = datetime(2026, 2, 22, 19, 0, tzinfo=timezone.utc)  # 14:00 EST
    assert is_in_quiet_hours(day, "America/New_York", time(21, 0), time(9, 0)) is False
    assert seconds_until_quiet_hours_end(now, "America/New_York", time(21, 0), time(9, 0)) > 0


def test_template_rendering_with_first_name_fallback() -> None:
    service = CampaignService()
    campaign = SimpleNamespace(message_template="Hi {first_name} from {business_name}. Call {phone_number}.")

    with_name = SimpleNamespace(first_name="Jamie")
    without_name = SimpleNamespace(first_name=None)

    assert "Hi Jamie" in service.render_template(campaign, with_name)
    assert "Hi there" in service.render_template(campaign, without_name)


@pytest.mark.asyncio
async def test_process_campaign_batch_rate_limit_and_opt_in_recheck(monkeypatch) -> None:
    campaign_id = uuid.uuid4()
    contact_ok = SimpleNamespace(
        id=uuid.uuid4(),
        phone_number="+15550000001",
        timezone="UTC",
        opt_in_status="opted_in",
        first_name="Sam",
    )
    contact_out = SimpleNamespace(
        id=uuid.uuid4(),
        phone_number="+15550000002",
        timezone="UTC",
        opt_in_status="opted_out",
        first_name=None,
    )
    campaign = SimpleNamespace(
        id=campaign_id,
        message_template="Hi {first_name}",
        status="scheduled",
        respect_timezone=False,
        quiet_hours_start=time(21, 0),
        quiet_hours_end=time(9, 0),
    )
    recipients = [
        SimpleNamespace(id=uuid.uuid4(), campaign_id=campaign_id, contact_id=contact_ok.id, status="pending", sent_at=None),
        SimpleNamespace(id=uuid.uuid4(), campaign_id=campaign_id, contact_id=contact_out.id, status="pending", sent_at=None),
    ]
    contacts = [contact_ok, contact_out]
    messages: list[Any] = []
    session = FakeSession(campaign=campaign, recipients=recipients, contacts=contacts, messages=messages)
    redis = FakeRedis()
    sms = FakeSMSService()

    async def fake_sleep(seconds: float):
        fake_sleep.calls.append(seconds)

    fake_sleep.calls = []

    monkeypatch.setattr(tasks, "AsyncSessionFactory", FakeSessionFactory(session))
    monkeypatch.setattr(tasks, "SMSService", lambda: sms)
    monkeypatch.setattr(tasks.asyncio, "sleep", fake_sleep)

    processed = await tasks.process_campaign_batch({"redis": redis}, str(campaign_id), 0, 50)

    assert processed == 1
    assert recipients[0].status == "sent"
    assert recipients[1].status == "skipped"  # opt-in re-check before send
    assert len(sms.sent) == 1
    assert fake_sleep.calls == [1]  # explicit 1 msg/sec delay
