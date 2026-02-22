from __future__ import annotations

import logging
import re
from typing import Any

import structlog

from app.core.masking import mask_phone_number

PHONE_PATTERN = re.compile(r"\+[1-9]\d{7,14}")


def _mask_value(value: Any) -> Any:
    if isinstance(value, str):
        if PHONE_PATTERN.fullmatch(value):
            return mask_phone_number(value)
        return PHONE_PATTERN.sub(lambda m: mask_phone_number(m.group(0)), value)
    if isinstance(value, dict):
        masked: dict[str, Any] = {}
        for key, item in value.items():
            if "phone" in key.lower() and isinstance(item, str):
                masked[key] = mask_phone_number(item)
            else:
                masked[key] = _mask_value(item)
        return masked
    if isinstance(value, list):
        return [_mask_value(item) for item in value]
    return value


def mask_pii_processor(
    logger: Any, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    _ = (logger, method_name)
    return _mask_value(event_dict)


def configure_structured_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            mask_pii_processor,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
