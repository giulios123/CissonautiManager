"""evening slot: edition evening hours and unlimited slot capacity

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-04
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Added nullable, filled for existing rows, then made NOT NULL: this avoids leaving
    # a default constraint behind (which would block dropping the column on SQL Server).
    with op.batch_alter_table("edition") as batch:
        batch.add_column(sa.Column("evening_start", sa.Time(), nullable=True))
        batch.add_column(sa.Column("evening_end", sa.Time(), nullable=True))
    op.execute("UPDATE edition SET evening_start = '19:00:00', evening_end = '00:00:00'")
    with op.batch_alter_table("edition") as batch:
        batch.alter_column("evening_start", existing_type=sa.Time(), nullable=False)
        batch.alter_column("evening_end", existing_type=sa.Time(), nullable=False)
    with op.batch_alter_table("slot") as batch:
        batch.alter_column("capacity", existing_type=sa.Integer(), nullable=True)


def downgrade() -> None:
    # Data loss on purpose: evening slots (and bookings on them) cannot exist in the old schema.
    op.execute(
        "DELETE FROM booking_slot WHERE slot_id IN (SELECT id FROM slot WHERE period = 'evening')"
    )
    op.execute("DELETE FROM slot WHERE period = 'evening'")
    with op.batch_alter_table("slot") as batch:
        batch.alter_column("capacity", existing_type=sa.Integer(), nullable=False)
    with op.batch_alter_table("edition") as batch:
        batch.drop_column("evening_end")
        batch.drop_column("evening_start")
