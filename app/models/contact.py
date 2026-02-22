from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, Index, String, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    phone_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    timezone: Mapped[str] = mapped_column(
        String(50), server_default=text("'America/New_York'")
    )
    opt_in_status: Mapped[str] = mapped_column(
        String(20), server_default=text("'opted_in'")
    )
    opt_in_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    opt_out_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        server_default=text("'{}'::jsonb"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    messages = relationship("Message", back_populates="contact")
    appointments = relationship("Appointment", back_populates="contact")
    conversation_state = relationship(
        "ConversationState", back_populates="contact", uselist=False
    )

    __table_args__ = (
        Index("idx_contacts_phone", "phone_number"),
        Index("idx_contacts_opt_in", "opt_in_status"),
    )
