"""Add bilingual activity content and private note history.

Revision ID: 0022_activity_details
Revises: 0021
"""

import sqlalchemy as sa
from alembic import op

from app.db import UtcDateTime

revision = "0022_activity_details"
down_revision = "0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("activity") as batch:
        batch.add_column(sa.Column("title_it", sa.Unicode(200), nullable=True))
        batch.add_column(sa.Column("title_en", sa.Unicode(200), nullable=True))
        batch.add_column(sa.Column("description_it", sa.UnicodeText(), nullable=True))
        batch.add_column(sa.Column("description_en", sa.UnicodeText(), nullable=True))
        batch.add_column(sa.Column("internal_note", sa.UnicodeText(), nullable=True))
    op.execute("UPDATE activity SET title_it = title, title_en = title")
    op.execute("UPDATE activity SET description_it = description, description_en = description")
    op.create_table(
        "activity_note_revision",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("activity_id", sa.Integer(), nullable=False),
        sa.Column("actor_id", sa.Integer(), nullable=False),
        sa.Column("note", sa.UnicodeText(), nullable=True),
        sa.Column("created_at", UtcDateTime(), nullable=False),
        sa.ForeignKeyConstraint(["activity_id"], ["activity.id"]),
        sa.ForeignKeyConstraint(["actor_id"], ["participant.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_activity_note_revision_activity_id",
        "activity_note_revision",
        ["activity_id", "id"],
    )


def downgrade() -> None:
    op.drop_index("ix_activity_note_revision_activity_id", table_name="activity_note_revision")
    op.drop_table("activity_note_revision")
    with op.batch_alter_table("activity") as batch:
        batch.drop_column("internal_note")
        batch.drop_column("description_en")
        batch.drop_column("description_it")
        batch.drop_column("title_en")
        batch.drop_column("title_it")
