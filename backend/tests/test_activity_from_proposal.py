from datetime import timedelta

from sqlalchemy import func, select

from app.models import (
    STATUS_CONFIRMED,
    Activity,
    AuditLog,
    Booking,
    BookingActivity,
    Contribution,
    Edition,
    Slot,
)
from app.services import edition as edition_service
from tests.helpers import d
from tests.test_auth import login

URL = "/api/admin/activities"
FORM = {
    "title_it": "Escursione",
    "title_en": "Hike",
    "description_it": "Sul monte",
    "description_en": "On the mountain",
    "date": "2026-07-14",
    "period": "morning",
    "start_time": "09:30",
    "end_time": "12:00",
    "price_cents": 0,
    "capacity": None,
}


def slot(db, day, period="morning") -> Slot:
    return db.scalar(select(Slot).where(Slot.date == d(day), Slot.period == period))


def proposal(db, booking, title="Macchine analitiche", kind="talk", hidden=False, now=None):
    contribution = Contribution(
        booking_id=booking.id,
        kind=kind,
        title=title,
        description="Un talk",
        created_at=now,
        updated_at=now,
        hidden_at=now if hidden else None,
    )
    db.add(contribution)
    db.commit()
    return contribution


def count(db) -> int:
    return db.scalar(select(func.count()).select_from(Activity))


def test_creates_an_activity_from_a_proposal(
    admin_client, db, edition, make_participant, make_booking, clock
):
    ada = make_booking(make_participant("ada@example.com"), [slot(db, 13)])
    source = proposal(db, ada, now=clock())
    response = admin_client.post(URL, json={**FORM, "source_contribution_id": source.id})
    assert response.status_code == 201
    body = response.json()
    assert body["source"] == {"contribution_id": source.id, "title": "Macchine analitiche"}
    activity = db.get(Activity, body["id"])
    assert (activity.source_contribution_id, activity.source_title) == (
        source.id,
        "Macchine analitiche",
    )
    log = db.scalar(select(AuditLog).where(AuditLog.action == "activity_created"))
    assert f"Dalla proposta n. {source.id}" in log.detail


def test_the_author_is_not_signed_up_automatically(
    admin_client, db, edition, make_participant, make_booking, clock
):
    ada = make_booking(make_participant("ada@example.com"), [slot(db, 14)])
    source = proposal(db, ada, now=clock())
    admin_client.post(URL, json={**FORM, "source_contribution_id": source.id})
    assert db.scalar(select(func.count()).select_from(BookingActivity)) == 0


def test_an_activity_without_a_source_has_none(admin_client, edition):
    assert admin_client.post(URL, json=FORM).json()["source"] is None


def test_one_proposal_can_create_more_activities(
    admin_client, db, edition, make_participant, make_booking, clock
):
    ada = make_booking(make_participant("ada@example.com"), [slot(db, 13)])
    source = proposal(db, ada, now=clock())
    first = admin_client.post(
        URL, json={**FORM, "source_contribution_id": source.id, "request_key": "key-0000-0001"}
    )
    second = admin_client.post(
        URL,
        json={
            **FORM,
            "date": "2026-07-15",
            "source_contribution_id": source.id,
            "request_key": "key-0000-0002",
        },
    )
    assert (first.status_code, second.status_code) == (201, 201)
    assert first.json()["id"] != second.json()["id"]
    assert count(db) == 2


def test_a_repeated_save_returns_the_same_activity(
    admin_client, db, edition, make_participant, make_booking, clock
):
    ada = make_booking(make_participant("ada@example.com"), [slot(db, 13)])
    source = proposal(db, ada, now=clock())
    body = {**FORM, "source_contribution_id": source.id, "request_key": "key-0000-0001"}
    first = admin_client.post(URL, json=body)
    again = admin_client.post(URL, json=body)
    assert (first.status_code, again.status_code) == (201, 200)
    assert again.json()["id"] == first.json()["id"]
    assert count(db) == 1
    assert (
        db.scalar(
            select(func.count()).select_from(AuditLog).where(AuditLog.action == "activity_created")
        )
        == 1
    )


def test_the_first_save_wins_when_the_same_key_comes_with_other_content(admin_client, db, edition):
    first = admin_client.post(URL, json={**FORM, "request_key": "key-0000-0001"})
    again = admin_client.post(
        URL, json={**FORM, "title_it": "Altro", "request_key": "key-0000-0001"}
    )
    assert again.status_code == 200
    assert again.json()["id"] == first.json()["id"]
    assert again.json()["title"] == "Escursione"
    assert count(db) == 1


def test_a_proposal_of_another_edition_is_refused(
    admin_client, db, edition, make_participant, clock
):
    other = Edition(
        name="Old", start_date=edition.start_date, end_date=edition.end_date, is_active=False
    )
    db.add(other)
    db.commit()
    privacy = edition_service.latest_legal_document(db, edition, "privacy")
    disclaimer = edition_service.latest_legal_document(db, edition, "disclaimer")
    foreign = Booking(
        edition_id=other.id,
        participant_id=make_participant("stranger@example.com").id,
        status=STATUS_CONFIRMED,
        hold_expires_at=clock() + timedelta(days=3),
        amount_due_cents=0,
        privacy_document_id=privacy.id,
        privacy_accepted_at=clock(),
        disclaimer_document_id=disclaimer.id,
        disclaimer_accepted_at=clock(),
    )
    db.add(foreign)
    db.commit()
    source = proposal(db, foreign, now=clock())
    response = admin_client.post(URL, json={**FORM, "source_contribution_id": source.id})
    assert response.status_code == 404
    assert count(db) == 0


def test_a_missing_proposal_is_refused(admin_client, edition, db):
    assert admin_client.post(URL, json={**FORM, "source_contribution_id": 999}).status_code == 404
    assert count(db) == 0


def test_a_hidden_proposal_can_still_become_an_activity(
    admin_client, db, edition, make_participant, make_booking, clock
):
    ada = make_booking(make_participant("ada@example.com"), [slot(db, 13)])
    source = proposal(db, ada, hidden=True, now=clock())
    response = admin_client.post(URL, json={**FORM, "source_contribution_id": source.id})
    assert response.status_code == 201


def test_the_usual_checks_still_apply(
    admin_client, db, edition, make_participant, make_booking, clock
):
    ada = make_booking(make_participant("ada@example.com"), [slot(db, 13)])
    source = proposal(db, ada, now=clock())
    outside = admin_client.post(
        URL, json={**FORM, "date": "2026-08-01", "source_contribution_id": source.id}
    )
    missing_english = admin_client.post(
        URL, json={**FORM, "title_en": "", "source_contribution_id": source.id}
    )
    assert outside.status_code == 422
    assert missing_english.status_code == 422
    assert count(db) == 0


def test_editing_the_proposal_does_not_change_the_activity(
    admin_client, db, edition, make_participant, make_booking, clock
):
    ada = make_booking(make_participant("ada@example.com"), [slot(db, 13)])
    source = proposal(db, ada, now=clock())
    created = admin_client.post(URL, json={**FORM, "source_contribution_id": source.id}).json()
    source.title = "Titolo nuovo"
    source.description = "Altro"
    db.commit()
    detail = admin_client.get(f"{URL}/{created['id']}").json()
    assert detail["title"] == "Escursione"
    assert detail["source"] == {"contribution_id": source.id, "title": "Macchine analitiche"}


def test_participants_cannot_create_from_a_proposal(
    client, outbox, db, edition, make_participant, make_booking, clock
):
    ada = make_booking(make_participant("ada@example.com"), [slot(db, 13)])
    source = proposal(db, ada, now=clock())
    assert client.post(URL, json={**FORM, "source_contribution_id": source.id}).status_code == 401
    login(client, outbox, "ada@example.com")
    assert client.post(URL, json={**FORM, "source_contribution_id": source.id}).status_code == 403
    assert count(db) == 0


def test_a_race_between_two_saves_returns_the_winner(admin_client, db, edition, monkeypatch):
    from app.services import activities as activity_service

    first = admin_client.post(URL, json={**FORM, "request_key": "key-0000-0001"})
    real = activity_service.find_by_request_key
    calls = []

    def blind_the_first_lookup(db_, edition_, key):
        calls.append(key)
        return None if len(calls) == 1 else real(db_, edition_, key)

    monkeypatch.setattr(activity_service, "find_by_request_key", blind_the_first_lookup)
    again = admin_client.post(URL, json={**FORM, "request_key": "key-0000-0001"})
    assert again.status_code == 200
    assert again.json()["id"] == first.json()["id"]
    assert count(db) == 1


def _converted(admin_client, db, source):
    created = admin_client.post(URL, json={**FORM, "source_contribution_id": source.id}).json()
    return db.get(Activity, created["id"])


def test_the_activity_stays_when_the_author_deletes_the_proposal(
    admin_client, client, outbox, db, edition, make_participant, make_booking, clock
):
    ada = make_booking(make_participant("ada@example.com"), [slot(db, 13)])
    source = proposal(db, ada, now=clock())
    activity = _converted(admin_client, db, source)
    login(client, outbox, "ada@example.com")
    assert client.delete(f"/api/me/contributions/{source.id}").status_code == 204
    db.expire_all()
    activity = db.get(Activity, activity.id)
    assert activity.source_contribution_id is None
    assert activity.source_title == "Macchine analitiche"
    detail = admin_client.get(f"{URL}/{activity.id}").json()
    assert detail["source"] == {"contribution_id": None, "title": "Macchine analitiche"}


def test_the_activity_stays_when_the_booking_is_removed(
    admin_client, client, outbox, db, edition, make_participant, make_booking, clock
):
    ada = make_booking(make_participant("ada@example.com"), [slot(db, 13)])
    source = proposal(db, ada, now=clock())
    other = proposal(db, ada, title="Altro", now=clock())
    activity = _converted(admin_client, db, source)
    ids = (source.id, other.id, activity.id)
    login(client, outbox, "ada@example.com")
    assert client.post("/api/me/booking/cancel").json() == {"outcome": "removed"}
    db.expire_all()
    assert db.get(Contribution, ids[0]) is None
    assert db.get(Contribution, ids[1]) is None
    activity = db.get(Activity, ids[2])
    assert activity.source_contribution_id is None
    assert activity.source_title == "Macchine analitiche"


def test_other_proposals_keep_their_activities(
    admin_client, client, outbox, db, edition, make_participant, make_booking, clock
):
    ada = make_booking(make_participant("ada@example.com"), [slot(db, 13)])
    bob = make_booking(make_participant("bob@example.com", first_name="Bob"), [slot(db, 13)])
    ada_proposal = proposal(db, ada, now=clock())
    bob_proposal = proposal(db, bob, title="Saldatura", now=clock())
    ada_activity = _converted(admin_client, db, ada_proposal)
    bob_activity = _converted(admin_client, db, bob_proposal)
    ids = (ada_activity.id, bob_activity.id, bob_proposal.id)
    login(client, outbox, "ada@example.com")
    client.post("/api/me/booking/cancel")
    db.expire_all()
    assert db.get(Activity, ids[0]).source_contribution_id is None
    assert db.get(Activity, ids[1]).source_contribution_id == ids[2]


def test_the_contributions_view_lists_the_activities_created(
    admin_client, db, edition, make_participant, make_booking, clock
):
    ada = make_booking(make_participant("ada@example.com"), [slot(db, 13)])
    talk = proposal(db, ada, now=clock())
    proposal(db, ada, title="Senza attività", now=clock())
    admin_client.post(URL, json={**FORM, "source_contribution_id": talk.id})
    admin_client.post(
        URL,
        json={
            **FORM,
            "date": "2026-07-13",
            "title_it": "Prima",
            "title_en": "First",
            "source_contribution_id": talk.id,
        },
    )
    rows = {r["title"]: r for r in admin_client.get("/api/admin/views/contributions").json()}
    assert [
        (a["title"], a["date"], a["period"]) for a in rows["Macchine analitiche"]["activities"]
    ] == [
        ("Prima", "2026-07-13", "morning"),
        ("Escursione", "2026-07-14", "morning"),
    ]
    assert rows["Senza attività"]["activities"] == []


def test_the_contributions_view_uses_the_title_of_the_language_in_use(
    admin_client, db, edition, make_participant, make_booking, clock
):
    ada = make_booking(make_participant("ada@example.com"), [slot(db, 13)])
    talk = proposal(db, ada, now=clock())
    admin_client.post(URL, json={**FORM, "source_contribution_id": talk.id})
    english = admin_client.get("/api/admin/views/contributions", headers={"Accept-Language": "en"})
    assert english.json()[0]["activities"][0]["title"] == "Hike"


def test_the_contributions_csv_has_a_column_with_the_activities(
    admin_client, db, edition, make_participant, make_booking, clock
):
    import csv
    import io

    ada = make_booking(make_participant("ada@example.com"), [slot(db, 13)])
    talk = proposal(db, ada, now=clock())
    proposal(db, ada, title="Senza attività", now=clock())
    admin_client.post(URL, json={**FORM, "source_contribution_id": talk.id})
    admin_client.post(
        URL,
        json={
            **FORM,
            "date": "2026-07-13",
            "title_it": "Prima",
            "title_en": "First",
            "source_contribution_id": talk.id,
        },
    )
    response = admin_client.get("/api/admin/views/contributions?format=csv")
    rows = list(csv.reader(io.StringIO(response.content.decode("utf-8-sig")), delimiter=";"))
    assert rows[0][-1] == "Attività create"
    by_title = {r[1]: r[-1] for r in rows[1:]}
    assert by_title == {"Macchine analitiche": "Prima; Escursione", "Senza attività": ""}


def test_the_links_are_read_with_a_single_query(
    admin_client, db, edition, make_participant, make_booking, clock
):
    from sqlalchemy import event
    from sqlalchemy.engine import Engine

    ada = make_booking(make_participant("ada@example.com"), [slot(db, 13)])
    for number in range(4):
        source = proposal(db, ada, title=f"Proposta {number}", now=clock())
        admin_client.post(URL, json={**FORM, "source_contribution_id": source.id})
    statements: list[str] = []

    def record(conn, cursor, statement, *args):
        statements.append(statement)

    event.listen(Engine, "before_cursor_execute", record)
    try:
        admin_client.get("/api/admin/views/contributions")
    finally:
        event.remove(Engine, "before_cursor_execute", record)
    on_activity = [s for s in statements if "FROM activity" in s and "source_contribution_id" in s]
    assert len(on_activity) == 1


def test_participants_never_receive_the_source(
    admin_client, client, outbox, db, edition, make_participant, make_booking, clock
):
    ada = make_booking(make_participant("ada@example.com"), [slot(db, 14)])
    talk = proposal(db, ada, now=clock())
    admin_client.post(URL, json={**FORM, "source_contribution_id": talk.id})
    login(client, outbox, "ada@example.com")
    for path in ("/api/me", "/api/me/proposals"):
        response = client.get(path)
        assert response.status_code in (200, 403), path
        text = response.text
        assert "source_title" not in text and "source_contribution" not in text, path
        assert "Macchine analitiche" not in text.replace('"title":"Macchine analitiche"', ""), path
