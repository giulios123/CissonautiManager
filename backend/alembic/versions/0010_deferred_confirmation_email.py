"""payment: remember when a deferred confirmation email is due and when it was sent

Revision ID: 0010
Revises: 0009
Create Date: 2026-11-05
"""

import sqlalchemy as sa
from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Nullable on purpose: every existing payment sent (or did not need) its email at the time.
    with op.batch_alter_table("payment") as batch:
        batch.add_column(
            sa.Column("confirmation_email_due_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch.add_column(
            sa.Column("confirmation_email_sent_at", sa.DateTime(timezone=True), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table("payment") as batch:
        batch.drop_column("confirmation_email_sent_at")
        batch.drop_column("confirmation_email_due_at")
