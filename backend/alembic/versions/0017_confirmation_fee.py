"""Prepare saved registration fees and confirmation notice cycles.

Revision ID: 0017
Revises: 0016
"""

import sqlalchemy as sa
from alembic import op

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("edition") as batch:
        batch.add_column(sa.Column("confirmation_policy", sa.Unicode(24), nullable=True))
        batch.add_column(sa.Column("confirmation_policy_activated_at", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("confirmation_policy_preview_token", sa.String(64), nullable=True))
    op.execute("UPDATE edition SET confirmation_policy = 'legacy_total'")
    with op.batch_alter_table("edition") as batch:
        batch.alter_column(
            "confirmation_policy", existing_type=sa.Unicode(24), nullable=False
        )

    with op.batch_alter_table("booking") as batch:
        batch.add_column(sa.Column("registration_fee_cents", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("confirmation_cycle", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("confirmation_claimed_cycle", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("confirmation_notice_due_at", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("confirmation_notice_payment_id", sa.Integer(), nullable=True))
    op.execute("UPDATE booking SET confirmation_cycle = 0, confirmation_claimed_cycle = 0")
    with op.batch_alter_table("booking") as batch:
        batch.alter_column("confirmation_cycle", existing_type=sa.Integer(), nullable=False)
        batch.alter_column("confirmation_claimed_cycle", existing_type=sa.Integer(), nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("booking") as batch:
        for column in (
            "confirmation_notice_payment_id",
            "confirmation_notice_due_at",
            "confirmation_claimed_cycle",
            "confirmation_cycle",
            "registration_fee_cents",
        ):
            batch.drop_column(column)
    with op.batch_alter_table("edition") as batch:
        for column in (
            "confirmation_policy_preview_token",
            "confirmation_policy_activated_at",
            "confirmation_policy",
        ):
            batch.drop_column(column)
