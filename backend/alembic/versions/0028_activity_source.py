"""Link an activity to the proposal it was created from (MVP 29).

Revision ID: 0028_activity_source
Revises: 0027_contribution_hidden
"""

import sqlalchemy as sa
from alembic import op

revision = "0028_activity_source"
down_revision = "0027_contribution_hidden"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("activity") as batch:
        batch.add_column(sa.Column("source_contribution_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("source_title", sa.Unicode(200), nullable=True))
        batch.add_column(sa.Column("request_key", sa.Unicode(36), nullable=True))
        batch.create_foreign_key(
            "fk_activity_source_contribution",
            "contribution",
            ["source_contribution_id"],
            ["id"],
        )
    op.create_index(
        "uq_activity_request_key",
        "activity",
        ["request_key"],
        unique=True,
        mssql_where=sa.text("request_key IS NOT NULL"),
        sqlite_where=sa.text("request_key IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_activity_request_key", table_name="activity")
    with op.batch_alter_table("activity") as batch:
        batch.drop_constraint("fk_activity_source_contribution", type_="foreignkey")
        batch.drop_column("request_key")
        batch.drop_column("source_title")
        batch.drop_column("source_contribution_id")
