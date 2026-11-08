"""Keep cancellation history after a booking is removed.

Revision ID: 0020
Revises: 0019
"""

import sqlalchemy as sa
from alembic import op

revision = "0020"
down_revision = "0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("audit_log") as batch:
        batch.alter_column("actor_id", existing_type=sa.Integer(), nullable=True)
        batch.add_column(sa.Column("participant_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("edition_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("outcome", sa.Unicode(24), nullable=True))
        batch.create_foreign_key(
            "fk_audit_log_participant_id_participant",
            "participant",
            ["participant_id"],
            ["id"],
        )
        batch.create_foreign_key(
            "fk_audit_log_edition_id_edition", "edition", ["edition_id"], ["id"]
        )

    op.create_index(
        "ix_audit_log_edition_cancellation",
        "audit_log",
        ["edition_id", "at", "id"],
    )


def downgrade() -> None:
    op.drop_index("ix_audit_log_edition_cancellation", table_name="audit_log")
    # Older audit rows require an actor. Participant-authored cancellation events already have
    # the participant id, so preserve their self-attribution before dropping the new column.
    op.execute(
        sa.text(
            "UPDATE audit_log SET actor_id = participant_id "
            "WHERE actor_id IS NULL AND participant_id IS NOT NULL"
        )
    )
    with op.batch_alter_table("audit_log") as batch:
        batch.drop_constraint("fk_audit_log_edition_id_edition", type_="foreignkey")
        batch.drop_constraint("fk_audit_log_participant_id_participant", type_="foreignkey")
        batch.drop_column("outcome")
        batch.drop_column("edition_id")
        batch.drop_column("participant_id")
        batch.alter_column("actor_id", existing_type=sa.Integer(), nullable=False)
