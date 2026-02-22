from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


class ContactResponse(BaseModel):
    id: str
    phone_number: str
    first_name: Optional[str]
    last_name: Optional[str]
    timezone: str
    opt_in_status: str
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class ContactListResponse(BaseModel):
    contacts: list[ContactResponse]

    model_config = ConfigDict(from_attributes=True)
