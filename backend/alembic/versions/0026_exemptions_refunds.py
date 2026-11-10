"""Add booking category, exemptions and refunds on active bookings (MVP 25c).

Revision ID: 0026_exemptions_refunds
Revises: 0025_external_movements
"""

import sqlalchemy as sa
from alembic import op

from app.db import UtcDateTime

revision = "0026_exemptions_refunds"
down_revision = "0025_external_movements"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("booking") as batch:
        batch.add_column(
            sa.Column("category", sa.Unicode(24), nullable=False, server_default="ordinary")
        )
        batch.add_column(
            sa.Column("fee_exempt", sa.Boolean(), nullable=False, server_default=sa.false())
        )
        batch.add_column(sa.Column("exemption_preview_token", sa.String(64), nullable=True))
    with op.batch_alter_table("booking_meal") as batch:
        batch.add_column(
            sa.Column("exempt", sa.Boolean(), nullable=False, server_default=sa.false())
        )
    with op.batch_alter_table("booking_activity") as batch:
        batch.add_column(
            sa.Column("exempt", sa.Boolean(), nullable=False, server_default=sa.false())
        )
    op.create_table(
        "booking_refund",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("booking_id", sa.Integer(), nullable=False),
        sa.Column("amount_cents", sa.Integer(), nullable=False),
        sa.Column("channel", sa.Unicode(32), nullable=False),
        sa.Column("refunded_on", sa.Date(), nullable=False),
        sa.Column("note", sa.UnicodeText(), nullable=True),
        sa.Column("recorded_by_id", sa.Integer(), nullable=False),
        sa.Column("created_at", UtcDateTime(), nullable=False),
        sa.Column("voided_at", UtcDateTime(), nullable=True),
        sa.Column("voided_by_id", sa.Integer(), nullable=True),
        sa.Column("void_reason", sa.UnicodeText(), nullable=True),
        sa.Column("request_key", sa.Unicode(36), nullable=True),
        sa.CheckConstraint("amount_cents > 0", name="ck_booking_refund_amount"),
        sa.ForeignKeyConstraint(["booking_id"], ["booking.id"]),
        sa.ForeignKeyConstraint(["recorded_by_id"], ["participant.id"]),
        sa.ForeignKeyConstraint(["voided_by_id"], ["participant.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_booking_refund_booking_id", "booking_refund", ["booking_id"])
    op.create_index(
        "uq_booking_refund_request_key",
        "booking_refund",
        ["request_key"],
        unique=True,
        mssql_where=sa.text("request_key IS NOT NULL"),
        sqlite_where=sa.text("request_key IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_booking_refund_request_key", table_name="booking_refund")
    op.drop_index("ix_booking_refund_booking_id", table_name="booking_refund")
    op.drop_table("booking_refund")
    mssql = op.get_bind().dialect.name == "mssql"
    for table, column in (("booking_activity", "exempt"), ("booking_meal", "exempt")):
        if mssql:
            _drop_default_constraint(table, column)
        with op.batch_alter_table(table) as batch:
            batch.drop_column(column)
    if mssql:
        _drop_default_constraint("booking", "fee_exempt")
        _drop_default_constraint("booking", "category")
    with op.batch_alter_table("booking") as batch:
        batch.drop_column("exemption_preview_token")
        batch.drop_column("fee_exempt")
        batch.drop_column("category")


def _drop_default_constraint(table_name: str, column_name: str) -> None:
    qualified_table = f"[dbo].[{table_name}]"
    op.execute(
        sa.text(
            f"""
            DECLARE @constraint_name sysname;
            DECLARE @statement nvarchar(max);
            SELECT @constraint_name = dc.name
            FROM sys.default_constraints AS dc
            INNER JOIN sys.columns AS c
                ON c.object_id = dc.parent_object_id
                AND c.column_id = dc.parent_column_id
            WHERE dc.parent_object_id = OBJECT_ID(N'{qualified_table}')
                AND c.name = N'{column_name}';
            IF @constraint_name IS NOT NULL
            BEGIN
                SET @statement = N'ALTER TABLE {qualified_table} DROP CONSTRAINT '
                    + QUOTENAME(@constraint_name);
                EXEC sp_executesql @statement;
            END;
            """
        )
    )
