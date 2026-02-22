from __future__ import annotations

import json
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.services.ai_service import AIService


def _tool_response(function_name: str, payload: dict) -> SimpleNamespace:
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    tool_calls=[
                        SimpleNamespace(
                            function=SimpleNamespace(
                                name=function_name,
                                arguments=json.dumps(payload),
                            )
                        )
                    ],
                    content=None,
                )
            )
        ]
    )


class FakeCompletions:
    def __init__(self, response: SimpleNamespace | None = None, error: Exception | None = None) -> None:
        self._response = response
        self._error = error

    async def create(self, **kwargs):  # noqa: ANN003
        if self._error:
            raise self._error
        return self._response


class FakeClient:
    def __init__(self, response: SimpleNamespace | None = None, error: Exception | None = None) -> None:
        self.chat = SimpleNamespace(completions=FakeCompletions(response=response, error=error))


@pytest.mark.asyncio
async def test_detect_intent_returns_structured_result() -> None:
    response = _tool_response(
        "submit_intent",
        {
            "intent": "BOOK",
            "confidence": 0.95,
            "extracted_data": {"date_preference": "2026-03-15", "time_preference": "afternoon"},
            "response_text": "I can help with that. Let me check next Tuesday afternoon.",
            "needs_info": ["time"],
        },
    )
    service = AIService(client=FakeClient(response=response))

    result = await service.detect_intent(
        message="Can I book for next Tuesday afternoon?",
        conversation_history=[{"role": "user", "content": "Hi"}],
    )

    assert result.intent == "BOOK"
    assert result.confidence == 0.95
    assert result.extracted_data["date_preference"] == "2026-03-15"
    assert result.needs_info == ["time"]


@pytest.mark.asyncio
async def test_detect_intent_fallback_on_error() -> None:
    service = AIService(client=FakeClient(error=TimeoutError("timeout")))

    result = await service.detect_intent(
        message="book",
        conversation_history=[],
    )

    assert result.intent == "UNCLEAR"
    assert result.confidence == 0.0
    assert "brief issue" in result.response_text


@pytest.mark.asyncio
async def test_parse_slot_selection_handles_numeric_and_ordinal() -> None:
    service = AIService(client=FakeClient(response=_tool_response("select_slot", {"slot_id": None})))
    slots = [
        {"id": "slot-1", "start_time": "2026-03-15T14:00:00+00:00"},
        {"id": "slot-2", "start_time": "2026-03-15T15:30:00+00:00"},
        {"id": "slot-3", "start_time": "2026-03-16T10:00:00+00:00"},
    ]

    assert await service.parse_slot_selection("2", slots) == "slot-2"
    assert await service.parse_slot_selection("the second one please", slots) == "slot-2"


@pytest.mark.asyncio
async def test_parse_slot_selection_uses_llm_fallback() -> None:
    response = _tool_response("select_slot", {"slot_id": "slot-3"})
    service = AIService(client=FakeClient(response=response))
    slots = [
        {"id": "slot-1", "start_time": "2026-03-15T14:00:00+00:00"},
        {"id": "slot-2", "start_time": "2026-03-15T15:30:00+00:00"},
        {"id": "slot-3", "start_time": "2026-03-16T10:00:00+00:00"},
    ]

    selected = await service.parse_slot_selection("that morning option works", slots)
    assert selected == "slot-3"


def test_history_is_capped_to_last_ten_messages() -> None:
    service = AIService(client=FakeClient(response=_tool_response("submit_intent", {})))
    history = [{"role": "user", "content": f"message-{i}"} for i in range(20)]
    prepared = service._prepare_history(history)
    assert len(prepared) == 10
    assert prepared[0]["content"] == "message-10"


def test_generate_slot_and_confirmation_text() -> None:
    service = AIService(client=FakeClient(response=_tool_response("submit_intent", {})))
    slots = [{"id": "slot-1", "start_time": datetime(2026, 3, 15, 14, 0, tzinfo=timezone.utc)}]

    presentation = service.generate_slot_presentation(slots, "America/New_York")
    confirmation = service.generate_confirmation(
        {"start_time": datetime(2026, 3, 15, 14, 0, tzinfo=timezone.utc)},
        "America/New_York",
    )

    assert "Here are some available times" in presentation
    assert "Reply with a number to book" in presentation
    assert "You're all set! Your appointment is confirmed for" in confirmation
