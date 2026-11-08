"""Record privacy acceptances independently and track one notification attempt.

Revision ID: 0019
Revises: 0018
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import select, union

revision = "0019"
down_revision = "0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("consent_event") as batch:
        batch.alter_column("locale", existing_type=sa.String(2), nullable=True)

    op.create_table(
        "privacy_notice_attempt",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("edition_id", sa.Integer(), sa.ForeignKey("edition.id"), nullable=False),
        sa.Column("participant_id", sa.Integer(), sa.ForeignKey("participant.id"), nullable=False),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("legal_document.id"), nullable=False),
        sa.Column("attempted_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint(
            "edition_id",
            "participant_id",
            "document_id",
            name="uq_privacy_notice_attempt_edition_id",
        ),
    )

    bind = op.get_bind()
    legal = sa.table(
        "legal_document",
        sa.column("id", sa.Integer()),
        sa.column("kind", sa.Unicode(16)),
    )
    bookings = sa.table(
        "booking",
        sa.column("edition_id", sa.Integer()),
        sa.column("participant_id", sa.Integer()),
        sa.column("privacy_document_id", sa.Integer()),
        sa.column("privacy_accepted_at", sa.DateTime()),
    )
    slots = sa.table(
        "slot",
        sa.column("id", sa.Integer()),
        sa.column("edition_id", sa.Integer()),
    )
    waitlist = sa.table(
        "waitlist_entry",
        sa.column("slot_id", sa.Integer()),
        sa.column("participant_id", sa.Integer()),
        sa.column("privacy_document_id", sa.Integer()),
        sa.column("privacy_accepted_at", sa.DateTime()),
    )
    source = union(
        select(
            bookings.c.edition_id,
            bookings.c.participant_id,
            bookings.c.privacy_document_id.label("document_id"),
            bookings.c.privacy_accepted_at.label("recorded_at"),
        )
        .select_from(bookings.join(legal, legal.c.id == bookings.c.privacy_document_id))
        .where(legal.c.kind == "privacy"),
        select(
            slots.c.edition_id,
            waitlist.c.participant_id,
            waitlist.c.privacy_document_id.label("document_id"),
            waitlist.c.privacy_accepted_at.label("recorded_at"),
        )
        .select_from(
            waitlist.join(slots, slots.c.id == waitlist.c.slot_id).join(
                legal, legal.c.id == waitlist.c.privacy_document_id
            )
        )
        .where(legal.c.kind == "privacy"),
    )
    events = sa.table(
        "consent_event",
        sa.column("edition_id", sa.Integer()),
        sa.column("participant_id", sa.Integer()),
        sa.column("kind", sa.Unicode(16)),
        sa.column("action", sa.Unicode(12)),
        sa.column("document_id", sa.Integer()),
        sa.column("locale", sa.String(2)),
        sa.column("recorded_at", sa.DateTime()),
        sa.column("source", sa.Unicode(20)),
    )
    legacy_events = bind.execute(source).all()
    for row in legacy_events:
        bind.execute(
            events.insert().values(
                edition_id=row.edition_id,
                participant_id=row.participant_id,
                kind="privacy",
                action="accepted",
                document_id=row.document_id,
                locale=None,
                recorded_at=row.recorded_at,
                source="legacy_import",
            )
        )


def downgrade() -> None:
    op.drop_table("privacy_notice_attempt")
    op.execute(sa.text("DELETE FROM consent_event WHERE kind = 'privacy'"))
    with op.batch_alter_table("consent_event") as batch:
        batch.alter_column("locale", existing_type=sa.String(2), nullable=False)
