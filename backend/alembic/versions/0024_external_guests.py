"""Add external guests: people without an account in meals and activities (MVP 25a).

Revision ID: 0024_external_guests
Revises: 0023_included_meal
"""

import sqlalchemy as sa
from alembic import op

from app.db import UtcDateTime

revision = "0024_external_guests"
down_revision = "0023_included_meal"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "external_guest",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("edition_id", sa.Integer(), nullable=False),
        sa.Column("first_name", sa.Unicode(100), nullable=False),
        sa.Column("last_name", sa.Unicode(100), nullable=False),
        sa.Column("phone", sa.Unicode(50), nullable=True),
        sa.Column("reference", sa.Unicode(200), nullable=True),
        sa.Column("internal_note", sa.UnicodeText(), nullable=True),
        sa.Column("payer", sa.Unicode(16), nullable=False, server_default="paying"),
        sa.Column("diet", sa.Unicode(16), nullable=True),
        sa.Column("allergies", sa.UnicodeText(), nullable=True),
        sa.Column("allergies_consent_at", UtcDateTime(), nullable=True),
        sa.Column("allergies_consent_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", UtcDateTime(), nullable=False),
        sa.Column("created_by_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["edition_id"], ["edition.id"]),
        sa.ForeignKeyConstraint(["allergies_consent_by_id"], ["participant.id"]),
        sa.ForeignKeyConstraint(["created_by_id"], ["participant.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_external_guest_edition_id", "external_guest", ["edition_id"])
    op.create_table(
        "external_guest_meal",
        sa.Column("guest_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("kind", sa.Unicode(8), nullable=False),
        sa.ForeignKeyConstraint(["guest_id"], ["external_guest.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("guest_id", "date", "kind"),
    )
    op.create_table(
        "external_guest_activity",
        sa.Column("guest_id", sa.Integer(), nullable=False),
        sa.Column("activity_id", sa.Integer(), nullable=False),
        sa.Column("joined_at", UtcDateTime(), nullable=False),
        sa.ForeignKeyConstraint(["guest_id"], ["external_guest.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["activity_id"], ["activity.id"]),
        sa.PrimaryKeyConstraint("guest_id", "activity_id"),
    )


def downgrade() -> None:
    op.drop_table("external_guest_activity")
    op.drop_table("external_guest_meal")
    op.drop_index("ix_external_guest_edition_id", table_name="external_guest")
    op.drop_table("external_guest")
