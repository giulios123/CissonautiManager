"""Structured activity times and payments collected directly by providers.

Revision ID: 0015
Revises: 0014
"""

import sqlalchemy as sa
from alembic import op

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("activity") as batch:
        batch.add_column(sa.Column("starts_at", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("ends_at", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("payment_mode", sa.Unicode(16), nullable=True))
        batch.add_column(sa.Column("payment_instructions", sa.UnicodeText(), nullable=True))
    op.execute("UPDATE activity SET payment_mode = 'organizer'")
    with op.batch_alter_table("activity") as batch:
        batch.alter_column("payment_mode", existing_type=sa.Unicode(16), nullable=False)
    op.create_table(
        "meal_setting",
        sa.Column("edition_id", sa.Integer(), sa.ForeignKey("edition.id"), primary_key=True),
        sa.Column("date", sa.Date(), primary_key=True),
        sa.Column("kind", sa.Unicode(8), primary_key=True),
        sa.Column("payment_mode", sa.Unicode(16), nullable=False),
        sa.Column("price_cents", sa.Integer(), nullable=True),
        sa.Column("payment_instructions", sa.UnicodeText(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("meal_setting")
    with op.batch_alter_table("activity") as batch:
        for column in ("payment_instructions", "payment_mode", "ends_at", "starts_at"):
            batch.drop_column(column)
