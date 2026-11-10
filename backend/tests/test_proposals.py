from datetime import timedelta

from sqlalchemy import select

from app.models import (
    STATUS_CANCEL_REQUESTED,
    STATUS_CONFIRMED,
    STATUS_EXPIRED,
    Booking,
    Contribution,
    Edition,
    Slot,
)
from app.services import edition as edition_service
from tests.helpers import d
from tests.test_auth import login
from tests.test_consents import _event, add_optional_document

URL = "/api/me/proposals"


def slot(db, day, period="morning") -> Slot:
    return db.scalar(select(Slot).where(Slot.date == d(day), Slot.period == period))


def offer(db, booking, kind, title, at, description=None):
    contribution = Contribution(
        booking_id=booking.id,
        kind=kind,
        title=title,
        description=description,
        created_at=at,
        updated_at=at,
    )
    db.add(contribution)
    db.commit()
    return contribution


def person(make_participant, make_booking, db, email, first, last, **booking):
    participant = make_participant(email, first_name=first, last_name=last)
    return participant, make_booking(participant, [slot(db, 13)], **booking)


def test_the_name_is_shown_only_with_a_valid_consent(
    client, outbox, db, edition, make_participant, make_booking, clock
):
    document = add_optional_document(db, edition)
    ada, ada_booking = person(make_participant, make_booking, db, "ada@example.com", "Ada", "L")
    bob, bob_booking = person(make_participant, make_booking, db, "bob@example.com", "Bob", "B")
    cara, _ = person(make_participant, make_booking, db, "cara@example.com", "Cara", "C")
    _event(db, edition, ada, document, "granted", clock)
    _event(db, edition, bob, document, "declined", clock)
    offer(db, ada_booking, "talk", "Macchine", clock(), "Venti minuti")
    offer(db, bob_booking, "skill", "Saldatura", clock() + timedelta(seconds=1))
    login(client, outbox, "cara@example.com")
    response = client.get(URL)
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.json() == [
        {
            "id": response.json()[0]["id"],
            "kind": "talk",
            "title": "Macchine",
            "description": "Venti minuti",
            "author": {"display_name": "Ada L"},
        },
        {
            "id": response.json()[1]["id"],
            "kind": "skill",
            "title": "Saldatura",
            "description": None,
            "author": None,
        },
    ]


def test_a_revoked_consent_makes_the_proposal_anonymous_on_the_next_read(
    client, outbox, db, edition, make_participant, make_booking, clock
):
    document = add_optional_document(db, edition)
    ada, ada_booking = person(make_participant, make_booking, db, "ada@example.com", "Ada", "L")
    person(make_participant, make_booking, db, "cara@example.com", "Cara", "C")
    _event(db, edition, ada, document, "granted", clock)
    offer(db, ada_booking, "talk", "Macchine", clock())
    login(client, outbox, "cara@example.com")
    assert client.get(URL).json()[0]["author"] == {"display_name": "Ada L"}
    _event(db, edition, ada, document, "withdrawn", clock)
    assert client.get(URL).json()[0]["author"] is None


def test_the_payload_of_an_anonymous_proposal_has_nothing_about_the_author(
    client, outbox, db, edition, make_participant, make_booking, clock
):
    _, bob_booking = person(make_participant, make_booking, db, "bob@example.com", "Bob", "Bianchi")
    person(make_participant, make_booking, db, "cara@example.com", "Cara", "C")
    offer(db, bob_booking, "topic", "Open source", clock())
    login(client, outbox, "cara@example.com")
    text = client.get(URL).text.lower()
    for leak in ("bob", "bianchi", "bob@example.com", "booking_id", "participant", "phone"):
        assert leak not in text
    assert set(client.get(URL).json()[0]) == {"id", "kind", "title", "description", "author"}


def test_own_expired_cancelled_hidden_and_other_edition_proposals_are_left_out(
    client, outbox, db, edition, make_participant, make_booking, clock
):
    _, cara_booking = person(make_participant, make_booking, db, "cara@example.com", "Cara", "C")
    offer(db, cara_booking, "talk", "Mio", clock())
    _, expired = person(
        make_participant,
        make_booking,
        db,
        "old@example.com",
        "Old",
        "E",
        status=STATUS_EXPIRED,
        hold_expires_at=clock() - timedelta(minutes=1),
    )
    offer(db, expired, "talk", "Scaduto", clock())
    _, cancelled = person(
        make_participant,
        make_booking,
        db,
        "gone@example.com",
        "Gone",
        "C",
        status=STATUS_CANCEL_REQUESTED,
    )
    offer(db, cancelled, "talk", "Disdetto", clock())
    _, dan_booking = person(
        make_participant, make_booking, db, "dan@example.com", "Dan", "D", status=STATUS_CONFIRMED
    )
    hidden = offer(db, dan_booking, "talk", "Nascosto", clock())
    hidden.hidden_at = clock()
    offer(db, dan_booking, "talk", "Visibile", clock())
    db.commit()
    login(client, outbox, "cara@example.com")
    assert [p["title"] for p in client.get(URL).json()] == ["Visibile"]


def test_kinds_are_ordered_and_can_be_filtered(
    client, outbox, db, edition, make_participant, make_booking, clock
):
    _, ada_booking = person(make_participant, make_booking, db, "ada@example.com", "Ada", "L")
    person(make_participant, make_booking, db, "cara@example.com", "Cara", "C")
    offer(db, ada_booking, "wanted_skill", "Video", clock())
    offer(db, ada_booking, "talk", "Macchine", clock())
    login(client, outbox, "cara@example.com")
    assert [p["kind"] for p in client.get(URL).json()] == ["talk", "wanted_skill"]
    assert [p["title"] for p in client.get(URL, params={"kind": "wanted_skill"}).json()] == [
        "Video"
    ]
    assert client.get(URL, params={"kind": "song"}).status_code == 422


def test_without_an_active_booking_it_is_forbidden(
    client, outbox, db, edition, make_participant, make_booking, clock
):
    _, ada_booking = person(make_participant, make_booking, db, "ada@example.com", "Ada", "L")
    offer(db, ada_booking, "talk", "Macchine", clock())
    make_participant("nobody@example.com")  # no booking at all
    person(
        make_participant,
        make_booking,
        db,
        "late@example.com",
        "Late",
        "L",
        status=STATUS_EXPIRED,
        hold_expires_at=clock() - timedelta(minutes=1),
    )
    for email in ("nobody@example.com", "late@example.com"):
        login(client, outbox, email)
        assert client.get(URL).status_code == 403
        client.post("/api/auth/logout")


def test_it_needs_a_session(client, edition):
    assert client.get(URL).status_code == 401


def test_an_admin_can_read_them_without_a_booking(
    admin_client, db, edition, make_participant, make_booking, clock
):
    _, ada_booking = person(make_participant, make_booking, db, "ada@example.com", "Ada", "L")
    offer(db, ada_booking, "talk", "Macchine", clock())
    assert [p["title"] for p in admin_client.get(URL).json()] == ["Macchine"]


def test_editions_do_not_mix(client, outbox, db, edition, make_participant, make_booking, clock):
    _, cara_booking = person(make_participant, make_booking, db, "cara@example.com", "Cara", "C")
    other = Edition(
        name="Old", start_date=edition.start_date, end_date=edition.end_date, is_active=False
    )
    db.add(other)
    db.commit()
    stranger = make_participant("stranger@example.com")
    privacy = edition_service.latest_legal_document(db, edition, "privacy")
    disclaimer = edition_service.latest_legal_document(db, edition, "disclaimer")
    foreign = Booking(
        edition_id=other.id,
        participant_id=stranger.id,
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
    offer(db, foreign, "talk", "Altra edizione", clock())
    login(client, outbox, "cara@example.com")
    assert client.get(URL).json() == []
    assert cara_booking.id  # the viewer is active in the current edition


class TestHide:
    def hide(self, client, contribution, **body):
        return client.post(f"/api/admin/contributions/{contribution.id}/hide", json=body)

    def test_a_hidden_proposal_disappears_for_the_others_but_not_for_its_author(
        self, admin_client, client, outbox, db, edition, make_participant, make_booking, clock
    ):
        _, ada_booking = person(make_participant, make_booking, db, "ada@example.com", "Ada", "L")
        person(make_participant, make_booking, db, "cara@example.com", "Cara", "C")
        contribution = offer(db, ada_booking, "talk", "Macchine", clock())
        assert self.hide(admin_client, contribution, reason="Contiene un nome").json() == {
            "id": contribution.id,
            "hidden": True,
        }
        login(client, outbox, "cara@example.com")
        assert client.get(URL).json() == []
        client.post("/api/auth/logout")
        login(client, outbox, "ada@example.com")
        mine = client.get("/api/me").json()["contributions"]
        assert [c["title"] for c in mine] == ["Macchine"]

    def test_hiding_twice_leaves_one_trace_and_showing_again_restores_it(
        self, admin_client, client, outbox, db, edition, make_participant, make_booking, clock
    ):
        from app.models import AuditLog

        _, ada_booking = person(make_participant, make_booking, db, "ada@example.com", "Ada", "L")
        person(make_participant, make_booking, db, "cara@example.com", "Cara", "C")
        contribution = offer(db, ada_booking, "talk", "Macchine", clock())
        self.hide(admin_client, contribution, reason="Nome")
        self.hide(admin_client, contribution)
        entries = list(db.scalars(select(AuditLog).where(AuditLog.action == "contribution_hidden")))
        assert len(entries) == 1
        assert "Nome" in entries[0].detail and entries[0].booking_id == ada_booking.id
        shown = admin_client.post(f"/api/admin/contributions/{contribution.id}/unhide")
        assert shown.json()["hidden"] is False
        admin_client.post(f"/api/admin/contributions/{contribution.id}/unhide")
        assert (
            len(list(db.scalars(select(AuditLog).where(AuditLog.action == "contribution_shown"))))
            == 1
        )
        login(client, outbox, "cara@example.com")
        assert [p["title"] for p in client.get(URL).json()] == ["Macchine"]

    def test_the_admin_view_and_csv_mark_hidden_proposals(
        self, admin_client, db, edition, make_participant, make_booking, clock
    ):
        _, ada_booking = person(make_participant, make_booking, db, "ada@example.com", "Ada", "L")
        contribution = offer(db, ada_booking, "talk", "Macchine", clock())
        offer(db, ada_booking, "topic", "Open source", clock() + timedelta(seconds=1))
        self.hide(admin_client, contribution)
        rows = admin_client.get("/api/admin/views/contributions").json()
        assert {r["title"]: r["hidden"] for r in rows} == {"Macchine": True, "Open source": False}
        response = admin_client.get("/api/admin/views/contributions?format=csv")
        lines = response.content.decode("utf-8-sig").splitlines()
        assert lines[0].split(";")[-1] == "Nascosta agli altri"
        assert sorted(line.split(";")[-1] for line in lines[1:]) == ["No", "Sì"]

    def test_only_admins_hide_and_unknown_ones_are_404(
        self, admin_client, client, outbox, db, edition, make_participant, make_booking, clock
    ):
        _, ada_booking = person(make_participant, make_booking, db, "ada@example.com", "Ada", "L")
        contribution = offer(db, ada_booking, "talk", "Macchine", clock())
        assert admin_client.post("/api/admin/contributions/9999/hide").status_code == 404
        anonymous = client.post(f"/api/admin/contributions/{contribution.id}/hide")
        assert anonymous.status_code == 401
        login(client, outbox, "ada@example.com")
        assert client.post(f"/api/admin/contributions/{contribution.id}/hide").status_code == 403
        assert client.post(f"/api/admin/contributions/{contribution.id}/unhide").status_code == 403
        db.refresh(contribution)
        assert contribution.hidden_at is None
