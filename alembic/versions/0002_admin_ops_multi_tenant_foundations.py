"""add admin ops and multi-tenant foundations

Revision ID: 0002_admin_ops_multi_tenant_foundations
Revises: 0001_initial_schema
Create Date: 2026-02-22 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0002_admin_ops_multi_tenant_foundations"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("slug", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("idx_tenants_slug", "tenants", ["slug"], unique=False)
    op.execute(
        "INSERT INTO tenants (slug, name) VALUES ('default', 'Default Tenant') "
        "ON CONFLICT (slug) DO NOTHING"
    )

    for table in ("campaigns", "contacts", "messages", "availability_slots", "appointments"):
        op.add_column(table, sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True))
        op.create_foreign_key(
            f"fk_{table}_tenant_id_tenants",
            table,
            "tenants",
            ["tenant_id"],
            ["id"],
        )

    op.create_index("idx_campaigns_tenant", "campaigns", ["tenant_id"], unique=False)
    op.create_index("idx_contacts_tenant", "contacts", ["tenant_id"], unique=False)
    op.create_index("idx_messages_tenant", "messages", ["tenant_id"], unique=False)
    op.create_index("idx_availability_tenant", "availability_slots", ["tenant_id"], unique=False)
    op.create_index("idx_appointments_tenant", "appointments", ["tenant_id"], unique=False)

    op.create_table(
        "admin_users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("role", sa.String(length=50), server_default=sa.text("'super_admin'"), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("TRUE"), nullable=True),
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
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )
    op.create_index("idx_admin_users_tenant_role", "admin_users", ["tenant_id", "role"], unique=False)

    op.create_table(
        "audit_events",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("actor_username", sa.String(length=100), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column(
            "before_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=True,
        ),
        sa.Column(
            "after_json",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=True,
        ),
        sa.Column("request_id", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_audit_events_tenant_created",
        "audit_events",
        ["tenant_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "idx_audit_events_entity",
        "audit_events",
        ["entity_type", "entity_id", "created_at"],
        unique=False,
    )

    op.create_table(
        "waitlist_entries",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("contact_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=20), server_default=sa.text("'open'"), nullable=True),
        sa.Column("desired_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("desired_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(["contact_id"], ["contacts.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_waitlist_tenant_status", "waitlist_entries", ["tenant_id", "status"], unique=False
    )
    op.create_index(
        "idx_waitlist_contact", "waitlist_entries", ["contact_id", "created_at"], unique=False
    )

    op.create_table(
        "reminder_workflows",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("appointment_status", sa.String(length=20), nullable=True),
        sa.Column("minutes_before", sa.Integer(), nullable=False),
        sa.Column("channel", sa.String(length=20), server_default=sa.text("'sms'"), nullable=True),
        sa.Column("template", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("TRUE"), nullable=True),
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
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_reminder_workflows_tenant_active",
        "reminder_workflows",
        ["tenant_id", "is_active"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_reminder_workflows_tenant_active", table_name="reminder_workflows")
    op.drop_table("reminder_workflows")
    op.drop_index("idx_waitlist_contact", table_name="waitlist_entries")
    op.drop_index("idx_waitlist_tenant_status", table_name="waitlist_entries")
    op.drop_table("waitlist_entries")
    op.drop_index("idx_audit_events_entity", table_name="audit_events")
    op.drop_index("idx_audit_events_tenant_created", table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_index("idx_admin_users_tenant_role", table_name="admin_users")
    op.drop_table("admin_users")

    op.drop_index("idx_appointments_tenant", table_name="appointments")
    op.drop_constraint("fk_appointments_tenant_id_tenants", "appointments", type_="foreignkey")
    op.drop_column("appointments", "tenant_id")

    op.drop_index("idx_availability_tenant", table_name="availability_slots")
    op.drop_constraint("fk_availability_slots_tenant_id_tenants", "availability_slots", type_="foreignkey")
    op.drop_column("availability_slots", "tenant_id")

    op.drop_index("idx_messages_tenant", table_name="messages")
    op.drop_constraint("fk_messages_tenant_id_tenants", "messages", type_="foreignkey")
    op.drop_column("messages", "tenant_id")

    op.drop_index("idx_contacts_tenant", table_name="contacts")
    op.drop_constraint("fk_contacts_tenant_id_tenants", "contacts", type_="foreignkey")
    op.drop_column("contacts", "tenant_id")

    op.drop_index("idx_campaigns_tenant", table_name="campaigns")
    op.drop_constraint("fk_campaigns_tenant_id_tenants", "campaigns", type_="foreignkey")
    op.drop_column("campaigns", "tenant_id")

    op.drop_index("idx_tenants_slug", table_name="tenants")
    op.drop_table("tenants")
