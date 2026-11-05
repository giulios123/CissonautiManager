"""admin panel: refund details, voided payments and the audit log

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-05
"""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("booking") as batch:
        batch.add_column(sa.Column("refund_cents", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("refunded_at", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("refund_note", sa.UnicodeText(), nullable=True))
        batch.add_column(sa.Column("refunded_by_id", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "fk_booking_refunded_by_id_participant", "participant", ["refunded_by_id"], ["id"]
        )
    with op.batch_alter_table("payment") as batch:
        batch.add_column(sa.Column("voided_at", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("voided_by_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("void_reason", sa.UnicodeText(), nullable=True))
        batch.create_foreign_key(
            "fk_payment_voided_by_id_participant", "participant", ["voided_by_id"], ["id"]
        )
    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("at", sa.DateTime(), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=False),
        sa.Column("booking_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.Unicode(length=40), nullable=False),
        sa.Column("detail", sa.UnicodeText(), nullable=False),
        sa.ForeignKeyConstraint(
            ["actor_id"], ["participant.id"], name="fk_audit_log_actor_id_participant"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_audit_log"),
    )


def downgrade() -> None:
    op.drop_table("audit_log")
    with op.batch_alter_table("payment") as batch:
        batch.drop_constraint("fk_payment_voided_by_id_participant", type_="foreignkey")
        batch.drop_column("void_reason")
        batch.drop_column("voided_by_id")
        batch.drop_column("voided_at")
    with op.batch_alter_table("booking") as batch:
        batch.drop_constraint("fk_booking_refunded_by_id_participant", type_="foreignkey")
        batch.drop_column("refunded_by_id")
        batch.drop_column("refund_note")
        batch.drop_column("refunded_at")
        batch.drop_column("refund_cents")
