from datetime import timedelta

import pytest
from sqlalchemy import select

from app.models import STATUS_EXPIRED, Contribution, Slot
from tests.helpers import d
from tests.test_auth import login


def slot(db, day, period="morning") -> Slot:
    return db.scalar(select(Slot).where(Slot.date == d(day), Slot.period == period))


@pytest.fixture
def booking(db, make_participant, make_booking):
    ada = make_participant("ada@example.com", can_bring="Una torta")
    return make_booking(ada, [slot(db, 13)])


@pytest.fixture
def member(client, outbox, booking):
    login(client, outbox)
    return client


TALK = {"kind": "talk", "title": "Macchine analitiche", "description": "Venti minuti"}


def test_add_edit_and_remove(member, db):
    created = member.post("/api/me/contributions", json=TALK)
    assert created.status_code == 201
    cid = created.json()["id"]
    me = member.get("/api/me").json()
    assert [c["title"] for c in me["contributions"]] == ["Macchine analitiche"]
    assert me["can_bring"] == "Una torta"
    edited = member.patch(
        f"/api/me/contributions/{cid}", json={"kind": "skill", "title": "Saldatura"}
    )
    assert (edited.json()["kind"], edited.json()["description"]) == ("skill", None)
    assert member.delete(f"/api/me/contributions/{cid}").status_code == 204
    assert member.get("/api/me").json()["contributions"] == []


def test_a_skill_i_look_for_is_a_fourth_kind(member):
    created = member.post(
        "/api/me/contributions", json={"kind": "wanted_skill", "title": "Chi sa fare video?"}
    )
    assert created.status_code == 201
    assert created.json()["kind"] == "wanted_skill"
    kinds = [c["kind"] for c in member.get("/api/me").json()["contributions"]]
    assert kinds == ["wanted_skill"]


def test_many_contributions_are_allowed(member):
    for title in ("Uno", "Due", "Tre"):
        member.post("/api/me/contributions", json=dict(TALK, title=title))
    assert len(member.get("/api/me").json()["contributions"]) == 3


def test_title_is_required_and_kind_checked(member):
    assert member.post("/api/me/contributions", json=dict(TALK, title="   ")).status_code == 422
    assert member.post("/api/me/contributions", json=dict(TALK, kind="song")).status_code == 422


def test_nobody_touches_the_contributions_of_others(member, db, make_participant, make_booking):
    bob_booking = make_booking(make_participant("bob@example.com"), [slot(db, 13)])
    theirs = Contribution(booking_id=bob_booking.id, kind="topic", title="Altro")
    db.add(theirs)
    db.commit()
    assert member.patch(f"/api/me/contributions/{theirs.id}", json=TALK).status_code == 404
    assert member.delete(f"/api/me/contributions/{theirs.id}").status_code == 404


def test_expired_booking_cannot_add(member, db, booking, clock):
    booking.status = STATUS_EXPIRED
    booking.hold_expires_at = clock() - timedelta(hours=1)
    db.commit()
    assert member.post("/api/me/contributions", json=TALK).status_code == 409


def test_they_go_with_a_removed_booking(member, db):
    member.post("/api/me/contributions", json=TALK)
    assert member.post("/api/me/booking/cancel").json()["outcome"] == "removed"
    assert db.scalar(select(Contribution)) is None
