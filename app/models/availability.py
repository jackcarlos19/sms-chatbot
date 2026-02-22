from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Index, Integer, String, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class AvailabilitySlot(Base):
    __tablename__ = "availability_slots"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    provider_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True))
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    buffer_minutes: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    slot_type: Mapped[str] = mapped_column(
        String(50), server_default=text("'standard'")
    )
    is_available: Mapped[bool] = mapped_column(Boolean, server_default=text("TRUE"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    appointments = relationship("Appointment", back_populates="slot")

    __table_args__ = (
        Index(
            "idx_availability_available",
            "start_time",
            postgresql_where=text("is_available = TRUE"),
        ),
        Index(
            "idx_availability_provider",
            "provider_id",
            "start_time",
            postgresql_where=text("is_available = TRUE"),
        ),
    )
