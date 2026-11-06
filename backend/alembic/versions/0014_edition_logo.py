"""Store the edition logo as an optional PNG.

Revision ID: 0014
Revises: 0013
Create Date: 2026-11-06
"""

import sqlalchemy as sa
from alembic import op

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("edition") as batch:
        batch.add_column(sa.Column("logo_image", sa.LargeBinary(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("edition") as batch:
        batch.drop_column("logo_image")
