"""edition: editable sign-up intro; email_text: editable parts of the emails

Revision ID: 0011
Revises: 0010
Create Date: 2026-11-06
"""

import sqlalchemy as sa
from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("edition") as batch:
        batch.add_column(sa.Column("registration_intro", sa.UnicodeText(), nullable=True))
    op.create_table(
        "email_text",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("edition_id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.Unicode(length=32), nullable=False),
        sa.Column("subject", sa.Unicode(length=200), nullable=True),
        sa.Column("intro", sa.UnicodeText(), nullable=True),
        sa.Column("closing", sa.UnicodeText(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("updated_by_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["edition_id"], ["edition.id"]),
        sa.ForeignKeyConstraint(["updated_by_id"], ["participant.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("edition_id", "kind"),
    )


def downgrade() -> None:
    op.drop_table("email_text")
    with op.batch_alter_table("edition") as batch:
        batch.drop_column("registration_intro")
