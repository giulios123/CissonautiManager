import pytest
from sqlalchemy import select

from app.models import AuditLog, Participant, Slot
from tests.helpers import d
from tests.test_auth import login


@pytest.fixture
def invited(db, make_participant):
    return make_participant(
        "bob@example.com", first_name="Bob", last_name="Neri", invited_by="Ada Lovelace"
    )


@pytest.fixture
def uninvited(db, make_participant):
    return make_participant("cleo@example.com", first_name="Cleo", last_name="Gialli")


def put(client, person, verified=True):
    return client.put(f"/api/admin/participants/{person.id}/plus-one", json={"verified": verified})


def history_of(db, person):
    return [
        a for a in db.scalars(select(AuditLog).order_by(AuditLog.id)) if person.email in a.detail
    ]


class TestVerify:
    def test_an_admin_verifies_and_the_who_and_when_are_saved(
        self, admin_client, db, invited, clock
    ):
        response = put(admin_client, invited)
        assert response.status_code == 200, response.text
        body = response.json()
        assert body["verified"] is True
        assert body["verified_by"] == "Ada Lovelace"
        db.refresh(invited)
        assert invited.plus_one_verified_at == clock()
        admin = db.scalar(select(Participant).where(Participant.email == "boss@example.com"))
        assert invited.plus_one_verified_by_id == admin.id

    def test_taking_the_verification_back_clears_it(self, admin_client, db, invited):
        put(admin_client, invited)
        response = put(admin_client, invited, verified=False)
        assert response.json() == {
            "participant_id": invited.id,
            "verified": False,
            "verified_at": None,
            "verified_by": None,
        }
        db.refresh(invited)
        assert invited.plus_one_verified_at is None and invited.plus_one_verified_by_id is None

    def test_without_who_invited_them_it_is_refused(self, admin_client, db, uninvited):
        response = put(admin_client, uninvited)
        assert response.status_code == 422
        assert "chi l'ha invitata" in response.json()["detail"]
        db.refresh(uninvited)
        assert uninvited.plus_one_verified_at is None

    def test_spaces_only_count_as_empty(self, admin_client, db, make_participant):
        spaces = make_participant("sp@example.com", invited_by="   ")
        assert put(admin_client, spaces).status_code == 422

    def test_an_unknown_person_is_not_found(self, admin_client):
        response = admin_client.put(
            "/api/admin/participants/9999/plus-one", json={"verified": True}
        )
        assert response.status_code == 404

    def test_doing_it_twice_changes_and_logs_nothing_more(self, admin_client, db, invited):
        put(admin_client, invited)
        db.refresh(invited)
        first = invited.plus_one_verified_at
        put(admin_client, invited)
        db.refresh(invited)
        assert invited.plus_one_verified_at == first
        put(admin_client, invited, verified=False)
        put(admin_client, invited, verified=False)
        db.refresh(invited)
        assert first is not None and invited.plus_one_verified_at is None
        assert [a.action for a in history_of(db, invited)] == [
            "plus_one_verified",
            "plus_one_removed",
        ]

    def test_a_participant_cannot_call_it(self, client, outbox, invited, uninvited):
        login(client, outbox, email="cleo@example.com")
        assert put(client, invited).status_code == 403

    def test_an_anonymous_visitor_is_refused(self, client, invited):
        assert put(client, invited).status_code in (401, 403)


class TestHistory:
    def test_it_is_logged_even_for_someone_without_a_booking(self, admin_client, db, invited):
        put(admin_client, invited)
        [entry] = history_of(db, invited)
        assert entry.booking_id is None
        assert "Bob Neri" in entry.detail and "Ada Lovelace" in entry.detail

    def test_it_shows_in_the_history_of_their_booking(
        self, admin_client, db, make_booking, make_participant, slot_ids
    ):
        person = make_participant("dan@example.com", first_name="Dan", invited_by="Ada")
        booking = make_booking(person, [db.get(Slot, slot_ids[(d(13), "morning")])])
        put(admin_client, person)
        detail = admin_client.get(f"/api/admin/registrations/{booking.id}").json()
        assert (
            detail["participant"]["plus_one_verified_by"] == "Boss Admin"
            or detail["participant"]["plus_one_verified_by"]
        )
        assert detail["participant"]["plus_one_verified_at"] is not None
        assert [h["action"] for h in detail["history"]] == ["plus_one_verified"]

    def test_emptying_who_invited_them_drops_the_verification(
        self, admin_client, db, make_booking, make_participant, slot_ids
    ):
        person = make_participant("eve@example.com", first_name="Eve", invited_by="Ada")
        booking = make_booking(person, [db.get(Slot, slot_ids[(d(13), "morning")])])
        put(admin_client, person)
        response = admin_client.patch(
            f"/api/admin/registrations/{booking.id}", json={"invited_by": ""}
        )
        assert response.status_code == 200, response.text
        assert response.json()["participant"]["plus_one_verified_at"] is None
        db.refresh(person)
        assert person.plus_one_verified_at is None
        actions = [h["action"] for h in response.json()["history"]]
        assert "plus_one_removed" in actions and "details_changed" in actions

    def test_changing_who_invited_them_keeps_the_verification(
        self, admin_client, db, make_booking, make_participant, slot_ids
    ):
        person = make_participant("fay@example.com", first_name="Fay", invited_by="Ada")
        booking = make_booking(person, [db.get(Slot, slot_ids[(d(13), "morning")])])
        put(admin_client, person)
        admin_client.patch(f"/api/admin/registrations/{booking.id}", json={"invited_by": "Grace"})
        db.refresh(person)
        assert person.plus_one_verified_at is not None
