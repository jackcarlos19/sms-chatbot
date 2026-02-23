from __future__ import annotations

import uuid
from datetime import datetime, time
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, Time, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    tenant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id")
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    message_template: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), server_default=text("'draft'"))
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    quiet_hours_start: Mapped[time] = mapped_column(
        Time, server_default=text("'21:00'::time")
    )
    quiet_hours_end: Mapped[time] = mapped_column(
        Time, server_default=text("'09:00'::time")
    )
    respect_timezone: Mapped[bool] = mapped_column(server_default=text("TRUE"))
    total_recipients: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    sent_count: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    delivered_count: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    failed_count: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    reply_count: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    messages = relationship("Message", back_populates="campaign")
    recipients = relationship("CampaignRecipient", back_populates="campaign")

    __table_args__ = (Index("idx_campaigns_tenant", "tenant_id"),)
