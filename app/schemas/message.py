from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


class MessageResponse(BaseModel):
    id: str
    contact_id: Optional[str]
    direction: str
    body: str
    sms_sid: Optional[str]
    status: str
    error_code: Optional[str]
    campaign_id: Optional[str]
    created_at: str

    model_config = ConfigDict(from_attributes=True)
