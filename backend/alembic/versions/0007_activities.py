"""activities, sign-ups to activities and contributions

Revision ID: 0007
Revises: 0006
Create Date: 2026-11-05
"""

import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "activity",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("edition_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.Unicode(length=200), nullable=False),
        sa.Column("description", sa.UnicodeText(), nullable=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("period", sa.Unicode(length=12), nullable=False),
        sa.Column("time_label", sa.Unicode(length=50), nullable=True),
        sa.Column("price_cents", sa.Integer(), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["edition_id"], ["edition.id"], name="fk_activity_edition_id_edition"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_activity"),
    )
    op.create_table(
        "booking_activity",
        sa.Column("booking_id", sa.Integer(), nullable=False),
        sa.Column("activity_id", sa.Integer(), nullable=False),
        sa.Column("joined_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["booking_id"], ["booking.id"], name="fk_booking_activity_booking_id_booking"
        ),
        sa.ForeignKeyConstraint(
            ["activity_id"], ["activity.id"], name="fk_booking_activity_activity_id_activity"
        ),
        sa.PrimaryKeyConstraint("booking_id", "activity_id", name="pk_booking_activity"),
    )
    op.create_table(
        "contribution",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("booking_id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.Unicode(length=16), nullable=False),
        sa.Column("title", sa.Unicode(length=200), nullable=False),
        sa.Column("description", sa.UnicodeText(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["booking_id"], ["booking.id"], name="fk_contribution_booking_id_booking"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_contribution"),
    )


def downgrade() -> None:
    op.drop_table("contribution")
    op.drop_table("booking_activity")
    op.drop_table("activity")
