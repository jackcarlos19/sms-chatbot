from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
from zoneinfo import ZoneInfo

from openai import AsyncOpenAI

from app.config import get_settings

logger = logging.getLogger(__name__)

INTENTS = {
    "BOOK",
    "RESCHEDULE",
    "CANCEL",
    "QUESTION",
    "CONFIRM",
    "DENY",
    "SELECT_SLOT",
    "UNCLEAR",
}
FALLBACK_TEXT = "Sorry, having a brief issue. Please try again in a moment."


@dataclass
class IntentResult:
    intent: str
    confidence: float
    extracted_data: dict[str, Any] = field(default_factory=dict)
    response_text: str = FALLBACK_TEXT
    needs_info: list[str] = field(default_factory=list)


class AIService:
    def __init__(self, client: Optional[AsyncOpenAI] = None) -> None:
        self._settings = get_settings()
        self._client = client or AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self._settings.openrouter_api_key,
        )

    async def detect_intent(
        self,
        message: str,
        conversation_history: list[dict[str, Any]],
        available_slots: Optional[list[dict[str, Any]]] = None,
        current_appointment: Optional[dict[str, Any]] = None,
        conversation_state: str = "idle",
        contact_timezone: str = "UTC",
    ) -> IntentResult:
        context_section = self._build_context_section(
            available_slots, current_appointment
        )
        system_prompt = (
            f"You are a friendly SMS scheduling assistant for {self._settings.business_name}. "
            "Keep responses concise under 320 chars when possible and max 480 chars. "
            f"Current datetime: {datetime.now(timezone.utc).isoformat()} ({contact_timezone}). "
            f"Conversation state: {conversation_state}. {context_section} "
            "Use the tool to return structured output."
        )

        history = self._prepare_history(conversation_history)
        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": message})

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "submit_intent",
                    "description": "Return structured intent result.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "intent": {"type": "string", "enum": sorted(INTENTS)},
                            "confidence": {"type": "number"},
                            "extracted_data": {"type": "object"},
                            "response_text": {"type": "string"},
                            "needs_info": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                        "required": [
                            "intent",
                            "confidence",
                            "extracted_data",
                            "response_text",
                            "needs_info",
                        ],
                    },
                },
            }
        ]

        try:
            response = await self._client.chat.completions.create(
                model=self._settings.ai_model,
                messages=messages,
                tools=tools,
                tool_choice={"type": "function", "function": {"name": "submit_intent"}},
                temperature=0.2,
            )
            result = self._parse_intent_response(response)
            if result.confidence < 0.6:
                result.intent = "UNCLEAR"
                result.response_text = self._truncate(
                    "Could you clarify if you want to book, reschedule, cancel, or ask a question?"
                )
            return result
        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "ai_detect_intent_failed",
                extra={"error": str(exc), "user_message": message},
            )
            return IntentResult(
                intent="UNCLEAR",
                confidence=0.0,
                extracted_data={},
                response_text=FALLBACK_TEXT,
                needs_info=[],
            )

    async def parse_slot_selection(
        self,
        message: str,
        presented_slots: list[dict[str, Any]],
        timezone_name: str = "UTC",
    ) -> Optional[str]:
        if not presented_slots:
            return None

        normalized = (message or "").strip().lower()
        if not normalized:
            return None

        numeric = re.search(r"\b(\d+)\b", normalized)
        if numeric:
            choice = int(numeric.group(1))
            if 1 <= choice <= len(presented_slots):
                return str(presented_slots[choice - 1]["id"])

        ordinal_map = {
            "first": 1,
            "second": 2,
            "third": 3,
            "fourth": 4,
            "fifth": 5,
        }
        for word, number in ordinal_map.items():
            if word in normalized and number <= len(presented_slots):
                return str(presented_slots[number - 1]["id"])

        time_matches: list[str] = []
        day_matches: list[str] = []
        for slot in presented_slots:
            slot_id = str(slot["id"])
            dt_local = self._coerce_datetime(slot.get("start_time"), timezone_name)
            if dt_local is None:
                continue
            time_tokens = {
                dt_local.strftime("%-I%p").lower(),
                dt_local.strftime("%-I:%M%p").lower(),
                dt_local.strftime("%H:%M").lower(),
            }
            day_tokens = {
                dt_local.strftime("%A").lower(),
                dt_local.strftime("%a").lower(),
            }
            compact_message = normalized.replace(" ", "")
            if any(token.replace(" ", "") in compact_message for token in time_tokens):
                time_matches.append(slot_id)
            if any(token in normalized for token in day_tokens):
                day_matches.append(slot_id)

        if len(time_matches) == 1:
            return time_matches[0]
        if len(day_matches) == 1:
            return day_matches[0]

        try:
            slots_summary = [
                {
                    "id": str(slot["id"]),
                    "index": idx + 1,
                    "start": str(slot.get("start_time")),
                }
                for idx, slot in enumerate(presented_slots)
            ]
            response = await self._client.chat.completions.create(
                model=self._settings.ai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "Map user selection to a slot id or return null if unclear.",
                    },
                    {
                        "role": "user",
                        "content": json.dumps(
                            {"message": message, "presented_slots": slots_summary},
                            ensure_ascii=True,
                        ),
                    },
                ],
                tools=[
                    {
                        "type": "function",
                        "function": {
                            "name": "select_slot",
                            "parameters": {
                                "type": "object",
                                "properties": {"slot_id": {"type": ["string", "null"]}},
                                "required": ["slot_id"],
                            },
                        },
                    }
                ],
                tool_choice={"type": "function", "function": {"name": "select_slot"}},
                temperature=0.0,
            )
            tool_calls = response.choices[0].message.tool_calls or []
            if not tool_calls:
                return None
            args = json.loads(tool_calls[0].function.arguments or "{}")
            selected = args.get("slot_id")
            if selected is None:
                return None
            valid_ids = {str(slot["id"]) for slot in presented_slots}
            return str(selected) if str(selected) in valid_ids else None
        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "ai_parse_slot_selection_failed", extra={"error": str(exc)}
            )
            return None

    def generate_slot_presentation(
        self, slots: list[dict[str, Any]], timezone_name: str
    ) -> str:
        if not slots:
            return "I don't have open slots right now. Would you like me to check again later?"

        lines = ["Here are some available times:"]
        for idx, slot in enumerate(slots, start=1):
            dt_local = self._coerce_datetime(slot.get("start_time"), timezone_name)
            if dt_local is None:
                continue
            lines.append(f"{idx}) {dt_local.strftime('%a %b %d, %-I:%M %p')}")
        lines.append("Reply with a number to book.")
        return self._truncate("\n".join(lines))

    def generate_confirmation(
        self, appointment: dict[str, Any], timezone_name: str
    ) -> str:
        start = (
            appointment.get("start_time")
            or appointment.get("slot", {}).get("start_time")
            or appointment.get("appointment_time")
        )
        dt_local = self._coerce_datetime(start, timezone_name)
        if dt_local is None:
            return "You're all set! Your appointment is confirmed."
        return self._truncate(
            "You're all set! Your appointment is confirmed for "
            f"{dt_local.strftime('%a %b %d at %-I:%M %p')}. "
            "Reply CANCEL to cancel or RESCHEDULE to change."
        )

    def generate_error_response(self, error_type: str) -> str:
        responses = {
            "slot_unavailable": "Sorry, that time was just taken. I can share a few new options.",
            "api_error": FALLBACK_TEXT,
            "validation_error": "I couldn't understand that. Could you rephrase in one short sentence?",
        }
        return self._truncate(responses.get(error_type, FALLBACK_TEXT))

    def _prepare_history(
        self, conversation_history: list[dict[str, Any]]
    ) -> list[dict[str, str]]:
        limited = conversation_history[-10:]
        trimmed: list[dict[str, str]] = []
        token_budget = 2000

        for item in reversed(limited):
            role = str(item.get("role", "user"))
            content = str(item.get("content", ""))
            estimated_tokens = max(1, len(content) // 4)
            if token_budget - estimated_tokens < 0:
                continue
            trimmed.append({"role": role, "content": content})
            token_budget -= estimated_tokens

        return list(reversed(trimmed))

    def _build_context_section(
        self,
        available_slots: Optional[list[dict[str, Any]]],
        current_appointment: Optional[dict[str, Any]],
    ) -> str:
        context: dict[str, Any] = {}
        if available_slots:
            context["available_slots"] = [
                {"id": str(slot.get("id")), "start_time": str(slot.get("start_time"))}
                for slot in available_slots[:10]
            ]
        if current_appointment:
            context["current_appointment"] = current_appointment
        if not context:
            return ""
        return f"Context: {json.dumps(context, ensure_ascii=True)}."

    def _parse_intent_response(self, response: Any) -> IntentResult:
        tool_calls = response.choices[0].message.tool_calls or []
        payload: dict[str, Any]

        if tool_calls:
            payload = json.loads(tool_calls[0].function.arguments or "{}")
        else:
            content = response.choices[0].message.content or "{}"
            payload = json.loads(content)

        intent = str(payload.get("intent", "UNCLEAR")).upper()
        if intent not in INTENTS:
            intent = "UNCLEAR"

        confidence = float(payload.get("confidence", 0.0))
        extracted_data = payload.get("extracted_data") or {}
        response_text = self._truncate(str(payload.get("response_text", FALLBACK_TEXT)))
        needs_info = payload.get("needs_info") or []

        return IntentResult(
            intent=intent,
            confidence=confidence,
            extracted_data=extracted_data,
            response_text=response_text,
            needs_info=[str(value) for value in needs_info],
        )

    @staticmethod
    def _truncate(text: str) -> str:
        return text if len(text) <= 480 else text[:477] + "..."

    @staticmethod
    def _coerce_datetime(value: Any, timezone_name: str) -> Optional[datetime]:
        if value is None:
            return None
        if isinstance(value, datetime):
            dt = value
        else:
            try:
                dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            except ValueError:
                return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        try:
            return dt.astimezone(ZoneInfo(timezone_name))
        except Exception:  # noqa: BLE001
            return dt.astimezone(timezone.utc)
