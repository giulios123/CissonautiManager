"""personal page: hold start, payment reminders and cancellation request time

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-05
"""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # hold_started_at is added nullable, filled, then made NOT NULL: this avoids leaving a
    # default constraint behind (which would block dropping the column on SQL Server).
    with op.batch_alter_table("booking") as batch:
        batch.add_column(sa.Column("hold_started_at", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("reminder_mid_sent_at", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("reminder_final_sent_at", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("cancel_requested_at", sa.DateTime(), nullable=True))
    op.execute("UPDATE booking SET hold_started_at = created_at")
    with op.batch_alter_table("booking") as batch:
        batch.alter_column("hold_started_at", existing_type=sa.DateTime(), nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("booking") as batch:
        batch.drop_column("cancel_requested_at")
        batch.drop_column("reminder_final_sent_at")
        batch.drop_column("reminder_mid_sent_at")
        batch.drop_column("hold_started_at")
