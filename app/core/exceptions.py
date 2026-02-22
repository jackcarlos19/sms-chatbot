from __future__ import annotations


class SMSChatbotError(Exception):
    """Base exception for domain-level chatbot errors."""

    def __init__(self, message: str, user_message: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.user_message = user_message


class SlotUnavailableError(SMSChatbotError):
    """Raised when a requested slot is no longer available."""
