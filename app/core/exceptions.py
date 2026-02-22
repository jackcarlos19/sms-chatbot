class SMSChatbotError(Exception):
    """Base exception for domain-level chatbot errors."""


class SlotUnavailableError(SMSChatbotError):
    """Raised when a requested slot is no longer available."""

