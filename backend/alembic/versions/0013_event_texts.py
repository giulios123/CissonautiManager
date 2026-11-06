"""edition: editable paragraph above the sign-up form, one per language

Revision ID: 0013
Revises: 0012
Create Date: 2026-11-06
"""

import sqlalchemy as sa
from alembic import op

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Nullable, no default: empty means the standard text, as for the email templates.
    with op.batch_alter_table("edition") as batch:
        batch.add_column(sa.Column("registration_intro_it", sa.UnicodeText(), nullable=True))
        batch.add_column(sa.Column("registration_intro_en", sa.UnicodeText(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("edition") as batch:
        batch.drop_column("registration_intro_en")
        batch.drop_column("registration_intro_it")
