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
        self._client = client or self._build_client()

    def _build_client(self) -> AsyncOpenAI:
        if self._settings.ai_provider == "vercel_gateway":
            base_url = self._settings.ai_base_url or "https://ai-gateway.vercel.sh/v1"
            api_key = self._settings.vercel_ai_gateway_api_key
            return AsyncOpenAI(base_url=base_url, api_key=api_key)

        base_url = self._settings.ai_base_url or "https://openrouter.ai/api/v1"
        return AsyncOpenAI(base_url=base_url, api_key=self._settings.openrouter_api_key)

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
        state_instructions = {
            "idle": (
                "User is starting fresh. Detect: BOOK (any scheduling intent), "
                "RESCHEDULE, CANCEL, or QUESTION."
            ),
            "showing_slots": (
                "User sees numbered time slots. Detect: SELECT_SLOT (they pick one), "
                "BOOK (want different times), CANCEL/RESCHEDULE (changed mind)."
            ),
            "confirming_booking": (
                "User was asked 'Reply YES to confirm [time]'. "
                "ANY affirmative (yes/yep/y/yeah/sure/ok/confirm/👍/sounds good/do it/book it/perfect) -> CONFIRM. "
                "ANY negative (no/nope/nah/different/change) -> DENY. "
                "STRONGLY bias toward CONFIRM for ambiguous affirmatives."
            ),
            "confirming_cancel": (
                "User was asked to confirm cancellation. "
                "Affirmative -> CONFIRM. Negative -> DENY."
            ),
            "reschedule_show_slots": (
                "User is picking a new time for rescheduling. "
                "Same as showing_slots."
            ),
            "confirming_reschedule": (
                "User was asked to confirm rescheduled time. "
                "Affirmative -> CONFIRM. Negative -> DENY."
            ),
            "awaiting_info": (
                "We asked for more info. Detect the underlying intent from their reply."
            ),
        }
        state_instruction = state_instructions.get(
            conversation_state, state_instructions["idle"]
        )
        system_prompt = (
            f"You are a concise SMS scheduling assistant for {self._settings.business_name}.\n\n"
            "HARD RULES:\n"
            "- Responses MUST be under 300 characters. This is SMS.\n"
            "- NEVER invent details (prices, locations, hours, services). "
            "If asked, respond: 'Please contact us for that info.'\n"
            "- NEVER write poems, stories, jokes, or off-topic content. "
            "Redirect: 'I help with scheduling! Want to book an appointment?'\n"
            "- NEVER ask more than one question per message.\n"
            "- When showing time slots, always use numbered format.\n\n"
            f"CURRENT STATE: {conversation_state}\n"
            f"INSTRUCTION: {state_instruction}\n\n"
            f"Datetime: {datetime.now(timezone.utc).isoformat()} "
            f"(contact tz: {contact_timezone}).\n"
            f"{context_section}\n"
            "Return your response via the submit_intent tool."
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
            return self._heuristic_intent_result(
                message=message,
                conversation_state=conversation_state,
                available_slots=available_slots or [],
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
                        "content": (
                            "Map the user's message to one of the presented slot IDs. "
                            "If the user says a number (e.g. '2'), map to the slot at that index. "
                            "If the user describes a time/day, find the closest match. "
                            "Return null ONLY if truly unclear. Never invent slot IDs."
                        ),
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
        payload: dict[str, Any] = {}

        if tool_calls:
            raw_args = tool_calls[0].function.arguments or "{}"
            try:
                payload = json.loads(raw_args)
            except json.JSONDecodeError:
                logger.warning("tool_call_json_parse_failed", extra={"raw": raw_args[:500]})

        if not payload:
            content = response.choices[0].message.content or ""
            try:
                match = re.search(r"\{[^{}]*\"intent\"[^{}]*\}", content, re.DOTALL)
                if match:
                    payload = json.loads(match.group(0))
                elif content.strip().startswith("{"):
                    payload = json.loads(content)
            except (json.JSONDecodeError, ValueError):
                logger.warning(
                    "content_json_parse_failed", extra={"content": content[:300]}
                )

        if not payload:
            return IntentResult(
                intent="UNCLEAR",
                confidence=0.0,
                extracted_data={},
                response_text=FALLBACK_TEXT,
                needs_info=[],
            )

        raw_intent = str(payload.get("intent", "UNCLEAR")).strip().upper()
        intent_aliases = {
            "CONFIRM_YES": "CONFIRM",
            "CONFIRMATION": "CONFIRM",
            "YES": "CONFIRM",
            "AFFIRM": "CONFIRM",
            "DENY_NO": "DENY",
            "NO": "DENY",
            "REJECTION": "DENY",
            "BOOKING": "BOOK",
            "SCHEDULE": "BOOK",
            "SELECT": "SELECT_SLOT",
            "SLOT_SELECTION": "SELECT_SLOT",
            "ASK": "QUESTION",
            "FAQ": "QUESTION",
            "INFO": "QUESTION",
            "UNKNOWN": "UNCLEAR",
            "NONE": "UNCLEAR",
        }
        intent = intent_aliases.get(raw_intent, raw_intent)
        if intent not in INTENTS:
            logger.warning(
                "unknown_intent", extra={"raw": raw_intent, "resolved": "UNCLEAR"}
            )
            intent = "UNCLEAR"

        confidence = float(payload.get("confidence", 0.0))
        if confidence > 1.0:
            confidence = min(confidence / 100.0, 1.0)
        confidence = max(0.0, min(1.0, confidence))

        extracted_data = payload.get("extracted_data") or {}
        if not isinstance(extracted_data, dict):
            extracted_data = {}
        response_text = self._truncate(str(payload.get("response_text", FALLBACK_TEXT)))
        needs_info = payload.get("needs_info") or []
        if not isinstance(needs_info, list):
            needs_info = []

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

    @staticmethod
    def _contains_any(text: str, terms: list[str]) -> bool:
        return any(term in text for term in terms)

    def _heuristic_intent_result(
        self,
        message: str,
        conversation_state: str,
        available_slots: list[dict[str, Any]],
    ) -> IntentResult:
        text = (message or "").strip().lower()
        affirmative = [
            "yes",
            "y",
            "yep",
            "yeah",
            "sure",
            "ok",
            "okay",
            "confirm",
            "sounds good",
            "do it",
            "book it",
            "perfect",
            "👍",
        ]
        negative = ["no", "nope", "nah", "different", "change"]

        if conversation_state in {
            "confirming_booking",
            "confirming_cancel",
            "confirming_reschedule",
        }:
            if self._contains_any(text, affirmative):
                return IntentResult("CONFIRM", 0.8, {}, "Confirmed.", [])
            if self._contains_any(text, negative):
                return IntentResult("DENY", 0.8, {}, "No problem.", [])

        if available_slots and re.search(r"\b\d+\b", text):
            return IntentResult("SELECT_SLOT", 0.75, {}, "Selecting a slot.", [])

        if self._contains_any(text, ["reschedule", "move", "change time"]):
            return IntentResult("RESCHEDULE", 0.75, {}, "Let's reschedule.", [])
        if "cancel" in text:
            return IntentResult("CANCEL", 0.75, {}, "Let's cancel.", [])
        if self._contains_any(text, ["book", "appointment", "schedule"]):
            return IntentResult("BOOK", 0.75, {}, "Let's get you booked.", [])
        if self._contains_any(text, ["poem", "story", "joke"]):
            return IntentResult(
                "QUESTION",
                0.7,
                {},
                "I help with scheduling. Want to book an appointment?",
                [],
            )
        if self._contains_any(text, ["how much", "price", "cost", "charge"]):
            return IntentResult(
                "QUESTION",
                0.7,
                {},
                "Please contact us for that info.",
                [],
            )
        if "?" in text:
            return IntentResult("QUESTION", 0.65, {}, "Please contact us for that info.", [])
        return IntentResult("UNCLEAR", 0.0, {}, FALLBACK_TEXT, [])
