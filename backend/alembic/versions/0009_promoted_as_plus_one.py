"""waitlist: remember whether a promoted person was a verified plus one

Revision ID: 0009
Revises: 0008
Create Date: 2026-11-05
"""

import sqlalchemy as sa
from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Added nullable, filled, then made NOT NULL, as in 0006: no default constraint is left behind.
    # Every promotion so far happened before plus ones could be verified, so false is the truth.
    with op.batch_alter_table("waitlist_entry") as batch:
        batch.add_column(sa.Column("promoted_as_plus_one", sa.Boolean(), nullable=True))
    op.execute("UPDATE waitlist_entry SET promoted_as_plus_one = 0")
    with op.batch_alter_table("waitlist_entry") as batch:
        batch.alter_column("promoted_as_plus_one", existing_type=sa.Boolean(), nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("waitlist_entry") as batch:
        batch.drop_column("promoted_as_plus_one")
