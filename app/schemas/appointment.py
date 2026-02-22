from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


class AppointmentResponse(BaseModel):
    id: str
    contact_id: str
    slot_id: str
    status: str
    booked_at: str
    cancelled_at: Optional[str]
    rescheduled_from_id: Optional[str]

    model_config = ConfigDict(from_attributes=True)
