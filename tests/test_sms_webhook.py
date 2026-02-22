from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(autouse=True)
def clear_overrides() -> None:
    yield
    app.dependency_overrides.clear()


class FakeSMSService:
    def __init__(self, valid_signature: bool = True) -> None:
        self.valid_signature = valid_signature
        self.signature_calls = 0
        self.inbound_calls: list[tuple[str, str, str, object | None]] = []
        self.status_calls: list[tuple[str, str, str | None, str | None]] = []

    def validate_signature(
        self, url: str, params: dict[str, str], signature: str
    ) -> bool:
        self.signature_calls += 1
        return self.valid_signature

    async def handle_inbound(
        self,
        from_number: str,
        body: str,
        sms_sid: str,
        conversation_service=None,
    ) -> None:
        self.inbound_calls.append((from_number, body, sms_sid, conversation_service))

    async def update_status(
        self,
        sms_sid: str,
        status: str,
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> None:
        self.status_calls.append((sms_sid, status, error_code, error_message))


class FakeIdempotencyService:
    def __init__(self, duplicate: bool = False) -> None:
        self.duplicate = duplicate
        self.marked: list[str] = []

    async def is_duplicate(self, sms_sid: str) -> bool:
        return self.duplicate

    async def mark_processed(self, sms_sid: str) -> None:
        self.marked.append(sms_sid)


class FakeConversationService:
    async def process_inbound_message(
        self, phone_number: str, body: str, sms_sid: str
    ) -> None:
        _ = (phone_number, body, sms_sid)


def test_inbound_returns_twiml_and_dispatches_background_task(monkeypatch) -> None:
    fake_sms = FakeSMSService(valid_signature=True)
    fake_idempotency = FakeIdempotencyService(duplicate=False)
    fake_conversation = FakeConversationService()
    monkeypatch.setattr("app.api.webhooks.get_sms_service", lambda: fake_sms)
    monkeypatch.setattr(
        "app.api.webhooks.get_idempotency_service", lambda: fake_idempotency
    )
    monkeypatch.setattr(
        "app.api.webhooks.get_conversation_service", lambda: fake_conversation
    )

    with TestClient(app) as client:
        response = client.post(
            "/webhooks/sms/inbound",
            data={"From": "+12345678901", "Body": "Hello", "MessageSid": "SM123"},
            headers={
                "X-Twilio-Signature": "valid",
                "X-Forwarded-Proto": "https",
                "X-Forwarded-Host": "example.test",
            },
        )

    assert response.status_code == 200
    assert response.text == "<Response></Response>"
    assert response.headers["content-type"].startswith("application/xml")
    assert fake_sms.signature_calls == 1
    assert fake_idempotency.marked == ["SM123"]
    assert fake_sms.inbound_calls == [
        ("+12345678901", "Hello", "SM123", fake_conversation)
    ]


def test_inbound_duplicate_returns_immediately(monkeypatch) -> None:
    fake_sms = FakeSMSService(valid_signature=True)
    fake_idempotency = FakeIdempotencyService(duplicate=True)
    monkeypatch.setattr("app.api.webhooks.get_sms_service", lambda: fake_sms)
    monkeypatch.setattr(
        "app.api.webhooks.get_idempotency_service", lambda: fake_idempotency
    )
    monkeypatch.setattr(
        "app.api.webhooks.get_conversation_service", lambda: FakeConversationService()
    )

    with TestClient(app) as client:
        response = client.post(
            "/webhooks/sms/inbound",
            data={"From": "+12345678901", "Body": "Hello", "MessageSid": "SM_DUP"},
            headers={
                "X-Twilio-Signature": "valid",
                "X-Forwarded-Proto": "https",
                "X-Forwarded-Host": "example.test",
            },
        )

    assert response.status_code == 200
    assert response.text == "<Response></Response>"
    assert fake_sms.inbound_calls == []
    assert fake_idempotency.marked == []


def test_inbound_rejects_invalid_signature(monkeypatch) -> None:
    fake_sms = FakeSMSService(valid_signature=False)
    fake_idempotency = FakeIdempotencyService(duplicate=False)
    monkeypatch.setattr("app.api.webhooks.get_sms_service", lambda: fake_sms)
    monkeypatch.setattr(
        "app.api.webhooks.get_idempotency_service", lambda: fake_idempotency
    )
    monkeypatch.setattr(
        "app.api.webhooks.get_conversation_service", lambda: FakeConversationService()
    )

    with TestClient(app) as client:
        response = client.post(
            "/webhooks/sms/inbound",
            data={"From": "+12345678901", "Body": "Hello", "MessageSid": "SM_BAD"},
            headers={
                "X-Twilio-Signature": "invalid",
                "X-Forwarded-Proto": "https",
                "X-Forwarded-Host": "example.test",
            },
        )

    assert response.status_code == 403
    assert fake_sms.signature_calls == 1
    assert fake_sms.inbound_calls == []


def test_status_callback_updates_message(monkeypatch) -> None:
    fake_sms = FakeSMSService(valid_signature=True)
    monkeypatch.setattr("app.api.webhooks.get_sms_service", lambda: fake_sms)

    with TestClient(app) as client:
        response = client.post(
            "/webhooks/sms/status",
            data={
                "MessageSid": "SM_STATUS",
                "MessageStatus": "delivered",
                "ErrorCode": "",
                "ErrorMessage": "",
            },
            headers={
                "X-Twilio-Signature": "valid",
                "X-Forwarded-Proto": "https",
                "X-Forwarded-Host": "example.test",
            },
        )

    assert response.status_code == 200
    assert fake_sms.signature_calls == 1
    assert fake_sms.status_calls == [("SM_STATUS", "delivered", None, None)]
