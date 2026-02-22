from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    status: str
    db: str
    redis: str

    model_config = ConfigDict(from_attributes=True)
