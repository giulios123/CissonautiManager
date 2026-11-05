"""plus one: an admin can verify who invited a participant

Revision ID: 0008
Revises: 0007
Create Date: 2026-11-05
"""

import sqlalchemy as sa
from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("participant") as batch:
        batch.add_column(sa.Column("plus_one_verified_at", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("plus_one_verified_by_id", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "fk_participant_plus_one_verified_by_id_participant",
            "participant",
            ["plus_one_verified_by_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("participant") as batch:
        batch.drop_constraint(
            "fk_participant_plus_one_verified_by_id_participant", type_="foreignkey"
        )
        batch.drop_column("plus_one_verified_by_id")
        batch.drop_column("plus_one_verified_at")
