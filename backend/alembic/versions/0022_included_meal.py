"""Add optional included meal policy.

Revision ID: 0022
Revises: 0021
"""

import sqlalchemy as sa
from alembic import op

revision = "0022"
down_revision = "0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "benefit",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("edition_id", sa.Integer(), nullable=False),
        sa.Column("name_it", sa.Unicode(200), nullable=False),
        sa.Column("name_en", sa.Unicode(200), nullable=False),
        sa.Column("retired", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["edition_id"], ["edition.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_benefit_edition_id", "benefit", ["edition_id"])
    with op.batch_alter_table("edition") as batch:
        batch.add_column(
            sa.Column("included_meal_policy", sa.Unicode(32), nullable=False, server_default="none")
        )
        batch.add_column(sa.Column("included_meal_preview_token", sa.String(64), nullable=True))
    with op.batch_alter_table("booking_meal") as batch:
        batch.add_column(
            sa.Column("included_in_fee", sa.Boolean(), nullable=False, server_default=sa.false())
        )


def downgrade() -> None:
    op.drop_index("ix_benefit_edition_id", table_name="benefit")
    op.drop_table("benefit")
    with op.batch_alter_table("booking_meal") as batch:
        batch.drop_column("included_in_fee")
    with op.batch_alter_table("edition") as batch:
        batch.drop_column("included_meal_preview_token")
        batch.drop_column("included_meal_policy")
