from app.models import ConsentEvent, Edition, LegalDocument
from app.services import consents as consent_service


def add_optional_document(db, edition, version=1):
    document = LegalDocument(
        edition_id=edition.id,
        kind="attendance",
        version=version,
        body=f"Presence v{version}",
        body_it=f"Presenza v{version}",
        body_en=f"Presence v{version}",
    )
    db.add(document)
    db.commit()
    return document


def test_legacy_person_without_optional_events_is_unexpressed(db, edition, make_participant):
    add_optional_document(db, edition)
    participant = make_participant()

    states = consent_service.get_states(db, edition, participant)

    assert [(state.kind, state.action) for state in states] == [
        ("attendance", "not_expressed"),
        ("media", "not_expressed"),
    ]


def test_record_choice_grant_decline_and_revoke_preserve_prior_evidence(
    db, edition, make_participant, clock
):
    document = add_optional_document(db, edition)
    participant = make_participant()
    first = consent_service.record_choice(
        db,
        edition,
        participant,
        kind="attendance",
        granted=True,
        document_id=document.id,
        version=document.version,
        locale="en",
        expected_event_id=None,
        source="self_service",
        now=clock(),
    )
    db.commit()

    revoked = consent_service.record_choice(
        db,
        edition,
        participant,
        kind="attendance",
        granted=False,
        document_id=document.id,
        version=document.version,
        locale="it",
        expected_event_id=first.id,
        source="self_service",
        now=clock(),
    )
    db.commit()

    rows = db.query(ConsentEvent).order_by(ConsentEvent.id).all()
    assert [(row.action, row.document_id) for row in rows] == [
        ("granted", document.id),
        ("withdrawn", document.id),
    ]
    assert revoked.action == "withdrawn"
    assert revoked.locale == "it"
    assert revoked.recorded_at == clock()


def test_identical_choice_is_noop_but_a_stale_different_choice_conflicts(
    db, edition, make_participant, clock
):
    document = add_optional_document(db, edition)
    participant = make_participant()
    first = consent_service.record_choice(
        db,
        edition,
        participant,
        kind="attendance",
        granted=False,
        document_id=document.id,
        version=document.version,
        locale="it",
        expected_event_id=None,
        source="self_service",
        now=clock(),
    )
    db.commit()

    assert (
        consent_service.record_choice(
            db,
            edition,
            participant,
            kind="attendance",
            granted=False,
            document_id=document.id,
            version=document.version,
            locale="it",
            expected_event_id=None,
            source="self_service",
            now=clock(),
        )
        is None
    )

    try:
        consent_service.record_choice(
            db,
            edition,
            participant,
            kind="attendance",
            granted=True,
            document_id=document.id,
            version=document.version,
            locale="it",
            expected_event_id=None,
            source="self_service",
            now=clock(),
        )
    except consent_service.ConsentConflict:
        pass
    else:
        raise AssertionError("stale different choice should conflict")

    assert db.query(ConsentEvent).count() == 1
    assert first.action == "declined"


def test_old_or_foreign_edition_document_cannot_be_used(db, edition, make_participant, clock):
    old_document = add_optional_document(db, edition)
    current_document = LegalDocument(
        edition_id=edition.id,
        kind="attendance",
        version=2,
        body="Current bilingual text",
        body_it="Testo corrente",
        body_en="Current text",
    )
    db.add(current_document)
    foreign_edition = Edition(name="Archived edition", is_active=False)
    db.add(foreign_edition)
    db.flush()
    foreign = LegalDocument(
        edition_id=foreign_edition.id,
        kind="attendance",
        version=1,
        body="Foreign",
        body_it="Foreign IT",
        body_en="Foreign EN",
    )
    db.add(foreign)
    db.commit()
    participant = make_participant()

    for document, expected_exception in (
        (old_document, consent_service.ConsentConflict),
        (foreign, consent_service.ConsentDocumentUnavailable),
    ):
        try:
            consent_service.record_choice(
                db,
                edition,
                participant,
                kind="attendance",
                granted=True,
                document_id=document.id,
                version=document.version,
                locale="it",
                expected_event_id=None,
                source="self_service",
                now=clock(),
            )
        except expected_exception:
            db.rollback()
        else:
            raise AssertionError("stale or foreign document should be rejected")

    assert current_document.id != old_document.id
    assert db.query(ConsentEvent).count() == 0


def test_unknown_purpose_is_rejected(db, edition, make_participant, clock):
    participant = make_participant()
    try:
        consent_service.record_choice(
            db,
            edition,
            participant,
            kind="privacy",
            granted=True,
            document_id=1,
            version=1,
            locale="it",
            expected_event_id=None,
            source="self_service",
            now=clock(),
        )
    except consent_service.InvalidConsentKind:
        pass
    else:
        raise AssertionError("mandatory purpose should not be accepted here")
