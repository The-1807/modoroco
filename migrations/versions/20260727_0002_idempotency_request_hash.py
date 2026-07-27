"""Bind idempotency records to the original request payload.

Revision ID: 20260727_0002
Revises: 20260719_0001
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision = "20260727_0002"
down_revision = "20260719_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    columns = {
        column["name"] for column in inspect(op.get_bind()).get_columns("idempotency_records")
    }
    if "request_hash" not in columns:
        with op.batch_alter_table("idempotency_records") as batch:
            batch.add_column(sa.Column("request_hash", sa.String(length=64), nullable=True))
        op.execute(
            "UPDATE idempotency_records SET request_hash = 'legacy-response-not-payload-bound'"
        )
        with op.batch_alter_table("idempotency_records") as batch:
            batch.alter_column("request_hash", nullable=False)


def downgrade() -> None:
    columns = {
        column["name"] for column in inspect(op.get_bind()).get_columns("idempotency_records")
    }
    if "request_hash" in columns:
        with op.batch_alter_table("idempotency_records") as batch:
            batch.drop_column("request_hash")
