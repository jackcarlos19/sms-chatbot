from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


class CampaignResponse(BaseModel):
    id: str
    name: str
    status: str
    scheduled_at: Optional[str]
    total_recipients: int
    sent_count: int
    delivered_count: int
    failed_count: int
    reply_count: int
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class CampaignCreateResponse(BaseModel):
    id: str
    name: str
    status: str
    total_recipients: int

    model_config = ConfigDict(from_attributes=True)


class CampaignStatsResponse(BaseModel):
    total_recipients: int
    sent_count: int
    delivered_count: int
    failed_count: int

    model_config = ConfigDict(from_attributes=True)
