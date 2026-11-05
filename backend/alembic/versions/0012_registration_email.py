"""editable registration email: texts per language and the picture with the name

Revision ID: 0012
Revises: 0011
Create Date: 2026-11-05
"""

import sqlalchemy as sa
from alembic import op

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "email_template",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("edition_id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.Unicode(length=32), nullable=False),
        sa.Column("locale", sa.String(length=2), nullable=False),
        sa.Column("subject", sa.Unicode(length=200), nullable=False),
        sa.Column("body", sa.UnicodeText(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("updated_by_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["edition_id"], ["edition.id"], name="fk_email_template_edition_id_edition"
        ),
        sa.ForeignKeyConstraint(
            ["updated_by_id"],
            ["participant.id"],
            name="fk_email_template_updated_by_id_participant",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_email_template"),
        sa.UniqueConstraint(
            "edition_id", "kind", "locale", name=op.f("uq_email_template_edition_id")
        ),
    )
    op.create_table(
        "registration_card",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("edition_id", sa.Integer(), nullable=False),
        sa.Column("image", sa.LargeBinary(), nullable=True),
        sa.Column("text_it", sa.UnicodeText(), nullable=False),
        sa.Column("text_en", sa.UnicodeText(), nullable=False),
        sa.Column("text_color", sa.String(length=7), nullable=False),
        sa.Column("text_position", sa.String(length=8), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["edition_id"], ["edition.id"], name="fk_registration_card_edition_id_edition"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_registration_card"),
        sa.UniqueConstraint("edition_id", name=op.f("uq_registration_card_edition_id")),
    )


def downgrade() -> None:
    op.drop_table("registration_card")
    op.drop_table("email_template")
