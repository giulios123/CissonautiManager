"""participant: remember the language (it or en) used for emails and messages

Revision ID: 0011
Revises: 0010
Create Date: 2026-11-05
"""

import sqlalchemy as sa
from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Everyone registered so far used the Italian-only app: they keep receiving Italian emails.
    with op.batch_alter_table("participant") as batch:
        batch.add_column(
            sa.Column("locale", sa.String(length=2), nullable=False, server_default="it")
        )


def downgrade() -> None:
    with op.batch_alter_table("participant") as batch:
        batch.drop_column("locale")
