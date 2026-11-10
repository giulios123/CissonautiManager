"""Let an admin hide a contribution from the other participants (MVP 27).

Revision ID: 0027_contribution_hidden
Revises: 0026_exemptions_refunds
"""

import sqlalchemy as sa
from alembic import op

from app.db import UtcDateTime

revision = "0027_contribution_hidden"
down_revision = "0026_exemptions_refunds"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("contribution") as batch:
        batch.add_column(sa.Column("hidden_at", UtcDateTime(), nullable=True))
        batch.add_column(sa.Column("hidden_by_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("hidden_reason", sa.Unicode(200), nullable=True))
        batch.create_foreign_key(
            "fk_contribution_hidden_by", "participant", ["hidden_by_id"], ["id"]
        )


def downgrade() -> None:
    with op.batch_alter_table("contribution") as batch:
        batch.drop_constraint("fk_contribution_hidden_by", type_="foreignkey")
        batch.drop_column("hidden_reason")
        batch.drop_column("hidden_by_id")
        batch.drop_column("hidden_at")
