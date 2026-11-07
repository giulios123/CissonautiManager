"""Store bilingual legal bodies and optional consent events.

Revision ID: 0016
Revises: 0015
"""

import sqlalchemy as sa
from alembic import op

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("legal_document") as batch:
        batch.add_column(sa.Column("body_it", sa.UnicodeText(), nullable=True))
        batch.add_column(sa.Column("body_en", sa.UnicodeText(), nullable=True))

    op.create_table(
        "consent_event",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("edition_id", sa.Integer(), sa.ForeignKey("edition.id"), nullable=False),
        sa.Column("participant_id", sa.Integer(), sa.ForeignKey("participant.id"), nullable=False),
        sa.Column("kind", sa.Unicode(16), nullable=False),
        sa.Column("action", sa.Unicode(12), nullable=False),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("legal_document.id"), nullable=False),
        sa.Column("locale", sa.String(2), nullable=False),
        sa.Column("recorded_at", sa.DateTime(), nullable=False),
        sa.Column("source", sa.Unicode(20), nullable=False),
    )
    op.create_index(
        "ix_consent_event_edition_participant_kind_id",
        "consent_event",
        ["edition_id", "participant_id", "kind", "id"],
    )


def downgrade() -> None:
    op.drop_index("ix_consent_event_edition_participant_kind_id", table_name="consent_event")
    op.drop_table("consent_event")
    with op.batch_alter_table("legal_document") as batch:
        batch.drop_column("body_en")
        batch.drop_column("body_it")
