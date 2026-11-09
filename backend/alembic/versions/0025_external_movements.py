"""Add the register of payments and refunds of external guests (MVP 25b).

Revision ID: 0025_external_movements
Revises: 0024_external_guests
"""

import sqlalchemy as sa
from alembic import op

from app.db import UtcDateTime

revision = "0025_external_movements"
down_revision = "0024_external_guests"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "external_movement",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("edition_id", sa.Integer(), nullable=False),
        sa.Column("guest_id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.Unicode(8), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("channel", sa.Unicode(32), nullable=False),
        sa.Column("paid_on", sa.Date(), nullable=False),
        sa.Column("note", sa.UnicodeText(), nullable=True),
        sa.Column("recorded_by_id", sa.Integer(), nullable=False),
        sa.Column("created_at", UtcDateTime(), nullable=False),
        sa.Column("voided_at", UtcDateTime(), nullable=True),
        sa.Column("voided_by_id", sa.Integer(), nullable=True),
        sa.Column("void_reason", sa.UnicodeText(), nullable=True),
        sa.Column("request_key", sa.Unicode(36), nullable=True),
        sa.CheckConstraint("amount_cents > 0", name="ck_external_movement_amount"),
        sa.ForeignKeyConstraint(["edition_id"], ["edition.id"]),
        sa.ForeignKeyConstraint(["guest_id"], ["external_guest.id"]),
        sa.ForeignKeyConstraint(["recorded_by_id"], ["participant.id"]),
        sa.ForeignKeyConstraint(["voided_by_id"], ["participant.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_external_movement_edition_id", "external_movement", ["edition_id"])
    op.create_index("ix_external_movement_guest_id", "external_movement", ["guest_id"])
    op.create_index(
        "uq_external_movement_request_key",
        "external_movement",
        ["request_key"],
        unique=True,
        mssql_where=sa.text("request_key IS NOT NULL"),
        sqlite_where=sa.text("request_key IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_external_movement_request_key", table_name="external_movement")
    op.drop_index("ix_external_movement_guest_id", table_name="external_movement")
    op.drop_index("ix_external_movement_edition_id", table_name="external_movement")
    op.drop_table("external_movement")
