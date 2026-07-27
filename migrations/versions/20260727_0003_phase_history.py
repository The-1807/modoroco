"""Persist completed and skipped session phases.

Revision ID: 20260727_0003
Revises: 20260727_0002
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision = "20260727_0003"
down_revision = "20260727_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    inspector = inspect(op.get_bind())
    if "session_phase_history" in inspector.get_table_names():
        return
    op.create_table(
        "session_phase_history",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("phase_key", sa.String(length=60), nullable=False),
        sa.Column("phase_index", sa.Integer(), nullable=False),
        sa.Column("outcome", sa.String(length=24), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("session_version", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["timer_sessions.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "session_id",
            "session_version",
            name="uq_session_phase_history_version",
        ),
    )
    op.create_index(
        op.f("ix_session_phase_history_session_id"),
        "session_phase_history",
        ["session_id"],
    )
    op.create_index(
        op.f("ix_session_phase_history_tenant_id"),
        "session_phase_history",
        ["tenant_id"],
    )


def downgrade() -> None:
    if "session_phase_history" not in inspect(op.get_bind()).get_table_names():
        return
    op.drop_index(
        op.f("ix_session_phase_history_tenant_id"),
        table_name="session_phase_history",
    )
    op.drop_index(
        op.f("ix_session_phase_history_session_id"),
        table_name="session_phase_history",
    )
    op.drop_table("session_phase_history")
