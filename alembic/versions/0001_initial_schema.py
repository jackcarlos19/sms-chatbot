"""create initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-02-21 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    op.create_table(
        "campaigns",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("message_template", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default=sa.text("'draft'"),
            nullable=True,
        ),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "quiet_hours_start",
            sa.Time(),
            server_default=sa.text("'21:00'::time"),
            nullable=True,
        ),
        sa.Column(
            "quiet_hours_end",
            sa.Time(),
            server_default=sa.text("'09:00'::time"),
            nullable=True,
        ),
        sa.Column(
            "respect_timezone",
            sa.Boolean(),
            server_default=sa.text("TRUE"),
            nullable=True,
        ),
        sa.Column(
            "total_recipients", sa.Integer(), server_default=sa.text("0"), nullable=True
        ),
        sa.Column(
            "sent_count", sa.Integer(), server_default=sa.text("0"), nullable=True
        ),
        sa.Column(
            "delivered_count", sa.Integer(), server_default=sa.text("0"), nullable=True
        ),
        sa.Column(
            "failed_count", sa.Integer(), server_default=sa.text("0"), nullable=True
        ),
        sa.Column(
            "reply_count", sa.Integer(), server_default=sa.text("0"), nullable=True
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "contacts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("phone_number", sa.String(length=20), nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=True),
        sa.Column("last_name", sa.String(length=100), nullable=True),
        sa.Column(
            "timezone",
            sa.String(length=50),
            server_default=sa.text("'America/New_York'"),
            nullable=True,
        ),
        sa.Column(
            "opt_in_status",
            sa.String(length=20),
            server_default=sa.text("'opted_in'"),
            nullable=True,
        ),
        sa.Column("opt_in_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("opt_out_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("phone_number"),
    )
    op.create_index("idx_contacts_phone", "contacts", ["phone_number"], unique=False)
    op.create_index("idx_contacts_opt_in", "contacts", ["opt_in_status"], unique=False)

    op.create_table(
        "messages",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("contact_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("direction", sa.String(length=10), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("sms_sid", sa.String(length=64), nullable=True),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default=sa.text("'queued'"),
            nullable=True,
        ),
        sa.Column("error_code", sa.String(length=10), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"]),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("sms_sid"),
    )
    op.create_index("idx_messages_campaign", "messages", ["campaign_id"], unique=False)
    op.create_index(
        "idx_messages_contact",
        "messages",
        ["contact_id", sa.text("created_at DESC")],
        unique=False,
    )
    op.create_index("idx_messages_sms_sid", "messages", ["sms_sid"], unique=False)

    op.create_table(
        "availability_slots",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("provider_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "buffer_minutes", sa.Integer(), server_default=sa.text("0"), nullable=True
        ),
        sa.Column(
            "slot_type",
            sa.String(length=50),
            server_default=sa.text("'standard'"),
            nullable=True,
        ),
        sa.Column(
            "is_available", sa.Boolean(), server_default=sa.text("TRUE"), nullable=True
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_availability_available",
        "availability_slots",
        ["start_time"],
        unique=False,
        postgresql_where=sa.text("is_available = TRUE"),
    )
    op.create_index(
        "idx_availability_provider",
        "availability_slots",
        ["provider_id", "start_time"],
        unique=False,
        postgresql_where=sa.text("is_available = TRUE"),
    )

    op.create_table(
        "appointments",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("contact_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("slot_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default=sa.text("'confirmed'"),
            nullable=True,
        ),
        sa.Column(
            "booked_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancellation_reason", sa.Text(), nullable=True),
        sa.Column("rescheduled_from_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"]),
        sa.ForeignKeyConstraint(["rescheduled_from_id"], ["appointments.id"]),
        sa.ForeignKeyConstraint(["slot_id"], ["availability_slots.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_appointments_active_slot",
        "appointments",
        ["slot_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('confirmed', 'rescheduled')"),
    )
    op.create_index(
        "idx_appointments_contact",
        "appointments",
        ["contact_id", "status"],
        unique=False,
    )

    op.create_table(
        "campaign_recipients",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("contact_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            server_default=sa.text("'pending'"),
            nullable=True,
        ),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"]),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "campaign_id", "contact_id", name="unique_campaign_contact"
        ),
    )

    op.create_table(
        "conversation_states",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("contact_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "current_state",
            sa.String(length=50),
            server_default=sa.text("'idle'"),
            nullable=True,
        ),
        sa.Column(
            "context",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("contact_id"),
    )
    op.create_index(
        "idx_conversation_expires",
        "conversation_states",
        ["expires_at"],
        unique=False,
        postgresql_where=sa.text("current_state != 'idle'"),
    )


def downgrade() -> None:
    op.drop_index("idx_conversation_expires", table_name="conversation_states")
    op.drop_table("conversation_states")
    op.drop_table("campaign_recipients")
    op.drop_index("idx_appointments_contact", table_name="appointments")
    op.drop_index("idx_appointments_active_slot", table_name="appointments")
    op.drop_table("appointments")
    op.drop_index("idx_availability_provider", table_name="availability_slots")
    op.drop_index("idx_availability_available", table_name="availability_slots")
    op.drop_table("availability_slots")
    op.drop_index("idx_messages_sms_sid", table_name="messages")
    op.drop_index("idx_messages_contact", table_name="messages")
    op.drop_index("idx_messages_campaign", table_name="messages")
    op.drop_table("messages")
    op.drop_index("idx_contacts_opt_in", table_name="contacts")
    op.drop_index("idx_contacts_phone", table_name="contacts")
    op.drop_table("contacts")
    op.drop_table("campaigns")
