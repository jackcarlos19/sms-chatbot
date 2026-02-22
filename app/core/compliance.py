from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

OPT_OUT_KEYWORDS = {"STOP", "STOPALL", "UNSUBSCRIBE", "END", "QUIT"}
# NOTE: "CANCEL" intentionally excluded — it conflicts with appointment cancellation.
# Twilio's Advanced Opt-Out handles CANCEL at the carrier level if needed.
OPT_IN_KEYWORDS = {"START", "YES", "UNSTOP"}
HELP_KEYWORDS = {"HELP", "INFO"}


def is_compliance_keyword(text: str) -> tuple[bool, str | None]:
    normalized = (text or "").strip().upper()
    if normalized in OPT_OUT_KEYWORDS:
        return True, "opt_out"
    if normalized in OPT_IN_KEYWORDS:
        return True, "opt_in"
    if normalized in HELP_KEYWORDS:
        return True, "help"
    return False, None


def handle_compliance(
    contact: SimpleNamespace,
    keyword_type: str,
    business_name: str,
    support_number: str,
) -> str:
    now = datetime.now(timezone.utc)
    if keyword_type == "opt_out":
        contact.opt_in_status = "opted_out"
        contact.opt_out_date = now
        return (
            "You have been unsubscribed and will not receive further messages. "
            "Reply START to re-subscribe."
        )

    if keyword_type == "opt_in":
        contact.opt_in_status = "opted_in"
        contact.opt_in_date = now
        return (
            f"You have been re-subscribed to {business_name} messages. "
            "Reply STOP to unsubscribe."
        )

    if keyword_type == "help":
        return (
            f"{business_name}: For support call {support_number}. "
            "Msg frequency varies. Msg&data rates may apply. Reply STOP to cancel."
        )

    raise ValueError(f"Unknown compliance keyword type: {keyword_type}")
