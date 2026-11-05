"""waitlist: entries per full slot and the waitlist size setting

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-05
"""

import sqlalchemy as sa
from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Added nullable, filled, then made NOT NULL, as in 0002: no default constraint is left behind.
    with op.batch_alter_table("edition") as batch:
        batch.add_column(sa.Column("waitlist_percent", sa.Integer(), nullable=True))
    op.execute("UPDATE edition SET waitlist_percent = 20")
    with op.batch_alter_table("edition") as batch:
        batch.alter_column("waitlist_percent", existing_type=sa.Integer(), nullable=False)
    op.create_table(
        "waitlist_entry",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("slot_id", sa.Integer(), nullable=False),
        sa.Column("participant_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("closed_at", sa.DateTime(), nullable=True),
        sa.Column("close_reason", sa.Unicode(length=16), nullable=True),
        sa.Column("promoted_booking_id", sa.Integer(), nullable=True),
        sa.Column("privacy_document_id", sa.Integer(), nullable=False),
        sa.Column("privacy_accepted_at", sa.DateTime(), nullable=False),
        sa.Column("disclaimer_document_id", sa.Integer(), nullable=False),
        sa.Column("disclaimer_accepted_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["slot_id"], ["slot.id"], name="fk_waitlist_entry_slot_id_slot"),
        sa.ForeignKeyConstraint(
            ["participant_id"],
            ["participant.id"],
            name="fk_waitlist_entry_participant_id_participant",
        ),
        sa.ForeignKeyConstraint(
            ["privacy_document_id"],
            ["legal_document.id"],
            name="fk_waitlist_entry_privacy_document_id_legal_document",
        ),
        sa.ForeignKeyConstraint(
            ["disclaimer_document_id"],
            ["legal_document.id"],
            name="fk_waitlist_entry_disclaimer_document_id_legal_document",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_waitlist_entry"),
    )


def downgrade() -> None:
    op.drop_table("waitlist_entry")
    with op.batch_alter_table("edition") as batch:
        batch.drop_column("waitlist_percent")
