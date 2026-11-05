import csv
import io
from datetime import timedelta

import pytest
from sqlalchemy import select

from app.models import CLOSE_REMOVED, AuditLog, Slot
from tests.helpers import d
from tests.test_auth import login


def slot(db, day, period="morning") -> Slot:
    return db.scalar(select(Slot).where(Slot.date == d(day), Slot.period == period))


def parse(response):
    return list(csv.reader(io.StringIO(response.content.decode("utf-8-sig")), delimiter=";"))


@pytest.fixture
def queue(db, fill_slot, make_participant, add_entry, clock):
    """Monday morning full; Bea then Cid wait for it. Bea has no booking at all."""
    target = slot(db, 13)
    fill_slot(target)
    bea = make_participant("bea@example.com", first_name="Bea", last_name="Neri")
    cid = make_participant("cid@example.com", first_name="Cid", last_name="Rossi")
    first = add_entry(target, bea, clock() - timedelta(hours=2))
    second = add_entry(target, cid, clock() - timedelta(hours=1))
    return target, first, second


def test_slots_view_shows_the_queue_in_order(admin_client, queue):
    target, first, second = queue
    days = admin_client.get("/api/admin/views/slots").json()["days"]
    monday = next(s for s in days[0]["slots"] if s["id"] == target.id)
    assert [(w["first_name"], w["position"]) for w in monday["waitlist"]] == [
        ("Bea", 1),
        ("Cid", 2),
    ]
    assert monday["free"] == 0


def test_slots_csv_has_a_row_per_person_waiting(admin_client, queue):
    header, *rows = parse(admin_client.get("/api/admin/views/slots?format=csv"))
    waiting = [dict(zip(header, r, strict=True)) for r in rows if r[6] == "In lista d'attesa"]
    assert [(w["Nome"], w["Posizione in lista"]) for w in waiting] == [("Bea", "1"), ("Cid", "2")]


def test_admin_removes_an_entry_with_history_and_no_email(
    admin_client, db, queue, outbox, make_booking
):
    target, first, second = queue
    booking = make_booking(second.participant, [slot(db, 14)])
    outbox.sent.clear()
    assert admin_client.delete(f"/api/admin/waitlist/{second.id}").status_code == 204
    db.refresh(second)
    assert second.close_reason == CLOSE_REMOVED
    assert outbox.sent == []
    log = db.scalar(select(AuditLog).where(AuditLog.action == "waitlist_removed"))
    assert log.booking_id == booking.id
    assert "Cid Rossi (cid@example.com)" in log.detail
    assert admin_client.delete(f"/api/admin/waitlist/{second.id}").status_code == 404


def test_participants_cannot_remove_entries(client, outbox, queue):
    target, first, second = queue
    login(client, outbox, "bea@example.com")
    assert client.delete(f"/api/admin/waitlist/{first.id}").status_code == 403


def test_people_only_on_the_list_appear_in_people(admin_client, db, queue, make_booking):
    target, first, second = queue
    make_booking(second.participant, [slot(db, 14)])
    rows = admin_client.get("/api/admin/registrations").json()
    bea = next(r for r in rows if r["first_name"] == "Bea")
    cid = next(r for r in rows if r["first_name"] == "Cid")
    assert (bea["id"], bea["status"], bea["waitlist_slots"]) == (None, "in_lista", 1)
    assert cid["id"] is not None and cid["waitlist_slots"] == 1
    only = admin_client.get("/api/admin/registrations?status=in_lista").json()
    assert [r["first_name"] for r in only] == ["Bea"]
    assert admin_client.get("/api/admin/registrations?q=neri").json()[0]["first_name"] == "Bea"
    header, *csv_rows = parse(admin_client.get("/api/admin/registrations?format=csv"))
    bea_csv = dict(zip(header, next(r for r in csv_rows if r[0] == "Bea"), strict=True))
    assert bea_csv["Stato"] == "Solo in lista d'attesa"
    assert bea_csv["Slot in lista d'attesa"] == "1"


def test_detail_lists_the_persons_entries(admin_client, db, queue, make_booking):
    target, first, second = queue
    booking = make_booking(second.participant, [slot(db, 14)])
    detail = admin_client.get(f"/api/admin/registrations/{booking.id}").json()
    assert [(w["label"], w["position"]) for w in detail["waitlist"]] == [
        ("lun 13/07 mattina (09:00-13:00)", 2)
    ]


def test_a_verified_plus_one_is_shown_first_with_the_real_position(admin_client, db, queue, clock):
    target, first, second = queue
    cid = second.participant
    cid.invited_by = "Bea"
    cid.plus_one_verified_at = clock()
    first.participant.invited_by = "Grace"  # named but not verified
    db.commit()

    days = admin_client.get("/api/admin/views/slots").json()["days"]
    monday = next(s for s in days[0]["slots"] if s["id"] == target.id)

    assert [(w["first_name"], w["position"], w["plus_one"]) for w in monday["waitlist"]] == [
        ("Cid", 1, True),
        ("Bea", 2, False),
    ]
    cid_row, bea_row = monday["waitlist"]
    assert cid_row["participant_id"] == cid.id and cid_row["invited_by"] == "Bea"
    assert bea_row["invited_by"] == "Grace"


def test_nobody_verified_keeps_the_arrival_order_and_no_plus_one(admin_client, queue):
    target, first, second = queue
    days = admin_client.get("/api/admin/views/slots").json()["days"]
    monday = next(s for s in days[0]["slots"] if s["id"] == target.id)
    assert [w["plus_one"] for w in monday["waitlist"]] == [False, False]
    assert [w["invited_by"] for w in monday["waitlist"]] == [None, None]


def test_the_csv_shows_the_plus_one_and_who_invited_them(admin_client, db, queue, clock):
    target, first, second = queue
    second.participant.invited_by = "Bea"
    second.participant.plus_one_verified_at = clock()
    db.commit()
    header, *rows = parse(admin_client.get("/api/admin/views/slots?format=csv"))
    waiting = [dict(zip(header, r, strict=True)) for r in rows if r[6] == "In lista d'attesa"]
    assert [(w["Nome"], w["Posizione in lista"], w["+1 verificato"]) for w in waiting] == [
        ("Cid", "1", "sì"),
        ("Bea", "2", "no"),
    ]
    assert waiting[0]["Invitato da"] == "Bea"
    people = [dict(zip(header, r, strict=True)) for r in rows if r[6] != "In lista d'attesa"]
    assert all(p["+1 verificato"] == "" and p["Invitato da"] == "" for p in people)
