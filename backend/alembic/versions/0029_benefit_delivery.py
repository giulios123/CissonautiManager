"""Add the deliveries of the benefits of the edition (MVP 30).

Revision ID: 0029_benefit_delivery
Revises: 0028_activity_source
"""

import sqlalchemy as sa
from alembic import op

from app.db import UtcDateTime

revision = "0029_benefit_delivery"
down_revision = "0028_activity_source"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "benefit_delivery",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("edition_id", sa.Integer(), nullable=False),
        sa.Column("participant_id", sa.Integer(), nullable=False),
        sa.Column("benefit_id", sa.Integer(), nullable=False),
        sa.Column("delivered_at", UtcDateTime(), nullable=False),
        sa.Column("delivered_by_id", sa.Integer(), nullable=False),
        sa.Column("annulled_at", UtcDateTime(), nullable=True),
        sa.Column("annulled_by_id", sa.Integer(), nullable=True),
        sa.Column("annul_reason", sa.Unicode(200), nullable=True),
        sa.Column("request_key", sa.Unicode(36), nullable=True),
        sa.ForeignKeyConstraint(["edition_id"], ["edition.id"]),
        sa.ForeignKeyConstraint(["participant_id"], ["participant.id"]),
        sa.ForeignKeyConstraint(["benefit_id"], ["benefit.id"]),
        sa.ForeignKeyConstraint(["delivered_by_id"], ["participant.id"]),
        sa.ForeignKeyConstraint(["annulled_by_id"], ["participant.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_benefit_delivery_edition_id", "benefit_delivery", ["edition_id"])
    op.create_index("ix_benefit_delivery_participant_id", "benefit_delivery", ["participant_id"])
    op.create_index("ix_benefit_delivery_benefit_id", "benefit_delivery", ["benefit_id"])
    op.create_index(
        "uq_benefit_delivery_active",
        "benefit_delivery",
        ["participant_id", "benefit_id"],
        unique=True,
        mssql_where=sa.text("annulled_at IS NULL"),
        sqlite_where=sa.text("annulled_at IS NULL"),
    )
    op.create_index(
        "uq_benefit_delivery_request_key",
        "benefit_delivery",
        ["request_key"],
        unique=True,
        mssql_where=sa.text("request_key IS NOT NULL"),
        sqlite_where=sa.text("request_key IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_benefit_delivery_request_key", table_name="benefit_delivery")
    op.drop_index("uq_benefit_delivery_active", table_name="benefit_delivery")
    op.drop_index("ix_benefit_delivery_benefit_id", table_name="benefit_delivery")
    op.drop_index("ix_benefit_delivery_participant_id", table_name="benefit_delivery")
    op.drop_index("ix_benefit_delivery_edition_id", table_name="benefit_delivery")
    op.drop_table("benefit_delivery")
