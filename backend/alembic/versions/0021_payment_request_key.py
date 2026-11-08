"""Add idempotency keys for quick payment entry.

Revision ID: 0021
Revises: 0020
"""

import sqlalchemy as sa
from alembic import op

revision = "0021"
down_revision = "0020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("payment") as batch:
        batch.add_column(sa.Column("request_key", sa.Unicode(36), nullable=True))
    op.create_index(
        "uq_payment_request_key",
        "payment",
        ["request_key"],
        unique=True,
        mssql_where=sa.text("request_key IS NOT NULL"),
        sqlite_where=sa.text("request_key IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_payment_request_key", table_name="payment")
    with op.batch_alter_table("payment") as batch:
        batch.drop_column("request_key")
