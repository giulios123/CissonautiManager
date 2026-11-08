"""Add reusable and per-edition participant profile fields.

Revision ID: 0018
Revises: 0017
"""

import sqlalchemy as sa
from alembic import op

revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("participant") as batch:
        batch.add_column(sa.Column("telegram", sa.Unicode(100), nullable=True))
        batch.add_column(sa.Column("linkedin", sa.Unicode(500), nullable=True))
    op.create_table(
        "participant_edition_profile",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("participant_id", sa.Integer(), sa.ForeignKey("participant.id"), nullable=False),
        sa.Column("edition_id", sa.Integer(), sa.ForeignKey("edition.id"), nullable=False),
        sa.Column("city", sa.Unicode(200), nullable=False),
        sa.Column("province", sa.Unicode(100), nullable=True),
        sa.Column("region", sa.Unicode(100), nullable=True),
        sa.Column("country", sa.Unicode(100), nullable=False),
        sa.Column("istat_code", sa.Unicode(12), nullable=True),
        sa.Column("job_title", sa.Unicode(200), nullable=False),
        sa.Column("company", sa.Unicode(200), nullable=False),
        sa.Column("expectations", sa.UnicodeText(), nullable=False),
        sa.Column("attended_previous", sa.Boolean(), nullable=False),
        sa.Column("attendance_source", sa.Unicode(16), nullable=False),
        sa.Column("previous_edition_id", sa.Integer(), sa.ForeignKey("edition.id"), nullable=True),
        sa.UniqueConstraint("participant_id", "edition_id", name="uq_participant_edition_profile"),
    )


def downgrade() -> None:
    op.drop_table("participant_edition_profile")
    with op.batch_alter_table("participant") as batch:
        batch.drop_column("linkedin")
        batch.drop_column("telegram")
