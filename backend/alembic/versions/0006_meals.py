"""meals: lunch and dinner sign-ups, meal prices and dietary needs

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-05
"""

import sqlalchemy as sa
from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Added nullable, filled, then made NOT NULL, as in 0002: no default constraint is left behind.
    with op.batch_alter_table("edition") as batch:
        batch.add_column(sa.Column("lunch_price_cents", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("dinner_price_cents", sa.Integer(), nullable=True))
    op.execute("UPDATE edition SET lunch_price_cents = 800, dinner_price_cents = 1200")
    with op.batch_alter_table("edition") as batch:
        batch.alter_column("lunch_price_cents", existing_type=sa.Integer(), nullable=False)
        batch.alter_column("dinner_price_cents", existing_type=sa.Integer(), nullable=False)
    with op.batch_alter_table("booking") as batch:
        batch.add_column(sa.Column("diet", sa.Unicode(length=16), nullable=True))
        batch.add_column(sa.Column("allergies", sa.UnicodeText(), nullable=True))
        batch.add_column(sa.Column("health_consent_document_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("health_consent_at", sa.DateTime(), nullable=True))
        batch.create_foreign_key(
            "fk_booking_health_consent_document_id_legal_document",
            "legal_document",
            ["health_consent_document_id"],
            ["id"],
        )
    op.create_table(
        "booking_meal",
        sa.Column("booking_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("kind", sa.Unicode(length=8), nullable=False),
        sa.ForeignKeyConstraint(
            ["booking_id"], ["booking.id"], name="fk_booking_meal_booking_id_booking"
        ),
        sa.PrimaryKeyConstraint("booking_id", "date", "kind", name="pk_booking_meal"),
    )


def downgrade() -> None:
    op.drop_table("booking_meal")
    with op.batch_alter_table("booking") as batch:
        batch.drop_constraint(
            "fk_booking_health_consent_document_id_legal_document", type_="foreignkey"
        )
        batch.drop_column("health_consent_at")
        batch.drop_column("health_consent_document_id")
        batch.drop_column("allergies")
        batch.drop_column("diet")
    with op.batch_alter_table("edition") as batch:
        batch.drop_column("dinner_price_cents")
        batch.drop_column("lunch_price_cents")
